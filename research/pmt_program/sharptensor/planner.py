"""Rank allocation for certified contract-then-truncate computations.

The planner never *certifies*; only :func:`sharptensor.certificate.certify` on an executed run does.

Pipeline (APPLICATIONS_BOUNDARY §5, CATC spec §6):

1. **Pilot** at full rank: singular values ``σ^(v)`` and child-norm products ``∏‖R_i‖`` per node give
   estimated curves ``η_v(r) = √(Σ_{j>r} σ_j²) / (∏‖R_i‖ · M_v)`` and costs ``c_v(r)``.
   Curves are estimates: after truncation the children change, so actual defects differ.
2. **Stage A (additive DP)**: minimise ``Σ c_v(r_v)`` subject to ``Λ_T Σ η_v(r_v) ≤ ε`` (knapsack on a
   conservative, rounded-up weight grid).
3. **Stage B (sharp refinement)**: greedy rank reductions accepted while
   ``Λ_T · gbox_float(η) ≤ ε`` (``gBox ≤ Σ η`` guarantees a superset of Stage A).
4. **A posteriori loop**: execute, certify; if the certified bound exceeds ``ε``, raise the rank of the
   node with the largest measured ``η_v`` and repeat.

:func:`plan_certified_search` is a slower alternative for small models: greedy reductions from full
rank, each accepted only if an executed and certified run meets ``ε`` (with the best certificate).
"""

from __future__ import annotations

import math

from .certificate import certify
from .gbox import gbox_float


def pilot_curves(model):
    res = model.execute(None, with_exact=False)
    run = res.run
    M = {n.name: n.M for n in run.nodes}
    lam = math.prod(n.M for n in run.nodes) * math.prod(l.norm for l in run.leaves)
    curves, costs, fulls = {}, {}, {}
    for n in run.nodes:
        if n.is_root:
            continue
        s = res.singular_values[n.name]
        cprod = res.child_norm_products[n.name]
        full = len(s)
        rows, cols = res.local_shapes[n.name]
        curve, cost = {}, {}
        tail = [0.0] * (full + 1)
        for j in range(full - 1, -1, -1):
            tail[j] = tail[j + 1] + float(s[j]) ** 2
        for r in range(0, full + 1):
            rho = (math.sqrt(tail[r]) / cprod) if cprod > 0 else 0.0
            curve[r] = rho / M[n.name] if M[n.name] > 0 else 0.0
            cost[r] = 8 * r * (rows + cols)
        curves[n.name], costs[n.name], fulls[n.name] = curve, cost, full
    return {"lambda": lam, "curves": curves, "costs": costs, "full": fulls, "pilot": res}


def _dp_additive(curves, costs, fulls, budget, bins=2000):
    names = list(curves)
    if budget <= 0:
        return {v: fulls[v] for v in names}
    INF = float("inf")
    best = [0.0] + [INF] * bins
    choice = []
    for v in names:
        new = [INF] * (bins + 1)
        arg = [None] * (bins + 1)
        for r in range(1, fulls[v] + 1):
            w = curves[v][r]
            wb = math.ceil(w / budget * bins - 1e-12) if w > 0 else 0
            if wb > bins:
                continue
            c = costs[v][r]
            for b in range(bins - wb + 1):
                if best[b] < INF and best[b] + c < new[b + wb]:
                    new[b + wb] = best[b] + c
                    arg[b + wb] = (b, r)
        choice.append(arg)
        best = new
    b_end = min(range(bins + 1), key=lambda b: best[b])
    if best[b_end] == INF:
        return {v: fulls[v] for v in names}
    ranks = {}
    b = b_end
    for v, arg in zip(reversed(names), reversed(choice)):
        prev, r = arg[b]
        ranks[v] = r
        b = prev
    return ranks


def _refine_gbox(ranks, curves, costs, lam, eps):
    ranks = dict(ranks)
    while True:
        best_move, best_saving = None, 0.0
        for v in ranks:
            r = ranks[v]
            if r <= 1:
                continue
            trial = dict(ranks)
            trial[v] = r - 1
            etas = [curves[u][trial[u]] for u in trial]
            val, _ = gbox_float(etas, grid=256)
            if lam * val <= eps * (1 - 1e-9):
                saving = costs[v][r] - costs[v][r - 1]
                if saving > best_saving:
                    best_move, best_saving = v, saving
        if best_move is None:
            return ranks
        ranks[best_move] -= 1


def plan_theorem_r(model, eps: float, max_iter: int = 50, tol: float = 1e-9):
    """DP additive plan, gBox refinement, then the a posteriori certification loop (Theorem R)."""
    p = pilot_curves(model)
    lam = p["lambda"]
    budget = eps / lam if lam > 0 else math.inf
    ranks_a = _dp_additive(p["curves"], p["costs"], p["full"], budget)
    ranks = _refine_gbox(ranks_a, p["curves"], p["costs"], lam, eps)
    history = []
    for it in range(max_iter):
        res = model.execute(ranks)
        cert = certify(res.run, tol=tol, actual_error=res.actual_error)
        e = cert["theorem_r"]["absolute_error_upper"]
        history.append({"iter": it, "ranks": dict(ranks), "certified": e})
        if e <= eps:
            return {"ranks": ranks, "stage_a": ranks_a, "result": res, "certificate": cert,
                    "history": history, "met": True}
        eta = cert["theorem_r"]["eta"]
        cand = [v for v in ranks if ranks[v] < p["full"][v]]
        if not cand:
            break
        v = max(cand, key=lambda u: eta.get(u, 0.0))
        ranks[v] += 1
    return {"ranks": ranks, "stage_a": ranks_a, "result": res, "certificate": cert, "history": history,
            "met": False}


def plan_certified_search(model, eps: float, which: str = "best", tol: float = 1e-9, max_steps: int = 400):
    """Greedy certified search: every accepted configuration is executed and certified."""
    p = pilot_curves(model)
    ranks = dict(p["full"])
    res = model.execute(ranks)
    cert = certify(res.run, tol=tol, actual_error=res.actual_error)
    key = "absolute_error_upper" if which == "best" else None

    def value(c):
        return c[key] if key else c["theorem_r"]["absolute_error_upper"]

    if value(cert) > eps:
        return {"ranks": ranks, "result": res, "certificate": cert, "met": False, "steps": 0}
    steps = 0
    improved = True
    while improved and steps < max_steps:
        improved = False
        order = sorted(ranks, key=lambda v: -(p["costs"][v][ranks[v]] - p["costs"][v][max(ranks[v] - 1, 0)]))
        for v in order:
            if ranks[v] <= 1:
                continue
            trial = dict(ranks)
            trial[v] -= 1
            r2 = model.execute(trial)
            c2 = certify(r2.run, tol=tol, actual_error=r2.actual_error)
            steps += 1
            if value(c2) <= eps:
                ranks, res, cert = trial, r2, c2
                improved = True
                break
    return {"ranks": ranks, "result": res, "certificate": cert, "met": True, "steps": steps}
