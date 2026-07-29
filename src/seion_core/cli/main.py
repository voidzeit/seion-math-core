from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from ..certification.claims import claims_lint
from ..certification.report import summarize_runs, write_claims_report
from ..certification.runner import certify_config, run_profile


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="seion-core", description="Finite-dimensional SEION verification CLI")
    sub = parser.add_subparsers(dest="command", required=True)
    certify = sub.add_parser("certify", help="run a self-contained experiment certificate")
    certify.add_argument("config")
    suite = sub.add_parser("run-suite", help="run a named reproducibility profile")
    suite.add_argument("--profile", choices=["fast", "full", "extended"], default="fast")
    suite.add_argument("--device", default="auto")
    sub.add_parser("audit", help="audit claim and run registries")
    experiment = sub.add_parser("experiment", help="alias for certify")
    experiment.add_argument("config")
    compare = sub.add_parser("compare", help="summarize completed run artifacts")
    compare.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(__file__).resolve().parents[3]
    if args.command in {"certify", "experiment"}:
        path = certify_config(args.config, root)
        print(path)
        return 0
    if args.command == "run-suite":
        result = run_profile(args.profile, root, args.device)
        print(json.dumps(result, indent=2))
        return 0 if result.get("status") == "COMPLETE" else 1
    if args.command == "audit":
        result = {"claims": claims_lint(root), "runs": len(summarize_runs(root))}
        write_claims_report(root)
        print(json.dumps(result, indent=2))
        return 0 if result["claims"]["passed"] else 1
    if args.command == "compare":
        records = summarize_runs(root)
        print(json.dumps(records, indent=2) if args.json else f"completed artifact records: {len(records)}")
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
