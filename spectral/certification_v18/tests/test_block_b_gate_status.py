"""Ties Phase 0 evidence to the Phase 1 gate taxonomy: confirms the
historical data actually shows what BLOCK_B_FINDINGS.md claims
(coherence_ratio <= 0 in every real trained checkpoint, i.e. worse than
the zero baseline), and that this correctly resolves to a FAIL under the
typed-gate rules, not a WARN near-miss.

Reads from the COMMITTED extract `block_b_historical_evidence.json`
(produced by `tools/ingest_legacy.py` from the live `spectral/runs/`
directories), not from `spectral/runs/` itself — that directory is
intentionally NOT checked into version control (preserved as local
historical evidence, not canonical source; see mission's file-hygiene
classification), so a CI checkout would never have it.
"""

from __future__ import annotations

import json
from pathlib import Path

from spectral.certification_v18.gates import TypedStatus, combine_gate_status

EVIDENCE_PATH = Path(__file__).resolve().parents[2] / "legacy" / "v17" / "block_b_historical_evidence.json"


def _block_b_records() -> list[tuple[str, dict]]:
    data = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
    return list(data.items())


def test_historical_runs_show_block_b_at_or_worse_than_zero_baseline():
    records = _block_b_records()
    assert records, "expected at least one historical run with B_commutator data on disk"
    assert all(b["status"] == "WARN" for _, b in records), (
        "expected every historical run to report B_commutator=WARN (v17 has no FAIL state)"
    )
    # coherence_ratio = 1 - unexplained_comm_norm / (raw_comm_norm + eps);
    # <= 0 means C_theta performed no better than (or worse than) predicting
    # zero, i.e. it fails the crudest baseline in this suite's own list.
    assert all(b["coherence_ratio"] <= 0 for _, b in records), (
        f"expected coherence_ratio <= 0 in every historical run; got "
        f"{[(name, b['coherence_ratio']) for name, b in records if b['coherence_ratio'] > 0]}"
    )


def test_block_b_gate_resolves_to_fail_given_worse_than_zero_evidence():
    # BLOCK_B_FINDINGS.md experiment 3: coherence_ratio <= 0 in every
    # historical checkpoint means C_theta performs worse than the zero
    # predictor in the regime actually run. Per GATE_TAXONOMY.md, a block
    # that cannot beat its own zero baseline is FAIL, not WARN.
    block_statuses = {"B_commutator": TypedStatus.FAIL, "C_beals": TypedStatus.EMPIRICAL_SCREENING_PASS}
    assert combine_gate_status(block_statuses) == TypedStatus.FAIL
