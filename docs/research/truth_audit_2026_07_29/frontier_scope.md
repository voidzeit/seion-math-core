# Frontier-scope audit (Priority C legitimate work vs. Priority E overreach)

## What legitimately exists: finite cohomology (Priority C)

`src/seion_core/cohomology/chain_complex.py` and `compatibility.py`
implement a finite cochain complex with `d²=0` and a commuting-operator
descent check — `THM_COHOMOLOGY_DESCENT_FINITE_V1`
(`docs/theorems/cohomology_descent.md`), labeled
`PROVED_UNDER_ASSUMPTIONS`, with a short correct proof and an explicit
closing disclaimer: "No claim about infinite-resolution limits follows."
`paper/sections/13_truncated_cohomology.tex` and
`tests/unit/test_cohomology.py` back this with real, bounded content.
`papers/truncated_cohomology/` is currently a one-line placeholder README
("Reserved for a focused paper on finite complexes...") — correctly scoped,
not yet written.

`src/seion_core/cohomology/discrete_hodge.py` contains one function,
`hodge_laplacian`, computing the standard combinatorial Hodge Laplacian
`d_{k-1} d_{k-1}^* + d_k^* d_k` on a finite chain complex — this is
textbook discrete/combinatorial Hodge theory (Eckmann 1944, Dodziuk 1976,
already cited as prior art), not the continuum Seionic Hodge Program (SHP)
described in the mission. It is a small, standard, correctly-scoped
utility, not evidence of SHP progress.

## What does not exist: the SHP / Hodge-conjecture frontier

A repository-wide search (`docs/`, `papers/`, `claims/`, `src/`, `.ai/`) for
SHP, "Hodge conjecture," Laurent-polynomial algebraization, E8-as-Lie-
algebra, G-ASUn/"Generative...Automaton," Riemann-Hilbert, D-module,
holonomic, PsiDO/Ψ⁰, and microlocal analysis found **zero constructive
hits**. Every occurrence of this vocabulary is a negative/comparative
disclaimer:

- `paper/sections/17_limitations.tex`: "Continuous kernel limits, strong
  operator convergence, microlocal regularity, D-modules,
  Riemann–Hilbert, and algebraicity are not combined into a theorem."
- `docs/open_problems/index.md`, item 4: an explicit instruction to keep
  scopes separate — "Separate finite cohomology descent from any strong
  operator or microlocal upgrade."
- `claims/scope_registry_v4.yaml` formally fences
  `claims/conjecture_registry.yaml` under `SPECULATIVE`, distinct from
  `CANONICAL_FINITE_CORE`.
- No file claims to have proved or made progress on the Hodge conjecture,
  claims `P ∈ Ψ⁰`, or claims a D-module/holonomicity/Riemann-Hilbert
  result.

No exceptional-Lie-algebra code exists: `jacobi.py` is generic (arbitrary
finite-dimensional law), and the only text match for "E8" repository-wide
is the hex color `#E8EEF2` in a figure-style module — not the Lie algebra.

## A more precise finding than "absent": disclaimed primitive fragments exist

Direct inspection of `src/seion_core/geometry/` (beyond what the frontier
scan above covered) found isolated utility functions that supply raw
*ingredients* the mission's G-ASUn section describes, without any assembly
into a system and without the interpretive claims:

- `geometry/hamiltonian_dynamics.py` — one function,
  `experimental_hamiltonian_step`, a symplectic-Euler position/momentum
  update. Its docstring reads verbatim: "A labeled experimental symplectic
  Euler step; no physical interpretation."
- `geometry/stiefel.py` — `orthonormalize` (QR-based) and
  `project_tangent` (tangent-space projection for a Stiefel manifold);
  standard differential-geometry primitives, no manifold class, no
  constraint/metric assembly.
- `geometry/riemannian_metrics.py`, `geometry/left_actions.py`,
  `variational/energies.py`, `algebra/cp_law.py` similarly supply isolated
  pieces (metrics, curried operators, associator energy, CP factorization)
  that a G-ASUn-style dynamical system would need.

None of these are composed into a configuration manifold, Hamiltonian,
dissipation law, or integrator loop; none carries a G-ASUn name, class, or
orchestration file; none makes a physical, cognitive, or "universal
automaton" interpretive claim. This is the mission's own prescribed
conservative fallback for section 1.19 ("classify it as a geometric
dynamical system on a parameter space of n-ary laws unless a genuine
field-theoretic formulation..."), except even more minimal — it is a
scattered set of honestly-labeled utility functions, not yet an assembled
dynamical system of any kind.

## Verdict

No overclaim found. The finite cohomology work is real, small, and
correctly labeled. The SHP/Hodge-conjecture/E8/G-ASUn program described in
the mission is not present in this repository beyond a few honestly-
disclaimed low-level utility functions that could, in principle, later be
assembled toward something like it — that assembly, and any interpretive
claim about it, has not happened and should not be assumed to be implied
by the presence of these fragments.
