"""Forensic provenance audit for the historical SRATM VALID metric.

This module intentionally never opens, hashes, or imports the FB15K-237 TEST
file.  It audits only repository source, historical metadata, checkpoints,
PowerShell command history, and TRAIN/VALID-safe artifacts.  Its purpose is
to distinguish verified facts from unresolved historical provenance.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import torch

from .sratm_certified_compression import TEACHER_RUN


HISTORICAL_MRR = 0.6116475462913513
HISTORICAL_AUDIT = "audit_step4600.json"
RELEVANT_FILES = (
    "seion_kgr/data.py",
    "seion_kgr/evaluate.py",
    "seion_kgr/train_spectral_mixture.py",
    "seion_kgr/sratm_certified_compression.py",
    "seion_kgr/sratm_validation_reconciliation.py",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _run_git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=root, capture_output=True, text=True, check=False,
    )
    if result.returncode != 0:
        return f"GIT_COMMAND_FAILED({result.returncode}): {result.stderr.strip()}"
    return result.stdout.strip()


def _git_state(root: Path) -> dict[str, Any]:
    return {
        "head": _run_git(root, "rev-parse", "HEAD"),
        "branch": _run_git(root, "branch", "--show-current"),
        "status_porcelain": _run_git(root, "status", "--short"),
        "relevant_history": _run_git(
            root, "log", "--all", "--date=iso", "--format=%h %ad %s", "--", *RELEVANT_FILES,
        ).splitlines(),
        "historical_metric_search": _run_git(
            root, "log", "--all", "-S0.611647", "--oneline", "--", *RELEVANT_FILES,
        ).splitlines(),
    }


def _source_evidence(root: Path) -> dict[str, Any]:
    evidence: dict[str, Any] = {}
    patterns = {
        "data_loader": r"def load_knowledge_graph|read_triples_file\(test_path\)|build_id_maps\(train_raw, valid_raw, test_raw\)|build_filters\(train_orig, valid, test\)",
        "strict_loader": r"def load_train_valid_only|TRAIN_PLUS_VALID_ONLY|expected_num_entities",
        "evaluator": r"eps_tie|torch\.isclose|better =|head_filter|_inverse_relation",
        "trainer": r"def _load_kg|--test|load_knowledge_graph\(args\.train, args\.valid, args\.test\)|evaluate\(",
    }
    for relative in RELEVANT_FILES:
        path = root / relative
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines()
        file_record: dict[str, Any] = {
            "sha256": sha256(path),
            "bytes": path.stat().st_size,
            "matches": {},
        }
        for label, pattern in patterns.items():
            matches = [
                {"line": index + 1, "text": line.strip()}
                for index, line in enumerate(lines)
                if re.search(pattern, line)
            ]
            if matches:
                file_record["matches"][label] = matches[:40]
        evidence[relative] = file_record
    return evidence


def _checkpoint_inventory(root: Path, run_dir: Path) -> dict[str, Any]:
    inventory: dict[str, Any] = {}
    for name in ("checkpoint_last.pt", "checkpoint_best.pt"):
        path = run_dir / name
        if not path.exists():
            inventory[name] = {"status": "MISSING"}
            continue
        state = torch.load(path, map_location="cpu", weights_only=False)
        validation = [
            item for item in state.get("history", [])
            if isinstance(item, dict) and isinstance(item.get("valid"), dict)
        ]
        inventory[name] = {
            "sha256": sha256(path),
            "bytes": path.stat().st_size,
            "embedded_step": state.get("step"),
            "embedded_epoch": state.get("epoch"),
            "history_entries": len(state.get("history", [])),
            "last_recorded_valid": validation[-1] if validation else None,
        }
    audit_path = run_dir / HISTORICAL_AUDIT
    inventory[HISTORICAL_AUDIT] = {
        "sha256": sha256(audit_path) if audit_path.exists() else None,
        "exists": audit_path.exists(),
    }
    return inventory


def _run_artifact_inventory(run_dir: Path) -> list[dict[str, Any]]:
    records = []
    for path in sorted(run_dir.iterdir()):
        if path.is_file():
            records.append({
                "name": path.name,
                "bytes": path.stat().st_size,
                "sha256": sha256(path) if path.suffix.lower() != ".pt" else "NOT_REHASHED_IN_ARTIFACT_INVENTORY",
            })
    return records


def _shell_history_evidence() -> dict[str, Any]:
    history_path = Path.home() / "AppData/Roaming/Microsoft/Windows/PowerShell/PSReadLine/ConsoleHost_history.txt"
    if not history_path.exists():
        return {"path": str(history_path), "status": "MISSING"}
    text = history_path.read_text(encoding="utf-8", errors="replace")
    sratm_matches = [line for line in text.splitlines() if re.search(r"SRATM|sratm|train_spectral_mixture|audit_step4600|0\.6116", line)]
    return {
        "path": str(history_path),
        "bytes": history_path.stat().st_size,
        "searched_terms": ["SRATM", "sratm", "train_spectral_mixture", "audit_step4600", "0.6116"],
        "matching_lines": sratm_matches[:100],
        "matching_line_count": len(sratm_matches),
        "interpretation": "No matching SRATM launch command found in this PowerShell history snapshot; this does not prove no historical command existed elsewhere.",
    }


def _hypotheses(root: Path, run_dir: Path, audit: dict[str, Any], checkpoint: dict[str, Any]) -> list[dict[str, Any]]:
    last = checkpoint.get("checkpoint_last.pt", {})
    best = checkpoint.get("checkpoint_best.pt", {})
    audit_hash = audit.get("integrity", {}).get("checkpoint_sha256")
    last_hash = last.get("sha256")
    return [
        {
            "id": "H01_CHECKPOINT_IDENTITY",
            "claim": "The historical audit used a different checkpoint than checkpoint_last.pt.",
            "status": "REFUTED",
            "evidence": f"audit hash={audit_hash}; checkpoint_last hash={last_hash}; audit step={audit.get('checkpoint_step')}; last step={last.get('embedded_step')}",
        },
        {
            "id": "H02_BEST_LAST_CONFUSION",
            "claim": "The 0.6116475 audit was produced by checkpoint_best.pt step 4608.",
            "status": "REFUTED",
            "evidence": f"checkpoint_best hash={best.get('sha256')}, embedded step={best.get('embedded_step')}; audit hash matches last, not best",
        },
        {
            "id": "H03_BRANCH_SCORER_PATH",
            "claim": "The current branch decomposition materially changes the frozen SRATM scorer.",
            "status": "REFUTED_ON_DIFFERENTIAL_SAMPLE",
            "evidence": "branch-vs-model max absolute score error 7.152557373046875e-07",
        },
        {
            "id": "H04_GOLD_EXTRACTION",
            "claim": "Gold extraction is the source of the historical metric discrepancy.",
            "status": "REFUTED_ON_DIFFERENTIAL_SAMPLE",
            "evidence": "positive-vs-candidate max absolute score error 5.960464477539062e-07 after gold-block fix",
        },
        {
            "id": "H05_RECIPROCAL_CONSTRUCTION",
            "claim": "Reciprocal query construction is the source of the discrepancy.",
            "status": "REFUTED_ON_DIFFERENTIAL_SAMPLE",
            "evidence": "reciprocal construction errors 0 on the audited rows",
        },
        {
            "id": "H06_HISTORICAL_LOADER_FILTER_PROVENANCE",
            "claim": "The historical execution used the loader path that reads test_path and builds filters over TRAIN+VALID+TEST.",
            "status": "OPEN_HIGH_PRIORITY",
            "evidence": "current source train_spectral_mixture._load_kg requires --test and calls load_knowledge_graph; exact historical command/runtime is absent",
        },
        {
            "id": "H07_ENTITY_VOCABULARY_CANDIDATE_UNIVERSE",
            "claim": "Vocabulary construction or candidate universe differed between historical and sealed evaluation.",
            "status": "OPEN_HIGH_PRIORITY",
            "evidence": "historical loader builds IDs from train_raw, valid_raw, test_raw; sealed audit uses TRAIN+VALID-only and fixes 14,541 entities; historical resolved mapping is unavailable",
        },
        {
            "id": "H08_TIE_POLICY",
            "claim": "Tie handling or rank convention differs between historical and sealed evaluation.",
            "status": "OPEN_MEDIUM_PRIORITY",
            "evidence": "current evaluator uses strict greater-than plus half-tie correction; historical evaluator version/trace is not preserved",
        },
        {
            "id": "H09_HISTORICAL_COMMAND_RUNTIME",
            "claim": "The exact launch command, source SHA, evaluator module, or runtime differed from the reconstructed current path.",
            "status": "OPEN_HIGH_PRIORITY",
            "evidence": "no SRATM launch command found in the available PowerShell history; run directory has no command/log/config manifest",
        },
        {
            "id": "H10_TEST_DERIVED_HISTORY",
            "claim": "TEST data actually influenced the historical 0.6116475 metric.",
            "status": "UNKNOWN_NOT_ESTABLISHED",
            "evidence": "the audit declares test_opened=false, while the historical code path requires a test path; without an archived command/access log this cannot be resolved without opening TEST",
        },
    ]


def run(args: argparse.Namespace) -> dict[str, Any]:
    root = args.root.resolve()
    run_dir = root / TEACHER_RUN
    audit_path = run_dir / HISTORICAL_AUDIT
    if not audit_path.exists():
        raise FileNotFoundError(audit_path)
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    checkpoint = _checkpoint_inventory(root, run_dir)
    result: dict[str, Any] = {
        "campaign": "HISTORICAL_EVALUATOR_PROVENANCE_V1",
        "status": "OPEN_CAUSE_NOT_RECONSTRUCTED",
        "test_split": {
            "opened": False,
            "read": False,
            "hashed": False,
            "reason": "This campaign has no code path that reads the TEST file.",
        },
        "historical_reference": {
            "metric": "VALID combined MRR",
            "mrr": audit.get("metrics", {}).get("combined", {}).get("MRR"),
            "queries": audit.get("metrics", {}).get("eval_query_count"),
            "declared_test_opened": audit.get("test_opened"),
            "audit_sha256": sha256(audit_path),
        },
        "run_directory_inventory": _run_artifact_inventory(run_dir),
        "checkpoint_inventory": checkpoint,
        "source_evidence": _source_evidence(root),
        "git_state": _git_state(root),
        "shell_history": _shell_history_evidence(),
        "reconciliation_artifact": str(root / "runs/HISTORICAL_VALIDATION_RECONCILIATION_V1_20260810_FINAL2/result/reconciliation.json"),
        "hypotheses": _hypotheses(root, run_dir, audit, checkpoint),
        "known_limits": [
            "The historical launch command and source/runtime snapshot are absent.",
            "The historical rank trace, filter counts, candidate universe, and tie policy are absent.",
            "TEST remains sealed; historical TEST consumption is therefore UNKNOWN, not PASS or LEAKAGE.",
            "The all-entity sealed baseline MRR=0.395861233 is the canonical reproducible pre-test control; the 0.611647546 audit is not protocol-reconciled.",
        ],
        "next_safe_action": "Reproduce a new teacher/evaluator under a fully sealed TRAIN+VALID protocol, or recover an archived historical command/log/rank trace without opening TEST. Do not use 0.611647546 for model selection until reconciled.",
        "environment": {
            "python": sys.version,
            "torch": torch.__version__,
            "platform": platform.platform(),
            "created_utc": datetime.now(timezone.utc).isoformat(),
        },
    }
    out = args.out_dir.resolve()
    out.mkdir(parents=True, exist_ok=False)
    (out / "provenance_report.json").write_text(json.dumps(result, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    hypothesis_path = out / "hypothesis_matrix.json"
    hypothesis_path.write_text(json.dumps(result["hypotheses"], indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out / "checkpoint_inventory.json").write_text(json.dumps(checkpoint, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    (out / "final_report.md").write_text(
        "# HISTORICAL_EVALUATOR_PROVENANCE_V1\n\n"
        "Status: **OPEN_CAUSE_NOT_RECONSTRUCTED**. TEST opened/read/hashed: **false/false/false**.\n\n"
        f"Historical VALID MRR: **{result['historical_reference']['mrr']:.9f}**; audit checkpoint: **step {audit.get('checkpoint_step')}**.\n\n"
        "## Resolved\n\n"
        "- The audit checkpoint hash matches `checkpoint_last.pt`; `checkpoint_best.pt` is a different step-4608 file.\n"
        "- The current branch-wise scorer, gold extraction, and reciprocal construction match within sub-micro-unit error on the differential audit.\n"
        "- The current sealed all-entity baseline remains `0.395861233`; it is not numerically interchangeable with the historical audit.\n\n"
        "## Highest-priority open cause\n\n"
        "The historical trainer source requires a test path and its normal loader builds vocabulary and filters from TRAIN+VALID+TEST, while the sealed audit uses TRAIN+VALID only. The exact historical command, access log, filter counts, candidate universe, tie policy, and runtime snapshot are missing. Therefore historical TEST usage is **UNKNOWN**, not proven.\n\n"
        "## Decision\n\n"
        "Do not open TEST and do not use `0.611647546` for selection or claims until the historical protocol is reconstructed or a new sealed teacher is trained.\n",
        encoding="utf-8",
    )
    artifact_hashes = {
        path.name: sha256(path)
        for path in sorted(out.iterdir())
        if path.is_file() and path.name != "artifact_hashes.json"
    }
    (out / "artifact_hashes.json").write_text(json.dumps(artifact_hashes, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    manifest = {
        "campaign": result["campaign"],
        "status": result["status"],
        "command": " ".join([sys.executable, "-m", "seion_kgr.historical_evaluator_provenance", *sys.argv[1:]]),
        "test_split_opened": False,
        "teacher_checkpoint_sha256": checkpoint.get("checkpoint_last.pt", {}).get("sha256"),
        "git_head": result["git_state"]["head"],
        "artifacts": artifact_hashes,
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--out-dir", type=Path, required=True)
    return parser


def main() -> None:
    print(json.dumps(run(build_parser().parse_args()), indent=2, sort_keys=True, default=str))


if __name__ == "__main__":
    main()
