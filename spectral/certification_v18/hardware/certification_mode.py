"""Certification-mode hardware discipline (mission sections 3 and 5).

Real gotcha found and fixed during this campaign: the LEGACY script
(spectral/legacy/v17/...py:60-67) sets
`torch.backends.cuda.matmul.allow_tf32 = True` and
`torch.set_float32_matmul_precision("high")` unconditionally at IMPORT
TIME if CUDA is available. Anything in a v18 certification-mode process
that imports code depending on legacy primitives (or simply runs after
something else enabled TF32 in the same process) must explicitly
re-disable it — TF32 is a process-global flag, not scoped to a module.
`enter_certification_mode()` is the single call site that does this, and
`assert_certification_discipline()` is a runtime check other code can call
to fail loudly instead of silently computing under contaminated settings.
"""

from __future__ import annotations

from dataclasses import dataclass

import torch


@dataclass
class HardwareInventory:
    cuda_available: bool
    gpu_name: str | None
    cuda_version: str | None
    torch_version: str
    cpu_logical_cores: int


def inventory() -> HardwareInventory:
    import os

    return HardwareInventory(
        cuda_available=torch.cuda.is_available(),
        gpu_name=torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        cuda_version=torch.version.cuda if torch.cuda.is_available() else None,
        torch_version=torch.__version__,
        cpu_logical_cores=os.cpu_count() or 1,
    )


def enter_certification_mode() -> None:
    """Idempotent: safe to call multiple times, safe to call after
    anything else (including the legacy module) may have mutated these
    process-global flags."""
    if torch.cuda.is_available():
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False
    torch.set_float32_matmul_precision("highest")
    torch.use_deterministic_algorithms(True)


def assert_certification_discipline() -> None:
    errors = []
    if torch.cuda.is_available():
        if torch.backends.cuda.matmul.allow_tf32:
            errors.append("torch.backends.cuda.matmul.allow_tf32 is True")
        if torch.backends.cudnn.allow_tf32:
            errors.append("torch.backends.cudnn.allow_tf32 is True")
    if torch.get_float32_matmul_precision() != "highest":
        errors.append(f"float32_matmul_precision={torch.get_float32_matmul_precision()!r}, expected 'highest'")
    if not torch.are_deterministic_algorithms_enabled():
        errors.append("deterministic algorithms are not enabled")
    if errors:
        raise RuntimeError("certification-mode discipline violated: " + "; ".join(errors))
