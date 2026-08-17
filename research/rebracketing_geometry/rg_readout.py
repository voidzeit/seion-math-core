"""Positive-control readout for the k=2 rebracketing sweep.

The whole point of this file is the calibration column. J_2 = 2 is PROVED
attainable in the same-law/shared-projector class by an exact witness
(RG_CANONICAL.md, Theorem 3.1), so the J arm is a POSITIVE CONTROL on the
search itself:

    gamma_J := J_found / 2          in the same-law class

If gamma_J is close to 1, the optimizer demonstrably reaches hard same-law
extremizers, and only then does a shortfall in the S arm,

    gamma_S := S_found / Sigma_2(eta),

carry information about the mathematics rather than about the optimizer. If
gamma_J is materially below 1, NOTHING may be concluded from gamma_S -- the
harness has not been shown to reach the frontier of that class.

Reads the raw JSON of rg_fused_search.py (or rg4_s2_search.py, same schema).
"""

from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
CALIBRATION_THRESHOLD = 0.99


def load(paths):
    runs = []
    for path in paths:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        runs.extend(payload["runs"])
    return runs


def best_ratio(rows):
    """Highest attained/ceiling over a set of cells, and where it happened."""
    if not rows:
        return None
    best = max(rows, key=lambda r: r["best"] / r["ceiling"])
    return {"ratio": best["best"] / best["ceiling"], "value": best["best"],
            "ceiling": best["ceiling"], "eta": best["eta"],
            "dim": best["dim"], "rank": best["rank"]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", nargs="+",
                        default=[str(HERE / "rg_fused_search_raw.json")])
    args = parser.parse_args()

    runs = load(args.json)
    grouped = defaultdict(list)
    for row in runs:
        grouped[(row["class"], row["objective"])].append(row)

    classes = sorted({row["class"] for row in runs})
    objectives = [o for o in ("J", "H", "S")
                  if any(row["objective"] == o for row in runs)]

    print(f"{len(runs)} cells\n")
    header = f"{'class':>18}" + "".join(
        f" | {o + ' attained/ceiling':>22}" for o in objectives)
    print(header)
    print("-" * len(header))
    for klass in classes:
        line = f"{klass:>18}"
        for objective in objectives:
            best = best_ratio(grouped[(klass, objective)])
            line += (f" | {best['ratio'] * 100:8.4f}%  "
                     f"(eta {best['eta']:.3f} D{best['dim']}r{best['rank']})"
                     if best else f" | {'--':>22}")
        print(line)

    print("\nCalibration:")
    verdicts = {}
    for klass in classes:
        control = best_ratio(grouped[(klass, "J")])
        if control is None:
            continue
        gamma_J = control["ratio"]
        calibrated = gamma_J >= CALIBRATION_THRESHOLD
        verdicts[klass] = calibrated
        print(f"  {klass:>18}: gamma_J = {gamma_J:.6f} "
              f"-> {'CALIBRATED' if calibrated else 'NOT CALIBRATED'}")
        target = best_ratio(grouped[(klass, "S")])
        if target is None:
            continue
        gamma_S = target["ratio"]
        if calibrated:
            reading = (f"gamma_S = {gamma_S:.6f}; the optimizer reaches this "
                       f"class's known extremum, so a persistent shortfall "
                       f"here is evidence about the geometry")
            if gamma_S >= CALIBRATION_THRESHOLD:
                reading += " -- but there is no shortfall: S is saturated too"
        else:
            reading = (f"gamma_S = {gamma_S:.6f} is UNINTERPRETABLE: the "
                       f"harness was not shown to reach this class's frontier")
        print(f"  {'':>18}  {reading}")

    print("\nWorst excess over any ceiling (must be <= 0):")
    for klass in classes:
        for objective in objectives:
            rows = grouped[(klass, objective)]
            if not rows:
                continue
            worst = max(rows, key=lambda r: r["best"] - r["ceiling"])
            print(f"  {klass:>18} {objective}: "
                  f"{worst['best'] - worst['ceiling']:+.3e}")
    violations = [r for r in runs if r["best"] > r["ceiling"] + 1e-6]
    print(f"\n  cells above a ceiling: {len(violations)}")

    # eta-resolved S curve in every calibrated class: this is where a genuine
    # structural restriction would show up as a stable, eta-independent deficit
    # rather than as optimizer noise.
    for klass in classes:
        rows = grouped[(klass, "S")]
        if not rows:
            continue
        print(f"\n  S ratio vs eta, {klass}"
              f"{'' if verdicts.get(klass) else '  [class NOT calibrated]'}:")
        by_eta = defaultdict(list)
        for row in rows:
            by_eta[row["eta"]].append(row["best"] / row["ceiling"])
        for eta in sorted(by_eta):
            print(f"    eta={eta:6.4f}  max ratio {max(by_eta[eta]):.6f}  "
                  f"Sigma_2={math.sin(min(2 * math.asin(min(eta, 1.0)), math.pi / 2)) / eta:.6f}")


if __name__ == "__main__":
    main()
