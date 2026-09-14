"""Independent re-certification of an extremal candidate.

The search loop uses a cheap feasibility projection so it can afford many
restarts. That is fine for discovery and unacceptable for adjudication: a law
whose operator norm is 1 + 1e-6 can manufacture a spurious C_T > k-1, and the
whole point of this campaign is a second-order coefficient of size ~1e-4.

So every reported value is recomputed here with expensive, independent norm
estimates, and the configuration is rejected unless it is strictly admissible
after an exact final rescale.
"""

from __future__ import annotations

import torch

from .optimizer import (CERT_ITERS, CERT_RESTARTS, DTYPE, coordinate_projector,
                        make_feasible, multilinear_op_norm)
from .skeletons import internal_nodes, projected_root_error


def certify(root, params: list[torch.Tensor], eta: float, dim: int, rank: int,
            *, seed: int = 12345, tol: float = 1e-9) -> dict:
    """Recompute the candidate's value under strict, independently-estimated caps."""
    dev = params[0].device
    gen = torch.Generator(device=dev).manual_seed(seed)
    nodes = internal_nodes(root)
    projectors = {id(n): coordinate_projector(dim, rank, dev) for n in nodes}
    leaf = torch.zeros(dim, dtype=DTYPE, device=dev)
    leaf[0] = 1.0
    eye = torch.eye(dim, dtype=DTYPE, device=dev)

    laws, diagnostics = {}, []
    with torch.no_grad():
        for node, raw in zip(nodes, params):
            mu = make_feasible(raw, node.arity, projectors[id(node)], eta, generator=gen)

            # Independent, expensive estimates of both caps.
            op, _ = multilinear_op_norm(mu, node.arity, iters=CERT_ITERS,
                                        restarts=CERT_RESTARTS, generator=gen)
            if float(op) > 1.0:
                mu = mu / op                       # exact rescale onto the cap
                op, _ = multilinear_op_norm(mu, node.arity, iters=CERT_ITERS,
                                            restarts=CERT_RESTARTS, generator=gen)
            normal = eye - projectors[id(node)]
            clo, _ = multilinear_op_norm(mu, node.arity, post=normal,
                                         restrict=projectors[id(node)],
                                         iters=CERT_ITERS, restarts=CERT_RESTARTS,
                                         generator=gen)
            if float(clo) > eta:
                tang = torch.tensordot(mu, projectors[id(node)], dims=([node.arity], [0]))
                nrm = torch.tensordot(mu, normal, dims=([node.arity], [0]))
                mu = tang + (eta / clo) * nrm
                op, _ = multilinear_op_norm(mu, node.arity, iters=CERT_ITERS,
                                            restarts=CERT_RESTARTS, generator=gen)
                clo, _ = multilinear_op_norm(mu, node.arity, post=normal,
                                             restrict=projectors[id(node)],
                                             iters=CERT_ITERS, restarts=CERT_RESTARTS,
                                             generator=gen)
            laws[id(node)] = mu
            diagnostics.append({"arity": node.arity, "op_norm": float(op),
                                "closure": float(clo)})

        value = float(projected_root_error(root, laws, projectors, leaf))

    admissible = all(d["op_norm"] <= 1.0 + tol and d["closure"] <= eta + tol
                     for d in diagnostics)
    return {
        "certified_value": value,
        "certified_constant": value / eta,
        "admissible": admissible,
        "max_op_norm": max(d["op_norm"] for d in diagnostics),
        "max_closure": max(d["closure"] for d in diagnostics),
        "eta": eta, "dim": dim, "rank": rank,
        "nodes": diagnostics,
    }


def negative_controls(root, dim: int, rank: int, eta: float = 0.3, seed: int = 0) -> dict:
    """Configurations whose projected error must vanish identically."""
    dev = torch.device("cpu")
    gen = torch.Generator(device=dev).manual_seed(seed)
    nodes = internal_nodes(root)
    leaf = torch.zeros(dim, dtype=DTYPE, device=dev)
    leaf[0] = 1.0
    eye = torch.eye(dim, dtype=DTYPE, device=dev)
    raws = [torch.randn((dim,) * (n.arity + 1), dtype=DTYPE, generator=gen) for n in nodes]

    out = {}

    # (1) every projector the identity -> R == F at every node.
    proj_id = {id(n): eye for n in nodes}
    laws = {id(n): make_feasible(r, n.arity, eye, eta, generator=gen)
            for n, r in zip(nodes, raws)}
    out["all_projectors_identity"] = float(projected_root_error(root, laws, proj_id, leaf))

    # (2) only the root projects -> the root defect is annihilated by P_r.
    proj_root = {id(n): (coordinate_projector(dim, rank, dev) if n is root else eye)
                 for n in nodes}
    laws = {id(n): make_feasible(r, n.arity, proj_root[id(n)], eta, generator=gen)
            for n, r in zip(nodes, raws)}
    out["only_root_projects"] = float(projected_root_error(root, laws, proj_root, leaf))

    # (3) zero closure budget -> every law lands inside its projector range.
    proj = {id(n): coordinate_projector(dim, rank, dev) for n in nodes}
    laws = {id(n): make_feasible(r, n.arity, proj[id(n)], 0.0, generator=gen)
            for n, r in zip(nodes, raws)}
    out["zero_closure_budget"] = float(projected_root_error(root, laws, proj, leaf))
    return out
