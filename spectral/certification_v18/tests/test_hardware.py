from __future__ import annotations

import torch

from spectral.certification_v18.hardware.certification_mode import (
    assert_certification_discipline,
    enter_certification_mode,
    inventory,
)


def test_inventory_reports_real_hardware():
    inv = inventory()
    assert inv.cpu_logical_cores >= 1
    assert isinstance(inv.cuda_available, bool)


def test_enter_certification_mode_then_assert_does_not_raise():
    # simulate contamination (as if legacy module had been imported)
    if torch.cuda.is_available():
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.backends.cudnn.allow_tf32 = True
    torch.set_float32_matmul_precision("high")
    enter_certification_mode()
    assert_certification_discipline()  # must not raise


def test_assert_raises_if_contaminated_after_entering():
    enter_certification_mode()
    if torch.cuda.is_available():
        torch.backends.cuda.matmul.allow_tf32 = True
        try:
            import pytest

            with pytest.raises(RuntimeError, match="tf32"):
                assert_certification_discipline()
        finally:
            enter_certification_mode()  # restore discipline for subsequent tests
