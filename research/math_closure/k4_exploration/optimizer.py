"""Free-law extremal search with hard feasibility projection.

The admissible set is
    ||mu_v||_op <= 1,     rho_v^proj = ||(I-P_v) mu_v(P.,...,P.)||_op <= eta,
and the objective is E_T^P. Soft penalties are deliberately NOT used as the
feasibility guarantee: a candidate that violates the operator norm by 1e-6 can
manufacture a spurious C_T > k-1. Instead every parameter vector is mapped onto
a feasible point before the objective is evaluated -- divide by the computed
operator norm, then shrink the normal component until the closure cap holds --
so every value reported is attained by an admissible configuration.

Norms of multilinear maps are computed by alternating maximization (the natural
generalisation of power iteration), with the maximising vectors detached so the
outer gradient is a valid subgradient of the projected objective.

WLOG each projector is a fixed coordinate projector: any orthogonal projector is
U P U^* and the rotations can be absorbed into the adjacent laws without
changing any operator norm.
"""

from __future__ import annotations

import torch

from .skeletons import LEAF, contract, internal_nodes, projected_root_error

DTYPE = torch.float64


def coordinate_projector(dim: int, rank: int, device) -> torch.Tensor:
    d = torch.zeros(dim, dtype=DTYPE, device=device)
    d[:rank] = 1.0
    return torch.diag(d)


SEARCH_ITERS, SEARCH_RESTARTS = 8, 2       # fast, inside the optimization loop
CERT_ITERS, CERT_RESTARTS = 250, 24        # accurate, for certification only


_GRID_CACHE: dict = {}


def _angle_grid(n: int, device) -> torch.Tensor:
    key = (n, str(device))
    if key not in _GRID_CACHE:
        a = torch.linspace(0, 2 * torch.pi, n + 1, dtype=DTYPE, device=device)[:-1]
        _GRID_CACHE[key] = torch.stack((torch.cos(a), torch.sin(a)), dim=1)  # [n,2]
    return _GRID_CACHE[key]


def _plane_op_norm(tensor: torch.Tensor, arity: int, post, restrict, grid_n: int):
    """Exhaustive global maximisation over the unit circle(s), for dim == 2.

    Alternating maximisation only finds a local maximum; in dimension two the
    admissible input set is a product of circles and can simply be enumerated,
    which is both faster and globally correct. Inputs restricted to a rank-one
    range collapse to the single unit vector spanning it (up to sign, immaterial
    for a norm).
    """
    device = tensor.device
    if restrict is not None:
        rank = int(torch.round(torch.diagonal(restrict).sum()).item())
        if rank <= 1:
            e = restrict[:, 0] if restrict[0, 0] > 0.5 else restrict[:, 1]
            e = e / torch.linalg.norm(e)
            vs = [e] * arity
            val = contract(tensor, vs)
            return torch.linalg.norm(post @ val if post is not None else val), vs
    pts = _angle_grid(grid_n, device)
    specs = {1: "ia,gi->ga", 2: "ija,gi,hj->gha", 3: "ijka,gi,hj,lk->ghla"}
    if arity not in specs:
        raise NotImplementedError(f"plane grid path supports arity <= 3, got {arity}")
    with torch.no_grad():
        out = torch.einsum(specs[arity], tensor, *([pts] * arity))
        if post is not None:
            out = torch.einsum("...a,ba->...b", out, post)
        norms = torch.linalg.norm(out, dim=-1)
        idx = torch.unravel_index(torch.argmax(norms), norms.shape)
        vs = [pts[int(i)] for i in idx]
        # The coarse grid locates the global basin; a few exact alternating
        # steps then converge inside it. Grid alone would need ~10^4 points per
        # axis for this accuracy, which is far more expensive than refining.
        for _ in range(12):
            for i in range(arity):
                mat = tensor
                for j in sorted((j for j in range(arity) if j != i), reverse=True):
                    mat = torch.tensordot(vs[j], mat, dims=([0], [j]))
                mat = mat.T if post is None else post @ mat.T
                vs[i] = torch.linalg.svd(mat)[2][0]
    val = contract(tensor, vs)
    if post is not None:
        val = post @ val
    return torch.linalg.norm(val), vs


def multilinear_op_norm(tensor: torch.Tensor, arity: int, *, post: torch.Tensor | None = None,
                        restrict: torch.Tensor | None = None, iters: int = SEARCH_ITERS,
                        restarts: int = SEARCH_RESTARTS, generator=None,
                        grid_n: int | None = None) -> tuple[torch.Tensor, list]:
    if tensor.shape[0] == 2:
        n = grid_n or (48 if iters <= SEARCH_ITERS else 256)
        if arity >= 3:
            n = min(n, 32 if iters <= SEARCH_ITERS else 96)
        return _plane_op_norm(tensor, arity, post, restrict, n)
    """sup ||post . mu(x_1,...,x_m)|| over unit x_i (optionally in Range(restrict))."""
    dim = tensor.shape[0]
    device = tensor.device
    best_val, best_vecs = None, None
    for _ in range(restarts):
        vs = []
        for _ in range(arity):
            v = torch.randn(dim, dtype=DTYPE, device=device, generator=generator)
            if restrict is not None:
                v = restrict @ v
            n = torch.linalg.norm(v)
            vs.append(v / n if n > 1e-12 else torch.zeros_like(v))
        for _ in range(iters):
            for i in range(arity):
                # Contract every slot but i, leaving a linear map in slot i.
                # Descending order so the surviving lower indices keep their
                # positions as each contraction removes one axis.
                out = tensor
                for j in sorted((j for j in range(arity) if j != i), reverse=True):
                    out = torch.tensordot(vs[j], out, dims=([0], [j]))
                # `out` is now [dim_i, dim_out]; optionally post-composed.
                mat = out.T if post is None else post @ out.T
                if restrict is not None:
                    mat = mat @ restrict
                u, s, vh = torch.linalg.svd(mat)
                cand = vh[0]
                if restrict is not None:
                    cand = restrict @ cand
                    n = torch.linalg.norm(cand)
                    if n < 1e-12:
                        continue
                    cand = cand / n
                vs[i] = cand
        # Envelope theorem: hold the maximising vectors fixed and let the tensor
        # carry the gradient. Detaching the *norm* instead (as an earlier version
        # did) yields a descent direction that ignores the normalisation
        # entirely, and the search then stalls far below the known optimum.
        vs = [v.detach() for v in vs]
        val = contract(tensor, vs)
        if post is not None:
            val = post @ val
        val = torch.linalg.norm(val)
        if best_val is None or float(val) > float(best_val):
            best_val, best_vecs = val, vs
    return best_val, best_vecs


def make_feasible(raw: torch.Tensor, arity: int, projector: torch.Tensor, eta: float,
                  generator=None) -> torch.Tensor:
    """Map a raw tensor onto an admissible law: unit operator norm, closure <= eta."""
    dim = raw.shape[0]
    device = raw.device
    op, vecs = multilinear_op_norm(raw, arity, generator=generator)
    tensor = raw / op.clamp(min=1e-12)

    eye = torch.eye(dim, dtype=DTYPE, device=device)
    normal = eye - projector
    clo, _ = multilinear_op_norm(tensor, arity, post=normal, restrict=projector,
                                 generator=generator)
    if float(clo) > eta:
        scale = eta / clo.clamp(min=1e-12)
        # Split into tangential and normal output components and shrink only the
        # normal part; this cannot increase the operator norm.
        tang = torch.tensordot(tensor, projector, dims=([arity], [0]))
        norm_part = torch.tensordot(tensor, normal, dims=([arity], [0]))
        tensor = tang + scale * norm_part
    return tensor


def objective(params: list[torch.Tensor], nodes: list, projectors: dict, leaf: torch.Tensor,
              eta: float, root, generator=None) -> torch.Tensor:
    laws = {}
    for node, raw in zip(nodes, params):
        laws[id(node)] = make_feasible(raw, node.arity, projectors[id(node)], eta,
                                       generator=generator)
    return projected_root_error(root, laws, projectors, leaf)


def search(root, eta: float, dim: int, rank: int, *, restarts: int = 24, steps: int = 400,
           lr: float = 0.05, seed: int = 0, device: str = "cpu") -> dict:
    """Maximize E_T^P; return the best value and the configuration that achieved it."""
    dev = torch.device(device)
    gen = torch.Generator(device=dev).manual_seed(seed)
    nodes = internal_nodes(root)
    projectors = {id(n): coordinate_projector(dim, rank, dev) for n in nodes}
    leaf = torch.zeros(dim, dtype=DTYPE, device=dev)
    leaf[0] = 1.0

    best = {"value": -1.0, "params": None}
    for r in range(restarts):
        params = [torch.randn((dim,) * (n.arity + 1), dtype=DTYPE, device=dev,
                              generator=gen, requires_grad=True) for n in nodes]
        opt = torch.optim.Adam(params, lr=lr)
        for _ in range(steps):
            opt.zero_grad(set_to_none=True)
            val = objective(params, nodes, projectors, leaf, eta, root, generator=gen)
            (-val).backward()
            opt.step()
        with torch.no_grad():
            val = objective(params, nodes, projectors, leaf, eta, root, generator=gen)
        if float(val) > best["value"]:
            best = {"value": float(val),
                    "params": [p.detach().clone() for p in params]}
    best.update({"eta": eta, "dim": dim, "rank": rank, "seed": seed,
                 "restarts": restarts, "steps": steps})
    return best
