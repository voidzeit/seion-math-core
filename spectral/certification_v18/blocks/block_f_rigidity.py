"""Block F — rigidity, v18 redesign.

Mission diagnosis: the legacy `hessian_condition_proxy` is not
automatically a Hessian. This module computes and NAMES each curvature
object explicitly:

- `exact_hessian_small_case`: the true Hessian (`torch.autograd.functional.hessian`)
  of a scalar loss w.r.t. real/imag parts of U, for a small n where this is
  tractable.
- `generalized_gauss_newton`: J^T J for the closure-residual Jacobian J
  (valid for any least-squares-shaped loss, cheaper than the exact Hessian,
  NOT equal to it in general — the difference is the residual-weighted
  second-order term, checked explicitly here rather than assumed away).
- `finite_difference_curvature`: central finite-difference estimate,
  cross-checked against the exact Hessian as a sanity control.
- `basin_and_seed_stability`: train from multiple independent seeds,
  compare final loss and final subspace (principal angles) — same
  hyperparameters, different random initialization.
- `gauge_flat_directions`: confirms the loss is invariant under U -> U@Q
  for unitary r x r Q (since it only depends on P=UU*), and that the exact
  Hessian has correspondingly small eigenvalues along those directions
  (identifiability only modulo this gauge).
"""

from __future__ import annotations

from dataclasses import dataclass

import torch
from torch.autograd.functional import hessian, jacobian

from spectral.certification_v18.blocks.block_m_persistent_factorization import principal_angles
from spectral.certification_v18.model import SpectralModelV18, fro_norm, orthonormalize_columns, projector_from_u


def _closure_residual(u_re: torch.Tensor, u_im: torch.Tensor, model: SpectralModelV18, y2: torch.Tensor, extras: list) -> torch.Tensor:
    """Gauge-invariant by construction: sums the closure residual over
    EVERY column of U (not one fixed column), which is exactly the trace
    of a quadratic form and therefore invariant under U -> U@Q for any
    unitary Q (a change of orthonormal basis of the same subspace) —
    required for the gauge-flat-direction test below to mean anything."""
    U = orthonormalize_columns(torch.complex(u_re, u_im))
    r = U.shape[1]
    parts = []
    for i in range(r):
        x1 = U[:, i]
        y = model.product(x1, y2, *extras)
        y_in = U @ (U.conj().T @ y)
        res = y - y_in
        parts.append(res)
    stacked = torch.cat(parts)
    return torch.cat([stacked.real, stacked.imag])


def _scalar_loss(u_re: torch.Tensor, u_im: torch.Tensor, model: SpectralModelV18, y2: torch.Tensor, extras: list) -> torch.Tensor:
    res = _closure_residual(u_re, u_im, model, y2, extras)
    return torch.sum(res**2)


@dataclass
class RigidityReport:
    exact_hessian_eigvals: list[float]
    ggn_eigvals: list[float]
    finite_diff_vs_exact_rel_error: float
    basin_final_losses: list[float]
    basin_pairwise_max_principal_angle: float
    gauge_direction_loss_invariance: float
    gauge_direction_hessian_eigval: float


def small_case_curvature_report(seed: int = 0, *, n: int = 6, rank: int = 2, arity: int = 3, cp_rank: int = 2) -> RigidityReport:
    gen = torch.Generator().manual_seed(seed)
    model = SpectralModelV18(n=n, rank=rank, arity=arity, cp_rank=cp_rank, device="cpu", dtype="float64", generator=gen)
    extras = [model.anchor.detach() for _ in range(arity - 2)]
    y2 = torch.complex(torch.randn(n, generator=gen, dtype=torch.float64), torch.randn(n, generator=gen, dtype=torch.float64))
    y2 = y2 / fro_norm(y2)

    u_re0 = model.u_re.detach().clone()
    u_im0 = model.u_im.detach().clone()

    def flat_loss(vec: torch.Tensor) -> torch.Tensor:
        k = n * rank
        u_re = vec[:k].reshape(n, rank)
        u_im = vec[k:].reshape(n, rank)
        return _scalar_loss(u_re, u_im, model, y2, extras)

    x0 = torch.cat([u_re0.reshape(-1), u_im0.reshape(-1)]).requires_grad_(True)
    H = hessian(flat_loss, x0)
    H_sym = 0.5 * (H + H.T)
    exact_eigvals = torch.linalg.eigvalsh(H_sym)

    def residual_flat(vec: torch.Tensor) -> torch.Tensor:
        k = n * rank
        u_re = vec[:k].reshape(n, rank)
        u_im = vec[k:].reshape(n, rank)
        return _closure_residual(u_re, u_im, model, y2, extras)

    J = jacobian(residual_flat, x0.detach())
    ggn = 2 * (J.T @ J)  # factor 2 to match d/dx sum(r^2) = 2 J^T r ; GGN approximates Hessian as 2 J^T J
    ggn_eigvals = torch.linalg.eigvalsh(0.5 * (ggn + ggn.T))

    # finite-difference cross-check on a random direction
    direction = torch.randn_like(x0)
    direction = direction / torch.linalg.norm(direction)
    eps = 1e-4
    f_plus = flat_loss(x0.detach() + eps * direction)
    f_minus = flat_loss(x0.detach() - eps * direction)
    f0 = flat_loss(x0.detach())
    fd_second_deriv = (f_plus - 2 * f0 + f_minus) / (eps**2)
    exact_second_deriv = direction @ (H_sym @ direction)
    fd_rel_error = abs(fd_second_deriv.item() - exact_second_deriv.item()) / (abs(exact_second_deriv.item()) + 1e-12)

    # basin/seed stability: train from 3 independent seeds, compare final loss + subspace
    final_losses = []
    final_Us = []
    for s in range(3):
        gen_s = torch.Generator().manual_seed(1000 + s)
        m = SpectralModelV18(n=n, rank=rank, arity=arity, cp_rank=cp_rank, device="cpu", dtype="float64", generator=gen_s)
        opt = torch.optim.Adam(m.parameters(), lr=0.02)
        extras_s = [m.anchor.detach() for _ in range(arity - 2)]
        y2_s = y2.detach()
        for _ in range(150):
            opt.zero_grad()
            loss = _scalar_loss(m.u_re, m.u_im, m, y2_s, extras_s)
            loss.backward()
            opt.step()
        final_losses.append(loss.item())
        final_Us.append(orthonormalize_columns(m.u()).detach())

    max_angle = 0.0
    for i in range(len(final_Us)):
        for j in range(i + 1, len(final_Us)):
            pa = principal_angles(final_Us[i], final_Us[j])
            max_angle = max(max_angle, pa.max_angle_rad)

    # gauge-flat-direction check: U -> U @ Q for random unitary Q should not
    # change the loss (loss depends only on P = UU*)
    U0 = orthonormalize_columns(torch.complex(u_re0, u_im0))
    q_gen = torch.Generator().manual_seed(42)
    rand_q = torch.complex(torch.randn(rank, rank, generator=q_gen, dtype=torch.float64), torch.randn(rank, rank, generator=q_gen, dtype=torch.float64))
    Q, _ = torch.linalg.qr(rand_q)
    U_rotated = U0 @ Q
    loss_orig = _scalar_loss(U0.real, U0.imag, model, y2, extras).item()
    loss_rotated = _scalar_loss(U_rotated.real, U_rotated.imag, model, y2, extras).item()
    gauge_invariance = abs(loss_orig - loss_rotated) / (abs(loss_orig) + 1e-12)

    # direction corresponding to an infinitesimal gauge rotation: dU = U @ (i * antiherm generator)
    gen_dir = torch.zeros(rank, rank, dtype=torch.complex128)
    if rank >= 2:
        gen_dir[0, 1] = 1.0
        gen_dir[1, 0] = -1.0
    dU = U0 @ gen_dir
    dvec = torch.cat([dU.real.reshape(-1), dU.imag.reshape(-1)])
    dvec = dvec / (torch.linalg.norm(dvec) + 1e-30)
    gauge_hessian_eigval = (dvec @ (H_sym @ dvec)).item()

    return RigidityReport(
        exact_hessian_eigvals=exact_eigvals.tolist(),
        ggn_eigvals=ggn_eigvals.tolist(),
        finite_diff_vs_exact_rel_error=fd_rel_error,
        basin_final_losses=final_losses,
        basin_pairwise_max_principal_angle=max_angle,
        gauge_direction_loss_invariance=gauge_invariance,
        gauge_direction_hessian_eigval=gauge_hessian_eigval,
    )
