"""CP-factorized n-ary laws and explicit gauge handling."""

from __future__ import annotations

from itertools import permutations

import numpy as np

from ..exceptions import ShapeError
from .nary_law import NaryLaw


class CPLaw:
    """Represent ``K = sum_r o_r o a_r^(1) o ... o a_r^(n)``.

    ``output_factor`` has shape ``(d_out, rank)`` and each input factor has
    shape ``(rank, d_i)``.  Weights are stored separately to make gauge tests
    explicit.
    """

    def __init__(
        self,
        output_factor: np.ndarray,
        input_factors: list[np.ndarray] | tuple[np.ndarray, ...],
        weights: np.ndarray | None = None,
        name: str = "cp_law",
    ) -> None:
        self.output_factor = np.asarray(output_factor)
        self.input_factors = [np.asarray(a) for a in input_factors]
        if self.output_factor.ndim != 2 or not self.input_factors:
            raise ShapeError("CP factors must be a 2-D output factor and non-empty input factors")
        self.rank = int(self.output_factor.shape[1])
        self.arity = len(self.input_factors)
        if any(a.shape != (self.rank, a.shape[1]) or a.ndim != 2 for a in self.input_factors):
            raise ShapeError("input factors must have shape (rank, dimension)")
        if weights is None:
            self.weights = np.ones(self.rank, dtype=np.result_type(self.output_factor, *self.input_factors))
        else:
            self.weights = np.asarray(weights)
            if self.weights.shape != (self.rank,):
                raise ShapeError("weights must have shape (rank,)")
        self.name = name

    @property
    def output_dim(self) -> int:
        return int(self.output_factor.shape[0])

    @property
    def input_dims(self) -> tuple[int, ...]:
        return tuple(int(a.shape[1]) for a in self.input_factors)

    @property
    def dtype(self) -> np.dtype:
        return np.result_type(self.output_factor, self.weights, *self.input_factors)

    def __call__(self, *vectors: np.ndarray) -> np.ndarray:
        if len(vectors) != self.arity:
            raise ShapeError(f"expected {self.arity} inputs")
        responses = []
        for i, (factor, vector, dim) in enumerate(zip(self.input_factors, vectors, self.input_dims)):
            value = np.asarray(vector)
            if value.ndim != 1 or value.shape != (dim,):
                raise ShapeError(f"input {i} must have shape ({dim},), got {value.shape}")
            responses.append(factor @ value)
        component_values = self.weights.copy()
        for response in responses:
            component_values = component_values * response
        return self.output_factor @ component_values

    def to_dense(self) -> NaryLaw:
        tensor = np.zeros((self.output_dim, *self.input_dims), dtype=self.dtype)
        for r in range(self.rank):
            term = self.output_factor[:, r] * self.weights[r]
            for axis, factor in enumerate(self.input_factors):
                term = np.multiply.outer(term, factor[r])
            tensor += term
        return NaryLaw(tensor, self.arity, name=f"dense({self.name})")

    @classmethod
    def from_rank_one_factors(
        cls, output: np.ndarray, inputs: list[np.ndarray], weight: complex = 1.0, name: str = "rank_one_cp"
    ) -> "CPLaw":
        out = np.asarray(output).reshape(-1, 1)
        factors = [np.asarray(a).reshape(1, -1) for a in inputs]
        return cls(out, factors, np.asarray([weight]), name=name)

    @classmethod
    def from_dense(
        cls, law: NaryLaw, rank: int, seed: int = 0, iterations: int = 30
    ) -> "CPLaw":
        """Deterministic greedy CP approximation.

        The method is intentionally documented as an approximation, not a
        uniqueness theorem.  Rank-one tensors are recovered exactly up to
        floating-point arithmetic; general tensors receive a power-iteration
        residual approximation suitable for error sweeps.
        """
        if rank <= 0:
            raise ValueError("rank must be positive")
        rng = np.random.default_rng(seed)
        residual = law.tensor.astype(np.result_type(law.tensor, np.float64), copy=True)
        outputs = np.zeros((law.output_dim, rank), dtype=residual.dtype)
        inputs = [np.zeros((rank, d), dtype=residual.dtype) for d in law.input_dims]
        weights = np.zeros(rank, dtype=residual.dtype)
        for r in range(rank):
            vectors = [rng.normal(size=d) for d in residual.shape]
            vectors = [v / (np.linalg.norm(v) or 1.0) for v in vectors]
            for _ in range(iterations):
                for axis in range(residual.ndim):
                    other = np.ones_like(residual)
                    # Contract all axes except the target with current vectors.
                    contraction = residual
                    for j in reversed(range(residual.ndim)):
                        if j != axis:
                            contraction = np.tensordot(contraction, vectors[j], axes=([j if j < contraction.ndim else 0], [0]))
                    vectors[axis] = np.asarray(contraction)
                    norm = np.linalg.norm(vectors[axis])
                    if norm:
                        vectors[axis] = vectors[axis] / norm
            weight = residual
            for axis, vector in enumerate(vectors):
                weight = np.tensordot(weight, vector, axes=([0], [0]))
            weights[r] = weight
            outputs[:, r] = vectors[0]
            for j in range(law.arity):
                inputs[j][r] = vectors[j + 1]
            term = np.asarray(vectors[0]) * weight
            for vector in vectors[1:]:
                term = np.multiply.outer(term, vector)
            residual = residual - term
        return cls(outputs, inputs, weights, name=f"cp_approx({law.name})")

    def canonicalize(self) -> "CPLaw":
        out = self.output_factor.copy()
        factors = [a.copy() for a in self.input_factors]
        weights = self.weights.copy()
        for r in range(self.rank):
            norms = [np.linalg.norm(out[:, r])]
            norms.extend(np.linalg.norm(a[r]) for a in factors)
            for scale, target in zip(norms, [out, *factors]):
                if scale:
                    if target is out:
                        out[:, r] /= scale
                    else:
                        target[r] /= scale
                    weights[r] *= scale
        order = np.argsort(-np.abs(weights))
        return CPLaw(out[:, order], [a[order] for a in factors], weights[order], f"canonical({self.name})")

    def gauge_transform(self, scales: list[np.ndarray] | tuple[np.ndarray, ...]) -> "CPLaw":
        if len(scales) != self.arity + 1:
            raise ValueError("one component-wise scale vector per factor is required")
        values = [np.asarray(s) for s in scales]
        if any(s.shape != (self.rank,) for s in values):
            raise ShapeError("each gauge scale must have shape (rank,)")
        if not np.allclose(np.prod(np.stack(values), axis=0), 1.0):
            raise ValueError("gauge scales must have component-wise product one")
        out = self.output_factor * values[0][None, :]
        factors = [a * values[i + 1][:, None] for i, a in enumerate(self.input_factors)]
        return CPLaw(out, factors, self.weights.copy(), f"gauge({self.name})")

    def relative_frobenius_error(self, target: NaryLaw) -> float:
        denominator = max(np.linalg.norm(target.tensor.ravel()), np.finfo(float).eps)
        return float(np.linalg.norm(self.to_dense().tensor.ravel() - target.tensor.ravel()) / denominator)

    def factor_distance(self, other: "CPLaw") -> float:
        if self.rank != other.rank:
            raise ValueError("factor distance requires equal rank")
        a = self.canonicalize()
        b = other.canonicalize()
        return float(np.sqrt(np.linalg.norm(a.output_factor - b.output_factor) ** 2 + sum(np.linalg.norm(x - y) ** 2 for x, y in zip(a.input_factors, b.input_factors))))

    def gauge_aligned_distance(self, other: "CPLaw") -> float:
        """Minimize a simple component permutation and per-factor scale gauge."""
        if self.rank != other.rank:
            raise ValueError("gauge-aligned distance requires equal rank")
        best = float("inf")
        for order in permutations(range(self.rank)):
            candidate = CPLaw(other.output_factor[:, order], [a[list(order)] for a in other.input_factors], other.weights[list(order)])
            left = self.canonicalize()
            right = candidate.canonicalize()
            dist = left.factor_distance(right)
            best = min(best, dist)
        return best

