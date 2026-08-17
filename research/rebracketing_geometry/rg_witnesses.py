"""Explicit witnesses for the k=2 rebracketing constants J_2, H_2, S_2.

Implementation control for RG_CANONICAL.md, Theorems 3.1, 4.1 and Corollary
5.2. The mathematics is proved there; this file only checks that the tensors
written down really are admissible and really attain the claimed ratios.

What is verified for each witness, independently of the proofs:

  * ||mu||_op = M = 1                     (alternating maximization + a grid
                                           sweep in the low-dimensional cases)
  * rho_v^proj <= eta at every vertex, with the CANONICAL restriction of
    Definition 4.1: slot i is restricted to Ran(P_hat) of that child, and a
    leaf child's extended projector is the identity
  * E_T^P <= rho M L for each tree separately (C_2^P = 1)
  * the bridge identity D = -e_T + e_T'
  * the achieved ratios against 2, 2 and Sigma_2(eta)

A failure here is a bug in the witness, not a refutation of the theorems --
but a witness that is not admissible proves nothing, so the admissibility
checks are the point of the file.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
TOL = 1e-11
LAW_LABELS = ("inner_L", "inner_M", "root_L", "root_M")


# --------------------------------------------------------------------------
# operator norms
# --------------------------------------------------------------------------

def contract3(tensor: np.ndarray, x: np.ndarray, y: np.ndarray,
              z: np.ndarray) -> np.ndarray:
    """mu(x, y, z) for tensor[out, slot1, slot2, slot3]."""
    return np.einsum("oacd,a,c,d->o", tensor, x, y, z)


def _alternating_op_norm(tensor: np.ndarray, restarts: int, iters: int,
                         seed: int) -> float:
    """Operator norm by alternating maximization over the three slots.

    Each sweep replaces one slot by the leading right singular vector of the
    matrix obtained from the other two, which is exactly the maximizer of that
    slot with the others held fixed. Restarts matter: a single start can stall
    on a saddle and UNDERESTIMATE the norm, and an underestimated M would make
    an inadmissible law look admissible. All restarts are advanced together as
    one batch axis, so the whole sweep is a stack of tiny SVDs.
    """
    rng = np.random.default_rng(seed)
    dims = tensor.shape[1:]
    vecs = []
    for dim in dims:
        block = rng.standard_normal((restarts, dim))
        vecs.append(block / np.linalg.norm(block, axis=1, keepdims=True))
    specs = ["oacd,nc,nd->noa", "oacd,na,nd->noc", "oacd,na,nc->nod"]
    for _ in range(iters):
        for slot in range(3):
            others = [s for s in range(3) if s != slot]
            mat = np.einsum(specs[slot], tensor, vecs[others[0]],
                            vecs[others[1]])
            _, _, vh = np.linalg.svd(mat, full_matrices=False)
            vecs[slot] = vh[:, 0, :]
    values = np.einsum("oacd,na,nc,nd->no", tensor, *vecs)
    return float(np.linalg.norm(values, axis=1).max())


def _grid_op_norm(tensor: np.ndarray, samples: int) -> float:
    """Brute-force sweep, used when every slot has dimension <= 2.

    An independent check on the alternating maximizer: if the two disagree the
    reported norm is not trustworthy and the caller says so.
    """
    dims = tensor.shape[1:]
    if any(d > 2 for d in dims):
        return float("nan")

    def sphere(dim: int) -> np.ndarray:
        if dim == 1:
            return np.array([[1.0], [-1.0]])
        angles = np.linspace(0.0, 2.0 * math.pi, samples, endpoint=False)
        return np.stack([np.cos(angles), np.sin(angles)], axis=1)

    s1, s2, s3 = (sphere(d) for d in dims)
    best = 0.0
    for x in s1:                                   # chunked to bound memory
        slice3 = np.einsum("oacd,a->ocd", tensor, x)
        partial = np.einsum("ocd,mc,nd->mno", slice3, s2, s3, optimize=True)
        best = max(best, float(np.linalg.norm(partial, axis=2).max()))
    return best


def op_norm(tensor: np.ndarray, restarts: int = 400, iters: int = 60,
            seed: int = 0, grid: int = 121) -> dict:
    """Operator norm, with a brute sweep as a corroborating LOWER bound.

    Both methods are lower bounds -- the sweep evaluates finitely many points,
    the alternating maximizer can in principle stall. So the sweep cannot
    confirm the value, only detect a stall (`no_stall` below). The reported
    value is compared against the analytic norm by the caller; the analytic
    value is what the proofs use.
    """
    alternating = _alternating_op_norm(tensor, restarts, iters, seed)
    swept = _grid_op_norm(tensor, grid)
    value = alternating if math.isnan(swept) else max(alternating, swept)
    return {"value": value, "alternating": alternating, "grid": swept,
            "no_stall": bool(math.isnan(swept) or swept <= alternating + 1e-9)}


def restrict_slots(tensor: np.ndarray, bases) -> np.ndarray:
    """Restrict each slot to the span of an orthonormal basis (columns)."""
    out = tensor
    for slot, basis in enumerate(bases):
        if basis is None:
            continue
        spec = ["oacd,ab->obcd", "oacd,cb->oabd", "oacd,db->oacb"][slot]
        out = np.einsum(spec, out, basis)
    return out


def closure_defect(tensor: np.ndarray, projector: np.ndarray, bases,
                   **kwargs) -> dict:
    """rho_v^proj: ||(I-P) mu(...)||_op with each slot restricted per Def 4.1."""
    normal = np.eye(projector.shape[0]) - projector
    reduced = restrict_slots(np.einsum("qo,oacd->qacd", normal, tensor), bases)
    return op_norm(reduced, **kwargs)


def orthonormal_basis(projector: np.ndarray) -> np.ndarray:
    """Columns spanning Ran(projector)."""
    values, vectors = np.linalg.eigh(projector)
    return vectors[:, values > 0.5]


# --------------------------------------------------------------------------
# the rebracketing pair
# --------------------------------------------------------------------------

def evaluate_pair(mu_inner_L, P_inner_L, mu_root_L,
                  mu_inner_M, P_inner_M, mu_root_M,
                  P_root, leaves) -> dict:
    """T_L = mu(mu(x1,x2,x3), x4, x5) versus T_M = mu(x1, mu(x2,x3,x4), x5)."""
    x1, x2, x3, x4, x5 = leaves

    F_iL = contract3(mu_inner_L, x1, x2, x3)
    R_iL = P_inner_L @ F_iL
    F_L = contract3(mu_root_L, F_iL, x4, x5)
    R_L = P_root @ contract3(mu_root_L, R_iL, x4, x5)

    F_iM = contract3(mu_inner_M, x2, x3, x4)
    R_iM = P_inner_M @ F_iM
    F_M = contract3(mu_root_M, x1, F_iM, x5)
    R_M = P_root @ contract3(mu_root_M, x1, R_iM, x5)

    e_L = P_root @ F_L - R_L
    e_M = P_root @ F_M - R_M
    A = F_L - F_M
    A_hat = R_L - R_M
    PA = P_root @ A
    D = A_hat - PA
    return {"F_iL": F_iL, "R_iL": R_iL, "D_iL": F_iL - R_iL,
            "F_iM": F_iM, "R_iM": R_iM, "D_iM": F_iM - R_iM,
            "F_L": F_L, "R_L": R_L, "F_M": F_M, "R_M": R_M,
            "e_L": e_L, "e_M": e_M, "A": A, "A_hat": A_hat, "PA": PA, "D": D}


def cosine(u: np.ndarray, v: np.ndarray) -> float:
    denominator = np.linalg.norm(u) * np.linalg.norm(v)
    return float("nan") if denominator < 1e-14 else float(u @ v / denominator)


# --------------------------------------------------------------------------
# witnesses
# --------------------------------------------------------------------------

def witness_j2_dim3(eta: float) -> dict:
    """Theorem 3.1: one law, one projector, both trees, ambient dimension 3.

    mu(x,y,z) = eta x0 y0 z0 e1 + (x1 y0 - x0 y1) z2 e0,  P = diag(1,0,1).
    Every leaf lies in Ran(P), so the witness survives even under the stricter
    reading in which leaf data is required to be already reduced.
    """
    dim = 3
    mu = np.zeros((dim, dim, dim, dim))
    mu[1, 0, 0, 0] = eta
    mu[0, 1, 0, 2] = 1.0
    mu[0, 0, 1, 2] = -1.0
    P = np.diag([1.0, 0.0, 1.0])
    e0, e2 = np.eye(dim)[0], np.eye(dim)[2]
    return {"name": "J2_H2_dim3_shared_law_shared_projector", "eta": eta,
            "mu_inner_L": mu, "P_inner_L": P, "mu_root_L": mu,
            "mu_inner_M": mu, "P_inner_M": P, "mu_root_M": mu,
            "P_root": P, "leaves": [e0, e0, e0, e0, e2],
            "expected_M": dict.fromkeys(LAW_LABELS, 1.0),
            "expected_rho": dict.fromkeys(LAW_LABELS, eta),
            "predicted_J2": 2.0, "predicted_H2": 2.0, "predicted_S2": None}


def witness_j2_dim2(eta: float) -> dict:
    """Remark 3.3: the same construction in ambient dimension 2.

    Leaf x5 = e1 lies outside Ran(P); admissible because leaves are not reduced
    (Definition 1.4), and dimension 2 is minimal for k=2 saturation.
    """
    dim = 2
    mu = np.zeros((dim, dim, dim, dim))
    mu[1, 0, 0, 0] = eta
    mu[0, 1, 0, 1] = 1.0
    mu[0, 0, 1, 1] = -1.0
    P = np.diag([1.0, 0.0])
    e0, e1 = np.eye(dim)[0], np.eye(dim)[1]
    return {"name": "J2_H2_dim2_shared_law_shared_projector", "eta": eta,
            "mu_inner_L": mu, "P_inner_L": P, "mu_root_L": mu,
            "mu_inner_M": mu, "P_inner_M": P, "mu_root_M": mu,
            "P_root": P, "leaves": [e0, e0, e0, e0, e1],
            "expected_M": dict.fromkeys(LAW_LABELS, 1.0),
            "expected_rho": dict.fromkeys(LAW_LABELS, eta),
            "predicted_J2": 2.0, "predicted_H2": 2.0, "predicted_S2": None}


def sigma2(eta: float) -> float:
    """Sigma_2(eta) = sin(min(2 arcsin eta, pi/2))/eta."""
    return math.sin(min(2.0 * math.asin(min(eta, 1.0)), 0.5 * math.pi)) / eta


def witness_s2(eta: float) -> dict:
    """Corollary 5.2: A = 0 exactly while ||A_hat|| = Sigma_2(eta) rho M L.

    Three different laws; the ambient cancellation is carried by the clean part
    R_i, whose norm competes with the defect through d^2 + r^2 <= 1.
    """
    d = min(eta, 1.0 / math.sqrt(2.0))
    r = math.sqrt(1.0 - d * d)
    dim = 2
    mu_inner = np.zeros((dim, dim, dim, dim))
    mu_inner[0, 0, 0, 0] = r                        # clean part  r e0
    mu_inner[1, 0, 0, 0] = d                        # defect part d e1
    mu_root_L = np.zeros((dim, dim, dim, dim))
    mu_root_L[0, 1, 0, 0] = r
    mu_root_L[0, 0, 0, 0] = -d
    mu_root_M = np.zeros((dim, dim, dim, dim))
    mu_root_M[0, 0, 1, 0] = -r
    mu_root_M[0, 0, 0, 0] = d
    P = np.diag([1.0, 0.0])
    e0 = np.eye(dim)[0]
    return {"name": "S2_dim2_free_laws", "eta": eta,
            "mu_inner_L": mu_inner, "P_inner_L": P, "mu_root_L": mu_root_L,
            "mu_inner_M": mu_inner, "P_inner_M": P, "mu_root_M": mu_root_M,
            "P_root": P, "leaves": [e0] * 5,
            "expected_M": dict.fromkeys(LAW_LABELS, 1.0),
            "expected_rho": {"inner_L": d, "inner_M": d,
                             "root_L": 0.0, "root_M": 0.0},
            "predicted_J2": None, "predicted_H2": None,
            "predicted_S2": sigma2(eta)}


# --------------------------------------------------------------------------
# audit
# --------------------------------------------------------------------------

def audit(witness: dict, quality: int = 1) -> dict:
    eta = witness["eta"]
    P_root = witness["P_root"]
    dim = P_root.shape[0]
    identity_basis = np.eye(dim)
    restarts = 400 * quality

    values = evaluate_pair(
        witness["mu_inner_L"], witness["P_inner_L"], witness["mu_root_L"],
        witness["mu_inner_M"], witness["P_inner_M"], witness["mu_root_M"],
        P_root, witness["leaves"])

    report = {"name": witness["name"], "eta": eta, "dim": dim, "checks": {},
              "quantities": {}}

    # --- admissibility -----------------------------------------------------
    laws = {"inner_L": (witness["mu_inner_L"], witness["P_inner_L"],
                        [identity_basis] * 3),
            "inner_M": (witness["mu_inner_M"], witness["P_inner_M"],
                        [identity_basis] * 3),
            "root_L": (witness["mu_root_L"], P_root,
                       [orthonormal_basis(witness["P_inner_L"]),
                        identity_basis, identity_basis]),
            "root_M": (witness["mu_root_M"], P_root,
                       [identity_basis,
                        orthonormal_basis(witness["P_inner_M"]),
                        identity_basis])}
    for label, (tensor, projector, bases) in laws.items():
        norm = op_norm(tensor, restarts=restarts, seed=abs(hash(label)) % 9973)
        rho = closure_defect(tensor, projector, bases, restarts=restarts,
                             seed=(abs(hash(label)) + 1) % 9973)
        report["quantities"][f"M[{label}]"] = norm["value"]
        report["quantities"][f"rho_proj[{label}]"] = rho["value"]
        report["checks"][f"M[{label}] <= 1"] = bool(norm["value"] <= 1.0 + 1e-9)
        report["checks"][f"rho_proj[{label}] <= eta"] = bool(
            rho["value"] <= eta + 1e-9)
        report["checks"][f"M[{label}] matches analytic value"] = bool(
            abs(norm["value"] - witness["expected_M"][label]) < 1e-9)
        report["checks"][f"rho_proj[{label}] matches analytic value"] = bool(
            abs(rho["value"] - witness["expected_rho"][label]) < 1e-9)
        report["checks"][f"maximizer did not stall [{label}]"] = (
            norm["no_stall"] and rho["no_stall"])

    # --- per-tree error, C_2^P = 1 ----------------------------------------
    for tree, key in (("T_L", "e_L"), ("T_M", "e_M")):
        error = float(np.linalg.norm(values[key]))
        report["quantities"][f"E^P[{tree}]/(rho M L)"] = error / eta
        report["checks"][f"E^P[{tree}] <= rho M L"] = bool(
            error <= eta + 1e-9)

    # --- identities and ratios --------------------------------------------
    identity_gap = float(np.linalg.norm(
        values["D"] - (-values["e_L"] + values["e_M"])))
    report["quantities"]["bridge_identity_residual"] = identity_gap
    report["checks"]["D = -e_T + e_T'"] = bool(identity_gap < TOL)

    ratios = {"J2": float(np.linalg.norm(values["D"])) / eta,
              "S2": float(np.linalg.norm(values["A_hat"])) / eta,
              "H2": float(np.linalg.norm(values["PA"])) / eta}
    report["quantities"].update(ratios)
    report["quantities"]["||PA||/(rho M L)"] = ratios["H2"]
    report["quantities"]["||A||"] = float(np.linalg.norm(values["A"]))
    report["quantities"]["||A_hat||"] = float(np.linalg.norm(values["A_hat"]))
    report["quantities"]["chi"] = cosine(values["e_L"], values["e_M"])
    report["quantities"]["theta/pi"] = (
        math.acos(max(-1.0, min(1.0, cosine(values["PA"], values["D"]))))
        / math.pi if np.linalg.norm(values["PA"]) > 1e-14 else float("nan"))

    if witness["predicted_J2"] is not None:
        report["checks"]["J2 attains 2"] = bool(
            abs(ratios["J2"] - witness["predicted_J2"]) < 1e-12)
    if witness["predicted_H2"] is not None:
        report["checks"]["A_hat = 0 (total concealment)"] = bool(
            np.linalg.norm(values["A_hat"]) < TOL)
        report["checks"]["H2 attains 2"] = bool(
            abs(ratios["H2"] - witness["predicted_H2"]) < 1e-12)
    if witness["predicted_S2"] is not None:
        report["checks"]["A = 0 (nothing genuine to see)"] = bool(
            np.linalg.norm(values["A"]) < TOL)
        report["checks"]["S2 attains Sigma_2(eta)"] = bool(
            abs(ratios["S2"] - witness["predicted_S2"]) < 1e-12)
        report["quantities"]["Sigma_2(eta)"] = witness["predicted_S2"]

    # Theorem 5.1 in its constraint-free form, checked on the witness itself.
    slack = (float(np.linalg.norm(values["A_hat"]))
             - float(np.linalg.norm(values["PA"]))) / eta
    report["quantities"]["(||A_hat|| - ||PA||)/(rho M L)"] = slack
    report["checks"]["Theorem 5.1 holds"] = bool(slack <= sigma2(eta) + 1e-9)

    report["all_passed"] = all(report["checks"].values())
    return report


BUILDERS = {"witness_j2_dim3": witness_j2_dim3,
            "witness_j2_dim2": witness_j2_dim2,
            "witness_s2": witness_s2}


def _audit_one(job):
    """Worker entry point: one (builder, eta) audit."""
    builder, eta, quality = job
    return audit(BUILDERS[builder](eta), quality=quality)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--etas", type=float, nargs="+",
                        default=[0.05, 0.1, 0.2, 0.4, 1 / math.sqrt(2), 0.8,
                                 0.9, 1.0])
    parser.add_argument("--eta-grid", type=int, default=0,
                        help="if >0, use this many etas evenly on (0,1] "
                             "instead of --etas")
    parser.add_argument("--quality", type=int, default=1)
    parser.add_argument("--workers", type=int, default=0,
                        help="0 = os.cpu_count(); 1 = serial")
    parser.add_argument("--json", type=str, default="rg_witnesses_report.json")
    args = parser.parse_args()

    etas = args.etas
    if args.eta_grid > 0:
        # include the crossover exactly: it is where Sigma_2 changes branch
        etas = sorted({round(i / args.eta_grid, 12)
                       for i in range(1, args.eta_grid + 1)}
                      | {1 / math.sqrt(2)})
    jobs = [(name, eta, args.quality) for eta in etas for name in BUILDERS]
    workers = args.workers or os.cpu_count() or 1
    workers = max(1, min(workers, len(jobs)))

    print(f"{len(jobs)} audits over {len(etas)} etas on {workers} worker(s)")
    print(f"{'witness':>42} {'eta':>6} {'J2':>9} {'H2':>9} {'S2':>9} "
          f"{'Sigma2':>9} {'chi':>7} {'ok':>4}")

    started = time.time()
    if workers == 1:
        reports = [_audit_one(job) for job in jobs]
    else:
        with ProcessPoolExecutor(max_workers=workers) as pool:
            reports = list(pool.map(_audit_one, jobs, chunksize=1))

    failures = 0
    for report in reports:
        failures += 0 if report["all_passed"] else 1
        quantities, eta = report["quantities"], report["eta"]
        print(f"{report['name']:>42} {eta:6.3f} "
              f"{quantities['J2']:9.6f} {quantities['H2']:9.6f} "
              f"{quantities['S2']:9.6f} {sigma2(eta):9.6f} "
              f"{quantities['chi']:+7.3f} "
              f"{'PASS' if report['all_passed'] else 'FAIL':>4}")
        if not report["all_passed"]:
            for name, ok in report["checks"].items():
                if not ok:
                    print(f"      failed check: {name}")

    (HERE / args.json).write_text(json.dumps(reports, indent=2),
                                  encoding="utf-8")
    print(f"\n{len(reports)} audits, {failures} failed, "
          f"{time.time() - started:.0f}s on {workers} worker(s) -> {args.json}")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
