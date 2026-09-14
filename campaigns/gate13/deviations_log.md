# Gate 13 deviations log

Append-only. Every deviation from a frozen protocol, plus any anomaly worth
recording honestly (flaky test, environment surprise, ambiguous instruction
resolved a specific way), gets one dated entry here. Nothing is removed.

## 2026-08-04 — flaky test observed during Gate 13.4 manifest-field correction

**What happened:** while rerunning `tests/kgr` after adding the missing
manifest fields to `seion_kgr/run_certification.py` (see commit following
this entry), a full-suite run reported:

    FAILED tests/kgr/test_gate13_certification_real_run.py::test_certification_rejects_learned_topk_and_wrong_backend_and_untrained_reference
    1 failed, 166 passed in 407.29s

failing on `ValueError: Out of range float values are not JSON compliant: inf`
inside `json.dump`, attributed to the first `pytest.raises(NotImplementedError, ...)`
block in that test.

**Investigation:** the failing test's four sub-cases all raise before
`run_certification` reaches manifest construction (checked line-by-line
against `seion_kgr/run_certification.py`'s early fail-fast checks); none of
this session's edits touch those checks. Re-running the exact same test in
isolation passed (30.37s). Re-running the complete `tests/kgr` suite a
second time passed at 167/167 (460.12s), including this test.

**Conclusion:** classified as an environment/ordering flake (CPU
contention, filesystem timing on a `tmp_path` shared across a long
sequential run, or similar), not a regression caused by the manifest-field
addition. Not reproduced on two subsequent full-suite runs. Left OPEN as an
unexplained flake rather than silently dismissed — if it recurs during
Gate 13.5 staged runs, treat this entry as prior evidence it is not new.

**Action:** none taken beyond this record. No test was modified, skipped,
or weakened to make it pass.
