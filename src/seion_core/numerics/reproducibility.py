from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path


def _run(command: list[str]) -> str | None:
    try:
        return subprocess.check_output(command, stderr=subprocess.STDOUT, text=True, timeout=10).strip()
    except Exception:
        return None


def inventory(repo_root: str | Path | None = None) -> dict:
    root = Path(repo_root or Path.cwd())
    git_hash = _run(["git", "rev-parse", "HEAD"])
    git_status = _run(["git", "status", "--porcelain"])
    python = {"version": sys.version, "executable": sys.executable}
    torch_info = {}
    try:
        import torch
        torch_info = {"version": torch.__version__, "cuda_available": bool(torch.cuda.is_available()), "cuda_version": torch.version.cuda, "device_count": int(torch.cuda.device_count())}
        if torch.cuda.is_available():
            torch_info["devices"] = [{"name": torch.cuda.get_device_name(i), "capability": list(torch.cuda.get_device_capability(i)), "memory_bytes": int(torch.cuda.get_device_properties(i).total_memory)} for i in range(torch.cuda.device_count())]
    except Exception as exc:
        torch_info = {"available": False, "error": str(exc)}
    try:
        import psutil
        memory = psutil.virtual_memory()
        memory_info = {"total_bytes": int(memory.total), "available_bytes": int(memory.available), "cpu_count_physical": psutil.cpu_count(logical=False)}
    except Exception:
        memory_info = {"total_bytes": None, "available_bytes": None}
    return {
        "operating_system": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "cpu_count_logical": os.cpu_count(),
        "memory": memory_info,
        "python": python,
        "torch": torch_info,
        "disk_free_bytes": shutil.disk_usage(root).free if root.exists() else None,
        "git_commit": git_hash,
        "dirty_worktree": bool(git_status),
    }


def write_inventory(repo_root: str | Path) -> tuple[Path, Path, Path]:
    root = Path(repo_root)
    target = root / "artifacts" / "system"
    target.mkdir(parents=True, exist_ok=True)
    data = inventory(root)
    hardware = {key: data[key] for key in ["operating_system", "machine", "processor", "cpu_count_logical", "memory", "torch", "disk_free_bytes"]}
    software = {"python": data["python"], "git_commit": data["git_commit"], "dirty_worktree": data["dirty_worktree"]}
    hardware_path = target / "hardware_inventory.json"; software_path = target / "software_inventory.json"; report_path = target / "environment_report.md"
    hardware_path.write_text(json.dumps(hardware, indent=2, default=str) + "\n", encoding="utf-8")
    software_path.write_text(json.dumps(software, indent=2, default=str) + "\n", encoding="utf-8")
    report_path.write_text("# Environment report\n\n```json\n" + json.dumps(data, indent=2, default=str) + "\n```\n", encoding="utf-8")
    return hardware_path, software_path, report_path


if __name__ == "__main__":
    paths = write_inventory(Path.cwd())
    print(json.dumps({"written": [str(path) for path in paths]}, indent=2))
