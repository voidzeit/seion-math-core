from __future__ import annotations

import torch

from seion_kgr.score_space import (
    CandidateWhitening,
    grassmann_chordal_distance,
    prefix_allocation_dp,
    prefix_lagrangian_allocation,
    ranking_certificate,
    spectral_energy_ranks,
    spectral_waterfill,
)


def test_candidate_whitening_preserves_scores_full_rank():
    torch.manual_seed(3)
    entities = torch.randn(11, 5, dtype=torch.float64)
    queries = torch.randn(7, 5, dtype=torch.float64)
    whitening = CandidateWhitening.fit(entities)
    reconstructed = whitening.reconstruct_scores(queries, entities)
    torch.testing.assert_close(reconstructed, queries @ entities.T, rtol=1e-10, atol=1e-10)


def test_singular_candidate_gram_preserves_scores_and_projector_is_supported():
    torch.manual_seed(4)
    base = torch.randn(12, 3, dtype=torch.float64)
    entities = torch.cat([base, torch.zeros(12, 2, dtype=torch.float64)], dim=1)
    queries = torch.randn(8, 5, dtype=torch.float64)
    whitening = CandidateWhitening.fit(entities)
    assert whitening.support_rank == 3
    torch.testing.assert_close(
        whitening.reconstruct_scores(queries, entities), queries @ entities.T, rtol=1e-10, atol=1e-10
    )
    projector = whitening.relation_projector(queries, rank=2)
    torch.testing.assert_close(
        projector.basis.T @ (torch.eye(5, dtype=torch.float64) - whitening.support_projector),
        torch.zeros((2, 5), dtype=torch.float64),
        rtol=1e-8,
        atol=1e-8,
    )


def test_spectral_projector_matches_score_space_rank_oracle():
    torch.manual_seed(5)
    entities = torch.randn(16, 6, dtype=torch.float64)
    queries = torch.randn(9, 6, dtype=torch.float64)
    whitening = CandidateWhitening.fit(entities)
    projector = whitening.relation_projector(queries, rank=3)
    full = queries @ entities.T
    compressed = whitening.projected_scores(queries, entities, projector)
    observed = (full - compressed).pow(2).sum()
    assert abs(float(observed) - float(projector.residual_energy)) < 1e-8


def test_waterfill_and_energy_ranks_are_prefix_policies():
    spectra = torch.tensor([[9.0, 1.0, 0.0], [4.0, 3.0, 1.0]], dtype=torch.float64)
    ranks = spectral_energy_ranks(spectra[0], [0.9, 0.99])
    assert ranks[0.9] == 1
    assert ranks[0.99] == 2
    result = spectral_waterfill(spectra, tolerance_squared=0.5)
    assert result["feasible"]
    assert result["ranks"] == [1, 3]


def test_ranking_certificate_and_grassmann_distance():
    full = torch.tensor([[5.0, 4.0, 1.0], [3.0, 2.9, 0.0]])
    compressed = torch.tensor([[4.9, 4.1, 1.0], [2.8, 3.1, 0.0]])
    result = ranking_certificate(full, compressed, torch.tensor([0.1, 0.1]), k=1)
    assert result["stable"].tolist() == [True, False]
    q = torch.eye(4)[:, :2]
    assert float(grassmann_chordal_distance(q, q)) == 0.0


def test_prefix_allocation_dp_finds_exact_small_case_solution():
    spectra = torch.tensor([[8.0, 1.0, 0.0], [5.0, 4.0, 0.0]])
    result = prefix_allocation_dp(spectra, budget_units=3)
    assert result["feasible"]
    assert result["cost_units"] == 3
    assert result["allocation"] in ([1, 2], [2, 1])
    assert abs(float(result["weighted_residual"]) - 0.5) < 1e-12


def test_prefix_lagrangian_allocation_handles_shared_nonmonotone_modes():
    spectra = torch.tensor([[1.0, 8.0, 0.0], [1.0, 4.0, 0.0]])
    result = prefix_lagrangian_allocation(spectra, tolerance_squared=0.5)
    assert result["feasible"]
    assert result["ranks"] == [2, 2]
