from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from ..certification.claims import claims_lint
from ..certification.report import summarize_runs, write_claims_report
from ..certification.runner import certify_config, run_profile
from ..governance.actions import evaluate_action
from ..governance.audit import audit_governance
from ..governance.context import build_context_pack
from ..governance.postflight import record_postflight
from ..governance.runs import deduplicate_runs


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
    governance = sub.add_parser("governance", help="repository-local governance and memory controls")
    governance_sub = governance.add_subparsers(dest="governance_command", required=True)
    governance_audit = governance_sub.add_parser("audit", help="audit memory, claims, artifacts, and paper gates")
    governance_audit.add_argument("--strict", action="store_true")
    governance_audit.add_argument("--json", action="store_true")
    governance_context = governance_sub.add_parser("context", help="compile a bounded recovery context pack")
    governance_context.add_argument("--task", required=True)
    governance_context.add_argument("--output")
    governance_context.add_argument("--extra", action="append", default=[])
    governance_dedupe = governance_sub.add_parser("dedupe-runs", help="build a non-destructive unique-run index")
    governance_dedupe.add_argument("--output")
    governance_dedupe.add_argument("--json", action="store_true")
    governance_gate = governance_sub.add_parser("gate", help="evaluate a governed action")
    governance_gate.add_argument("action")
    governance_gate.add_argument("--risk", choices=["low", "medium", "high", "critical"], default="medium")
    governance_gate.add_argument("--evidence", choices=["declared", "observed", "verified", "approved"], default="declared")
    governance_gate.add_argument("--human-approval", action="store_true")
    governance_gate.add_argument("--check", action="append", default=[], help="pass a required check name")
    governance_postflight = governance_sub.add_parser("postflight", help="append a durable session handoff")
    governance_postflight.add_argument("--task", required=True)
    governance_postflight.add_argument("--summary", required=True)
    governance_postflight.add_argument("--outcome", default="completed")
    governance_postflight.add_argument("--validation", required=True)
    governance_postflight.add_argument("--command", dest="run_command", required=True)
    governance_postflight.add_argument("--changed-file", action="append", default=[])
    governance_postflight.add_argument("--limitation", action="append", default=[])
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
        result = {
            "claims": claims_lint(root),
            "runs": len(summarize_runs(root)),
            "governance": audit_governance(root),
        }
        write_claims_report(root)
        print(json.dumps(result, indent=2))
        return 0 if result["claims"]["passed"] and result["governance"]["passed"] else 1
    if args.command == "compare":
        records = summarize_runs(root)
        print(json.dumps(records, indent=2) if args.json else f"completed artifact records: {len(records)}")
        return 0
    if args.command == "governance":
        if args.governance_command == "audit":
            result = audit_governance(root, strict=args.strict)
            print(json.dumps(result, indent=2))
            return 0 if result.get("passed") else 1
        if args.governance_command == "context":
            path = build_context_pack(root, task=args.task, output=args.output, extra_files=args.extra)
            print(str(path))
            return 0
        if args.governance_command == "dedupe-runs":
            result = deduplicate_runs(root, output=args.output)
            print(json.dumps(result, indent=2) if args.json else str(result["output"]))
            return 0
        if args.governance_command == "gate":
            checks = {name: True for name in args.check}
            result = evaluate_action(
                root,
                action=args.action,
                risk=args.risk,
                evidence_authority=args.evidence,
                human_approval=args.human_approval,
                checks=checks,
            )
            print(json.dumps(result, indent=2))
            return 0 if result["allowed"] else 1
        if args.governance_command == "postflight":
            result = record_postflight(
                root,
                task=args.task,
                summary=args.summary,
                outcome=args.outcome,
                validation=args.validation,
                command=args.run_command,
                changed_files=args.changed_file,
                limitations=args.limitation,
            )
            print(json.dumps(result, indent=2))
            return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
