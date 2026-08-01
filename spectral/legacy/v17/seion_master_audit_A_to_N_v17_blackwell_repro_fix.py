#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SEION Master Audit A-to-N v17 Blackwell Repro/Ultra
Cyclic n-ary internal law + projector + multiscale persistence audit, optimized for RTX PRO Blackwell laptops.

Core goal:
    Learn/audit a cyclic n-ary CP law mu: V^arity -> V and a rank-r projector P,
    then certify: projector validity, snapping, rigidity, Beals proxy, closure,
    projected associator/curvature, normalized tensor interscale persistence,
    HOSVD compactness, gauge canonicalization, persistent factorization,
    cyclic symmetry, and GJI-like associator coherence.

Designed for:
    RTX PRO 5000 Blackwell Laptop / Windows CLI, Google Colab GPU, or local PyTorch.

Ultra optimizations:
    - TF32 / high matmul precision on CUDA.
    - Batched closure, associator, cyclic and GJI stochastic losses.
    - CP-einsum reduced tensor extraction without rank^arity Python loops.
    - Cached quick diagnostics from blackwell_fast.
    - Persistent geometric buffers for reproducible resume.
    - Detailed manifest/history/audit/performance/checkpoint logs.
    - Param-group optimizer for tensor-explicit J/M phases.

Author: SEION / Biospinor experimental audit scaffold
"""

from __future__ import annotations

import argparse
import csv
import itertools
import json
import math
import os
import sys
import hashlib
import platform
import subprocess
import shutil
import random
import string
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
import torch
import torch.nn as nn


# ============================================================
# Blackwell / RTX PRO runtime acceleration
# ============================================================
# This script is dominated by many small complex-valued operations and
# audit diagnostics. TF32 does not fix Python overhead, but it helps the
# matrix multiplications that remain in float32 paths on RTX Ada/Blackwell.
if torch.cuda.is_available():
    torch.backends.cuda.matmul.allow_tf32 = True
    torch.backends.cudnn.allow_tf32 = True

try:
    torch.set_float32_matmul_precision("high")
except Exception:
    pass


# ============================================================
# Basic utilities
# ============================================================

def ensure_dir(path: str | Path) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def resolve_dtype(name: str) -> torch.dtype:
    name = str(name).lower().strip()
    if name in {"float32", "fp32"}:
        return torch.float32
    if name in {"float64", "fp64", "double"}:
        return torch.float64
    raise ValueError(f"Unsupported dtype: {name}")


def complex_dtype_from_real(rdtype: torch.dtype) -> torch.dtype:
    if rdtype == torch.float32:
        return torch.complex64
    if rdtype == torch.float64:
        return torch.complex128
    raise ValueError(f"Unsupported real dtype: {rdtype}")


def make_complex(re: torch.Tensor, im: torch.Tensor) -> torch.Tensor:
    cdt = complex_dtype_from_real(re.dtype)
    return re.to(cdt) + 1j * im.to(cdt)


def tensor_to_float(x: Any) -> float:
    if isinstance(x, (int, float)):
        return float(x)
    if isinstance(x, np.ndarray):
        return float(np.real(x).item())
    if isinstance(x, torch.Tensor):
        y = x.detach().cpu()
        if y.numel() != 1:
            raise ValueError("tensor_to_float expects a scalar tensor")
        return float(torch.real(y).item())
    return float(x)


def fro_sq(x: torch.Tensor) -> torch.Tensor:
    return torch.real(torch.sum(torch.conj(x) * x))


def fro_norm(x: torch.Tensor) -> torch.Tensor:
    return torch.sqrt(fro_sq(x) + 1e-30)


def safe_div(num: torch.Tensor, den: torch.Tensor, eps: float = 1e-12) -> torch.Tensor:
    return num / (den + eps)


def commutator(a: torch.Tensor, b: torch.Tensor) -> torch.Tensor:
    return a @ b - b @ a


def identity(n: int, *, device: str, dtype: torch.dtype) -> torch.Tensor:
    return torch.eye(n, device=device, dtype=dtype)


def orthonormalize_columns(u: torch.Tensor) -> torch.Tensor:
    q, _ = torch.linalg.qr(u, mode="reduced")
    return q


def projector_from_u(u: torch.Tensor) -> torch.Tensor:
    return u @ torch.conj(u).T


def hermitian_random(n: int, *, device: str, rdtype: torch.dtype, scale: float = 1.0) -> torch.Tensor:
    cdt = complex_dtype_from_real(rdtype)
    a = torch.randn(n, n, device=device, dtype=rdtype) * scale
    b = torch.randn(n, n, device=device, dtype=rdtype) * scale
    z = a.to(cdt) + 1j * b.to(cdt)
    return 0.5 * (z + torch.conj(z).T)


def make_shift_operator(n: int, *, device: str, dtype: torch.dtype) -> torch.Tensor:
    s = torch.zeros((n, n), dtype=dtype, device=device)
    for i in range(n - 1):
        s[i, i + 1] = 1.0
    return s


def random_complex_unit(r: int, device: str, rdtype: torch.dtype) -> torch.Tensor:
    cdt = complex_dtype_from_real(rdtype)
    a = torch.randn(r, device=device, dtype=rdtype)
    b = torch.randn(r, device=device, dtype=rdtype)
    z = a.to(cdt) + 1j * b.to(cdt)
    return z / (torch.linalg.norm(z) + 1e-30)


def random_complex_unit_batch(r: int, batch: int, device: str, rdtype: torch.dtype) -> torch.Tensor:
    """Return a matrix of shape (r, batch) with unit-norm complex columns."""
    cdt = complex_dtype_from_real(rdtype)
    a = torch.randn(r, batch, device=device, dtype=rdtype)
    b = torch.randn(r, batch, device=device, dtype=rdtype)
    z = a.to(cdt) + 1j * b.to(cdt)
    return z / (torch.linalg.norm(z, dim=0, keepdim=True) + 1e-30)


def flatten_dict(d: Dict[str, Any], prefix: str = "") -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for k, v in d.items():
        kk = f"{prefix}{k}" if prefix else str(k)
        if isinstance(v, dict):
            out.update(flatten_dict(v, kk + "__"))
        elif isinstance(v, (list, tuple)):
            out[kk] = json.dumps(v, ensure_ascii=False)
        else:
            out[kk] = v
    return out


def safe_json_dump(path: Path, obj: Any) -> None:
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")



def sha256_file(path: str | Path, chunk_size: int = 1 << 20) -> str:
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            while True:
                b = f.read(chunk_size)
                if not b:
                    break
                h.update(b)
        return h.hexdigest()
    except Exception:
        return "unavailable"


def run_command_capture(cmd: Sequence[str], timeout: float = 3.0) -> str:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        txt = (r.stdout or r.stderr or "").strip()
        return txt[:20000]
    except Exception as e:
        return f"unavailable: {type(e).__name__}: {e}"


def get_env_manifest(cfg: Optional["AuditConfig"] = None) -> Dict[str, Any]:
    gpu_name = "CPU"
    cuda_available = bool(torch.cuda.is_available())
    if cuda_available:
        try:
            gpu_name = torch.cuda.get_device_name(0)
        except Exception:
            gpu_name = "CUDA device"
    return {
        "python_executable": sys.executable,
        "python_version": sys.version,
        "platform": platform.platform(),
        "processor": platform.processor(),
        "torch_version": torch.__version__,
        "torch_cuda_version": torch.version.cuda,
        "cuda_available": cuda_available,
        "cuda_device_count": torch.cuda.device_count() if cuda_available else 0,
        "gpu_name_0": gpu_name,
        "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES", ""),
        "nvidia_smi": run_command_capture(["nvidia-smi", "--query-gpu=name,driver_version,memory.total,power.limit", "--format=csv,noheader"], timeout=3.0) if shutil.which("nvidia-smi") else "nvidia-smi not found",
        "cwd": os.getcwd(),
        "argv": sys.argv,
        "config": asdict(cfg) if cfg is not None else None,
    }


def get_rng_state_package() -> Dict[str, Any]:
    return {
        "torch": torch.get_rng_state(),
        "cuda": torch.cuda.get_rng_state_all() if torch.cuda.is_available() else None,
        "numpy": np.random.get_state(),
        "python": random.getstate(),
    }


def restore_rng_state_package(pkg: Optional[Dict[str, Any]]) -> None:
    if not isinstance(pkg, dict):
        return
    try:
        if pkg.get("torch") is not None:
            torch.set_rng_state(pkg["torch"])
        if torch.cuda.is_available() and pkg.get("cuda") is not None:
            torch.cuda.set_rng_state_all(pkg["cuda"])
        if pkg.get("numpy") is not None:
            np.random.set_state(pkg["numpy"])
        if pkg.get("python") is not None:
            random.setstate(pkg["python"])
    except Exception as e:
        print(f"[WARN] Failed to restore RNG state: {e}", flush=True)


def get_perf_snapshot() -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    if torch.cuda.is_available():
        try:
            out.update({
                "gpu_mem_alloc_gb": float(torch.cuda.memory_allocated() / 1024**3),
                "gpu_mem_reserved_gb": float(torch.cuda.memory_reserved() / 1024**3),
                "gpu_mem_max_alloc_gb": float(torch.cuda.max_memory_allocated() / 1024**3),
                "gpu_name": torch.cuda.get_device_name(0),
            })
        except Exception:
            pass
    try:
        import psutil  # type: ignore
        proc = psutil.Process(os.getpid())
        out.update({
            "cpu_rss_gb": float(proc.memory_info().rss / 1024**3),
            "cpu_percent": float(psutil.cpu_percent(interval=None)),
            "ram_percent": float(psutil.virtual_memory().percent),
        })
    except Exception:
        pass
    # Optional lightweight nvidia-smi telemetry. It is intentionally short and non-fatal.
    if shutil.which("nvidia-smi"):
        try:
            q = run_command_capture([
                "nvidia-smi",
                "--query-gpu=utilization.gpu,temperature.gpu,power.draw,memory.used,memory.total,clocks.sm,clocks.mem",
                "--format=csv,noheader,nounits",
            ], timeout=1.5)
            first = q.splitlines()[0] if q else ""
            vals = [v.strip() for v in first.split(",")]
            if len(vals) >= 7:
                out.update({
                    "nvsmi_gpu_util_pct": float(vals[0]),
                    "nvsmi_temp_c": float(vals[1]),
                    "nvsmi_power_w": float(vals[2]),
                    "nvsmi_mem_used_mb": float(vals[3]),
                    "nvsmi_mem_total_mb": float(vals[4]),
                    "nvsmi_sm_clock_mhz": float(vals[5]),
                    "nvsmi_mem_clock_mhz": float(vals[6]),
                })
        except Exception:
            pass
    return out


def loss_weights_from_cfg(cfg: "AuditConfig") -> Dict[str, float]:
    return {
        "loss_projector": cfg.lambda_projector,
        "loss_sub": cfg.lambda_sub,
        "loss_leak": cfg.lambda_leak,
        "loss_comm_raw": cfg.lambda_comm,
        "loss_cdc": cfg.lambda_cdc,
        "loss_norm": cfg.lambda_norm,
        "loss_closure": cfg.lambda_closure,
        "loss_assoc_proj": cfg.lambda_assoc_proj,
        "loss_assoc_raw": cfg.lambda_assoc_raw,
        "loss_hodge": cfg.lambda_hodge,
        "loss_inter_sub_rel": cfg.lambda_inter_sub,
        "loss_inter_proj": cfg.lambda_inter_proj,
        "loss_tensor_j": cfg.lambda_tensor_j,
        "loss_cyclic": cfg.lambda_cyclic,
        "loss_gji": cfg.lambda_gji,
        "loss_reg": cfg.lambda_reg,
    }


def weighted_loss_report(losses_float: Dict[str, float], cfg: "AuditConfig") -> Dict[str, float]:
    weights = loss_weights_from_cfg(cfg)
    out: Dict[str, float] = {}
    for k, w in weights.items():
        if k in losses_float:
            out[f"weighted_{k}"] = float(w) * float(losses_float[k])
    if out:
        top = sorted(out.items(), key=lambda kv: abs(kv[1]), reverse=True)[:5]
        out["weighted_top_terms_json"] = json.dumps(top)
    return out

def top_abs_entries(vec: torch.Tensor, k: int = 8) -> List[Dict[str, float]]:
    v = vec.detach().cpu().reshape(-1)
    k = min(k, v.numel())
    idx = torch.topk(torch.abs(v), k=k).indices.tolist()
    out: List[Dict[str, float]] = []
    for i in idx:
        z = v[i]
        out.append({
            "index": int(i),
            "abs": float(torch.abs(z).item()),
            "real": float(torch.real(z).item()),
            "imag": float(torch.imag(z).item()) if torch.is_complex(z) else 0.0,
        })
    return out


# ============================================================
# Gauge and tensor utilities
# ============================================================

def _einsum_symbols_needed(k: int) -> List[str]:
    base = list(string.ascii_lowercase + string.ascii_uppercase)
    if k > len(base):
        raise ValueError(f"Not enough einsum symbols for k={k}")
    return base[:k]


def build_einsum_reduce_out(ndim: int) -> str:
    """
    Output-mode gauge action:
        X[a, i1, ..., im] = sum_b conj(Q).T[a,b] T[b, i1, ..., im]
    """
    if ndim < 2:
        raise ValueError("Reduced tensor must have ndim >= 2")
    syms = _einsum_symbols_needed(ndim + 1)
    a = syms[0]
    b = syms[1]
    rest = syms[2:2 + (ndim - 1)]
    q_sub = a + b
    t_sub = b + "".join(rest)
    out_sub = a + "".join(rest)
    return f"{q_sub},{t_sub}->{out_sub}"


def build_einsum_apply_in(ndim: int, mode: int) -> str:
    """
    Input-mode gauge action:
        Y[..., new, ...] = sum_old X[..., old, ...] Q[old,new]
    mode is tensor mode index, with 1 <= mode < ndim.
    """
    if ndim < 2:
        raise ValueError("Reduced tensor must have ndim >= 2")
    if not (1 <= mode < ndim):
        raise ValueError(f"mode must satisfy 1 <= mode < ndim, got mode={mode}, ndim={ndim}")

    syms = _einsum_symbols_needed(ndim + 1)
    out_idx = syms[0]
    inds = syms[1:1 + (ndim - 1)]
    old = inds[mode - 1]
    new = syms[ndim]

    tensor_sub = out_idx + "".join(inds)
    q_sub = old + new

    out_inds = inds.copy()
    out_inds[mode - 1] = new
    out_sub = out_idx + "".join(out_inds)

    return f"{tensor_sub},{q_sub}->{out_sub}"


def tensor_slice_gram(T: torch.Tensor) -> torch.Tensor:
    r = T.shape[0]
    S = T.reshape(r, -1)
    G = S @ torch.conj(S).T
    return 0.5 * (G + torch.conj(G).T)


def canonical_gauge_from_tensor(T: torch.Tensor, eps: float = 1e-10) -> Tuple[torch.Tensor, torch.Tensor]:
    G = tensor_slice_gram(T)
    evals, evecs = torch.linalg.eigh(G)
    idx = torch.argsort(evals, descending=True)
    evals = evals[idx]
    Q = evecs[:, idx]

    cols = []
    for j in range(Q.shape[1]):
        col = Q[:, j]
        k = int(torch.argmax(torch.abs(col)).item())
        z = col[k]
        if torch.abs(z) > eps:
            phase = torch.angle(z)
            col = col * torch.exp(-1j * phase)
            if torch.real(col[k]) < 0:
                col = -col
        cols.append(col)

    return torch.stack(cols, dim=1), evals


def apply_gauge_to_reduced_tensor(T: torch.Tensor, Q: torch.Tensor) -> torch.Tensor:
    """
    Applies canonical unitary gauge to reduced tensor T[out,in1,...,inarity].
    This version avoids duplicate einsum output symbols.
    """
    if T.ndim < 2:
        raise ValueError("Reduced tensor must have ndim >= 2")
    r = T.shape[0]
    if any(s != r for s in T.shape):
        raise ValueError(f"Reduced tensor must be cubic in all modes, got shape={tuple(T.shape)}")
    if Q.shape != (r, r):
        raise ValueError(f"Q must be shape {(r, r)}, got {tuple(Q.shape)}")

    X = torch.einsum(build_einsum_reduce_out(T.ndim), torch.conj(Q).T, T)
    for mode in range(1, T.ndim):
        X = torch.einsum(build_einsum_apply_in(T.ndim, mode), X, Q)
    return X


def normalize_tensor(T: torch.Tensor) -> torch.Tensor:
    return T / (fro_norm(T) + 1e-30)


def mode_unfold_np(T: np.ndarray, mode: int) -> np.ndarray:
    axes = [mode] + [i for i in range(T.ndim) if i != mode]
    X = np.transpose(T, axes=axes)
    return X.reshape(T.shape[mode], -1)


def hosvd_mode_energy(X: np.ndarray, energy_threshold: float = 0.99) -> Dict[str, Any]:
    s = np.linalg.svd(X, compute_uv=False, full_matrices=False)
    if s.size == 0:
        return {"singular_values": [], "energy_cum": [], "rank_threshold": 0}
    e = s ** 2
    e = e / max(float(np.sum(e)), 1e-30)
    c = np.cumsum(e)
    rank_thr = int(np.searchsorted(c, energy_threshold, side="left") + 1)
    return {
        "singular_values": s.tolist(),
        "energy_cum": c.tolist(),
        "rank_threshold": rank_thr,
    }


def hosvd_signature(T: np.ndarray, energy_threshold: float) -> Dict[str, Any]:
    sig: Dict[str, Any] = {}
    for mode in range(T.ndim):
        X = mode_unfold_np(T, mode)
        s = np.linalg.svd(X, compute_uv=False, full_matrices=False)
        e = s ** 2
        e = e / max(float(np.sum(e)), 1e-30)
        c = np.cumsum(e)
        r = int(np.searchsorted(c, energy_threshold, side="left") + 1)
        sig[f"mode_{mode}"] = {"singular_values": s.tolist(), "rank_thr": r}
    return sig


def compare_hosvd_signatures(sig_a: Dict[str, Any], sig_b: Dict[str, Any]) -> float:
    vals: List[float] = []
    for k in sig_a.keys():
        if k not in sig_b:
            continue
        sa = np.array(sig_a[k]["singular_values"], dtype=np.float64)
        sb = np.array(sig_b[k]["singular_values"], dtype=np.float64)
        m = min(len(sa), len(sb))
        if m == 0:
            continue
        # Normalize singular spectra before comparing scale-free shapes.
        sa = sa[:m] / max(np.linalg.norm(sa[:m]), 1e-30)
        sb = sb[:m] / max(np.linalg.norm(sb[:m]), 1e-30)
        vals.append(float(np.linalg.norm(sa - sb)))
    return float(np.mean(vals)) if vals else float("inf")


def corrected_gap_metrics(eig_real: np.ndarray, threshold: float, tol_zero_one: float = 1e-5) -> Dict[str, Any]:
    eig_real = np.sort(np.array(eig_real, dtype=np.float64))
    below = eig_real[eig_real < threshold]
    above = eig_real[eig_real >= threshold]

    eig_min = float(np.min(eig_real)) if eig_real.size else float("nan")
    eig_max = float(np.max(eig_real)) if eig_real.size else float("nan")
    gap_to_half = float(np.min(np.abs(eig_real - threshold))) if eig_real.size else float("nan")

    cluster_0_max = float(np.max(below)) if below.size else float("nan")
    cluster_1_min = float(np.min(above)) if above.size else float("nan")
    intercluster_gap = float(cluster_1_min - cluster_0_max) if below.size and above.size else float("nan")

    cluster_0_width = float(np.max(np.abs(below))) if below.size else 0.0
    cluster_1_width = float(np.max(np.abs(above - 1.0))) if above.size else 0.0

    near_zero = int(np.sum(np.abs(eig_real) <= tol_zero_one))
    near_one = int(np.sum(np.abs(eig_real - 1.0) <= tol_zero_one))
    away = int(eig_real.size - near_zero - near_one)

    return {
        "eig_min": eig_min,
        "eig_max": eig_max,
        "gap_to_half": gap_to_half,
        "cluster_below_half": int(below.size),
        "cluster_above_equal_half": int(above.size),
        "cluster_0_max": cluster_0_max,
        "cluster_1_min": cluster_1_min,
        "intercluster_gap": intercluster_gap,
        "cluster_0_width_from_0": cluster_0_width,
        "cluster_1_width_from_1": cluster_1_width,
        "count_near_0": near_zero,
        "count_near_1": near_one,
        "count_away_from_{0,1}": away,
    }


# ============================================================
# Config
# ============================================================

@dataclass
class AuditConfig:
    outdir: str = "runs/master_audit_A_to_N_v17_colab"
    seed: int = 0
    device: str = "cuda"
    dtype: str = "float32"
    run_mode: str = "smoke"              # smoke | closure | interscale | certify
    eval_mode: str = "screening"         # screening | certification

    n: int = 32
    n_hi: int = 64
    rank: int = 8
    arity: int = 3
    cp_rank: int = 8
    hi_cp_rank: int = 8

    steps: int = 80
    lr: float = 4e-4
    print_every: int = 1
    save_every: int = 10
    full_audit_every: int = 10
    # Blackwell optimization: expensive quick diagnostics are cached and
    # recomputed every N steps instead of every step. Set to 1 for original behavior.
    quick_every: int = 5
    # Ultra optimization: reduce CPU<->GPU synchronization and disk logging frequency.
    log_every: int = 5
    diag_every: int = 5
    grad_check_every: int = 5
    time_budget_minutes: float = 0.0

    assoc_samples: int = 3
    hodge_samples: int = 2
    hodge_every: int = 4
    nary_num_trials: int = 8
    tensor_j_every: int = 4

    beals_f_count: int = 4
    beals_x_count: int = 2
    beals_max_order: int = 2
    top_comm_singular_vectors: int = 5

    lambda_projector: float = 1.0
    lambda_sub: float = 5.0
    lambda_leak: float = 4.0
    lambda_comm: float = 0.1
    lambda_cdc: float = 1.0
    lambda_norm: float = 1.0
    lambda_closure: float = 2.0
    lambda_assoc_proj: float = 1.5
    lambda_assoc_raw: float = 0.02
    lambda_hodge: float = 0.005
    lambda_inter_sub: float = 1.0
    lambda_inter_proj: float = 0.5
    lambda_tensor_j: float = 0.10
    lambda_cyclic: float = 5.0
    lambda_gji: float = 2.0
    lambda_reg: float = 1e-8

    snap_threshold: float = 0.5
    gauge_fix_mode: str = "gram"         # gram | none
    gauge_eps: float = 1e-10
    hi_law_mode: str = "explicit"        # explicit | lifted
    use_product_hi: bool = True
    initialize_hi_from_low: bool = True
    freeze_hi_until_frac: float = 0.35

    use_phi_in_normal: bool = True
    use_mix_in_normal: bool = True
    normalize_phi_for_normal: bool = True
    clean_interscale_target: bool = True
    use_selector: bool = True
    selector_scale: float = 1.0

    pass_thresh_B_unexplained_rel: float = 1e-2
    pass_thresh_B_norm_unexplained_rel: float = 1e-2
    pass_thresh_B_coherence: float = 0.75
    strong_pass_thresh_B_unexplained_rel: float = 1e-3
    strong_pass_thresh_B_norm_unexplained_rel: float = 1e-3
    strong_pass_thresh_B_coherence: float = 0.90

    pass_thresh_E_proj_rel: float = 5e-2
    pass_thresh_E_proc_rel: float = 5e-2
    pass_thresh_G_closure_rel: float = 1e-2
    pass_thresh_H_assoc_rel: float = 1e-2
    pass_thresh_J_tensor_rel: float = 5e-2
    pass_thresh_M_persist_rel: float = 0.25
    pass_thresh_L_gauge_rel: float = 1e-8
    pass_thresh_N_cyclic_rel: float = 1e-6
    pass_thresh_N_gji_rel: float = 5e-2
    hosvd_energy_threshold: float = 0.99

    resume: bool = False
    resume_path: Optional[str] = None
    strict_resume: bool = False
    restore_rng: bool = False
    resume_optimizer: bool = True

    # Repro / logging / performance extras
    script_path: str = __file__
    manifest_filename: str = "manifest.json"
    profile_every: int = 25
    stall_factor: float = 20.0

    # Tensor J/M training modes
    tensor_j_loss_mode: str = "canonical"      # raw | canonical | hybrid
    use_param_groups: bool = False
    lr_low_u_mult: float = 1.0
    lr_low_product_mult: float = 1.0
    lr_hi_u_mult: float = 1.0
    lr_hi_product_mult: float = 1.0
    lr_mix_mult: float = 1.0


def thresholds_for_mode(cfg: AuditConfig) -> Dict[str, float]:
    if cfg.eval_mode == "screening":
        return {
            "A_tol": 1e-5,
            "B_comm_tol": cfg.pass_thresh_B_unexplained_rel,
            "B_norm_tol": 5e-2,
            "B_coh_tol": 0.70,
            "D_tol": 1e-5,
            "E_proj_tol": max(cfg.pass_thresh_E_proj_rel, 0.25),
            "E_proc_tol": 1e-3,
            "F_rank_tol": 1e-4,
            "G_closure_tol": max(cfg.pass_thresh_G_closure_rel, 5e-2),
            "H_assoc_tol": max(cfg.pass_thresh_H_assoc_rel, 5e-2),
            "J_tensor_tol": max(cfg.pass_thresh_J_tensor_rel, 2.5e-1),
            "L_gauge_tol": max(cfg.pass_thresh_L_gauge_rel, 1e-6),
            "M_persist_tol": max(cfg.pass_thresh_M_persist_rel, 2.5e-1),
            "N_cyclic_tol": max(cfg.pass_thresh_N_cyclic_rel, 1e-5),
            "N_gji_tol": max(cfg.pass_thresh_N_gji_rel, 1e-1),
        }
    return {
        "A_tol": 1e-10,
        "B_comm_tol": cfg.pass_thresh_B_unexplained_rel,
        "B_norm_tol": cfg.pass_thresh_B_norm_unexplained_rel,
        "B_coh_tol": cfg.pass_thresh_B_coherence,
        "D_tol": 1e-10,
        "E_proj_tol": cfg.pass_thresh_E_proj_rel,
        "E_proc_tol": cfg.pass_thresh_E_proc_rel,
        "F_rank_tol": 1e-6,
        "G_closure_tol": cfg.pass_thresh_G_closure_rel,
        "H_assoc_tol": cfg.pass_thresh_H_assoc_rel,
        "J_tensor_tol": cfg.pass_thresh_J_tensor_rel,
        "L_gauge_tol": cfg.pass_thresh_L_gauge_rel,
        "M_persist_tol": cfg.pass_thresh_M_persist_rel,
        "N_cyclic_tol": cfg.pass_thresh_N_cyclic_rel,
        "N_gji_tol": cfg.pass_thresh_N_gji_rel,
    }


# ============================================================
# Cyclic CP n-ary law
# ============================================================

class CyclicCPProduct(nn.Module):
    """
    CP n-ary law with explicit cyclic symmetrization.

    mu(x1,...,xn) = average over cyclic rotations of CP_raw(rotation).
    Therefore cyclic symmetry is structurally enforced up to floating-point noise.
    """

    def __init__(self, n: int, arity: int, cp_rank: int, *, device: str, rdtype: torch.dtype):
        super().__init__()
        self.n = int(n)
        self.arity = int(arity)
        self.cp_rank = int(cp_rank)
        self.device = device
        self.rdtype = rdtype
        self.cdtype = complex_dtype_from_real(rdtype)

        self.out_re = nn.Parameter(torch.randn(n, cp_rank, device=device, dtype=rdtype) / math.sqrt(max(n, 1)))
        self.out_im = nn.Parameter(torch.randn(n, cp_rank, device=device, dtype=rdtype) / math.sqrt(max(n, 1)))

        self.in_re = nn.ParameterList([
            nn.Parameter(torch.randn(n, cp_rank, device=device, dtype=rdtype) / math.sqrt(max(n, 1)))
            for _ in range(arity)
        ])
        self.in_im = nn.ParameterList([
            nn.Parameter(torch.randn(n, cp_rank, device=device, dtype=rdtype) / math.sqrt(max(n, 1)))
            for _ in range(arity)
        ])

        self.log_lam = nn.Parameter(torch.zeros(cp_rank, device=device, dtype=rdtype))

    def out(self) -> torch.Tensor:
        return make_complex(self.out_re, self.out_im)

    def factor(self, j: int) -> torch.Tensor:
        return make_complex(self.in_re[j], self.in_im[j])

    def lam(self) -> torch.Tensor:
        return torch.exp(self.log_lam).to(self.cdtype)

    def cp_raw(self, xs: Sequence[torch.Tensor]) -> torch.Tensor:
        if len(xs) != self.arity:
            raise ValueError(f"Expected arity={self.arity}, got {len(xs)}")
        for x in xs:
            if x.shape[0] != self.n:
                raise ValueError(f"Ambient mismatch: product n={self.n}, got vector size {x.shape[0]}")
        coeff = self.lam()
        for j, x in enumerate(xs):
            coeff = coeff * (torch.conj(self.factor(j)).T @ x)
        return self.out() @ coeff

    def forward(self, *xs: torch.Tensor) -> torch.Tensor:
        if len(xs) != self.arity:
            raise ValueError(f"Expected arity={self.arity}, got {len(xs)}")
        xlist = list(xs)
        acc = torch.zeros(self.n, dtype=self.cdtype, device=self.device)
        for shift in range(self.arity):
            rotated = xlist[shift:] + xlist[:shift]
            acc = acc + self.cp_raw(rotated)
        return acc / float(self.arity)

    def cp_raw_batch(self, xs: Sequence[torch.Tensor]) -> torch.Tensor:
        """Batched CP raw product. Each x is (n, B); output is (n, B)."""
        if len(xs) != self.arity:
            raise ValueError(f"Expected arity={self.arity}, got {len(xs)}")
        batch = xs[0].shape[1]
        coeff = self.lam()[:, None].expand(self.cp_rank, batch)
        for j, x in enumerate(xs):
            if x.ndim != 2 or x.shape[0] != self.n:
                raise ValueError(f"Expected x shape ({self.n}, B), got {tuple(x.shape)}")
            coeff = coeff * (torch.conj(self.factor(j)).T @ x)
        return self.out() @ coeff

    def forward_batch(self, *xs: torch.Tensor) -> torch.Tensor:
        """Batched cyclic product. Each x is (n, B); output is (n, B)."""
        if len(xs) != self.arity:
            raise ValueError(f"Expected arity={self.arity}, got {len(xs)}")
        xlist = list(xs)
        acc = torch.zeros_like(xlist[0])
        for shift in range(self.arity):
            rotated = xlist[shift:] + xlist[:shift]
            acc = acc + self.cp_raw_batch(rotated)
        return acc / float(self.arity)

    def cyclic_defect_batch(self, xs: Sequence[torch.Tensor]) -> torch.Tensor:
        """Mean cyclic defect over a batch of columns."""
        xlist = list(xs)
        y0 = self.forward_batch(*xlist)
        acc = torch.zeros(y0.shape[1], dtype=self.rdtype, device=self.device)
        ref = torch.real(torch.sum(torch.conj(y0) * y0, dim=0)) + 1e-12
        for shift in range(1, self.arity):
            yr = self.forward_batch(*(xlist[shift:] + xlist[:shift]))
            diff = yr - y0
            acc = acc + torch.real(torch.sum(torch.conj(diff) * diff, dim=0)) / ref
        return torch.mean(acc)

    def cyclic_defect(self, xs: Sequence[torch.Tensor]) -> torch.Tensor:
        xlist = list(xs)
        y0 = self.forward(*xlist)
        acc = torch.tensor(0.0, dtype=self.rdtype, device=self.device)
        for shift in range(1, self.arity):
            yr = self.forward(*(xlist[shift:] + xlist[:shift]))
            acc = acc + fro_sq(yr - y0)
        return acc / (fro_sq(y0) + 1e-12)

    def regularization(self) -> torch.Tensor:
        reg = fro_sq(self.out())
        for j in range(self.arity):
            reg = reg + fro_sq(self.factor(j))
        reg = reg + torch.sum(torch.exp(self.log_lam) ** 2)
        return reg

    @torch.no_grad()
    def copy_low_params_into(self, target: "CyclicCPProduct") -> None:
        m_n = min(self.n, target.n)
        m_r = min(self.cp_rank, target.cp_rank)
        target.out_re[:m_n, :m_r].copy_(self.out_re[:m_n, :m_r])
        target.out_im[:m_n, :m_r].copy_(self.out_im[:m_n, :m_r])
        target.log_lam[:m_r].copy_(self.log_lam[:m_r])
        for j in range(min(self.arity, target.arity)):
            target.in_re[j][:m_n, :m_r].copy_(self.in_re[j][:m_n, :m_r])
            target.in_im[j][:m_n, :m_r].copy_(self.in_im[j][:m_n, :m_r])


# ============================================================
# Model
# ============================================================

class SeionV17Model(nn.Module):
    def __init__(self, cfg: AuditConfig):
        super().__init__()
        self.cfg = cfg
        self.device = cfg.device
        self.rdtype = resolve_dtype(cfg.dtype)
        self.cdtype = complex_dtype_from_real(self.rdtype)

        self.u_re = nn.Parameter(torch.randn(cfg.n, cfg.rank, device=cfg.device, dtype=self.rdtype) / math.sqrt(cfg.n))
        self.u_im = nn.Parameter(torch.randn(cfg.n, cfg.rank, device=cfg.device, dtype=self.rdtype) / math.sqrt(cfg.n))

        self.has_hi = cfg.n_hi > 0
        if self.has_hi:
            self.u_hi_re = nn.Parameter(torch.randn(cfg.n_hi, cfg.rank, device=cfg.device, dtype=self.rdtype) / math.sqrt(cfg.n_hi))
            self.u_hi_im = nn.Parameter(torch.randn(cfg.n_hi, cfg.rank, device=cfg.device, dtype=self.rdtype) / math.sqrt(cfg.n_hi))
        else:
            self.u_hi_re = None
            self.u_hi_im = None

        self.product = CyclicCPProduct(cfg.n, cfg.arity, cfg.cp_rank, device=cfg.device, rdtype=self.rdtype)
        self.product_hi: Optional[CyclicCPProduct] = None
        if self.has_hi and cfg.use_product_hi and cfg.hi_law_mode == "explicit":
            self.product_hi = CyclicCPProduct(cfg.n_hi, cfg.arity, cfg.hi_cp_rank, device=cfg.device, rdtype=self.rdtype)

        # Persistent geometric buffers. These define the actual audited world and
        # must travel with checkpoints; otherwise resume can silently change B/J/M.
        self.register_buffer("delta", hermitian_random(cfg.n, device=cfg.device, rdtype=self.rdtype, scale=1.0), persistent=True)
        if cfg.use_selector:
            self.register_buffer("selector", hermitian_random(cfg.n, device=cfg.device, rdtype=self.rdtype, scale=cfg.selector_scale), persistent=True)
        else:
            self.register_buffer("selector", torch.empty(0, dtype=self.cdtype, device=cfg.device), persistent=True)

        self.register_buffer("d", make_shift_operator(cfg.n, device=cfg.device, dtype=self.cdtype), persistent=True)
        self.register_buffer("d_star", torch.conj(self.d).T, persistent=True)
        self.register_buffer("basis", torch.eye(cfg.n, dtype=self.cdtype, device=cfg.device), persistent=True)

        self.register_buffer("anchor_low", self.anchor_for_dim(cfg.n), persistent=True)
        if self.has_hi:
            self.register_buffer("anchor_hi", self.anchor_for_dim(cfg.n_hi), persistent=True)
            self.register_buffer("t_lo_to_hi", self.build_lift_operator(cfg.n, cfg.n_hi, cfg.device, self.rdtype), persistent=True)
        else:
            self.register_buffer("anchor_hi", torch.empty(0, dtype=self.cdtype, device=cfg.device), persistent=True)
            self.register_buffer("t_lo_to_hi", torch.empty(0, dtype=self.cdtype, device=cfg.device), persistent=True)

        self.w_mix_re = nn.Parameter(0.05 * torch.randn(cfg.rank, cfg.rank, device=cfg.device, dtype=self.rdtype))
        self.w_mix_im = nn.Parameter(0.05 * torch.randn(cfg.rank, cfg.rank, device=cfg.device, dtype=self.rdtype))
        self.mix_gate_logit = nn.Parameter(torch.tensor(0.0, device=cfg.device, dtype=self.rdtype))

        if cfg.initialize_hi_from_low and self.has_hi:
            self.initialize_high_from_low()

    def anchor_for_dim(self, n: int) -> torch.Tensor:
        a = torch.zeros(n, dtype=self.cdtype, device=self.device)
        a[0] = 1.0
        return a

    def build_lift_operator(self, n: int, n_hi: int, device: str, rdtype: torch.dtype) -> torch.Tensor:
        x_lo = torch.linspace(0.0, 1.0, n, device=device, dtype=rdtype)
        x_hi = torch.linspace(0.0, 1.0, n_hi, device=device, dtype=rdtype)
        dist = torch.abs(x_hi[:, None] - x_lo[None, :])
        width = 1.5 / max(n, 1)
        w = torch.exp(-(dist / max(width, 1e-8)) ** 2)
        w = w / torch.clamp(w.sum(dim=1, keepdim=True), min=1e-12)
        return w.to(self.cdtype)

    @torch.no_grad()
    def initialize_high_from_low(self) -> None:
        if not self.has_hi:
            return
        U_lo = orthonormalize_columns(self.u())
        U_hi = orthonormalize_columns(self.t_lo_to_hi @ U_lo)
        self.u_hi_re.copy_(torch.real(U_hi).to(self.rdtype))
        self.u_hi_im.copy_(torch.imag(U_hi).to(self.rdtype))
        if self.product_hi is not None:
            self.product.copy_low_params_into(self.product_hi)

    def u(self) -> torch.Tensor:
        return make_complex(self.u_re, self.u_im)

    def u_hi(self) -> Optional[torch.Tensor]:
        if not self.has_hi:
            return None
        return make_complex(self.u_hi_re, self.u_hi_im)

    def p(self) -> torch.Tensor:
        return projector_from_u(orthonormalize_columns(self.u()))

    def p_hi(self) -> Optional[torch.Tensor]:
        if not self.has_hi:
            return None
        return projector_from_u(orthonormalize_columns(self.u_hi()))

    def w_mix(self) -> torch.Tensor:
        return make_complex(self.w_mix_re, self.w_mix_im)

    def mix_gate(self) -> torch.Tensor:
        return torch.sigmoid(self.mix_gate_logit).to(self.cdtype)

    def product_for(self, ambient: str) -> CyclicCPProduct:
        if ambient == "lo":
            return self.product
        if ambient == "hi":
            if self.product_hi is None:
                raise RuntimeError("product_hi is not initialized.")
            return self.product_hi
        raise ValueError(f"Unknown ambient={ambient}")

    def product_on_ambient(self, ambient: str, *xs: torch.Tensor) -> torch.Tensor:
        if ambient == "lo":
            return self.product(*xs)
        if ambient == "hi":
            if self.cfg.hi_law_mode == "explicit":
                if self.product_hi is None:
                    raise RuntimeError("product_hi not initialized")
                return self.product_hi(*xs)
            if self.cfg.hi_law_mode == "lifted":
                L = self.t_lo_to_hi
                Ldag = torch.conj(L).T
                xs_lo = [Ldag @ x for x in xs]
                return L @ self.product(*xs_lo)
            raise ValueError(f"Unknown hi_law_mode={self.cfg.hi_law_mode}")
        raise ValueError(f"Unknown ambient={ambient}")

    def product_on_ambient_batch(self, ambient: str, *xs: torch.Tensor) -> torch.Tensor:
        """Batched ambient product. Each x is (n, B); output is (n, B)."""
        if ambient == "lo":
            return self.product.forward_batch(*xs)
        if ambient == "hi":
            if self.cfg.hi_law_mode == "explicit":
                if self.product_hi is None:
                    raise RuntimeError("product_hi not initialized")
                return self.product_hi.forward_batch(*xs)
            if self.cfg.hi_law_mode == "lifted":
                L = self.t_lo_to_hi
                Ldag = torch.conj(L).T
                xs_lo = [Ldag @ x for x in xs]
                return L @ self.product.forward_batch(*xs_lo)
            raise ValueError(f"Unknown hi_law_mode={self.cfg.hi_law_mode}")
        raise ValueError(f"Unknown ambient={ambient}")

    def anchored_product(self, x: torch.Tensor, y: torch.Tensor, ambient: str = "lo") -> torch.Tensor:
        if self.cfg.arity < 3:
            raise ValueError("anchored_product requires arity >= 3")
        anchor = self.anchor_low if ambient == "lo" else self.anchor_hi
        extras = [anchor for _ in range(self.cfg.arity - 2)]
        return self.product_on_ambient(ambient, x, y, *extras)

    def associator(self, x: torch.Tensor, y: torch.Tensor, z: torch.Tensor, ambient: str = "lo") -> torch.Tensor:
        xy = self.anchored_product(x, y, ambient)
        yz = self.anchored_product(y, z, ambient)
        return self.anchored_product(xy, z, ambient) - self.anchored_product(x, yz, ambient)

    def anchored_product_batch(self, x: torch.Tensor, y: torch.Tensor, ambient: str = "lo") -> torch.Tensor:
        if self.cfg.arity < 3:
            raise ValueError("anchored_product_batch requires arity >= 3")
        anchor = self.anchor_low if ambient == "lo" else self.anchor_hi
        batch = x.shape[1]
        extras = [anchor[:, None].expand(anchor.shape[0], batch) for _ in range(self.cfg.arity - 2)]
        return self.product_on_ambient_batch(ambient, x, y, *extras)

    def associator_batch(self, x: torch.Tensor, y: torch.Tensor, z: torch.Tensor, ambient: str = "lo") -> torch.Tensor:
        xy = self.anchored_product_batch(x, y, ambient)
        yz = self.anchored_product_batch(y, z, ambient)
        return self.anchored_product_batch(xy, z, ambient) - self.anchored_product_batch(x, yz, ambient)

    def reduced_connection(self, U: torch.Tensor) -> torch.Tensor:
        return U.conj().T @ self.delta @ U

    def reduced_curvature_matrix(self, U: torch.Tensor) -> torch.Tensor:
        r = U.shape[1]
        cols: List[torch.Tensor] = []
        for j in range(r):
            uj = U[:, j]
            assoc_j = self.associator(uj, self.anchor_low, self.anchor_low, "lo")
            cols.append(U.conj().T @ assoc_j)
        return torch.stack(cols, dim=1)

    def coherent_dynamic_curvature(self, U: torch.Tensor, P: torch.Tensor, K: torch.Tensor, Phi: torch.Tensor) -> torch.Tensor:
        left = U @ Phi @ U.conj().T @ self.delta @ K
        right = K @ self.delta @ U @ Phi.conj().T @ U.conj().T
        return left - right

    def coherent_normal(self, U: torch.Tensor, K: torch.Tensor, Omega: torch.Tensor, Phi: torch.Tensor) -> torch.Tensor:
        r = U.shape[1]
        if self.cfg.normalize_phi_for_normal:
            Phi_eff = Phi / (torch.linalg.norm(Phi) + 1e-30)
        else:
            Phi_eff = Phi

        Omega_eff = Omega / (torch.linalg.norm(Omega) + 1e-30)

        Mix = torch.zeros_like(Phi_eff)
        if self.cfg.use_mix_in_normal:
            W = self.w_mix()
            Mix_raw = W @ (Omega_eff @ Phi_eff + Phi_eff @ Omega_eff)
            Mix = Mix_raw / (torch.linalg.norm(Mix_raw) + 1e-30)

        gate = self.mix_gate()
        cols: List[torch.Tensor] = []

        for j in range(r):
            uj = U[:, j]
            acc = torch.zeros(U.shape[0], dtype=self.cdtype, device=self.device)
            for k in range(r):
                uk = U[:, k]
                acc = acc + Omega[k, j] * self.anchored_product(uk, uj, "lo")
                if self.cfg.use_phi_in_normal:
                    acc = acc + Phi_eff[k, j] * self.associator(uk, uj, self.anchor_low, "lo")
                if self.cfg.use_mix_in_normal:
                    mix_vec = self.anchored_product(self.associator(uk, uj, self.anchor_low, "lo"), self.anchor_low, "lo")
                    acc = acc + gate * Mix[k, j] * mix_vec
            cols.append(K @ acc)

        return torch.stack(cols, dim=1)

    def build_highres_U_target_from_lowres(self, U: torch.Tensor) -> torch.Tensor:
        if not self.has_hi:
            raise ValueError("No high-resolution space")
        return orthonormalize_columns(self.t_lo_to_hi @ U)

    def interscale_losses(self, U: torch.Tensor, P: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        if not self.has_hi:
            z = torch.tensor(0.0, dtype=self.rdtype, device=self.device)
            return z, z, z, z

        U_hi = orthonormalize_columns(self.u_hi())
        P_hi_model = projector_from_u(U_hi)
        U_hi_target = self.build_highres_U_target_from_lowres(U)
        P_hi_target = projector_from_u(U_hi_target)

        if not self.cfg.clean_interscale_target:
            P_hi_target = 0.5 * (P_hi_target + P_hi_model)
            P_hi_target = 0.5 * (P_hi_target + P_hi_target.conj().T)

        proj_rel = fro_norm(P_hi_model - P_hi_target) / (fro_norm(P_hi_target) + 1e-30)
        sub_rel = fro_norm(P_hi_model @ P_hi_target - P_hi_target) / (fro_norm(P_hi_target) + 1e-30)
        return P_hi_model, P_hi_target, sub_rel, proj_rel

    def closure_loss(self, U: torch.Tensor, ambient: str, trials: int) -> torch.Tensor:
        """Batched closure loss. Uses residual y-UU*y, avoiding dense K=I-P construction."""
        trials = max(int(trials), 1)
        r = U.shape[1]
        xs = [U @ random_complex_unit_batch(r, trials, self.device, self.rdtype) for _ in range(self.cfg.arity)]
        y = self.product_on_ambient_batch(ambient, *xs)
        res = y - U @ (torch.conj(U).T @ y)
        return fro_sq(res) / (fro_sq(y) + 1e-12)

    def assoc_projected_loss(self, U: torch.Tensor, ambient: str, trials: int) -> torch.Tensor:
        """Batched projected associator loss. Uses residual A-UU*A to reduce memory traffic."""
        if self.cfg.arity < 3:
            return torch.tensor(0.0, dtype=self.rdtype, device=self.device)
        trials = max(int(trials), 1)
        r = U.shape[1]
        x = U @ random_complex_unit_batch(r, trials, self.device, self.rdtype)
        y = U @ random_complex_unit_batch(r, trials, self.device, self.rdtype)
        z = U @ random_complex_unit_batch(r, trials, self.device, self.rdtype)
        A = self.associator_batch(x, y, z, ambient)
        res = A - U @ (torch.conj(U).T @ A)
        return fro_sq(res) / (fro_sq(A) + 1e-12)

    def assoc_raw_loss(self, trials: int) -> torch.Tensor:
        xs = []
        for _ in range(max(3, self.cfg.assoc_samples)):
            a = torch.randn(self.cfg.n, device=self.device, dtype=self.rdtype)
            b = torch.randn(self.cfg.n, device=self.device, dtype=self.rdtype)
            z = a.to(self.cdtype) + 1j * b.to(self.cdtype)
            xs.append(z / (torch.linalg.norm(z) + 1e-30))
        acc = torch.tensor(0.0, dtype=self.rdtype, device=self.device)
        count = 0
        for i in range(len(xs) - 2):
            acc = acc + fro_sq(self.associator(xs[i], xs[i + 1], xs[i + 2], "lo"))
            count += 1
        return acc / max(count, 1)

    def hodge_compatibility_loss(self, num_pairs: int) -> torch.Tensor:
        n = self.cfg.n
        total = torch.tensor(0.0, dtype=self.rdtype, device=self.device)
        pair_indices = torch.randint(0, n, (max(num_pairs, 1), 2), device=self.device)
        for idx in range(pair_indices.shape[0]):
            i = int(pair_indices[idx, 0].item())
            j = int(pair_indices[idx, 1].item())
            a = self.basis[i]
            b = self.basis[j]
            cols = []
            for k in range(n):
                extras = [self.basis[k]]
                while len(extras) < self.cfg.arity - 2:
                    extras.append(self.anchor_low)
                cols.append(self.product(a, b, *extras))
            tab = torch.stack(cols, dim=1)
            total = total + fro_sq(commutator(self.d, tab)) + fro_sq(commutator(self.d_star, tab))
        return total / pair_indices.shape[0]

    def cyclic_loss(self, U: torch.Tensor, ambient: str, trials: int) -> torch.Tensor:
        trials = max(int(trials), 1)
        r = U.shape[1]
        xs = [U @ random_complex_unit_batch(r, trials, self.device, self.rdtype) for _ in range(self.cfg.arity)]
        y0 = self.product_on_ambient_batch(ambient, *xs)
        ref = torch.real(torch.sum(torch.conj(y0) * y0, dim=0)) + 1e-12
        acc = torch.zeros(trials, dtype=self.rdtype, device=self.device)
        xlist = list(xs)
        for shift in range(1, self.cfg.arity):
            yr = self.product_on_ambient_batch(ambient, *(xlist[shift:] + xlist[:shift]))
            diff = yr - y0
            acc = acc + torch.real(torch.sum(torch.conj(diff) * diff, dim=0)) / ref
        return torch.mean(acc)

    def gji_loss(self, U: torch.Tensor, ambient: str, trials: int) -> torch.Tensor:
        """Batched GJI-like associator coherence loss."""
        if self.cfg.arity < 3:
            return torch.tensor(0.0, dtype=self.rdtype, device=self.device)

        trials = max(int(trials), 1)
        r = U.shape[1]
        x = U @ random_complex_unit_batch(r, trials, self.device, self.rdtype)
        y = U @ random_complex_unit_batch(r, trials, self.device, self.rdtype)
        z = U @ random_complex_unit_batch(r, trials, self.device, self.rdtype)

        A_xyz = self.associator_batch(x, y, z, ambient)
        A_yxz = self.associator_batch(y, x, z, ambient)
        A_yzx = self.associator_batch(y, z, x, ambient)
        A_zyx = self.associator_batch(z, y, x, ambient)
        A_zxy = self.associator_batch(z, x, y, ambient)
        A_xzy = self.associator_batch(x, z, y, ambient)

        J = A_xyz - A_yxz + A_yzx - A_zyx + A_zxy - A_xzy
        ref = (
            fro_sq(A_xyz) + fro_sq(A_yxz) + fro_sq(A_yzx)
            + fro_sq(A_zyx) + fro_sq(A_zxy) + fro_sq(A_xzy)
        )
        return fro_sq(J) / (ref + 1e-12)

    def extract_reduced_tensor(self, U: torch.Tensor, ambient: str) -> torch.Tensor:
        """
        Fast CP/einsum reduced tensor extraction.

        Original v17 loops over rank^(arity+1) entries and calls the product once per
        entry. Since the law is CP, the full reduced tensor can be assembled by one
        einsum per cyclic rotation. This heavily accelerates blocks I/J/K/L/M.
        """
        r = U.shape[1]

        if ambient == "lo":
            prod = self.product
            U_eff = U
        elif ambient == "hi":
            if self.cfg.hi_law_mode == "explicit":
                if self.product_hi is None:
                    raise RuntimeError("product_hi not initialized")
                prod = self.product_hi
                U_eff = U
            elif self.cfg.hi_law_mode == "lifted":
                # <U_hi_out, L product_lo(L* inputs)> = <L* U_hi_out, product_lo(L* inputs)>
                prod = self.product
                U_eff = torch.conj(self.t_lo_to_hi).T @ U
            else:
                raise ValueError(f"Unknown hi_law_mode={self.cfg.hi_law_mode}")
        else:
            raise ValueError(f"Unknown ambient={ambient}")

        if self.cfg.arity > 12:
            raise ValueError("Fast reduced tensor extractor supports arity <= 12 for einsum symbols")

        out_coeff = U_eff.conj().T @ prod.out()          # (r, cp)
        out_coeff = out_coeff * prod.lam()[None, :]      # (r, cp)
        in_coeffs = [prod.factor(j).conj().T @ U_eff for j in range(self.cfg.arity)]  # each (cp, r)

        # Use a dedicated CP symbol and one symbol per input mode.
        in_syms_pool = [c for c in string.ascii_lowercase if c not in {"o", "s"}]
        in_syms = in_syms_pool[:self.cfg.arity]
        out_sub = "o" + "".join(in_syms)
        acc = None
        for shift in range(self.cfg.arity):
            # forward() averages cp_raw(x_shift, ..., x_shift-1).
            # factor j consumes original argument mode (j + shift) % arity.
            subs = ["os"]
            operands: List[torch.Tensor] = [out_coeff]
            for j in range(self.cfg.arity):
                arg_mode = (j + shift) % self.cfg.arity
                subs.append("s" + in_syms[arg_mode])
                operands.append(in_coeffs[j])
            eq = ",".join(subs) + "->" + out_sub
            term = torch.einsum(eq, *operands)
            acc = term if acc is None else acc + term
        return acc / float(self.cfg.arity)

    def canonical_tensor(self, U: torch.Tensor, ambient: str, normalize: bool = False) -> torch.Tensor:
        T = self.extract_reduced_tensor(U, ambient)
        if self.cfg.gauge_fix_mode != "none":
            Q, _ = canonical_gauge_from_tensor(T, self.cfg.gauge_eps)
            T = apply_gauge_to_reduced_tensor(T, Q)
        if normalize:
            T = normalize_tensor(T)
        return T

    def tensor_j_loss(self, U_lo: torch.Tensor, U_hi: torch.Tensor) -> torch.Tensor:
        if U_hi is None:
            return torch.tensor(0.0, dtype=self.rdtype, device=self.device)
        mode = str(getattr(self.cfg, "tensor_j_loss_mode", "canonical")).lower()
        T_lo_raw = normalize_tensor(self.extract_reduced_tensor(U_lo, "lo"))
        T_hi_raw = normalize_tensor(self.extract_reduced_tensor(U_hi, "hi"))
        raw_loss = fro_sq(T_hi_raw - T_lo_raw)
        if mode == "raw":
            return raw_loss
        T_lo_can = self.canonical_tensor(U_lo, "lo", normalize=True)
        T_hi_can = self.canonical_tensor(U_hi, "hi", normalize=True)
        can_loss = fro_sq(T_hi_can - T_lo_can)
        if mode == "hybrid":
            return 0.7 * raw_loss + 0.3 * can_loss
        return can_loss

    def regularization(self) -> torch.Tensor:
        reg = torch.real(torch.sum(torch.conj(self.u()) * self.u()))
        reg = reg + self.product.regularization()
        reg = reg + fro_sq(self.w_mix())
        reg = reg + torch.real(self.mix_gate_logit * self.mix_gate_logit)
        if self.has_hi:
            reg = reg + torch.real(torch.sum(torch.conj(self.u_hi()) * self.u_hi()))
        if self.product_hi is not None:
            reg = reg + self.product_hi.regularization()
        return reg

    def spectral_loss(self, P: torch.Tensor) -> torch.Tensor:
        if self.selector is None or self.selector.numel() == 0:
            return torch.tensor(0.0, dtype=self.rdtype, device=self.device)
        return -torch.real(torch.trace(P @ self.selector))

    def forward_losses(self, step: int, freeze_hi: bool = False) -> Dict[str, torch.Tensor]:
        U = orthonormalize_columns(self.u())
        P = projector_from_u(U)
        K = identity(self.cfg.n, device=self.device, dtype=self.cdtype) - P

        idem = fro_sq(P @ P - P)
        selfadj = fro_sq(P.conj().T - P)
        loss_projector = idem + selfadj

        Omega = self.reduced_connection(U)
        Phi = self.reduced_curvature_matrix(U)
        C_theta = self.coherent_dynamic_curvature(U, P, K, Phi)
        N_theta = self.coherent_normal(U, K, Omega, Phi)

        raw_comm = commutator(self.delta, P)
        E_comm = raw_comm - C_theta
        raw_normal = K @ self.delta @ U
        E_norm = raw_normal - N_theta

        _, _, loss_inter_sub_rel, loss_inter_proj = self.interscale_losses(U, P)

        loss_closure = self.closure_loss(U, "lo", self.cfg.nary_num_trials)
        loss_assoc_proj = self.assoc_projected_loss(U, "lo", self.cfg.nary_num_trials)
        loss_assoc_raw = self.assoc_raw_loss(self.cfg.assoc_samples)

        if step % max(self.cfg.hodge_every, 1) == 0:
            loss_hodge = self.hodge_compatibility_loss(self.cfg.hodge_samples)
        else:
            loss_hodge = torch.tensor(0.0, dtype=self.rdtype, device=self.device)

        loss_tensor_j = torch.tensor(0.0, dtype=self.rdtype, device=self.device)
        if self.has_hi and step % max(self.cfg.tensor_j_every, 1) == 0:
            U_hi = orthonormalize_columns(self.u_hi())
            loss_tensor_j = self.tensor_j_loss(U, U_hi)
            if freeze_hi:
                loss_tensor_j = loss_tensor_j.detach()

        loss_cyclic = self.cyclic_loss(U, "lo", self.cfg.nary_num_trials)
        loss_gji = self.gji_loss(U, "lo", self.cfg.nary_num_trials)

        PHK = P @ self.delta @ K
        KHP = K @ self.delta @ P
        loss_leak = fro_sq(PHK) + fro_sq(KHP)
        loss_sub = fro_sq(raw_normal)
        loss_comm_raw = fro_sq(raw_comm)
        loss_cdc = fro_sq(E_comm)
        loss_norm = fro_sq(E_norm)
        loss_reg = self.regularization()

        loss_total = (
            self.cfg.lambda_projector * loss_projector
            + self.cfg.lambda_sub * loss_sub
            + self.cfg.lambda_leak * loss_leak
            + self.cfg.lambda_comm * loss_comm_raw
            + self.cfg.lambda_cdc * loss_cdc
            + self.cfg.lambda_norm * loss_norm
            + self.cfg.lambda_closure * loss_closure
            + self.cfg.lambda_assoc_proj * loss_assoc_proj
            + self.cfg.lambda_assoc_raw * loss_assoc_raw
            + self.cfg.lambda_hodge * loss_hodge
            + self.cfg.lambda_inter_sub * loss_inter_sub_rel
            + self.cfg.lambda_inter_proj * loss_inter_proj
            + self.cfg.lambda_tensor_j * loss_tensor_j
            + self.cfg.lambda_cyclic * loss_cyclic
            + self.cfg.lambda_gji * loss_gji
            + self.cfg.lambda_reg * loss_reg
        )

        return {
            "loss_total": loss_total,
            "loss_projector": loss_projector,
            "loss_sub": loss_sub,
            "loss_leak": loss_leak,
            "loss_comm_raw": loss_comm_raw,
            "loss_cdc": loss_cdc,
            "loss_norm": loss_norm,
            "loss_inter_sub_rel": loss_inter_sub_rel,
            "loss_inter_proj": loss_inter_proj,
            "loss_closure": loss_closure,
            "loss_assoc_proj": loss_assoc_proj,
            "loss_assoc_raw": loss_assoc_raw,
            "loss_hodge": loss_hodge,
            "loss_tensor_j": loss_tensor_j,
            "loss_cyclic": loss_cyclic,
            "loss_gji": loss_gji,
            "loss_reg": loss_reg,
        }

    @torch.no_grad()
    def diagnostics(self) -> Dict[str, float]:
        U = orthonormalize_columns(self.u())
        P = projector_from_u(U)
        idem = fro_norm(P @ P - P)
        selfadj = fro_norm(P.conj().T - P)
        dyn = fro_norm(commutator(self.delta, P))
        return {
            "delta_idem": tensor_to_float(idem / (fro_norm(P) + 1e-30)),
            "delta_selfadj": tensor_to_float(selfadj / (fro_norm(P) + 1e-30)),
            "delta_dyn": tensor_to_float(dyn / (fro_norm(self.delta) * fro_norm(P) + 1e-30)),
            "rank_eff": tensor_to_float(torch.real(torch.trace(P))),
            "fro_P": tensor_to_float(fro_norm(P)),
            "loss_idem_abs": tensor_to_float(fro_sq(P @ P - P)),
            "loss_selfadj_abs": tensor_to_float(fro_sq(P.conj().T - P)),
        }


# ============================================================
# Audit blocks A-N
# ============================================================

def block_A_projector(model: SeionV17Model, cfg: AuditConfig) -> Dict[str, Any]:
    t = thresholds_for_mode(cfg)
    U = orthonormalize_columns(model.u())
    P = projector_from_u(U)
    idem_rel = tensor_to_float(fro_norm(P @ P - P) / (fro_norm(P) + 1e-30))
    selfadj_rel = tensor_to_float(fro_norm(P.conj().T - P) / (fro_norm(P) + 1e-30))
    out = {
        "shape": list(P.shape),
        "rank_eff_trace": tensor_to_float(torch.real(torch.trace(P))),
        "fro_P": tensor_to_float(fro_norm(P)),
        "idem_rel": idem_rel,
        "selfadj_rel": selfadj_rel,
        "tol_used": t["A_tol"],
    }
    out["status"] = "PASS" if max(idem_rel, selfadj_rel) < t["A_tol"] else "WARN"
    return out


def block_B_commutator(model: SeionV17Model, cfg: AuditConfig) -> Dict[str, Any]:
    t = thresholds_for_mode(cfg)
    U = orthonormalize_columns(model.u())
    P = projector_from_u(U)
    K = identity(cfg.n, device=model.device, dtype=model.cdtype) - P
    Delta = model.delta

    Omega = model.reduced_connection(U)
    Phi = model.reduced_curvature_matrix(U)
    C_theta = model.coherent_dynamic_curvature(U, P, K, Phi)
    N_theta = model.coherent_normal(U, K, Omega, Phi)

    raw_comm = commutator(Delta, P)
    E_comm = raw_comm - C_theta
    raw_normal = K @ Delta @ U
    E_norm = raw_normal - N_theta

    raw_comm_norm = fro_norm(raw_comm)
    unexpl_comm_norm = fro_norm(E_comm)
    raw_normal_norm = fro_norm(raw_normal)
    unexpl_normal_norm = fro_norm(E_norm)

    comm_rel = tensor_to_float(raw_comm_norm / (fro_norm(Delta) * fro_norm(P) + 1e-30))
    comm_unexpl = tensor_to_float(unexpl_comm_norm / (fro_norm(Delta) * fro_norm(P) + 1e-30))
    normal_unexpl = tensor_to_float(unexpl_normal_norm / (fro_norm(Delta @ U) + 1e-30))
    normal_raw_rel = tensor_to_float(raw_normal_norm / (fro_norm(Delta @ U) + 1e-30))
    coherence = float(1.0 - tensor_to_float(unexpl_comm_norm / (raw_comm_norm + 1e-30)))

    svals_raw = torch.linalg.svdvals(raw_comm)
    svals_phi = torch.linalg.svdvals(Phi)
    top_k = min(max(cfg.top_comm_singular_vectors, 1), svals_raw.numel())

    status = "WARN"
    if (
        comm_unexpl < cfg.strong_pass_thresh_B_unexplained_rel
        and normal_unexpl < cfg.strong_pass_thresh_B_norm_unexplained_rel
        and coherence > cfg.strong_pass_thresh_B_coherence
    ):
        status = "PASS_STRONG"
    elif comm_unexpl < t["B_comm_tol"] and normal_unexpl < t["B_norm_tol"] and coherence > t["B_coh_tol"]:
        status = "PASS"
    elif coherence > 0.50:
        status = "WARN_GEOMETRIC"

    fail_reasons = []
    if status not in {"PASS", "PASS_STRONG"}:
        fail_reasons.append(
            f"comm_unexplained_rel={comm_unexpl:.6e}, "
            f"normal_unexplained_rel={normal_unexpl:.6e}, "
            f"coherence_ratio={coherence:.6f}"
        )

    return {
        "comm_abs": tensor_to_float(raw_comm_norm),
        "comm_rel": comm_rel,
        "comm_unexplained_rel": comm_unexpl,
        "normal_raw_rel": normal_raw_rel,
        "normal_unexplained_rel": normal_unexpl,
        "coherence_ratio": coherence,
        "delta_fro": tensor_to_float(fro_norm(Delta)),
        "P_fro": tensor_to_float(fro_norm(P)),
        "phi_fro": tensor_to_float(fro_norm(Phi)),
        "singular_values_top": [float(x) for x in svals_raw[:top_k].detach().cpu().tolist()],
        "phi_singular_values_top": [float(x) for x in svals_phi[:top_k].detach().cpu().tolist()],
        "dynamic_obstruction_score": float(-math.log10(max(comm_unexpl, 1e-16))),
        "tol_comm_used": t["B_comm_tol"],
        "tol_norm_used": t["B_norm_tol"],
        "tol_coh_used": t["B_coh_tol"],
        "fail_reasons": fail_reasons,
        "status": status,
    }


def build_beals_observables(n: int, device: str, rdtype: torch.dtype, f_count: int, x_count: int) -> List[Tuple[str, torch.Tensor]]:
    cdt = complex_dtype_from_real(rdtype)
    xs = torch.linspace(0.0, 2.0 * math.pi, n, device=device, dtype=rdtype)
    ops: List[Tuple[str, torch.Tensor]] = []
    for k in range(1, f_count + 1):
        ops.append((f"f{k-1}", torch.diag(torch.cos(k * xs).to(cdt))))
    for k in range(x_count):
        ops.append((f"X{k}", make_shift_operator(n, device=device, dtype=cdt)))
    return ops


def apply_nested_commutators(P: torch.Tensor, mats: Sequence[torch.Tensor]) -> torch.Tensor:
    out = P
    for m in mats:
        out = commutator(m, out)
    return out


def block_C_beals(model: SeionV17Model, cfg: AuditConfig) -> Dict[str, Any]:
    U = orthonormalize_columns(model.u())
    P = projector_from_u(U)
    ops = build_beals_observables(cfg.n, cfg.device, model.rdtype, cfg.beals_f_count, cfg.beals_x_count)

    entries: List[Dict[str, Any]] = [{"order": 0, "kind": "P", "norm": tensor_to_float(fro_norm(P))}]
    for name, op in ops:
        entries.append({"order": 1, "kind": f"[{name},P]", "norm": tensor_to_float(fro_norm(commutator(op, P)))})

    small_ops = ops[: min(4, len(ops))]
    for order in range(2, max(cfg.beals_max_order, 1) + 1):
        for combo in itertools.product(range(len(small_ops)), repeat=order):
            names = [small_ops[i][0] for i in combo]
            mats = [small_ops[i][1] for i in combo]
            val = apply_nested_commutators(P, mats)
            entries.append({"order": order, "kind": "nested_" + "_".join(names), "norm": tensor_to_float(fro_norm(val))})

    max_norm = max(float(e["norm"]) for e in entries) if entries else 0.0
    return {"entries": entries, "max_norm_overall": max_norm, "status": "PASS" if max_norm < 1e3 else "WARN"}


def block_D_snapping(model: SeionV17Model, cfg: AuditConfig) -> Dict[str, Any]:
    t = thresholds_for_mode(cfg)
    U = orthonormalize_columns(model.u())
    P = projector_from_u(U)
    evals, evecs = torch.linalg.eigh(P)
    q = (evals >= cfg.snap_threshold).to(model.cdtype)
    Q = evecs @ torch.diag(q) @ evecs.conj().T

    dist_rel = tensor_to_float(fro_norm(Q - P) / (fro_norm(P) + 1e-30))
    idem_rel = tensor_to_float(fro_norm(Q @ Q - Q) / (fro_norm(Q) + 1e-30))
    selfadj_rel = tensor_to_float(fro_norm(Q.conj().T - Q) / (fro_norm(Q) + 1e-30))
    comm_rel = tensor_to_float(fro_norm(commutator(model.delta, Q)) / (fro_norm(model.delta) * fro_norm(Q) + 1e-30))
    gap = corrected_gap_metrics(torch.real(evals).detach().cpu().numpy(), cfg.snap_threshold)

    out = {
        "snap_threshold": cfg.snap_threshold,
        "dist_Q_minus_P_rel": dist_rel,
        "Q_idem_rel": idem_rel,
        "Q_selfadj_rel": selfadj_rel,
        "Q_comm_delta_rel": comm_rel,
        "tol_used": t["D_tol"],
        **gap,
    }
    out["status"] = "PASS" if max(dist_rel, idem_rel, selfadj_rel) < t["D_tol"] else "WARN"
    return out


def block_E_interscale(model: SeionV17Model, cfg: AuditConfig) -> Dict[str, Any]:
    t = thresholds_for_mode(cfg)
    if not model.has_hi:
        return {"enabled": False, "status": "N/A"}
    U = orthonormalize_columns(model.u())
    P = projector_from_u(U)
    P_hi_model, P_hi_target, sub_rel, proj_rel = model.interscale_losses(U, P)
    proj = tensor_to_float(proj_rel)
    sub = tensor_to_float(sub_rel)
    return {
        "enabled": True,
        "shape_lo": list(P.shape),
        "shape_hi": list(P_hi_model.shape),
        "lifted_vs_hi_rel": proj,
        "subspace_residual_rel": sub,
        "trace_lo": tensor_to_float(torch.real(torch.trace(P))),
        "trace_hi": tensor_to_float(torch.real(torch.trace(P_hi_model))),
        "tol_proj_used": t["E_proj_tol"],
        "tol_proc_used": t["E_proc_tol"],
        "status": "PASS" if (proj < t["E_proj_tol"] and sub < t["E_proc_tol"]) else "WARN",
    }


def block_F_rigidity(model: SeionV17Model, cfg: AuditConfig, snap: Dict[str, Any]) -> Dict[str, Any]:
    t = thresholds_for_mode(cfg)
    U = orthonormalize_columns(model.u())
    P = projector_from_u(U)
    evals, _ = torch.linalg.eigh(P)
    gap = corrected_gap_metrics(torch.real(evals).detach().cpu().numpy(), cfg.snap_threshold)

    stable_rank = tensor_to_float((fro_norm(P) ** 2) / (torch.linalg.matrix_norm(P, ord=2) ** 2 + 1e-30))
    rank_trace = tensor_to_float(torch.real(torch.trace(P)))
    rank_diff = abs(stable_rank - rank_trace)

    h = model.delta.detach().cpu().numpy().real
    try:
        ev = np.linalg.eigvalsh(h)
        hcond = float((abs(np.max(ev)) + 12.0) / max(abs(np.min(ev)) + 12.0, 1e-30))
    except Exception:
        hcond = float("nan")

    out = {
        **gap,
        "hessian_condition_proxy": hcond,
        "rank_trace": rank_trace,
        "stable_rank_proxy": stable_rank,
        "stable_rank_ranktrace_absdiff": rank_diff,
        "rank_tol_used": t["F_rank_tol"],
    }
    out["status"] = "PASS" if np.isfinite(hcond) and rank_diff < t["F_rank_tol"] and gap["intercluster_gap"] > 0.25 else "WARN"
    return out


def block_G_nary_closure(model: SeionV17Model, cfg: AuditConfig) -> Dict[str, Any]:
    t = thresholds_for_mode(cfg)
    U = orthonormalize_columns(model.u())
    rel = tensor_to_float(model.closure_loss(U, "lo", cfg.nary_num_trials))
    return {
        "enabled": True,
        "arity": cfg.arity,
        "num_trials": cfg.nary_num_trials,
        "closure_rel": rel,
        "tol_used": t["G_closure_tol"],
        "status": "PASS" if rel < t["G_closure_tol"] else "WARN",
    }


def block_H_nary_associator(model: SeionV17Model, cfg: AuditConfig) -> Dict[str, Any]:
    t = thresholds_for_mode(cfg)
    U = orthonormalize_columns(model.u())
    rel = tensor_to_float(model.assoc_projected_loss(U, "lo", cfg.nary_num_trials))
    return {
        "enabled": True,
        "arity": cfg.arity,
        "num_trials": cfg.nary_num_trials,
        "assoc_rel": rel,
        "tol_used": t["H_assoc_tol"],
        "status": "PASS" if rel < t["H_assoc_tol"] else "WARN",
    }


def block_I_reduced_tensor(model: SeionV17Model, cfg: AuditConfig) -> Dict[str, Any]:
    U = orthonormalize_columns(model.u())
    T_lo = model.extract_reduced_tensor(U, "lo")
    out: Dict[str, Any] = {
        "enabled": True,
        "shape_lo": list(T_lo.shape),
        "fro_norm_lo": tensor_to_float(fro_norm(T_lo)),
        "max_abs_entry_lo": float(torch.max(torch.abs(T_lo)).detach().cpu().item()) if T_lo.numel() else 0.0,
        "rank": cfg.rank,
        "arity": cfg.arity,
        "entries_lo": int(np.prod(T_lo.shape)),
        "hi_tensor_available": bool(model.has_hi),
        "status": "PASS",
    }
    if model.has_hi:
        U_hi = orthonormalize_columns(model.u_hi())
        T_hi = model.extract_reduced_tensor(U_hi, "hi")
        out["shape_hi"] = list(T_hi.shape)
        out["fro_norm_hi"] = tensor_to_float(fro_norm(T_hi))
        out["max_abs_entry_hi"] = float(torch.max(torch.abs(T_hi)).detach().cpu().item()) if T_hi.numel() else 0.0
    return out


def block_J_tensor_interscale(model: SeionV17Model, cfg: AuditConfig) -> Dict[str, Any]:
    t = thresholds_for_mode(cfg)
    if not model.has_hi:
        return {"enabled": False, "status": "N/A"}
    U_lo = orthonormalize_columns(model.u())
    U_hi = orthonormalize_columns(model.u_hi())
    T_lo = model.extract_reduced_tensor(U_lo, "lo")
    T_hi = model.extract_reduced_tensor(U_hi, "hi")

    if cfg.gauge_fix_mode != "none":
        Q_lo, _ = canonical_gauge_from_tensor(T_lo, cfg.gauge_eps)
        Q_hi, _ = canonical_gauge_from_tensor(T_hi, cfg.gauge_eps)
        T_lo_can = apply_gauge_to_reduced_tensor(T_lo, Q_lo)
        T_hi_can = apply_gauge_to_reduced_tensor(T_hi, Q_hi)
    else:
        T_lo_can = T_lo
        T_hi_can = T_hi

    T_lo_norm = normalize_tensor(T_lo_can)
    T_hi_norm = normalize_tensor(T_hi_can)
    diff_abs = fro_norm(T_hi_norm - T_lo_norm)
    diff_rel = tensor_to_float(diff_abs)  # already scale-free due normalization

    return {
        "enabled": True,
        "shape_lo": list(T_lo.shape),
        "shape_hi": list(T_hi.shape),
        "fro_norm_lo_can": tensor_to_float(fro_norm(T_lo_can)),
        "fro_norm_hi_can": tensor_to_float(fro_norm(T_hi_can)),
        "tensor_diff_abs": tensor_to_float(diff_abs),
        "tensor_diff_rel": diff_rel,
        "gauge_fix_mode": cfg.gauge_fix_mode,
        "normalized_comparison": True,
        "tol_used": t["J_tensor_tol"],
        "status": "PASS" if diff_rel < t["J_tensor_tol"] else "WARN",
    }


def block_K_hosvd(model: SeionV17Model, cfg: AuditConfig) -> Dict[str, Any]:
    U = orthonormalize_columns(model.u())
    T_lo = model.extract_reduced_tensor(U, "lo").detach().cpu().numpy()
    per_mode: Dict[str, Any] = {}
    ranks: List[int] = []
    for mode in range(T_lo.ndim):
        diag = hosvd_mode_energy(mode_unfold_np(T_lo, mode), cfg.hosvd_energy_threshold)
        diag["energy_threshold"] = cfg.hosvd_energy_threshold
        per_mode[f"mode_{mode}"] = diag
        ranks.append(int(diag["rank_threshold"]))
    max_rank = max(ranks) if ranks else 0
    return {
        "enabled": True,
        "shape_lo": list(T_lo.shape),
        "fro_norm_lo": float(np.linalg.norm(T_lo.ravel())),
        "energy_threshold": cfg.hosvd_energy_threshold,
        "per_mode": per_mode,
        "max_rank_needed": max_rank,
        "ambient_rank": cfg.rank,
        "status": "PASS" if max_rank <= cfg.rank else "WARN",
    }


def block_L_gauge_canonicalization(model: SeionV17Model, cfg: AuditConfig) -> Dict[str, Any]:
    t = thresholds_for_mode(cfg)
    U = orthonormalize_columns(model.u())
    T = model.extract_reduced_tensor(U, "lo")
    if cfg.gauge_fix_mode == "none":
        Q = identity(cfg.rank, device=model.device, dtype=model.cdtype)
        evals = torch.linalg.eigvalsh(tensor_slice_gram(T))
        T_can = T
    else:
        Q, evals = canonical_gauge_from_tensor(T, cfg.gauge_eps)
        T_can = apply_gauge_to_reduced_tensor(T, Q)
    I = identity(Q.shape[0], device=Q.device, dtype=Q.dtype)
    unitary_rel = tensor_to_float(fro_norm(Q.conj().T @ Q - I) / (fro_norm(I) + 1e-30))
    return {
        "enabled": True,
        "gauge_fix_mode": cfg.gauge_fix_mode,
        "shape_lo": list(T.shape),
        "fro_norm_lo": tensor_to_float(fro_norm(T)),
        "fro_norm_lo_can": tensor_to_float(fro_norm(T_can)),
        "gram_eigenvalues_lo": [float(torch.real(x).detach().cpu().item()) for x in evals],
        "gauge_unitarity_rel_lo": unitary_rel,
        "tol_used": t["L_gauge_tol"],
        "status": "PASS" if unitary_rel < t["L_gauge_tol"] else "WARN",
    }


def block_M_persistent_factorization(model: SeionV17Model, cfg: AuditConfig) -> Dict[str, Any]:
    t = thresholds_for_mode(cfg)
    U_lo = orthonormalize_columns(model.u())
    T_lo = model.canonical_tensor(U_lo, "lo", normalize=True)
    sig_lo = hosvd_signature(T_lo.detach().cpu().numpy(), cfg.hosvd_energy_threshold)
    out: Dict[str, Any] = {
        "enabled": True,
        "energy_threshold": cfg.hosvd_energy_threshold,
        "signature_lo": sig_lo,
        "status": "PASS",
    }
    if model.has_hi:
        U_hi = orthonormalize_columns(model.u_hi())
        T_hi = model.canonical_tensor(U_hi, "hi", normalize=True)
        sig_hi = hosvd_signature(T_hi.detach().cpu().numpy(), cfg.hosvd_energy_threshold)
        persist_rel = compare_hosvd_signatures(sig_lo, sig_hi)
        out.update({
            "signature_hi": sig_hi,
            "persist_rel": persist_rel,
            "tol_used": t["M_persist_tol"],
            "normalized_comparison": True,
            "status": "PASS" if persist_rel < t["M_persist_tol"] else "WARN",
        })
    return out


def block_N_cyclic_law(model: SeionV17Model, cfg: AuditConfig) -> Dict[str, Any]:
    t = thresholds_for_mode(cfg)
    U = orthonormalize_columns(model.u())
    cyc = tensor_to_float(model.cyclic_loss(U, "lo", cfg.nary_num_trials))
    gji = tensor_to_float(model.gji_loss(U, "lo", cfg.nary_num_trials))
    return {
        "enabled": True,
        "arity": cfg.arity,
        "num_trials": cfg.nary_num_trials,
        "cyclic_rel": cyc,
        "gji_rel": gji,
        "tol_cyclic_used": t["N_cyclic_tol"],
        "tol_gji_used": t["N_gji_tol"],
        "status": "PASS" if (cyc < t["N_cyclic_tol"] and gji < t["N_gji_tol"]) else "WARN",
    }


# ============================================================
# Logging and scoring
# ============================================================

class JSONLogger:
    def __init__(self, outdir: Path, filename: str):
        self.path = outdir / filename
        if self.path.exists():
            self.path.unlink()

    def write(self, record: Dict[str, Any]) -> None:
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


class CSVLogger:
    def __init__(self, outdir: Path, filename: str):
        self.path = outdir / filename
        if self.path.exists():
            self.path.unlink()
        self.fieldnames: Optional[List[str]] = None

    def write(self, flat: Dict[str, Any]) -> None:
        if self.fieldnames is None:
            self.fieldnames = list(flat.keys())
            with open(self.path, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=self.fieldnames)
                w.writeheader()
                w.writerow(flat)
        else:
            missing = [k for k in flat.keys() if k not in self.fieldnames]
            if missing:
                with open(self.path, "r", newline="", encoding="utf-8") as f:
                    rows = list(csv.DictReader(f))
                self.fieldnames += missing
                with open(self.path, "w", newline="", encoding="utf-8") as f:
                    w = csv.DictWriter(f, fieldnames=self.fieldnames)
                    w.writeheader()
                    for row in rows:
                        w.writerow(row)
                    w.writerow({k: flat.get(k, "") for k in self.fieldnames})
            else:
                with open(self.path, "a", newline="", encoding="utf-8") as f:
                    w = csv.DictWriter(f, fieldnames=self.fieldnames)
                    w.writerow({k: flat.get(k, "") for k in self.fieldnames})


def score_status(st: str) -> float:
    if st in {"PASS", "PASS_STRONG"}:
        return 1.0
    if st == "WARN_GEOMETRIC":
        return 0.75
    if st == "N/A":
        return 1.0
    return 0.5


def compute_master_score(blocks: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    scores = {k: score_status(str(v.get("status", "WARN"))) for k, v in blocks.items()}
    statuses = {k: v.get("status", "UNKNOWN") for k, v in blocks.items()}
    fail: List[str] = []
    for k, v in blocks.items():
        st = str(v.get("status", "UNKNOWN"))
        if st not in {"PASS", "PASS_STRONG", "N/A"}:
            reasons = v.get("fail_reasons", None)
            if isinstance(reasons, list) and reasons:
                for r in reasons:
                    fail.append(f"{k}: {r}")
            else:
                fail.append(f"{k}: status={st}")
    return {
        "master_score": 100.0 * float(np.mean(list(scores.values()))) if scores else 0.0,
        "block_scores_0_to_1": scores,
        "statuses": statuses,
        "fail_reasons": fail,
    }


def grad_health(model: nn.Module) -> Dict[str, Any]:
    has_nan = False
    has_inf = False
    gmax = 0.0
    for p in model.parameters():
        if p.grad is None:
            continue
        g = p.grad.detach()
        has_nan = has_nan or bool(torch.isnan(g).any().item())
        has_inf = has_inf or bool(torch.isinf(g).any().item())
        gmax = max(gmax, float(torch.max(torch.abs(g)).item()))
    return {
        "has_nan_grad": has_nan,
        "has_inf_grad": has_inf,
        "grad_absmax": gmax,
        "exploding_grad_warning": gmax > 1e3,
        "vanishing_grad_warning": gmax < 1e-12,
    }


def phase_name(step: int, cfg: AuditConfig) -> str:
    f = step / max(cfg.steps, 1)
    if f < 0.12:
        return "projector_warmup"
    if f < 0.35:
        return "cyclic_law_lock"
    if f < 0.55:
        return "algebra_closure"
    if f < 0.70:
        return "gji_alignment"
    if f < 0.85:
        return "interscale_persistence"
    if f < 0.95:
        return "dynamic_explanation"
    return "certification_polish"


def lr_scale_for_phase(phase: str) -> float:
    return {
        "projector_warmup": 1.0,
        "cyclic_law_lock": 0.8,
        "algebra_closure": 0.65,
        "gji_alignment": 0.50,
        "interscale_persistence": 0.30,
        "dynamic_explanation": 0.18,
        "certification_polish": 0.06,
    }.get(phase, 0.5)


def configure_run_mode(cfg: AuditConfig) -> AuditConfig:
    """
    Adjust objective emphasis by run_mode.
    Explicit CLI values remain in cfg, but this provides sensible presets.
    """
    if cfg.run_mode == "smoke":
        return cfg
    if cfg.run_mode == "closure":
        cfg.lambda_cyclic = max(cfg.lambda_cyclic, 8.0)
        cfg.lambda_gji = max(cfg.lambda_gji, 4.0)
        cfg.lambda_closure = max(cfg.lambda_closure, 5.0)
        cfg.lambda_assoc_proj = max(cfg.lambda_assoc_proj, 3.0)
        cfg.lambda_cdc = min(cfg.lambda_cdc, 0.5)
        cfg.lambda_norm = min(cfg.lambda_norm, 0.5)
        cfg.lambda_inter_sub = min(cfg.lambda_inter_sub, 0.75)
        cfg.lambda_inter_proj = min(cfg.lambda_inter_proj, 0.35)
        return cfg
    if cfg.run_mode == "interscale":
        cfg.lambda_inter_sub = max(cfg.lambda_inter_sub, 3.0)
        cfg.lambda_inter_proj = max(cfg.lambda_inter_proj, 1.0)
        cfg.lambda_tensor_j = max(cfg.lambda_tensor_j, 0.50)
        cfg.lambda_closure = max(cfg.lambda_closure, 2.0)
        cfg.lambda_assoc_proj = max(cfg.lambda_assoc_proj, 1.5)
        return cfg
    if cfg.run_mode == "tensor_explicit":
        cfg.hi_law_mode = "explicit"
        cfg.use_product_hi = True
        cfg.lambda_tensor_j = max(cfg.lambda_tensor_j, 1.0)
        cfg.lambda_inter_sub = min(cfg.lambda_inter_sub, 0.75)
        cfg.lambda_inter_proj = min(cfg.lambda_inter_proj, 0.35)
        cfg.lambda_sub = min(cfg.lambda_sub, 0.25)
        cfg.lambda_leak = min(cfg.lambda_leak, 0.25)
        cfg.lambda_comm = min(cfg.lambda_comm, 0.005)
        cfg.lambda_cdc = min(cfg.lambda_cdc, 0.005)
        cfg.lambda_norm = min(cfg.lambda_norm, 0.005)
        cfg.lambda_closure = max(cfg.lambda_closure, 6.0)
        cfg.lambda_assoc_proj = max(cfg.lambda_assoc_proj, 8.0)
        cfg.lambda_cyclic = max(cfg.lambda_cyclic, 8.0)
        cfg.lambda_gji = max(cfg.lambda_gji, 4.0)
        if not cfg.use_param_groups:
            cfg.use_param_groups = True
            cfg.lr_low_u_mult = 0.05
            cfg.lr_low_product_mult = 0.05
            cfg.lr_hi_u_mult = 1.0
            cfg.lr_hi_product_mult = 1.0
            cfg.lr_mix_mult = 0.1
        return cfg
    if cfg.run_mode == "certify":
        cfg.lambda_cyclic = max(cfg.lambda_cyclic, 8.0)
        cfg.lambda_gji = max(cfg.lambda_gji, 5.0)
        cfg.lambda_closure = max(cfg.lambda_closure, 5.0)
        cfg.lambda_assoc_proj = max(cfg.lambda_assoc_proj, 3.0)
        cfg.lambda_inter_sub = max(cfg.lambda_inter_sub, 2.0)
        cfg.lambda_inter_proj = max(cfg.lambda_inter_proj, 1.0)
        cfg.lambda_tensor_j = max(cfg.lambda_tensor_j, 0.50)
        cfg.lambda_cdc = max(cfg.lambda_cdc, 2.0)
        cfg.lambda_norm = max(cfg.lambda_norm, 2.0)
        return cfg
    return cfg


def run_full_audit(model: SeionV17Model, cfg: AuditConfig) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Any]]:
    blocks: Dict[str, Dict[str, Any]] = {
        "A_projector": block_A_projector(model, cfg),
        "B_commutator": block_B_commutator(model, cfg),
        "C_beals": block_C_beals(model, cfg),
        "D_snapping": block_D_snapping(model, cfg),
        "E_interscale": block_E_interscale(model, cfg),
    }
    blocks["F_rigidity"] = block_F_rigidity(model, cfg, blocks["D_snapping"])
    blocks["G_nary_closure"] = block_G_nary_closure(model, cfg)
    blocks["H_nary_associator"] = block_H_nary_associator(model, cfg)
    blocks["I_reduced_tensor"] = block_I_reduced_tensor(model, cfg)
    blocks["J_tensor_interscale"] = block_J_tensor_interscale(model, cfg)
    blocks["K_hosvd"] = block_K_hosvd(model, cfg)
    blocks["L_gauge_canonicalization"] = block_L_gauge_canonicalization(model, cfg)
    blocks["M_persistent_factorization"] = block_M_persistent_factorization(model, cfg)
    blocks["N_cyclic_law"] = block_N_cyclic_law(model, cfg)
    return blocks, compute_master_score(blocks)


def save_checkpoint(path: Path, model: SeionV17Model, opt: torch.optim.Optimizer, step: int, cfg: AuditConfig, best_record: Dict[str, Any]) -> None:
    torch.save({
        "step": step,
        "config": asdict(cfg),
        "model_state": model.state_dict(),
        "optimizer_state": opt.state_dict(),
        "best_record": best_record,
        "rng_state": get_rng_state_package(),
        "env": get_env_manifest(cfg),
        "script_sha256": sha256_file(getattr(cfg, "script_path", __file__)),
    }, path)


def build_optimizer(model: SeionV17Model, cfg: AuditConfig) -> torch.optim.Optimizer:
    if not getattr(cfg, "use_param_groups", False):
        return torch.optim.Adam(model.parameters(), lr=cfg.lr)
    groups: List[Dict[str, Any]] = []

    def add_group(name: str, params: Iterable[torch.nn.Parameter], lr_mult: float) -> None:
        ps = [p for p in params if p is not None and p.requires_grad]
        if ps:
            groups.append({"name": name, "params": ps, "lr": cfg.lr * float(lr_mult)})

    add_group("low_u", [model.u_re, model.u_im], cfg.lr_low_u_mult)
    add_group("low_product", list(model.product.parameters()), cfg.lr_low_product_mult)
    if model.has_hi:
        add_group("hi_u", [model.u_hi_re, model.u_hi_im], cfg.lr_hi_u_mult)
    if model.product_hi is not None:
        add_group("hi_product", list(model.product_hi.parameters()), cfg.lr_hi_product_mult)
    add_group("mix", [model.w_mix_re, model.w_mix_im, model.mix_gate_logit], cfg.lr_mix_mult)
    if not groups:
        groups = [{"name": "all", "params": list(model.parameters()), "lr": cfg.lr}]
    return torch.optim.Adam(groups, lr=cfg.lr)


# ============================================================
# Main audit loop
# ============================================================

def run_audit(cfg: AuditConfig) -> Dict[str, Any]:
    if cfg.device == "cuda" and not torch.cuda.is_available():
        print("[WARN] CUDA requested but not available. Falling back to CPU.", flush=True)
        cfg.device = "cpu"

    cfg = configure_run_mode(cfg)
    set_seed(cfg.seed)
    outdir = ensure_dir(cfg.outdir)

    history_jsonl = JSONLogger(outdir, "history.jsonl")
    gradients_jsonl = JSONLogger(outdir, "gradients.jsonl")
    audit_jsonl = JSONLogger(outdir, "audit_history.jsonl")
    perf_jsonl = JSONLogger(outdir, "perf_gpu.jsonl")
    csv_logger = CSVLogger(outdir, "history.csv")
    checkpoint_index = CSVLogger(outdir, "checkpoint_index.csv")

    safe_json_dump(outdir / cfg.manifest_filename, {
        "created_time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "script_sha256": sha256_file(getattr(cfg, "script_path", __file__)),
        "env": get_env_manifest(cfg),
        "config": asdict(cfg),
    })

    model = SeionV17Model(cfg).to(cfg.device)
    opt = build_optimizer(model, cfg)

    start_step = 1
    best_record: Dict[str, Any] = {}
    best_selection_score = float("inf")

    if cfg.resume:
        resume_path = cfg.resume_path or str(outdir / "latest_checkpoint.pt")
        # PyTorch >=2.6 defaults torch.load(..., weights_only=True).
        # Our SEION checkpoints intentionally store optimizer state, RNG state,
        # numpy/python RNG objects and manifest metadata, so they must be loaded
        # as full trusted checkpoints. Only use this for checkpoints you created.
        try:
            ckpt = torch.load(resume_path, map_location=cfg.device, weights_only=False)
        except TypeError:
            # Older PyTorch builds do not expose weights_only.
            ckpt = torch.load(resume_path, map_location=cfg.device)
        incompatible = model.load_state_dict(ckpt["model_state"], strict=bool(getattr(cfg, "strict_resume", False)))
        missing_keys = list(getattr(incompatible, "missing_keys", []) or [])
        unexpected_keys = list(getattr(incompatible, "unexpected_keys", []) or [])
        if (missing_keys or unexpected_keys):
            print(f"[RESUME-WARN] missing={missing_keys} unexpected={unexpected_keys}", flush=True)
        # If an older lifted/no-product_hi checkpoint is resumed into tensor_explicit,
        # product_hi will be absent from the old state_dict. Seed it from the loaded low law.
        if model.product_hi is not None and any(k.startswith("product_hi.") for k in missing_keys):
            with torch.no_grad():
                model.product.copy_low_params_into(model.product_hi)
            print("[RESUME] product_hi was missing in checkpoint; initialized from loaded low product.", flush=True)
        if getattr(cfg, "resume_optimizer", True) and "optimizer_state" in ckpt:
            try:
                opt.load_state_dict(ckpt["optimizer_state"])
            except Exception as e:
                print(f"[RESUME-WARN] optimizer_state not loaded: {e}", flush=True)
        if getattr(cfg, "restore_rng", False):
            restore_rng_state_package(ckpt.get("rng_state"))
        start_step = int(ckpt.get("step", 0)) + 1
        best_record = ckpt.get("best_record", {})
        best_selection_score = float(best_record.get("selection_score", float("inf")))
        print(f"[RESUME] Loaded {resume_path} from step {start_step - 1}", flush=True)

    t0 = time.time()
    t = thresholds_for_mode(cfg)

    cached_statuses: Dict[str, str] = {}
    cached_master_score = float("nan")
    cached_fail_reasons: List[str] = []
    cached_quick: Dict[str, Any] = {}
    cached_diag: Dict[str, float] = {}
    cached_grad_health: Dict[str, Any] = {
        "has_nan_grad": False,
        "has_inf_grad": False,
        "grad_absmax": 0.0,
        "exploding_grad_warning": False,
        "vanishing_grad_warning": False,
    }
    last_tensor_j: Optional[float] = None
    best_tensor_j = float("inf")
    step_times: List[float] = []

    for step in range(start_step, cfg.steps + 1):
        if cfg.time_budget_minutes > 0 and (time.time() - t0) > cfg.time_budget_minutes * 60.0:
            print(f"[TIME-BUDGET] stopping at step {step-1}", flush=True)
            break

        step_t0 = time.time()
        phase = phase_name(step, cfg)
        lr_eff = cfg.lr * lr_scale_for_phase(phase)
        for g in opt.param_groups:
            base_mult = float(g.get("base_lr_mult", g.get("lr", cfg.lr) / max(cfg.lr, 1e-30))) if getattr(cfg, "use_param_groups", False) else 1.0
            # For newly created groups, infer multiplier from their initial lr, then preserve it.
            if "base_lr_mult" not in g:
                g["base_lr_mult"] = base_mult
            g["lr"] = lr_eff * float(g.get("base_lr_mult", 1.0))

        freeze_hi = cfg.has_hi if hasattr(cfg, "has_hi") else False
        if cfg.freeze_hi_until_frac > 0:
            freeze_hi = (step / max(cfg.steps, 1)) < cfg.freeze_hi_until_frac

        opt.zero_grad(set_to_none=True)
        losses = model.forward_losses(step, freeze_hi=freeze_hi)
        losses["loss_total"].backward()

        grad_stride = max(int(getattr(cfg, "grad_check_every", 1)), 1)
        if step == start_step or step % grad_stride == 0 or step == cfg.steps:
            cached_grad_health = grad_health(model)
            if cached_grad_health["has_nan_grad"] or cached_grad_health["has_inf_grad"]:
                print("[WARN] invalid gradients detected; stopping.", flush=True)
                break
        gh = cached_grad_health

        opt.step()

        # Reproject U and U_hi to Stiefel after optimizer step.
        with torch.no_grad():
            q = orthonormalize_columns(model.u())
            model.u_re.copy_(torch.real(q).to(model.rdtype))
            model.u_im.copy_(torch.imag(q).to(model.rdtype))

            if model.has_hi and not freeze_hi:
                qh = orthonormalize_columns(model.u_hi())
                model.u_hi_re.copy_(torch.real(qh).to(model.rdtype))
                model.u_hi_im.copy_(torch.imag(qh).to(model.rdtype))

        do_print = (step % max(cfg.print_every, 1) == 0 or step == 1 or step == cfg.steps)
        do_log = (step % max(int(getattr(cfg, "log_every", 1)), 1) == 0 or step == 1 or step == cfg.steps)
        diag_stride = max(int(getattr(cfg, "diag_every", 1)), 1)
        if (not cached_diag) or step == start_step or step % diag_stride == 0 or do_print or step == cfg.steps:
            cached_diag = model.diagnostics()
        diag = cached_diag
        losses_float: Optional[Dict[str, float]] = None

        # Lightweight B and algebra metrics for selection.
        # Blackwell optimization: this block is expensive because it recomputes
        # curvature/normal diagnostics and several stochastic algebra probes.
        # Cache it for quick_every steps to reduce Python overhead and CPU<->GPU syncs.
        quick_stride = max(int(getattr(cfg, "quick_every", 1)), 1)
        recompute_quick = (not cached_quick) or (step == start_step) or (step % quick_stride == 0) or (step == cfg.steps)
        if recompute_quick:
            Bquick = block_B_commutator(model, cfg)
            Ulow_quick = orthonormalize_columns(model.u())
            q_trials = max(2, cfg.nary_num_trials // 2)
            closure_quick = tensor_to_float(model.closure_loss(Ulow_quick, "lo", q_trials))
            assoc_quick = tensor_to_float(model.assoc_projected_loss(Ulow_quick, "lo", q_trials))
            cyclic_quick = tensor_to_float(model.cyclic_loss(Ulow_quick, "lo", q_trials))
            gji_quick = tensor_to_float(model.gji_loss(Ulow_quick, "lo", q_trials))
            cached_quick = {
                "Bquick": Bquick,
                "closure_quick": closure_quick,
                "assoc_quick": assoc_quick,
                "cyclic_quick": cyclic_quick,
                "gji_quick": gji_quick,
            }
        else:
            Bquick = cached_quick["Bquick"]
            closure_quick = float(cached_quick["closure_quick"])
            assoc_quick = float(cached_quick["assoc_quick"])
            cyclic_quick = float(cached_quick["cyclic_quick"])
            gji_quick = float(cached_quick["gji_quick"])

        selection_score = (
            3.0 * float(Bquick["comm_unexplained_rel"])
            + 8.0 * float(Bquick["normal_unexplained_rel"])
            + 2.0 * max(0.0, 1.0 - float(Bquick["coherence_ratio"]))
            + 2.0 * closure_quick
            + 2.0 * assoc_quick
            + 1.0 * cyclic_quick
            + 1.0 * gji_quick
        )

        do_full = (step == 1) or (step == cfg.steps) or (step % max(cfg.full_audit_every, 1) == 0)
        if do_full:
            blocks, master = run_full_audit(model, cfg)
            cached_statuses = {k: str(v.get("status", "UNKNOWN")) for k, v in blocks.items()}
            cached_master_score = float(master["master_score"])
            cached_fail_reasons = list(master["fail_reasons"])
            mini = dict(blocks)
            mini["master_audit"] = master
            safe_json_dump(outdir / f"mini_audit_step_{step:06d}.json", mini)
            audit_jsonl.write({
                "step": step,
                "wall_time_sec_from_start": time.time() - t0,
                "master_score": float(master.get("master_score", float("nan"))),
                "statuses": master.get("statuses", {}),
                "fail_reasons": master.get("fail_reasons", []),
                "B_comm_unexplained_rel": blocks.get("B_commutator", {}).get("comm_unexplained_rel"),
                "B_norm_unexplained_rel": blocks.get("B_commutator", {}).get("normal_unexplained_rel"),
                "B_coherence_ratio": blocks.get("B_commutator", {}).get("coherence_ratio"),
                "G_closure_rel": blocks.get("G_nary_closure", {}).get("closure_rel"),
                "H_assoc_rel": blocks.get("H_nary_associator", {}).get("assoc_rel"),
                "J_tensor_diff_rel": blocks.get("J_tensor_interscale", {}).get("tensor_diff_rel"),
                "M_persist_rel": blocks.get("M_persistent_factorization", {}).get("persist_rel"),
                "N_gji_rel": blocks.get("N_cyclic_law", {}).get("gji_rel"),
            })

        if selection_score < best_selection_score:
            if losses_float is None:
                losses_float = {k: tensor_to_float(v) for k, v in losses.items()}
            best_selection_score = selection_score
            best_record = {
                "step": step,
                "lr": lr_eff,
                "phase": phase,
                **losses_float,
                **diag,
                "comm_rel": float(Bquick["comm_rel"]),
                "comm_unexplained_rel": float(Bquick["comm_unexplained_rel"]),
                "normal_unexplained_rel": float(Bquick["normal_unexplained_rel"]),
                "coherence_ratio": float(Bquick["coherence_ratio"]),
                "closure_quick": closure_quick,
                "assoc_quick": assoc_quick,
                "cyclic_quick": cyclic_quick,
                "gji_quick": gji_quick,
                "selection_score": selection_score,
            }
            torch.save({
                "step": step,
                "config": asdict(cfg),
                "model_state": model.state_dict(),
                "best_record": best_record,
            }, outdir / "best_model.pt")

        if do_log or do_print:
            if losses_float is None:
                losses_float = {k: tensor_to_float(v) for k, v in losses.items()}
            step_elapsed_now = time.time() - step_t0
            perf = get_perf_snapshot() if (step % max(int(getattr(cfg, "profile_every", 25)), 1) == 0 or do_print or step == cfg.steps) else {}
            weighted = weighted_loss_report(losses_float, cfg)
            record = {
                "step": step,
                "wall_time_sec_from_start": time.time() - t0,
                "wall_time_sec_step": step_elapsed_now,
                "device": cfg.device,
                "dtype": cfg.dtype,
                "run_mode": cfg.run_mode,
                "eval_mode": cfg.eval_mode,
                "lr": lr_eff,
                "phase": phase,
                "freeze_hi": freeze_hi,
                **losses_float,
                **weighted,
                **diag,
                **gh,
                **perf,
                "comm_rel": float(Bquick["comm_rel"]),
                "comm_unexplained_rel": float(Bquick["comm_unexplained_rel"]),
                "normal_unexplained_rel": float(Bquick["normal_unexplained_rel"]),
                "coherence_ratio": float(Bquick["coherence_ratio"]),
                "closure_quick": closure_quick,
                "assoc_quick": assoc_quick,
                "cyclic_quick": cyclic_quick,
                "gji_quick": gji_quick,
                "selection_score": selection_score,
                "cached_statuses": cached_statuses,
                "cached_master_score": cached_master_score,
                "cached_fail_reasons": cached_fail_reasons,
            }

            history_jsonl.write(record)
            csv_logger.write(flatten_dict(record))
            gradients_jsonl.write({
                "step": step,
                "wall_time_sec_from_start": time.time() - t0,
                **gh,
            })
            if perf:
                perf_jsonl.write({"step": step, "wall_time_sec_from_start": time.time() - t0, **perf})

        if do_print:
            if losses_float is None:
                losses_float = {k: tensor_to_float(v) for k, v in losses.items()}
            Aflag = "P" if max(diag["delta_idem"], diag["delta_selfadj"]) < t["A_tol"] else "W"
            Bflag = "P" if (
                float(Bquick["comm_unexplained_rel"]) < t["B_comm_tol"]
                and float(Bquick["normal_unexplained_rel"]) < t["B_norm_tol"]
                and float(Bquick["coherence_ratio"]) > t["B_coh_tol"]
            ) else "W"
            Nflag = cached_statuses.get("N_cyclic_law", "U")[0] if cached_statuses else "U"
            Gflag = cached_statuses.get("G_nary_closure", "U")[0] if cached_statuses else "U"
            Hflag = cached_statuses.get("H_nary_associator", "U")[0] if cached_statuses else "U"
            Jflag = cached_statuses.get("J_tensor_interscale", "U")[0] if cached_statuses else "U"
            Mflag = cached_statuses.get("M_persistent_factorization", "U")[0] if cached_statuses else "U"

            cur_tensor_j = float(losses_float.get("loss_tensor_j", float("nan")))
            if math.isfinite(cur_tensor_j):
                best_tensor_j = min(best_tensor_j, cur_tensor_j)
            delta_j = float("nan") if last_tensor_j is None or not math.isfinite(cur_tensor_j) else cur_tensor_j - float(last_tensor_j)
            last_tensor_j = cur_tensor_j
            step_dt = time.time() - step_t0
            step_times.append(step_dt)
            if len(step_times) > 100:
                step_times = step_times[-100:]
            eta_sec = max(cfg.steps - step, 0) * (float(np.median(step_times)) if step_times else step_dt)
            perf_short = get_perf_snapshot()
            mem_short = perf_short.get("gpu_mem_reserved_gb", 0.0)
            pow_short = perf_short.get("nvsmi_power_w", 0.0)
            util_short = perf_short.get("nvsmi_gpu_util_pct", 0.0)
            print(
                f"[{step:06d}] dt={step_dt:.2f}s eta={eta_sec/60:.1f}m total={losses_float['loss_total']:.6e} "
                f"cyc={losses_float['loss_cyclic']:.3e} gji={losses_float['loss_gji']:.3e} "
                f"closure={losses_float['loss_closure']:.3e} assocP={losses_float['loss_assoc_proj']:.3e} "
                f"inter={losses_float['loss_inter_proj']:.3e} tensorJ={losses_float['loss_tensor_j']:.3e} "
                f"dJ={delta_j:+.2e} bestJ={best_tensor_j:.3e}\n"
                f"         idem={diag['delta_idem']:.2e} comm={float(Bquick['comm_rel']):.3e} "
                f"unexp={float(Bquick['comm_unexplained_rel']):.3e} "
                f"norm_un={float(Bquick['normal_unexplained_rel']):.3e} "
                f"coh={float(Bquick['coherence_ratio']):.3e} rank={diag['rank_eff']:.2f} "
                f"score={selection_score:.3f} master={cached_master_score:.2f} A/{Aflag} B/{Bflag} N/{Nflag} G/{Gflag} H/{Hflag} J/{Jflag} M/{Mflag} "
                f"gpu={util_short:.0f}% {pow_short:.0f}W mem={mem_short:.2f}GB phase={phase}",
                flush=True,
            )

        if step % max(cfg.save_every, 1) == 0 or step == cfg.steps:
            latest_path = outdir / "latest_checkpoint.pt"
            step_path = outdir / f"checkpoint_step_{step:06d}.pt"
            save_checkpoint(latest_path, model, opt, step, cfg, best_record)
            save_checkpoint(step_path, model, opt, step, cfg, best_record)
            checkpoint_index.write({
                "step": step,
                "checkpoint_path": str(step_path),
                "latest_path": str(latest_path),
                "best_step": best_record.get("step", ""),
                "best_selection_score": best_selection_score,
                "cached_master_score": cached_master_score,
                "A": cached_statuses.get("A_projector", ""),
                "B": cached_statuses.get("B_commutator", ""),
                "G": cached_statuses.get("G_nary_closure", ""),
                "H": cached_statuses.get("H_nary_associator", ""),
                "J": cached_statuses.get("J_tensor_interscale", ""),
                "M": cached_statuses.get("M_persistent_factorization", ""),
                "N": cached_statuses.get("N_cyclic_law", ""),
            })

    # Final audit and exports.
    blocks, master = run_full_audit(model, cfg)

    with torch.no_grad():
        U_lo = orthonormalize_columns(model.u())
        T_lo = model.extract_reduced_tensor(U_lo, "lo")
        np.save(outdir / "block_I_reduced_tensor_lo.npy", T_lo.detach().cpu().numpy())

        hi_path = None
        if model.has_hi:
            U_hi = orthonormalize_columns(model.u_hi())
            T_hi = model.extract_reduced_tensor(U_hi, "hi")
            np.save(outdir / "block_I_reduced_tensor_hi.npy", T_hi.detach().cpu().numpy())
            hi_path = str(outdir / "block_I_reduced_tensor_hi.npy")

    for name, obj in blocks.items():
        safe_json_dump(outdir / f"{name}.json", obj)

    summary = {
        "config": asdict(cfg),
        "best_step": best_record.get("step", None),
        "best_record": best_record,
        "final_diagnostics": model.diagnostics(),
        "wall_time_sec": time.time() - t0,
        "blocks": blocks,
        "master_audit": master,
        "selection_score": best_selection_score,
        "env": get_env_manifest(cfg),
        "script_sha256": sha256_file(getattr(cfg, "script_path", __file__)),
        "files": {
            "summary_json": str(outdir / "summary.json"),
            "manifest_json": str(outdir / cfg.manifest_filename),
            "history_jsonl": str(outdir / "history.jsonl"),
            "audit_history_jsonl": str(outdir / "audit_history.jsonl"),
            "perf_gpu_jsonl": str(outdir / "perf_gpu.jsonl"),
            "checkpoint_index_csv": str(outdir / "checkpoint_index.csv"),
            "best_model": str(outdir / "best_model.pt"),
            "latest_checkpoint": str(outdir / "latest_checkpoint.pt"),
            "block_I_reduced_tensor_lo_npy": str(outdir / "block_I_reduced_tensor_lo.npy"),
            "block_I_reduced_tensor_hi_npy": hi_path,
        },
    }

    safe_json_dump(outdir / "summary.json", summary)
    (outdir / "run_report.md").write_text(
        "# SEION v17 Blackwell Repro Run Report\n\n"
        f"- master_score: {master.get('master_score')}\n"
        f"- best_step: {best_record.get('step', None)}\n"
        f"- best_selection_score: {best_selection_score}\n"
        f"- wall_time_sec: {summary['wall_time_sec']}\n"
        f"- statuses: `{json.dumps(master.get('statuses', {}), ensure_ascii=False)}`\n"
        f"- fail_reasons: `{json.dumps(master.get('fail_reasons', []), ensure_ascii=False)}`\n",
        encoding="utf-8",
    )
    return summary


# ============================================================
# CLI
# ============================================================

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="SEION Master Audit A-to-N v17 Blackwell Ultra")

    p.add_argument("--outdir", type=str, default=AuditConfig.outdir)
    p.add_argument("--seed", type=int, default=AuditConfig.seed)
    p.add_argument("--device", type=str, default=("cuda" if torch.cuda.is_available() else "cpu"))
    p.add_argument("--dtype", type=str, default=AuditConfig.dtype, choices=["float32", "float64"])
    p.add_argument("--run-mode", type=str, default=AuditConfig.run_mode, choices=["smoke", "closure", "interscale", "tensor_explicit", "certify"])
    p.add_argument("--eval-mode", type=str, default=AuditConfig.eval_mode, choices=["screening", "certification"])

    p.add_argument("--n", type=int, default=AuditConfig.n)
    p.add_argument("--n-hi", type=int, default=AuditConfig.n_hi)
    p.add_argument("--rank", type=int, default=AuditConfig.rank)
    p.add_argument("--arity", type=int, default=AuditConfig.arity)
    p.add_argument("--cp-rank", type=int, default=AuditConfig.cp_rank)
    p.add_argument("--hi-cp-rank", type=int, default=AuditConfig.hi_cp_rank)

    p.add_argument("--steps", type=int, default=AuditConfig.steps)
    p.add_argument("--lr", type=float, default=AuditConfig.lr)
    p.add_argument("--print-every", type=int, default=AuditConfig.print_every)
    p.add_argument("--save-every", type=int, default=AuditConfig.save_every)
    p.add_argument("--full-audit-every", type=int, default=AuditConfig.full_audit_every)
    p.add_argument("--quick-every", type=int, default=AuditConfig.quick_every,
                   help="Recompute B/G/H/N quick diagnostics every N steps; 1 restores original behavior.")
    p.add_argument("--log-every", type=int, default=AuditConfig.log_every,
                   help="Write JSONL/CSV history every N steps instead of every step.")
    p.add_argument("--diag-every", type=int, default=AuditConfig.diag_every,
                   help="Recompute scalar projector diagnostics every N steps; cached between recomputes.")
    p.add_argument("--grad-check-every", type=int, default=AuditConfig.grad_check_every,
                   help="Check gradient health every N steps; cached between checks.")
    p.add_argument("--time-budget-minutes", type=float, default=AuditConfig.time_budget_minutes)
    p.add_argument("--profile-every", type=int, default=AuditConfig.profile_every)
    p.add_argument("--stall-factor", type=float, default=AuditConfig.stall_factor)

    p.add_argument("--assoc-samples", type=int, default=AuditConfig.assoc_samples)
    p.add_argument("--hodge-samples", type=int, default=AuditConfig.hodge_samples)
    p.add_argument("--hodge-every", type=int, default=AuditConfig.hodge_every)
    p.add_argument("--nary-num-trials", type=int, default=AuditConfig.nary_num_trials)
    p.add_argument("--tensor-j-every", type=int, default=AuditConfig.tensor_j_every)

    p.add_argument("--beals-f-count", type=int, default=AuditConfig.beals_f_count)
    p.add_argument("--beals-x-count", type=int, default=AuditConfig.beals_x_count)
    p.add_argument("--beals-max-order", type=int, default=AuditConfig.beals_max_order)
    p.add_argument("--top-comm-singular-vectors", type=int, default=AuditConfig.top_comm_singular_vectors)

    p.add_argument("--lambda-projector", type=float, default=AuditConfig.lambda_projector)
    p.add_argument("--lambda-sub", type=float, default=AuditConfig.lambda_sub)
    p.add_argument("--lambda-leak", type=float, default=AuditConfig.lambda_leak)
    p.add_argument("--lambda-comm", type=float, default=AuditConfig.lambda_comm)
    p.add_argument("--lambda-cdc", type=float, default=AuditConfig.lambda_cdc)
    p.add_argument("--lambda-norm", type=float, default=AuditConfig.lambda_norm)
    p.add_argument("--lambda-closure", type=float, default=AuditConfig.lambda_closure)
    p.add_argument("--lambda-assoc-proj", type=float, default=AuditConfig.lambda_assoc_proj)
    p.add_argument("--lambda-assoc-raw", type=float, default=AuditConfig.lambda_assoc_raw)
    p.add_argument("--lambda-hodge", type=float, default=AuditConfig.lambda_hodge)
    p.add_argument("--lambda-inter-sub", type=float, default=AuditConfig.lambda_inter_sub)
    p.add_argument("--lambda-inter-proj", type=float, default=AuditConfig.lambda_inter_proj)
    p.add_argument("--lambda-tensor-j", type=float, default=AuditConfig.lambda_tensor_j)
    p.add_argument("--lambda-cyclic", type=float, default=AuditConfig.lambda_cyclic)
    p.add_argument("--lambda-gji", type=float, default=AuditConfig.lambda_gji)
    p.add_argument("--lambda-reg", type=float, default=AuditConfig.lambda_reg)
    p.add_argument("--tensor-j-loss-mode", type=str, default=AuditConfig.tensor_j_loss_mode, choices=["raw", "canonical", "hybrid"])
    p.add_argument("--use-param-groups", action="store_true")
    p.add_argument("--no-param-groups", dest="use_param_groups", action="store_false")
    p.set_defaults(use_param_groups=AuditConfig.use_param_groups)
    p.add_argument("--lr-low-u-mult", type=float, default=AuditConfig.lr_low_u_mult)
    p.add_argument("--lr-low-product-mult", type=float, default=AuditConfig.lr_low_product_mult)
    p.add_argument("--lr-hi-u-mult", type=float, default=AuditConfig.lr_hi_u_mult)
    p.add_argument("--lr-hi-product-mult", type=float, default=AuditConfig.lr_hi_product_mult)
    p.add_argument("--lr-mix-mult", type=float, default=AuditConfig.lr_mix_mult)

    p.add_argument("--snap-threshold", type=float, default=AuditConfig.snap_threshold)
    p.add_argument("--gauge-fix-mode", type=str, default=AuditConfig.gauge_fix_mode, choices=["gram", "none"])
    p.add_argument("--gauge-eps", type=float, default=AuditConfig.gauge_eps)
    p.add_argument("--hi-law-mode", type=str, default=AuditConfig.hi_law_mode, choices=["explicit", "lifted"])
    p.add_argument("--use-product-hi", action="store_true")
    p.add_argument("--no-product-hi", dest="use_product_hi", action="store_false")
    p.set_defaults(use_product_hi=AuditConfig.use_product_hi)
    p.add_argument("--initialize-hi-from-low", action="store_true")
    p.add_argument("--no-initialize-hi-from-low", dest="initialize_hi_from_low", action="store_false")
    p.set_defaults(initialize_hi_from_low=AuditConfig.initialize_hi_from_low)
    p.add_argument("--freeze-hi-until-frac", type=float, default=AuditConfig.freeze_hi_until_frac)

    p.add_argument("--use-selector", action="store_true")
    p.add_argument("--no-selector", dest="use_selector", action="store_false")
    p.set_defaults(use_selector=AuditConfig.use_selector)
    p.add_argument("--selector-scale", type=float, default=AuditConfig.selector_scale)
    p.add_argument("--no-phi-in-normal", dest="use_phi_in_normal", action="store_false")
    p.set_defaults(use_phi_in_normal=AuditConfig.use_phi_in_normal)
    p.add_argument("--no-mix-in-normal", dest="use_mix_in_normal", action="store_false")
    p.set_defaults(use_mix_in_normal=AuditConfig.use_mix_in_normal)
    p.add_argument("--no-normalize-phi-for-normal", dest="normalize_phi_for_normal", action="store_false")
    p.set_defaults(normalize_phi_for_normal=AuditConfig.normalize_phi_for_normal)
    p.add_argument("--dirty-interscale-target", dest="clean_interscale_target", action="store_false")
    p.set_defaults(clean_interscale_target=AuditConfig.clean_interscale_target)

    p.add_argument("--pass-thresh-B-unexplained-rel", type=float, default=AuditConfig.pass_thresh_B_unexplained_rel)
    p.add_argument("--pass-thresh-B-norm-unexplained-rel", type=float, default=AuditConfig.pass_thresh_B_norm_unexplained_rel)
    p.add_argument("--pass-thresh-B-coherence", type=float, default=AuditConfig.pass_thresh_B_coherence)
    p.add_argument("--strong-pass-thresh-B-unexplained-rel", type=float, default=AuditConfig.strong_pass_thresh_B_unexplained_rel)
    p.add_argument("--strong-pass-thresh-B-norm-unexplained-rel", type=float, default=AuditConfig.strong_pass_thresh_B_norm_unexplained_rel)
    p.add_argument("--strong-pass-thresh-B-coherence", type=float, default=AuditConfig.strong_pass_thresh_B_coherence)
    p.add_argument("--pass-thresh-E-proj-rel", type=float, default=AuditConfig.pass_thresh_E_proj_rel)
    p.add_argument("--pass-thresh-E-proc-rel", type=float, default=AuditConfig.pass_thresh_E_proc_rel)
    p.add_argument("--pass-thresh-G-closure-rel", type=float, default=AuditConfig.pass_thresh_G_closure_rel)
    p.add_argument("--pass-thresh-H-assoc-rel", type=float, default=AuditConfig.pass_thresh_H_assoc_rel)
    p.add_argument("--pass-thresh-J-tensor-rel", type=float, default=AuditConfig.pass_thresh_J_tensor_rel)
    p.add_argument("--pass-thresh-M-persist-rel", type=float, default=AuditConfig.pass_thresh_M_persist_rel)
    p.add_argument("--pass-thresh-L-gauge-rel", type=float, default=AuditConfig.pass_thresh_L_gauge_rel)
    p.add_argument("--pass-thresh-N-cyclic-rel", type=float, default=AuditConfig.pass_thresh_N_cyclic_rel)
    p.add_argument("--pass-thresh-N-gji-rel", type=float, default=AuditConfig.pass_thresh_N_gji_rel)
    p.add_argument("--hosvd-energy-threshold", type=float, default=AuditConfig.hosvd_energy_threshold)

    p.add_argument("--resume", action="store_true")
    p.add_argument("--resume-path", type=str, default=None)
    p.add_argument("--strict-resume", action="store_true")
    p.add_argument("--restore-rng", action="store_true")
    p.add_argument("--no-resume-optimizer", dest="resume_optimizer", action="store_false")
    p.set_defaults(resume_optimizer=AuditConfig.resume_optimizer)

    return p


def args_to_config(args: argparse.Namespace) -> AuditConfig:
    return AuditConfig(
        outdir=args.outdir,
        seed=args.seed,
        device=args.device,
        dtype=args.dtype,
        run_mode=args.run_mode,
        eval_mode=args.eval_mode,
        n=args.n,
        n_hi=args.n_hi,
        rank=args.rank,
        arity=args.arity,
        cp_rank=args.cp_rank,
        hi_cp_rank=args.hi_cp_rank,
        steps=args.steps,
        lr=args.lr,
        print_every=args.print_every,
        save_every=args.save_every,
        full_audit_every=args.full_audit_every,
        quick_every=args.quick_every,
        log_every=args.log_every,
        diag_every=args.diag_every,
        grad_check_every=args.grad_check_every,
        time_budget_minutes=args.time_budget_minutes,
        profile_every=args.profile_every,
        stall_factor=args.stall_factor,
        assoc_samples=args.assoc_samples,
        hodge_samples=args.hodge_samples,
        hodge_every=args.hodge_every,
        nary_num_trials=args.nary_num_trials,
        tensor_j_every=args.tensor_j_every,
        beals_f_count=args.beals_f_count,
        beals_x_count=args.beals_x_count,
        beals_max_order=args.beals_max_order,
        top_comm_singular_vectors=args.top_comm_singular_vectors,
        lambda_projector=args.lambda_projector,
        lambda_sub=args.lambda_sub,
        lambda_leak=args.lambda_leak,
        lambda_comm=args.lambda_comm,
        lambda_cdc=args.lambda_cdc,
        lambda_norm=args.lambda_norm,
        lambda_closure=args.lambda_closure,
        lambda_assoc_proj=args.lambda_assoc_proj,
        lambda_assoc_raw=args.lambda_assoc_raw,
        lambda_hodge=args.lambda_hodge,
        lambda_inter_sub=args.lambda_inter_sub,
        lambda_inter_proj=args.lambda_inter_proj,
        lambda_tensor_j=args.lambda_tensor_j,
        lambda_cyclic=args.lambda_cyclic,
        lambda_gji=args.lambda_gji,
        lambda_reg=args.lambda_reg,
        tensor_j_loss_mode=args.tensor_j_loss_mode,
        use_param_groups=args.use_param_groups,
        lr_low_u_mult=args.lr_low_u_mult,
        lr_low_product_mult=args.lr_low_product_mult,
        lr_hi_u_mult=args.lr_hi_u_mult,
        lr_hi_product_mult=args.lr_hi_product_mult,
        lr_mix_mult=args.lr_mix_mult,
        snap_threshold=args.snap_threshold,
        gauge_fix_mode=args.gauge_fix_mode,
        gauge_eps=args.gauge_eps,
        hi_law_mode=args.hi_law_mode,
        use_product_hi=args.use_product_hi,
        initialize_hi_from_low=args.initialize_hi_from_low,
        freeze_hi_until_frac=args.freeze_hi_until_frac,
        use_phi_in_normal=args.use_phi_in_normal,
        use_mix_in_normal=args.use_mix_in_normal,
        normalize_phi_for_normal=args.normalize_phi_for_normal,
        clean_interscale_target=args.clean_interscale_target,
        use_selector=args.use_selector,
        selector_scale=args.selector_scale,
        pass_thresh_B_unexplained_rel=args.pass_thresh_B_unexplained_rel,
        pass_thresh_B_norm_unexplained_rel=args.pass_thresh_B_norm_unexplained_rel,
        pass_thresh_B_coherence=args.pass_thresh_B_coherence,
        strong_pass_thresh_B_unexplained_rel=args.strong_pass_thresh_B_unexplained_rel,
        strong_pass_thresh_B_norm_unexplained_rel=args.strong_pass_thresh_B_norm_unexplained_rel,
        strong_pass_thresh_B_coherence=args.strong_pass_thresh_B_coherence,
        pass_thresh_E_proj_rel=args.pass_thresh_E_proj_rel,
        pass_thresh_E_proc_rel=args.pass_thresh_E_proc_rel,
        pass_thresh_G_closure_rel=args.pass_thresh_G_closure_rel,
        pass_thresh_H_assoc_rel=args.pass_thresh_H_assoc_rel,
        pass_thresh_J_tensor_rel=args.pass_thresh_J_tensor_rel,
        pass_thresh_M_persist_rel=args.pass_thresh_M_persist_rel,
        pass_thresh_L_gauge_rel=args.pass_thresh_L_gauge_rel,
        pass_thresh_N_cyclic_rel=args.pass_thresh_N_cyclic_rel,
        pass_thresh_N_gji_rel=args.pass_thresh_N_gji_rel,
        hosvd_energy_threshold=args.hosvd_energy_threshold,
        resume=args.resume,
        resume_path=args.resume_path,
        strict_resume=args.strict_resume,
        restore_rng=args.restore_rng,
        resume_optimizer=args.resume_optimizer,
        script_path=__file__,
    )


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    cfg = args_to_config(args)
    summary = run_audit(cfg)
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
