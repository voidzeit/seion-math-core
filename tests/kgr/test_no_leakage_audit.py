from pathlib import Path

import pytest

from seion_kgr.no_leakage_audit import AccessSentinel, is_forbidden_test_path


def test_forbidden_test_path_classifier_is_specific():
    assert is_forbidden_test_path(r"C:\data\FB15K-237\test.txt")
    assert not is_forbidden_test_path(r"C:\data\FB15K-237\valid.txt")
    assert is_forbidden_test_path(r"C:\data\WN18RR\test.txt")


def test_runtime_sentinel_rejects_forbidden_open_without_touching_disk(tmp_path: Path):
    sentinel = AccessSentinel()
    forbidden = tmp_path / "data" / "FB15K-237" / "test.txt"
    with sentinel.installed():
        with pytest.raises(RuntimeError, match="TEST_SPLIT_ACCESS_FORBIDDEN"):
            forbidden.open("r", encoding="utf-8")
    assert len(sentinel.forbidden) == 1


def test_runtime_sentinel_restores_pathlib_stat():
    sentinel = AccessSentinel()
    with sentinel.installed():
        assert Path(".").exists()
    assert Path(".").exists()
