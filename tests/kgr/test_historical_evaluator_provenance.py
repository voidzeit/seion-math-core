from seion_kgr.historical_evaluator_provenance import _hypotheses


def test_historical_provenance_classifies_checkpoint_and_open_loader_cause(tmp_path):
    hypotheses = _hypotheses(
        tmp_path,
        tmp_path,
        {"integrity": {"checkpoint_sha256": "last"}, "checkpoint_step": 4600},
        {
            "checkpoint_last.pt": {"sha256": "last", "embedded_step": 4600},
            "checkpoint_best.pt": {"sha256": "best", "embedded_step": 4608},
        },
    )
    by_id = {item["id"]: item for item in hypotheses}
    assert by_id["H01_CHECKPOINT_IDENTITY"]["status"] == "REFUTED"
    assert by_id["H02_BEST_LAST_CONFUSION"]["status"] == "REFUTED"
    assert by_id["H06_HISTORICAL_LOADER_FILTER_PROVENANCE"]["status"] == "OPEN_HIGH_PRIORITY"
    assert by_id["H10_TEST_DERIVED_HISTORY"]["status"] == "UNKNOWN_NOT_ESTABLISHED"
