"""Seeded CPU candidate search with full linear matrix norm constraints."""

import numpy as np
from scipy.optimize import minimize

from seion_core.pmt.chain import audit_chain, evaluate_chain, planar_chain


def search_chain(eta, dimension=2, rank=1, seed=0, max_iterations=200, optimizer="SLSQP"):
    if not 0 < eta <= 1 or not 1 <= rank < dimension:
        raise ValueError("require 0<eta<=1 and 1<=rank<dimension")
    rng = np.random.default_rng(seed)
    p = np.diag([1.]*rank + [0.]*(dimension-rank))
    q = np.eye(dimension) - p
    x = np.ones(1)
    sizes = [dimension, dimension**2, dimension**2]

    def unpack(z):
        blocks = np.split(z, np.cumsum(sizes)[:-1])
        return [blocks[0].reshape(dimension, 1)] + [a.reshape(dimension, dimension) for a in blocks[1:]]

    def pack(ops):
        return np.concatenate([a.ravel() for a in ops])

    def repair(ops):
        result = []
        for j, a in enumerate(ops):
            b = q @ a if j == 0 else q @ a[:, :rank]
            scale = max(1., np.linalg.norm(a, 2), np.linalg.norm(b, 2)/eta)
            result.append(a / (scale * (1 + 2e-12)))
        return result

    def objective(z):
        tr = evaluate_chain(unpack(z), [p]*3, x)
        return -float(np.linalg.norm(tr.ambient[-1]-tr.reduced[-1]))/eta

    def constraints(z):
        vals = []
        for j, a in enumerate(unpack(z)):
            b = q @ a if j == 0 else q @ a[:, :rank]
            vals.extend(np.linalg.eigvalsh(np.eye(a.shape[1])-a.T@a))
            vals.extend(np.linalg.eigvalsh(eta**2*np.eye(b.shape[1])-b.T@b))
        return np.asarray(vals)

    t = min(eta, np.sqrt(3/7))
    plane_ops, _, _ = planar_chain([t]*3)
    initial = []
    indices = [0, rank]
    for j, a in enumerate(plane_ops[:3]):
        big = np.zeros((dimension, 1 if j == 0 else dimension))
        if j == 0:
            big[indices, 0] = a[:, 0]
        else:
            big[np.ix_(indices, indices)] = a
        # Every seed perturbs all free coordinates, including unused supports.
        big += rng.normal(size=big.shape) * .025
        initial.append(big)
    start = pack(repair(initial))
    if optimizer == "SLSQP":
        result = minimize(objective, start, method="SLSQP",
                          constraints={"type": "ineq", "fun": constraints},
                          options={"maxiter": max_iterations, "ftol": 2e-11})
    elif optimizer == "Powell":
        # Different search: hard global spectral rescaling on every evaluation.
        # Derivative-free, so no frozen-normalization gradient is introduced.
        result = minimize(lambda z: objective(pack(repair(unpack(z)))), start,
                          method="Powell", options={"maxiter": max_iterations,
                                                    "maxfev": 12000, "ftol": 1e-9,
                                                    "xtol": 1e-7})
    else:
        raise ValueError("optimizer must be SLSQP or Powell")
    raw_ops = unpack(result.x)
    ops = repair(raw_ops)
    tr = evaluate_chain(ops, [p]*3, x)
    error = tr.ambient[-1]-tr.reduced[-1]
    direction = error/np.linalg.norm(error) if np.linalg.norm(error) else np.eye(dimension)[0]
    ops.append(np.outer(np.eye(dimension)[0], direction))
    ps = [p]*4
    audit = audit_chain(ops, ps, x, eta)
    return {"seed": seed, "dimension": dimension, "rank": rank, "eta": eta,
            "optimizer": optimizer,
            "status": audit["status"], "optimizer_success": bool(result.success),
            "optimizer_message": str(result.message), "iterations": int(result.nit),
            "initial_normalized_error": -objective(start),
            "raw_normalized_error": -objective(result.x),
            "optimizer_objective_normalized": -float(result.fun),
            "raw_constraint_minimum": float(constraints(result.x).min()),
            "audit": audit, "operators": [a.tolist() for a in ops],
            "projectors": [p.tolist() for p in ps], "x": x.tolist(),
            "source_gram_at_stage3": tr.grams[-1].tolist(),
            "projected_state_gram_at_stage3": tr.projected_grams[-1].tolist(),
            "normal_state_gram_at_stage3": tr.normal_grams[-1].tolist()}
