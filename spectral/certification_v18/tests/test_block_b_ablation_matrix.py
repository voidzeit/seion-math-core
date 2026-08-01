from __future__ import annotations

from spectral.certification_v18.blocks.block_b_ablation_matrix import full_ablation_matrix


def test_ablation_matrix_runs_all_regimes():
    rows = full_ablation_matrix(seed=0, n=12, rank=3, cp_rank=3, steps=80)
    names = {r.regime for r in rows}
    assert names == {
        "isolated_B_only",
        "plus_closure",
        "plus_associator",
        "joint_all",
        "frozen_law_train_projector",
        "frozen_projector_train_law",
        "staged_competing_then_B",
    }
    for r in rows:
        assert r.final_comm_unexplained_rel == r.final_comm_unexplained_rel  # not NaN


def test_isolated_b_reaches_lower_unexplained_rel_than_joint_all():
    rows = {r.regime: r for r in full_ablation_matrix(seed=0, n=12, rank=3, cp_rank=3, steps=150)}
    assert rows["isolated_B_only"].final_comm_unexplained_rel <= rows["joint_all"].final_comm_unexplained_rel + 1e-6, (
        "isolated training should reach at least as low an unexplained residual as training under competing objectives"
    )
