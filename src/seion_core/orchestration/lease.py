"""Liveness-aware resource leases under .ai/runtime/locks/, so two
lifecycle sessions cannot claim the same task/paths concurrently.

Liveness rule (deliberately simple, modeled on the truth table in
Hyperghaps EMA / EMA-AI's AGENT_MEMORY_ARCHITECTURE.md: age-based
staleness is wrong in both directions -- a lease can be young but its
owning process already dead, or old but still legitimately held):

- same machine + owning pid no longer running -> force-breakable
  regardless of ttl.
- different machine, or same machine + pid still running -> only TTL
  expiry breaks it.
"""

from __future__ import annotations

import ctypes
import json
import os
import platform
import secrets
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


class LeaseConflict(RuntimeError):
    pass


def _locks_dir(repo_root: str | Path) -> Path:
    return Path(repo_root) / ".ai" / "runtime" / "locks"


def _slug(resource: str) -> str:
    return "".join(c if c.isalnum() else "-" for c in resource).strip("-") or "resource"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if os.name == "nt":
        try:
            process_query_limited_information = 0x1000
            handle = ctypes.windll.kernel32.OpenProcess(process_query_limited_information, False, pid)
            if handle:
                ctypes.windll.kernel32.CloseHandle(handle)
                return True
            return False
        except Exception:
            return True  # cannot determine; conservative default is "alive", never force-break blindly
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


@dataclass
class Lease:
    lease_id: str
    session_id: str
    resource: str
    pid: int
    machine: str
    acquired_at: str
    heartbeat_at: str
    expires_at: str
    ttl_minutes: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Lease":
        return cls(**data)


def _path_for(repo_root: str | Path, resource: str) -> Path:
    return _locks_dir(repo_root) / f"{_slug(resource)}.json"


def _is_breakable(lease: Lease) -> bool:
    if _now() >= datetime.fromisoformat(lease.expires_at):
        return True
    if lease.machine == platform.node() and not _pid_alive(lease.pid):
        return True
    return False


def acquire(repo_root: str | Path, *, resource: str, session_id: str, ttl_minutes: int = 60) -> Lease:
    path = _path_for(repo_root, resource)
    if path.exists():
        existing = Lease.from_dict(json.loads(path.read_text(encoding="utf-8")))
        if existing.session_id != session_id and not _is_breakable(existing):
            raise LeaseConflict(
                f"resource {resource!r} is held by session {existing.session_id!r} "
                f"(lease {existing.lease_id}, expires {existing.expires_at}); not breakable yet"
            )
    now = _now()
    lease = Lease(
        lease_id=secrets.token_hex(8),
        session_id=session_id,
        resource=resource,
        pid=os.getpid(),
        machine=platform.node(),
        acquired_at=now.isoformat(),
        heartbeat_at=now.isoformat(),
        expires_at=(now + timedelta(minutes=ttl_minutes)).isoformat(),
        ttl_minutes=ttl_minutes,
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(lease.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return lease


def release(repo_root: str | Path, *, resource: str, session_id: str) -> bool:
    path = _path_for(repo_root, resource)
    if not path.exists():
        return False
    existing = Lease.from_dict(json.loads(path.read_text(encoding="utf-8")))
    if existing.session_id != session_id:
        raise LeaseConflict(f"session {session_id!r} does not own the lease on {resource!r}")
    path.unlink()
    return True


def status(repo_root: str | Path, *, resource: str) -> Lease | None:
    path = _path_for(repo_root, resource)
    if not path.exists():
        return None
    return Lease.from_dict(json.loads(path.read_text(encoding="utf-8")))
