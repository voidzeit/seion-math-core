from pathlib import Path

import pytest

from seion_kgr.train_sratm_sealed import SealedTestAccessViolation, _forbidden_test_path, sealed_access_sentinel


def test_sealed_runner_rejects_test_like_split_paths():
    assert _forbidden_test_path(Path("data/FB15K-237/test.txt"))
    assert _forbidden_test_path("C:/dataset/test.tsv")
    assert not _forbidden_test_path(Path("data/FB15K-237/train.txt"))
    assert not _forbidden_test_path(Path("data/FB15K-237/valid.txt"))


def test_runtime_sentinel_fails_closed(tmp_path):
    log = []
    with pytest.raises(SealedTestAccessViolation):
        with sealed_access_sentinel(log):
            Path("data/FB15K-237/test.txt").open("rb")
