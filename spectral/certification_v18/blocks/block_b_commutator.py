"""Block B — dynamic commutator explanation, v18 redesign.

Mathematical setup (see model.py for the reimplementation and citations):
`P = U U*` is the learned rank-r projector, `K = I - P`, `Delta` a fixed
random Hermitian operator, and the raw target is the exact algebraic
identity

    raw_comm := [Delta, P] == K @ Delta @ P - P @ Delta @ K   (rank <= 2r)

The legacy hypothesis is that a specific closed-form "coherent dynamic
curvature"

    C_theta(U, K, Phi) := U @ Phi @ U* @ Delta @ K - K @ Delta @ U @ Phi* @ U*

(also rank <= 2r; Phi := reduced_curvature_matrix(U), derived from the CP
law's associator) explains most of raw_comm, leaving a small residual.
Every historical run scored this WARN (see
spectral/legacy/v17/legacy_claim_reclassification.yaml): comm_unexplained_rel
~3-4e-2, normal_unexplained_rel ~2-3e-1, coherence_ratio slightly negative.

This module asks the mission's actual question: is that near-miss real
signal, or does C_theta fail to beat trivial baselines built from the same
rank budget? Five conditions, all evaluated on the SAME held-out instances:

1. zero              — C = 0. Sanity floor; unexplained_rel must be 1.0.
2. c_theta_as_given   — C = C_theta (c=1, no fitting). What the legacy code reports.
3. best_scalar        — C = c* * C_theta, c* fit by complex projection.
                        Tests whether c=1 is a normalization bug.
4. best_rank_2r       — best rank-2r SVD truncation of raw_comm ITSELF.
                        Capacity ceiling: raw_comm already has rank <= 2r,
                        so this is a near-exact reconstruction and shows
                        what "using the same rank budget optimally" can
                        achieve — the bar C_theta is actually competing
                        against, not a strawman.
5. randomized_phi     — C_theta computed with Phi replaced by a random r x r
                        matrix of matching Frobenius norm (same U, Delta, K,
                        same functional form). Adversarial control: isolates
                        whether Phi's specific geometric content (from the
                        real associator) matters, or whether any matrix of
                        the same shape/scale plugged into the same formula
                        would explain raw_comm just as well.
6. best_linear        — least-squares weights over
                        {C_theta_as_given, 3 independent randomized_phi
                        draws}, FIT ON TRAINING INSTANCES ONLY, then applied
                        (fixed) to held-out instances. Tests whether the
                        real-Phi term earns a consistently larger weight
                        than the random-Phi terms out of sample.

A run only supports "the coherent-curvature hypothesis has real
explanatory content" if condition 2/3 beats condition 5 by a wide,
held-out-stable margin, AND condition 6's fitted weight on the real term is
consistently larger than on the random terms across held-out instances.
Beating condition 1 (zero) alone is not sufficient — that only shows
raw_comm is nonzero.
"""

from __future__ import annotations

from dataclasses import dataclass

import torch

from spectral.certification_v18.model import (
    SpectralModelV18,
    commutator,
    fro_norm,
    identity,
    orthonormalize_columns,
    projector_from_u,
)


@dataclass
class BInstance:
    seed: int
    raw_comm: torch.Tensor
    c_theta: torch.Tensor
    rank2r_best: torch.Tensor
    randomized_phi_draws: list[torch.Tensor]


def build_instance(seed: int, *, n: int = 24, rank: int = 6, arity: int = 3, cp_rank: int = 6, dtype: str = "float64", n_random_phi_draws: int = 3) -> BInstance:
    gen = torch.Generator().manual_seed(seed)
    model = SpectralModelV18(n=n, rank=rank, arity=arity, cp_rank=cp_rank, device="cpu", dtype=dtype, generator=gen)
    U = orthonormalize_columns(model.u())
    P = projector_from_u(U)
    K = identity(n, device=model.device, dtype=model.cdtype) - P
    Phi = model.reduced_curvature_matrix(U)

    raw_comm = commutator(model.delta, P)
    c_theta = model.coherent_dynamic_curvature(U, K, Phi)

    u_svd, s_svd, vh_svd = torch.linalg.svd(raw_comm)
    two_r = min(2 * rank, s_svd.numel())
    rank2r_best = (u_svd[:, :two_r] * s_svd[:two_r]) @ vh_svd[:two_r, :]

    phi_scale = torch.linalg.norm(Phi)
    randomized_draws = []
    for k in range(n_random_phi_draws):
        rgen = torch.Generator().manual_seed(seed * 1000 + k + 1)
        re = torch.randn(rank, rank, generator=rgen, dtype=model.rdtype)
        im = torch.randn(rank, rank, generator=rgen, dtype=model.rdtype)
        rand_phi = torch.complex(re, im)
        rand_phi = rand_phi * (phi_scale / (torch.linalg.norm(rand_phi) + 1e-30))
        randomized_draws.append(model.coherent_dynamic_curvature(U, K, rand_phi))

    return BInstance(seed=seed, raw_comm=raw_comm, c_theta=c_theta, rank2r_best=rank2r_best, randomized_phi_draws=randomized_draws)


def unexplained_rel(target: torch.Tensor, candidate: torch.Tensor) -> float:
    return (fro_norm(target - candidate) / (fro_norm(target) + 1e-30)).item()


def complex_inner(a: torch.Tensor, b: torch.Tensor) -> complex:
    return torch.sum(torch.conj(a) * b).item()


def best_scalar_fit(target: torch.Tensor, candidate: torch.Tensor) -> complex:
    denom = complex_inner(candidate, candidate)
    if abs(denom) < 1e-30:
        return 0j
    return complex_inner(candidate, target) / denom


def fit_linear_weights(instances: list[BInstance]) -> torch.Tensor:
    """Least-squares weights for {c_theta, randomized_phi_draws...} pooled
    across all given (training) instances, shared across instances."""
    n_features = 1 + len(instances[0].randomized_phi_draws)
    rows = []
    targets = []
    for inst in instances:
        features = [inst.c_theta] + inst.randomized_phi_draws
        feat_mat = torch.stack([f.reshape(-1) for f in features], dim=1)  # (n^2, n_features)
        rows.append(feat_mat)
        targets.append(inst.raw_comm.reshape(-1))
    A = torch.cat(rows, dim=0)
    b = torch.cat(targets, dim=0)
    solution = torch.linalg.lstsq(A, b.unsqueeze(1)).solution.squeeze(1)
    assert solution.numel() == n_features
    return solution


def evaluate_best_linear(instance: BInstance, weights: torch.Tensor) -> float:
    features = [instance.c_theta] + instance.randomized_phi_draws
    combined = sum(w * f for w, f in zip(weights.tolist(), features))
    return unexplained_rel(instance.raw_comm, combined)


def solve_optimal_phi(U: torch.Tensor, K: torch.Tensor, delta: torch.Tensor, target: torch.Tensor, rank: int) -> torch.Tensor:
    """Closed-form best-possible Phi for the SAME C_theta formula and the
    SAME (U, K, delta), dropping the constraint that Phi must equal the
    associator-derived reduced_curvature_matrix(U).

    C_theta(Phi) = U @ Phi @ A - B @ Phi^H @ U^H, with A = U^H @ delta @ K
    (r x n) and B = K @ delta @ U (n x r), is R-linear in Phi (not
    complex-linear, because of the Phi^H term) — so the optimal Phi in the
    least-squares sense is found by building the real-linear operator's
    matrix explicitly (2*rank^2 real unknowns) and solving one lstsq.

    This is the true capacity ceiling for block B's functional form: if the
    real associator-derived Phi does not come close to this ceiling, the
    formula's specific geometric constraint is costing real fit quality
    (mission's "insufficient expressive capacity" diagnosis); if it does,
    any remaining gap is attributable to the shape of the formula itself,
    not to which Phi was plugged in.
    """
    n = U.shape[0]
    A = U.conj().T @ delta @ K
    B = K @ delta @ U

    def c_theta_of(phi: torch.Tensor) -> torch.Tensor:
        return U @ phi @ A - B @ phi.conj().T @ U.conj().T

    basis_cols = []
    for k in range(rank):
        for l in range(rank):
            e = torch.zeros(rank, rank, dtype=U.dtype)
            e[k, l] = 1.0
            basis_cols.append(c_theta_of(e).reshape(-1))
            basis_cols.append(c_theta_of(1j * e).reshape(-1))
    # Stack as a REAL linear system: real and imaginary parts of the output
    # are independent real equations.
    M_complex = torch.stack(basis_cols, dim=1)  # (n*n, 2*rank^2), complex dtype but used as real map
    M_real = torch.cat([M_complex.real, M_complex.imag], dim=0)
    t_real = torch.cat([target.reshape(-1).real, target.reshape(-1).imag], dim=0)
    coeffs = torch.linalg.lstsq(M_real, t_real.unsqueeze(1)).solution.squeeze(1)

    phi_opt = torch.zeros(rank, rank, dtype=U.dtype)
    idx = 0
    for k in range(rank):
        for l in range(rank):
            phi_opt[k, l] = coeffs[idx] + 1j * coeffs[idx + 1]
            idx += 2
    return phi_opt


def train_u_to_minimize_comm(seed: int, *, steps: int = 300, lr: float = 5e-3, n: int = 24, rank: int = 6, arity: int = 3, cp_rank: int = 6, dtype: str = "float64") -> dict:
    """Light gradient-descent training of U (and the CP-law parameters that
    determine Phi via the associator) to minimize comm_unexplained_rel with
    the REAL associator-derived Phi — matching the objective the historical
    v17 runs actually trained against (lambda_cdc in configure_run_mode).
    Returns the trained model state needed for the capacity comparison.
    """
    gen = torch.Generator().manual_seed(seed)
    model = SpectralModelV18(n=n, rank=rank, arity=arity, cp_rank=cp_rank, device="cpu", dtype=dtype, generator=gen)
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    history = []
    for step in range(steps):
        opt.zero_grad()
        U = orthonormalize_columns(model.u())
        P = projector_from_u(U)
        K = identity(n, device=model.device, dtype=model.cdtype) - P
        Phi = model.reduced_curvature_matrix(U)
        raw_comm = commutator(model.delta, P)
        c_theta = model.coherent_dynamic_curvature(U, K, Phi)
        loss = (fro_norm(raw_comm - c_theta) / (fro_norm(raw_comm) + 1e-30)) ** 2
        loss.backward()
        opt.step()
        if step % max(steps // 10, 1) == 0 or step == steps - 1:
            history.append({"step": step, "comm_unexplained_rel": (loss.detach() ** 0.5).item()})

    with torch.no_grad():
        U = orthonormalize_columns(model.u())
        P = projector_from_u(U)
        K = identity(n, device=model.device, dtype=model.cdtype) - P
        Phi = model.reduced_curvature_matrix(U)
        raw_comm = commutator(model.delta, P)
        c_theta = model.coherent_dynamic_curvature(U, K, Phi)
    return {
        "seed": seed,
        "U": U,
        "K": K,
        "delta": model.delta,
        "raw_comm": raw_comm,
        "c_theta_trained": c_theta,
        "final_unexplained_rel_real_phi": unexplained_rel(raw_comm, c_theta),
        "training_history": history,
    }


def run_block_b_capacity_test(*, seeds: list[int], steps: int = 300, lr: float = 5e-3, n: int = 24, rank: int = 6, arity: int = 3, cp_rank: int = 6, dtype: str = "float64") -> dict:
    """The decisive test: for each seed, train U to minimize
    comm_unexplained_rel using the real associator-derived Phi, then solve
    (in closed form, no further training) for the best possible Phi for
    that SAME trained U. Compare the two unexplained_rel values."""
    rows = []
    for seed in seeds:
        trained = train_u_to_minimize_comm(seed, steps=steps, lr=lr, n=n, rank=rank, arity=arity, cp_rank=cp_rank, dtype=dtype)
        phi_opt = solve_optimal_phi(trained["U"], trained["K"], trained["delta"], trained["raw_comm"], rank=rank)
        c_theta_opt = trained["U"] @ phi_opt @ (trained["U"].conj().T @ trained["delta"] @ trained["K"]) - (
            trained["K"] @ trained["delta"] @ trained["U"]
        ) @ phi_opt.conj().T @ trained["U"].conj().T
        opt_rel = unexplained_rel(trained["raw_comm"], c_theta_opt)
        real_rel = trained["final_unexplained_rel_real_phi"]
        gap = real_rel - opt_rel
        rows.append(
            {
                "seed": seed,
                "trained_real_phi_unexplained_rel": real_rel,
                "optimal_free_phi_unexplained_rel": opt_rel,
                "capacity_gap": gap,
                "training_history": trained["training_history"],
            }
        )

    mean_real = sum(r["trained_real_phi_unexplained_rel"] for r in rows) / len(rows)
    mean_opt = sum(r["optimal_free_phi_unexplained_rel"] for r in rows) / len(rows)
    mean_gap = mean_real - mean_opt
    # A large gap means the associator constraint costs real fit quality
    # relative to the same formula's best-possible Phi (insufficient
    # expressive capacity / geometric misalignment). A near-zero gap means
    # the real Phi already realizes the formula's own ceiling.
    verdict = "REAL_PHI_NEAR_OPTIMAL_FOR_THIS_FORMULA" if mean_gap < 0.1 * max(mean_opt, 1e-6) + 1e-3 else "REAL_PHI_FAR_FROM_FORMULA_CEILING_CAPACITY_GAP"

    return {
        "config": {"n": n, "rank": rank, "arity": arity, "cp_rank": cp_rank, "dtype": dtype, "steps": steps, "lr": lr},
        "seeds": seeds,
        "rows": rows,
        "mean_trained_real_phi_unexplained_rel": mean_real,
        "mean_optimal_free_phi_unexplained_rel": mean_opt,
        "mean_capacity_gap": mean_gap,
        "verdict": verdict,
    }


def run_block_b_ablation(*, train_seeds: list[int], held_out_seeds: list[int], n: int = 24, rank: int = 6, arity: int = 3, cp_rank: int = 6, dtype: str = "float64") -> dict:
    if set(train_seeds) & set(held_out_seeds):
        raise ValueError("train_seeds and held_out_seeds must be disjoint")

    train_instances = [build_instance(s, n=n, rank=rank, arity=arity, cp_rank=cp_rank, dtype=dtype) for s in train_seeds]
    held_out_instances = [build_instance(s, n=n, rank=rank, arity=arity, cp_rank=cp_rank, dtype=dtype) for s in held_out_seeds]

    linear_weights = fit_linear_weights(train_instances)

    def per_instance_report(inst: BInstance) -> dict:
        zero = 1.0
        as_given = unexplained_rel(inst.raw_comm, inst.c_theta)
        c_star = best_scalar_fit(inst.raw_comm, inst.c_theta)
        best_scalar = unexplained_rel(inst.raw_comm, c_star * inst.c_theta)
        rank2r = unexplained_rel(inst.raw_comm, inst.rank2r_best)
        randomized = [unexplained_rel(inst.raw_comm, rp) for rp in inst.randomized_phi_draws]
        best_linear = evaluate_best_linear(inst, linear_weights)
        return {
            "seed": inst.seed,
            "zero": zero,
            "c_theta_as_given": as_given,
            "best_scalar": best_scalar,
            "best_scalar_c": {"real": c_star.real, "imag": c_star.imag} if isinstance(c_star, complex) else float(c_star),
            "best_rank_2r": rank2r,
            "randomized_phi_mean": sum(randomized) / len(randomized),
            "randomized_phi_min": min(randomized),
            "best_linear": best_linear,
        }

    train_report = [per_instance_report(inst) for inst in train_instances]
    held_out_report = [per_instance_report(inst) for inst in held_out_instances]

    def mean_field(rows: list[dict], key: str) -> float:
        return sum(r[key] for r in rows) / len(rows)

    held_out_c_theta = mean_field(held_out_report, "c_theta_as_given")
    held_out_random_mean = mean_field(held_out_report, "randomized_phi_mean")
    beats_randomized_control = held_out_c_theta < held_out_random_mean

    real_weight = float(linear_weights[0].abs().item())
    random_weights_mean = float(torch.stack([w.abs() for w in linear_weights[1:]]).mean().item())
    real_term_dominates = real_weight > random_weights_mean

    verdict = "SURVIVES_HELD_OUT_ADVERSARIAL_TEST" if (beats_randomized_control and real_term_dominates) else "REFUTED_BY_RANDOMIZED_CONTROL"

    return {
        "config": {"n": n, "rank": rank, "arity": arity, "cp_rank": cp_rank, "dtype": dtype},
        "train_seeds": train_seeds,
        "held_out_seeds": held_out_seeds,
        "train_report": train_report,
        "held_out_report": held_out_report,
        "held_out_mean_c_theta_as_given": held_out_c_theta,
        "held_out_mean_randomized_phi_control": held_out_random_mean,
        "held_out_mean_best_rank_2r": mean_field(held_out_report, "best_rank_2r"),
        "held_out_mean_best_scalar": mean_field(held_out_report, "best_scalar"),
        "fitted_linear_weights": {"real_phi": real_weight, "random_phi_mean_abs": random_weights_mean},
        "beats_randomized_control_held_out": beats_randomized_control,
        "real_term_dominates_fitted_weights": real_term_dominates,
        "verdict": verdict,
    }
