import json

from seion_core.canonical.atomic import atomic_write_json, sha256_file
from seion_core.canonical.models import EvidenceEvent
from seion_core.canonical.services import CanonicalRepositoryService


def test_atomic_json_and_event_ledger(tmp_path):
    target = tmp_path / "state.json"
    atomic_write_json(target, {"ok": True})
    assert json.loads(target.read_text()) == {"ok": True}
    assert len(sha256_file(target)) == 64
    service = CanonicalRepositoryService(tmp_path)
    event = EvidenceEvent(event_id="evt_test", event_type="TEST", subject_id="subject", authority_level=1, actor="pytest", status="observed")
    assert service.append_event(event)
    assert (tmp_path / ".ai/evidence/ledger.jsonl").exists()
