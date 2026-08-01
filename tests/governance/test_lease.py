from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from seion_core.orchestration.lease import Lease, LeaseConflict, acquire, release, status


def test_acquire_and_release_round_trip(tmp_path: Path):
    lease = acquire(tmp_path, resource="task:demo", session_id="s1", ttl_minutes=30)
    assert status(tmp_path, resource="task:demo").session_id == "s1"
    assert release(tmp_path, resource="task:demo", session_id="s1") is True
    assert status(tmp_path, resource="task:demo") is None


def test_second_session_cannot_acquire_a_live_lease(tmp_path: Path):
    acquire(tmp_path, resource="task:demo", session_id="s1", ttl_minutes=30)
    with pytest.raises(LeaseConflict):
        acquire(tmp_path, resource="task:demo", session_id="s2", ttl_minutes=30)


def test_same_session_can_reacquire_its_own_lease(tmp_path: Path):
    acquire(tmp_path, resource="task:demo", session_id="s1", ttl_minutes=30)
    lease = acquire(tmp_path, resource="task:demo", session_id="s1", ttl_minutes=30)
    assert lease.session_id == "s1"


def test_release_by_non_owner_raises(tmp_path: Path):
    acquire(tmp_path, resource="task:demo", session_id="s1", ttl_minutes=30)
    with pytest.raises(LeaseConflict):
        release(tmp_path, resource="task:demo", session_id="s2")


def test_expired_lease_is_force_breakable_by_another_session(tmp_path: Path):
    path = tmp_path / ".ai" / "runtime" / "locks" / "task-demo.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    past = datetime.now(timezone.utc) - timedelta(minutes=5)
    expired = Lease(
        lease_id="deadbeef",
        session_id="s1",
        resource="task:demo",
        pid=999999,
        machine="some-other-machine",
        acquired_at=past.isoformat(),
        heartbeat_at=past.isoformat(),
        expires_at=past.isoformat(),
        ttl_minutes=1,
    )
    path.write_text(json.dumps(expired.to_dict()), encoding="utf-8")
    lease = acquire(tmp_path, resource="task:demo", session_id="s2", ttl_minutes=30)
    assert lease.session_id == "s2"


def test_unexpired_cross_machine_lease_is_not_breakable(tmp_path: Path):
    path = tmp_path / ".ai" / "runtime" / "locks" / "task-demo.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)
    live = Lease(
        lease_id="deadbeef",
        session_id="s1",
        resource="task:demo",
        pid=999999,  # would look dead locally, but machine differs so pid is not checked
        machine="some-other-machine",
        acquired_at=now.isoformat(),
        heartbeat_at=now.isoformat(),
        expires_at=(now + timedelta(minutes=30)).isoformat(),
        ttl_minutes=30,
    )
    path.write_text(json.dumps(live.to_dict()), encoding="utf-8")
    with pytest.raises(LeaseConflict):
        acquire(tmp_path, resource="task:demo", session_id="s2", ttl_minutes=30)


def test_same_machine_dead_pid_is_force_breakable(tmp_path: Path):
    import platform

    path = tmp_path / ".ai" / "runtime" / "locks" / "task-demo.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)
    dead = Lease(
        lease_id="deadbeef",
        session_id="s1",
        resource="task:demo",
        pid=999999999,  # extremely unlikely to be a live pid
        machine=platform.node(),
        acquired_at=now.isoformat(),
        heartbeat_at=now.isoformat(),
        expires_at=(now + timedelta(minutes=30)).isoformat(),  # not expired, but pid is dead
        ttl_minutes=30,
    )
    path.write_text(json.dumps(dead.to_dict()), encoding="utf-8")
    lease = acquire(tmp_path, resource="task:demo", session_id="s2", ttl_minutes=30)
    assert lease.session_id == "s2"


def test_resource_slug_handles_special_characters(tmp_path: Path):
    lease = acquire(tmp_path, resource="src/seion_core/orchestration/", session_id="s1")
    assert status(tmp_path, resource="src/seion_core/orchestration/").lease_id == lease.lease_id
