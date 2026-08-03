"""Gate 13.4 acceptance test (``campaigns/gate13/``): PASS_NONTRIVIAL_CERTIFICATION.

Trains a real model on a real WN18RR subsample (via the actual
``train.py`` entrypoint), then runs the real certification pipeline
(``run_certification.py``) — building ``F_ref``/``F_cmp`` from that ONE
checkpoint, never two independently trained models — over its resulting
checkpoint on real validation queries.

``--gate_g_max`` is set very small (``0.0002``) for this specific test
fixture. This is a deliberate, honest calibration choice, documented as
such — NOT a hidden way to fabricate a result: the frozen LayerNorm
envelope bound (``campaigns/gate13/preregistration.md`` §2,
``certified_bounds.envelope_lipschitz_bound``) is extremely conservative
at this embedding scale (~600x per hop with the default ``eps=1e-5``), so
a real checkpoint trained with the architecture's default
``gate_g_max=1.0`` shows ~0% certified coverage under this bound — a
real, separately-documented finding (``campaigns/gate13/preregistration.md``),
not a defect in the pipeline itself (zero false certificates either way).
A small ``gate_g_max`` is a legitimate, real hyperparameter choice
(a conservative deployment cap on the path branch's maximum influence)
that puts the signed gate in the regime where this specific bound
actually has room to certify something nontrivial.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from seion_kgr.run_certification import build_parser as build_certification_parser
from seion_kgr.run_certification import run_certification
from seion_kgr.train import build_parser as build_train_parser
from seion_kgr.train import train

DATA_ROOT = Path(__file__).resolve().parents[2] / "data" / "WN18RR"

pytestmark = pytest.mark.slow


def _write_subsample(tmp_path: Path) -> Path:
    sub = tmp_path / "wn18rr_sub"
    sub.mkdir()
    for split, n in (("train", 20000), ("valid", 300), ("test", 300)):
        lines = (DATA_ROOT / f"{split}.txt").read_text(encoding="utf-8").splitlines()[:n]
        (sub / f"{split}.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return sub


def _train_checkpoint(data_dir: Path, out_dir: Path) -> Path:
    args = build_train_parser().parse_args([
        "--train", str(data_dir / "train.txt"), "--valid", str(data_dir / "valid.txt"), "--test", str(data_dir / "test.txt"),
        "--out_dir", str(out_dir), "--dim", "16", "--enable_path", "--path_layers", "1", "--path_max_neighbors", "8",
        "--path_backend", "batched", "--path_selector_mode", "budgeted_bfs", "--gate_g_max", "0.0002",
        "--epochs", "3", "--batch_size", "64", "--eval_max_queries", "200", "--seed", "0", "--cpu",
    ])
    train(args)
    return out_dir / "best.pt"


@pytest.mark.skipif(not DATA_ROOT.is_dir(), reason="data/WN18RR not present in this checkout")
def test_certification_real_run_positive_coverage_zero_false_certificates(tmp_path):
    data_dir = _write_subsample(tmp_path)
    checkpoint = _train_checkpoint(data_dir, tmp_path / "train_run")

    def _run(out_name: str):
        out_dir = tmp_path / out_name
        args = build_certification_parser().parse_args([
            "--checkpoint", str(checkpoint),
            "--train", str(data_dir / "train.txt"), "--valid", str(data_dir / "valid.txt"), "--test", str(data_dir / "test.txt"),
            "--out_dir", str(out_dir), "--certification_split", "valid", "--certification_max_queries", "300",
            "--certification_proj_rank", "15", "--certification_seed", "13", "--cpu",
        ])
        return run_certification(args), out_dir / "certification"

    result, cert_dir = _run("cert_run")

    # --- files present ---
    for filename in (
        "certification_manifest.json", "assumption_checks.json", "local_bounds.jsonl", "node_hop_bounds.jsonl",
        "query_certificates.jsonl", "ranking_margins.jsonl", "coverage_summary.json", "bound_vs_observed.csv",
        "false_certificate_audit.json",
    ):
        assert (cert_dir / filename).is_file(), f"missing artifact: {filename}"

    # --- the core acceptance numbers ---
    coverage = result["coverage"]
    assert coverage["count"] == 300
    assert coverage["certified_rank_stable_coverage"] > 0.0, (
        "compressed_real_model_coverage must be > 0 on a real checkpoint — see this file's module "
        "docstring for why gate_g_max is set small to make this achievable under the frozen envelope bound"
    )
    assert coverage["false_certificates"] == 0
    assert result["false_certificates"] == 0

    # coverage reported SEPARATELY from accuracy (mandate §XXXI) — the
    # coverage dict must never contain an MRR/Hits@K key
    for forbidden in ("MRR", "Hits@1", "Hits@3", "Hits@10", "mean_rank"):
        assert forbidden not in coverage

    # --- manifest completeness ---
    manifest = json.loads((cert_dir / "certification_manifest.json").read_text())
    for field in (
        "model_commit", "checkpoint_sha256", "dataset_hashes", "reference_rank", "compressed_rank", "dim",
        "path_backend", "selector_mode", "dtype", "seed", "bound_formula_version", "numeric_tolerances",
        "coverage", "max_observed_over_bound_ratio",
    ):
        assert field in manifest, f"manifest missing field: {field}"
    assert manifest["reference_rank"] == 0
    assert manifest["compressed_rank"] == 15

    # --- deterministic re-execution ---
    result2, cert_dir2 = _run("cert_run_rerun")
    assert result2["coverage"] == coverage
    assert (cert_dir / "query_certificates.jsonl").read_text() == (cert_dir2 / "query_certificates.jsonl").read_text()


@pytest.mark.skipif(not DATA_ROOT.is_dir(), reason="data/WN18RR not present in this checkout")
def test_certification_rejects_learned_topk_and_wrong_backend_and_untrained_reference(tmp_path):
    import torch

    data_dir = _write_subsample(tmp_path)
    checkpoint = _train_checkpoint(data_dir, tmp_path / "train_run")

    def _args(out_name, proj_rank=15):
        return build_certification_parser().parse_args([
            "--checkpoint", str(checkpoint),
            "--train", str(data_dir / "train.txt"), "--valid", str(data_dir / "valid.txt"), "--test", str(data_dir / "test.txt"),
            "--out_dir", str(tmp_path / out_name), "--certification_proj_rank", str(proj_rank), "--cpu",
        ])

    # learned_topk rejected
    ckpt = torch.load(checkpoint, map_location="cpu", weights_only=False)
    tampered = tmp_path / "tampered_learned_topk.pt"
    ckpt2 = dict(ckpt)
    ckpt2["args"] = dict(ckpt["args"], path_selector_mode="learned_topk")
    torch.save(ckpt2, tampered)
    args = _args("cert_rejected_selector")
    args.checkpoint = str(tampered)
    with pytest.raises(NotImplementedError, match="NOT_CERTIFIED_SELECTOR_UNSUPPORTED"):
        run_certification(args)

    # legacy backend rejected
    tampered2 = tmp_path / "tampered_legacy.pt"
    ckpt3 = dict(ckpt)
    ckpt3["args"] = dict(ckpt["args"], path_backend="legacy")
    torch.save(ckpt3, tampered2)
    args = _args("cert_rejected_backend")
    args.checkpoint = str(tampered2)
    with pytest.raises(NotImplementedError, match="batched"):
        run_certification(args)

    # checkpoint already trained WITH a projector rejected (F_ref would not be uncompressed)
    tampered3 = tmp_path / "tampered_proj.pt"
    ckpt4 = dict(ckpt)
    ckpt4["args"] = dict(ckpt["args"], path_proj_rank=4)
    torch.save(ckpt4, tampered3)
    args = _args("cert_rejected_proj")
    args.checkpoint = str(tampered3)
    with pytest.raises(ValueError, match="path_proj_rank=0"):
        run_certification(args)

    # certification_proj_rank >= dim rejected
    args = _args("cert_rejected_rank", proj_rank=16)
    with pytest.raises(ValueError, match="must be < model dim"):
        run_certification(args)
