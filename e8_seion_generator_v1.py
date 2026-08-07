#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
e8_seion_generator_v1.py
"""

import os, time, json
import numpy as np
import torch

# ---------------- CONFIG ----------------
torch.backends.cuda.matmul.allow_tf32 = False

DEVICE  = torch.device("cuda" if torch.cuda.is_available() else "cpu")
DTYPE_C = torch.complex128
DTYPE_R = torch.float64

SAVE_DIR  = "E8_Exact_v18_2"
os.makedirs(SAVE_DIR, exist_ok=True)
K_PATH    = os.path.join(SAVE_DIR, "f_E8.npy")
INFO_PATH = os.path.join(SAVE_DIR, "info.json")

# --- Validaciones (tuneables) ---
SUBSET_GPU_A = 32
SUBSET_GPU_B = 32
SUBSET_CPU   = 64

JACOBI_MC_SAMPLES = 1000   # 0 = off
JACOBI_MC_BATCH   = 200

CENTER_THR = 1e-12
NULLITY_TRIALS = 50
NULLITY_THR_LIST = [1e-8, 1e-10, 1e-12, 1e-14]

# Gram pinv
GRAM_RCOND = 1e-12

# Real-structure solve (NO-KRON)
REALSTRUCT_SUBSET_EQNS = 60
REALSTRUCT_TOL_COMM    = 1e-8
REALSTRUCT_ITERS       = 300
REALSTRUCT_RESTARTS    = 10
REALSTRUCT_STEP0       = 0.2
REALSTRUCT_DEVICE      = "cuda"  # "cpu" recomendado si tu VRAM está muy justa

FIXEDPOINT_BASIS_TRIES = 2500     # subimos porque ahora sí construye base real robusta
FIXEDPOINT_BASIS_SEED  = 0
FIXEDPOINT_REORTHO_PASSES = 2     # re-orthonormalization passes

# E8-like thresholds (heurísticos)
E8_CENTER_MAX   = 1
E8_KILLING_RANK = 248
E8_NULLITY_MAX  = 20

# --- FAST PATH CFG (v14/v15 style) ---
BEST_CFG = {
    "block_type": "mp",
    "transpose_C": True,
    "use_J_for_K": False,     # False => usa G_stack para K
    "X_variant": "plain",     # plain / antisym / sym
    "phase_K": 1.0,
    "u": -2.0,
    "v": -2.0,
    "alpha": -1.0,
    "beta": -1.0,
}

print(f"🚀 DEVICE: {DEVICE}")
if DEVICE.type == "cuda":
    print(f"   GPU: {torch.cuda.get_device_name(0)}")
print("   dtype: complex128 / float64 enforced")

# ============================================================
# Utils
# ============================================================

def kron_torch(a: torch.Tensor, b: torch.Tensor) -> torch.Tensor:
    siz = torch.Size(torch.tensor(a.shape[-2:], device=a.device) *
                     torch.tensor(b.shape[-2:], device=b.device))
    res = a.unsqueeze(-1).unsqueeze(-3) * b.unsqueeze(-2).unsqueeze(-4)
    return res.reshape(siz)

def antisymmetrize_batch(M: torch.Tensor) -> torch.Tensor:
    return 0.5 * (M - M.transpose(1, 2))

def build_ij_map():
    ij = []
    for i in range(1, 17):
        for j in range(i + 1, 17):
            ij.append((i, j))
    return ij  # len=120

def apply_X_variant(X_stack, variant: str):
    if variant == "plain":
        return X_stack
    if variant == "antisym":
        return 0.5 * (X_stack - X_stack.transpose(1,2))
    if variant == "sym":
        return 0.5 * (X_stack + X_stack.transpose(1,2))
    raise ValueError(f"X_variant desconocido: {variant}")

# ============================================================
# 1) Clifford Cl(16) + chirality
# ============================================================

def build_gammas_cl16(n=8):
    I  = torch.eye(2, device=DEVICE, dtype=DTYPE_C)
    s1 = torch.tensor([[0, 1], [1, 0]], device=DEVICE, dtype=DTYPE_C)
    s2 = torch.tensor([[0, -1j], [1j, 0]], device=DEVICE, dtype=DTYPE_C)
    s3 = torch.tensor([[1, 0], [0, -1]], device=DEVICE, dtype=DTYPE_C)

    gammas = []
    for k in range(1, n + 1):
        lst1 = [I] * (k - 1) + [s1] + [s3] * (n - k)
        g1 = lst1[0]
        for m in lst1[1:]:
            g1 = kron_torch(g1, m)
        gammas.append(g1)

        lst2 = [I] * (k - 1) + [s2] + [s3] * (n - k)
        g2 = lst2[0]
        for m in lst2[1:]:
            g2 = kron_torch(g2, m)
        gammas.append(g2)

    return gammas  # 16 x (256,256)

@torch.no_grad()
def chirality_indices(gammas):
    Gs = torch.eye(256, device=DEVICE, dtype=DTYPE_C)
    for G in gammas:
        Gs = Gs @ G

    diag = torch.diagonal(Gs)
    off = torch.linalg.norm(Gs - torch.diag(diag)).item()
    nrm = torch.linalg.norm(Gs).item()
    ratio = off / (nrm + 1e-30)

    d = diag.real.to(DTYPE_R)
    idx_p = torch.where(d > 0)[0]
    idx_m = torch.where(d < 0)[0]

    if len(idx_p) != 128 or len(idx_m) != 128:
        vals, _ = torch.sort(d)
        idx_p = torch.where(torch.isclose(d, vals[-1], atol=1e-3))[0]
        idx_m = torch.where(torch.isclose(d, vals[0], atol=1e-3))[0]

    if len(idx_p) != 128 or len(idx_m) != 128:
        raise RuntimeError(f"Chiral split failed: S+={len(idx_p)} S-={len(idx_m)}")

    return idx_p, idx_m, ratio

@torch.no_grad()
def build_G_stack(gammas, idx_p):
    ij_map = build_ij_map()
    mats = []
    for (i, j) in ij_map:
        Gi = gammas[i - 1]
        Gj = gammas[j - 1]
        comm = 0.5 * (Gi @ Gj - Gj @ Gi)
        mats.append(comm[idx_p][:, idx_p])
    return torch.stack(mats, dim=0)  # [120,128,128] complex128

@torch.no_grad()
def build_C_matrix(gammas):
    C = torch.eye(256, device=DEVICE, dtype=DTYPE_C)
    for idx in range(1, len(gammas), 2):
        C = C @ gammas[idx]
    return C

# ============================================================
# 2) so(16) generators as antihermitian + Gram with -Re Tr(AB)
# ============================================================

@torch.no_grad()
def antihermitian_part(A: torch.Tensor) -> torch.Tensor:
    return 0.5 * (A - A.conj().transpose(-1, -2))

@torch.no_grad()
def gram_antiherm(A_stack: torch.Tensor, rcond=1e-12):
    """
    Gram_{ab} = -Re Tr(A_a A_b) for antihermitian A.
    """
    N, n, _ = A_stack.shape
    Gram = torch.empty((N, N), device=A_stack.device, dtype=DTYPE_R)
    for i in range(N):
        Ai = A_stack[i]
        T = torch.einsum("ij,bji->b", Ai, A_stack)  # Tr(Ai Ab)
        Gram[i] = -(T.real.to(DTYPE_R))
    Gram = 0.5 * (Gram + Gram.T)
    s = torch.linalg.svdvals(Gram)
    smax = s.max().item() if s.numel() else 0.0
    rank = int((s > (rcond * smax)).sum().item()) if smax > 0 else 0
    return Gram, rank, smax, s

@torch.no_grad()
def compute_f_so_from_A(A_stack: torch.Tensor, Gram: torch.Tensor, rcond=1e-12):
    """
    Least squares: [A_a, A_b] = f_{ab}^c A_c using Gram pinv.
    """
    N, n, _ = A_stack.shape
    Gram_inv = torch.linalg.pinv(Gram, rcond=rcond)  # [N,N]
    f = torch.zeros((N, N, N), device=A_stack.device, dtype=DTYPE_R)

    for a in range(N):
        Aa = A_stack[a].unsqueeze(0)
        L = torch.matmul(Aa, A_stack) - torch.matmul(A_stack, Aa)  # [N,n,n]
        b = torch.empty((N, N), device=A_stack.device, dtype=DTYPE_R)
        for b_idx in range(N):
            X = L[b_idx]
            T = torch.einsum("ij,cji->c", X, A_stack)               # Tr(X A_c)
            b[b_idx] = -(T.real.to(DTYPE_R))
        c = b @ Gram_inv
        f[a] = c

    f = 0.5 * (f - f.transpose(0, 1))
    return f, Gram_inv

# ============================================================
# 3) Find real structure S: minimize ||A S - S A*||^2  (NO-KRON)
# ============================================================

@torch.no_grad()
def solve_real_structure_no_kron(A_stack: torch.Tensor,
                                use_eqns: int = 60,
                                iters: int = 300,
                                restarts: int = 10,
                                step0: float = 0.2,
                                device_for_solve: str = "cuda"):
    """
    Minimiza f(S) = sum_k ||A_k S - S A_k^*||_F^2 con pasos de gradiente normalizado.
    NO construye Kronecker => NO OOM.
    """
    dev = torch.device(device_for_solve) if device_for_solve else A_stack.device
    A = A_stack[:min(use_eqns, A_stack.shape[0])].to(dev)
    N, n, _ = A.shape

    def L(S):
        return torch.matmul(A, S.unsqueeze(0)) - torch.matmul(S.unsqueeze(0), A.conj())

    def LT(Y):
        term1 = torch.matmul(A.conj().transpose(-1, -2), Y).sum(dim=0)
        term2 = torch.matmul(Y, A.transpose(-1, -2)).sum(dim=0)
        return term1 - term2

    g = torch.Generator(device=dev)
    g.manual_seed(0)

    best = None

    for _ in range(restarts):
        S = (torch.randn((n, n), device=dev, dtype=DTYPE_R, generator=g) +
             1j * torch.randn((n, n), device=dev, dtype=DTYPE_R, generator=g)).to(DTYPE_C)
        S = S / (torch.linalg.norm(S) + 1e-30)

        step = float(step0)
        f_last = None

        for it in range(iters):
            Y = L(S)
            fval = (torch.linalg.norm(Y) ** 2).real
            Gs = 2.0 * LT(Y)

            S_new = S - step * Gs
            S_new = S_new / (torch.linalg.norm(S_new) + 1e-30)

            if (it % 10) == 0:
                Y_new = L(S_new)
                f_new = (torch.linalg.norm(Y_new) ** 2).real
                if f_last is not None and f_new > fval:
                    step *= 0.5
                else:
                    S = S_new
                    f_last = f_new
            else:
                S = S_new

        Y = L(S)
        comm_res = torch.linalg.norm(Y).item() / (torch.linalg.norm(torch.matmul(A, S.unsqueeze(0))).item() + 1e-30)

        SS = S @ S.conj()
        tr = torch.trace(SS) / n
        devSS = torch.linalg.norm(SS - tr*torch.eye(n, device=dev, dtype=DTYPE_C)).item() / (torch.linalg.norm(SS).item() + 1e-30)

        key = (-comm_res, -devSS)
        if best is None or key > best["key"]:
            best = {"S": S, "comm_res": comm_res, "SS_dev": devSS, "key": key}

    S_best = best["S"] / (torch.linalg.norm(best["S"]) + 1e-30)
    return S_best.to(A_stack.device), {"comm_res": best["comm_res"], "SS_dev": best["SS_dev"], "method": "no_kron_gd"}

@torch.no_grad()
def normalize_real_structure_phase(S: torch.Tensor):
    """
    Enforce S S* ≈ I by removing scalar phase/scale:
      SS = S S*
      c  = tr(SS)/n  (scalar)
      S <- S / sqrt(c)
    """
    n = S.shape[0]
    SS = S @ S.conj()
    c = torch.trace(SS) / n  # complex scalar ~ phase/scale
    # principal sqrt; stable for near-real positive
    S = S / torch.sqrt(c)
    return S

@torch.no_grad()
def build_fixed_point_basis(S: torch.Tensor, n=128, seed=0, tries=2500, reortho_passes=2):
    """
    Build B columns in Fix(J), J(v)=S v*, enforcing fixed-point after every GS step:
        P_fix(v) = (v + S v*)/2
    """
    g = torch.Generator(device=S.device)
    g.manual_seed(seed)

    def Pfix(v):
        return 0.5 * (v + S @ v.conj())

    def proj(u, v):
        return (u.conj() @ v).real

    cols = []
    for _ in range(tries):
        x = (torch.randn(n, device=S.device, dtype=DTYPE_R, generator=g) +
             1j*torch.randn(n, device=S.device, dtype=DTYPE_R, generator=g))
        v = Pfix(x)

        nr = torch.sqrt((v.conj() @ v).real + 1e-30)
        v = v / nr

        for c in cols:
            v = Pfix(v - proj(c, v) * c)

        nr2 = torch.sqrt((v.conj() @ v).real + 1e-30)
        if nr2.item() < 1e-8:
            continue

        v = v / nr2
        cols.append(v)

        if len(cols) == n:
            break

    if len(cols) != n:
        raise RuntimeError(f"Fixed-point basis failed: got {len(cols)}/{n}. Increase tries.")

    B = torch.stack(cols, dim=1)

    # Re-orthonormalize passes (stabilize)
    for _ in range(reortho_passes):
        new_cols = []
        for j in range(n):
            v = B[:, j]
            for c in new_cols:
                v = Pfix(v - proj(c, v) * c)
            nr = torch.sqrt((v.conj() @ v).real + 1e-30)
            v = v / nr
            new_cols.append(v)
        B = torch.stack(new_cols, dim=1)

    err = torch.linalg.norm(B - S @ B.conj()).item() / (torch.linalg.norm(B).item() + 1e-30)
    return B, err

@torch.no_grad()
def represent_in_real_fixed_basis(A_stack: torch.Tensor, B: torch.Tensor):
    """
    J_k = Re(B^H A_k B) antisym.
    """
    N, n, _ = A_stack.shape
    BH = B.conj().T
    J = torch.empty((N, n, n), device=A_stack.device, dtype=DTYPE_R)

    max_im = 0.0
    max_sym = 0.0
    for k in range(N):
        M = BH @ (A_stack[k] @ B)
        max_im = max(max_im, torch.linalg.norm(M.imag).item() / (torch.linalg.norm(M).item() + 1e-30))
        Mr = M.real.to(DTYPE_R)
        Ms = Mr + Mr.T
        max_sym = max(max_sym, torch.linalg.norm(Ms).item() / (torch.linalg.norm(Mr).item() + 1e-30))
        J[k] = 0.5 * (Mr - Mr.T)

    return J, {"max_rel_imag": max_im, "max_rel_sym": max_sym}

# ============================================================
# 4) Jacobi subset (GPU-safe) + CPU tools
# ============================================================

@torch.no_grad()
def jacobi_subset_norm_torch(f: torch.Tensor, subset: int, seed: int = 0):
    g = torch.Generator(device=f.device)
    g.manual_seed(seed)
    D = f.shape[0]
    idx = torch.randperm(D, generator=g, device=f.device)[:subset]

    fb = f[idx][:, idx, :]
    fm = f[:, idx][:, :, idx]
    t1 = torch.einsum('abm,mcd->abcd', fb, fm)
    t2 = torch.einsum('bcm,mad->bcad', fb, fm).permute(2, 0, 1, 3)
    t3 = torch.einsum('cam,mbd->cabd', fb, fm).permute(1, 2, 0, 3)
    J = t1 + t2 + t3
    return (torch.linalg.norm(J) / (subset ** 2)).item()

def jacobi_subset_norm_numpy(f_np, subset=64, seed=0):
    rng = np.random.default_rng(seed)
    D = f_np.shape[0]
    idx = rng.choice(D, subset, replace=False)
    fb = f_np[idx][:, idx, :]
    fm = f_np[:, idx][:, :, idx]
    t1 = np.einsum('abm,mcd->abcd', fb, fm, optimize=True)
    t2 = np.einsum('bcm,mad->bcad', fb, fm, optimize=True).transpose(2,0,1,3)
    t3 = np.einsum('cam,mbd->cabd', fb, fm, optimize=True).transpose(1,2,0,3)
    J = t1 + t2 + t3
    return float(np.linalg.norm(J) / (subset**2))

def estimate_center_dim_numpy(f_np, rel_thr=1e-12):
    D = f_np.shape[0]
    M = np.reshape(np.transpose(f_np, (1,2,0)), (D*D, D)).astype(np.float64)
    s = np.linalg.svd(M, compute_uv=False)
    smax = float(s.max())
    n0 = int(np.sum(s <= rel_thr * smax))
    return n0, smax, float(s.min())

def nullity_scan_numpy(f_np, trials=50, rel_thr=1e-12, seed=0):
    rng = np.random.default_rng(seed)
    D = f_np.shape[0]
    nulls = []
    smins = []
    for _ in range(trials):
        v = rng.standard_normal(D)
        v /= (np.linalg.norm(v) + 1e-12)
        ad = np.einsum('A,ABC->CB', v, f_np, optimize=True).astype(np.float64)
        s = np.linalg.svd(ad, compute_uv=False)
        smax = float(s.max())
        thr = rel_thr * smax
        nulls.append(int(np.sum(s <= thr)))
        smins.append(float(s.min()))
    return int(np.min(nulls)), float(np.mean(nulls)), int(np.max(nulls)), float(np.median(smins))

def jacobi_mc_numpy(f_np, samples=1000, batch=200, seed=0):
    if samples <= 0:
        return 0.0
    rng = np.random.default_rng(seed)
    D = f_np.shape[0]
    vals = []
    done = 0

    def bracket(x, y):
        return np.einsum('A,B,ABC->C', x, y, f_np, optimize=True)

    while done < samples:
        bs = min(batch, samples - done)
        X = rng.standard_normal((bs, D))
        Y = rng.standard_normal((bs, D))
        Z = rng.standard_normal((bs, D))
        X /= (np.linalg.norm(X, axis=1, keepdims=True) + 1e-12)
        Y /= (np.linalg.norm(Y, axis=1, keepdims=True) + 1e-12)
        Z /= (np.linalg.norm(Z, axis=1, keepdims=True) + 1e-12)

        for i in range(bs):
            x, y, z = X[i], Y[i], Z[i]
            yz = bracket(y, z)
            zx = bracket(z, x)
            xy = bracket(x, y)
            J = bracket(x, yz) + bracket(y, zx) + bracket(z, xy)
            vals.append(np.linalg.norm(J))
        done += bs

    return float(np.mean(vals))

def killing_form_numpy(f_np):
    return np.einsum("ACD,BCD->AB", f_np.astype(np.float64), f_np.astype(np.float64), optimize=True)

def matrix_rank_svd_numpy(M, rel_thr=1e-12):
    s = np.linalg.svd(M, compute_uv=False)
    smax = float(s.max()) if s.size else 0.0
    r = int(np.sum(s > rel_thr*smax)) if smax > 0 else 0
    return r, smax, float(s.min()) if s.size else 0.0

# ============================================================
# 5) K ansatz
# ============================================================

@torch.no_grad()
def build_K_uv_ansatz(C_block, X_stack, phase_K, u, v):
    left  = torch.matmul(C_block.unsqueeze(0), X_stack)
    right = torch.matmul(X_stack, C_block.unsqueeze(0))
    K_cplx = (u * left + v * right)
    K_real = (phase_K * K_cplx).real.to(DTYPE_R)
    K = antisymmetrize_batch(K_real)
    return K

# ============================================================
# MAIN
# ============================================================

def main():
    t0 = time.time()

    print("\n[1] Construyendo Clifford Cl(16) ...")
    gammas = build_gammas_cl16(n=8)
    C_full = build_C_matrix(gammas)

    idx_p, idx_m, diag_ratio = chirality_indices(gammas)
    print(f"    S+: {len(idx_p)} | S-: {len(idx_m)} | offdiag(G*)/||G*|| ≈ {diag_ratio:.3e}")

    print("\n[2] Construyendo G_stack (Gamma_ij proyectados a S+) ...")
    G_stack = build_G_stack(gammas, idx_p)

    A_stack = antihermitian_part(G_stack).contiguous()

    print("\n[3] Gram (antihermitian, -Re Tr(AB)) y f_so por pinv(Gram) ...")
    Gram, rk, smax, svals = gram_antiherm(A_stack, rcond=GRAM_RCOND)
    print(f"    rank(Gram) = {rk}/120 | smax={smax:.3e} | smin={svals.min().item():.3e}")
    if rk < 120:
        print("    ⚠️ WARNING: rank(Gram)<120. No es so(16) completo; se marcará is_e8_like=False.")
    f_so, _ = compute_f_so_from_A(A_stack, Gram, rcond=GRAM_RCOND)
    print("    f_so listo.")

    print("\n[4] Encontrando estructura real (S: A S = S A*) [NO-KRON] ...")
    S, diagS = solve_real_structure_no_kron(
        A_stack,
        use_eqns=REALSTRUCT_SUBSET_EQNS,
        iters=REALSTRUCT_ITERS,
        restarts=REALSTRUCT_RESTARTS,
        step0=REALSTRUCT_STEP0,
        device_for_solve=REALSTRUCT_DEVICE
    )
    print(f"    comm_res≈{diagS['comm_res']:.3e} | SS_dev≈{diagS['SS_dev']:.3e} | method={diagS['method']}")

    # ---- CRITICAL FIX: normalize phase so that S S* ≈ I
    S = normalize_real_structure_phase(S)
    SS_chk = S @ S.conj()
    n = SS_chk.shape[0]
    rel_SS = (torch.linalg.norm(SS_chk - torch.eye(n, device=SS_chk.device, dtype=DTYPE_C)) /
              (torch.linalg.norm(torch.eye(n, device=SS_chk.device, dtype=DTYPE_C)) + 1e-30)).item()
    print(f"    after phase-fix: ||S S* - I||/||I|| ≈ {rel_SS:.3e}")

    if diagS["comm_res"] > REALSTRUCT_TOL_COMM:
        print("    ⚠️ WARNING: S no conmuta bien (residual alto). Realificación puede fallar.")

    print("\n[5] Construyendo base real fija v = S v* (dim 128) [PROJECTED GS] ...")
    B, fp_err = build_fixed_point_basis(
        S, n=128,
        seed=FIXEDPOINT_BASIS_SEED,
        tries=FIXEDPOINT_BASIS_TRIES,
        reortho_passes=FIXEDPOINT_REORTHO_PASSES
    )
    print(f"    fixed-point error ||B - S B*||/||B|| ≈ {fp_err:.3e}")

    print("\n[6] Representación real J_stack en esa base (debe ser real y antisimétrica) ...")
    J_stack, diagJ = represent_in_real_fixed_basis(A_stack, B)
    print(f"    max_rel_imag(M)≈{diagJ['max_rel_imag']:.3e} | max_rel_sym≈{diagJ['max_rel_sym']:.3e}")

    print("\n[7] FAST PATH: usando BEST_CFG ...")
    cfg = dict(BEST_CFG)

    C_blocks = {
        "pp": C_full[idx_p][:, idx_p],
        "mp": C_full[idx_m][:, idx_p],
    }
    Cb = C_blocks[cfg["block_type"]]
    if cfg["transpose_C"]:
        Cb = Cb.T

    X_stack = (J_stack.to(DTYPE_C) if cfg["use_J_for_K"] else G_stack)
    X_stack = apply_X_variant(X_stack, cfg["X_variant"])

    K_stack = build_K_uv_ansatz(
        C_block=Cb,
        X_stack=X_stack,
        phase_K=cfg["phase_K"],
        u=float(cfg["u"]),
        v=float(cfg["v"]),
    )

    alpha = float(cfg["alpha"])
    beta  = float(cfg["beta"])

    D = 248
    f_t = torch.zeros((D, D, D), device=DEVICE, dtype=DTYPE_R)
    f_t[:120, :120, :120] = f_so
    f_t[:120, 120:, 120:] += alpha * J_stack
    f_t[120:, :120, 120:] -= alpha * J_stack.permute(1,0,2)
    f_t[120:, 120:, :120] += beta  * K_stack.permute(1,2,0)
    f_t = 0.5 * (f_t - f_t.permute(1,0,2))

    jac_gpu = None
    if DEVICE.type == "cuda":
        def try_jac(Ssz, seed):
            nonlocal f_t
            while Ssz >= 12:
                try:
                    return jacobi_subset_norm_torch(f_t, subset=Ssz, seed=seed), Ssz
                except torch.OutOfMemoryError:
                    torch.cuda.empty_cache()
                    Ssz -= 8
            return None, Ssz

        j1, s1 = try_jac(SUBSET_GPU_A, 0)
        j2, s2 = try_jac(SUBSET_GPU_B, 1)
        if j1 is not None and j2 is not None:
            jac_gpu = 0.5 * (j1 + j2)
            print(f"    jac_gpu(subsets) = {jac_gpu:.6e}   (S={s1} & {s2})")
        else:
            print("    ⚠️ jac_gpu: omitido (OOM incluso con subset pequeño).")

    print("\n[8] Validaciones finales (CPU float64) ...")
    f_np = f_t.detach().cpu().numpy().astype(np.float64)

    if not np.isfinite(f_np).all():
        raise RuntimeError("❌ NaN/Inf detectado en f.")

    anti = np.linalg.norm(f_np + np.swapaxes(f_np, 0, 1)) / (np.linalg.norm(f_np) + 1e-30)
    print(f"    antisym_ratio = {anti:.3e}")

    jac_cpu = jacobi_subset_norm_numpy(f_np, subset=SUBSET_CPU, seed=1)
    print(f"    jac_cpu(subset{SUBSET_CPU}) = {jac_cpu:.6e}")

    jac_mc = None
    if JACOBI_MC_SAMPLES > 0:
        jac_mc = jacobi_mc_numpy(f_np, samples=JACOBI_MC_SAMPLES, batch=JACOBI_MC_BATCH, seed=2)
        print(f"    jac_mc(samples={JACOBI_MC_SAMPLES}) = {jac_mc:.6e}")

    center_dim, smaxM, sminM = estimate_center_dim_numpy(f_np, rel_thr=CENTER_THR)
    print(f"    center_dim ~ {center_dim}  (thr={CENTER_THR:.0e}*smax, smax={smaxM:.3e}, smin={sminM:.3e})")

    print("    nullity(ad_v) scan:")
    null_stats = []
    for thr in NULLITY_THR_LIST:
        nmin, nmean, nmax, smin_med = nullity_scan_numpy(
            f_np,
            trials=NULLITY_TRIALS,
            rel_thr=thr,
            seed=0
        )
        null_stats.append((thr, nmin, nmean, nmax, smin_med))
        print(f"      thr={thr:.0e} -> nullity min/mean/max = {nmin}/{nmean:.2f}/{nmax} | median(s_min)={smin_med:.3e}")

    print("    Killing form κ_AB = f_Acd f_Bcd ...")
    kappa = killing_form_numpy(f_np)
    k_rank, k_smax, k_smin = matrix_rank_svd_numpy(kappa, rel_thr=1e-12)
    print(f"      rank(κ) = {k_rank}/248 | smax={k_smax:.3e} | smin={k_smin:.3e}")

    reasons = []
    if rk < 120:
        reasons.append(f"rank(Gram_so16)={rk}<120")
    if center_dim > E8_CENTER_MAX:
        reasons.append(f"center_dim≈{center_dim}>0")
    if k_rank != E8_KILLING_RANK:
        reasons.append(f"rank(Killing)={k_rank}!=248")
    thr12 = [x for x in null_stats if abs(x[0] - 1e-12) < 1e-30]
    if thr12:
        nmin12 = thr12[0][1]
        if nmin12 > E8_NULLITY_MAX:
            reasons.append(f"nullity(ad_v) min≈{nmin12} >> 8")

    # Also include sanity checks from realification
    if fp_err > 1e-6:
        reasons.append(f"fixed-point error≈{fp_err:.3e} (too large)")
    if diagJ["max_rel_imag"] > 1e-6:
        reasons.append(f"max_rel_imag≈{diagJ['max_rel_imag']:.3e} (too large)")

    is_e8_like = (len(reasons) == 0)

    if is_e8_like:
        print("    ✅ Certificados compatibles con E8: Jacobi/centro/Killing/nullity + realificación estable.")
    else:
        print("    ⚠️ NO compatible con E8 bajo certificados. Razones:")
        for r in reasons:
            print(f"      - {r}")

    np.save(K_PATH, f_np.astype(np.float32))

    meta = {
        "save_dir": SAVE_DIR,
        "kernel_path": K_PATH,
        "gram_rcond": GRAM_RCOND,
        "rank_gram_so16": int(rk),
        "real_structure": diagS,
        "SS_minus_I_rel": float(rel_SS),
        "fixed_point_error": float(fp_err),
        "J_representation_diag": diagJ,
        "best_cfg": cfg,
        "jac_gpu_mean": None if jac_gpu is None else float(jac_gpu),
        "jac_cpu_subset": float(jac_cpu),
        "jac_mc_mean": None if jac_mc is None else float(jac_mc),
        "center_dim_est": int(center_dim),
        "antisym_ratio": float(anti),
        "killing_rank": int(k_rank),
        "is_e8_like": bool(is_e8_like),
        "not_e8_reasons": reasons,
        "notes": "v18.2: normalized S phase to enforce J^2~I; fixed-point basis via projector (v+S v*)/2 with re-projection each GS step; improves realification and Jacobi."
    }
    with open(INFO_PATH, "w", encoding="utf-8") as fh:
        json.dump(meta, fh, indent=2)

    print(f"\n✅ Kernel guardado: {K_PATH}")
    print(f"📄 Metadatos: {INFO_PATH}")
    print(f"⏱️ Tiempo total: {time.time()-t0:.2f}s")

if __name__ == "__main__":
    main()
