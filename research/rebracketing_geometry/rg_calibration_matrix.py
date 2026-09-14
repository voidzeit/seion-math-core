"""Calibration matrix: make the search answer five questions we already know.

The k=2 table has six cells and only one open:

              free            same-mu
    J          2                 2
    H          2                 2
    S       Sigma_2              ?

So before asking the sixth, the same pipeline is required to recover the five
analytic ones. Two numbers summarize that:

    Gamma = min over the five KNOWN cells of (attained / known)
    G_S   = Gamma - gamma_S^same-mu

`Gamma` is a single health score for the search, taken as a MINIMUM so that a
campaign cannot quietly report only the controls that happened to work. `G_S`
is what makes a deficit in the open cell readable: a `gamma_S^same = 0.90` means
one thing when `Gamma = 0.997` (the gap dwarfs the search's demonstrated error
on problems whose answers are known) and nothing at all when `Gamma = 0.94`.

The open cell is never folded into `Gamma`, and is printed separately as
UNKNOWN TARGET, because its ceiling `Sigma_2` is an upper bound that same-mu is
not known to attain.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
GATE = 0.99
KNOWN = {("J", "free"), ("J", "same_law_same_P"),
         ("H", "free"), ("H", "same_law_same_P"), ("S", "free")}
OPEN = ("S", "same_law_same_P")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", default=str(HERE / "cal2_diff_v1.json"))
    args = parser.parse_args()

    runs = json.loads(Path(args.json).read_text(encoding="utf-8"))["runs"]
    best = defaultdict(float)
    where = {}
    for row in runs:
        key = (row["objective"], row["class"])
        ratio = row["best"] / row["ceiling"]
        if ratio > best[key]:
            best[key], where[key] = ratio, row

    print(f"{len(runs)} cells\n")
    print(f"{'objective':>10} {'class':>18} {'attained/known':>15} "
          f"{'at':>22}")
    for key in sorted(KNOWN):
        row = where.get(key)
        if row is None:
            continue
        location = f"eta {row['eta']:.3f} D{row['dim']}r{row['rank']}"
        print(f"{key[0]:>10} {key[1]:>18} {best[key]:15.6f} "
              f"{location:>22}")

    known = [best[k] for k in sorted(KNOWN) if k in best]
    gamma = min(known) if known else float("nan")
    print(f"\n  Gamma_calibration = min over known cells = {gamma:.6f}"
          f"   -> {'PASS' if gamma >= GATE else 'FAIL'} (gate {GATE})")

    if OPEN in best:
        gamma_s = best[OPEN]
        print(f"\n{'':>10} {'UNKNOWN TARGET':>18} {gamma_s:15.6f}"
              f"   S attained / Sigma_2")
        print(f"  G_S = Gamma - gamma_S^same = {gamma - gamma_s:+.6f}")
        if gamma < GATE:
            print("  -> UNINTERPRETABLE: the search has not recovered the "
                  "cells whose answers are known.")
        elif gamma - gamma_s > 0.02:
            print("  -> the deficit exceeds the search's demonstrated error on "
                  "known problems; worth investigating as geometry.")
        else:
            print("  -> no deficit beyond the search's own error: consistent "
                  "with S_2^same-mu = Sigma_2.")


if __name__ == "__main__":
    main()
