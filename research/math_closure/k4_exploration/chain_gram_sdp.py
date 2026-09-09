"""Full-subspace Gram SDP for a free chain (advisory exact-model proof in report).

No solver value from this module is a certified bound. The model retains
each source and its P/Q parts and constrains leakage on their entire P span.
"""

from __future__ import annotations

import numpy as np


def selectors(n):
    """X=(R,u1,...); next X=(P A R,A u1,...,Q A R)."""
    tp = np.zeros((2*n, n+1))
    tq = np.zeros_like(tp)
    tp[0, 0] = 1
    tq[0, n] = 1
    for i in range(1, n):
        tp[i, i] = tp[n+i, i] = 1
        tq[i, i] = tq[n+i, i] = 1
    return tp, tq


def solve_chain_sdp(eta: float, active_stages: int = 3, solver: str = "CLARABEL") -> dict:
    import cvxpy as cp
    if not 0 < eta <= 1 or active_stages < 1:
        raise ValueError("require 0 < eta <= 1 and at least one active stage")
    gp, gq = np.ones((1, 1)), np.zeros((1, 1))
    constraints, stages = [], []
    for n in range(1, active_stages + 1):
        hp = cp.Variable((2*n, 2*n), symmetric=True, name=f"HP{n}")
        hq = cp.Variable((2*n, 2*n), symmetric=True, name=f"HQ{n}")
        gin = cp.bmat([[gp, np.zeros((n,n))], [np.zeros((n,n)), gq]])
        slack = gin - hp - hq
        closure_slack = eta**2 * gp - hq[:n, :n]
        constraints += [hp >> 0, hq >> 0, slack >> 0, closure_slack >> 0]
        tp, tq = selectors(n)
        gp, gq = tp.T @ hp @ tp, tq.T @ hq @ tq
        stages.append((hp, hq, slack, closure_slack, gp, gq))
    c = np.ones(active_stages+1)
    c[0] = 0
    objective = cp.sum(cp.multiply(np.outer(c, c), gp + gq))
    problem = cp.Problem(cp.Maximize(objective), constraints)
    options = ({"tol_gap_abs": 1e-10, "tol_gap_rel": 1e-10, "tol_feas": 1e-10,
                "max_iter": 300} if solver == "CLARABEL" else
               {"eps": 1e-7, "max_iters": 100000})
    value = problem.solve(solver=solver, **options)
    rows = []
    for hp, hq, slack, cs, gp, gq in stages:
        vals = [m.value for m in (hp, hq, slack, cs, gp, gq)]
        if any(v is None for v in vals):
            continue
        rows.append({"HP": vals[0].tolist(), "HQ": vals[1].tolist(),
                     "GP": vals[4].tolist(), "GQ": vals[5].tolist(),
                     "minimum_eigenvalues": [float(np.linalg.eigvalsh(v)[0]) for v in vals[:4]]})
    return {"status": "NUMERICAL_CANDIDATE", "solver_status": problem.status,
            "solver": solver, "solver_options": options, "eta": eta,
            "active_stages": active_stages, "objective_squared": float(value),
            "normalized_error": float(np.sqrt(max(0, value))/eta),
            "stages": rows, "certified_upper_bound": None,
            "dual_matrices": [None if con.dual_value is None else con.dual_value.tolist()
                              for con in constraints],
            "limitation": "Floating primal/dual output is not an outward-rounded certificate."}
