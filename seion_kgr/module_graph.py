"""Gate 13.3 (``campaigns/gate13/``): module registry + ablation context
managers for ``attribution.py``.

Scope decision (see ``campaigns/gate13/preregistration.md`` §5c for the
full rationale): the mission brief's per-layer module list
(``path.layer_0.message``, ``path.layer_1.projector``, ...) does not map
onto this codebase's actual architecture — every reasoning layer reuses
the SAME ``mu``/``U``/``V``/``W``/``projector`` weights
(``PathReasoner.message`` is called identically at every layer), so
"layer 0's message function" and "layer 1's message function" are not
independently ablatable parameters. The tractable, genuinely
non-trivial-to-attribute granularity is the path reasoner's INTERNAL
composition instead:

- ``mu``: the CP ternary law term, ``self.mu(x_u, a_edge, q_query)``.
- ``residual``: the linear residual terms, ``U(x_u) + V(a_edge) + W(q_query)``.
- ``projector``: the Stiefel projection applied to their sum.

These three feed into a SHARED nonlinearity (mean-aggregate across
incoming edges, then ``LayerNorm(tanh(.))``) that is repeated across
``num_layers`` hops — genuinely composing nonlinearly across layers, unlike
the higher-level branches (path/seion/structural_kernel), whose
contributions to the TOTAL SCORE are a plain sum (`s = s_base + gamma*s_path
+ eta*s_seion + s_kernel`) and are therefore additively decomposable by
construction — attributing THAT decomposition is exact and
order-independent for a trivial reason (see ``attribution.py``'s
``branch_level_telescoping``), not a property attribution needed to
discover.
"""
from __future__ import annotations

from contextlib import contextmanager
from typing import Iterable

import torch

from .reasoner import PathReasoner

PATH_INTERNAL_MODULES = ("mu", "residual", "projector")
BRANCH_MODULES = ("path", "seion", "structural_kernel")


@contextmanager
def ablate_path_components(reasoner: PathReasoner, active: Iterable[str]):
    """Temporarily replace ``reasoner.message`` with a version that only
    includes the components named in ``active`` (subset of
    ``PATH_INTERNAL_MODULES``); every other component's contribution is
    replaced with exact zero (not removed from the computation graph —
    this is an ABLATION, "what if this term were absent", not a structural
    change). Restores the original ``message`` method on exit, even if the
    body raises."""
    active = set(active)
    unknown = active - set(PATH_INTERNAL_MODULES)
    if unknown:
        raise ValueError(f"unknown path-internal module id(s): {unknown}, expected subset of {PATH_INTERNAL_MODULES}")
    original_message = reasoner.message

    def patched_message(x_u: torch.Tensor, a_edge: torch.Tensor, q_query: torch.Tensor) -> torch.Tensor:
        m_tilde = torch.zeros_like(x_u)
        if "mu" in active:
            m_tilde = m_tilde + reasoner.mu(x_u, a_edge, q_query)
        if "residual" in active:
            m_tilde = m_tilde + reasoner.U(x_u) + reasoner.V(a_edge) + reasoner.W(q_query)
        if "projector" in active and reasoner.projector.enabled:
            return reasoner.projector.apply(m_tilde)
        return m_tilde

    reasoner.message = patched_message
    try:
        yield
    finally:
        reasoner.message = original_message


@contextmanager
def corrupt_module(reasoner: PathReasoner, module_id: str, scale: float = 50.0, seed: int = 0):
    """Negative control (mission brief §13.3, "corromper deliberadamente un
    único proyector"): temporarily replace ``module_id``'s behavior with a
    corrupted version, restoring the original on exit. ``module_id`` in
    ``PATH_INTERNAL_MODULES``.

    ``mu``/``residual`` are corrupted by overwriting their trainable
    weights with large-magnitude random noise (default 50x a
    standard-normal init) so the corrupted module dominates whatever else
    it is compared against. ``projector`` is corrupted differently — by
    monkeypatching ``.apply`` directly, NOT by re-randomizing its
    ``raw`` parameter: ``StiefelProjector.Q()`` retracts via
    ``torch.linalg.qr``, which is scale-invariant (``qr(c*raw)`` and
    ``qr(raw)`` give the same orthonormal ``Q`` up to per-column sign for
    any ``c>0``), so scaling ``raw`` would NOT actually change the
    projector's behavior — a real, worth-documenting consequence of the
    Stiefel reparameterization, not a limitation of this test."""
    if module_id not in PATH_INTERNAL_MODULES:
        raise ValueError(f"module_id must be one of {PATH_INTERNAL_MODULES}, got {module_id!r}")
    gen = torch.Generator().manual_seed(seed)

    if module_id == "projector":
        if not reasoner.projector.enabled:
            raise ValueError("cannot corrupt the projector: it is disabled (proj_rank=0)")
        original_apply = reasoner.projector.apply
        reasoner.projector.apply = lambda x: -scale * x  # sign-flipped, blown-up: clearly wrong, not just "a different projection"
        try:
            yield
        finally:
            reasoner.projector.apply = original_apply
        return

    layers = (
        [reasoner.mu.A, reasoner.mu.B, reasoner.mu.C, reasoner.mu.O] if module_id == "mu"
        else [reasoner.U, reasoner.V, reasoner.W]
    )
    originals = []
    try:
        for layer in layers:
            originals.append((layer, layer.weight.data.clone()))
            layer.weight.data.copy_(scale * torch.randn(layer.weight.shape, generator=gen))
        yield
    finally:
        for layer, original_tensor in originals:
            layer.weight.data.copy_(original_tensor)
