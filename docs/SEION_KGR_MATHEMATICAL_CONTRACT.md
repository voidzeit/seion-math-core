# SEION-KGR v26 MAX — mathematical contract

Fase 0 deliverable for the SEION-KGR v26 MAX line. This contract does not
re-derive results already proved in the finite typed-tree track
(`docs/theorems_v3/`) or the kernel-integrated extension
(`papers/kernel_integrated_laws_v5/main.tex`). It states what SEION-KGR
*adds* — a typed knowledge-graph instantiation, a message-passing
unrolling, KGE scorers, a rank controller, and a state→score→ranking
certificate chain — and labels every new object with the same six-level
status vocabulary used for the rest of this repository's `[P]/[A]/[S]`
labels in `docs/epistemic_policy.md`.

Status labels (fixed for this document and for
`SEION_KGR_CLAIM_MATRIX.md`):

| Label | Meaning | Relation to `docs/epistemic_policy.md` |
|---|---|---|
| `DEFINITION` | fixes notation/an object, no truth claim | definition |
| `PROVED` | exact identity, no standing assumption | proof |
| `PROVED_UNDER_ASSUMPTIONS` | theorem with declared hypotheses (uniform bounds, orthogonality, Lipschitz, separability) | conditional proof |
| `NUMERICALLY_TESTED` | measured on finite runs with recorded seed/dtype/artifact path | numerical observation / empirical heuristic |
| `EXPLORATORY` | ran, but not preregistered or not confirmatory | empirical heuristic, fail-open |
| `OPEN` | no proof or systematic evidence yet | conjecture / open problem |

A claim never receives a stronger label here than it has in the source
theorem/claim registry it depends on. Where a KGR object composes two
already-proved pieces, the composition is `PROVED_UNDER_ASSUMPTIONS` at
best, never `PROVED`, because the composition itself (KG unrolling into
signed trees, Lipschitz envelope around the certified core) is new.

Full per-claim table: see `SEION_KGR_CLAIM_MATRIX.md`. Full assumption
inventory: see `SEION_KGR_ASSUMPTION_LEDGER.md`.

## I. Reused proof authority (not re-derived here)

| Object | Proof location | Status there |
|---|---|---|
| Typed tree, four root errors, Pythagorean split, `E_red = E_proj` | `docs/theorems_v3/typed_model.md` (`THM_V3_ROOT_ERROR_ORTHOGONALITY`) | `PROVED_UNDER_ASSUMPTIONS` |
| Exact nonempty-subset local expansion | `docs/theorems_v3/exact_subset_expansion.md` (`THM_V3_EXACT_SUBSET_EXPANSION`) | `PROVED` |
| Ambient coefficient `k` | `docs/theorems_v3/homogeneous_constants.md` (`THM_V3_HOMOGENEOUS_AMBIENT_K`) | `PROVED_UNDER_ASSUMPTIONS` |
| Projected/reduced coefficient `k-1` | `docs/theorems_v3/homogeneous_constants.md` (`THM_V3_PROJECTED_ROOT_K_MINUS_ONE`) | `PROVED_UNDER_ASSUMPTIONS`; sharpness at fixed `eta=rho/M` `OPEN` |
| Optimal telescoping order | `docs/theorems_v3/telescoping_order.md` (`THM_V3_OPTIMAL_TELESCOPING_ORDER`) | `PROVED_UNDER_ASSUMPTIONS` |
| Mixed-mask nodewise certificate, path-sum pathwise majorant | `docs/theorems_v3/nodewise_certificates.md` (`THM_V3_NODEWISE_MIXED_CERTIFICATE`, `THM_V3_NODEWISE_PATH_SUM`) | `PROVED_UNDER_ASSUMPTIONS` |
| Representation-vs-closure error separation | `docs/theorems_v3/cp_projection_budget.md` | `PROVED_UNDER_ASSUMPTIONS` |
| Signed-forest cancellation scope (what is/isn't captured) | `docs/theorems_v3/signed_forests.md` | mixed: symbolic grouping `PROVED`; adversarial forest ratio `EMPIRICAL_LOWER_BOUND` |
| Projected 5-input ternary associator, triangle coefficient 2 | `docs/theorems_v3/signed_forests.md` (`COR_V3_PROJECTED_TERNARY_ASSOCIATOR_TWO`) | `PROVED_UNDER_ASSUMPTIONS` |
| `L^2` ternary kernel boundedness, kernel-Lipschitz stability | `papers/kernel_integrated_laws_v5/main.tex` §XV (unlabeled Proposition, Cauchy–Schwarz + Fubini) | `PROVED_UNDER_ASSUMPTIONS` (finite `L^2` norm) |
| Composite kernels `K_L, K_R`, associator defect kernel `Phi_K`, vanishing-iff-associative | `papers/kernel_integrated_laws_v5/main.tex` §"Kernel of the associator" | `PROVED_UNDER_ASSUMPTIONS` (density/integrability conditions declared, not universal) |
| Riemannian gradient on Stiefel manifold for `Q` | `papers/kernel_integrated_laws_v5/main.tex` §"Variational program" | `PROVED` (standard differential-geometric identity); explicit remark that a numerical minimum is neither global nor canonical |
| Finite cohomology descent (`Td=dT ⟹` induces `H^p→H^p`), Hodge compatibility (`[T,d]=[T,d*]=0 ⟹ [T,Δ]=0`) | `papers/kernel_integrated_laws_v5/main.tex` §"Finite cohomology and truncated Hodge theory"; also `claims/theorem_registry.yaml` (`THM_COHOMOLOGY_DESCENT_FINITE_V1`), `claims/theorem_registry_v2.yaml` (`PROP_FINITE_COHOMOLOGY_DESCENT_V2`) | `PROVED` (finite/truncated only) |
| Spectral truncation `E_d^Λ`, spectral dimension `d_s` | `papers/kernel_integrated_laws_v5/main.tex` §"Markov operator and induced Laplacian" | remark: existence of the `t↓0` limit is an *additional hypothesis*, `OPEN` in general |
| Multiscale transport defects `D_mu`, `D_P` across resolutions | `papers/kernel_integrated_laws_v5/main.tex` §"Multiscale structure" | explicit remark: a finite decreasing sequence does **not** establish a continuum limit; `OPEN` |
| CP factor gauge group (permutation + scale with product 1) | `docs/definitions/nary_laws.md` (`CPLaw`) | `DEFINITION`, gauge ops implemented |
| Closure leakage functional | `docs/definitions/projectors.md` | `DEFINITION` + `NUMERICALLY_TESTED` (sample mean only, not an operator-norm bound) |
| Five-input associator, anchored binary associator (distinct objects) | `docs/definitions/associators.md` | `DEFINITION` |
| Non-persistence of learned subspaces, near-orthogonality across seeds, associator ratio decreasing `0.40→0.12` for `n=12→96`, GPU 3.2–3.5× slower than CPU, Procrustes-comparison vacuity, gauge-objective correction | `academic_submission_package_v2_20260801/sources/numerical_study/main.tex` (abstract, 14 experiments + 208-config sweep) | `NUMERICALLY_TESTED` |
| Pathwise rank allocation vs. `uniform`/`singular_energy`/`local_error_greedy`: **mixed/negative** on the preregistered confirmatory design; majorant is a genuine upper bound in 100/100 measured triples, ratio `true_error/majorant ∈ [0.35, 0.93]` (never `>1`); Pearson 0.933 / Spearman 0.922 correlation | `applications/adaptive_tensor_network/results/LEVEL1_FINDINGS.md`, `CAMPAIGN_FINDINGS.md` | `NUMERICALLY_TESTED` (Level 1, confirmatory); Levels 2–3 `EXPLORATORY` |

**Correction to the source design note.** The design note that seeded
this contract flagged "`empirical upper bound` vs. ratio 0.35–0.93" as an
unresolved orientation inconsistency. It is not: `LEVEL1_FINDINGS.md`
defines the ratio as `true_error / majorant`, always `≤ 0.93 < 1`, which
is exactly the statement that the majorant dominates the true error in
every measured case — i.e. it *is* an upper bound, just a loose one
(never tighter than ~1.08× in the observed range). No naming fix is
needed beyond keeping the object named `empirical_pathwise_majorant`
(already `NUMERICALLY_TESTED`, never `certified_upper_bound`, since the
100 measured triples are not a proof for all triples).

## II. Typed knowledge-graph objects [DEFINITION, new]

Reuses `docs/theorems_v3/typed_model.md`'s typed-space/projector
machinery (`V_tau`, `Q_tau`, `P_tau = Q_tau Q_tau^*`) with one added type
family for entities, relations, and queries:

```
V_E   (entity states)      V_R   (relation states)      V_Q   (query states)
```

Knowledge graph `G = (Vert, Rel, Edges)`, `Edges ⊆ Vert × Rel × Vert`.
Reciprocal closure: `Rel± = Rel ⊔ Rel^{-1}`; every stored triple `(h,r,t)`
contributes `(t, r^{-1}, h)`. This is a `DEFINITION` (a modeling choice
that collapses head- and tail-prediction into one task), not a theorem;
it is motivated by the v25 empirical finding logged in
`SEION_V25_DESIGN.md` that a directional fixed law degrades severely on
head-ranking (`head MRR = 0.0751` vs `tail MRR = 0.2235` for the `E_8`
fixed-tensor run) — cited as motivation, not proof that reciprocal
closure fixes it.

## III. Ternary seionic law per layer [DEFINITION, new — CP instance of an already-typed object]

```
mu_l(x,a,q) = O_l[(A_l x) ⊙ (B_l a) ⊙ (C_l q)]
```

is exactly `docs/definitions/nary_laws.md`'s `CPLaw` specialized to arity
3 with output map `O_l`. The CP-equals-dense-contraction identity
(`K_{l,dijk} = Σ_α O_{l,dα} A_{l,αi} B_{l,αj} C_{l,αk}`) is `PROVED` by
direct substitution (same proof pattern as `docs/definitions/nary_laws.md`
and gate-tested by `CPLaw` vs. dense-tensor equivalence tests already in
the v3 suite). The CP gauge group (per-component scale with product 1,
plus permutation) is `docs/definitions/nary_laws.md`'s existing gauge
group — carries over unchanged; comparisons across seeds/runs must use
tensor reconstruction, induced scores, or projectors, never raw factors,
per the `numerical_study` finding above (subspaces pairwise
near-orthogonal across seeds at comparable loss).

## IV. Cyclic symmetrization [DEFINITION + PROVED-by-construction]

`Π_cyc = (1/a) Σ_j σ^j` is idempotent and self-adjoint because `σ` is
unitary under the Frobenius inner product — `PROVED`, same identity
class as the "idempotence and self-adjointness of `UU*`" result already
verified in `numerical_study`. Imposed cyclic symmetry is a property of
the parametrization, not evidence the data required it — this caveat is
carried forward unchanged from `docs/definitions/associators.md`'s
scope note and the `numerical_study` finding that imposed structure
should not be read as discovered structure.

## V. Associators and Filippov identity as diagnostics only [DEFINITION]

`A_mu^(5)` (five-input) and `A_{mu,e}^(3)` (anchored binary) are the two
distinct objects fixed in `docs/definitions/associators.md` — never
fused. The Filippov-identity residual `F_mu` is a new `DEFINITION`
specific to this contract (SEION-KGR did not need it before; the finite
tree track's associator work does not use it). Its energy
`L_FI = E[|F_mu|^2 / (…)]` is `NUMERICALLY_TESTED` at best once
measured; reducing it does not by itself establish a 3-Lie algebra
unless `mu` is verified totally antisymmetric — stated as `OPEN` unless
demonstrated per-run.

## VI. Closure under projection [PROVED_UNDER_ASSUMPTIONS, reused]

`r_mu = (I - P_{τ0}) mu(P_{τ1}·, …, P_{τa}·)` and `ρ_mu = ‖r_mu‖_op` are
exactly `docs/definitions/projectors.md`'s closure-leakage object,
retyped for the KG message space. The sample-mean closure loss
`L_closure` is `NUMERICALLY_TESTED`/a training signal; it is **not** a
bound on `ρ_mu` (operator norm), per the existing scope note in
`docs/definitions/projectors.md`.

## VII. Query-conditioned message passing [DEFINITION, new]

Sections 10.1–10.5 of the source design note (indicator state, ambient
message `m̃`, projected message `m = P_{l+1} m̃`, aggregation `z_v`,
update `x_v^{(l+1)}`) are new `DEFINITION`s specific to SEION-KGR. They
are not proved or disproved by anything in the existing repo; they are
the object the rest of this contract's inherited theorems get applied
*to*, once unrolled into trees (§IX below).

## VIII. Certified core vs. nonlinear envelope [DEFINITION, structural]

`F_l = N_l ∘ C_l`, with `C_l = P_{l+1} ∘ (mu_l + linear residual branches)`
certified by the typed-tree theory, and `N_l = LN ∘ (I + σ_l)` requiring a
Lipschitz treatment (§X). This split is the load-bearing modeling choice
that lets the rest of this contract cite `THM_V3_*` at all — **the `k-1`
theorem must not be applied to a full layer with LayerNorm/attention/gates
without this split**, echoing the same warning already present in
`docs/theorems_v3/typed_model.md`'s "these are identities, not bounds"
framing.

## IX. DAG unrolling into signed trees [PROVED_UNDER_ASSUMPTIONS for the tree part, OPEN for the DAG-specific error]

A message-passing computation over a knowledge graph is a DAG, not a
tree, once nodes are shared across paths. Per-query, finite-depth
unrolling into a (possibly large) collection of trees with duplicated
shared subcomputations is always possible (`DEFINITION`), and the
resulting combination `F = Σ_α c_α F_{T_α}` inherits the signed-forest
scope already fixed in `docs/theorems_v3/signed_forests.md`: symbolic
grouping of syntactically identical unrolled trees is `PROVED`, but a
triangle-inequality sum over `α` (ignoring shared-state reuse and
cancellation across paths) is conservative and not claimed tight. Tight
constants for DAG-native (non-unrolled) cancellation are `OPEN` — this is
new territory beyond `docs/theorems_v3/`, not answered there.

## X. Lipschitz envelope propagation [PROVED_UNDER_ASSUMPTIONS, standard]

`E_root ≤ Σ_v λ_v ∏_{e∈path(v,root)} L_e` for `L_e`-Lipschitz nonlinear
updates is a standard composition-of-Lipschitz-maps argument
(`PROVED_UNDER_ASSUMPTIONS` given declared `L_e`). It does **not**
inherit the exact `k-1` (vs. `k`) improvement, because that improvement
is a consequence of exact orthogonal projection (`P(I-P)=0`) at a
multilinear root, not of Lipschitz continuity alone — this is the same
distinction `docs/theorems_v3/typed_model.md` draws between identities
and bounds, applied here to explicitly block over-claiming `k-1` on the
non-linear envelope.

## XI. KGE scorers [DEFINITION, new]

Reciprocal ComplEx, the seionic scalar scorer
`s_seion(h,r,t) = ⟨q_seion(h,r), T e_t⟩` (with the batched form
`S_seion(h,r,:) = q_seion(h,r) (TE)^T` avoiding `[B,N,R]` tensors), the
path scorer `s_path`, and the residual router
`s = s_base + γ_r s_path + η_r s_seion + ε_r s_{E8}` with
`γ_r,η_r,ε_r ≈ 0` at init are all `DEFINITION`s. None are theorems; they
are architecture choices motivated by the v25 postmortem
(`SEION_V25_DESIGN.md`: bilinear MRR 0.201 > fixed-`E_8` MRR 0.149 >
CP-rank-128 valid MRR ≈0.079 with severe head/tail asymmetry) — the
residual-router-near-zero-init choice exists specifically so a weak
branch cannot start with non-trivial weight, as recommended in that
postmortem's §7.

## XII. `E_8` prior and mandatory controls [DEFINITION + OPEN causal claim]

`mu_l^Θ = mu_l^learned + ε_{l,r} W_l mu_{E8}(…)` is a `DEFINITION`. The
required control set (`E_8`, random scale-matched, permuted,
sign-shuffled, zero, frozen, learned-residual) is a falsification
protocol, not a proof; whether `E_8`'s specific structure is causally
responsible for any measured gain is listed `OPEN` in
`SEION_KGR_CLAIM_MATRIX.md` and must stay open until the controls are
run and a specific structure ablation beats the random-matched control
by a preregistered margin (same discipline as
`applications/adaptive_tensor_network/experiments/PREREGISTRATION.md`).

## XIII. Loss and rank-controller definitions [DEFINITION + reused evidence]

1-vs-all / BCE, N3 regularization, the geometric total loss with
schedules `w_C, w_A, w_F`, and the bilevel rank-allocation problem
(§§XXII–XXVIII of the source note) are `DEFINITION`s. The rank-controller
feature vector `φ_v` (combining `λ_v`, pathwise score, singular energy,
gradient sensitivity, Fisher, cost) is specified *because* the pathwise
score alone already failed as a universal policy — see the reused
evidence row above (`LEVEL1_FINDINGS.md`: pathwise loses to `uniform`
and `local_error_greedy` at equal budget in the confirmatory design).
This contract commits to never shipping "rank = pathwise score alone" as
a default policy.

## XIV. State-error → score-error → ranking certificate chain [OPEN, new]

Proposition 29.1 (`‖s-s̃‖_∞ ≤ L_ψ B`), Theorem 30.1 (margin `>2ε` implies
order preservation — elementary, `PROVED` once `L_ψ` and `B` are fixed),
and the partial-MRR certificate (§XXXI of the source note) are the
genuinely new mathematical contribution of SEION-KGR beyond the existing
repo. Theorem 30.1 itself is an elementary triangle-inequality argument
and can be marked `PROVED` in isolation; but the *chain* — a certified
`B_state` from §IX/§X composed with a certified `L_ψ` to get a
certified-coverage MRR contribution — is not established anywhere in
this repo and is `OPEN`. It is the one item in this contract that must
not be marketed as inherited from the finite-tree papers.

## XV. Reproducibility contract [DEFINITION, reused pattern]

The `runs/<run_id>/{resolved_config.json, command.txt, environment.json,
hardware.json, git_manifest.json, dataset_manifest.json,
kernel_manifest.json, metrics.jsonl, gradients.jsonl, rank_history.jsonl,
error_attribution.jsonl, projection_audit.json, best.pt, last.pt,
final_metrics.json, output_manifest.json}` contract mirrors the pattern
already required by `papers/software_v4/main.tex` and
`docs/governance.md`'s authority ladder (`declared → observed → verified
→ approved`); SHA-256 on every artifact, append-only history, resumes
never counted as independent seeds — same discipline, new file list for
the KGR trainer specifically.

## XVI. Canonical object

```
S_KGR = (G±, T, V, mu, Q, P, Phi, s, r, L, B)
```
`DEFINITION` — the tuple is a naming convenience for governance/config
registration, not a mathematical claim in itself.
