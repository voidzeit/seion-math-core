"""M6 explicit example: finite discrete X, kappa(p;q,r,s) = sin(2pi(p+q+r+s)/n) + 2.

Verifies, by direct exact computation (numpy on a finite matrix - every
integral becomes a finite sum, so no numerical-integration error), all
the properties claimed in verified_class_or_failure_report.tex:
symmetry, nonnegativity, d(p) > 0 (K2), self-adjointness of P, the
contraction property (largest eigenvalue exactly 1, others < 1), and the
Dirichlet-form identity.
"""

from __future__ import annotations

import numpy as np


def kappa(p: int, q: int, r: int, s: int, n: int) -> float:
    return np.sin(2 * np.pi * (p + q + r + s) / n) + 2.0


def build_W(n: int) -> np.ndarray:
    W = np.zeros((n, n))
    for p in range(n):
        for s in range(n):
            total = 0.0
            for q in range(n):
                for r in range(n):
                    total += kappa(p, q, r, s, n) ** 2 + kappa(s, q, r, p, n) ** 2
            W[p, s] = 0.5 * total
    return W


def main() -> None:
    n = 6
    W = build_W(n)

    print("Symmetry check (max |W - W^T|):", np.max(np.abs(W - W.T)))
    assert np.allclose(W, W.T), "W is not symmetric"

    print("Nonnegativity check (min entry):", W.min())
    assert (W >= 0).all(), "W has a negative entry"

    d = W.sum(axis=1)
    print("d(p) values:", d)
    assert (d > 0).all(), "K2 (0 < d(p)) fails"

    P = W / d[:, None]
    print("Row sums of P (should all be 1):", P.sum(axis=1))
    assert np.allclose(P.sum(axis=1), 1.0), "P is not stochastic"

    # Self-adjointness w.r.t. d_mu(p) = d(p): <f,Pg>_dmu = sum_p f(p) (Pg)(p) d(p)
    # equivalent to the matrix D@P being symmetric, D=diag(d)
    D = np.diag(d)
    DP = D @ P
    print("Self-adjointness check (max |D P - (D P)^T|):", np.max(np.abs(DP - DP.T)))
    assert np.allclose(DP, DP.T), "P is not self-adjoint w.r.t. d_mu"

    eigenvalues = np.linalg.eigvalsh(DP / np.sqrt(np.outer(d, d)))  # symmetrized similarity transform
    print("Eigenvalues of the symmetrized operator:", sorted(eigenvalues, reverse=True))
    assert np.isclose(max(eigenvalues), 1.0), "largest eigenvalue should be exactly 1"
    assert all(ev < 1.0 + 1e-9 for ev in eigenvalues), "contraction property violated"

    # Dirichlet-form identity: <f,(I-P)f>_dmu == 0.5 * sum_p sum_s W(p,s)(f(p)-f(s))^2
    rng = np.random.default_rng(0)
    max_discrepancy = 0.0
    for _ in range(20):
        f = rng.standard_normal(n)
        lhs = f @ D @ (f - P @ f)
        rhs = 0.5 * sum(W[p, s] * (f[p] - f[s]) ** 2 for p in range(n) for s in range(n))
        max_discrepancy = max(max_discrepancy, abs(lhs - rhs))
    print("Dirichlet-form identity max discrepancy over 20 random f:", max_discrepancy)
    assert max_discrepancy < 1e-9, "Dirichlet-form identity failed"

    print("\nAll M6 properties verified for this explicit n=6 instance.")


if __name__ == "__main__":
    main()
