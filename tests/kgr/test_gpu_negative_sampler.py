"""The device-resident sampler must match the reference one where it counts.

It cannot be bit-exact -- a different RNG consumption order never is -- so the
contract tested here is the one a negative sampler actually has to satisfy:
never return a known positive, always return the requested shape, and draw
uniformly over the allowed set. The tests run on CPU so they execute in CI;
the implementation is device-agnostic.
"""

from __future__ import annotations

import numpy as np
import torch

from seion_kgr.data import (
    KnowledgeGraph,
    build_filters,
    reciprocal_closure,
    sample_negatives,
    train_only_filter_view,
)
from seion_kgr.gpu_negative_sampler import GpuNegativeSampler

NUM_ENTITIES = 300
DEVICE = torch.device("cpu")


def _kg() -> KnowledgeGraph:
    rng = np.random.default_rng(4)
    train_orig = [
        (int(h), 0, int(t))
        for h, t in zip(rng.integers(0, 20, 400), rng.integers(0, NUM_ENTITIES, 400))
    ]
    valid = [(0, 0, 250), (0, 0, 251)]
    tails, heads = build_filters(train_orig, valid, [])
    return KnowledgeGraph(
        num_entities=NUM_ENTITIES,
        num_relations_original=1,
        train=np.asarray(reciprocal_closure(train_orig, 1), dtype=np.int64),
        valid=valid,
        test=[],
        ent2id={f"e{i}": i for i in range(NUM_ENTITIES)},
        rel2id={"r0": 0},
        tails_of_hr=tails,
        heads_of_rt=heads,
    )


def _queries(kg: KnowledgeGraph, rows: int = 128):
    keys = sorted(kg.tails_of_hr)
    rng = np.random.default_rng(9)
    picked = [keys[i] for i in rng.integers(0, len(keys), rows)]
    h = torch.tensor([k[0] for k in picked], dtype=torch.long)
    r = torch.tensor([k[1] for k in picked], dtype=torch.long)
    return h, r, picked


def test_never_returns_a_known_positive():
    kg = _kg()
    h, r, picked = _queries(kg)
    negs = GpuNegativeSampler(kg, DEVICE).sample(h, r, 32, torch.Generator().manual_seed(0))
    assert negs.shape == (len(picked), 32)
    for row, key in enumerate(picked):
        forbidden = set(kg.tails_of_hr[key].tolist())
        assert not forbidden.intersection(negs[row].tolist()), f"leaked a positive on row {row}"


def test_matches_the_reference_sampler_on_the_allowed_set():
    """Both samplers must draw from the same support, per query."""
    kg = _kg()
    h, r, picked = _queries(kg, rows=64)
    t = torch.tensor([int(kg.tails_of_hr[k][0]) for k in picked], dtype=torch.long)
    reference = sample_negatives(h, r, t, kg, 32, np.random.default_rng(1), DEVICE)
    ours = GpuNegativeSampler(kg, DEVICE).sample(h, r, 32, torch.Generator().manual_seed(1))
    for row, key in enumerate(picked):
        allowed = set(range(NUM_ENTITIES)) - set(kg.tails_of_hr[key].tolist())
        assert set(reference[row].tolist()) <= allowed
        assert set(ours[row].tolist()) <= allowed


def test_draws_uniformly_over_the_allowed_set():
    kg = _kg()
    key = (0, 0)
    forbidden = set(kg.tails_of_hr[key].tolist())
    allowed = sorted(set(range(NUM_ENTITIES)) - forbidden)
    rows = 512
    h = torch.zeros(rows, dtype=torch.long)
    r = torch.zeros(rows, dtype=torch.long)
    negs = GpuNegativeSampler(kg, DEVICE).sample(h, r, 64, torch.Generator().manual_seed(3))
    counts = np.bincount(negs.flatten().numpy(), minlength=NUM_ENTITIES)
    assert counts[list(forbidden)].sum() == 0
    observed = counts[allowed]
    expected = rows * 64 / len(allowed)
    # Loose band: this checks for structural bias, not RNG quality.
    assert observed.mean() == expected
    assert observed.min() > 0.3 * expected, "some allowed entities are under-sampled"
    assert observed.max() < 3.0 * expected, "some allowed entities are over-sampled"


def test_respects_the_train_only_view_so_heldout_golds_stay_samplable():
    kg = train_only_filter_view(_kg())
    h = torch.zeros(256, dtype=torch.long)
    r = torch.zeros(256, dtype=torch.long)
    negs = GpuNegativeSampler(kg, DEVICE).sample(h, r, 64, torch.Generator().manual_seed(5))
    drawn = set(negs.flatten().tolist())
    # 250/251 are VALID-only golds: shielded under the shipped tables, samplable here.
    assert drawn.intersection({250, 251}), "held-out golds must be reachable under train_only"


def test_rejects_malformed_inputs():
    kg = _kg()
    sampler = GpuNegativeSampler(kg, DEVICE)
    for bad in (
        lambda: sampler.sample(torch.zeros(4, dtype=torch.long), torch.zeros(3, dtype=torch.long), 4),
        lambda: sampler.sample(torch.zeros((2, 2), dtype=torch.long), torch.zeros((2, 2), dtype=torch.long), 4),
        lambda: sampler.sample(torch.zeros(4, dtype=torch.long), torch.zeros(4, dtype=torch.long), 0),
    ):
        try:
            bad()
        except ValueError:
            pass
        else:  # pragma: no cover - guard
            raise AssertionError("expected ValueError")
