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
from ..orchestration.loop import advance, record_verify_result, start_session
from ..orchestration.roles import roles_for_stage
from ..orchestration.session import list_sessions, load_session


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
    governance_lifecycle = governance_sub.add_parser(
        "lifecycle", help="drive a task through the 8-stage development lifecycle graph"
    )
    lifecycle_sub = governance_lifecycle.add_subparsers(dest="lifecycle_command", required=True)
    lifecycle_start = lifecycle_sub.add_parser("start", help="open a new lifecycle session at INTAKE")
    lifecycle_start.add_argument("--task", required=True)
    lifecycle_start.add_argument("--workstream", required=True)
    lifecycle_start.add_argument("--risk", choices=["low", "medium", "high", "critical"], default="medium")
    lifecycle_start.add_argument("--evidence-json", default="{}", help="JSON object satisfying the intake stage's required fields")
    lifecycle_advance = lifecycle_sub.add_parser("advance", help="attempt a stage transition for a session")
    lifecycle_advance.add_argument("session_id")
    lifecycle_advance.add_argument("--to", required=True, help="target stage key (context/plan/change/verify/evidence/postflight/release) or blocked/superseded")
    lifecycle_advance.add_argument("--evidence-json", default="{}", help="JSON object satisfying the target stage's required fields")
    lifecycle_advance.add_argument("--gate-confirm", action="store_true", help="explicitly confirm the CURRENT stage's gate condition")
    lifecycle_verify_result = lifecycle_sub.add_parser(
        "verify-result", help="record a verify-stage pass/fail; fail routes back to change with a capped retry"
    )
    lifecycle_verify_result.add_argument("session_id")
    lifecycle_verify_result.add_argument("--passed", action="store_true")
    lifecycle_verify_result.add_argument("--evidence-json", default="{}")
    lifecycle_verify_result.add_argument("--gate-confirm", action="store_true")
    lifecycle_verify_result.add_argument("--max-retries", type=int, default=5)
    lifecycle_status = lifecycle_sub.add_parser("status", help="show a session's current stage and history")
    lifecycle_status.add_argument("session_id")
    lifecycle_sub.add_parser("list", help="list all lifecycle sessions")
    lifecycle_roles = lifecycle_sub.add_parser("roles", help="show which roles are bound to a stage")
    lifecycle_roles.add_argument("stage")
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
        if args.governance_command == "lifecycle":
            return _dispatch_lifecycle(root, args)
    return 2


def _dispatch_lifecycle(root: Path, args: argparse.Namespace) -> int:
    if args.lifecycle_command == "start":
        evidence = json.loads(args.evidence_json)
        result = start_session(root, task=args.task, workstream=args.workstream, risk_level=args.risk, evidence=evidence)
        print(json.dumps({"ok": result.ok, "session": result.session.to_dict(), "problems": list(result.problems)}, indent=2))
        return 0 if result.ok else 1
    if args.lifecycle_command == "advance":
        evidence = json.loads(args.evidence_json)
        gate_confirmations = {}
        try:
            session = load_session(root, args.session_id)
            from ..orchestration.lifecycle import load_lifecycle

            current_spec = load_lifecycle(root).stage_for_state(session.current_stage)
            if current_spec:
                gate_confirmations[current_spec.key] = args.gate_confirm
        except FileNotFoundError as exc:
            print(json.dumps({"ok": False, "problems": [str(exc)]}, indent=2))
            return 1
        result = advance(root, session_id=args.session_id, target=args.to, evidence=evidence, gate_confirmations=gate_confirmations)
        print(json.dumps({"ok": result.ok, "session": result.session.to_dict(), "problems": list(result.problems)}, indent=2))
        return 0 if result.ok else 1
    if args.lifecycle_command == "verify-result":
        evidence = json.loads(args.evidence_json)
        result = record_verify_result(
            root,
            session_id=args.session_id,
            passed=args.passed,
            evidence=evidence,
            gate_confirmations={"verify": args.gate_confirm},
            max_retries=args.max_retries,
        )
        print(json.dumps({"ok": result.ok, "session": result.session.to_dict(), "problems": list(result.problems)}, indent=2))
        return 0 if result.ok else 1
    if args.lifecycle_command == "status":
        session = load_session(root, args.session_id)
        print(json.dumps(session.to_dict(), indent=2))
        return 0
    if args.lifecycle_command == "list":
        sessions = list_sessions(root)
        print(json.dumps([s.to_dict() for s in sessions], indent=2))
        return 0
    if args.lifecycle_command == "roles":
        roles = roles_for_stage(root, args.stage)
        print(json.dumps([r.agent_id for r in roles], indent=2))
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
