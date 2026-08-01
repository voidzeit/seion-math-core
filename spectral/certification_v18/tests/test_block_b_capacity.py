from __future__ import annotations

import torch

from spectral.certification_v18.blocks.block_b_commutator import (
    build_instance,
    run_block_b_capacity_test,
    solve_optimal_phi,
    unexplained_rel,
)
from spectral.certification_v18.model import (
    SpectralModelV18,
    commutator,
    identity,
    orthonormalize_columns,
    projector_from_u,
)


def test_optimal_phi_is_never_worse_than_the_real_associator_phi():
    """The optimal free Phi is a least-squares minimizer over the SAME
    functional form; by definition no other Phi (including the real
    associator-derived one) can achieve a strictly lower residual."""
    inst = build_instance(seed=0, n=16, rank=4, cp_rank=4)
    gen = torch.Generator().manual_seed(0)
    model = SpectralModelV18(n=16, rank=4, arity=3, cp_rank=4, device="cpu", dtype="float64", generator=gen)
    U = orthonormalize_columns(model.u())
    P = projector_from_u(U)
    K = identity(16, device="cpu", dtype=model.cdtype) - P
    raw_comm = commutator(model.delta, P)

    phi_opt = solve_optimal_phi(U, K, model.delta, raw_comm, rank=4)
    c_theta_opt = U @ phi_opt @ (U.conj().T @ model.delta @ K) - (K @ model.delta @ U) @ phi_opt.conj().T @ U.conj().T
    opt_rel = unexplained_rel(raw_comm, c_theta_opt)
    real_rel = unexplained_rel(raw_comm, inst.c_theta)
    assert opt_rel <= real_rel + 1e-6


def test_capacity_experiment_runs_and_reports_a_verdict():
    result = run_block_b_capacity_test(seeds=[0, 1], steps=40, n=12, rank=3, cp_rank=3)
    assert result["verdict"] in (
        "REAL_PHI_NEAR_OPTIMAL_FOR_THIS_FORMULA",
        "REAL_PHI_FAR_FROM_FORMULA_CEILING_CAPACITY_GAP",
    )
    for row in result["rows"]:
        assert row["optimal_free_phi_unexplained_rel"] <= row["trained_real_phi_unexplained_rel"] + 1e-6
