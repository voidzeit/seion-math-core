"""Block N — cyclic law and versioned GJI formula, v18 redesign.

Mission diagnosis: `CyclicCPProduct.forward` (model.py) averages over all
cyclic rotations of its arguments, so near-zero cyclic defect measured on
`forward()` is a CONSTRUCTION IDENTITY (holds by averaging, not because
symmetry was "learned"). This module reports the RAW (unsymmetrized,
`cp_raw`) defect and the SYMMETRIZED (`forward`) defect SEPARATELY, and
never describes the symmetrized number as evidence of anything beyond
floating-point roundoff.

GJI_v18: ONE exact, versioned formula —

    GJI(x,y,z) := sum over all 6 permutations sigma of {x,y,z}
                  of sign(sigma) * A(sigma(x,y,z))

where A is the anchored associator and sign(sigma) is the permutation
parity (+1 even, -1 odd: identity/3-cycles are +1, transpositions are -1).
This is the FULL antisymmetrization of the associator over its 3 arguments
(matching the legacy script's `gji_loss`, ~line 1160, reimplemented here
independently via `itertools.permutations` + parity rather than the
legacy's manually unrolled 6-term expression, so the two can be
cross-checked against each other).
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass

import torch

from spectral.certification_v18.model import SpectralModelV18, orthonormalize_columns


def _permutation_sign(perm: tuple[int, ...]) -> int:
    perm = list(perm)
    n = len(perm)
    visited = [False] * n
    sign = 1
    for i in range(n):
        if visited[i]:
            continue
        cycle_len = 0
        j = i
        while not visited[j]:
            visited[j] = True
            j = perm[j]
            cycle_len += 1
        if cycle_len % 2 == 0:
            sign *= -1
    return sign


def gji_independent_implementation(model: SpectralModelV18, x: torch.Tensor, y: torch.Tensor, z: torch.Tensor) -> torch.Tensor:
    """Independent implementation: iterate itertools.permutations and
    permutation parity directly, rather than a hand-unrolled 6-term sum."""
    args = [x, y, z]
    total = torch.zeros_like(x)
    for perm in itertools.permutations(range(3)):
        sign = _permutation_sign(perm)
        a, b, c = args[perm[0]], args[perm[1]], args[perm[2]]
        total = total + sign * model.associator(a, b, c)
    return total


def gji_manually_unrolled(model: SpectralModelV18, x: torch.Tensor, y: torch.Tensor, z: torch.Tensor) -> torch.Tensor:
    """Second, independent-by-construction implementation matching the
    legacy script's explicit 6-term expression (line 1178), for
    cross-validation against the itertools-based version above."""
    a_xyz = model.associator(x, y, z)
    a_yxz = model.associator(y, x, z)
    a_yzx = model.associator(y, z, x)
    a_zyx = model.associator(z, y, x)
    a_zxy = model.associator(z, x, y)
    a_xzy = model.associator(x, z, y)
    return a_xyz - a_yxz + a_yzx - a_zyx + a_zxy - a_xzy


@dataclass
class CyclicNReport:
    raw_defect_mean: float
    symmetrized_defect_mean: float
    symmetrized_defect_is_roundoff_floor: bool
    gji_cross_check_max_rel_diff: float
    gji_ratio_mean: float
    gji_ratio_adversarial_max: float
    mutation_test_detects_wrong_sign: bool


def cyclic_and_gji_report(seed: int = 0, *, n: int = 16, rank: int = 4, arity: int = 3, cp_rank: int = 4, trials: int = 200, adversarial_steps: int = 100) -> CyclicNReport:
    gen = torch.Generator().manual_seed(seed)
    model = SpectralModelV18(n=n, rank=rank, arity=arity, cp_rank=cp_rank, device="cpu", dtype="float64", generator=gen)

    def rand_unit():
        v = torch.complex(torch.randn(n, generator=gen, dtype=torch.float64), torch.randn(n, generator=gen, dtype=torch.float64))
        return v / (torch.linalg.norm(v) + 1e-30)

    raw_defects = []
    sym_defects = []
    gji_diffs = []
    gji_ratios = []
    for _ in range(trials):
        xs = [rand_unit() for _ in range(arity)]
        y0_raw = model.product.cp_raw(xs)
        y0_sym = model.product(*xs)
        raw_acc = 0.0
        sym_acc = 0.0
        ref_raw = (torch.linalg.norm(y0_raw) ** 2).item() + 1e-12
        ref_sym = (torch.linalg.norm(y0_sym) ** 2).item() + 1e-12
        xlist = xs
        for shift in range(1, arity):
            rotated = xlist[shift:] + xlist[:shift]
            raw_acc += (torch.linalg.norm(model.product.cp_raw(rotated) - y0_raw) ** 2).item() / ref_raw
            sym_acc += (torch.linalg.norm(model.product(*rotated) - y0_sym) ** 2).item() / ref_sym
        raw_defects.append(raw_acc / (arity - 1))
        sym_defects.append(sym_acc / (arity - 1))

        x, y, z = rand_unit(), rand_unit(), rand_unit()
        g1 = gji_independent_implementation(model, x, y, z)
        g2 = gji_manually_unrolled(model, x, y, z)
        diff = (torch.linalg.norm(g1 - g2) / (torch.linalg.norm(g1) + 1e-30)).item()
        gji_diffs.append(diff)
        ref = sum(torch.linalg.norm(model.associator(a, b, c)).item() ** 2 for a, b, c in itertools.permutations((x, y, z)))
        ratio = (torch.linalg.norm(g1).item() ** 2) / (ref + 1e-12)
        gji_ratios.append(ratio)

    # mutation test: flip one sign in the manually-unrolled formula and
    # confirm it now disagrees with the correct independent implementation
    x, y, z = rand_unit(), rand_unit(), rand_unit()
    correct = gji_independent_implementation(model, x, y, z)
    a_xyz = model.associator(x, y, z)
    a_yxz = model.associator(y, x, z)
    a_yzx = model.associator(y, z, x)
    a_zyx = model.associator(z, y, x)
    a_zxy = model.associator(z, x, y)
    a_xzy = model.associator(x, z, y)
    mutated = a_xyz + a_yxz + a_yzx - a_zyx + a_zxy - a_xzy  # sign of a_yxz flipped (bug injected)
    mutation_diff = (torch.linalg.norm(mutated - correct) / (torch.linalg.norm(correct) + 1e-30)).item()
    mutation_detects = mutation_diff > 1e-6

    # adversarial search maximizing the GJI ratio
    xr = torch.randn(n, generator=gen, dtype=torch.float64, requires_grad=True)
    xi = torch.randn(n, generator=gen, dtype=torch.float64, requires_grad=True)
    yr = torch.randn(n, generator=gen, dtype=torch.float64, requires_grad=True)
    yi = torch.randn(n, generator=gen, dtype=torch.float64, requires_grad=True)
    zr = torch.randn(n, generator=gen, dtype=torch.float64, requires_grad=True)
    zi = torch.randn(n, generator=gen, dtype=torch.float64, requires_grad=True)
    opt = torch.optim.Adam([xr, xi, yr, yi, zr, zi], lr=0.05)
    best_ratio = max(gji_ratios)
    for _ in range(adversarial_steps):
        opt.zero_grad()

        def u(re, im):
            v = torch.complex(re, im)
            return v / (torch.linalg.norm(v) + 1e-30)

        xa, ya, za = u(xr, xi), u(yr, yi), u(zr, zi)
        g = gji_independent_implementation(model, xa, ya, za)
        ref = sum(torch.linalg.norm(model.associator(a, b, c)) ** 2 for a, b, c in itertools.permutations((xa, ya, za)))
        ratio = (torch.linalg.norm(g) ** 2) / (ref + 1e-12)
        loss = -ratio
        loss.backward()
        opt.step()
        best_ratio = max(best_ratio, ratio.item())

    return CyclicNReport(
        raw_defect_mean=sum(raw_defects) / len(raw_defects),
        symmetrized_defect_mean=sum(sym_defects) / len(sym_defects),
        symmetrized_defect_is_roundoff_floor=(sum(sym_defects) / len(sym_defects)) < 1e-20,
        gji_cross_check_max_rel_diff=max(gji_diffs),
        gji_ratio_mean=sum(gji_ratios) / len(gji_ratios),
        gji_ratio_adversarial_max=best_ratio,
        mutation_test_detects_wrong_sign=mutation_detects,
    )
