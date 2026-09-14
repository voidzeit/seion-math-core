"""F3: transverse-field Ising ground-state MPS, amplitude/overlap evaluation with frozen TT-SVD projectors.

Construction (SVD selects projectors; the contraction is the PMT instance):
  1. H = -J sum Z_i Z_{i+1} - h sum X_i (open chain, J = 1); exact ground state psi by Lanczos.
  2. Exact left-canonical MPS by TT-SVD with no truncation: cores A_j in R^{chi_{j-1} x 2 x chi_j}.
     The bond-j basis is the left Schmidt basis, ordered by Schmidt coefficient.
  3. Frozen bond projectors P_j = diag(1_r, 0) on R^{chi_j} (identity if r >= chi_j); last node = root, P = I.
  4. PMT chain: node j law mu_j(v, x) = sum_{a,s} v_a x_s A_j[a, s, :] (node 1: mu_1(x) = sum_s x_s A_1[0, s, :]);
     leaves x are basis states e_{s_j} (bitstrings sampled from |psi|^2) or random real product states.
Law tensor T_j[b, a, s] = A_j[a, s, b]; its flattening (chi_j, chi_{j-1} * 2) has orthonormal rows
(left-canonical), so M_hat = 1 by flattening. Exact F = <x_1 ... x_n | psi>.
"""
from __future__ import annotations

import itertools
import math

import numpy as np
import scipy.sparse as sps
from scipy.sparse.linalg import eigsh

from pmt_eval import Node
from seeding import stable_seed


def tfim_ground_state(n: int, h: float, J: float = 1.0) -> np.ndarray:
    X = sps.csr_matrix([[0.0, 1.0], [1.0, 0.0]]); Z = sps.csr_matrix([[1.0, 0.0], [0.0, -1.0]])
    I = sps.identity(2, format="csr")

    def op(single, i):
        out = sps.identity(1, format="csr")
        for j in range(n):
            out = sps.kron(out, single if j == i else I, format="csr")
        return out

    H = sps.csr_matrix((2 ** n, 2 ** n))
    for i in range(n - 1):
        H = H - J * (op(Z, i) @ op(Z, i + 1))
    for i in range(n):
        H = H - h * op(X, i)
    vals, vecs = eigsh(H, k=1, which="SA")
    psi = vecs[:, 0]
    return psi / np.linalg.norm(psi)


def tt_svd_left_canonical(psi: np.ndarray, n: int, tol: float = 1e-14):
    cores, rem, chi_l = [], psi.reshape(1, -1), 1
    for j in range(n - 1):
        M = rem.reshape(chi_l * 2, -1)
        U, s, Vt = np.linalg.svd(M, full_matrices=False)
        keep = max(1, int(np.sum(s > tol * s[0])))
        U, s, Vt = U[:, :keep], s[:keep], Vt[:keep]
        cores.append(U.reshape(chi_l, 2, keep))
        rem = (s[:, None] * Vt)
        chi_l = keep
    cores.append(rem.reshape(chi_l, 2, 1))
    return cores


def flattening_norm3(T):
    a, b, c = T.shape
    return float(min(np.linalg.norm(T.reshape(a, b * c), 2),
                     np.linalg.norm(np.transpose(T, (1, 0, 2)).reshape(b, a * c), 2),
                     np.linalg.norm(np.transpose(T, (2, 0, 1)).reshape(c, a * b), 2)))


def chain_nodes(cores, r, leaves):
    n = len(cores)
    nodes, lawT = {}, []
    for j, A in enumerate(cores):
        T = np.transpose(A, (2, 0, 1))                        # (chi_j, chi_{j-1}, 2)
        lawT.append(T)
    M_hat = max(flattening_norm3(T) for T in lawT)
    for j in range(n):
        is_root = j == n - 1
        vid = "root" if is_root else f"s{j}"
        T = lawT[j]
        if j == 0:
            law = lambda cv, lv, T=T: T[:, 0, :] @ lv[0]
            children = []
        else:
            law = lambda cv, lv, T=T: np.einsum("bas,a,s->b", T, cv[0], lv[0])
            children = [f"s{j-1}" if j - 1 < n - 1 else "root"]
        chi_j = T.shape[0]
        if is_root or r >= chi_j:
            P = None if is_root else (lambda y: np.asarray(y))
        else:
            D = np.zeros(chi_j); D[:r] = 1.0
            P = lambda y, D=D: D * np.asarray(y)
        nodes[vid] = Node(children=children, leaves=[leaves[j]], law=law, M_hat=M_hat, M_provenance="flattening",
                          projector=P, is_root=is_root, extra={"output_shape": (chi_j,)})
    return nodes, lawT, M_hat


def eta_full_chain(lawT, r, M_hat):
    worst = 0.0
    for j, T in enumerate(lawT[:-1]):
        chi_j, chi_prev = T.shape[0], T.shape[1]
        Pj = np.diag((np.arange(chi_j) < r).astype(float))
        Q = np.eye(chi_j) - Pj
        Pprev = np.eye(chi_prev) if j == 0 else np.diag((np.arange(chi_prev) < r).astype(float))
        Tq = np.einsum("bc,cas,ad->bds", Q, T, Pprev)
        worst = max(worst, flattening_norm3(Tq) / M_hat)
    return worst


def instances(family: str, quick: bool = False):
    ns = [8] if quick else [8, 10, 12]
    hs = [1.0] if quick else [0.5, 1.0, 2.0]
    ranks = [1, 2, 4, 8]
    for n, h in itertools.product(ns, hs):
        psi = tfim_ground_state(n, h)
        cores = tt_svd_left_canonical(psi, n)
        rng = np.random.default_rng(stable_seed("F3", n, h))
        probs = psi ** 2 / np.sum(psi ** 2)
        idx = rng.choice(2 ** n, size=8 if quick else 64, p=probs)
        inputs = []
        for s in idx:
            bits = [(int(s) >> (n - 1 - j)) & 1 for j in range(n)]
            inputs.append(("bitstring", [np.eye(2)[b] for b in bits]))
        for _ in range(2 if quick else 16):
            ang = rng.uniform(0, math.pi, n)
            inputs.append(("product_state", [np.array([math.cos(a), math.sin(a)]) for a in ang]))
        for r in ranks:
            for t, (kind, leaves) in enumerate(inputs):
                nodes, lawT, M_hat = chain_nodes(cores, r, leaves)
                ef = eta_full_chain(lawT, r, M_hat)
                meta = {"family": "F3", "variant": kind, "topology": "chain", "n": n, "h": h, "rank": r,
                        "chi_max": max(T.shape[0] for T in lawT), "input_index": t}
                yield {"nodes": nodes, "root": "root", "meta": meta, "M_provenance": "flattening",
                       "expected_violation": False, "eta_full": ef}
