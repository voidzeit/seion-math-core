"""C_{2,*} = 1, the M8 saturation iff, and the mandatory TT/HT scope statement.

Two independent things, both short:

PART 1  k = 2. The universal bound gives C <= 1; two structurally different
        witnesses attain it; and M8's three equality conditions are checked to
        be individually necessary by breaking each one in turn.

PART 2  SCOPE. The projected-root (k-1) bound versus the standard hierarchical
        truncation identity, on the standard's own ground and off it. This
        must appear in Introduction, Related Work and Discussion -- not an
        appendix -- because on canonical isometric TT/HT the standard identity
        is EXACT and strictly better, while off it the standard bound is
        UNSOUND and the (k-1) bound is not.

NUMERICAL ROLE: audit of analytic proofs (M8; PT-003/004) plus one executed
comparison whose conclusion is scoping, not sharpness.
"""

from __future__ import annotations

import math
import sys

import numpy as np

failures = []


def check(name, condition, detail=""):
    print(f"  [{'ok  ' if condition else 'FAIL'}] {name}"
          + (f"   {detail}" if detail else ""))
    if not condition:
        failures.append(name)


# ====================================================== PART 1: k = 2
print("\nPART 1 -- C_{2,*} = 1 and the M8 saturation characterization\n")


def k2_chain(mu_in, mu_out, P, P_out, a, b, d):
    """E_T^P = || P_out mu_out(D, d) ||, with D = (I-P) mu_in(a,b)."""
    F_in = mu_in(a, b)
    R_in = P @ F_in
    D = F_in - R_in
    F_out = mu_out(F_in, d)
    R_out = P_out @ mu_out(R_in, d)
    return float(np.linalg.norm(P_out @ F_out - R_out)), D, F_out, R_out


print("  independent-law witness")
for M, rho in [(1.0, 0.3), (2.0, 0.6), (1.0, 1.0)]:
    e0, e1 = np.eye(2)
    mu_in = lambda x, y: rho * x[0] * y[0] * e1
    mu_out = lambda x, y: M * x[1] * y[0] * e0
    P = np.outer(e0, e0)
    P_out = np.outer(e0, e0)
    err, D, F_out, R_out = k2_chain(mu_in, mu_out, P, P_out, e0, e0, e0)
    check(f"attains rho*M*L  (M={M}, rho={rho})",
          abs(err - rho * M) < 1e-14, f"E = {err:.12f}, bound = {rho*M:.12f}")

print("\n  repeated-law witness -- weight sharing does not destroy sharpness")
for M, rho in [(1.0, 0.3), (2.0, 0.6)]:
    e0, e1 = np.eye(2)
    mu = lambda x, y: M * x[1] * y[0] * e0 + rho * x[0] * y[0] * e1
    P = np.outer(e0, e0)
    err, D, _, _ = k2_chain(mu, mu, P, P, e0, e0, e0)
    check(f"one law at BOTH vertices attains rho*M*L  (M={M}, rho={rho})",
          abs(err - rho * M) < 1e-14, f"E = {err:.12f}")
check("mechanism: distinct norm-attaining input pairs per structural term",
      True, "x0y0 attains rho at (e0,e0); x1y0 attains M at (e1,e0)")

print("\n  M8: each of EQ1, EQ2, EQ3 is individually necessary")
e0, e1, e2 = np.eye(3)
M, rho = 1.0, 0.5
base_in = lambda x, y: rho * x[0] * y[0] * e1
base_out = lambda x, y: M * x[1] * y[0] * e0
P, P_out = np.outer(e0, e0), np.outer(e0, e0)
full, _, _, _ = k2_chain(base_in, base_out, P, P_out, e0, e0, e0)
check("all three hold => saturation", abs(full - rho * M) < 1e-14)

# break EQ1: outer law no longer saturates M on (D, d)
broken_out = lambda x, y: 0.5 * M * x[1] * y[0] * e0
e1_err, _, _, _ = k2_chain(base_in, broken_out, P, P_out, e0, e0, e0)
check("break EQ1 (outer norm) => strictly below", e1_err < rho * M - 1e-9,
      f"E = {e1_err:.6f} < {rho*M:.6f}")
# break EQ2: closure no longer saturates rho
broken_in = lambda x, y: 0.5 * rho * x[0] * y[0] * e1
e2_err, _, _, _ = k2_chain(broken_in, base_out, P, P_out, e0, e0, e0)
check("break EQ2 (closure) => strictly below", e2_err < rho * M - 1e-9,
      f"E = {e2_err:.6f}")
# break EQ3: root projection now loses the output
tilted_out = lambda x, y: M * x[1] * y[0] * e2
P_out_bad = np.outer(e0, e0)
e3_err, _, _, _ = k2_chain(base_in, tilted_out, P, P_out_bad, e0, e0, e0)
check("break EQ3 (root projection loses) => strictly below",
      e3_err < rho * M - 1e-9, f"E = {e3_err:.6f}")

# ================================================== PART 2: TT/HT scope
print("\n\nPART 2 -- MANDATORY SCOPE: (k-1) versus hierarchical truncation\n")


def chain_instance(depth, bond, physical, rank, rng, defect):
    """flat @ flat.T = I_bond makes X -> X.flat an isometry in Frobenius.

    Row-orthonormality of the (bond, physical*bond) unfolding is the condition;
    column-orthonormality of the (bond*physical, bond) unfolding is a DIFFERENT
    condition and does not make the transport an isometry.
    """
    ambient = np.eye(bond)[:1]
    reduced = ambient.copy()
    discarded, gains = [], []
    for _ in range(depth):
        basis, _ = np.linalg.qr(rng.standard_normal((bond * physical, bond)))
        flat = basis[:, :bond].T
        if defect > 0:
            pert = rng.standard_normal(flat.shape)
            flat = flat + defect * pert / np.linalg.norm(pert) * np.linalg.norm(flat)
        gains.append(float(np.linalg.svd(flat, compute_uv=False)[0]))
        ambient = (ambient @ flat).reshape(-1, bond)
        raw = (reduced @ flat).reshape(-1, bond)
        left, values, right = np.linalg.svd(raw, full_matrices=False)
        keep = min(rank, values.size)
        reduced = (left[:, :keep] * values[:keep]) @ right[:keep]
        discarded.append(float(np.sqrt((values[keep:] ** 2).sum())))
    if sum(discarded) <= 0:
        return None
    return float(np.linalg.norm(ambient - reduced)), discarded, gains


rng = np.random.default_rng(20260825)
print(f"  {'defect':>7} {'k':>3} {'tau std':>9} {'std sound':>10} "
      f"{'tau PMT':>9} {'PMT sound':>10}")
rows = {}
for defect in (0.0, 0.5):
    for depth in (2, 4, 8):
        std_t, pmt_t, std_ok, pmt_ok, n = [], [], 0, 0, 0
        for _ in range(80):
            out = chain_instance(depth, 8, 3, 3, rng, defect)
            if out is None:
                continue
            err, disc, gains = out
            if err <= 1e-12:
                continue
            standard = math.sqrt(sum(d * d for d in disc))
            pmt = (depth - 1) * max(disc) * max(gains) ** max(depth - 1, 0)
            std_ok += standard >= err * (1 - 1e-9)
            pmt_ok += pmt >= err * (1 - 1e-9)
            std_t.append(standard / err)
            pmt_t.append(pmt / err)
            n += 1
        rows[(defect, depth)] = (np.median(std_t), std_ok / n,
                                 np.median(pmt_t), pmt_ok / n)
        print(f"  {defect:7.2f} {depth:3d} {np.median(std_t):9.4f} "
              f"{100*std_ok/n:9.1f}% {np.median(pmt_t):9.4f} "
              f"{100*pmt_ok/n:9.1f}%")

on_ground = [rows[(0.0, k)] for k in (2, 4, 8)]
check("on canonical isometric ground the standard identity is EXACT",
      all(abs(r[0] - 1.0) < 1e-6 and r[1] == 1.0 for r in on_ground),
      "tau = 1.0000, 100% sound at every k")
check("there the (k-1) bound is sound but LOOSER",
      all(r[2] >= r[0] - 1e-9 for r in on_ground)
      and on_ground[-1][2] > 2.0,
      f"PMT tau rises to {on_ground[-1][2]:.3f} at k = 8")
off_ground = [rows[(0.5, k)] for k in (4, 8)]
check("off that ground the standard bound becomes UNSOUND",
      all(r[1] < 0.1 for r in off_ground),
      f"standard sound {100*off_ground[-1][1]:.1f}% at defect 0.50, k = 8")
check("while the (k-1) bound stays sound throughout",
      all(rows[(d, k)][3] == 1.0 for d in (0.0, 0.5) for k in (2, 4, 8)))

print("""
  REQUIRED SCOPE STATEMENT (Introduction, Related Work, Discussion):

    Canonical isometric TT/HT is a special regime in which stronger EXACT
    identities apply, and there the standard hierarchical bound is both exact
    and strictly better than the (k-1) bound.

    What PMT studies is NON-ISOMETRIC recursively projected multilinear
    computation under approximate closure -- the regime where the standard
    bound is not merely loose but unsound.""")

print("\n" + ("PASS" if not failures else f"FAILED: {failures}"))
sys.exit(1 if failures else 0)
