"""Gate 11 (per the Fase-2 proposal this session received): the FP64
oracle's self-test battery is fully seeded and must be exactly
reproducible — same seed, same process, identical floats — since it is
meant to serve as ground truth other implementations are checked
against. If it weren't deterministic, "cp_dense_equivalence max error
8.9e-16" from one run would be meaningless as a reference number.
"""
import seion_kgr_reference_fp64 as oracle


def _flatten_numeric(obj, prefix=""):
    """Collect (path, value) pairs for every int/float leaf in a nested
    dict, so two runs can be compared value-by-value with a clear error
    message if any field differs."""
    out = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            out.update(_flatten_numeric(v, f"{prefix}.{k}" if prefix else str(k)))
    elif isinstance(obj, (int, float)):
        out[prefix] = obj
    return out


def test_self_tests_are_byte_identical_across_repeated_calls_same_seed():
    first = oracle.run_self_tests(seed=7)
    second = oracle.run_self_tests(seed=7)
    flat_first = _flatten_numeric(first)
    flat_second = _flatten_numeric(second)
    assert flat_first.keys() == flat_second.keys()
    for key in flat_first:
        assert flat_first[key] == flat_second[key], f"non-deterministic field: {key} ({flat_first[key]} != {flat_second[key]})"


def test_self_tests_differ_with_a_different_seed():
    """Sanity complement: if two different seeds produced identical
    results, the determinism test above would be vacuous (it could be
    passing because nothing is actually seed-dependent, not because the
    computation is genuinely reproducible)."""
    a = oracle.run_self_tests(seed=7)
    b = oracle.run_self_tests(seed=8)
    flat_a = _flatten_numeric(a)
    flat_b = _flatten_numeric(b)
    differing = [k for k in flat_a if flat_a.get(k) != flat_b.get(k)]
    assert differing, "different seeds produced identical numeric output everywhere — suspicious"


def test_projector_random_rank_is_seed_deterministic():
    p1 = oracle.Projector.random_rank(dim=6, rank=3, seed=42)
    p2 = oracle.Projector.random_rank(dim=6, rank=3, seed=42)
    assert (p1.Q == p2.Q).all()
    p3 = oracle.Projector.random_rank(dim=6, rank=3, seed=43)
    assert not (p1.Q == p3.Q).all()
