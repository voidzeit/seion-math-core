"""Safe file-backed mutation primitives for canonical repository services."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


class LockError(RuntimeError):
    pass


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


class FileLock:
    def __init__(self, path: Path, stale_seconds: int = 3600) -> None:
        self.path = path
        self.stale_seconds = stale_seconds
        self.acquired = False

    def __enter__(self) -> "FileLock":
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps({"pid": os.getpid(), "created_utc": datetime.now(timezone.utc).isoformat()}) + "\n"
        try:
            fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(payload)
            self.acquired = True
            return self
        except FileExistsError as exc:
            age = time.time() - self.path.stat().st_mtime if self.path.exists() else 0
            raise LockError(f"Lock exists ({age:.1f}s old): {self.path}") from exc

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        if self.acquired:
            try:
                self.path.unlink()
            except FileNotFoundError:
                pass
            self.acquired = False


def atomic_write_bytes(path: Path, data: bytes, expected_sha256: str | None = None, backup_dir: Path | None = None) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    if expected_sha256 is not None and path.exists() and sha256_bytes(path.read_bytes()) != expected_sha256:
        raise LockError(f"Optimistic concurrency hash mismatch: {path}")
    if backup_dir is not None and path.exists():
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup = backup_dir / f"{path.name}.{int(time.time())}.bak"
        backup.write_bytes(path.read_bytes())
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)
    return sha256_bytes(data)


def atomic_write_text(path: Path, text: str, expected_sha256: str | None = None, backup_dir: Path | None = None) -> str:
    return atomic_write_bytes(path, text.encode("utf-8"), expected_sha256, backup_dir)


def atomic_write_json(path: Path, value: Any, expected_sha256: str | None = None, backup_dir: Path | None = None) -> str:
    text = json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    return atomic_write_text(path, text, expected_sha256, backup_dir)


def append_jsonl(path: Path, value: Any, lock_path: Path | None = None) -> str:
    lock = lock_path or path.with_suffix(path.suffix + ".lock")
    line = json.dumps(value, ensure_ascii=False, sort_keys=True) + "\n"
    with FileLock(lock):
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("ab") as handle:
            handle.write(line.encode("utf-8"))
            handle.flush()
            os.fsync(handle.fileno())
    return sha256_bytes(line.encode("utf-8"))
