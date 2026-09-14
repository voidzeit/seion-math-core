"""Campaign Phase B3: E8 residual branch + matched controls.

Uses a small synthetic "fake E8-shaped" tensor for every test that must
run in CI (no 59MB file there); the real ``E8_Exact_v18_2/f_E8.npy`` is
exercised in ``test_e8_exact_real_kernel_loads_and_runs_when_available``
and ``test_variants_share_architecture_real_kernel``, both skipped
automatically when the file is absent.
"""
import pytest
import torch

from seion_kgr.structural_kernel import (
    DEFAULT_E8_INFO_PATH,
    DEFAULT_E8_KERNEL_PATH,
    StructuralKernelResidual,
    VARIANTS,
    build_kernel,
    load_e8_info,
    load_e8_kernel,
)

pytestmark = pytest.mark.symbolic

_HAS_REAL_E8 = DEFAULT_E8_KERNEL_PATH.is_file()


def _fake_e8_like(kernel_dim=6, seed=0):
    gen = torch.Generator().manual_seed(seed)
    return torch.randn(kernel_dim, kernel_dim, kernel_dim, generator=gen)


# ------------------------------------------------------------------ build_kernel / provenance


def test_zero_kernel_is_exactly_zero_and_hashed():
    fake = _fake_e8_like()
    K, prov = build_kernel("zero_kernel", e8_kernel=fake)
    assert torch.equal(K, torch.zeros_like(fake))
    assert prov.frobenius_norm == 0.0
    assert len(prov.sha256) == 64


def test_random_scale_matched_has_matching_frobenius_norm():
    fake = _fake_e8_like()
    K, prov = build_kernel("random_scale_matched", e8_kernel=fake, seed=1)
    target = float(torch.linalg.norm(fake.reshape(-1)).item())
    assert abs(prov.frobenius_norm - target) < 1e-4
    assert K.shape == fake.shape


def test_permuted_indices_preserves_frobenius_norm_but_changes_values():
    fake = _fake_e8_like()
    K, prov = build_kernel("permuted_indices", e8_kernel=fake, seed=2)
    assert abs(prov.frobenius_norm - float(torch.linalg.norm(fake.reshape(-1)).item())) < 1e-4
    assert not torch.equal(K, fake)  # permutation actually changed the layout (astronomically unlikely to be identity)


def test_sign_shuffled_preserves_magnitudes_changes_signs():
    fake = _fake_e8_like()
    K, prov = build_kernel("sign_shuffled", e8_kernel=fake, seed=3)
    assert torch.allclose(K.abs(), fake.abs(), atol=1e-6)
    assert not torch.equal(K, fake)


def test_unknown_variant_rejected():
    with pytest.raises(ValueError):
        build_kernel("not_a_real_variant", e8_kernel=_fake_e8_like())


def test_permuted_and_sign_shuffled_require_a_real_kernel():
    with pytest.raises(ValueError):
        build_kernel("permuted_indices", e8_kernel=None, dim=4)
    with pytest.raises(ValueError):
        build_kernel("E8_exact", e8_kernel=None, dim=4)


def test_all_variants_produce_distinct_hashes_from_the_same_base_kernel():
    fake = _fake_e8_like()
    hashes = set()
    for variant in ("zero_kernel", "random_scale_matched", "permuted_indices", "sign_shuffled"):
        _, prov = build_kernel(variant, e8_kernel=fake, seed=7)
        hashes.add(prov.sha256)
    assert len(hashes) == 4  # every control is a genuinely different tensor


# ------------------------------------------------------------------ StructuralKernelResidual: architecture, gradients, matched controls


def _residual_for(variant: str, dim=5, kernel_dim=6, num_rel=4, seed=0) -> StructuralKernelResidual:
    fake = _fake_e8_like(kernel_dim=kernel_dim, seed=seed)
    K, prov = build_kernel(variant, e8_kernel=fake, seed=seed)
    return StructuralKernelResidual(dim=dim, K=K, num_relations_total=num_rel, provenance=prov)


@pytest.mark.parametrize("variant", ["zero_kernel", "random_scale_matched", "permuted_indices", "sign_shuffled"])
def test_forward_runs_and_is_finite_for_every_ci_testable_variant(variant):
    residual = _residual_for(variant)
    x, a, q = torch.randn(3, 5), torch.randn(3, 5), torch.randn(3, 5)
    relation_ids = torch.tensor([0, 1, 2])
    out = residual(x, a, q, relation_ids)
    assert out.shape == (3, 5)
    assert torch.isfinite(out).all()


def test_zero_kernel_residual_contributes_exactly_zero_regardless_of_gate():
    """Gate 7 style control: a zero kernel must produce zero residual
    output even if epsilon is manually set far from its near-zero init —
    the zero-ness must come from K, not merely from the init."""
    residual = _residual_for("zero_kernel")
    with torch.no_grad():
        residual.epsilon_raw.weight.fill_(10.0)  # sigmoid(10) ~ 1.0, gate wide open
    x, a, q = torch.randn(2, 5), torch.randn(2, 5), torch.randn(2, 5)
    out = residual(x, a, q, torch.tensor([0, 1]))
    assert torch.linalg.norm(out).item() == 0.0


def test_zero_init_gate_makes_residual_contribution_exactly_zero():
    """Gate 13.1 reparameterization (``campaigns/gate13/``): the gate is now
    ``g_max*tanh(epsilon_raw)`` with ``epsilon_raw`` initialized to exactly
    0, so ``gate(0) == 0`` exactly (was ``sigmoid(-4) ~= 0.018``, near-zero
    but never exactly zero)."""
    residual = _residual_for("random_scale_matched")
    x, a, q = torch.randn(4, 5), torch.randn(4, 5), torch.randn(4, 5)
    out = residual(x, a, q, torch.tensor([0, 1, 2, 3]))
    gate = (residual.gate_g_max * torch.tanh(residual.epsilon_raw.weight)).mean().item()
    assert gate == 0.0
    assert torch.equal(out, torch.zeros_like(out))  # exact-zero gate -> exact-zero branch output at init


def test_gate_gets_gradient_at_init_but_adapters_only_after_the_gate_moves():
    """A multiplicative zero-init gate (``out = gate * branch(...)``) has a
    real, expected consequence: at ``gate == 0`` exactly, the branch's own
    internal adapters (``Ux``/``Ua``/``Uq``/``W``) get EXACTLY zero gradient
    (their contribution is scaled by 0 before it reaches the loss), while the
    gate parameter itself still gets a nonzero gradient (``d(gate)/d(alpha)``
    at ``alpha=0`` is ``gate_g_max``, not 0). This is the same tradeoff
    documented in ``model.py``'s Gate 13.1 docstring for the path/seion
    router gates. Once the gate has taken one step away from exactly 0, the
    adapters start receiving gradient too."""
    residual = _residual_for("random_scale_matched")
    x = torch.randn(3, 5, requires_grad=True)
    a = torch.randn(3, 5, requires_grad=True)
    q = torch.randn(3, 5, requires_grad=True)
    out = residual(x, a, q, torch.tensor([0, 1, 2])).sum()
    out.backward()
    for name in ("Ux", "Ua", "Uq", "W"):
        layer = getattr(residual, name)
        assert layer.weight.grad is None or float(layer.weight.grad.norm().item()) == 0.0, name
    assert residual.epsilon_raw.weight.grad is not None
    assert float(residual.epsilon_raw.weight.grad.norm().item()) > 0.0
    assert residual.K.grad is None  # buffer, never trainable, structurally cannot accumulate a gradient
    assert x.grad is not None and a.grad is not None and q.grad is not None
    assert torch.equal(x.grad, torch.zeros_like(x.grad))  # eps=0 also blocks input gradient, same reasoning

    # Move the gate away from exactly 0 (mimics the effect of one optimizer
    # step on epsilon_raw), then re-run: adapters now get real gradient.
    with torch.no_grad():
        residual.epsilon_raw.weight.add_(0.1)
    residual.zero_grad()
    out2 = residual(x.detach().requires_grad_(), a.detach().requires_grad_(), q.detach().requires_grad_(), torch.tensor([0, 1, 2])).sum()
    out2.backward()
    for name in ("Ux", "Ua", "Uq", "W"):
        layer = getattr(residual, name)
        assert layer.weight.grad is not None and float(layer.weight.grad.norm().item()) > 0.0, name


def test_gate_differs_per_relation_after_a_training_step():
    torch.manual_seed(0)
    residual = _residual_for("random_scale_matched", num_rel=3)
    # Optimize ONLY the gate (isolates the effect being tested from the
    # adapters/W also moving, and avoids the divergence a naive
    # high-lr joint SGD step produced here initially).
    x, a, q = torch.randn(3, 5), torch.randn(3, 5), torch.randn(3, 5)
    relation_ids = torch.tensor([0, 1, 2])

    # Probe each relation's natural (pre-gate) branch-output sign, so the
    # loss below can reliably push relation 0's gate positive and relation
    # 2's gate negative REGARDLESS of that random sign. Without this, a loss
    # built directly from the raw (random-sign) branch output can push both
    # gates in the same direction — Adam's step is ~sign(grad), not
    # magnitude-proportional, so two same-sign, same-shape gradients drive
    # both gates along near-identical trajectories from the same zero init,
    # landing on indistinguishable values even though nothing is broken.
    with torch.no_grad():
        residual.epsilon_raw.weight.fill_(2.0)  # temporarily open the gate to read the branch's sign
        probe = residual(x, a, q, relation_ids)
        sign0 = torch.sign(probe[0].sum()).item() or 1.0
        sign2 = torch.sign(probe[2].sum()).item() or 1.0
        residual.epsilon_raw.weight.fill_(0.0)  # reset to the true zero init before the real test

    opt = torch.optim.Adam([residual.epsilon_raw.weight], lr=0.05)
    for _ in range(20):
        opt.zero_grad()
        out = residual(x, a, q, relation_ids)
        # A LINEAR reduction of ``out``, not a square: at the gate's exact-
        # zero init, ``d(out**2)/d(gate) = 2*out*d(out)/d(gate) = 0`` because
        # ``out`` itself is 0 there (a genuine saddle point for any loss
        # that is stationary in ``out`` at ``out=0``) — a linear reduction
        # has ``d(loss)/d(gate) = d(loss)/d(out) . d(out)/d(gate)``, nonzero
        # as long as ``d(out)/d(gate) = branch_raw`` is (generically nonzero),
        # matching how the real KGE ranking loss is linear in the gated
        # branch's contribution to the total score, not quadratic in it.
        loss = -sign0 * out[0].sum() + sign2 * out[2].sum()  # deterministically pushes relation 0's gate up, relation 2's down
        loss.backward()
        opt.step()
    # Compare the PRE-activation alpha, not the post-tanh gate: a large
    # enough learning rate saturates tanh to +-1 for both relations, which
    # would mask a real (still-differing) alpha under a post-tanh comparison
    # — the low lr here keeps both in the unsaturated regime as a sanity
    # check too.
    alpha = residual.epsilon_raw.weight.detach().squeeze(-1)
    gates = residual.gate_g_max * torch.tanh(alpha)
    assert torch.isfinite(gates).all()
    assert abs(float(alpha[0] - alpha[2])) > 1e-4
    assert abs(float(gates[0] - gates[2])) > 1e-4


def test_matched_controls_share_identical_architecture_and_trainable_param_count():
    """The mandate's 'as closely as mathematically possible matched'
    requirement: every variant built from the same fake kernel shape
    must have the SAME trainable-parameter count outside the frozen
    buffer, so a downstream comparison isn't confounded by capacity."""
    counts = set()
    for variant in ("zero_kernel", "random_scale_matched", "permuted_indices", "sign_shuffled"):
        residual = _residual_for(variant)
        counts.add(residual.parameter_count_outside_kernel())
    assert len(counts) == 1, f"matched controls have different trainable parameter counts: {counts}"


def test_mu_kernel_matches_v25_fixed_predict_formula_directly():
    """Direct arithmetic cross-check against the same double-contraction
    formula, computed independently with plain einsum calls (not by
    calling mu_kernel itself), so this isn't just testing that the code
    equals itself."""
    dim, kernel_dim = 4, 5
    fake = _fake_e8_like(kernel_dim=kernel_dim, seed=9)
    K, prov = build_kernel("random_scale_matched", e8_kernel=fake, seed=9)
    residual = StructuralKernelResidual(dim=dim, K=K, num_relations_total=2, provenance=prov)
    x = torch.randn(kernel_dim)
    a = torch.randn(kernel_dim)
    q = torch.randn(kernel_dim)

    got = residual.mu_kernel(x, a, q)
    inner_expected = torch.einsum("bcf,b,c->f", K, a, q)
    matrix_expected = torch.einsum("afd,f->ad", K, inner_expected)
    expected = torch.einsum("ad,a->d", matrix_expected, x)
    assert torch.allclose(got, expected, atol=1e-6)


# ------------------------------------------------------------------ real E8 kernel (local-only, skipped in CI)


@pytest.mark.skipif(not _HAS_REAL_E8, reason="E8_Exact_v18_2/f_E8.npy not present (not committed to git)")
def test_e8_exact_real_kernel_loads_and_runs_when_available():
    K_e8 = load_e8_kernel()
    assert K_e8.shape == (248, 248, 248)
    K, prov = build_kernel("E8_exact", e8_kernel=K_e8, e8_info=load_e8_info())
    assert prov.variant == "E8_exact"
    assert prov.shape == (248, 248, 248)
    assert prov.kernel_properties.get("is_e8_like") is True  # inherited metadata, reported as a kernel property
    assert prov.kernel_properties.get("killing_rank") == 248

    residual = StructuralKernelResidual(dim=16, K=K, num_relations_total=4, provenance=prov)
    x, a, q = torch.randn(2, 16), torch.randn(2, 16), torch.randn(2, 16)
    out = residual(x, a, q, torch.tensor([0, 1]))
    assert out.shape == (2, 16)
    assert torch.isfinite(out).all()


@pytest.mark.skipif(not _HAS_REAL_E8, reason="E8_Exact_v18_2/f_E8.npy not present (not committed to git)")
def test_variants_share_architecture_real_kernel():
    K_e8 = load_e8_kernel()
    dim = 8
    outputs = {}
    for variant in VARIANTS:
        K, prov = build_kernel(variant, e8_kernel=K_e8, e8_info=load_e8_info(), seed=13)
        residual = StructuralKernelResidual(dim=dim, K=K, num_relations_total=2, provenance=prov)
        with torch.no_grad():
            residual.epsilon_raw.weight.fill_(10.0)  # open the gate to actually compare kernel effects
        torch.manual_seed(0)
        x, a, q = torch.randn(2, dim), torch.randn(2, dim), torch.randn(2, dim)
        outputs[variant] = residual(x, a, q, torch.tensor([0, 1]))
    # E8_exact must differ from zero_kernel (nontrivial structure) and,
    # almost surely, from the random/permuted/sign-shuffled controls
    # (this does NOT claim E8 is "better" — only that it is a distinct
    # object, which is a precondition for any later causal comparison).
    assert not torch.allclose(outputs["E8_exact"], outputs["zero_kernel"])
    for control in ("random_scale_matched", "permuted_indices", "sign_shuffled"):
        assert not torch.allclose(outputs["E8_exact"], outputs[control])
