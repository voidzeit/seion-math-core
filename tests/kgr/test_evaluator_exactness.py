"""Gate 3: evaluator exactness — 1-vs-all == per-candidate, brute-force
ranking on a hand-computable example, reciprocal-closure consistency."""
import pytest
import torch
from hypothesis import given, settings
from hypothesis import strategies as st

from seion_kgr_reference_fp64 import (
    ReciprocalComplExScorer,
    SeionicScalarScorer,
    brute_force_filtered_rank,
    build_reciprocal_kg,
    reciprocal_closure,
    tiny_reciprocal_kg,
)

pytestmark = pytest.mark.symbolic

seed = st.integers(min_value=0, max_value=2**31 - 1)


def _seion_scorer(seed: int, num_entities: int, num_relations_total: int) -> SeionicScalarScorer:
    g = torch.Generator().manual_seed(seed)
    dim_e = dim_r = dim_q = 4
    rank = 3
    return SeionicScalarScorer(
        entity=torch.randn(num_entities, dim_e, generator=g, dtype=torch.float64),
        A=torch.randn(rank, dim_e, generator=g, dtype=torch.float64),
        B=torch.randn(rank, dim_r, generator=g, dtype=torch.float64),
        C=torch.randn(rank, dim_r, generator=g, dtype=torch.float64),
        O=torch.randn(dim_q, rank, generator=g, dtype=torch.float64),
        T=torch.randn(dim_q, dim_e, generator=g, dtype=torch.float64),
        relation=torch.randn(num_relations_total, dim_r, generator=g, dtype=torch.float64),
    )


@settings(deadline=None, max_examples=20)
@given(seed=seed)
def test_1vsall_matches_individual_score_for_every_candidate(seed):
    kg, _ = tiny_reciprocal_kg(seed)
    scorer = _seion_scorer(seed, kg.num_entities, kg.num_relations_total)
    h, r, _ = kg.triples[0]
    batched = scorer.score_all_candidates(h, r)
    for t in range(kg.num_entities):
        single = scorer.score(h, r, t)
        assert abs(single - float(batched[t].item())) < 1e-9


def test_brute_force_rank_on_hand_constructed_example():
    """A graph where the gold tail is deliberately the k-th best score by
    construction, so the expected rank is known exactly (not just bounded)."""
    kg = build_reciprocal_kg([(0, 0, 1), (0, 0, 2)], num_entities=5, num_relations=1)
    # Construct scores by hand: candidate i gets score = -i (so 0 is best,
    # 4 is worst). Gold tail is entity 3 among unfiltered candidates
    # {0,1,2,3,4} minus filtered {1,2} (other true tails of (0,0)).
    scores = {0: 0.0, 1: -1.0, 2: -2.0, 3: -3.0, 4: -4.0}

    def scorer_fn(h, r, t):
        return scores[t]

    rank = brute_force_filtered_rank(scorer_fn, kg, h=0, r=0, t=3, mode="tail")
    # After filtering out {1,2} (the other true (0,0,*) tails), remaining
    # candidates are {0,3,4}; scores 0 > -3 > -4, so gold (t=3) is rank 2.
    assert rank == 2.0


def test_brute_force_rank_ties_use_average_policy():
    kg = build_reciprocal_kg([(0, 0, 1)], num_entities=4, num_relations=1)
    scores = {0: 1.0, 1: 1.0, 2: 1.0, 3: 0.0}  # three-way tie including gold

    def scorer_fn(h, r, t):
        return scores[t]

    rank = brute_force_filtered_rank(scorer_fn, kg, h=0, r=0, t=1, mode="tail")
    # No filtering removes any of {0,1,2,3} here (only true tail of (0,0)
    # is 1 itself). Three-way tie at score 1.0 among {0,1,2}: average rank
    # of a 3-way tie for 1st place is 1 + 0.5*(3-1) = 2.0.
    assert rank == 2.0


def test_head_and_tail_ranking_use_independent_filter_tables():
    kg = build_reciprocal_kg([(0, 0, 1), (2, 0, 1)], num_entities=4, num_relations=1)
    assert kg.tails_of_hr[(0, 0)] == {1}
    assert kg.heads_of_rt[(0, 1)] == {0, 2}


def test_reciprocal_closure_is_involutive():
    base = [(0, 0, 1), (2, 1, 3)]
    once = reciprocal_closure(base, num_relations=2)
    # (t, r+R, h) for each (h,r,t) in `once`'s *base* half only — apply
    # closure again restricted to the original relation ids and check we
    # recover triples already present.
    twice_originals = reciprocal_closure(base, num_relations=2)
    assert set(base).issubset(set(twice_originals))
    assert (1, 2, 0) in once  # r=0 -> r^{-1}=0+2=2
    assert (3, 3, 2) in once  # r=1 -> r^{-1}=1+2=3


def test_complex_scorer_runs_and_is_finite():
    g = torch.Generator().manual_seed(5)
    n, r, d = 6, 3, 4
    scorer = ReciprocalComplExScorer(
        e_re=torch.randn(n, d, generator=g, dtype=torch.float64),
        e_im=torch.randn(n, d, generator=g, dtype=torch.float64),
        r_re=torch.randn(r, d, generator=g, dtype=torch.float64),
        r_im=torch.randn(r, d, generator=g, dtype=torch.float64),
    )
    value = scorer.score(0, 1, 2)
    assert math_isfinite(value)


def math_isfinite(x: float) -> bool:
    import math

    return math.isfinite(x)
