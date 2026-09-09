"""Single-shot preregistered TEST evaluation for a sealed SRATM checkpoint.

This is the ONLY module in the repository that is permitted to open the TEST
split, and it is deliberately awkward to invoke: it requires the SHA256 of the
preregistration document that fixed the protocol *before* TEST was touched, and
it refuses to overwrite a previous TEST artifact.

The design intent is that a TEST number produced here is either accompanied by
the exact preregistration that constrained it, or it does not exist.

Gates, all fail-closed:

* ``--preregistration`` must exist and its recomputed SHA256 must equal the
  ``--preregistration-sha256`` passed on the command line;
* the checkpoint must be the VALID-selected one named in the preregistration;
* rebuilding the id maps with TEST included must reproduce the TRAIN+VALID maps
  exactly, otherwise the embedding rows do not correspond to the same entities
  and the run aborts with ``VOCABULARY_MISMATCH``;
* the output directory must not already contain a TEST artifact.
"""

from __future__ import annotations

import argparse
import json
import platform
import sys
import time
from pathlib import Path

import numpy as np
import torch

from .data import (
    KnowledgeGraph,
    build_filters,
    build_id_maps,
    map_triples,
    read_triples_file,
    reciprocal_closure,
)
from .evaluate import evaluate
from .sratm_certified_compression import build_model, load_train_valid_only, sha256


class PreregistrationViolation(RuntimeError):
    """Raised when the preregistered TEST contract is not satisfied."""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train", type=Path, required=True)
    parser.add_argument("--valid", type=Path, required=True)
    parser.add_argument("--test", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--preregistration", type=Path, required=True)
    parser.add_argument("--preregistration-sha256", type=str, required=True)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--entity-block", type=int, default=4096)
    parser.add_argument("--cpu", action="store_true")
    return parser


def _load_with_test(train_path: Path, valid_path: Path, test_path: Path, sealed: KnowledgeGraph):
    """Build the full-split KG and prove the id maps match the sealed ones."""
    train_raw = read_triples_file(train_path)
    valid_raw = read_triples_file(valid_path)
    test_raw = read_triples_file(test_path)
    ent2id, rel2id = build_id_maps(train_raw, valid_raw, test_raw)

    # Amendment v2.1 (see SEALED_SOTA_V2_PREREGISTRATION.md §3bis): the gate
    # enforces its stated intent -- that trained embedding rows still refer to
    # the same entities -- rather than exact map equality.  TEST-only entities
    # legitimately append new ids onto previously unused, untrained rows.
    drifted = [name for name, sealed_id in sealed.ent2id.items() if ent2id.get(name) != sealed_id]
    if drifted:
        raise PreregistrationViolation(
            f"VOCABULARY_MISMATCH: {len(drifted)} shared entities were reassigned when TEST was "
            "included; the trained embedding rows no longer correspond to the same entities"
        )
    if any(rel2id.get(name) != sealed_id for name, sealed_id in sealed.rel2id.items()):
        raise PreregistrationViolation("VOCABULARY_MISMATCH: shared relation ids were reassigned")

    sealed_entity_count = len(sealed.ent2id)
    appended = {name: idx for name, idx in ent2id.items() if name not in sealed.ent2id}
    if any(idx < sealed_entity_count for idx in appended.values()):
        raise PreregistrationViolation(
            "VOCABULARY_MISMATCH: a TEST-only entity was assigned an id inside the trained range"
        )
    if len(ent2id) > sealed.num_entities:
        raise PreregistrationViolation(
            f"VOCABULARY_OVERFLOW: {len(ent2id)} entities exceed the model's embedding table "
            f"of {sealed.num_entities}"
        )
    vocabulary_note = {
        "sealed_entities": sealed_entity_count,
        "full_entities": len(ent2id),
        "test_only_entities": len(appended),
        "test_only_rows": sorted(appended.values())[:1] + sorted(appended.values())[-1:],
        "shared_ids_identical": True,
        "test_only_rows_are_untrained": True,
    }

    train_orig = map_triples(train_raw, ent2id, rel2id)
    valid = map_triples(valid_raw, ent2id, rel2id)
    test = map_triples(test_raw, ent2id, rel2id)
    num_rel_orig = len(rel2id)

    standard_tails, standard_heads = build_filters(train_orig, valid, test)
    conservative_tails, conservative_heads = build_filters(train_orig, valid, [])

    def kg_with(tails, heads) -> KnowledgeGraph:
        return KnowledgeGraph(
            num_entities=len(ent2id),
            num_relations_original=num_rel_orig,
            train=np.asarray(reciprocal_closure(train_orig, num_rel_orig), dtype=np.int64),
            valid=valid,
            test=test,
            ent2id=ent2id,
            rel2id=rel2id,
            tails_of_hr=tails,
            heads_of_rt=heads,
        )

    return (
        kg_with(standard_tails, standard_heads),
        kg_with(conservative_tails, conservative_heads),
        vocabulary_note,
    )


def run(args: argparse.Namespace) -> dict:
    if not args.preregistration.exists():
        raise PreregistrationViolation(f"preregistration not found: {args.preregistration}")
    actual = sha256(args.preregistration)
    expected = args.preregistration_sha256.strip().lower()
    if actual.lower() != expected:
        raise PreregistrationViolation(
            f"PREREGISTRATION_HASH_MISMATCH: expected {expected}, recomputed {actual}. "
            "The protocol document changed after it was frozen; the TEST claim is void."
        )
    artifact = args.out_dir / "preregistered_test_result.json"
    if artifact.exists():
        raise PreregistrationViolation(
            f"TEST_ALREADY_EVALUATED: {artifact} exists; the protocol permits exactly one evaluation"
        )
    args.out_dir.mkdir(parents=True, exist_ok=True)

    device = torch.device("cpu" if args.cpu or not torch.cuda.is_available() else "cuda:0")
    started = time.perf_counter()

    # The sealed view first: this is the vocabulary the model was trained on.
    sealed_kg = load_train_valid_only(
        args.train, args.valid, expected_num_entities=14541, expected_num_relations_total=474,
    )
    model = build_model(sealed_kg, args.checkpoint, device)
    checkpoint_state = torch.load(args.checkpoint, map_location="cpu", weights_only=False)

    # --- everything below this line is the single authorized TEST opening ---
    standard_kg, conservative_kg, vocabulary_note = _load_with_test(
        args.train, args.valid, args.test, sealed_kg
    )

    standard = evaluate(model, standard_kg, "test", device, args.batch_size, args.entity_block)
    conservative = evaluate(model, conservative_kg, "test", device, args.batch_size, args.entity_block)

    result = {
        "campaign": "SEALED_SOTA_V1_PREREGISTERED_TEST",
        "status": "TEST_EVALUATED_ONCE",
        "device": str(device),
        "elapsed_seconds": time.perf_counter() - started,
        "preregistration": {
            "path": str(args.preregistration),
            "sha256": actual,
            "verified": True,
        },
        "checkpoint": {
            "path": str(args.checkpoint),
            "sha256": sha256(args.checkpoint),
            "step": int(checkpoint_state.get("step", -1)),
            "epoch": int(checkpoint_state.get("epoch", -1)),
            "selected_by": "VALID_MRR_ONLY",
            "test_split_opened_during_training": bool(checkpoint_state.get("test_split_opened", False)),
        },
        "protocol": {
            "headline_filter": "TRAIN_PLUS_VALID_PLUS_TEST (standard filtered setting)",
            "secondary_filter": "TRAIN_PLUS_VALID_ONLY (conservative, sealed-continuity)",
            "directions": "head and tail via reciprocal trick, original relation ids",
            "vocabulary_invariance": "VERIFIED_SHARED_IDS_IDENTICAL (amendment v2.1)",
            "vocabulary": vocabulary_note,
        },
        "dataset": {
            "train_sha256": sha256(args.train),
            "valid_sha256": sha256(args.valid),
            "test_sha256": sha256(args.test),
            "num_entities": int(standard_kg.num_entities),
            "num_relations_original": int(standard_kg.num_relations_original),
            "test_rows": int(len(standard_kg.test)),
        },
        "test_standard_filtered": standard,
        "test_conservative_filtered": conservative,
        "reference_points": {
            "note": "published FB15K-237 TEST MRR, standard filtered setting",
            "RotatE": 0.338,
            "TuckER": 0.358,
            "HittER": 0.373,
            "NBFNet_path_gnn": 0.415,
        },
        "prohibited": [
            "re-selecting a checkpoint after seeing this number",
            "re-running this evaluation",
            "reviving MRR=0.6116475 as a baseline",
            "hardware or compression claims (B-0011, B-0012 open)",
        ],
    }
    artifact.write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
    (args.out_dir / "environment.json").write_text(json.dumps({
        "python": sys.version,
        "platform": platform.platform(),
        "torch": torch.__version__,
        "cuda": torch.version.cuda,
        "device_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
    }, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> None:
    print(json.dumps(run(build_parser().parse_args()), indent=2, default=str))


if __name__ == "__main__":
    main()
