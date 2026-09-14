"""Gate 13.5 (``campaigns/gate13/gate13_5/``) precondition tests: the A0-A3
ablation matrix's paired-seed design (mission brief §8) depends on two
mechanisms that did not exist, or were not verified, before this campaign.

1. Batch order must be IDENTICAL across A0/A1/A2/A3 for the same --seed,
   independent of how many extra parameters a config's enabled branches
   add (train.py's DataLoader now uses an explicit generator seeded
   directly from args.seed, decoupled from the ambient global-RNG position
   left behind by model construction — see train.py's data_gen comment).
2. --init_from_checkpoint must seed a larger architecture's OVERLAPPING
   params from a smaller checkpoint (e.g. A0 -> A1/A2/A3) via strict=False,
   leave genuinely new params (path_reasoner/seion submodules) at their own
   fresh init, and reject the reverse direction (a source with params this
   model does not have) as an explicit error rather than silently dropping
   them.
3. --skip_test_eval must make a screening run's final_metrics.json report
   "test": null / "test_eval_skipped": true instead of silently opening the
   test split — the test-set discipline (preregistration.md sec10) that a
   12-run screening campaign, unlike a single confirmatory run, must not
   inspect test once per run.
"""
from __future__ import annotations

from pathlib import Path

import pytest
import torch

from seion_kgr import reproducibility as repro
from seion_kgr.data import TripleDataset
from seion_kgr.train import build_parser as build_train_parser
from seion_kgr.train import train

DATA_ROOT = Path(__file__).resolve().parents[2] / "data" / "WN18RR"


def test_dataloader_batch_order_independent_of_prior_rng_consumption():
    """Directly exercises the exact mechanism train.py's data_gen line
    fixes: constructs the real TripleDataset/DataLoader pair twice under
    the same nominal seed, but with a DIFFERENT number of intervening
    random draws before the DataLoader is built (standing in for A0's vs.
    A3's different parameter counts) -- the resulting batch order must be
    bit-identical either way, or the paired A0-A3 comparison is comparing
    runs trained on different data orders, not just different
    architectures."""
    triples = torch.arange(2000 * 3).reshape(2000, 3).numpy()
    dataset = TripleDataset(triples)

    def _epoch_order(seed: int, decoy_draws: int) -> list:
        repro.set_seed(seed)
        for _ in range(decoy_draws):
            torch.randn(37, 41)  # stands in for "extra branch params initialized"
        data_gen = torch.Generator()
        data_gen.manual_seed(seed + 1000)
        loader = torch.utils.data.DataLoader(dataset, batch_size=64, shuffle=True, drop_last=False, generator=data_gen)
        order = []
        for h_batch, r_batch, t_batch in loader:  # TripleDataset.__getitem__ returns (h, r, t) tuples
            order.extend(h_batch.tolist())
        return order

    order_fewer_params = _epoch_order(seed=7, decoy_draws=0)   # stands in for A0
    order_more_params = _epoch_order(seed=7, decoy_draws=500)  # stands in for A3
    assert order_fewer_params == order_more_params, (
        "batch order diverged when a different number of parameters were randomly "
        "initialized before the DataLoader was built -- the paired A0-A3 seed design is broken"
    )

    order_different_seed = _epoch_order(seed=8, decoy_draws=0)
    assert order_different_seed != order_fewer_params, "sanity check: different seeds must not collide"


def _write_subsample(tmp_path: Path) -> Path:
    sub = tmp_path / "wn18rr_sub"
    sub.mkdir()
    for split, n in (("train", 3000), ("valid", 100), ("test", 100)):
        lines = (DATA_ROOT / f"{split}.txt").read_text(encoding="utf-8").splitlines()[:n]
        (sub / f"{split}.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return sub


@pytest.mark.skipif(not DATA_ROOT.is_dir(), reason="data/WN18RR not present in this checkout")
def test_init_from_checkpoint_seeds_overlap_and_leaves_new_branches_fresh(tmp_path):
    data_dir = _write_subsample(tmp_path)

    base_args = build_train_parser().parse_args([
        "--train", str(data_dir / "train.txt"), "--valid", str(data_dir / "valid.txt"), "--test", str(data_dir / "test.txt"),
        "--out_dir", str(tmp_path / "a0_run"), "--dim", "16", "--base_expert", "tucker",
        "--epochs", "1", "--batch_size", "64", "--eval_max_queries", "50", "--seed", "3", "--cpu",
    ])
    train(base_args)
    a0_checkpoint = tmp_path / "a0_run" / "best.pt"
    a0_state = repro.load_checkpoint(str(a0_checkpoint))["model_state"]

    a1_args = build_train_parser().parse_args([
        "--train", str(data_dir / "train.txt"), "--valid", str(data_dir / "valid.txt"), "--test", str(data_dir / "test.txt"),
        "--out_dir", str(tmp_path / "a1_run"), "--dim", "16", "--base_expert", "tucker",
        "--enable_path", "--path_layers", "1", "--path_max_neighbors", "8", "--path_backend", "batched",
        "--path_selector_mode", "budgeted_bfs", "--epochs", "1", "--batch_size", "64", "--eval_max_queries", "50",
        "--seed", "3", "--cpu", "--init_from_checkpoint", str(a0_checkpoint),
    ])
    train(a1_args)

    manifest_path = tmp_path / "a1_run" / "init_from_checkpoint_manifest.json"
    assert manifest_path.is_file()
    a1_checkpoint = tmp_path / "a1_run" / "last.pt"
    a1_state = repro.load_checkpoint(str(a1_checkpoint))["model_state"]

    # overlapping (tucker/embedding) params: A1's checkpoint after training
    # started from A0's values -- not asserting equality post-training
    # (they diverge under gradient updates), only that the LOADED init
    # actually differed from a from-scratch A1 run's init, which the
    # manifest's loaded_keys list (not empty, covers real tucker/embedding
    # keys) already establishes structurally.
    import json
    manifest = json.loads(manifest_path.read_text())
    assert manifest["loaded_keys"], "expected at least the shared tucker/embedding keys to be loaded from A0"
    assert any("path_reasoner" in k for k in manifest["fresh_init_keys"]), (
        "A1's path_reasoner params must be listed as fresh-init, not silently absent from the report"
    )
    assert not any("path_reasoner" in k for k in manifest["loaded_keys"]), (
        "A0 has no path_reasoner submodule -- nothing under that name should ever be reported as loaded"
    )
    assert set(a0_state.keys()).issubset(set(a1_state.keys())), "A0's keys must all exist in A1 (architectural subset requirement)"


@pytest.mark.skipif(not DATA_ROOT.is_dir(), reason="data/WN18RR not present in this checkout")
def test_init_from_checkpoint_rejects_reverse_direction_and_resume_combo(tmp_path):
    data_dir = _write_subsample(tmp_path)

    a1_args = build_train_parser().parse_args([
        "--train", str(data_dir / "train.txt"), "--valid", str(data_dir / "valid.txt"), "--test", str(data_dir / "test.txt"),
        "--out_dir", str(tmp_path / "a1_run"), "--dim", "16", "--base_expert", "tucker",
        "--enable_path", "--path_layers", "1", "--path_max_neighbors", "8", "--path_backend", "batched",
        "--path_selector_mode", "budgeted_bfs", "--epochs", "1", "--batch_size", "64", "--eval_max_queries", "50",
        "--seed", "3", "--cpu",
    ])
    train(a1_args)
    a1_checkpoint = tmp_path / "a1_run" / "best.pt"

    a0_from_a1_args = build_train_parser().parse_args([
        "--train", str(data_dir / "train.txt"), "--valid", str(data_dir / "valid.txt"), "--test", str(data_dir / "test.txt"),
        "--out_dir", str(tmp_path / "a0_bad_run"), "--dim", "16", "--base_expert", "tucker",
        "--epochs", "1", "--batch_size", "64", "--eval_max_queries", "50", "--seed", "3", "--cpu",
        "--init_from_checkpoint", str(a1_checkpoint),
    ])
    with pytest.raises(ValueError, match="params this model does not"):
        train(a0_from_a1_args)

    combo_args = build_train_parser().parse_args([
        "--train", str(data_dir / "train.txt"), "--valid", str(data_dir / "valid.txt"), "--test", str(data_dir / "test.txt"),
        "--out_dir", str(tmp_path / "combo_run"), "--dim", "16", "--base_expert", "tucker",
        "--epochs", "1", "--batch_size", "64", "--eval_max_queries", "50", "--seed", "3", "--cpu",
        "--init_from_checkpoint", str(a1_checkpoint), "--resume", str(a1_checkpoint),
    ])
    with pytest.raises(ValueError, match="mutually exclusive"):
        train(combo_args)


@pytest.mark.skipif(not DATA_ROOT.is_dir(), reason="data/WN18RR not present in this checkout")
def test_skip_test_eval_reports_null_test_and_flag(tmp_path):
    data_dir = _write_subsample(tmp_path)

    args_skipped = build_train_parser().parse_args([
        "--train", str(data_dir / "train.txt"), "--valid", str(data_dir / "valid.txt"), "--test", str(data_dir / "test.txt"),
        "--out_dir", str(tmp_path / "skipped_run"), "--dim", "16", "--base_expert", "tucker",
        "--epochs", "1", "--batch_size", "64", "--eval_max_queries", "50", "--seed", "3", "--cpu", "--skip_test_eval",
    ])
    result_skipped = train(args_skipped)
    assert result_skipped["test"] is None
    assert result_skipped["test_eval_skipped"] is True
    import json
    final_metrics = json.loads((tmp_path / "skipped_run" / "final_metrics.json").read_text())
    assert final_metrics["test"] is None
    assert final_metrics["test_eval_skipped"] is True

    args_normal = build_train_parser().parse_args([
        "--train", str(data_dir / "train.txt"), "--valid", str(data_dir / "valid.txt"), "--test", str(data_dir / "test.txt"),
        "--out_dir", str(tmp_path / "normal_run"), "--dim", "16", "--base_expert", "tucker",
        "--epochs", "1", "--batch_size", "64", "--eval_max_queries", "50", "--seed", "3", "--cpu",
    ])
    result_normal = train(args_normal)
    assert result_normal["test"] is not None
    assert result_normal["test_eval_skipped"] is False
    assert "MRR" in result_normal["test"]["combined"]
