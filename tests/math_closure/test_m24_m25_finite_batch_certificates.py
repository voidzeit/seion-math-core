"""Tests for M24/M25 finite-batch certificates.

These check the statements proved in
`research/math_closure/certificates/m24_m25_finite_batch_certificates.tex`
on randomized instances. They are implementation controls, not proofs.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest

MODULE_PATH = (
    Path(__file__).resolve().parents[2]
    / "research" / "math_closure" / "certificates"
    / "m24_m25_finite_batch_certificates.py"
)
_spec = importlib.util.spec_from_file_location("m24_m25", MODULE_PATH)
m24 = importlib.util.module_from_spec(_spec)
# Register before exec: the module defines a dataclass, and dataclasses
# resolves cls.__module__ through sys.modules during class construction.
sys.modules["m24_m25"] = m24
_spec.loader.exec_module(m24)


def instance(seed: int, *, topology: str, dim: int, rank: int, depth: int = 4, batch: int = 48):
    rng = np.random.default_rng(seed)
    root = m24.chain(depth, dim) if topology == "chain" else m24.branching(dim)
    _, laws, projectors, leaves = m24.build_instance(root, dim, rank, batch, rng)
    return root, laws, projectors, leaves


CASES = [
    (topology, dim, rank, depth)
    for topology in ("chain", "branching")
    for dim in (3, 5)
    for rank in (1, 2)
    for depth in (1, 3, 6)
]


@pytest.mark.parametrize("topology,dim,rank,depth", CASES)
@pytest.mark.parametrize("seed", [0, 11, 202])
def test_all_certificate_claims_hold(topology, dim, rank, depth, seed):
    root, laws, projectors, leaves = instance(
        seed, topology=topology, dim=dim, rank=rank, depth=depth
    )
    result = m24.certificates(root, laws, projectors, leaves)
    assert result["violations"] == [], result["violations"]


@pytest.mark.parametrize("seed", [0, 1, 2, 3, 4])
def test_lemma1_is_an_exact_identity(seed):
    """Lemma 1 introduces no slack; a nonzero residual would mean the slot
    maps are misdefined (wrong reduced/ambient split across slots)."""
    root, laws, projectors, leaves = instance(
        seed, topology="chain" if seed % 2 else "branching", dim=4, rank=2, depth=5
    )
    result = m24.certificates(root, laws, projectors, leaves)
    assert result["lemma1_max_residual"] < 1e-9


@pytest.mark.parametrize("seed", [7, 8, 9])
def test_root_bounds_are_ordered(seed):
    """actual <= G (M25) <= B (M24) <= Bbar (batch-decoupled) <= A (Frobenius).

    Ordering is the content of Theorem M25 and Propositions M24.2 / M24.3;
    an inversion would mean a refinement is not a refinement.
    """
    root, laws, projectors, leaves = instance(
        seed, topology="chain", dim=5, rank=2, depth=6
    )
    r = m24.certificates(root, laws, projectors, leaves)
    tol = 1e-9
    assert r["root_actual"] <= r["root_G"] + tol
    assert r["root_G"] <= r["root_B"] + tol
    assert r["root_B"] <= r["root_Bbar"] + tol
    assert r["root_Bbar"] <= r["root_A"] + tol


def test_full_rank_projectors_give_zero_bound():
    """With rank = dim nothing is truncated, so every closure residual is zero
    and the whole certified chain must collapse to zero."""
    root, laws, projectors, leaves = instance(
        3, topology="chain", dim=4, rank=4, depth=5
    )
    r = m24.certificates(root, laws, projectors, leaves)
    assert r["root_actual"] == pytest.approx(0.0, abs=1e-9)
    assert r["root_B"] == pytest.approx(0.0, abs=1e-9)
    assert r["root_G"] == pytest.approx(0.0, abs=1e-9)


def test_randomized_sweep_has_no_violations():
    results = m24.sweep(seeds=30)
    assert all(not r["violations"] for r in results)
    assert max(r["lemma1_max_residual"] for r in results) < 1e-9
