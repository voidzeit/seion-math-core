# M24 / M25 — where the certificate was collapsing

**EXPLORATORY, NOT CONFIRMATORY.** Same label as the depth sweep it reuses.

Implementation: `../src/geometric_certificate.py`. Campaign: the depth
sweep rerun unchanged (identical topologies, seeds, budgets, methods and
allocations — only the certificate computation was added), so allocator
results are bit-identical to `DEPTH_SWEEP_FINDINGS.md` and any tightness
difference is attributable to the composition rule alone. Raw:
`depth_sweep_raw.json` (4,800 records, each carrying all three
certificates). Analysis: `depth_sweep_analysis.json`.

## The three composition rules

All three certify the same quantity — an upper bound on
`max_n || ambient_root(n) - reduced_root(n) ||` over the supplied finite
leaf batch and rank assignment. What is measured locally is held fixed;
only the composition differs.

| | value bounds | slot gain | combination |
|---|---|---|---|
| **A** (existing) | `U_v = ‖K_v‖_F · ∏U_children`, propagated | `‖K_v‖_F · ∏_{j≠i} U_j` | `D_v ≤ C_v + Σ_i g_i D_i` |
| **B** (M24) | none formed | `‖K_v(.., x_{j≠i}(n), ..)‖_op`, per sample | unchanged, per sample |
| **C** (M25) | as B | as B | `‖a+b‖² = ‖a‖²+‖b‖²+2⟨a,b⟩`, `⟨a,b⟩ ≤ ‖Proj_{Ran(I-P_v)} a‖·‖b‖` |

## T(k): median tightness (E_real / B_cert; 1.0 would be exact)

| regime | k | A scalar/Frobenius | B restricted | C Gram-aware | B/A | C/B |
|---|---|---|---|---|---|---|
| iid | 3 | 1.32e−02 | 3.48e−01 | 3.77e−01 | 26× | 1.085 |
| iid | 6 | 1.63e−05 | 8.46e−02 | 9.45e−02 | 5.2e3× | 1.117 |
| iid | 10 | 1.20e−09 | 1.06e−02 | 1.20e−02 | 8.9e6× | 1.132 |
| iid | 16 | 1.18e−15 | 4.49e−04 | 4.86e−04 | 3.8e11× | 1.082 |
| iid | 24 | 4.25e−24 | 1.01e−05 | 1.07e−05 | **2.4e18×** | 1.056 |
| het | 3 | 1.70e−02 | 2.83e−01 | 3.04e−01 | 17× | 1.073 |
| het | 6 | 2.85e−05 | 5.27e−02 | 6.33e−02 | 1.8e3× | 1.202 |
| het | 10 | 2.29e−09 | 2.65e−03 | 3.09e−03 | 1.2e6× | 1.167 |
| het | 16 | 1.05e−15 | 2.04e−05 | 2.41e−05 | 1.9e10× | 1.182 |
| het | 24 | 1.64e−24 | 4.58e−08 | 5.16e−08 | **2.8e16×** | 1.126 |

**Soundness: all three certificates held in 100% of 4,800 records at every
depth and in both regimes.** A tighter bound that is ever violated would be
wrong rather than an improvement, so this is the gate, not the tightness.

## What this establishes

**1. The scalarization diagnosis was correct, and it was quantitatively
dominant.** Certificate A's per-level looseness factor is ≈10.5×; B's is
≈1.65×. Because it compounds, that 6.4× reduction in the per-level rate
becomes 10^18 at k=24. At k≤6 the certificate now sits at 5e−2 to 3.8e−1 —
within a factor of 3 to 20 of the true error, which is a usable regime.

**2. Two distinct defects were conflated in A, and the larger was not the
one flagged.** A's dominant loss was not the triangle inequality but its
recursively propagated *value bounds*: `U_v = ‖K_v‖_F · ∏U_children` grows
like ~11^k on this configuration while the measured values stay O(1). B
never forms a propagated value bound at all — it contracts the core against
each sample's own operating point and takes the exact operator norm of the
resulting slot map. The second defect, cross-sample decoupling
(`max_n‖M_n‖` paired with `max_n‖δ‖`, two different samples), cost roughly
another 10^6 at k=24 on its own and is removed by propagating per-sample
bounds and taking a single max at the root.

**3. Gram-awareness (M25) is real but small: +6% to +20%, always positive,
never violated.** The normal/tangential split at each projected node — the
same mechanism as Lemma 12.1's `D_1 ⊥ R_1` — recovers a consistent but
modest fraction. It is a genuine effect, not noise (it appears in all 10
regime×depth cells), and it is the direct empirical analogue of the k=3
geometric coupling, which is itself a second-order effect (§21:
`2 − W_3(η) = ¾η² + O(η⁴)`). The size is consistent with the theory.

## What is still collapsing, and why

B/C still decay exponentially in k, at ≈1.65× per level. The remaining
looseness is **not** the closure/propagated angle that M25 addresses — it is
the step `‖M_n δ‖ ≤ σ_max(M_n)·‖δ‖`, which assumes the incoming error
aligns with the slot map's top singular direction at *every level
simultaneously*. That is precisely the coherent-alignment worst case the
free-law witness of `CANONICAL_FORMALIZATION.md` §22 realizes, so some of
this residue is not removable within a class that admits that witness.

Closing it further requires tracking the *direction* of the propagated
error, not only its norm — propagating a subspace (or its Gram matrix)
rather than a scalar per node. That is the natural next step and is
distinct from what M25 does here.

## Scope

Chain and balanced-binary topologies, ambient dimension 6, synthetic cores.
Finite-batch certificates throughout: none of the three is a claim about
unbounded inputs. No claim about production compression.
