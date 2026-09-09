"""Empirical lower-bound searches with explicit non-certification language."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Sequence

import numpy as np
from scipy.optimize import differential_evolution

from .typed_tree import Leaf, Node, Tree, iter_internal


@dataclass(frozen=True, slots=True)
class SearchConfig:
    eta: float
    error_type: str = "projected"
    seeds: tuple[int, ...] = (0,)
    restarts_per_seed: int = 2
    adam_steps: int = 120
    lbfgs_steps: int = 30
    learning_rate: float = 0.04
    device: str = "cuda"
    dtype: str = "float64"

    def __post_init__(self) -> None:
        if not 0.0 < self.eta <= 1.0:
            raise ValueError("eta must lie in (0,1]")
        if self.error_type not in {"ambient", "projected", "normal"}:
            raise ValueError("unknown error type")
        if self.restarts_per_seed < 1 or self.adam_steps < 0 or self.lbfgs_steps < 0:
            raise ValueError("invalid optimizer budget")


@dataclass(frozen=True, slots=True)
class SearchResult:
    best_lower_bound: float
    best_seed: int
    best_restart: int
    best_tensor: np.ndarray
    history: tuple[dict[str, float | int | str], ...]
    optimizer: str
    device: str
    status: str = "EMPIRICAL_LOWER_BOUND"
    globally_certified: bool = False


def _uniform_arity(tree: Tree) -> int:
    arities = {node.arity for node in iter_internal(tree)}
    if not arities:
        raise ValueError("adversarial search requires at least one internal node")
    if len(arities) != 1:
        raise ValueError("this search parameterization requires one arity; mixed trees use nodewise search")
    return next(iter(arities))


def _torch_parameterized_tensor(raw, arity: int, eta: float):
    import torch

    closure_index = (1, *(0 for _ in range(arity)))
    mask = torch.ones_like(raw)
    mask[closure_index] = 0.0
    free = raw * mask
    norm = torch.linalg.vector_norm(free)
    free = free / torch.clamp(norm, min=torch.finfo(raw.dtype).eps)
    result = free * math.sqrt(max(0.0, 1.0 - eta * eta))
    basis = torch.zeros_like(raw)
    basis[closure_index] = eta
    return result + basis


def _torch_tree_ratio(tree: Tree, tensor, eta: float, error_type: str):
    import torch

    projector = torch.diag(torch.tensor([1.0, 0.0], dtype=tensor.dtype, device=tensor.device))
    leaf = torch.tensor([1.0, 0.0], dtype=tensor.dtype, device=tensor.device)
    alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"

    def apply(values):
        arity = len(values)
        out = alphabet[0]
        slots = alphabet[1 : arity + 1]
        return torch.einsum(f"{out}{slots}," + ",".join(slots) + f"->{out}", tensor, *values)

    def visit(item: Tree):
        if isinstance(item, Leaf):
            return leaf, leaf
        pairs = [visit(child) for child in item.children]
        ambient = apply([pair[0] for pair in pairs])
        projected = projector @ apply([pair[1] for pair in pairs])
        return ambient, projected

    ambient, reduced = visit(tree)
    if error_type == "ambient":
        error = torch.linalg.vector_norm(ambient - reduced)
    elif error_type == "projected":
        error = torch.linalg.vector_norm(projector @ ambient - reduced)
    else:
        error = torch.linalg.vector_norm((torch.eye(2, dtype=tensor.dtype, device=tensor.device) - projector) @ ambient)
    return error / eta


def gradient_search(tree: Tree, config: SearchConfig) -> SearchResult:
    """Multistart Adam followed by L-BFGS; result is an empirical lower bound."""

    import torch

    arity = _uniform_arity(tree)
    if config.device.startswith("cuda") and not torch.cuda.is_available():
        device = "cpu"
    else:
        device = config.device
    dtype = torch.float64 if config.dtype == "float64" else torch.float32
    if device.startswith("cuda"):
        torch.backends.cuda.matmul.allow_tf32 = False
    best = -math.inf
    best_seed = -1
    best_restart = -1
    best_tensor = np.empty(0)
    history: list[dict[str, float | int | str]] = []
    shape = (2, *(2 for _ in range(arity)))
    for seed in config.seeds:
        for restart in range(config.restarts_per_seed):
            torch.manual_seed(seed * 1009 + restart)
            raw = torch.randn(shape, dtype=dtype, device=device, requires_grad=True)
            optimizer = torch.optim.Adam([raw], lr=config.learning_rate)
            for step in range(config.adam_steps):
                optimizer.zero_grad(set_to_none=True)
                tensor = _torch_parameterized_tensor(raw, arity, config.eta)
                ratio = _torch_tree_ratio(tree, tensor, config.eta, config.error_type)
                (-ratio).backward()
                optimizer.step()
                if step == 0 or (step + 1) % max(1, config.adam_steps // 12) == 0:
                    history.append(
                        {
                            "seed": seed,
                            "restart": restart,
                            "phase": "adam",
                            "step": step + 1,
                            "ratio": float(ratio.detach().cpu()),
                        }
                    )
            if config.lbfgs_steps:
                optimizer_lbfgs = torch.optim.LBFGS(
                    [raw], max_iter=config.lbfgs_steps, line_search_fn="strong_wolfe"
                )

                def closure():
                    optimizer_lbfgs.zero_grad(set_to_none=True)
                    current = _torch_parameterized_tensor(raw, arity, config.eta)
                    loss = -_torch_tree_ratio(tree, current, config.eta, config.error_type)
                    loss.backward()
                    return loss

                optimizer_lbfgs.step(closure)
            final_tensor = _torch_parameterized_tensor(raw, arity, config.eta)
            final_ratio = float(
                _torch_tree_ratio(tree, final_tensor, config.eta, config.error_type)
                .detach()
                .cpu()
            )
            history.append(
                {
                    "seed": seed,
                    "restart": restart,
                    "phase": "final",
                    "step": config.adam_steps + config.lbfgs_steps,
                    "ratio": final_ratio,
                }
            )
            if final_ratio > best:
                best = final_ratio
                best_seed = seed
                best_restart = restart
                best_tensor = final_tensor.detach().cpu().numpy()
    return SearchResult(
        best_lower_bound=float(best),
        best_seed=best_seed,
        best_restart=best_restart,
        best_tensor=best_tensor,
        history=tuple(history),
        optimizer="multistart Adam + L-BFGS",
        device=device,
    )


def _numpy_parameterized_tensor(raw: np.ndarray, arity: int, eta: float) -> np.ndarray:
    shape = (2, *(2 for _ in range(arity)))
    data = np.asarray(raw, dtype=float).reshape(shape).copy()
    closure_index = (1, *(0 for _ in range(arity)))
    data[closure_index] = 0.0
    norm = np.linalg.norm(data)
    if norm == 0.0:
        data[(0, *(0 for _ in range(arity)))] = 1.0
        norm = 1.0
    data *= math.sqrt(max(0.0, 1.0 - eta * eta)) / norm
    data[closure_index] = eta
    return data


def _numpy_ratio(tree: Tree, tensor: np.ndarray, eta: float, error_type: str) -> float:
    from .local_constants import TypedLaw
    from .projected_evaluation import compute_tree_errors
    from .types import TypeSystem, TypedSpace

    arity = tensor.ndim - 1
    types = TypeSystem([TypedSpace.coordinate("tau", 2, 1)])
    laws = {
        node.law_id: TypedLaw(node.law_id, tuple("tau" for _ in range(arity)), "tau", tensor)
        for node in iter_internal(tree)
    }
    inputs = {leaf.label: np.array([1.0]) for leaf in _iter_leaves(tree)}
    errors = compute_tree_errors(tree, laws, types, inputs)
    value = {
        "ambient": errors.ambient,
        "projected": errors.projected_root,
        "normal": errors.normal_root,
    }[error_type]
    return value / eta


def _iter_leaves(tree: Tree):
    if isinstance(tree, Leaf):
        yield tree
    else:
        for child in tree.children:
            yield from _iter_leaves(child)


def derivative_free_search(
    tree: Tree,
    *,
    eta: float,
    error_type: str = "projected",
    seed: int = 0,
    maximum_iterations: int = 30,
    population_size: int = 8,
) -> SearchResult:
    """Independent SciPy differential-evolution lower-bound search."""

    arity = _uniform_arity(tree)
    parameter_count = 2 ** (arity + 1)

    def objective(raw):
        tensor = _numpy_parameterized_tensor(np.asarray(raw), arity, eta)
        return -_numpy_ratio(tree, tensor, eta, error_type)

    result = differential_evolution(
        objective,
        bounds=[(-1.0, 1.0)] * parameter_count,
        seed=seed,
        maxiter=maximum_iterations,
        popsize=population_size,
        polish=True,
        updating="immediate",
    )
    tensor = _numpy_parameterized_tensor(result.x, arity, eta)
    ratio = -float(result.fun)
    history = (
        {
            "seed": seed,
            "restart": 0,
            "phase": "differential_evolution",
            "step": int(result.nit),
            "ratio": ratio,
            "success": str(bool(result.success)),
        },
    )
    return SearchResult(
        best_lower_bound=ratio,
        best_seed=seed,
        best_restart=0,
        best_tensor=tensor,
        history=history,
        optimizer="SciPy differential evolution",
        device="cpu",
    )
