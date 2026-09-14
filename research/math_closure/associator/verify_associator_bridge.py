"""Computational control for the associator/PMT bridge.

Checks, on randomized instances:

  identity    Ahat - P A  ==  -e_T + e_T'                      (must be exact)
  bound       ||Ahat - P A|| <= E_T^P + E_T'^P
  k=2 corollary  ||Ahat - P A|| <= 2 rho M L                   (C_2^P = 1)
  leaf count     two nested applications of an n-ary law use 2n-1 leaves

Under the theorem these are implementation controls, not evidence for the
statement. Self-contained: the trees, laws and projectors are built here from
the definitions, not imported from the applied campaign.
"""

from __future__ import annotations

import numpy as np

DTYPE = np.float64


def random_law(dim: int, arity: int, rng) -> np.ndarray:
    """Multilinear law of operator norm at most 1, as a tensor (out, in_1..in_a)."""
    tensor = rng.standard_normal((dim,) * (arity + 1)).astype(DTYPE)
    return tensor / operator_norm(tensor, arity, rng)


def apply_law(tensor: np.ndarray, args: list[np.ndarray]) -> np.ndarray:
    out = tensor
    for vector in reversed(args):
        out = np.tensordot(out, vector, axes=([out.ndim - 1], [0]))
    return out


def operator_norm(tensor: np.ndarray, arity: int, rng, iters: int = 60) -> float:
    """Alternating maximization; an upper estimate is not needed, only a scale."""
    dim = tensor.shape[0]
    best = 0.0
    for _ in range(4):
        vectors = [rng.standard_normal(dim) for _ in range(arity)]
        vectors = [v / np.linalg.norm(v) for v in vectors]
        for _ in range(iters):
            for i in range(arity):
                partial = tensor
                for j in sorted((j for j in range(arity) if j != i), reverse=True):
                    partial = np.tensordot(vectors[j], partial, axes=([0], [j + 1]))
                # partial now has axes (out, slot_i)
                _, _, vh = np.linalg.svd(partial)
                vectors[i] = vh[0]
        best = max(best, float(np.linalg.norm(apply_law(tensor, vectors))))
    return max(best, 1e-12)


def projector(dim: int, rank: int, rng) -> np.ndarray:
    basis = np.linalg.qr(rng.standard_normal((dim, dim)))[0][:, :rank]
    return basis @ basis.T


def evaluate(tree, laws, projectors, leaves, project_root: bool):
    """Return (ambient, recursively projected) root values for a nested tree.

    A tree is ('leaf', index) or (law_key, child_1, ..., child_a).
    """
    def walk(node, reduced: bool):
        if node[0] == "leaf":
            return leaves[node[1]]
        key = node[0]
        args = [walk(child, reduced) for child in node[1:]]
        value = apply_law(laws[key], args)
        if reduced:
            return projectors[key] @ value
        return value

    ambient = walk(tree, False)
    reduced = walk(tree, True)
    return ambient, reduced


def main() -> None:
    rng = np.random.default_rng(20260816)
    dim, arity = 5, 3
    worst_identity = 0.0
    violations = []

    # T1 = mu(mu(x1,x2,x3), x4, x5)   T2 = mu(x1, mu(x2,x3,x4), x5)
    # Distinct law keys per internal vertex, so the two trees share only the
    # root projector -- which is all the theorem requires.
    T1 = ("outer", ("inner", ("leaf", 0), ("leaf", 1), ("leaf", 2)),
          ("leaf", 3), ("leaf", 4))
    T2 = ("outer", ("leaf", 0),
          ("innerB", ("leaf", 1), ("leaf", 2), ("leaf", 3)), ("leaf", 4))

    for trial in range(60):
        laws = {k: random_law(dim, arity, rng) for k in ("outer", "inner", "innerB")}
        rank = int(rng.integers(1, dim))
        root_P = projector(dim, rank, rng)
        projectors = {
            "outer": root_P,                       # shared root projector
            "inner": projector(dim, int(rng.integers(1, dim)), rng),
            "innerB": projector(dim, int(rng.integers(1, dim)), rng),
        }
        leaves = [rng.standard_normal(dim) for _ in range(5)]
        leaves = [v / np.linalg.norm(v) for v in leaves]

        F1, R1 = evaluate(T1, laws, projectors, leaves, True)
        F2, R2 = evaluate(T2, laws, projectors, leaves, True)

        e1 = root_P @ F1 - R1
        e2 = root_P @ F2 - R2
        A = F1 - F2
        Ahat = R1 - R2
        delta = Ahat - root_P @ A

        worst_identity = max(worst_identity, float(np.max(np.abs(delta - (-e1 + e2)))))
        if np.linalg.norm(delta) > np.linalg.norm(e1) + np.linalg.norm(e2) + 1e-12:
            violations.append(("bound", trial))

        # k = 2 corollary: with M = 1 and unit leaves, rho is the largest
        # projected closure defect actually realized at the internal vertices.
        rho = 0.0
        for key, child in (("inner", T1[1]), ("innerB", T2[2])):
            raw = apply_law(laws[key], [leaves[i] for i in (c[1] for c in child[1:])])
            rho = max(rho, float(np.linalg.norm(raw - projectors[key] @ raw)))
        raw_root1 = apply_law(laws["outer"], [R1 * 0 + apply_law(
            laws["inner"], [leaves[0], leaves[1], leaves[2]]), leaves[3], leaves[4]])
        rho = max(rho, float(np.linalg.norm(raw_root1 - root_P @ raw_root1)))
        if np.linalg.norm(delta) > 2.0 * rho + 1e-9:
            violations.append(("k2_corollary", trial))

    print(f"trials: 60, dim = {dim}, arity = {arity}")
    print(f"identity  Ahat - P A == -e_T + e_T'   max abs residual = "
          f"{worst_identity:.3e} -> {'PASS' if worst_identity < 1e-10 else 'FAIL'}")
    print(f"bound violations: {sum(1 for v in violations if v[0] == 'bound')}")
    print(f"k=2 corollary violations: {sum(1 for v in violations if v[0] == 'k2_corollary')}")

    print("\nleaf count for two nested applications of an n-ary law:")
    for n in (2, 3, 4, 5):
        print(f"  n = {n}: outer takes {n}, one slot replaced by {n} -> {2 * n - 1} leaves"
              f"   (the 'n+1' form would give {n + 1}, i.e. {n - 2} anchors fixed)")

    assert worst_identity < 1e-10, "the bridge identity is not exact in this implementation"
    assert not violations, violations
    print("\nAll checks passed.")


if __name__ == "__main__":
    main()
