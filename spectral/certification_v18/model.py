"""v18 differentiable geometry primitives.

This is a fresh reimplementation of the mathematical objects needed by the
A-N blocks (the n-ary cyclic CP law, the projector, the reduced curvature/
connection, and the "coherent dynamic curvature" candidate explanation for
[Delta, P]) — faithful to the formulas in
`spectral/legacy/v17/seion_master_audit_A_to_N_v17_blackwell_repro_fix.py`
(`CyclicCPProduct` at ~725, `SeionV17Model` at ~853), but written
independently rather than imported, for two reasons:

1. Importing the legacy module has a real side effect: at import time it
   unconditionally sets `torch.backends.cuda.matmul.allow_tf32 = True` and
   calls `torch.set_float32_matmul_precision("high")` if CUDA is available
   (lines 60-67 of the legacy file). That is exactly the kind of silent
   global-state contamination a certification-mode run (which requires
   TF32 disabled, see config.py) cannot tolerate.
2. What is under audit in v18 is the *evaluation methodology* around these
   objects (blocks, thresholds, baselines, controls) — not the objects
   themselves, which are legitimate mathematical constructions worth
   keeping. Re-deriving them here, with tests, keeps that methodology
   auditable without depending on a 2653-line legacy monolith that also
   contains argparse/CLI code this suite replaces entirely.

Every function below is checked in tests/test_model.py against small
hand-computable cases and against the algebraic identity
`[Delta, P] == K @ Delta @ P - P @ Delta @ K` (exact for any projector P,
independent of the CP law).
"""

from __future__ import annotations

import math
from typing import Sequence

import torch
from torch import nn


def resolve_dtype(name: str) -> torch.dtype:
    return {"float32": torch.float32, "float64": torch.float64}[name]


def complex_dtype_from_real(rdtype: torch.dtype) -> torch.dtype:
    return torch.complex64 if rdtype == torch.float32 else torch.complex128


def make_complex(re: torch.Tensor, im: torch.Tensor) -> torch.Tensor:
    return torch.complex(re, im)


def fro_norm(x: torch.Tensor) -> torch.Tensor:
    return torch.linalg.norm(x.reshape(-1))


def commutator(a: torch.Tensor, b: torch.Tensor) -> torch.Tensor:
    return a @ b - b @ a


def identity(n: int, *, device: str, dtype: torch.dtype) -> torch.Tensor:
    return torch.eye(n, device=device, dtype=dtype)


def orthonormalize_columns(u: torch.Tensor) -> torch.Tensor:
    q, r = torch.linalg.qr(u)
    d = torch.diagonal(r)
    phase = d / (torch.abs(d) + 1e-30)
    return q * phase.conj().unsqueeze(0)


def projector_from_u(u: torch.Tensor) -> torch.Tensor:
    return u @ u.conj().T


def hermitian_random(n: int, *, device: str, rdtype: torch.dtype, scale: float = 1.0, generator: torch.Generator | None = None) -> torch.Tensor:
    cdtype = complex_dtype_from_real(rdtype)
    re = torch.randn(n, n, device=device, dtype=rdtype, generator=generator)
    im = torch.randn(n, n, device=device, dtype=rdtype, generator=generator)
    a = make_complex(re, im) * scale
    return 0.5 * (a + a.conj().T)


class CyclicCPProduct(nn.Module):
    """CP n-ary law with explicit cyclic symmetrization: mu(x1..xn) is the
    average of CP_raw over all cyclic rotations of its arguments. Cyclic
    symmetry therefore holds up to floating-point noise BY CONSTRUCTION —
    this is the exact structural-identity concern block N must report
    separately from any learned property (see GATE_TAXONOMY.md, block N).
    """

    def __init__(self, n: int, arity: int, cp_rank: int, *, device: str, rdtype: torch.dtype, generator: torch.Generator | None = None):
        super().__init__()
        self.n = int(n)
        self.arity = int(arity)
        self.cp_rank = int(cp_rank)
        self.device = device
        self.rdtype = rdtype
        self.cdtype = complex_dtype_from_real(rdtype)

        def p(shape):
            return nn.Parameter(torch.randn(*shape, device=device, dtype=rdtype, generator=generator) / math.sqrt(max(n, 1)))

        self.out_re = p((n, cp_rank))
        self.out_im = p((n, cp_rank))
        self.in_re = nn.ParameterList([p((n, cp_rank)) for _ in range(arity)])
        self.in_im = nn.ParameterList([p((n, cp_rank)) for _ in range(arity)])
        self.log_lam = nn.Parameter(torch.zeros(cp_rank, device=device, dtype=rdtype))

    def out(self) -> torch.Tensor:
        return make_complex(self.out_re, self.out_im)

    def factor(self, j: int) -> torch.Tensor:
        return make_complex(self.in_re[j], self.in_im[j])

    def lam(self) -> torch.Tensor:
        return torch.exp(self.log_lam).to(self.cdtype)

    def cp_raw(self, xs: Sequence[torch.Tensor]) -> torch.Tensor:
        coeff = self.lam()
        for j, x in enumerate(xs):
            coeff = coeff * (torch.conj(self.factor(j)).T @ x)
        return self.out() @ coeff

    def forward(self, *xs: torch.Tensor) -> torch.Tensor:
        xlist = list(xs)
        acc = torch.zeros(self.n, dtype=self.cdtype, device=self.device)
        for shift in range(self.arity):
            rotated = xlist[shift:] + xlist[:shift]
            acc = acc + self.cp_raw(rotated)
        return acc / float(self.arity)


class SpectralModelV18(nn.Module):
    """Minimal geometry needed for blocks A, B, D, G, H, N (lo-scale only;
    E/J/K/M's hi-scale twin is added in their own phase-2 pass)."""

    def __init__(self, n: int, rank: int, arity: int, cp_rank: int, *, device: str, dtype: str, generator: torch.Generator | None = None):
        super().__init__()
        self.n, self.rank, self.arity = n, rank, arity
        self.rdtype = resolve_dtype(dtype)
        self.cdtype = complex_dtype_from_real(self.rdtype)
        self.device = device

        def p(shape):
            return nn.Parameter(torch.randn(*shape, device=device, dtype=self.rdtype, generator=generator) / math.sqrt(n))

        self.u_re = p((n, rank))
        self.u_im = p((n, rank))
        self.product = CyclicCPProduct(n, arity, cp_rank, device=device, rdtype=self.rdtype, generator=generator)
        self.register_buffer("delta", hermitian_random(n, device=device, rdtype=self.rdtype, generator=generator))
        anchor = torch.zeros(n, dtype=self.cdtype, device=device)
        anchor[0] = 1.0
        self.register_buffer("anchor", anchor)

    def u(self) -> torch.Tensor:
        return make_complex(self.u_re, self.u_im)

    def p(self) -> torch.Tensor:
        return projector_from_u(orthonormalize_columns(self.u()))

    def anchored_product(self, x: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
        extras = [self.anchor for _ in range(self.arity - 2)]
        return self.product(x, y, *extras)

    def associator(self, x: torch.Tensor, y: torch.Tensor, z: torch.Tensor) -> torch.Tensor:
        xy = self.anchored_product(x, y)
        yz = self.anchored_product(y, z)
        return self.anchored_product(xy, z) - self.anchored_product(x, yz)

    def reduced_connection(self, U: torch.Tensor) -> torch.Tensor:
        return U.conj().T @ self.delta @ U

    def reduced_curvature_matrix(self, U: torch.Tensor) -> torch.Tensor:
        cols = []
        for j in range(U.shape[1]):
            uj = U[:, j]
            assoc_j = self.associator(uj, self.anchor, self.anchor)
            cols.append(U.conj().T @ assoc_j)
        return torch.stack(cols, dim=1)

    def coherent_dynamic_curvature(self, U: torch.Tensor, K: torch.Tensor, Phi: torch.Tensor) -> torch.Tensor:
        left = U @ Phi @ U.conj().T @ self.delta @ K
        right = K @ self.delta @ U @ Phi.conj().T @ U.conj().T
        return left - right

    def reduced_law_tensor_loops(self, U: torch.Tensor) -> torch.Tensor:
        """Reduced (arity+1)-mode law tensor via explicit index loops (the
        slow, maximally-transparent reference implementation): for arity=3,
        T[i,j,k] := U[:,i]^H @ product(U[:,j], U[:,k], anchor, ..., anchor).
        Used only for parity checks against the fast einsum path — never
        used at scale."""
        r = U.shape[1]
        extras = [self.anchor for _ in range(self.arity - 2)]
        cols_j = []
        for j in range(r):
            cols_k = []
            for k in range(r):
                y = self.product(U[:, j], U[:, k], *extras)
                cols_k.append(U.conj().T @ y)  # (r,)
            cols_j.append(torch.stack(cols_k, dim=1))  # (r, r)
        return torch.stack(cols_j, dim=1)  # (r, r, r) indexed [i, j, k]

    def reduced_law_tensor_einsum(self, U: torch.Tensor) -> torch.Tensor:
        """Fast einsum-based reduced tensor extraction, algebraically
        equivalent to `reduced_law_tensor_loops` (including the cyclic
        AVERAGE over all `arity` rotations that `forward()` performs) but
        avoiding the Python double loop over (j,k). Restricted to arity=3,
        matching every other use of the CP law in this module.

        For arity=3 with call pattern product(U[:,j], U[:,k], anchor), the
        three cyclic rotations assign (xj, xk, anchor) to the law's three
        factor slots in a cycling pattern; this sums the einsum
        contribution of each rotation explicitly, then divides by arity —
        exactly what `forward()` does, verified against the loop version
        in tests/test_block_i.py.
        """
        if self.arity != 3:
            raise NotImplementedError("reduced_law_tensor_einsum is implemented for arity=3 only")
        r = U.shape[1]
        prod = self.product
        out_coeff = U.conj().T @ prod.out()  # (r, cp)
        out_coeff = out_coeff * prod.lam()[None, :]
        u_coeffs = [prod.factor(m).conj().T @ U for m in range(3)]  # each (cp, r)
        anchor_coeffs = [prod.factor(m).conj().T @ self.anchor for m in range(3)]  # each (cp,)

        # rotation s: slot assignment (which factor index sees xj, xk, anchor)
        # s=0: (xj->0, xk->1, anchor->2); s=1: (xj->2, xk->0, anchor->1); s=2: (xj->1, xk->2, anchor->0)
        slot_for_j = [0, 2, 1]
        slot_for_k = [1, 0, 2]
        slot_for_anchor = [2, 1, 0]

        total = torch.zeros(r, r, r, dtype=self.cdtype, device=self.device)
        for s in range(3):
            weighted = out_coeff * anchor_coeffs[slot_for_anchor[s]][None, :]
            total = total + torch.einsum("ic,cj,ck->ijk", weighted, u_coeffs[slot_for_j[s]], u_coeffs[slot_for_k[s]])
        return total / 3.0
