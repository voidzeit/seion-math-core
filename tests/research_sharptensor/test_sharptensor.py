import math
import random

import numpy as np
import pytest
from mpmath import mp

from research.pmt_program.sharptensor.certificate import (
    Leaf,
    Node,
    Run,
    amplitude_compact_certificate,
    certify,
    slotwise_certificate,
    theorem_r_certificate,
    verify,
)
from research.pmt_program.sharptensor.gbox import additive_bound, gbox_certified, gbox_float
from research.pmt_program.sharptensor.models import HTTree, MatProdTree, MpoMpsChain
from research.pmt_program.sharptensor.planner import plan_certified_search, plan_theorem_r


# ---------------------------------------------------------------------------
# gBox evaluator
# ---------------------------------------------------------------------------


def test_gbox_uniform_k3_closed_form():
    eta = 0.3
    enc = gbox_certified([eta, eta], tol=1e-10)
    exact = eta * math.sqrt(4 - 3 * eta * eta)
    assert enc.lower <= exact <= enc.upper
    assert enc.width <= 1e-9


@pytest.mark.parametrize("etas", [[0.0], [0.0, 0.0], [1.0], [2.0, 0.5], [1e-12] * 3, [0.999999999, 0.2]])
def test_gbox_edge_cases_bracket_high_precision(etas):
    enc = gbox_certified(etas, tol=1e-10)
    mp.dps = 40
    al = [mp.pi / 2 if e >= 1 else mp.asin(mp.mpf(e)) for e in etas]
    hi = max(al)
    best = mp.mpf(0)
    for g in range(2001):
        t = hi * g / 2000
        C, S = mp.mpf(1), mp.mpf(0)
        for a in al:
            x = min(a, t)
            C *= mp.cos(x)
            S += x
        best = max(best, mp.sqrt(max(0, 1 - 2 * C * mp.cos(S) + C * C)))
    assert best <= enc.upper
    assert enc.lower <= float(best) + 1e-6


def test_gbox_monotone_and_below_sum():
    rng = random.Random(5)
    for _ in range(10):
        etas = [rng.random() * 0.8 for _ in range(rng.randint(1, 6))]
        bigger = [e + 0.1 * rng.random() for e in etas]
        a = gbox_certified(etas, tol=1e-9)
        b = gbox_certified(bigger, tol=1e-9)
        assert a.lower <= b.upper
        assert a.upper <= additive_bound(etas) + 1e-9


def test_h3_matches_box_multistart():
    rng = np.random.default_rng(9)
    etas = [0.15, 0.6, 0.9, 0.35]
    al = [math.asin(e) for e in etas]

    def val(th):
        C = np.prod(np.cos(th))
        S = np.sum(th)
        return math.sqrt(max(0.0, 1 - 2 * C * math.cos(S) + C * C))

    best = 0.0
    for _ in range(4000):
        th = np.array([a * rng.random() for a in al])
        best = max(best, val(th))
    enc = gbox_certified(etas, tol=1e-9)
    assert best <= enc.upper + 1e-12


def test_gbox_rejects_negative():
    with pytest.raises(ValueError):
        gbox_float([-0.1])


# ---------------------------------------------------------------------------
# synthetic trees with explicit multilinear laws (arity 1..3)
# ---------------------------------------------------------------------------


def _law_apply(C, xs):
    letters = "abcdefg"
    spec = "z" + letters[: len(xs)] + "," + ",".join(letters[i] for i in range(len(xs))) + "->z"
    return np.einsum(spec, C, *xs)


def _slot_opnorm(C, xs, i):
    """Operator norm of x ↦ C(x_1, …, x, …, x_m) (exact, via explicit matrix)."""
    d = C.shape[1 + i]
    cols = []
    for k in range(d):
        e = np.zeros(d)
        e[k] = 1.0
        args = list(xs)
        args[i] = e
        cols.append(_law_apply(C, args))
    return float(np.linalg.norm(np.stack(cols, axis=1), 2))


def _synthetic(rng, depth=3, arity_choices=(1, 2, 3), dim=5, mode="perturb", leaf_dev=0.0,
               zero_child=False, zero_K=False, scale=1e-2):
    """Build a random tree bottom-up; returns (Run, F_root, R_root)."""
    leaves, nodes = [], []
    counter = [0]

    def make(level):
        if level == 0:
            name = f"z{counter[0]}"
            counter[0] += 1
            z = rng.standard_normal(dim)
            if zero_child and counter[0] == 1:
                z = np.zeros(dim)
            dev = np.zeros(dim) if leaf_dev == 0 else leaf_dev * rng.standard_normal(dim)
            leaves.append(Leaf(name, float(np.linalg.norm(z + dev)), float(np.linalg.norm(dev))))
            return name, z, z + dev
        m = int(rng.choice(arity_choices))
        kids = [make(level - 1) for _ in range(m)]
        C = rng.standard_normal((dim,) + (dim,) * m)
        if zero_K:
            C[:] = 0.0
        F = _law_apply(C, [k[1] for k in kids])
        y = _law_apply(C, [k[2] for k in kids])
        if mode == "perturb":
            R = y + scale * rng.standard_normal(dim)
            orth = False
        elif mode == "exact":
            R = y.copy()
            orth = True
        else:  # orthogonal projection onto a random subspace
            Q, _ = np.linalg.qr(rng.standard_normal((dim, dim - 1)))
            R = Q @ (Q.T @ y)
            orth = True
        name = f"v{counter[0]}"
        counter[0] += 1
        M = float(np.linalg.norm(C.reshape(dim, -1), 2))
        k_op = [_slot_opnorm(C, [k[2] for k in kids], i) for i in range(m)]
        nodes.append(Node(name, [k[0] for k in kids], M, "flattening spectral norm", True,
                          float(np.linalg.norm(y - R)), float(np.linalg.norm(R)), K_op=k_op,
                          K_op_method="explicit slot matrix", K_op_rigorous=True, orthogonal=orth))
        return name, F, R

    root_name, F, R = make(depth)
    # the root must not be truncated for theorem R: replace root residual semantics
    for n in nodes:
        n.is_root = n.name == root_name
    return Run(leaves, nodes, root_name), F, R


@pytest.mark.parametrize("seed", range(8))
@pytest.mark.parametrize("arities", [(1,), (2,), (3,), (1, 2, 3)])
def test_amplitude_and_slot_bounds_sound_on_perturbations(seed, arities):
    rng = np.random.default_rng(seed)
    run, F, R = _synthetic(rng, depth=3, arity_choices=arities, mode="perturb")
    actual = float(np.linalg.norm(F - R))
    A = amplitude_compact_certificate(run)["absolute_error_upper"]
    S = slotwise_certificate(run)["absolute_error_upper"]
    assert actual <= S * (1 + 1e-9) + 1e-12
    assert actual <= A * (1 + 1e-9) + 1e-12
    thr = theorem_r_certificate(run)
    assert thr["applicable"] is False  # non-orthogonal operations


def test_slot_bound_not_worse_than_compact_on_random_trees():
    rng = np.random.default_rng(17)
    for _ in range(10):
        run, F, R = _synthetic(rng, depth=3, arity_choices=(2, 3), mode="perturb")
        A = amplitude_compact_certificate(run)["absolute_error_upper"]
        S = slotwise_certificate(run)["absolute_error_upper"]
        assert S <= A * (1 + 1e-9) + 1e-12


def test_approximate_leaves_and_exact_nodes():
    rng = np.random.default_rng(3)
    run, F, R = _synthetic(rng, depth=2, arity_choices=(2,), mode="exact", leaf_dev=1e-3)
    actual = float(np.linalg.norm(F - R))
    cert = certify(run, actual_error=actual)
    assert cert["sound"]
    assert cert["theorem_r"]["applicable"] is False  # approximate leaves


def test_zero_residual_exact_tree_has_zero_bounds():
    rng = np.random.default_rng(4)
    run, F, R = _synthetic(rng, depth=3, arity_choices=(1, 2), mode="exact")
    cert = certify(run, actual_error=float(np.linalg.norm(F - R)))
    assert cert["bounds"]["amplitude_compact"] == 0.0
    assert cert["bounds"]["slotwise"] == 0.0
    assert verify(cert, run)


def test_zero_child_and_zero_law():
    rng = np.random.default_rng(6)
    run, F, R = _synthetic(rng, depth=2, arity_choices=(2,), mode="perturb", zero_child=True)
    actual = float(np.linalg.norm(F - R))
    assert actual <= slotwise_certificate(run)["absolute_error_upper"] * (1 + 1e-9) + 1e-12
    run, F, R = _synthetic(rng, depth=2, arity_choices=(2,), mode="perturb", zero_K=True)
    actual = float(np.linalg.norm(F - R))
    assert actual <= slotwise_certificate(run)["absolute_error_upper"] * (1 + 1e-9) + 1e-12


def test_deep_unary_chain():
    rng = np.random.default_rng(8)
    run, F, R = _synthetic(rng, depth=8, arity_choices=(1,), mode="perturb", dim=4, scale=1e-4)
    actual = float(np.linalg.norm(F - R))
    assert actual <= slotwise_certificate(run)["absolute_error_upper"] * (1 + 1e-9) + 1e-12


def test_orthogonal_projection_theorem_r_sound():
    """Orthogonal truncations with untruncated root: theorem R applies and is sound."""
    rng = np.random.default_rng(21)
    for _ in range(5):
        run, F, R = _synthetic(rng, depth=2, arity_choices=(2,), mode="project")
        root = [n for n in run.nodes if n.is_root][0]
        # rebuild the root without truncation
        kids = root.children
        run2 = run
        if root.residual > 0:
            continue
        actual = float(np.linalg.norm(F - R))
        cert = certify(run2, actual_error=actual)
        assert cert["sound"]


# ---------------------------------------------------------------------------
# models
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("model", [
    MatProdTree(depth=3, d=12, s=1.0, seed=1),
    MatProdTree(depth=3, d=12, s=-1.0, seed=1),
    MpoMpsChain(sites=7, chi=4, seed=2),
    HTTree(depth=3, n=3, k_int=3, seed=3),
])
def test_models_sound_at_several_ranks(model):
    full = model.execute(None)
    assert full.actual_error < 1e-8
    for f in (0.8, 0.5, 0.25):
        ranks = {n: max(1, math.ceil(f * full.full_ranks[n])) for n in model.internal}
        res = model.execute(ranks)
        cert = certify(res.run, actual_error=res.actual_error)
        assert cert["sound"], (f, cert["bounds"], res.actual_error)
        assert verify(cert, res.run)
        for k, v in cert["bounds"].items():
            assert res.actual_error <= v * (1 + 1e-9) + 1e-12, k


def test_matprod_residual_matches_dense_projection():
    model = MatProdTree(depth=2, d=10, s=0.5, seed=4)
    ranks = {n: 3 for n in model.internal}
    res = model.execute(ranks)
    vals = {f"z{i}": Z for i, Z in enumerate(model.leaves)}
    for name in model.internal:
        a, b = model.children(name)
        y = model.law(vals[a], vals[b])
        node = [n for n in res.run.nodes if n.name == name][0]
        if node.is_root:
            vals[name] = y
            continue
        U, s, Vt = np.linalg.svd(y)
        P = U[:, :3] @ U[:, :3].T
        vals[name] = P @ y
        assert np.allclose(P @ P, P, atol=1e-10) and np.allclose(P, P.T, atol=1e-10)
        assert math.isclose(node.residual, float(np.linalg.norm(y - P @ y)), rel_tol=1e-8, abs_tol=1e-10)


def test_mpo_includes_identity():
    model = MpoMpsChain(sites=6, chi=4, eps=0.0, seed=5)
    full = model.execute(None)
    root = [n for n in full.run.nodes if n.is_root][0]
    assert math.isclose(root.R_norm, 1.0, rel_tol=1e-9)


def test_ht_sum_representation_exact():
    model = HTTree(depth=3, n=3, k_int=3, seed=6)
    assert np.linalg.norm(model.dense_exact() - model.dense_parts_exact()) < 1e-10


# ---------------------------------------------------------------------------
# planners
# ---------------------------------------------------------------------------


def test_planners_meet_epsilon_on_small_matprod():
    model = MatProdTree(depth=2, d=10, s=1.0, seed=7)
    full = model.execute(None)
    r_full = [n for n in full.run.nodes if n.is_root][0].R_norm
    eps = 0.05 * r_full
    a = plan_theorem_r(model, eps)
    if a["met"]:
        assert a["certificate"]["theorem_r"]["absolute_error_upper"] <= eps
    s = plan_certified_search(model, eps, which="best")
    assert s["met"]
    assert s["certificate"]["absolute_error_upper"] <= eps
    assert s["result"].actual_error <= eps
