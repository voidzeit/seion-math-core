"""Is the certification tax caused by the certificate, or by uniform ranks?

The frontier sweep found a storage tax up to 3.75x, but tightening the
certificate by 47.7% recovered only 0-10% of it. That points somewhere else:
both the oracle and the certificate were forced to use the SAME rank at every
bond, so most of the gap may be the uniformity, not the bound.

This separates the two by measuring four allocators against one another on
trains whose cores have DIFFERENT spectra -- heterogeneity is what creates an
opportunity for non-uniform allocation in the first place, and the previous
corpus had none:

    uniform-oracle    one rank everywhere, chosen by the TRUE error
    uniform-cert      one rank everywhere, chosen by the Pythagorean certificate
    perbond-oracle    per-bond ranks, chosen by the TRUE error       <- the floor
    perbond-cert      per-bond ranks, chosen by the certificate      <- deployable
    threshold         the field baseline: one discarded-weight cutoff, ranks
                      follow from it

The search over per-bond rank vectors is EXHAUSTIVE, not greedy, so the oracle
is the real minimum and no allocation policy is smuggled into the measurement.
That fixes the chain small enough to enumerate.

Reading:
    tax_uniform_cert / tax_perbond_cert   how much allocation alone buys
    tax_perbond_cert  (vs perbond oracle) what the certificate still costs
"""

from __future__ import annotations

import argparse
import itertools
import json
import math
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent


def shaped_core(rows, columns, rate, rng):
    left, _ = np.linalg.qr(rng.standard_normal((rows, max(rows, columns))))
    right, _ = np.linalg.qr(rng.standard_normal((columns, max(rows, columns))))
    size = min(rows, columns)
    values = np.arange(1, size + 1, dtype=float) ** (-rate)
    return (left[:, :size] * values) @ right[:, :size].T


def heterogeneous_tt(bond, physical, cores, rng, rate_low, rate_high):
    """Each core gets its own decay rate: some bonds are cheap to truncate."""
    rates = rng.uniform(rate_low, rate_high, size=cores)
    train = [shaped_core(physical, bond, rates[0], rng)]
    for index in range(1, cores - 1):
        train.append(shaped_core(bond, physical * bond, rates[index], rng)
                     .reshape(bond, physical, bond))
    train.append(shaped_core(bond, physical, rates[-1], rng))
    return train, rates


def contract_step(partial, core):
    if core.ndim == 2:
        return (partial @ core).reshape(-1)
    out = np.einsum("Ni,inj->Nnj", partial, core)
    return out.reshape(-1, out.shape[2])


def evaluate_ranks(train, ranks):
    """Executed error and Pythagorean certificate for a per-bond rank vector."""
    ambient = train[0].copy()
    reduced = train[0].copy()
    certificate, kept, tails = 0.0, [], []
    bond_index = 0
    for index, core in enumerate(train[1:], start=1):
        gain = float(np.linalg.svd(core.reshape(core.shape[0], -1),
                                   compute_uv=False)[0])
        ambient = contract_step(ambient, core)
        raw = contract_step(reduced, core)
        if index == len(train) - 1:
            scale = float(np.linalg.norm(ambient))
            if scale <= 0:
                return None
            return {"error": float(np.linalg.norm(ambient - raw)) / scale,
                    "cert": gain * certificate / scale, "kept": kept,
                    "tails": tails}
        left, values, _ = np.linalg.svd(raw, full_matrices=False)
        keep = min(ranks[bond_index], values.size)
        basis = left[:, :keep]
        projected = basis @ (basis.T @ raw)
        gamma = float(np.linalg.norm(raw - projected))
        certificate = math.sqrt((gain * certificate) ** 2 + gamma ** 2)
        kept.append(keep)
        tails.append(values[keep:])
        bond_index += 1
        reduced = projected
    raise AssertionError("chain ended without a root")


def storage(kept, physical, bond):
    total, previous = physical * bond, bond
    for rank in kept:
        total += physical * previous * rank
        previous = rank
    return total + physical * previous


def threshold_ranks(train, cutoff, physical, bond, max_rank):
    """Field baseline: keep singular values above a common relative cutoff."""
    reduced = train[0].copy()
    ranks = []
    for index, core in enumerate(train[1:], start=1):
        if index == len(train) - 1:
            break
        raw = contract_step(reduced, core)
        left, values, _ = np.linalg.svd(raw, full_matrices=False)
        total = float(np.sqrt((values ** 2).sum()))
        keep = 1
        for candidate in range(1, values.size + 1):
            tail = float(np.sqrt((values[candidate:] ** 2).sum()))
            if tail <= cutoff * total:
                keep = candidate
                break
            keep = min(candidate + 1, values.size)
        keep = min(keep, max_rank)
        basis = left[:, :keep]
        reduced = basis @ (basis.T @ raw)
        ranks.append(keep)
    return ranks


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bond", type=int, default=8)
    parser.add_argument("--physical", type=int, default=3)
    parser.add_argument("--cores", type=int, default=5)
    parser.add_argument("--max-rank", type=int, default=8)
    parser.add_argument("--instances", type=int, default=40)
    parser.add_argument("--rate-low", type=float, default=0.6)
    parser.add_argument("--rate-high", type=float, default=2.6)
    parser.add_argument("--tolerances", type=float, nargs="+",
                        default=[3e-1, 1e-1, 3e-2, 1e-2])
    parser.add_argument("--seed", type=int, default=20260818)
    parser.add_argument("--json", type=str,
                        default="tt_allocation_split_v1.json")
    args = parser.parse_args()

    rng = np.random.default_rng(args.seed)
    bonds = args.cores - 2
    grid = list(itertools.product(range(1, args.max_rank + 1), repeat=bonds))
    print(f"{args.instances} instances, {args.cores} cores, {bonds} bonds, "
          f"exhaustive over {len(grid)} rank vectors")
    print(f"heterogeneous decay rates in [{args.rate_low}, {args.rate_high}]\n")

    corpus, violations = [], 0
    for _ in range(args.instances):
        train, _ = heterogeneous_tt(args.bond, args.physical, args.cores, rng,
                                    args.rate_low, args.rate_high)
        rows = []
        for ranks in grid:
            result = evaluate_ranks(train, ranks)
            if result is None:
                continue
            if result["cert"] < result["error"] * (1 - 1e-9):
                violations += 1
            rows.append({"ranks": ranks, "error": result["error"],
                         "cert": result["cert"],
                         "storage": storage(result["kept"], args.physical,
                                            args.bond)})
        corpus.append((train, rows))
    if violations:
        raise SystemExit(f"FAIL CLOSED: {violations} soundness violations")
    print("soundness: 0 violations\n")

    def cheapest(rows, key, tolerance, uniform_only=False):
        pool = [row for row in rows if row[key] <= tolerance
                and (not uniform_only or len(set(row["ranks"])) == 1)]
        return min(pool, key=lambda row: row["storage"]) if pool else None

    print(f"{'eps':>8} {'n':>4} {'uni-orac':>9} {'uni-cert':>9} "
          f"{'pb-orac':>9} {'pb-cert':>9} {'thresh':>9} | "
          f"{'taxUNI':>7} {'taxPB':>7} {'alloc gain':>11}")
    records = []
    for tolerance in args.tolerances:
        rows_out = {"uni_o": [], "uni_c": [], "pb_c": [], "thr": []}
        for train, rows in corpus:
            floor = cheapest(rows, "error", tolerance)
            uniform_oracle = cheapest(rows, "error", tolerance, True)
            uniform_cert = cheapest(rows, "cert", tolerance, True)
            perbond_cert = cheapest(rows, "cert", tolerance)
            if not (floor and uniform_oracle and uniform_cert and perbond_cert):
                continue
            ranks = threshold_ranks(train, tolerance, args.physical, args.bond,
                                    args.max_rank)
            checked = evaluate_ranks(train, ranks)
            threshold_cost = (storage(checked["kept"], args.physical,
                                      args.bond)
                              if checked and checked["error"] <= tolerance
                              else None)
            rows_out["uni_o"].append(uniform_oracle["storage"]
                                     / floor["storage"])
            rows_out["uni_c"].append(uniform_cert["storage"]
                                     / floor["storage"])
            rows_out["pb_c"].append(perbond_cert["storage"] / floor["storage"])
            if threshold_cost:
                rows_out["thr"].append(threshold_cost / floor["storage"])
        if not rows_out["uni_c"]:
            print(f"{tolerance:8.1e}    -   unreachable")
            continue
        uni_o = float(np.median(rows_out["uni_o"]))
        uni_c = float(np.median(rows_out["uni_c"]))
        pb_c = float(np.median(rows_out["pb_c"]))
        thr = float(np.median(rows_out["thr"])) if rows_out["thr"] else float("nan")
        print(f"{tolerance:8.1e} {len(rows_out['uni_c']):4d} {uni_o:9.3f} "
              f"{uni_c:9.3f} {1.000:9.3f} {pb_c:9.3f} {thr:9.3f} | "
              f"{uni_c:7.3f} {pb_c:7.3f} {uni_c / pb_c:10.3f}x")
        records.append({"tolerance": tolerance,
                        "uniform_oracle": uni_o, "uniform_cert": uni_c,
                        "perbond_cert": pb_c, "threshold": thr,
                        "allocation_gain": uni_c / pb_c,
                        "instances": len(rows_out["uni_c"])})

    print("\nAll costs are relative to the per-bond ORACLE, which is 1.000 by")
    print("construction. `taxUNI` is what a uniform-rank certified run costs;")
    print("`taxPB` is what the same certificate costs once it may allocate.")
    (HERE / args.json).write_text(json.dumps(
        {"config": vars(args), "rows": records}, indent=2), encoding="utf-8")
    print(f"\n-> {args.json}")


if __name__ == "__main__":
    main()
