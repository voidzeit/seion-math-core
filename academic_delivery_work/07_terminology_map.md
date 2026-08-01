# 07 — Terminology replacement map

Built from **measured occurrences** in the five manuscript sources, not from the generic list in the
governing instruction. Every row below corresponds to text that is actually present. Terms in the
instruction's table that do not occur in any manuscript are listed in §5 and are not carried forward.

Sources scanned:

| # | File | Commit |
| --- | --- | --- |
| 01 | `papers/tree_stability_v4/{main.tex, proofs/full_proofs.tex, generated_results.tex}` | `2e419ef` |
| 02 | `papers/kernel_integrated_laws_v5/main.tex` | `2e419ef` |
| 03 | `papers/a_to_n_certification_v18/main.tex` | `8e09941` |
| 04 | `papers/software_reproducibility_v5/main.tex` | `8e09941` |
| 05 | `papers/supplementary_visual_atlas_v18/main.tex` | `8e09941` |

---

## 1. Measured occurrence counts

Case-insensitive regex counts. Blank = zero.

| Term as it appears | 01 | 02 | 03 | 04 | 05 |
| --- | ---: | ---: | ---: | ---: | ---: |
| `gate` (as noun: "release gate", "resource gate", "critical gate") | 16 | | 19 | 11 | |
| `certification` | 3 | | 16 | 21 | 3 |
| `Block A`…`Block N` / `block A`…`block N` | 3 | | 12 | 1 | 8 |
| `projected-root` | 8 | | | | |
| `signed forest` | 6 | 2 | | | |
| `mixed-mask` | 6 | 3 | | | |
| `mixed-block` / `mixed-state` | 4 | | | | |
| `path-sum` | 5 | 2 | | | |
| `artifact` | 5 | 1 | 3 | 5 | 2 |
| `fail-closed` / `FAIL_CLOSED` | 2 | | 9 | 2 | |
| `v3` / `v4` / `v5` / `v18` version labels in prose | 13 | | 5 | 22 | 4 |
| `SEION` | | 2 | 1 | 3 | |
| `Kernel-Integrated` | | 5 | | | |
| `Track T` | | | 2 | | 1 |
| `A-N` / `A–N` (as a track name) | | | 1 | 3 | 4 |
| `tangent` (geometric misuse) | 1 | 6 | | | |
| `normal-to-tangent` | | 1 | | | |
| `curvature` | | 7 | 2 | 1 | |
| `snapping` | 1 | | 1 | | |
| `cyclic law` | | | 1 | | |
| `PENDING_HUMAN_REVIEW` | 3 | | 1 | | |
| `NOVELTY_NOT_ESTABLISHED` | 1 | | | | |
| `OPEN_K2…` / `OPEN_K3…` | 4 | | | | |
| `NOT_CERTIFIABLE_AS_DEFINED` / `not_certifiable` | 1 | | 1 | | |
| `structural_identity_pass` | | | 4 | | |
| `numerical_sanity_pass` | | | 1 | | |
| `empirical_screening_pass` | | | 4 | | |
| `statistically_validated_pass` | | | 3 | | |
| `validated_numerical_certificate` | | | 1 | | |
| `exact_certificate` | | | 2 | | |
| `registered cell` / `registered instance` | 1 | | | | |
| `resource-gated` / `resource gate` | 3 | | | | |
| `release blocker` | 1 | | | | |
| `terminal status` / `terminal state` | 1 | | | | |
| `claim registry` | 1 | | | | |

**Total distinct jargon tokens requiring replacement in scholarly prose: 34.**
**Total occurrences: 344.**

---

## 2. Replacements, with the mathematical check applied

The instruction forbids mechanical substitution. Each row records the *checked* meaning in this
corpus, which in several cases differs from the instruction's default suggestion.

| # | Occurrence | Checked meaning in these manuscripts | Replacement in scholarly prose |
| --- | --- | --- | --- |
| T-1 | `SEION` (02 abstract, 02 §Final synthesis; 03 thanks; 04 passim) | The research programme as a whole. No mathematical content. | Delete. In 02: "a theory of typed multilinear laws under recursive orthogonal projection". |
| T-2 | `Kernel-Integrated Laws` / `Kernel-Integrated Typed Multilinear Laws` (02 title, abstract) | The `L²` realisation `T_K(f₁,…,f_n) = ∫K(p;q)∏f_j(q_j)dμ`. | **kernel-defined multilinear operators** (analytic realisation) / **typed multilinear laws** (finite case). |
| T-3 | `Track T` (03 thanks, 03 §Limitations, 05 §missing) | The finite-dimensional projected-tree programme = manuscript 01. | "the finite-dimensional analysis of recursively projected multilinear composition trees" or a direct citation of manuscript 01. |
| T-4 | `A–N track`, `A-N certification` (03, 04, 05) | The 14-experiment numerical suite = manuscript 03. | "the numerical study of cyclic multilinear maps, orthogonal projectors, and multiresolution tensor representations". |
| T-5 | `Block A`…`Block N` (03 §Block-by-block results; 05 all nine captions) | 14 distinct experimental questions. | Descriptive section names — see §3 below for the checked one-to-one map. |
| T-6 | `fail-closed` (03 title, abstract, §final; 01 §Conclusion; 04) | Combination by **minimum** over criteria, never by mean; and refusal to emit a positive verdict absent all criteria. | "a conservative decision rule that combines criteria by their weakest element and withholds a positive conclusion unless every prespecified criterion is met". Where it labels the *combination operator* specifically, "minimum-combination rule" is exact and preferable. |
| T-7 | `gate`, `critical gate`, `research gate` (01, 03, 04) | A prespecified acceptance criterion. | **acceptance criterion** / **validation criterion**. |
| T-8 | `resource-gated`, `resource gate`, "the extended grid is resource-gated" (01) | The computation was **specified but never executed**, because of cost. | "not executed, under a stated computational-cost constraint". Must not read as a property of the mathematics. |
| T-9 | `release blocker` (01) | Administrative. | "a condition preventing submission". Belongs in a release note, **not** in the mathematical text (instruction §12). |
| T-10 | `structural_identity_pass` (03) | The identity holds **by construction**: `P = UU*` is idempotent for any orthonormal `U`; cyclic averaging by `Π_cyc` yields a cyclic tensor. | "identity verified by construction". Add, per instruction §13: "this is a property of the construction, not evidence about the fitted object." |
| T-11 | `numerical_sanity_pass` (03) | Residual at machine precision on a single configuration. | "elementary numerical consistency check". |
| T-12 | `empirical_screening_pass` (03) | Exploratory computation, no sampling model declared. | "exploratory numerical evidence". |
| T-13 | `statistically_validated_pass` (03 block G) | **2000 samples plus adversarial gradient ascent.** No sampling population, statistic, uncertainty calculation, or inferential procedure is stated anywhere in 03. | Instruction §16 forbids "statistically validated" without those five items. Replace with **"observed over 2000 sampled configurations"** unless the sampling model is added. Flagged in `01_statement_evidence_table.md` as S-3.7. |
| T-14 | `validated_numerical_certificate` (03 taxonomy) | Defined in the taxonomy; **never attained by any block in 03.** | "rigorous numerical enclosure". Note explicitly that no result reaches it. |
| T-15 | `exact_certificate` (03 taxonomy; 01 block A) | 01: directed interval arithmetic + exact symbolic elimination in low dimension. 03: taxonomy only. | "exact symbolic verification" (01) / "exact algebraic verification". |
| T-16 | `NOT_CERTIFIABLE_AS_DEFINED` (01 §signed-followup; 03) | The declared 6-term GJI variant evaluated to 10⁻¹⁶–10⁻²¹ in every one of 4000 trials plus five reseeded checks, under both leaf-input conventions. | Instruction §13 wording, and it fits exactly: "The quantity evaluated at numerical precision zero in all trials. This suggests the current formula may define an identically vanishing expression. Symbolic verification is required before it can be used as a nontrivial diagnostic." |
| T-17 | `OPEN_K2_WITH_CERTIFIED_GAP` (01) | k = 2: 6 of 75 homogeneous gated-rotation configurations attain the projected bound; gaps elsewhere run from 3.75×10⁻⁷ to 1.0. | "For trees with two internal vertices the exact constant is known only for part of the admissible parameter range; elsewhere the rigorous lower and upper bounds do not coincide." |
| T-18 | `OPEN_K3_WITH_CERTIFIED_TOPOLOGY_GAPS` (01) | k = 3: no configuration or error type attains optimality; projected gap floor 35 %. | "For three internal vertices the available bounds depend on tree topology and leave nonzero optimality gaps throughout." |
| T-19 | `PENDING_HUMAN_REVIEW` (01, 03) | Administrative. | "not yet independently verified". |
| T-20 | `NOVELTY_NOT_ESTABLISHED` (01) | A bounded search found no verbatim match. | "We make no claim of originality for this formulation, pending expert comparison with the literature." No score. |
| T-21 | `mixed-mask calculus` (01 §DP, 02 §"Mixed-mask calculus") | The three-state expansion of each slot into `{R, D^∥, D^⊥}` and the induced recursion on bounds. **Not a calculus** — no derivation operator, no chain rule, no algebra of operations is developed. | **state-resolved local error decomposition** (the identity) and **state-resolved recursion** (the bound). Instruction §9.2 applies: do not call it a calculus. |
| T-22 | `mixed-block` / `mixed-state` (01) | Operator norms of `μ_v` restricted to a state vector. | "block operator norms of the multilinear map restricted to the projected and orthogonal components". |
| T-23 | `path-sum certificate` (01, 02) | Unrolling the affine scalar recurrence `B_v ≤ λ_v + Σ_j h_{v,j}B_{c_j}`. | **pathwise residual bound** / **source-to-root residual expansion**. Instruction §9.3: must state it is the expansion of a scalar recurrence, **not** the exact expansion of all multilinear cross terms. |
| T-24 | `signed forest` (01, 02) | `F = Σ_α c_α T_α`, finite, compatible types. | **finite signed linear combination of composition trees**. Acceptable to keep "signed forest" thereafter *if formally defined at first use*; it is close to standard usage. |
| T-25 | `normal-to-tangent mechanism` (02) | `P_v μ_v(…, D_i^⊥, …) ≠ 0`: a child's orthogonal error acquires a component in the range of the parent projector. | **conversion of orthogonal error into projected error under subsequent composition**. |
| T-26 | `tangent` (01 ×1, 02 ×6: "tangent/normal plane", "tangent-normal calculus", "turned tangential") | **There is no tangent space.** `ran P` is a fixed linear subspace, not a tangent space to a manifold. The one legitimate use is 02 §Variational program, `T_Q St(d,r)`, which *is* a genuine tangent space. | Replace with **projected** / **in the range of `P`** everywhere except the Stiefel tangent space, which stays. This is the clearest instance of the instruction's §8 warning. |
| T-27 | `projected-root improvement` (01 §title, 8×) | The coefficient `k−1` in the estimate for `E^proj`, versus `k` for `E^amb`. | **improved coefficient in the projected-output error estimate**. |
| T-28 | `spectral snapping` (01, 03 block D) | Thresholded spectral projection with a Davis–Kahan-type perturbation bound. | **thresholded spectral projection**. |
| T-29 | `cyclic law` (03 block N) | A multilinear map invariant under cyclic permutation of its arguments. | **cyclically symmetric multilinear map**. |
| T-30 | `curvature` (02 ×7) | 02 already handles this correctly: it distinguishes `R_alg := A` (a *definition*) from `R_std(x,y) = [L_x,L_y] − L_{[x,y]}` (an operator), and proves `R_std(x,y)z = A(y,x,z) − A(x,y,z)`. | **Retain, with 02's existing hedge kept verbatim.** Rename `R_alg` to an **associator-based algebraic tensor** and state explicitly that it is not the curvature of a connection. 03's two uses ("coherent dynamic curvature", "reduced curvature") are software identifiers and must move to the reproducibility appendix. |
| T-31 | `artifact` (all five) | Three distinct referents: (a) saved JSON/parquet experiment output; (b) a figure source; (c) an unwanted numerical effect ("not a small-scale artifact", 03/05). | Disambiguate: (a) **computational output** / **dataset**; (b) **figure source**; (c) keep "artifact" — that use is standard English and correct. |
| T-32 | `registered cell` / `registered instance` (01) | One distinct mathematical configuration, deduplicated by `scientific_instance_hash`. | **parameter configuration** / **distinct mathematical test instance**. |
| T-33 | `claim registry`, `evidence registry` (01) | `claims/theorem_registry_v3.yaml`. | **statement–evidence table** / **provenance and evidence table**. |
| T-34 | Version labels `v3`, `v4`, `v5`, `v18` in prose (01 ×13, 03 ×5, 04 ×22, 05 ×4) | Repository development phases. | Delete from prose. Retain **only** in `provenance.md` and the reproducibility appendix, per instruction §24. |

---

## 3. Block letter → mathematical question (checked against `BLOCK_*_FINDINGS.md` and the block modules)

Each mapping was verified against the corresponding
`spectral/certification_v18/blocks/block_*.py` at `8e09941`, not inferred from the letter.

| Letter | Implementation module | Section name by mathematical content |
| --- | --- | --- |
| A | `block_a_projector.py` | Orthogonal projector identities |
| B | `block_b_commutator.py`, `block_b_ablation_matrix.py` | Approximation of a commutator by a parameterized model |
| C | `block_c_beals_proxy.py` | Finite nested-commutator diagnostics |
| D | `block_d_snapping.py` | Stability of thresholded spectral projectors |
| E | `block_e_interscale.py` | Transport of learned subspaces across resolutions |
| F | `block_f_rigidity.py` | Local identifiability and invariance under basis changes |
| G | `block_g_closure.py` | Approximate closure of multilinear maps |
| H | `block_h_associator.py` | Bounds for associators |
| I | `block_i_reduced_tensor.py` | Extraction of reduced tensors |
| J | (uses `gauge_utils.py`, applied to E's data) | Gauge-invariant tensor comparison |
| K | `block_k_hosvd.py` | Multilinear singular-value compression |
| L | `block_l_gauge_canonicalization.py` | Canonical representatives and residual basis freedom |
| M | `block_m_persistent_factorization.py` | Persistence of tensor factors across resolutions |
| N | `block_n_cyclic_gji.py` | Cyclic symmetrization and generalized Jacobi-type residuals |

Each letter may appear **once**, parenthetically, in the reproducibility table:
`Approximation of a commutator (internal implementation label: block B)`. Not thereafter.

**Note on C.** The module is named `block_c_beals_proxy.py` and manuscript 03 already renames it
`FINITE_BEALS_PROXY` with the explicit caveat that no Ψ⁰-membership or microlocal-regularity claim is
made. That caveat must survive into the rewritten section; "Beals" should not appear in the section
title, since Beals' commutator characterisation is a theorem about pseudodifferential operators and
this block computes finite Frobenius norms.

---

## 4. Prohibited phrasings present, with location

Instruction §2.3. Each of these is present and must be rewritten.

| Phrase | Where |
| --- | --- |
| "the strongest mathematical core of the theory" | 02 §Typed composition trees |
| "The scientifically most defensible object here is not a physical theory, but…" | 02 §Scope and epistemic map |
| "The defensible mathematical formalization of SEION is…" | 02 §Final synthesis |
| "the canonical formulation separates three levels" | 02 §Scope and epistemic map |
| "epistemic status", "epistemic boundary", "epistemic map" (§ headings) | 01 §"Contributions and epistemic status", 01 §"v4 theorem program and epistemic boundary"; 02 §"Scope and epistemic map" |
| "fail-closed release gate", "release status is therefore FAIL_CLOSED_NOVELTY" | 01 abstract, §Conclusion |
| "the presence of a compiled PDF is not a release authorization" | 01 §Reproducibility appendix |
| "registered scientific cells", "15,493 scientific instances" | 01 abstract |
| "deployed regime", "REFUTED_IN_DEPLOYED_REGIME" (in `docs/`, feeding 03) | `docs/research/`, 03 block B prose |
| "no process here self-issues a final certification" | 03 abstract |
| "the honest global label most consistent with the full evidence set" | 03 §final |

The last two are *epistemically admirable* and their content must be preserved — but as ordinary
academic prose in a Limitations section, not as a certification verdict in an abstract.

---

## 5. Instruction-list terms that do **not** occur, and are therefore not carried forward

`typed status`, `evidence registry` (as a phrase), `deployed regime` (in the manuscripts themselves —
it occurs only in `docs/`), `curvature equals associator` (02 correctly never asserts this),
`our framework`, `our ecosystem`, `the SEION object`, `the canonical track`, `certified roots`,
`full certification` (03 explicitly says the opposite), `paper-forward`, `release readiness`,
`fail-closed novelty` (occurs only as the generated macro value `FAIL_CLOSED_NOVELTY`),
`deployed failure`, `terminal classification`.

Recording these as absent matters: it prevents a later pass from "fixing" text that is not there,
and it documents that several of the instruction's worst-case phrasings were already avoided.
