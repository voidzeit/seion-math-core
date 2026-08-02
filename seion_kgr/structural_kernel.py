"""Campaign Phase B3: controlled structural-kernel residual branch (E_8 and matched controls).

Contract explicitly scoped `E_8` out of the numbered build sequence
until a control battery existed (CLM_KGR_018). This module is that
battery: `StructuralKernelResidual` wraps a FROZEN, fixed rank-3 tensor
``K`` of shape ``[kernel_dim, kernel_dim, kernel_dim]`` — the same
double-contraction construction already validated in
``seion_train_v25.py``'s `fixed_predict` (its self-test checks
``positive == head_gold == tail_gold`` to within 1e-5 for that exact
formula) — behind dimension-adapting linear maps and a near-zero-init
per-relation residual gate:

    mu_total = mu_learned + sigmoid(epsilon[r]) * W(mu_kernel(Ux(x), Ua(a), Uq(q)))

Five variants share the identical architecture and only differ in what
``K`` is:

    E8_exact              — E8_Exact_v18_2/f_E8.npy (248^3, real, local-only)
    random_scale_matched  — random tensor, same shape + Frobenius norm
    permuted_indices      — E8's own values, axes independently permuted
    sign_shuffled         — E8's own |values|, signs independently randomized
    zero_kernel           — all-zero (predictor collapses to mu_learned alone)

``E8_exact`` requires ``E8_Exact_v18_2/f_E8.npy`` on local disk — that
59MB file is intentionally NOT committed to git (same convention as
``data/``), so it is unavailable in CI. Every other variant needs no
external file (it is either synthetic or derived from an in-repo-sized
fixture the caller supplies), so the control machinery itself is fully
testable in CI even though the real E8 comparison is not.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np
import torch
import torch.nn as nn

VARIANTS = ("E8_exact", "random_scale_matched", "permuted_indices", "sign_shuffled", "zero_kernel")

DEFAULT_E8_KERNEL_PATH = Path("E8_Exact_v18_2/f_E8.npy")
DEFAULT_E8_INFO_PATH = Path("E8_Exact_v18_2/info.json")


@dataclass
class KernelProvenance:
    variant: str
    shape: tuple
    sha256: str
    frobenius_norm: float
    source: str
    seed: Optional[int] = None
    kernel_properties: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "variant": self.variant, "shape": list(self.shape), "sha256": self.sha256,
            "frobenius_norm": self.frobenius_norm, "source": self.source, "seed": self.seed,
            "kernel_properties": self.kernel_properties,
        }


def _tensor_sha256(t: torch.Tensor) -> str:
    return hashlib.sha256(t.detach().cpu().numpy().tobytes()).hexdigest()


def load_e8_kernel(path: Path = DEFAULT_E8_KERNEL_PATH) -> torch.Tensor:
    if not path.is_file():
        raise FileNotFoundError(
            f"E8_exact requires {path} (not committed to git, same convention as data/ — "
            "place the file locally, or use a matched-control variant instead)."
        )
    arr = np.load(path)
    return torch.from_numpy(arr.astype(np.float32))


def load_e8_info(path: Path = DEFAULT_E8_INFO_PATH) -> Dict[str, Any]:
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def build_kernel(
    variant: str,
    *,
    e8_kernel: Optional[torch.Tensor] = None,
    dim: Optional[int] = None,
    seed: int = 0,
    e8_info: Optional[Dict[str, Any]] = None,
) -> tuple:
    """Returns ``(K, KernelProvenance)``. ``e8_kernel`` must be supplied
    (already loaded) for every variant except ``zero_kernel``/
    ``random_scale_matched`` when used standalone with an explicit
    ``dim`` (e.g. for CI, where no real E8 file is available but the
    control machinery must still be testable against SOME fixed-shape
    tensor)."""
    if variant not in VARIANTS:
        raise ValueError(f"variant must be one of {VARIANTS}, got {variant!r}")

    gen = torch.Generator().manual_seed(seed)

    if variant == "zero_kernel":
        shape = tuple(e8_kernel.shape) if e8_kernel is not None else (dim, dim, dim)
        K = torch.zeros(shape)
        return K, KernelProvenance("zero_kernel", shape, _tensor_sha256(K), 0.0, "synthetic:zero", seed)

    if variant == "random_scale_matched":
        if e8_kernel is not None:
            shape = tuple(e8_kernel.shape)
            target_norm = float(torch.linalg.norm(e8_kernel.reshape(-1)).item())
        else:
            if dim is None:
                raise ValueError("random_scale_matched without e8_kernel requires dim")
            shape = (dim, dim, dim)
            target_norm = float(np.sqrt(np.prod(shape)))  # unit-variance-ish default target
        raw = torch.randn(shape, generator=gen)
        raw = raw * (target_norm / torch.linalg.norm(raw.reshape(-1)).clamp_min(1e-12))
        return raw, KernelProvenance("random_scale_matched", shape, _tensor_sha256(raw), float(torch.linalg.norm(raw.reshape(-1)).item()), "synthetic:random_scale_matched", seed)

    # permuted_indices, sign_shuffled, E8_exact all require the real kernel
    if e8_kernel is None:
        raise ValueError(f"variant {variant!r} requires e8_kernel (the real loaded E8 tensor)")
    shape = tuple(e8_kernel.shape)

    if variant == "E8_exact":
        K = e8_kernel.clone()
        props = dict(e8_info or {})
        return K, KernelProvenance("E8_exact", shape, _tensor_sha256(K), float(torch.linalg.norm(K.reshape(-1)).item()), str(DEFAULT_E8_KERNEL_PATH), None, props)

    if variant == "permuted_indices":
        d0, d1, d2 = shape
        p0 = torch.randperm(d0, generator=gen)
        p1 = torch.randperm(d1, generator=gen)
        p2 = torch.randperm(d2, generator=gen)
        K = e8_kernel[p0][:, p1][:, :, p2].clone()
        return K, KernelProvenance("permuted_indices", shape, _tensor_sha256(K), float(torch.linalg.norm(K.reshape(-1)).item()), "derived:E8_exact+permutation", seed)

    if variant == "sign_shuffled":
        signs = (torch.randint(0, 2, shape, generator=gen).float() * 2 - 1)
        K = (e8_kernel.abs() * signs).clone()
        return K, KernelProvenance("sign_shuffled", shape, _tensor_sha256(K), float(torch.linalg.norm(K.reshape(-1)).item()), "derived:E8_exact+sign_shuffle", seed)

    raise AssertionError("unreachable")  # all VARIANTS handled above


class StructuralKernelResidual(nn.Module):
    """``mu_total = mu_learned + sigmoid(epsilon[r]) * W(mu_kernel(Ux x, Ua a, Uq q))``.

    ``mu_kernel`` is the same double-contraction construction as
    ``seion_train_v25.py``'s validated ``fixed_predict``: a single
    rank-3 tensor ``K`` used twice with different axis roles, not four
    independent CP factor matrices — this is what makes it a faithful
    reproduction of the E8 structure-constant object rather than a CP
    law with a different name.
    """

    def __init__(self, dim: int, K: torch.Tensor, num_relations_total: int, provenance: KernelProvenance, gate_g_max: float = 1.0):
        super().__init__()
        self.dim = dim
        self.kernel_dim = int(K.shape[0])
        self.provenance = provenance
        self.register_buffer("K", K, persistent=True)  # frozen — never a trainable parameter
        self.Ux = nn.Linear(dim, self.kernel_dim, bias=False)
        self.Ua = nn.Linear(dim, self.kernel_dim, bias=False)
        self.Uq = nn.Linear(dim, self.kernel_dim, bias=False)
        self.W = nn.Linear(self.kernel_dim, dim, bias=False)
        for layer in (self.Ux, self.Ua, self.Uq, self.W):
            nn.init.xavier_uniform_(layer.weight)
        # Gate 13.1: same zero-init tanh reparameterization as the path/seion
        # router gates in model.py (was sigmoid(epsilon_raw), init -4.0, near-
        # zero gradient at init — see model.py's module docstring).
        self.gate_g_max = gate_g_max
        self.epsilon_raw = nn.Embedding(num_relations_total, 1)
        nn.init.constant_(self.epsilon_raw.weight, 0.0)

    def mu_kernel(self, x: torch.Tensor, a: torch.Tensor, q: torch.Tensor) -> torch.Tensor:
        """Double contraction against the single frozen tensor ``K``,
        mirroring ``SeionV25.fixed_predict`` exactly (x plays the role of
        v25's first argument ``a``, a plays v25's ``b``, q plays v25's
        ``c``)."""
        inner = torch.einsum("bcf,...b,...c->...f", self.K, a, q)
        matrix = torch.einsum("afd,...f->...ad", self.K, inner)
        return torch.einsum("...ad,...a->...d", matrix, x)

    def forward(self, x: torch.Tensor, a: torch.Tensor, q: torch.Tensor, relation_ids: torch.Tensor) -> torch.Tensor:
        xk, ak, qk = self.Ux(x), self.Ua(a), self.Uq(q)
        raw = self.mu_kernel(xk, ak, qk)
        out = self.W(raw)
        eps = self.gate_g_max * torch.tanh(self.epsilon_raw(relation_ids).squeeze(-1))
        while eps.ndim < out.ndim:
            eps = eps.unsqueeze(-1)
        return eps * out

    def parameter_count_outside_kernel(self) -> int:
        """For matched-control accounting: trainable parameter count
        excluding the frozen ``K`` buffer (which never appears in
        `.parameters()` since it's a buffer, not a Parameter, but this
        makes the exclusion explicit and auditable)."""
        return sum(p.numel() for p in self.parameters() if p.requires_grad)
