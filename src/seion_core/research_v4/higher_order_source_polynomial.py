"""Exact higher-order source provenance for small multilinear DAGs.

P6B represents each local source as a fixed vector multiplied by a formal
scalar amplitude.  Coefficients are therefore concrete output vectors, while
the multi-index records how many times every labelled source occurs.  This is
an exact finite polynomial for the declared numeric DAG, not a truncation or a
claim about an infinite formal series.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Mapping

import numpy as np


Array = np.ndarray
MultiIndex = tuple[tuple[str, int], ...]
MultilinearLaw = Callable[..., Array]


def _canonical_multiindex(counts: Mapping[str, int]) -> MultiIndex:
    return tuple(sorted((source_id, count) for source_id, count in counts.items() if count))


def _merge_multiindices(left: MultiIndex, right: MultiIndex) -> MultiIndex:
    counts: dict[str, int] = dict(left)
    for source_id, count in right:
        counts[source_id] = counts.get(source_id, 0) + count
    return _canonical_multiindex(counts)


def multiindex_degree(index: MultiIndex) -> int:
    return sum(count for _, count in index)


def _add_coefficients(target: dict[MultiIndex, Array], index: MultiIndex, value: Array) -> None:
    if index in target:
        target[index] = target[index] + value
    else:
        target[index] = np.array(value, copy=True)


def _numeric_vector(value: Array, *, name: str, dimension: int) -> Array:
    vector = np.asarray(value)
    if vector.ndim != 1 or vector.shape[0] != dimension:
        raise ValueError(f"{name} must be a numeric vector of dimension {dimension}")
    if not np.issubdtype(vector.dtype, np.number):
        raise TypeError(f"{name} must have a numeric dtype")
    return np.array(vector, copy=True)


def _numeric_matrix(value: Array, *, name: str, dimension: int) -> Array:
    matrix = np.asarray(value)
    if matrix.ndim != 2 or matrix.shape != (dimension, dimension):
        raise ValueError(f"{name} must be a square matrix of shape {(dimension, dimension)}")
    if not np.issubdtype(matrix.dtype, np.number):
        raise TypeError(f"{name} must have a numeric dtype")
    return np.array(matrix, copy=True)


@dataclass(frozen=True, slots=True)
class PolynomialDAGNode:
    """A leaf or internal node of a finite typed multilinear DAG.

    ``baseline`` is required only for leaves and is the recursively projected
    state at that leaf.  Internal nodes compute their projected baseline from
    their children.  ``local_sources`` injects fixed source vectors into the
    node's error polynomial; amplitudes are supplied later to ``evaluate``.
    ``projector`` defaults to the identity.
    """

    node_id: str
    dimension: int
    inputs: tuple[str, ...] = ()
    law: MultilinearLaw | None = None
    baseline: Array | None = None
    projector: Array | None = None
    local_sources: Mapping[str, Array] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.node_id:
            raise ValueError("DAG node ids must be nonempty")
        if self.dimension <= 0:
            raise ValueError("node dimensions must be positive")
        if self.inputs and self.law is None:
            raise ValueError("internal nodes require a multilinear law")
        if not self.inputs and self.law is not None:
            raise ValueError("leaf nodes cannot have a multilinear law")
        if self.inputs and self.baseline is not None:
            raise ValueError("internal node baselines are computed from children")
        if not self.inputs and self.baseline is None:
            raise ValueError("leaf nodes require a baseline vector")
        if self.baseline is not None:
            object.__setattr__(self, "baseline", _numeric_vector(self.baseline, name="baseline", dimension=self.dimension))
        matrix = np.eye(self.dimension) if self.projector is None else _numeric_matrix(
            self.projector, name="projector", dimension=self.dimension
        )
        object.__setattr__(self, "projector", matrix)
        normalized_sources: dict[str, Array] = {}
        for source_id, vector in self.local_sources.items():
            if not source_id:
                raise ValueError("source ids must be nonempty")
            normalized_sources[source_id] = _numeric_vector(
                vector, name=f"local source {source_id!r}", dimension=self.dimension
            )
        object.__setattr__(self, "local_sources", normalized_sources)


@dataclass(frozen=True, slots=True)
class SourcePolynomial:
    """Finite vector-valued polynomial indexed by source multiplicities."""

    dimension: int
    coefficients: Mapping[MultiIndex, Array]

    def __post_init__(self) -> None:
        if self.dimension <= 0:
            raise ValueError("polynomial dimension must be positive")
        normalized: dict[MultiIndex, Array] = {}
        for index, coefficient in self.coefficients.items():
            canonical = _canonical_multiindex(dict(index))
            if any(count <= 0 for _, count in canonical):
                raise ValueError("multi-index counts must be positive")
            normalized[canonical] = _numeric_vector(
                coefficient, name=f"coefficient {canonical!r}", dimension=self.dimension
            )
        object.__setattr__(self, "coefficients", normalized)

    @property
    def degree(self) -> int:
        return max((multiindex_degree(index) for index in self.coefficients), default=0)

    def evaluate(self, amplitudes: Mapping[str, complex | float] | None = None) -> Array:
        values = amplitudes or {}
        result = np.zeros(self.dimension, dtype=np.result_type(*self.coefficients.values(), float))
        for index, coefficient in self.coefficients.items():
            monomial = 1.0
            for source_id, count in index:
                if source_id not in values:
                    raise ValueError(f"missing amplitude for source {source_id!r}")
                monomial *= values[source_id] ** count
            result = result + monomial * coefficient
        return result

    def truncate(self, order: int, amplitudes: Mapping[str, complex | float] | None = None) -> "TruncationResult":
        if order < 0:
            raise ValueError("truncation order must be nonnegative")
        retained = {
            index: coefficient
            for index, coefficient in self.coefficients.items()
            if multiindex_degree(index) <= order
        }
        omitted = {
            index: coefficient
            for index, coefficient in self.coefficients.items()
            if multiindex_degree(index) > order
        }
        values = amplitudes or {}
        remainder_bound = 0.0
        for index, coefficient in omitted.items():
            monomial = 1.0
            for source_id, count in index:
                if source_id not in values:
                    raise ValueError(f"missing amplitude for source {source_id!r}")
                monomial *= abs(values[source_id]) ** count
            remainder_bound += float(np.linalg.norm(coefficient)) * monomial
        return TruncationResult(
            order=order,
            retained=SourcePolynomial(self.dimension, retained),
            omitted_terms=len(omitted),
            remainder_bound=remainder_bound,
        )


@dataclass(frozen=True, slots=True)
class TruncationResult:
    order: int
    retained: SourcePolynomial
    omitted_terms: int
    remainder_bound: float

    def evaluate(self, amplitudes: Mapping[str, complex | float] | None = None) -> Array:
        return self.retained.evaluate(amplitudes)


@dataclass(frozen=True, slots=True)
class SourcePolynomialCertificate:
    root: str
    topological_order: tuple[str, ...]
    baseline_states: Mapping[str, Array]
    node_polynomials: Mapping[str, SourcePolynomial]
    output_polynomial: SourcePolynomial
    projected_output: bool
    reference_checked: bool
    complexity: str = "exact finite polynomial; topological graph traversal with coefficient convolution"


def _validate_graph(nodes: Mapping[str, PolynomialDAGNode], root: str) -> tuple[str, ...]:
    if not nodes:
        raise ValueError("DAG must contain at least one node")
    if root not in nodes:
        raise ValueError(f"unknown root {root!r}")
    indegree = {node_id: 0 for node_id in nodes}
    outgoing: dict[str, list[str]] = {node_id: [] for node_id in nodes}
    for node in nodes.values():
        for input_id in node.inputs:
            if input_id not in nodes:
                raise ValueError(f"unknown input node {input_id!r}")
            if nodes[input_id].dimension != node.dimension:
                raise ValueError(
                    f"input {input_id!r} dimension {nodes[input_id].dimension} does not match "
                    f"node {node.node_id!r} dimension {node.dimension}"
                )
            indegree[node.node_id] += 1
            outgoing[input_id].append(node.node_id)
    ready = sorted(node_id for node_id, degree in indegree.items() if degree == 0)
    order: list[str] = []
    while ready:
        node_id = ready.pop(0)
        order.append(node_id)
        for target in sorted(outgoing[node_id]):
            indegree[target] -= 1
            if indegree[target] == 0:
                ready.append(target)
                ready.sort()
    if len(order) != len(nodes):
        raise ValueError("dependency graph contains a cycle")
    return tuple(order)


def _multilinear_expand(law: MultilinearLaw, slot_terms: list[Mapping[MultiIndex, Array]], dimension: int) -> SourcePolynomial:
    coefficients: dict[MultiIndex, Array] = {(): np.zeros(dimension, dtype=float)}
    for choices in _cartesian_terms(slot_terms):
        index = ()
        vectors: list[Array] = []
        for choice_index, vector in choices:
            index = _merge_multiindices(index, choice_index)
            vectors.append(vector)
        value = np.asarray(law(*vectors))
        if value.ndim != 1 or value.shape[0] != dimension:
            raise ValueError("multilinear law returned a vector with the wrong dimension")
        _add_coefficients(coefficients, index, value)
    return SourcePolynomial(dimension, coefficients)


def _cartesian_terms(slot_terms: list[Mapping[MultiIndex, Array]]):
    if not slot_terms:
        yield ()
        return
    first, *rest = slot_terms
    for index, vector in first.items():
        if rest:
            for tail in _cartesian_terms(rest):
                yield ((index, vector),) + tail
        else:
            yield ((index, vector),)


def _add_local_sources(polynomial: SourcePolynomial, node: PolynomialDAGNode) -> SourcePolynomial:
    coefficients = dict(polynomial.coefficients)
    for source_id, vector in node.local_sources.items():
        _add_coefficients(coefficients, ((source_id, 1),), vector)
    return SourcePolynomial(node.dimension, coefficients)


def _build_node(node: PolynomialDAGNode, child_baselines: list[Array], child_polynomials: list[SourcePolynomial]) -> tuple[Array, SourcePolynomial]:
    if not node.inputs:
        return np.array(node.baseline, copy=True), _add_local_sources(SourcePolynomial(node.dimension, {}), node)

    assert node.law is not None
    slot_terms: list[dict[MultiIndex, Array]] = []
    for baseline, polynomial in zip(child_baselines, child_polynomials):
        terms = {(): baseline}
        terms.update(polynomial.coefficients)
        slot_terms.append(terms)
    raw = _multilinear_expand(node.law, slot_terms, node.dimension)
    raw_baseline = raw.coefficients[()]
    projected_baseline = node.projector @ raw_baseline
    nonconstant = {index: coefficient for index, coefficient in raw.coefficients.items() if index}
    closure_residual = raw_baseline - projected_baseline
    if not np.allclose(closure_residual, 0.0, atol=0.0, rtol=0.0):
        _add_coefficients(nonconstant, ((f"closure:{node.node_id}", 1),), closure_residual)
    return projected_baseline, _add_local_sources(SourcePolynomial(node.dimension, nonconstant), node)


def _project_polynomial(polynomial: SourcePolynomial, projector: Array) -> SourcePolynomial:
    coefficients: dict[MultiIndex, Array] = {}
    for index, coefficient in polynomial.coefficients.items():
        projected = projector @ coefficient
        if np.allclose(projected, 0.0, atol=1.0e-12, rtol=1.0e-12):
            continue
        coefficients[index] = projected
    return SourcePolynomial(polynomial.dimension, coefficients)


def _evaluate_topological(nodes: Mapping[str, PolynomialDAGNode], root: str) -> tuple[tuple[str, ...], dict[str, Array], dict[str, SourcePolynomial]]:
    order = _validate_graph(nodes, root)
    baselines: dict[str, Array] = {}
    polynomials: dict[str, SourcePolynomial] = {}
    for node_id in order:
        node = nodes[node_id]
        child_baselines = [baselines[input_id] for input_id in node.inputs]
        child_polynomials = [polynomials[input_id] for input_id in node.inputs]
        baselines[node_id], polynomials[node_id] = _build_node(node, child_baselines, child_polynomials)
    return order, baselines, polynomials


def _evaluate_reference(
    nodes: Mapping[str, PolynomialDAGNode], node_id: str, visiting: set[str]
) -> tuple[Array, SourcePolynomial]:
    if node_id in visiting:
        raise ValueError("dependency graph contains a cycle")
    visiting.add(node_id)
    node = nodes[node_id]
    children = [_evaluate_reference(nodes, input_id, visiting) for input_id in node.inputs]
    visiting.remove(node_id)
    return _build_node(node, [baseline for baseline, _ in children], [polynomial for _, polynomial in children])


def certify_source_polynomial_dag(
    nodes: Mapping[str, PolynomialDAGNode],
    root: str,
    *,
    project_output: bool = True,
    check_reference: bool = True,
) -> SourcePolynomialCertificate:
    """Compute the exact finite source polynomial once per DAG node.

    The cached topological implementation preserves shared subexpressions.
    ``check_reference=True`` additionally computes the same root by recursively
    unrolling dependencies and verifies coefficient-by-coefficient equality;
    this is a deliberately slow validation path for small adversarial DAGs.
    """

    order, baselines, polynomials = _evaluate_topological(nodes, root)
    root_polynomial = polynomials[root]
    reference_checked = False
    if check_reference:
        reference_baseline, reference_polynomial = _evaluate_reference(nodes, root, set())
        if not np.allclose(reference_baseline, baselines[root], atol=1.0e-11, rtol=1.0e-11):
            raise AssertionError("topological and recursive baseline states disagree")
        if set(reference_polynomial.coefficients) != set(root_polynomial.coefficients):
            raise AssertionError("topological and recursive source polynomial supports disagree")
        for index in root_polynomial.coefficients:
            if not np.allclose(
                reference_polynomial.coefficients[index], root_polynomial.coefficients[index], atol=1.0e-11, rtol=1.0e-11
            ):
                raise AssertionError(f"topological and recursive coefficients disagree for {index!r}")
        reference_checked = True

    output = _project_polynomial(root_polynomial, nodes[root].projector) if project_output else root_polynomial
    return SourcePolynomialCertificate(
        root=root,
        topological_order=order,
        baseline_states=baselines,
        node_polynomials=polynomials,
        output_polynomial=output,
        projected_output=project_output,
        reference_checked=reference_checked,
    )
