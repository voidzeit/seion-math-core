"""Command-line entry point for a heterogeneous PMT report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .certificate import make_certificate


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate heterogeneous Theorem R scalar data")
    parser.add_argument("input", type=Path, help="JSON with operator_norms, defects and leaf_product")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--maxiter", type=int, default=300)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    data = json.loads(args.input.read_text(encoding="utf-8"))
    report = make_certificate(
        data["operator_norms"],
        data["defects"],
        data["leaf_product"],
        seed=args.seed,
        maxiter=args.maxiter,
    ).to_dict()
    encoded = json.dumps(report, indent=2, sort_keys=True)
    if args.output:
        args.output.write_text(encoded + "\n", encoding="utf-8", newline="\n")
    else:
        print(encoded)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

