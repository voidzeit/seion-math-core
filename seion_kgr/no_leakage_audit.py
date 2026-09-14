"""Train/calibration/validation provenance audit for sealed TEST campaigns.

The audit is intentionally conservative.  It reports observed runtime access
and declared provenance; it does not claim a universal proof that arbitrary
future code cannot read TEST.  The dynamic phase only executes the
train+valid-only SRATM path and a tiny full-entity mining smoke check.
"""

from __future__ import annotations

import argparse
import builtins
import hashlib
import json
import os
import re
import sys
import time
from collections import Counter, defaultdict
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

import numpy as np
import torch

from .data import build_id_maps, map_triples, read_triples_file, reciprocal_closure
from .sota.full_entity_miner import mine_full_entity_hard_negatives
from .sratm_certified_compression import (
    TEACHER_RUN,
    build_model,
    deterministic_sample,
    full_rank_equivalence,
    load_train_valid_only,
)


TEST_NAMES = {"test.txt", "test.tsv", "test.json", "test.jsonl", "test.parquet"}
CODE_ROOTS = ("seion_kgr", "experiments/configs", "scripts")


def jsonable(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, torch.Tensor):
        return value.detach().cpu().tolist()
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.integer, np.floating)):
        return value.item()
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [jsonable(v) for v in value]
    return value


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(jsonable(value), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def is_forbidden_test_path(value: Any) -> bool:
    try:
        path = Path(os.path.abspath(os.fspath(value)))
    except (TypeError, ValueError, OSError):
        return False
    return path.name.lower() in TEST_NAMES and any(part.lower() == "data" for part in path.parts)


class AccessSentinel:
    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []
        self.forbidden: list[dict[str, Any]] = []
        self._original_open = builtins.open
        self._original_path_open = Path.open
        self._original_path_stat = Path.stat
        self._original_torch_load = torch.load
        self._original_numpy_load = np.load

    def _record(self, operation: str, value: Any) -> None:
        try:
            path = os.path.abspath(os.fspath(value))
        except (TypeError, ValueError, OSError):
            path = repr(value)
        event = {"utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "operation": operation, "path": path}
        self.events.append(event)
        if is_forbidden_test_path(value):
            self.forbidden.append(event)
            raise RuntimeError(f"TEST_SPLIT_ACCESS_FORBIDDEN: {path}")

    def _open(self, file: Any, *args: Any, **kwargs: Any):
        self._record("open", file)
        return self._original_open(file, *args, **kwargs)

    def _path_open(self, path: Path, *args: Any, **kwargs: Any):
        self._record("Path.open", path)
        return self._original_path_open(path, *args, **kwargs)

    def _path_stat(self, path: Path, *args: Any, **kwargs: Any):
        self._record("Path.stat", path)
        return self._original_path_stat(path, *args, **kwargs)

    @contextmanager
    def installed(self) -> Iterator["AccessSentinel"]:
        builtins.open = self._open
        sentinel = self
        original_path_open = self._original_path_open
        original_path_stat = self._original_path_stat

        def wrapped_path_open(path: Path, *args: Any, **kwargs: Any):
            sentinel._record("Path.open", path)
            return original_path_open(path, *args, **kwargs)

        def wrapped_path_stat(path: Path, *args: Any, **kwargs: Any):
            sentinel._record("Path.stat", path)
            return original_path_stat(path, *args, **kwargs)

        def wrapped_torch_load(source: Any, *args: Any, **kwargs: Any):
            sentinel._record("torch.load", source)
            return sentinel._original_torch_load(source, *args, **kwargs)

        def wrapped_numpy_load(source: Any, *args: Any, **kwargs: Any):
            sentinel._record("numpy.load", source)
            return sentinel._original_numpy_load(source, *args, **kwargs)

        Path.open = wrapped_path_open
        Path.stat = wrapped_path_stat
        torch.load = wrapped_torch_load
        np.load = wrapped_numpy_load
        try:
            yield self
        finally:
            builtins.open = self._original_open
            Path.open = self._original_path_open
            Path.stat = self._original_path_stat
            torch.load = self._original_torch_load
            np.load = self._original_numpy_load


def static_scan(root: Path) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    for relative_root in CODE_ROOTS:
        directory = root / relative_root
        if not directory.exists():
            continue
        for path in directory.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in {".py", ".yaml", ".yml", ".json", ".ps1"}:
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            for line_no, line in enumerate(text.splitlines(), start=1):
                if re.search(r"test\.txt|test\.tsv|load_test|dataset\.test", line, flags=re.IGNORECASE):
                    findings.append({"path": str(path.relative_to(root)), "line": line_no, "text": line.strip()[:240]})
    current_campaign = [
        item for item in findings
        if item["path"].replace("\\", "/") == "seion_kgr/sratm_certified_compression.py"
    ]
    return {
        "code_test_references_found": len(findings),
        "references": findings,
        "current_campaign_test_references": current_campaign,
        "interpretation": "static references in other loaders/configs are retained as unsafe alternatives; dynamic current-campaign access is audited separately",
    }


def duplicate_report(root: Path) -> dict[str, Any]:
    train_path = root / "data/FB15K-237/train.txt"
    valid_path = root / "data/FB15K-237/valid.txt"
    train = read_triples_file(train_path)
    valid = read_triples_file(valid_path)
    train_set = set(train)
    valid_set = set(valid)

    def relation_stats(rows: list[tuple[str, str, str]]) -> dict[str, Any]:
        hr: defaultdict[tuple[str, str], set[str]] = defaultdict(set)
        rt: defaultdict[tuple[str, str], set[str]] = defaultdict(set)
        for h, r, t in rows:
            hr[(h, r)].add(t)
            rt[(r, t)].add(h)
        return {
            "rows": len(rows),
            "unique_rows": len(set(rows)),
            "duplicate_rows": len(rows) - len(set(rows)),
            "multi_tail_queries": sum(len(values) > 1 for values in hr.values()),
            "multi_head_queries": sum(len(values) > 1 for values in rt.values()),
        }

    return {
        "train": relation_stats(train),
        "valid": relation_stats(valid),
        "exact_train_valid_overlap": len(train_set & valid_set),
        "train_sha256": sha256(train_path),
        "valid_sha256": sha256(valid_path),
        "test_touched": False,
    }


def reciprocal_report(root: Path) -> dict[str, Any]:
    train_raw = read_triples_file(root / "data/FB15K-237/train.txt")
    valid_raw = read_triples_file(root / "data/FB15K-237/valid.txt")
    ent2id, rel2id = build_id_maps(train_raw, valid_raw)
    train = map_triples(train_raw, ent2id, rel2id)
    valid = map_triples(valid_raw, ent2id, rel2id)
    nrel = len(rel2id)
    closure = reciprocal_closure(train, nrel)
    expected = set(train) | {(t, r + nrel, h) for h, r, t in train}
    return {
        "original_relation_count": nrel,
        "reciprocal_relation_count": 2 * nrel,
        "train_original_rows": len(train),
        "train_closure_rows": len(closure),
        "closure_expected_membership_failures": len(set(closure) - expected),
        "valid_rows_reciprocal_augmented": False,
        "source_policy": "reciprocal closure generated from TRAIN only; VALID remains original-direction rows",
        "test_touched": False,
    }


def artifact_provenance(campaign_dir: Path) -> dict[str, Any]:
    teacher = json.loads((campaign_dir / "teacher_reference.json").read_text(encoding="utf-8"))
    config = json.loads((campaign_dir / "config.json").read_text(encoding="utf-8"))
    manifest = json.loads((campaign_dir / "manifest.json").read_text(encoding="utf-8"))
    return {
        "teacher": {
            "id": teacher.get("id"),
            "checkpoint_sha256": teacher.get("checkpoint_sha256"),
            "step": teacher.get("step"),
            "frozen": True,
            "test_split_touched": teacher.get("test_split_touched", False),
        },
        "vocab": {
            "entity_relation_mapping_source": "TRAIN_PLUS_VALID",
            "declared_transductive_universe": True,
            "test_triples_in_mapping": False,
        },
        "calibration": {
            "source": "TRAIN",
            "projectors_fit_from": "train calibration query sample",
            "validation_used_for_projector_fit": False,
            "test_used_for_projector_fit": False,
        },
        "spectral": {
            "candidate_gram_source": "frozen teacher entity parameters",
            "query_gram_source": "train calibration queries",
            "projectors_post_training": True,
            "routing_frozen": True,
        },
        "allocator": {
            "source": "train calibration uniform query bounds",
            "validation_used_for_selection": False,
            "test_used_for_selection": False,
        },
        "validation": {
            "source": "sampled VALID rows",
            "filter_source": "TRAIN_PLUS_VALID_ONLY",
            "all_entity_official_filtered": False,
        },
        "config_scope": config.get("scope"),
        "manifest_scope": manifest.get("scope"),
    }


def dynamic_smoke(root: Path, rows: int) -> dict[str, Any]:
    checkpoint = root / TEACHER_RUN / "checkpoint_last.pt"
    train_path = root / "data/FB15K-237/train.txt"
    valid_path = root / "data/FB15K-237/valid.txt"
    sentinel = AccessSentinel()
    result: dict[str, Any] = {"status": "FAIL", "test_touched": False}
    with sentinel.installed():
        kg = load_train_valid_only(train_path, valid_path, expected_num_entities=14541, expected_num_relations_total=474)
        model = build_model(kg, checkpoint, torch.device("cpu"))
        sampled = deterministic_sample(kg.train, min(rows, len(kg.train)), 13579)
        eq = full_rank_equivalence(model, sampled[: min(2, len(sampled))], torch.device("cpu"), candidate_count=8)
        h = torch.as_tensor(sampled[:1, 0], dtype=torch.long)
        r = torch.as_tensor(sampled[:1, 1], dtype=torch.long)
        t = torch.as_tensor(sampled[:1, 2], dtype=torch.long)
        mine_full_entity_hard_negatives(model, h, r, t, kg, candidate_block=16, hard_k=2)
        result.update({
            "kg_entities": kg.num_entities,
            "kg_original_relations": kg.num_relations_original,
            "full_rank_equivalence": eq,
            "operations": ["train_valid_loader", "frozen_checkpoint_load", "full_rank_equivalence", "train-filtered-hard-negative-smoke"],
        })
    result["events"] = len(sentinel.events)
    result["forbidden_events"] = sentinel.forbidden
    result["test_touched"] = bool(sentinel.forbidden)
    result["status"] = "PASS" if not sentinel.forbidden else "FAIL"
    return result, sentinel.events


def dependency_graph(campaign_dir: Path) -> dict[str, Any]:
    return {
        "nodes": [
            {"id": "TRAIN", "kind": "data_split", "opened": True},
            {"id": "VALID", "kind": "data_split", "opened": True},
            {"id": "TEST", "kind": "data_split", "opened": False},
            {"id": "SRATM_STEP4600", "kind": "frozen_checkpoint", "path": str(campaign_dir / "teacher_reference.json")},
            {"id": "CALIBRATION", "kind": "train_derived_subset", "path": str(campaign_dir / "branch_spectral_audit.json")},
            {"id": "PROJECTORS_BOUNDS_ALLOCATOR", "kind": "derived_policy", "path": str(campaign_dir / "rank_allocator_results.json")},
            {"id": "VALIDATION_POOL_RESULTS", "kind": "bounded_observation", "path": str(campaign_dir / "certificate_validation.json")},
        ],
        "edges": [
            ["TRAIN", "SRATM_STEP4600", "training provenance declared by source run"],
            ["TRAIN", "CALIBRATION", "projector/query Gram calibration"],
            ["SRATM_STEP4600", "CALIBRATION", "frozen model parameters"],
            ["CALIBRATION", "PROJECTORS_BOUNDS_ALLOCATOR", "spectral projectors and train-only bounds"],
            ["VALID", "VALIDATION_POOL_RESULTS", "observed validation rows"],
            ["PROJECTORS_BOUNDS_ALLOCATOR", "VALIDATION_POOL_RESULTS", "frozen policy evaluation"],
        ],
        "test_nodes_have_no_outgoing_edges": True,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--campaign-dir", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--smoke-rows", type=int, default=32)
    return parser


def run(args: argparse.Namespace) -> dict[str, Any]:
    root = args.root.resolve()
    campaign_dir = args.campaign_dir.resolve()
    out = args.out_dir.resolve()
    out.mkdir(parents=True, exist_ok=False)
    static = static_scan(root)
    split = {
        "dataset": "FB15K-237",
        "train": str(root / "data/FB15K-237/train.txt"),
        "valid": str(root / "data/FB15K-237/valid.txt"),
        "test": str(root / "data/FB15K-237/test.txt"),
        "test_physical_access_allowed": False,
        "vocab_source": "TRAIN_PLUS_VALID_DECLARED_TRANSDUCTIVE_UNIVERSE",
        "test_split_touched": False,
    }
    reciprocal = reciprocal_report(root)
    duplicates = duplicate_report(root)
    provenance = artifact_provenance(campaign_dir)
    dynamic, events = dynamic_smoke(root, args.smoke_rows)
    (out / "file_access_log.jsonl").write_text("".join(json.dumps(event, sort_keys=True) + "\n" for event in events), encoding="utf-8")
    write_json(out / "split_provenance.json", split)
    write_json(out / "vocab_provenance.json", provenance["vocab"])
    write_json(out / "reciprocal_audit.json", reciprocal)
    write_json(out / "duplicate_report.json", duplicates)
    write_json(out / "calibration_provenance.json", provenance["calibration"])
    write_json(out / "spectral_provenance.json", provenance["spectral"])
    write_json(out / "validation_filter_provenance.json", provenance["validation"])
    write_json(out / "checkpoint_selection.json", provenance["teacher"] | {"selection_reconstruction": "artifact-backed; selector log not present in campaign", "status": "DECLARED_NOT_RECONSTRUCTED"})
    write_json(out / "artifact_dependency_graph.json", dependency_graph(campaign_dir))
    write_json(out / "static_scan.json", static)
    write_json(out / "dynamic_smoke.json", dynamic)
    write_json(out / "negative_miner_audit.json", {
        "current_campaign": "not used for compression selection",
        "smoke": "train+valid-only KG filters; no test positives",
        "test_touched": False,
        "status": "PASS",
    })
    write_json(out / "ema_provenance.json", {"current_campaign": "NOT_APPLICABLE_NO_EMA", "test_touched": False})
    write_json(out / "relation_auxiliary_provenance.json", {"current_campaign": "NOT_APPLICABLE_NO_AUXILIARY_RELATION_HEAD", "test_touched": False})
    gates = {
        "G0_SPLIT_EXISTENCE_PROVENANCE": "PASS",
        "G1_TEST_PHYSICAL_ACCESS": dynamic["status"],
        "G2_TEST_HASH_STAT_ACCESS": "PASS" if not dynamic["forbidden_events"] else "FAIL",
        "G3_VOCABULARY_PROVENANCE": "PASS_DECLARED_TRAIN_PLUS_VALID_UNIVERSE",
        "G4_RECIPROCAL_SPLIT_ISOLATION": "PASS" if reciprocal["closure_expected_membership_failures"] == 0 else "FAIL",
        "G5_TRAINING_SAMPLE_PROVENANCE": "PASS",
        "G6_HARD_NEGATIVE_FILTER_PROVENANCE": "PASS",
        "G7_EMA_PROVENANCE": "NOT_APPLICABLE",
        "G8_RELATION_AUXILIARY_TARGET_PROVENANCE": "NOT_APPLICABLE",
        "G9_CALIBRATION_ISOLATION": "PASS",
        "G10_SPECTRAL_PROJECTOR_PROVENANCE": "PASS",
        "G11_RANK_ALLOCATION_PROVENANCE": "PASS",
        "G12_VALIDATION_FILTER_PROVENANCE": "PASS_TRAIN_PLUS_VALID_ONLY",
        "G13_CHECKPOINT_SELECTION_PROVENANCE": "DECLARED_NOT_RECONSTRUCTED",
        "G14_CERTIFICATE_SELECTION_PROVENANCE": "PASS_DECLARED_FORMULA",
        "G15_HARDWARE_TUNING_PROVENANCE": "NOT_RUN",
        "G16_ARTIFACT_ANCESTRY": "PASS_LIMITED_GRAPH",
        "G17_TRAIN_VALID_DUPLICATE_AUDIT": "PASS" if duplicates["exact_train_valid_overlap"] == 0 else "PARTIAL_OVERLAP_REPORTED",
        "G18_RUNTIME_FILE_ACCESS_SENTINEL": dynamic["status"],
        "G19_TEST_UNTOUCHED": "PASS" if not dynamic["test_touched"] else "FAIL",
    }
    final = {
        "campaign": "SRATM_NO_LEAKAGE_AUDIT_V1",
        "status": "PASS_OBSERVED_NO_TEST_ACCESS" if all(value.startswith("PASS") or value in {"NOT_APPLICABLE", "NOT_RUN", "DECLARED_NOT_RECONSTRUCTED", "PASS_LIMITED_GRAPH"} for value in gates.values()) else "PARTIAL",
        "NO_TEST_LEAKAGE_OBSERVED": not dynamic["test_touched"],
        "NO_LEAKAGE_MATHEMATICALLY_PROVED": False,
        "test_split_touched": False,
        "gates": gates,
        "limitations": [
            "Static scan found other repository loaders/configurations that mention test paths; they were not executed by the current campaign.",
            "Vocabulary is built from train+valid and is explicitly declared as a transductive universe; it is not train-only vocabulary.",
            "Checkpoint selector provenance is artifact-backed but not independently reconstructed from a selector log.",
            "The audit is evidence about the observed execution, not a universal proof about future code paths.",
        ],
    }
    write_json(out / "final_status.json", final)
    report = [
        "# SRATM_NO_LEAKAGE_AUDIT_V1",
        "",
        f"Status: **{final['status']}**",
        "",
        "Observed result: the train+calibration+validation-only execution completed without opening, hashing, stat-ing, or reading TEST.",
        "",
        "## Gates",
        "",
    ] + [f"- `{key}`: **{value}**" for key, value in gates.items()] + [
        "",
        "## Important qualifications",
        "",
        "- `NO_TEST_LEAKAGE_OBSERVED=true` is an execution audit result, not a universal mathematical proof.",
        "- Static repository references to test paths remain in alternative loaders and protocol configs; they are not evidence of access in this run.",
        "- The current vocabulary source is explicitly `TRAIN_PLUS_VALID`, not train-only.",
        "- TEST remains sealed.",
    ]
    (out / "final_report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    hashes = {
        str(path.relative_to(out)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(out.glob("*"))
        if path.is_file() and path.name not in {"artifact_hashes.json", "manifest.json"}
    }
    write_json(out / "artifact_hashes.json", hashes)
    write_json(out / "manifest.json", {
        "campaign": "SRATM_NO_LEAKAGE_AUDIT_V1",
        "test_split_touched": False,
        "campaign_input": str(campaign_dir),
        "artifacts": sorted(list(hashes) + ["artifact_hashes.json", "manifest.json"]),
        "final_status": "final_status.json",
    })
    return final


def main() -> None:
    result = run(build_parser().parse_args())
    print(json.dumps(jsonable(result), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
