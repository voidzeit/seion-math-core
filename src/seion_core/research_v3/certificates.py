"""Dynamic-programming error certificates using nodewise local summaries."""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import product
import math
from typing import Mapping, Sequence

from .mixed_norms import Mask, MixedNormTable
from .telescoping_order import SlotBound, named_order_costs, optimal_telescoping_order, telescoping_cost
from .typed_tree import Leaf, Node, Tree, iter_internal


Path = tuple[int, ...]


@dataclass(frozen=True, slots=True)
class LocalSummary:
    """Declared information available at one internal node.

    ``M`` bounds the full law, ``m`` the all-projected/output-projected law,
    and ``rho`` the all-projected/output-normal closure map.  Mixed tables and
    slot gains are optional certified refinements; absence falls back to the
    corresponding global bound.
    """

    law_id: str
    M: float
    m: float
    rho: float
    mixed: MixedNormTable | None = None
    gains_full: tuple[float, ...] | None = None
    gains_projected: tuple[float, ...] | None = None
    gains_normal: tuple[float, ...] | None = None

    def __post_init__(self) -> None:
        if min(self.M, self.m, self.rho) < 0.0:
            raise ValueError("local constants must be nonnegative")
        if self.m > self.M + 1.0e-12 or self.rho > self.M + 1.0e-12:
            raise ValueError("m and rho cannot exceed a valid full operator-norm upper bound M")

    def _mixed_or_default(self, output: str, mask: Mask) -> float:
        if self.mixed is not None:
            return self.mixed.norm(output, mask)
        all_projected = all(symbol == "P" for symbol in mask)
        if output == "P" and all_projected:
            return self.m
        if output == "N" and all_projected:
            return self.rho
        return self.M

    def gain(self, output: str, slot: int, arity: int) -> float:
        declared = {
            "F": self.gains_full,
            "P": self.gains_projected,
            "N": self.gains_normal,
        }[output]
        if declared is not None:
            if len(declared) != arity:
                raise ValueError(f"{output} slot gain count does not match arity")
            return float(declared[slot])
        mask = tuple("N" if index == slot else "P" for index in range(arity))
        return self._mixed_or_default(output, mask)


@dataclass(frozen=True, slots=True)
class NodeBound:
    path: Path
    B_F: float
    B_R: float
    B_A: float
    B_P: float
    B_N: float
    direct_subset_A: float
    orthogonal_A: float
    telescoping_A: float
    telescoping_P: float
    telescoping_N: float
    path_sum_A: float
    path_sum_P: float
    path_sum_N: float
    orders: Mapping[str, tuple[int, ...]]
    ambient_contributions: Mapping[Path, float] = field(default_factory=dict)
    projected_contributions: Mapping[Path, float] = field(default_factory=dict)
    normal_contributions: Mapping[Path, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        values = (
            self.B_F,
            self.B_R,
            self.B_A,
            self.B_P,
            self.B_N,
            self.direct_subset_A,
            self.orthogonal_A,
            self.telescoping_A,
            self.telescoping_P,
            self.telescoping_N,
            self.path_sum_A,
            self.path_sum_P,
            self.path_sum_N,
        )
        if min(values) < -1.0e-12:
            raise ValueError("node bounds must be nonnegative")


@dataclass(frozen=True, slots=True)
class BoundCertificate:
    root: NodeBound
    nodes: Mapping[Path, NodeBound]
    complexity: str
    homogeneous_ambient: float | None = None
    homogeneous_projected: float | None = None
    theorem_status: str = "CERTIFIED_UPPER_BOUND"


def _state_sums(summary: LocalSummary, children: Sequence[NodeBound]) -> tuple[float, float, float]:
    """Bound exact subset terms using states R, projected error, normal error."""

    full_sum = 0.0
    projected_sum = 0.0
    normal_sum = 0.0
    # state 0=R (projected), 1=P Delta (projected), 2=N Delta (normal)
    for states in product((0, 1, 2), repeat=len(children)):
        if all(state == 0 for state in states):
            continue
        magnitudes: list[float] = []
        mask: list[str] = []
        for state, child in zip(states, children):
            if state == 0:
                magnitudes.append(child.B_R)
                mask.append("P")
            elif state == 1:
                magnitudes.append(child.B_P)
                mask.append("P")
            else:
                magnitudes.append(child.B_N)
                mask.append("N")
        scale = math.prod(magnitudes)
        key = tuple(mask)
        full_sum += summary._mixed_or_default("F", key) * scale
        projected_sum += summary._mixed_or_default("P", key) * scale
        normal_sum += summary._mixed_or_default("N", key) * scale
    return full_sum, projected_sum, normal_sum


def _telescoping(
    summary: LocalSummary, children: Sequence[NodeBound], output: str
) -> tuple[float, tuple[int, ...], dict[str, object]]:
    slots = [
        SlotBound(
            slot=index,
            error=child.B_A,
            reduced=child.B_R,
            full=child.B_F,
            gain=summary.gain(output, index, len(children)),
        )
        for index, child in enumerate(children)
    ]
    order = optimal_telescoping_order(slots)
    return telescoping_cost(slots, order), order, named_order_costs(slots)


def _propagate_contributions(
    summary: LocalSummary,
    children: Sequence[NodeBound],
    child_paths: Sequence[Path],
    order: Sequence[int],
    output: str,
    contribution_field: str = "ambient_contributions",
) -> dict[Path, float]:
    result: dict[Path, float] = {}
    by_position = {slot: position for position, slot in enumerate(order)}
    for slot, child in enumerate(children):
        position = by_position[slot]
        previous = order[:position]
        later = order[position + 1 :]
        factor = (
            summary.gain(output, slot, len(children))
            * math.prod(children[index].B_R for index in previous)
            * math.prod(children[index].B_F for index in later)
        )
        child_contributions = getattr(child, contribution_field)
        for source, value in child_contributions.items():
            result[source] = result.get(source, 0.0) + factor * value
        # A zero-error leaf has no source contribution; child_paths is kept in
        # the signature to make the path mapping explicit and auditable.
        _ = child_paths[slot]
    return result


def certify_tree(
    tree: Tree,
    summaries: Mapping[str, LocalSummary],
    leaf_norms: Mapping[int, float] | Sequence[float],
    *,
    homogeneous_M: float | None = None,
    homogeneous_rho: float | None = None,
) -> BoundCertificate:
    """Compute ``B^F,B^R,B^A,B^P,B^N`` bottom-up.

    Complexity is ``O(|T| 3^a_max + |T| a_max log a_max)``.  For the declared
    bounded arities 2--4 this is linear in the number of nodes.
    """

    records: dict[Path, NodeBound] = {}

    def leaf_norm(leaf: Leaf) -> float:
        try:
            value = float(leaf_norms[leaf.label])
        except (KeyError, IndexError) as exc:
            raise ValueError(f"missing norm for leaf {leaf.label}") from exc
        if value < 0.0:
            raise ValueError("leaf norm bounds must be nonnegative")
        return value

    def visit(item: Tree, path: Path) -> NodeBound:
        if isinstance(item, Leaf):
            norm = leaf_norm(item)
            bound = NodeBound(
                path=path,
                B_F=norm,
                B_R=norm,
                B_A=0.0,
                B_P=0.0,
                B_N=0.0,
                direct_subset_A=0.0,
                orthogonal_A=0.0,
                telescoping_A=0.0,
                telescoping_P=0.0,
                telescoping_N=0.0,
                path_sum_A=0.0,
                path_sum_P=0.0,
                path_sum_N=0.0,
                orders={"A": (), "P": (), "N": (), "path_A": (), "path_P": (), "path_N": ()},
                ambient_contributions={},
                projected_contributions={},
                normal_contributions={},
            )
            records[path] = bound
            return bound
        if item.law_id not in summaries:
            raise ValueError(f"missing local constants for law {item.law_id!r}")
        summary = summaries[item.law_id]
        if summary.law_id != item.law_id:
            raise ValueError("summary map key and law id disagree")
        child_paths = [(*path, slot) for slot in range(item.arity)]
        children = [visit(child, child_path) for child, child_path in zip(item.children, child_paths)]
        full_terms, projected_terms, normal_terms = _state_sums(summary, children)
        local = summary.rho * math.prod(child.B_R for child in children)
        subset_A = local + full_terms
        subset_P = projected_terms
        subset_N = local + normal_terms
        tel_A_raw, order_A, _ = _telescoping(summary, children, "F")
        tel_P, order_P, _ = _telescoping(summary, children, "P")
        tel_N_raw, order_N, _ = _telescoping(summary, children, "N")
        tel_A = local + tel_A_raw
        tel_N = local + tel_N_raw
        path_slots_A = [
            SlotBound(
                slot=index,
                error=child.path_sum_A,
                reduced=child.B_R,
                full=child.B_F,
                gain=summary.gain("F", index, len(children)),
            )
            for index, child in enumerate(children)
        ]
        path_order_A = optimal_telescoping_order(path_slots_A)
        path_sum_A = local + telescoping_cost(path_slots_A, path_order_A)
        path_slots_P = [
            SlotBound(
                slot=index,
                error=child.path_sum_A,
                reduced=child.B_R,
                full=child.B_F,
                gain=summary.gain("P", index, len(children)),
            )
            for index, child in enumerate(children)
        ]
        path_order_P = optimal_telescoping_order(path_slots_P)
        path_sum_P = telescoping_cost(path_slots_P, path_order_P)
        path_slots_N = [
            SlotBound(
                slot=index,
                error=child.path_sum_A,
                reduced=child.B_R,
                full=child.B_F,
                gain=summary.gain("N", index, len(children)),
            )
            for index, child in enumerate(children)
        ]
        path_order_N = optimal_telescoping_order(path_slots_N)
        path_sum_N = local + telescoping_cost(path_slots_N, path_order_N)
        B_P = min(subset_P, tel_P)
        B_N = min(subset_N, tel_N)
        orthogonal = math.hypot(B_P, B_N)
        B_A = min(subset_A, tel_A, path_sum_A, orthogonal)
        contributions = _propagate_contributions(
            summary, children, child_paths, path_order_A, "F"
        )
        contributions[path] = contributions.get(path, 0.0) + local
        projected_contributions = _propagate_contributions(
            summary, children, child_paths, path_order_P, "P"
        )
        normal_contributions = _propagate_contributions(
            summary, children, child_paths, path_order_N, "N"
        )
        normal_contributions[path] = normal_contributions.get(path, 0.0) + local
        bound = NodeBound(
            path=path,
            B_F=summary.M * math.prod(child.B_F for child in children),
            B_R=summary.m * math.prod(child.B_R for child in children),
            B_A=B_A,
            B_P=B_P,
            B_N=B_N,
            direct_subset_A=subset_A,
            orthogonal_A=orthogonal,
            telescoping_A=tel_A,
            telescoping_P=tel_P,
            telescoping_N=tel_N,
            path_sum_A=path_sum_A,
            path_sum_P=path_sum_P,
            path_sum_N=path_sum_N,
            orders={
                "A": order_A,
                "P": order_P,
                "N": order_N,
                "path_A": path_order_A,
                "path_P": path_order_P,
                "path_N": path_order_N,
            },
            ambient_contributions=contributions,
            projected_contributions=projected_contributions,
            normal_contributions=normal_contributions,
        )
        records[path] = bound
        return bound

    root = visit(tree, ())
    k = sum(1 for _ in iter_internal(tree))
    product_leaf = math.prod(float(value) for value in leaf_norms.values()) if isinstance(leaf_norms, Mapping) else math.prod(float(value) for value in leaf_norms)
    ambient_h = None
    projected_h = None
    if homogeneous_M is not None and homogeneous_rho is not None:
        ambient_h = homogeneous_ambient_bound(k, homogeneous_M, homogeneous_rho, product_leaf)
        projected_h = homogeneous_projected_bound(k, homogeneous_M, homogeneous_rho, product_leaf)
    return BoundCertificate(
        root=root,
        nodes=records,
        complexity="O(|T| 3^a_max + |T| a_max log a_max); linear for bounded arity",
        homogeneous_ambient=ambient_h,
        homogeneous_projected=projected_h,
    )


def homogeneous_ambient_bound(k: int, M: float, rho: float, leaf_product: float = 1.0) -> float:
    if k < 0 or min(M, rho, leaf_product) < 0.0:
        raise ValueError("bound parameters must be nonnegative")
    if k == 0:
        return 0.0
    return float(k * rho * M ** (k - 1) * leaf_product)


def homogeneous_projected_bound(
    k: int, M: float, rho: float, leaf_product: float = 1.0
) -> float:
    """Universal projected-root theorem; the root residual is absent."""

    if k < 0 or min(M, rho, leaf_product) < 0.0:
        raise ValueError("bound parameters must be nonnegative")
    if k <= 1:
        return 0.0
    return float((k - 1) * rho * M ** (k - 1) * leaf_product)


def homogeneous_normal_bound(k: int, M: float, rho: float, leaf_product: float = 1.0) -> float:
    return homogeneous_ambient_bound(k, M, rho, leaf_product)
