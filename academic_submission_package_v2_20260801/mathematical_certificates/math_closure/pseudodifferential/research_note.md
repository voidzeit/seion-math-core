---
title: M7 — pseudodifferential and microlocal program, research note
status: OPEN_WITH_PRECISE_BOUNDARY
priority: lowest (per mission Section IV, explicitly "lower-priority than M1-M6")
---

# Why this is left open, precisely

The mission (Section IV.M7) explicitly forbids attempting these claims
"for arbitrary L2 kernels" and requires "an appropriate smooth kernel or
symbol class on a compact manifold" to be defined *first*. That
definitional work — choosing a compact manifold, a symbol class (e.g.
$S^m_{1,0}$ or a finite-order Hörmander class), and verifying the
multilinear laws in this repository's typed-tree framework actually land
in that class — has not been done anywhere in this repository's history
(checked: no `docs/theorems_v3/`, `docs/research/`, or `research/math_closure/`
file defines a symbol class or references Hörmander/wavefront-set theory
before this note).

This is real, substantial analysis work in its own right (defining a
symbol class compatible with the existing finite-dimensional typed-law
framework is not a mechanical extension of M1-M6's finite-dimensional
linear-algebra techniques — it requires genuinely different machinery:
pseudodifferential calculus, symbol composition asymptotics, and
wavefront-set propagation results that do not have finite-dimensional
analogues in this codebase to build on, unlike M5's continuum theorem,
which *was* a direct extension of the existing finite-tree proof
technique).

## What would be needed to close any of the 5 target questions

1. **Symbol class stability under multilinear composition**: requires
   fixing a manifold $\mathcal{M}$, a symbol class, and proving the
   existing typed-law contraction operations preserve it under
   composition — a genuine microlocal-analysis theorem, not proved here.
2. **Stability under $S \to P_0 S(P_1\cdot,\dots,P_a\cdot)$**: requires
   the projectors $P_i$ to be pseudodifferential of order 0 (or similar)
   and a composition calculus for that — not attempted.
3. **Symbol estimates for the associator**: would need the associator's
   defining identity (M4) reformulated as a symbol-composition
   discrepancy, with estimates in the chosen symbol class — not
   attempted; M4's results are purely finite-dimensional/algebraic.
4. **Wavefront-set propagation**: requires microlocal analysis machinery
   entirely absent from this codebase.
5. **Whether the final orthogonal projection removes any microlocal
   source**: cannot be assessed without (1)-(4) first.

## Honest terminal status

`OPEN_WITH_PRECISE_BOUNDARY`: the boundary is precisely that no symbol
class or manifold has been fixed anywhere in this project's history, and
doing so is a genuine, nontrivial research undertaking distinct in kind
(not degree) from the finite-dimensional work in M1-M6. No claim of a
pseudodifferential, D-module, Riemann-Hilbert, or algebraization result
is made here, per the mission's own explicit prohibition on doing so
without complete hypotheses and proof.

## What would make this tractable in a future session

Start with the single smallest case: a fixed compact manifold (e.g.
$S^1$ or the flat torus $\mathbb{T}^n$, where symbol classes and standard
pseudodifferential calculus are textbook material) and the *simplest*
named identity from M4 (the anchored binary associator, 2 terms) — verify
whether its defining contraction, reformulated with the manifold's
Fourier-multiplier laws in place of the finite-dimensional tensors used
throughout M1-M6, actually falls in a standard symbol class before
attempting any general theorem.
