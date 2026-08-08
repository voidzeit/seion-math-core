"""Deterministic trainer-state round-trip tests."""
from __future__ import annotations

import random
import json
from pathlib import Path

import numpy as np
import pytest
import torch

from seion_kgr import reproducibility as repro
from seion_kgr.train import build_parser, train


def test_rng_snapshot_restores_all_trainer_streams():
    random.seed(101)
    torch.manual_seed(102)
    numpy_rng = np.random.default_rng(103)
    data_loader = torch.Generator().manual_seed(104)
    geometry = torch.Generator().manual_seed(105)
    generators = {"data_loader": data_loader, "geometry": geometry}

    # Advance every stream before the checkpoint boundary.
    random.random()
    torch.rand(3)
    numpy_rng.integers(0, 100, size=3)
    torch.rand(3, generator=data_loader)
    torch.rand(3, generator=geometry)
    state = repro.rng_state_snapshot(1, numpy_rng=numpy_rng, generators=generators)

    expected = {
        "python": random.random(),
        "torch": torch.rand(3),
        "numpy": numpy_rng.integers(0, 100, size=3),
        "data_loader": torch.rand(3, generator=data_loader),
        "geometry": torch.rand(3, generator=geometry),
    }

    repro.restore_rng_state(state, numpy_rng=numpy_rng, generators=generators)
    actual = {
        "python": random.random(),
        "torch": torch.rand(3),
        "numpy": numpy_rng.integers(0, 100, size=3),
        "data_loader": torch.rand(3, generator=data_loader),
        "geometry": torch.rand(3, generator=geometry),
    }

    assert actual["python"] == expected["python"]
    assert torch.equal(actual["torch"], expected["torch"])
    assert np.array_equal(actual["numpy"], expected["numpy"])
    assert torch.equal(actual["data_loader"], expected["data_loader"])
    assert torch.equal(actual["geometry"], expected["geometry"])


def test_cpu_resume_matches_uninterrupted_run(tmp_path: Path):
    data_dir = tmp_path / "kg"
    data_dir.mkdir()
    triples = {
        "train": ["a\tr0\tb", "b\tr1\tc", "c\tr0\td", "d\tr1\ta", "a\tr1\tc", "c\tr1\ta"],
        "valid": ["a\tr0\tc", "b\tr1\td"],
        "test": ["a\tr1\td", "d\tr0\tb"],
    }
    for split, rows in triples.items():
        (data_dir / f"{split}.txt").write_text("\n".join(rows) + "\n", encoding="utf-8")

    def args(out_dir: Path, epochs: int, resume: Path | None = None):
        values = [
            "--train", str(data_dir / "train.txt"), "--valid", str(data_dir / "valid.txt"),
            "--test", str(data_dir / "test.txt"), "--out_dir", str(out_dir),
            "--dim", "8", "--base_expert", "tucker", "--epochs", str(epochs),
            "--batch_size", "4", "--neg_k", "2", "--eval_every", "1",
            "--eval_batch", "8", "--entity_block_eval", "8", "--n3_weight", "0",
            "--seed", "17", "--cpu", "--skip_test_eval",
        ]
        if resume is not None:
            values += ["--resume", str(resume)]
        return build_parser().parse_args(values)

    full_dir = tmp_path / "full"
    partial_dir = tmp_path / "partial"
    resumed_dir = tmp_path / "resumed"
    train(args(full_dir, 5))
    train(args(partial_dir, 3))
    train(args(resumed_dir, 5, partial_dir / "last.pt"))

    full_rows = [json.loads(line) for line in (full_dir / "metrics.jsonl").read_text().splitlines()]
    resumed_rows = [json.loads(line) for line in (resumed_dir / "metrics.jsonl").read_text().splitlines()]
    assert [row["epoch"] for row in resumed_rows] == [3, 4]
    def without_wall(rows):
        return [{key: value for key, value in row.items() if key != "wall_sec"} for row in rows]

    assert without_wall(resumed_rows) == without_wall(full_rows[3:])

    full_state = repro.load_checkpoint(full_dir / "last.pt")["model_state"]
    resumed_state = repro.load_checkpoint(resumed_dir / "last.pt")["model_state"]
    assert full_state.keys() == resumed_state.keys()
    assert all(torch.equal(full_state[name], resumed_state[name]) for name in full_state)


@pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA is not available")
def test_cuda_resume_matches_short_uninterrupted_run(tmp_path: Path):
    data_dir = tmp_path / "kg_cuda"
    data_dir.mkdir()
    triples = {
        "train": ["a\tr0\tb", "b\tr1\tc", "c\tr0\td", "d\tr1\ta"],
        "valid": ["a\tr0\tc", "b\tr1\td"],
        "test": ["a\tr1\td", "d\tr0\tb"],
    }
    for split, rows in triples.items():
        (data_dir / f"{split}.txt").write_text("\n".join(rows) + "\n", encoding="utf-8")

    def args(out_dir: Path, epochs: int, resume: Path | None = None):
        values = [
            "--train", str(data_dir / "train.txt"), "--valid", str(data_dir / "valid.txt"),
            "--test", str(data_dir / "test.txt"), "--out_dir", str(out_dir),
            "--dim", "8", "--base_expert", "tucker", "--epochs", str(epochs),
            "--batch_size", "4", "--neg_k", "2", "--eval_every", "1",
            "--eval_batch", "8", "--entity_block_eval", "8", "--n3_weight", "0",
            "--seed", "23", "--skip_test_eval",
        ]
        if resume is not None:
            values += ["--resume", str(resume)]
        return build_parser().parse_args(values)

    full_dir = tmp_path / "full_cuda"
    partial_dir = tmp_path / "partial_cuda"
    resumed_dir = tmp_path / "resumed_cuda"
    train(args(full_dir, 2))
    train(args(partial_dir, 1))
    train(args(resumed_dir, 2, partial_dir / "last.pt"))

    full_rows = [json.loads(line) for line in (full_dir / "metrics.jsonl").read_text().splitlines()]
    resumed_rows = [json.loads(line) for line in (resumed_dir / "metrics.jsonl").read_text().splitlines()]
    assert [row["epoch"] for row in resumed_rows] == [1]
    assert [{key: value for key, value in row.items() if key != "wall_sec"} for row in resumed_rows] == [
        {key: value for key, value in full_rows[1].items() if key != "wall_sec"}
    ]
    full_state = repro.load_checkpoint(full_dir / "last.pt")["model_state"]
    resumed_state = repro.load_checkpoint(resumed_dir / "last.pt")["model_state"]
    assert all(torch.equal(full_state[name], resumed_state[name]) for name in full_state)
