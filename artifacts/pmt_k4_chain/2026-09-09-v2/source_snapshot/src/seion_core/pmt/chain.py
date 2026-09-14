"""Source-resolved independent-law chains; numerical checks are not proofs.

The initial space has the identity projector (ambient leaf convention).
Every subsequent closure check is the spectral norm on the WHOLE reduced
input space. See research/math_closure/k4_exploration/CHAIN_GRAM_REPORT.md.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .model import PMTModel
from seion_core.research_v3.local_constants import TypedLaw
from seion_core.research_v3.typed_tree import Leaf, Node
from seion_core.research_v3.types import TypedSpace, TypeSystem


def gram(columns: np.ndarray) -> np.ndarray:
    return columns.conj().T @ columns


@dataclass(frozen=True)
class ChainTrace:
    ambient: tuple[np.ndarray, ...]
    reduced: tuple[np.ndarray, ...]
    sources: tuple[np.ndarray, ...]
    grams: tuple[np.ndarray, ...]
    projected_grams: tuple[np.ndarray, ...]
    normal_grams: tuple[np.ndarray, ...]
    projected_error: float
    source_sum_residual: float


def _validate(operators, projectors, x):
    if not operators or len(operators) != len(projectors):
        raise ValueError("provide equal nonempty operator/projector lists")
    x = np.asarray(x)
    if x.ndim != 1 or not np.all(np.isfinite(x)):
        raise ValueError("initial input must be a finite vector")
    dimension = len(x)
    for a, p in zip(operators, projectors):
        if a.ndim != 2 or a.shape[1] != dimension or p.shape != (a.shape[0],) * 2:
            raise ValueError("incompatible chain dimensions")
        if not np.all(np.isfinite(a)) or not np.all(np.isfinite(p)):
            raise ValueError("chain matrices must be finite")
        dimension = a.shape[0]


def evaluate_chain(operators, projectors, x) -> ChainTrace:
    """Trace u_i=A_j...A_(i+1)d_i and both projected/normal Gram blocks."""
    operators = tuple(np.asarray(a) for a in operators)
    projectors = tuple(np.asarray(p) for p in projectors)
    _validate(operators, projectors, x)
    f = r = np.asarray(x)
    u = np.zeros((len(x), 0), dtype=np.result_type(x, *operators, *projectors))
    fs, rs, sources, grams, gps, gqs = [], [], [], [], [], []
    residual = 0.0
    for a, p in zip(operators, projectors):
        raw = a @ r
        d = raw - p @ raw
        u = np.column_stack((a @ u, d))
        f, r = a @ f, p @ raw
        state = np.column_stack((r, u))
        fs.append(f)
        rs.append(r)
        sources.append(u)
        grams.append(gram(u))
        gps.append(gram(p @ state))
        gqs.append(gram(state - p @ state))
        residual = max(residual, float(np.linalg.norm(f - r - u.sum(axis=1))))
    return ChainTrace(tuple(fs), tuple(rs), tuple(sources), tuple(grams), tuple(gps),
                      tuple(gqs), float(np.linalg.norm(projectors[-1] @ f - r)), residual)


def audit_chain(operators, projectors, x, eta: float, tolerance: float = 1e-10) -> dict:
    """Full matrix checks, in floating point; never emits CERTIFIED_WITNESS."""
    if not np.isfinite(eta) or not 0 < eta <= 1 or tolerance <= 0:
        raise ValueError("require 0 < eta <= 1 and positive tolerance")
    operators = tuple(np.asarray(a) for a in operators)
    projectors = tuple(np.asarray(p) for p in projectors)
    _validate(operators, projectors, x)
    previous = np.eye(len(x))
    records = []
    for a, p in zip(operators, projectors):
        records.append({
            "operator_norm": float(np.linalg.norm(a, 2)),
            "projected_closure_norm": float(np.linalg.norm((np.eye(len(p)) - p) @ a @ previous, 2)),
            "projector_hermitian_residual": float(np.linalg.norm(p - p.conj().T, 2)),
            "projector_idempotent_residual": float(np.linalg.norm(p @ p - p, 2)),
        })
        previous = p
    feasible = np.linalg.norm(x) <= 1 + tolerance and all(
        row["operator_norm"] <= 1 + tolerance
        and row["projected_closure_norm"] <= eta + tolerance
        and row["projector_hermitian_residual"] <= tolerance
        and row["projector_idempotent_residual"] <= tolerance
        for row in records
    )
    trace = evaluate_chain(operators, projectors, x)
    return {"status": "NUMERICAL_CANDIDATE" if feasible else "REJECTED_INADMISSIBLE",
            "globally_checked_in_floating_point": bool(feasible), "stages": records,
            "tolerance": tolerance, "projected_error": trace.projected_error,
            "normalized_error": trace.projected_error / eta,
            "source_sum_residual": trace.source_sum_residual}


def chain_as_pmt(operators, projectors, x) -> tuple[PMTModel, dict]:
    """Exact algebraic lift mu_j(z,t)=t A_j z with scalar unit sibling leaves."""
    operators = tuple(np.asarray(a) for a in operators)
    projectors = tuple(np.asarray(p) for p in projectors)
    _validate(operators, projectors, x)
    field = "complex" if any(np.iscomplexobj(v) for v in (*operators, *projectors, x)) else "real"
    spaces = [TypedSpace.coordinate("leaf", len(x), len(x), field=field),
              TypedSpace.coordinate("gate", 1, 1, field=field)]
    laws, leaves = {}, {0: np.asarray(x)}
    tree, previous = Leaf(0, "leaf"), "leaf"
    for j, (a, p) in enumerate(zip(operators, projectors), 1):
        if not np.allclose(p, p.conj().T, atol=1e-12, rtol=0) or not np.allclose(p @ p, p, atol=1e-12, rtol=0):
            raise ValueError("orthogonal projector required for the typed lift")
        eig, vec = np.linalg.eigh(p)
        q = vec[:, eig > .5]
        if q.shape[1] == 0:
            raise ValueError("typed API requires a nonzero projector; pad an unused range direction")
        name, law_id = f"h{j}", f"a{j}"
        spaces.append(TypedSpace(name, len(p), q, field=field))
        laws[law_id] = TypedLaw(law_id, (previous, "gate"), name, a[:, :, None])
        tree = Node(law_id, name, (tree, Leaf(j, "gate")))
        leaves[j] = np.ones(1)
        previous = name
    return PMTModel(tree, TypeSystem(spaces), laws), leaves


def planar_chain(leakages, *, readout: str = "error"):
    """Analytic family: rank-one first map, planar rotations, root readout.

    With three equal active leakages t, E^2=t^2(9-15t^2+7t^4).
    'phase' reads the normal coordinate, reproducing the gated phase baseline.
    """
    ts = np.asarray(leakages, dtype=float)
    if ts.ndim != 1 or len(ts) == 0 or not np.all(np.isfinite(ts)) or np.any(abs(ts) > 1):
        raise ValueError("leakages must be a nonempty finite list in [-1,1]")
    if readout not in {"error", "phase"}:
        raise ValueError("readout must be error or phase")
    p = np.diag([1., 0.])
    x = np.array([1.])
    operators = [np.array([[np.sqrt(1 - ts[0]**2)], [ts[0]]])]
    for t in ts[1:]:
        c = np.sqrt(1 - t*t)
        operators.append(np.array([[c, -t], [t, c]]))
    projectors = [p.copy() for _ in ts]
    trace = evaluate_chain(operators, projectors, x)
    error = trace.ambient[-1] - trace.reduced[-1]
    direction = np.array([0., 1.]) if readout == "phase" else error
    norm = np.linalg.norm(direction)
    direction = direction / norm if norm else np.array([1., 0.])
    operators.append(np.outer(np.array([1., 0.]), direction))
    projectors.append(p.copy())
    return operators, projectors, x
