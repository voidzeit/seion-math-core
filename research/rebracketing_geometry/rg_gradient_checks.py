"""Does the backward pass differentiate the same function the forward evaluates?

The search evaluates an ADMISSIBLE law, obtained by dividing a raw tensor by a
scale factor built from its own operator norm and closure defect. If that factor
is computed under `no_grad` and then treated as a constant, autograd sees

    Ftilde_{mu0}(mu) = J( mu / s(mu0) )      instead of      F(mu) = J( mu / s(mu) )

The two disagree in exactly the direction that matters. In the same-law class
the objective is homogeneous of degree 2 before normalization, J(c mu) = c^2
J(mu), so Euler gives <grad J(mu), mu> = 2 J(mu) > 0: the frozen-denominator
surrogate reports a strongly ascending RADIAL direction. But the true normalized
objective is scale invariant, F(c mu) = F(mu), because s is homogeneous of
degree 1 too, and therefore

    DF(mu)[mu] = 0   exactly.

So a correct pipeline must return a radial derivative of zero, and a frozen one
returns something large and positive. That is the sharpest possible test of the
bug, it costs one extra contraction, and it is what this file checks.

Three checks, in increasing generality:

  RADIAL   DF(mu)[mu] must vanish -- scale invariance, exact, no tolerance
           games. Catches the frozen-denominator bug directly.
  FINITE   central finite differences against autograd along random directions
           at a point where NO constraint is exactly active, so the objective is
           smooth there and the comparison is meaningful.
  ENVELOPE the operator norm itself must carry a gradient: contracting the
           maximizer against a detached tensor returns grad = 0, which is the
           regression that hid inside the restart-batched kernel.

The checks deliberately avoid the exact witness: there `||mu||_op = 1` and
`closure = eta` are BOTH active, the scale factor is a max of two branches that
tie, and a tie has a subdifferential rather than a gradient. Testing only at the
witness would let a broken backward hide behind that non-smoothness.
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import torch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from rg_fused_search import (  # noqa: E402
    evaluate, feasibility_factors, score, share_laws,
)
from rg_kernels import DTYPE, coordinate_projectors, op_norms  # noqa: E402


def build_case(dim, rank, eta, batch, device, seed, scale=0.6):
    """A generic admissible-ish point, deliberately NOT on the constraint tie.

    `scale` shrinks the raw law so neither the operator norm nor the closure
    budget is exactly active, which is what makes the point smooth.
    """
    generator = torch.Generator(device=device).manual_seed(seed)
    law = (scale * torch.randn(batch, dim, dim, dim, dim, dtype=DTYPE,
                               device=device, generator=generator)
           ).requires_grad_(True)
    leaves = torch.randn(batch, 5, dim, dtype=DTYPE, device=device,
                         generator=generator).requires_grad_(True)
    ranks = torch.full((batch,), rank, dtype=torch.long, device=device)
    projector = coordinate_projectors(ranks, dim, device)
    return {"law": law, "leaves": leaves,
            "projectors": (projector, projector, projector),
            "eta": torch.full((batch,), eta, dtype=DTYPE, device=device),
            "shared": torch.ones(batch, dtype=torch.bool, device=device),
            "coefficients": torch.tensor([[1.0, 0.0, 0.0]], dtype=DTYPE,
                                         device=device).expand(batch, 3)}


def objective(case, law, strength, differentiable):
    raws = dict.fromkeys(("inner_L", "inner_M", "root_L", "root_M"), law)
    laws = share_laws(raws, case["shared"])
    factors = feasibility_factors(laws, case["projectors"], *strength,
                                  differentiable=differentiable)
    A_hat, PA, D, _ = evaluate(laws, case["projectors"], case["leaves"],
                               case["eta"], factors, case["shared"])
    return score(case["coefficients"], A_hat, PA, D, case["eta"])


def radial_check(case, strength, differentiable):
    """DF(mu)[mu] must be 0: the normalized objective is scale invariant."""
    law = case["law"]
    if law.grad is not None:
        law.grad = None
    values = objective(case, law, strength, differentiable)
    values.sum().backward()
    radial = (law.grad * law.detach()).flatten(1).sum(dim=1)
    return radial.abs().max().item(), values.detach().abs().mean().item()


def scale_invariance_check(case, strength, differentiable, factor=3.7):
    """F(c mu) must equal F(mu) in the FORWARD pass, for any c > 0."""
    with torch.no_grad():
        base = objective(case, case["law"], strength, differentiable)
        scaled = objective(case, factor * case["law"], strength,
                           differentiable)
    return (scaled - base).abs().max().item()


def finite_difference_check(case, strength, differentiable, epsilon, seed):
    """Central differences against autograd along a random direction."""
    law = case["law"]
    if law.grad is not None:
        law.grad = None
    values = objective(case, law, strength, differentiable)
    values.sum().backward()
    analytic_grad = law.grad.clone()

    generator = torch.Generator(device=law.device).manual_seed(seed)
    direction = torch.randn(law.shape, dtype=DTYPE, device=law.device,
                            generator=generator)
    direction /= direction.flatten(1).norm(dim=1).view(-1, 1, 1, 1, 1)

    with torch.no_grad():
        plus = objective(case, law + epsilon * direction, strength,
                         differentiable)
        minus = objective(case, law - epsilon * direction, strength,
                          differentiable)
    numeric = (plus - minus) / (2 * epsilon)
    analytic = (analytic_grad * direction).flatten(1).sum(dim=1)
    denominator = numeric.abs().clamp_min(1e-9)
    return ((numeric - analytic).abs() / denominator).max().item()


def envelope_check(dim, batch, device, seed):
    """The operator norm must carry a gradient at all."""
    generator = torch.Generator(device=device).manual_seed(seed)
    tensor = torch.randn(batch, dim, dim, dim, dim, dtype=DTYPE, device=device,
                         generator=generator).requires_grad_(True)
    norms = op_norms(tensor, restarts=16, iters=40, seed=3)
    norms.sum().backward()
    grad_norm = tensor.grad.flatten(1).norm(dim=1)
    # by homogeneity of degree 1, <grad N(mu), mu> = N(mu)
    euler = (tensor.grad * tensor.detach()).flatten(1).sum(dim=1)
    return (grad_norm.min().item(),
            (euler - norms.detach()).abs().max().item())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dim", type=int, default=3)
    parser.add_argument("--rank", type=int, default=2)
    parser.add_argument("--etas", type=float, nargs="+", default=[0.3, 1.0])
    parser.add_argument("--batch", type=int, default=32)
    parser.add_argument("--strength", type=int, nargs=2, default=[32, 40])
    parser.add_argument("--epsilon", type=float, default=1e-6)
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"device={device}  D={args.dim} rank={args.rank} "
          f"batch={args.batch}\n")

    smallest, euler_gap = envelope_check(args.dim, args.batch, device, 5)
    print("ENVELOPE  operator norm must be differentiable")
    print(f"  smallest ||grad N||            {smallest:.3e}"
          f"   {'FAIL (detached)' if smallest < 1e-12 else 'ok'}")
    print(f"  |<grad N, mu> - N|  (Euler)    {euler_gap:.3e}"
          f"   {'ok' if euler_gap < 1e-9 else 'FAIL'}\n")

    print(f"{'eta':>6} {'mode':>16} {'radial |DF[mu]|':>17} "
          f"{'|F(c.mu)-F(mu)|':>17} {'max FD rel err':>15}")
    failures = 0
    for eta in args.etas:
        for differentiable in (False, True):
            case = build_case(args.dim, args.rank, eta, args.batch, device,
                              seed=int(100 * eta) + 11)
            radial, magnitude = radial_check(case, tuple(args.strength),
                                             differentiable)
            invariance = scale_invariance_check(case, tuple(args.strength),
                                                differentiable)
            relative = finite_difference_check(case, tuple(args.strength),
                                               differentiable, args.epsilon,
                                               seed=17)
            mode = "DIFFERENTIABLE" if differentiable else "frozen"
            flag = ""
            if differentiable:
                bad = radial > 1e-6 * max(magnitude, 1.0) or relative > 1e-4
                failures += bool(bad)
                flag = "  <-- FAIL" if bad else "  <-- ok"
            print(f"{eta:6.2f} {mode:>16} {radial:17.3e} {invariance:17.3e} "
                  f"{relative:15.3e}{flag}")

    print()
    print("The FORWARD is scale invariant in both modes -- both columns two.")
    print("The BACKWARD is only scale invariant when the normalization is")
    print("differentiated: a large radial derivative in `frozen` mode IS the")
    print("bug, and it is exactly the direction the normalization cancels.")
    raise SystemExit(1 if failures else 0)


if __name__ == "__main__":
    main()
