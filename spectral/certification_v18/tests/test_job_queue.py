from __future__ import annotations

from spectral.certification_v18.hardware.job_queue import JobQueue


def test_submit_and_mark_completed(tmp_path):
    q = JobQueue(tmp_path / "ledger.jsonl")
    record = q.submit(scientific_instance_id="A_n16_r4_seed0", seed=0, precision="float64", hardware="cpu", config={"n": 16}, script_hash="abc123")
    assert record.retry_count == 0
    q.mark(record.execution_id, "COMPLETED", output_hashes={"result.json": "deadbeef"})
    resumable = q.resumable_jobs()
    assert resumable == []


def test_retry_increments_count_and_preserves_history(tmp_path):
    q = JobQueue(tmp_path / "ledger.jsonl")
    r1 = q.submit(scientific_instance_id="A_n16_r4_seed0", seed=0, precision="float64", hardware="cpu", config={"n": 16}, script_hash="abc")
    q.mark(r1.execution_id, "FAILED", error="OOM")
    r2 = q.submit(scientific_instance_id="A_n16_r4_seed0", seed=0, precision="float64", hardware="cpu", config={"n": 16}, script_hash="abc")
    assert r2.retry_count == 1
    assert r2.execution_id != r1.execution_id
    resumable = q.resumable_jobs()
    assert len(resumable) == 1
    assert resumable[0].execution_id == r2.execution_id


def test_lineage_follows_checkpoint_chain(tmp_path):
    q = JobQueue(tmp_path / "ledger.jsonl")
    r1 = q.submit(scientific_instance_id="inst1", seed=0, precision="float64", hardware="cpu", config={}, script_hash="x")
    q.mark(r1.execution_id, "COMPLETED", output_hashes={})
    r2 = q.submit(scientific_instance_id="inst2", seed=0, precision="float64", hardware="cpu", config={}, script_hash="x", checkpoint_parent_execution_id=r1.execution_id)
    chain = q.lineage(r2.execution_id)
    assert chain == [r2.execution_id, r1.execution_id]
