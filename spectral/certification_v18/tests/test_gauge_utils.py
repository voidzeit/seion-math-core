from __future__ import annotations

import torch

from spectral.certification_v18.blocks.gauge_utils import compare_with_gauge, orthogonal_procrustes


def _random_unitary(n: int, seed: int) -> torch.Tensor:
    gen = torch.Generator().manual_seed(seed)
    re = torch.randn(n, n, generator=gen, dtype=torch.float64)
    im = torch.randn(n, n, generator=gen, dtype=torch.float64)
    a = torch.complex(re, im)
    q, _ = torch.linalg.qr(a)
    return q


def test_raw_distance_is_not_gauge_invariant():
    gen = torch.Generator().manual_seed(0)
    m_a = torch.complex(torch.randn(6, 6, generator=gen, dtype=torch.float64), torch.randn(6, 6, generator=gen, dtype=torch.float64))
    q = _random_unitary(6, seed=1)
    m_b = q @ m_a  # gauge-equivalent, but a naive raw comparison should NOT see this as zero
    result = compare_with_gauge(m_a, m_b)
    assert result.raw_distance > 0.1, "sanity: a random gauge rotation should look very different under a raw (unaligned) comparison"


def test_procrustes_aligned_distance_recovers_gauge_equivalence():
    gen = torch.Generator().manual_seed(0)
    m_a = torch.complex(torch.randn(6, 6, generator=gen, dtype=torch.float64), torch.randn(6, 6, generator=gen, dtype=torch.float64))
    q = _random_unitary(6, seed=2)
    m_b = q @ m_a
    result = compare_with_gauge(m_a, m_b)
    assert result.procrustes_aligned_distance < 1e-8, "orthogonal Procrustes must recover exact gauge equivalence"


def test_procrustes_recovers_the_exact_generating_unitary():
    gen = torch.Generator().manual_seed(3)
    m_a = torch.complex(torch.randn(5, 5, generator=gen, dtype=torch.float64), torch.randn(5, 5, generator=gen, dtype=torch.float64))
    q = _random_unitary(5, seed=4)
    m_b = q @ m_a
    q_hat = orthogonal_procrustes(m_a, m_b)
    rel = torch.linalg.norm((q_hat - q).reshape(-1)) / torch.linalg.norm(q.reshape(-1))
    assert rel.item() < 1e-8


def test_permutation_aligned_distance_recovers_row_permutation():
    gen = torch.Generator().manual_seed(5)
    m_a = torch.complex(torch.randn(5, 5, generator=gen, dtype=torch.float64), torch.randn(5, 5, generator=gen, dtype=torch.float64))
    m_b = m_a[[2, 0, 4, 1, 3], :]
    result = compare_with_gauge(m_a, m_b)
    assert result.permutation_search_exhaustive
    assert result.permutation_aligned_distance < 1e-8


def test_amplitude_ratio_reported_separately_from_distance():
    gen = torch.Generator().manual_seed(6)
    m_a = torch.complex(torch.randn(4, 4, generator=gen, dtype=torch.float64), torch.randn(4, 4, generator=gen, dtype=torch.float64))
    m_b = 3.0 * m_a
    result = compare_with_gauge(m_a, m_b)
    assert abs(result.amplitude_ratio - 3.0) < 1e-8
    # raw_distance should reflect the 3x scale mismatch too (not silently absorbed)
    assert result.raw_distance > 1.0
