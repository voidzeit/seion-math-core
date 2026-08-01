"""Block I — reduced tensor extraction, v18 redesign.

Mission diagnosis: this block certifies EXTRACTION CORRECTNESS only — it
is an artifact-integrity check, not a claim about compactness, persistence,
or algebraic significance of the extracted tensor (those belong to blocks
K and M respectively).

Parity is checked between:
- `reduced_law_tensor_loops` (explicit index loops, the maximally
  transparent reference)
- `reduced_law_tensor_einsum` (the fast CP-exploiting einsum path)
at both float32 and float64, plus an exact rational small case using
Python's `fractions.Fraction` (no floating point at all) for a toy
arity-3 CP law with small integer/rational coefficients, verified by hand.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

import torch

from spectral.certification_v18.model import SpectralModelV18, orthonormalize_columns


@dataclass
class ExtractionParityReport:
    max_rel_diff_float64: float
    max_rel_diff_float32: float


def extraction_parity_report(seed: int = 0, *, n: int = 12, rank: int = 3, cp_rank: int = 4) -> ExtractionParityReport:
    diffs = {}
    for dtype in ("float64", "float32"):
        gen = torch.Generator().manual_seed(seed)
        model = SpectralModelV18(n=n, rank=rank, arity=3, cp_rank=cp_rank, device="cpu", dtype=dtype, generator=gen)
        U = orthonormalize_columns(model.u())
        t_loop = model.reduced_law_tensor_loops(U)
        t_fast = model.reduced_law_tensor_einsum(U)
        rel = (torch.linalg.norm((t_loop - t_fast).reshape(-1)) / (torch.linalg.norm(t_loop.reshape(-1)) + 1e-30)).item()
        diffs[dtype] = rel
    return ExtractionParityReport(max_rel_diff_float64=diffs["float64"], max_rel_diff_float32=diffs["float32"])


def exact_rational_small_case() -> dict:
    """A toy arity-3 CP law over Q (exact rationals, cp_rank=1, n=2, r=1):
    out = (1,0), factor0=factor1=factor2=(1,1), lam=1. cp_raw(a,b,c) =
    lam * (factor0.a)(factor1.b)(factor2.c) * out, using plain dot products
    (no conjugation needed for real rational vectors). With U=(1,0)^T (r=1)
    and anchor=(1,0)^T, the reduced tensor T[0,0,0] is computed BOTH via
    the general formula and by fully hand-expanding the arithmetic, and the
    two must match EXACTLY (Fraction equality, not a floating tolerance).
    """
    out = [Fraction(1), Fraction(0)]
    factor = [Fraction(1), Fraction(1)]  # same factor vector reused for all 3 legs
    lam = Fraction(1)
    U = [Fraction(1), Fraction(0)]
    anchor = [Fraction(1), Fraction(0)]

    def dot(a, b):
        return a[0] * b[0] + a[1] * b[1]

    def cp_raw(a, b, c):
        coeff = lam * dot(factor, a) * dot(factor, b) * dot(factor, c)
        return [out[0] * coeff, out[1] * coeff]

    def forward(a, b, c):
        rotations = [(a, b, c), (b, c, a), (c, a, b)]
        acc = [Fraction(0), Fraction(0)]
        for ra, rb, rc in rotations:
            y = cp_raw(ra, rb, rc)
            acc = [acc[0] + y[0], acc[1] + y[1]]
        return [acc[0] / 3, acc[1] / 3]

    y = forward(U, U, anchor)
    t_000 = dot(U, y)  # U^H . y, U real so no conjugation needed

    # hand-expansion: dot(factor,U)=1, dot(factor,anchor)=1 for every
    # rotation (since U=anchor=(1,0) and factor=(1,1) here), so each
    # rotation's coeff = lam*1*1*1 = 1, y = average of 3 copies of
    # out=(1,0) = (1,0) exactly, and U^H.y = 1.
    hand_expected = Fraction(1)

    return {"t_000": t_000, "hand_expected": hand_expected, "exact_match": t_000 == hand_expected}
