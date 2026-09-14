"""Exact rational certificates for the free-chain Gram SDP (research/pmt_program)."""
from __future__ import annotations

import copy
import glob
import importlib.util
import json
from fractions import Fraction
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CERT_DIR = ROOT / "research" / "pmt_program" / "certificates"


def _verifier():
    spec = importlib.util.spec_from_file_location("pmt_verify_certificates", CERT_DIR / "verify_certificates.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CERTS = sorted(glob.glob(str(CERT_DIR / "certificate_chain_k*_eta_*.json")))


def test_certificates_present():
    assert len(CERTS) == 7


@pytest.mark.parametrize("path", CERTS, ids=[Path(p).stem for p in CERTS])
def test_certificate_verifies_exactly(path):
    ok, info = _verifier().verify(path)
    assert ok, info
    k, eta = info["k"], Fraction(info["eta"])
    s = eta * eta
    closed_form = {3: s * (4 - 3 * s), 4: s * (9 - 15 * s + 7 * s * s), 5: s * (4 - 3 * s) * (4 - 8 * s + 5 * s * s)}[k]
    assert Fraction(info["upper_bound_V"]) == closed_form


@pytest.mark.parametrize("mutation", ["lower_bound", "perturb_entry", "wrong_eta"])
def test_certificate_negative_controls(tmp_path, mutation):
    verifier = _verifier()
    data = json.loads((CERT_DIR / "certificate_chain_k4_eta_3_5.json").read_text())
    bad = copy.deepcopy(data)
    if mutation == "lower_bound":
        bad["Z3"][0][0][0] = str(Fraction(bad["Z3"][0][0][0]) - Fraction(1, 10**9))
        bad["certified_value_squared"] = str(Fraction(data["certified_value_squared"]) - Fraction(1, 10**9))
    elif mutation == "perturb_entry":
        x = Fraction(bad["Z3"][2][1][2]) + Fraction(1, 10**3)
        bad["Z3"][2][1][2] = bad["Z3"][2][2][1] = str(x)
    else:
        bad["eta"] = "4/5"
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(bad))
    ok, _ = verifier.verify(str(path))
    assert not ok
