from __future__ import annotations

from spectral.certification_v18.blocks.block_b_commutator import (
    build_instance,
    run_block_b_ablation,
    unexplained_rel,
)


def test_zero_predictor_unexplained_rel_is_exactly_one():
    inst = build_instance(seed=0, n=12, rank=3, cp_rank=3)
    zero = inst.raw_comm * 0
    assert abs(unexplained_rel(inst.raw_comm, zero) - 1.0) < 1e-12


def test_best_rank_2r_is_near_exact_since_raw_comm_has_that_rank():
    inst = build_instance(seed=0, n=12, rank=3, cp_rank=3)
    rel = unexplained_rel(inst.raw_comm, inst.rank2r_best)
    assert rel < 1e-6, "raw_comm has rank <= 2*rank by construction; its own rank-2r SVD truncation must reconstruct it almost exactly"


def test_c_theta_beats_zero_but_gate_requires_beating_randomized_control_too():
    inst = build_instance(seed=0, n=12, rank=3, cp_rank=3)
    as_given = unexplained_rel(inst.raw_comm, inst.c_theta)
    assert as_given < 1.0, "sanity: C_theta should at least be nonzero-correlated with the target"


def test_ablation_runs_end_to_end_and_reports_a_verdict():
    result = run_block_b_ablation(train_seeds=[1, 2, 3, 4, 5], held_out_seeds=[101, 102, 103], n=16, rank=4, cp_rank=4)
    assert result["verdict"] in ("SURVIVES_HELD_OUT_ADVERSARIAL_TEST", "REFUTED_BY_RANDOMIZED_CONTROL")
    assert len(result["held_out_report"]) == 3
    assert set(result["train_seeds"]) == {1, 2, 3, 4, 5}


def test_train_and_held_out_seeds_must_be_disjoint():
    import pytest

    with pytest.raises(ValueError):
        run_block_b_ablation(train_seeds=[1, 2], held_out_seeds=[2, 3], n=12, rank=3, cp_rank=3)
