# Priority C audit — operator sector and remaining cohomology modules

## Part A — operator sector (`src/seion_core/operators/`)

- `laplacian.py:6-21` (`laplacian_from_curried`) builds `L = Σ opᵢ† opᵢ`
  over caller-supplied curried operators, then symmetrizes. Self-
  adjointness and PSD are true by construction and numerically re-checked
  (`min eigenvalue ≥ -1e-10`, :16) — this is the *correct* pattern, not the
  "nonnegative eigenvalues ⇒ Laplacian" fallacy the mission warns about.
  However, the object honestly flags its own limits: `"intrinsic": False`
  (:18), and the construction is described only as "sum of adjoint-
  compositions of declared curried operators" — no Dirichlet-form
  derivation, no graph/manifold structure, no boundary condition, no
  canonicity argument. `dirichlet_form` (:24-25) is just `⟨v, Lv⟩`, a
  quadratic-form evaluator, not an independent derivation that would
  justify canonicity. Net: honestly labeled non-canonical, but the name
  "Laplacian" is still applied to whatever caller-supplied operators are
  handed in, which is a soft version of the trap even though the code
  disclaims it.
- `heat.py:7-10` (`heat_kernel`) computes `expm(-tL)` for whatever matrix
  is passed, with **no check that `L` is self-adjoint or PSD** before
  exponentiating. `heat_trace` (:13-15) re-symmetrizes and calls
  `eigvalsh`, silently *assuming* self-adjointness rather than checking
  it, and returns `Σ exp(-tλ)` with no verification that this is actually
  a contractive/trace-class semigroup.
- `markov.py:6-13` row-normalizes a nonnegative matrix and reports a
  genuine `markovian: bool` construction check — fine as far as it goes.
- `curried.py`, `commutators.py` — thin, correctly-scoped linear-algebra
  utilities, no claims beyond what they compute.
- `spectral_dimension.py:6-10` fits `-2·slope` from `log(trace) ~
  slope·log(t)`, which presumes a genuine short-time heat-trace asymptotic
  — an assumption inherited from `heat_trace`'s unchecked self-adjointness
  above, so its output should be treated as a diagnostic number, not a
  proved spectral dimension.

**Tests/registry:** zero test files reference `laplacian`, `heat_kernel`,
`heat_trace`, `spectral_dimension`, `curried`, `commutator`, or `markov`;
zero registry entries exist for any of these six modules.

**Verdict — Part A:** No confirmed instance of the literal fallacy
("nonnegative eigenvalues therefore Laplacian"), because the code never
argues canonicity from eigenvalue sign alone — it just doesn't argue
canonicity at all, and says so. The concrete, fixable gap is `heat_kernel`
computing a matrix exponential without validating the self-adjointness/PSD
precondition its own sibling function (`laplacian_from_curried`) takes care
to check.

## Part B — remaining cohomology modules

(`chain_complex.py`/`compatibility.py` were already confirmed
proved-under-assumptions, and `discrete_hodge.py` a standard combinatorial
Hodge Laplacian, in the first audit pass. This covers what was left.)

- `torus_fourier.py:6-10` (`torus_fourier_differential`) builds a finite
  `(2·modes+1)`-dimensional diagonal matrix `diag(i·k)` for integer
  frequencies. Purely finite/discrete — no L², completeness, or
  convergence-to-continuum-operator claim in code, though the name alone
  invites that reading without scrutiny.
- `truncation.py:6-9` (`spectral_truncate`) symmetrizes, eigendecomposes,
  keeps the top-`rank` eigenvectors by magnitude, reconstructs. Self-
  labeled `"status": "finite_spectral_truncation"` — appropriately modest.
  **No error/convergence bound exists anywhere** for the discarded
  spectral mass — but no claim requiring one exists either.
- `induced_operator.py:6-7` (`induced_operator`) is **a no-op**: it
  returns `np.asarray(operator)` unchanged, and the `degree` parameter is
  accepted but unused — despite the name, it does not compute any actual
  induced or restricted operator on a graded piece. `commutator_defect`
  (:10-11) is a correctly-implemented but trivial `‖[A,D]‖` norm.

**Tests/registry:** `tests/unit/test_cohomology.py` only exercises the
already-audited chain-complex modules; none of these three modules has any
test or registry entry.

**Verdict — Part B:** No overclaim in `torus_fourier.py` or
`truncation.py` — both correctly stay silent on continuum/error-bound
questions they don't answer. `induced_operator.py` is the one genuine
finding here: **a function named for a nontrivial mathematical operation
(inducing/restricting an operator to a graded piece) that currently does
nothing** — it is dead-weight scaffolding, not a false theorem, but it
should not be assumed to compute what its name implies if anything ever
comes to depend on it.
