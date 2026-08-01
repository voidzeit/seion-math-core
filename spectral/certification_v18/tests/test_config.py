from __future__ import annotations

import pytest

from spectral.certification_v18.config import AuditConfigV18, ConfigValidationError, Dtype, EvalMode


def _base_kwargs(**overrides):
    kwargs = dict(seed=0, device="cpu", dtype=Dtype.FLOAT32, eval_mode=EvalMode.SCREENING)
    kwargs.update(overrides)
    return kwargs


def test_screening_mode_has_no_extra_requirements():
    cfg = AuditConfigV18(**_base_kwargs())
    cfg.validate()  # should not raise


def test_certification_mode_requires_double_precision():
    cfg = AuditConfigV18(**_base_kwargs(eval_mode=EvalMode.CERTIFICATION, held_out_seeds=(99,)))
    with pytest.raises(ConfigValidationError, match="dtype"):
        cfg.validate()


def test_certification_mode_requires_held_out_seed():
    cfg = AuditConfigV18(**_base_kwargs(eval_mode=EvalMode.CERTIFICATION, dtype=Dtype.FLOAT64))
    with pytest.raises(ConfigValidationError, match="held_out_seeds"):
        cfg.validate()


def test_certification_mode_forbids_non_strict_resume():
    cfg = AuditConfigV18(
        **_base_kwargs(
            eval_mode=EvalMode.CERTIFICATION,
            dtype=Dtype.FLOAT64,
            held_out_seeds=(99,),
            resume=True,
            strict_resume=False,
        )
    )
    with pytest.raises(ConfigValidationError, match="strict_resume"):
        cfg.validate()


def test_certification_mode_forbids_training_seed_in_held_out_set():
    cfg = AuditConfigV18(
        **_base_kwargs(eval_mode=EvalMode.CERTIFICATION, dtype=Dtype.FLOAT64, held_out_seeds=(0,))
    )
    with pytest.raises(ConfigValidationError, match="held_out_seeds"):
        cfg.validate()


def test_certification_mode_passes_with_full_discipline():
    cfg = AuditConfigV18(
        **_base_kwargs(eval_mode=EvalMode.CERTIFICATION, dtype=Dtype.FLOAT64, held_out_seeds=(99,))
    )
    cfg.validate()  # should not raise
