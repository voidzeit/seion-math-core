"""Computational control for M24/M25.

Per the project's epistemic scope, this verifies the identities and
inequalities asserted in `m24_m25_finite_batch_certificates.tex` on randomized
instances. It never substitutes for the proofs there; a failure here would
indicate an implementation or statement error, and a pass is an
implementation control only.

Deliberately self-contained: the tree, laws, projectors and both evaluations
are built here from the definitions in the .tex, not imported from the
applied campaign, so the two are independent realizations of the same
statement.

Claims checked, in the numbering of the .tex:

  Lemma 1     F_v - Rtilde_v = sum_j M_{v,j}(delta_{c_j})   (exact identity)
  Thm M24     ||delta_v|| <= B_v, per sample and per node
  Cor M24.1   max_n ||E|| <= max_n B_root
  Prop M24.2  max_n B_v <= Bbar_v   (per-sample beats batch-decoupled)
  Thm M25     ||delta_v|| <= G_v <= B_v
  Prop M24.3  B_v <= A_v            (dominance over the Frobenius rule)
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

DTYPE = np.float64


@dataclass(frozen=True)
class Node:
    node_id: str
    children: tuple                      # Node, or int (leaf index)
    dim: int


def chain(depth: int, dim: int) -> Node:
    current: Node | int = 0
    node = None
    for i in range(depth):
        node = Node(f"n{i}", (current if i > 0 else 0, i + 1), dim)
        current = node
    return node


def branching(dim: int) -> Node:
    """Two independent internal vertices feeding a common root."""
    left = Node("l", (0, 1), dim)
    right = Node("r", (2, 3), dim)
    return Node("root", (left, right), dim)


def postorder(node: Node) -> list[Node]:
    out = []
    for child in node.children:
        if isinstance(child, Node):
            out.extend(postorder(child))
    out.append(node)
    return out


def leaf_count(node: Node) -> int:
    total = 0
    for child in node.children:
        total += leaf_count(child) if isinstance(child, Node) else 1
    return total


def build_instance(root: Node, dim: int, rank: int, batch: int, rng):
    nodes = postorder(root)
    laws = {
        node.node_id: rng.standard_normal((dim,) + (dim,) * len(node.children)).astype(DTYPE)
        / np.sqrt(dim ** len(node.children))
        for node in nodes
    }
    projectors = {}
    for node in nodes:
        basis = np.linalg.qr(rng.standard_normal((dim, dim)))[0]
        retained = basis[:, :rank]
        projectors[node.node_id] = retained @ retained.T
    leaves = [rng.standard_normal((batch, dim)).astype(DTYPE) for _ in range(leaf_count(root))]
    return nodes, laws, projectors, leaves


def apply_law(tensor: np.ndarray, child_values: list[np.ndarray]) -> np.ndarray:
    letters = "abcdefgh"[: len(child_values)]
    spec = ",".join(f"N{c}" for c in letters)
    return np.einsum(f"Z{letters},{spec}->NZ", tensor, *child_values)


def evaluate(root: Node, laws, projectors, leaves):
    """Ambient F, raw reduced Rtilde, and the value each parent receives R."""
    F, Rtilde, R = {}, {}, {}

    def visit(item, reduced: bool):
        if isinstance(item, int):
            return leaves[item]
        return (R if reduced else F)[item.node_id]

    for node in postorder(root):
        F[node.node_id] = apply_law(laws[node.node_id], [visit(c, False) for c in node.children])
        Rtilde[node.node_id] = apply_law(laws[node.node_id], [visit(c, True) for c in node.children])
        R[node.node_id] = (
            Rtilde[node.node_id] if node.node_id == root.node_id
            else Rtilde[node.node_id] @ projectors[node.node_id].T
        )
    return F, Rtilde, R


def slot_map(tensor: np.ndarray, slot_inputs: list[np.ndarray], slot: int) -> np.ndarray:
    """Per-sample matrix of equation (1)."""
    letters = "abcdefgh"[: len(slot_inputs)]
    others = [j for j in range(len(slot_inputs)) if j != slot]
    specs = [f"Z{letters}"] + [f"N{letters[j]}" for j in others]
    operands = [tensor] + [slot_inputs[j] for j in others]
    return np.einsum(",".join(specs) + f"->NZ{letters[slot]}", *operands)


def top_singular(maps: np.ndarray) -> np.ndarray:
    return np.linalg.svd(maps, compute_uv=False)[:, 0]


def certificates(root: Node, laws, projectors, leaves, *, tol: float = 1e-9) -> dict:
    F, Rtilde, R = evaluate(root, laws, projectors, leaves)
    batch = leaves[0].shape[0]
    dim = root.dim

    delta = {}                                   # per-sample error vectors
    for node in postorder(root):
        if node.node_id != root.node_id:
            delta[node.node_id] = F[node.node_id] - R[node.node_id]
    for index in range(len(leaves)):
        delta[str(index)] = np.zeros_like(leaves[index])

    B, G = {}, {}                                # per-sample bounds
    Bbar, A, U = {}, {}, {}                      # batch-decoupled, Frobenius, value bounds
    for index, leaf in enumerate(leaves):
        B[str(index)] = np.zeros(batch)
        G[str(index)] = np.zeros(batch)
        Bbar[str(index)] = 0.0
        A[str(index)] = 0.0
        U[str(index)] = float(np.max(np.linalg.norm(leaf, axis=1)))

    lemma1_residual = 0.0
    for node in postorder(root):
        is_root = node.node_id == root.node_id
        tensor = laws[node.node_id]
        exact = [leaves[c] if isinstance(c, int) else F[c.node_id] for c in node.children]
        fed = [leaves[c] if isinstance(c, int) else R[c.node_id] for c in node.children]
        normal = np.eye(dim) - (np.zeros((dim, dim)) if is_root else projectors[node.node_id])

        telescoped = np.zeros((batch, dim))
        p = np.zeros(batch)
        pi = np.zeros(batch)
        nu = np.zeros(batch)
        pbar = 0.0
        a_bound = 0.0
        core_frobenius = float(np.linalg.norm(tensor.ravel()))
        for slot, child in enumerate(node.children):
            slot_inputs = [fed[j] if j < slot else exact[j] for j in range(len(node.children))]
            maps = slot_map(tensor, slot_inputs, slot)
            child_id = str(child) if isinstance(child, int) else child.node_id
            telescoped += np.einsum("NZa,Na->NZ", maps, delta[child_id])
            gains = top_singular(maps)
            p += gains * B[child_id]
            pi += gains * G[child_id]
            nu += top_singular(np.einsum("ZY,NYa->NZa", normal, maps)) * G[child_id]
            pbar += float(np.max(gains)) * Bbar[child_id]
            others = [U[str(c) if isinstance(c, int) else c.node_id]
                      for j, c in enumerate(node.children) if j != slot]
            a_bound += core_frobenius * float(np.prod(others)) * A[child_id]

        # Lemma 1 is an identity, so this residual must be at rounding level.
        lemma1_residual = max(lemma1_residual, float(np.max(np.abs(
            (F[node.node_id] - Rtilde[node.node_id]) - telescoped
        ))))

        U[node.node_id] = core_frobenius * float(np.prod(
            [U[str(c) if isinstance(c, int) else c.node_id] for c in node.children]
        ))
        if is_root:
            B[node.node_id], G[node.node_id] = p, pi
            Bbar[node.node_id], A[node.node_id] = pbar, a_bound
        else:
            gamma = np.linalg.norm(Rtilde[node.node_id] - R[node.node_id], axis=1)
            kappa = np.minimum(nu, pi)
            B[node.node_id] = p + gamma
            G[node.node_id] = np.sqrt(pi**2 + gamma**2 + 2.0 * kappa * gamma)
            Bbar[node.node_id] = pbar + float(np.max(gamma))
            A[node.node_id] = a_bound + float(np.max(gamma))

    checks = {"lemma1_max_residual": lemma1_residual, "violations": []}
    for node in postorder(root):
        key = node.node_id
        actual = (np.linalg.norm(F[key] - Rtilde[key], axis=1) if key == root.node_id
                  else np.linalg.norm(delta[key], axis=1))
        if np.any(actual > B[key] + tol):
            checks["violations"].append(("M24", key))
        if np.any(actual > G[key] + tol):
            checks["violations"].append(("M25_sound", key))
        if np.any(G[key] > B[key] + tol):
            checks["violations"].append(("M25_ordering", key))
        if float(np.max(B[key])) > Bbar[key] + tol:
            checks["violations"].append(("M24.2", key))
        if float(np.max(B[key])) > A[key] + tol:
            checks["violations"].append(("M24.3", key))

    root_id = root.node_id
    checks.update({
        "root_actual": float(np.max(np.linalg.norm(F[root_id] - Rtilde[root_id], axis=1))),
        "root_G": float(np.max(G[root_id])),
        "root_B": float(np.max(B[root_id])),
        "root_Bbar": float(Bbar[root_id]),
        "root_A": float(A[root_id]),
    })
    return checks


def sweep(seeds: int = 30) -> list[dict]:
    out = []
    for seed in range(seeds):
        rng = np.random.default_rng(seed)
        dim = int(rng.integers(3, 7))
        rank = int(rng.integers(1, dim + 1))
        depth = int(rng.integers(1, 8))
        root = chain(depth, dim) if seed % 2 == 0 else branching(dim)
        nodes, laws, projectors, leaves = build_instance(root, dim, rank, 64, rng)
        result = certificates(root, laws, projectors, leaves)
        result.update({"seed": seed, "dim": dim, "rank": rank,
                       "topology": "chain" if seed % 2 == 0 else "branching"})
        out.append(result)
    return out


def main() -> None:
    results = sweep()
    failures = [r for r in results if r["violations"]]
    worst_residual = max(r["lemma1_max_residual"] for r in results)
    print(f"instances: {len(results)}")
    print(f"Lemma 1 max residual over all instances: {worst_residual:.3e}")
    print(f"instances with any violation: {len(failures)}")
    for r in failures:
        print("   ", r["seed"], r["violations"])
    print("\nroot chain (must be nondecreasing left to right):")
    print(f"{'seed':>5} {'topology':>10} {'actual':>11} {'G (M25)':>11} "
          f"{'B (M24)':>11} {'Bbar':>11} {'A':>11}")
    for r in results[:10]:
        print(f"{r['seed']:5d} {r['topology']:>10} {r['root_actual']:11.4e} "
              f"{r['root_G']:11.4e} {r['root_B']:11.4e} {r['root_Bbar']:11.4e} "
              f"{r['root_A']:11.4e}")
    assert not failures, "certificate claim violated"
    assert worst_residual < 1e-9, "Lemma 1 is not an identity in this implementation"
    print("\nAll asserted inequalities held; Lemma 1 exact to rounding.")


if __name__ == "__main__":
    main()
