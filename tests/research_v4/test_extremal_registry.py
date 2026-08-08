import pytest

from seion_core.research_v4.extremal_registry import ExtremalRecord, merge_extremal_records


def record(lower, upper):
    return ExtremalRecord("chain", 2, 0.5, "real", 2, 1, lower, upper, "construction", "theorem", "OPEN", "test")


def test_extremal_registry_preserves_lower_upper_band_and_classification():
    merged = merge_extremal_records(record(0.2, 0.5), record(0.3, 0.4))
    assert merged.lower_bound == 0.3
    assert merged.upper_bound == 0.4
    assert merged.status == "POSITIVE_LOWER_BOUND_WITH_NONZERO_GAP"


def test_extremal_registry_closes_only_matching_band_and_handles_zero_theorem():
    assert merge_extremal_records(record(0.5, 0.5), record(0.5, 0.5)).status == "EXACTLY_DETERMINED_POSITIVE"
    zero = ExtremalRecord("single", 1, 0.5, "real", 1, 1, 0.0, 0.0, "none", "k-1 theorem", "PROVED", "test")
    assert zero.status == "EXACTLY_ZERO_BY_THEOREM"


def test_extremal_registry_rejects_looser_upper_or_inconsistent_cells():
    with pytest.raises(ValueError, match="tighten"):
        merge_extremal_records(record(0.2, 0.5), record(0.3, 0.6))
    with pytest.raises(ValueError, match="same extremal"):
        merge_extremal_records(record(0.2, 0.5), ExtremalRecord("branch", 2, 0.5, "real", 2, 1, 0.2, 0.5, "x", "y", "OPEN", "test"))

