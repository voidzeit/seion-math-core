"""Does tightening the certificate actually cost less, or only look smaller?

`tau` is not the commercial number. Rank is discrete, so a 47.7% reduction in
certificate slack buys exactly nothing unless it crosses an integer rank
boundary -- which an earlier sweep saw happening in only one of four tolerance
regimes. This measures the quantity that decides the question:

    Tax(eps) = Cost( cheapest rank whose CERTIFICATE clears eps )
             / Cost( cheapest rank whose TRUE ERROR clears eps )

for M24 and for the TT Pythagorean certificate, over a logarithmic sweep of
RELATIVE tolerances on normalized problems. Plus the frontier distance

    q(eps) = eps / C(r-)        r- = cheapest configuration that still FAILS

which says how much further tightening would be needed to drop a rank: q = 0.96
means 4% away and worth chasing; q = 0.45 means a further 55% is required and
probably is not worth inventing a theorem for.

COST MODEL. Errors and certificates are executed. Costs are the TT-FORMAT
storage and contraction FLOPs implied by the rank vector, computed
analytically -- the synthetic chain materializes its left index, so its own
memory traffic is not a tensor train's. Pairing an executed error with a
modelled cost is deliberate, and is the only honest option short of a real TT
runtime.

Ranks are swept UNIFORMLY across bonds. Per-bond allocation is the adaptive
question and is deliberately not entangled with this measurement.

FAIL CLOSED: any instance where a certificate falls below the true error is a
soundness violation and aborts the run.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent


def spectrum(size, decay, rate):
    """Prescribed singular values: this is what makes a train compressible."""
    index = np.arange(1, size + 1, dtype=float)
    if decay == "poly":
        return index ** (-rate)
    if decay == "exp":
        return np.exp(-rate * (index - 1))
    if decay == "flat":
        return np.ones(size)
    raise ValueError(decay)


def random_tt(bond, physical, cores, rng, decay="poly", rate=2.0):
    """A train whose cores have a controlled spectrum.

    Gaussian cores have a FLAT spectrum, hence no low-rank structure: truncation
    is catastrophic until nothing is discarded, and at full rank the error is
    exactly zero. Both the oracle and every certificate then pick the same rank
    and every tax is trivially 1.000 -- a property of the generator, not of the
    certificate. Real workloads are compressible, so the spectrum is imposed.
    """
    def shaped(rows, columns):
        left, _ = np.linalg.qr(rng.standard_normal((rows, max(rows, columns))))
        right, _ = np.linalg.qr(rng.standard_normal((columns,
                                                     max(rows, columns))))
        values = spectrum(min(rows, columns), decay, rate)
        return (left[:, :len(values)] * values) @ right[:, :len(values)].T

    train = [shaped(physical, bond)]
    for _ in range(cores - 2):
        train.append(shaped(bond, physical * bond).reshape(bond, physical,
                                                           bond))
    train.append(shaped(bond, physical))
    return train


def contract_step(partial, core):
    if core.ndim == 2:
        return (partial @ core).reshape(-1)
    out = np.einsum("Ni,inj->Nnj", partial, core)
    return out.reshape(-1, out.shape[2])


def run_at_rank(train, rank):
    """Executed: true error and both certificates, relative to the norm."""
    ambient = train[0].copy()
    reduced = train[0].copy()
    m24, pythagorean, kept = 0.0, 0.0, []
    for index, core in enumerate(train[1:], start=1):
        flat = core.reshape(core.shape[0], -1)
        gain = float(np.linalg.svd(flat, compute_uv=False)[0])
        ambient = contract_step(ambient, core)
        raw = contract_step(reduced, core)
        if index == len(train) - 1:
            scale = float(np.linalg.norm(ambient))
            if scale <= 0:
                return None
            return {"error": float(np.linalg.norm(ambient - raw)) / scale,
                    "m24": gain * m24 / scale,
                    "pyth": gain * pythagorean / scale,
                    "kept": kept}
        left, values, _ = np.linalg.svd(raw, full_matrices=False)
        keep = min(rank, values.size)
        basis = left[:, :keep]
        projected = basis @ (basis.T @ raw)
        gamma = float(np.linalg.norm(raw - projected))
        m24 = gain * m24 + gamma
        pythagorean = math.sqrt((gain * pythagorean) ** 2 + gamma ** 2)
        kept.append(keep)
        reduced = projected
    raise AssertionError("chain ended without a root")


def tt_storage(kept, physical, first_bond):
    """Sum over k of n_k r_(k-1) r_k, for the TT format the ranks imply."""
    total, previous = physical * first_bond, first_bond
    for rank in kept:
        total += physical * previous * rank
        previous = rank
    return total + physical * previous


def tt_flops(kept, physical, first_bond):
    """Contraction cost of the same train, one multiply-add per element."""
    total, previous = 0, first_bond
    for rank in kept:
        total += physical * previous * rank * previous
        previous = rank
    return max(total, 1)


def cheapest_clearing(rows, key, tolerance):
    feasible = [row for row in rows if row[key] <= tolerance]
    if not feasible:
        return None
    return min(feasible, key=lambda row: row["storage"])


def frontier_gap(rows, key, tolerance):
    """eps / C(r-) for the cheapest configuration that still fails."""
    failing = [row for row in rows if row[key] > tolerance]
    if not failing:
        return None
    nearest = min(failing, key=lambda row: row[key])
    return tolerance / nearest[key]


HEADER = ["tolerance", "instances", "tax_m24_storage", "tax_pyth_storage",
          "recovered_storage", "tax_m24_flops", "tax_pyth_flops",
          "recovered_flops", "q_frontier_pyth"]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bond", type=int, default=12)
    parser.add_argument("--physical", type=int, default=3)
    parser.add_argument("--cores", type=int, default=6)
    parser.add_argument("--ranks", type=int, nargs="+",
                        default=list(range(1, 13)))
    parser.add_argument("--instances", type=int, default=80)
    parser.add_argument("--tolerances", type=float, nargs="+",
                        default=[3e-1, 1e-1, 3e-2, 1e-2, 3e-3, 1e-3])
    parser.add_argument("--seed", type=int, default=20260818)
    parser.add_argument("--decay", choices=("poly", "exp", "flat"),
                        default="poly")
    parser.add_argument("--decay-rate", type=float, default=2.0)
    parser.add_argument("--label", type=str, default="dense-ranks")
    parser.add_argument("--csv", type=str, default="tt_econ_frontier_v1.csv")
    parser.add_argument("--json", type=str, default="tt_econ_frontier_v1.json")
    args = parser.parse_args()

    rng = np.random.default_rng(args.seed)
    corpus, violations = [], 0
    for _ in range(args.instances):
        train = random_tt(args.bond, args.physical, args.cores, rng,
                          args.decay, args.decay_rate)
        rows = []
        for rank in args.ranks:
            result = run_at_rank(train, rank)
            if result is None:
                continue
            if (result["m24"] < result["error"] * (1 - 1e-9)
                    or result["pyth"] < result["error"] * (1 - 1e-9)):
                violations += 1
            rows.append({"rank": rank, **result,
                         "storage": tt_storage(result["kept"], args.physical,
                                               args.bond),
                         "flops": tt_flops(result["kept"], args.physical,
                                           args.bond)})
        corpus.append(rows)

    if violations:
        raise SystemExit(f"FAIL CLOSED: {violations} soundness violations")

    print(f"{args.label}: {args.instances} instances, cores {args.cores}, "
          f"bond {args.bond}, spectrum {args.decay}(rate={args.decay_rate})")
    print("soundness: 0 violations\n")
    print(f"{'eps':>9} {'n':>4} {'TaxM24':>8} {'TaxPyth':>8} {'recov':>8} "
          f"{'TaxM24_F':>9} {'TaxPyth_F':>9} {'recov_F':>8} {'q_front':>8}")

    records = []
    for tolerance in args.tolerances:
        bucket = {"m24_s": [], "pyth_s": [], "m24_f": [], "pyth_f": [],
                  "q": []}
        for rows in corpus:
            oracle = cheapest_clearing(rows, "error", tolerance)
            cert_m24 = cheapest_clearing(rows, "m24", tolerance)
            cert_pyth = cheapest_clearing(rows, "pyth", tolerance)
            if not (oracle and cert_m24 and cert_pyth):
                continue
            bucket["m24_s"].append(cert_m24["storage"] / oracle["storage"])
            bucket["pyth_s"].append(cert_pyth["storage"] / oracle["storage"])
            bucket["m24_f"].append(cert_m24["flops"] / oracle["flops"])
            bucket["pyth_f"].append(cert_pyth["flops"] / oracle["flops"])
            gap = frontier_gap(rows, "pyth", tolerance)
            if gap is not None:
                bucket["q"].append(gap)
        if not bucket["m24_s"]:
            print(f"{tolerance:9.1e}    -   not reachable at any swept rank")
            continue
        m24_s = float(np.median(bucket["m24_s"]))
        pyth_s = float(np.median(bucket["pyth_s"]))
        m24_f = float(np.median(bucket["m24_f"]))
        pyth_f = float(np.median(bucket["pyth_f"]))
        recovered_s = ((m24_s - pyth_s) / (m24_s - 1)
                       if m24_s > 1 + 1e-12 else float("nan"))
        recovered_f = ((m24_f - pyth_f) / (m24_f - 1)
                       if m24_f > 1 + 1e-12 else float("nan"))
        gap = float(np.median(bucket["q"])) if bucket["q"] else float("nan")
        print(f"{tolerance:9.1e} {len(bucket['m24_s']):4d} {m24_s:8.3f} "
              f"{pyth_s:8.3f} {100 * recovered_s:7.1f}% {m24_f:9.3f} "
              f"{pyth_f:9.3f} {100 * recovered_f:7.1f}% {gap:8.3f}")
        records.append(dict(zip(HEADER, [tolerance, len(bucket["m24_s"]),
                                         m24_s, pyth_s, recovered_s, m24_f,
                                         pyth_f, recovered_f, gap])))

    with (HERE / args.csv).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=HEADER)
        writer.writeheader()
        writer.writerows(records)
    (HERE / args.json).write_text(json.dumps(
        {"config": vars(args), "soundness_violations": violations,
         "frontier": records}, indent=2), encoding="utf-8")
    print(f"\n-> {args.csv}, {args.json}")


if __name__ == "__main__":
    main()
