# SEION-KGR v26 MAX — assumption ledger

Every hypothesis a claim in `SEION_KGR_CLAIM_MATRIX.md` stands on,
listed once, with where it is checked (if it is) and what breaks if it
fails. Cross-references use the section numbers of
`SEION_KGR_MATHEMATICAL_CONTRACT.md` (§).

An assumption here is either:
- **structural** — enforced by construction/type-checking (Gate 0), so
  violating it should be impossible in a well-formed run, or
- **declared** — a numeric bound (`M`, `ρ`, `L`, `δ`) claimed to hold for
  a specific trained model, checked empirically per run, never proved
  in general.

| ID | Assumption | Kind | Where used | Checked by | If violated |
|---|---|---|---|---|---|
| A1 | `Q_τ^*Q_τ = I` (isometry) for every declared reduced subspace | structural | §II, all of §XII (theorems_v3) | Gate 1: `‖Q*Q-I‖ < 1e-10` in FP64 | Every downstream `P_τ = Q_τQ_τ^*` identity (idempotent, self-adjoint, `E_red=E_proj`) breaks; must be a hard reject, not a warning |
| A2 | Projector `P` is **orthogonal**, not oblique | structural | §VI, §IX, all `k`/`k-1` theorems | Gate 1: `‖P²-P‖`, `‖P*-P‖` | The Pythagorean split `(E_amb)²=(E_proj)²+(E_normal)²` (`docs/theorems_v3/typed_model.md`) requires orthogonality; an oblique projector invalidates the whole `k→k-1` chain, not just degrades it |
| A3 | `μ_v` bounded, `‖μ_v‖_op ≤ M` uniform over nodes in a given tree | declared | §IX–§X (`THM_V3_HOMOGENEOUS_AMBIENT_K`, `..._K_MINUS_ONE`) | measured per-run operator norm estimate; no proof `M` is tight | Bound `k ρ M^{k-1} L_T` becomes non-certified; must fall back to `empirical_error_predictor`, never labeled `certified_bound` |
| A4 | Closure leakage `‖r_v‖_op ≤ ρ` uniform over nodes | declared | same as A3 | `L_closure` sample mean is a *proxy*, not a bound on `ρ` (`docs/definitions/projectors.md`) | Same as A3 — sample-mean closure loss going to zero does not certify `ρ→0` |
| A5 | Every message-passing layer factors as `N_l ∘ C_l` with `C_l` exactly multilinear+projected and `N_l` isolated to LayerNorm/activation/gates | structural (by construction, must be enforced in code) | §VIII | code review / architecture assertion, not a numeric gate | If violated (e.g. a gate mixes into `C_l`), the `k-1` theorem cannot be applied to `C_l` at all — this is the single most likely way to accidentally over-claim a certified bound |
| A6 | Each `N_l` component is `L_v`-Lipschitz with a declared, checked constant | declared | §X (Lipschitz envelope) | must be measured (e.g. spectral norm bound on LN, known Lipschitz constant of the activation) per architecture choice | Without a checked `L_v`, §X's propagated bound is vacuous, not just loose |
| A7 | DAG→signed-tree unrolling triangle sum ignores cross-path cancellation | declared (known-conservative) | §IX | none — flagged conservative by construction | Bound is valid but may be far from tight; never report it as a tight/expected-case number |
| A8 | CP tensor `K_{ℓ,dijk}` reconstruction from `(A,B,C,O)` is the operative object; raw factors are gauge-free only up to `CPLaw`'s declared group (permutation + scale product 1) | structural | §III, §V (contract) | `CPLaw` gauge-invariance tests | Comparing raw factors across seeds/runs (not through reconstruction, scores, or projectors) is meaningless — confirmed empirically in `numerical_study` (pairwise near-orthogonal subspaces at comparable loss) |
| A9 | Cyclic symmetrization `Π_cyc` is imposed, not learned | structural | §IV | by construction (idempotent/self-adjoint identities always hold) | None — but never cite an imposed-symmetry model as evidence the KG data *has* that symmetry |
| A10 | Filippov-identity residual reduction ⟹ 3-Lie algebra | conditional, currently **not** asserted to hold | §V | requires separately verifying `μ` is totally antisymmetric | Do not claim 3-Lie-algebra structure from a low `L_FI` alone |
| A11 | `E_8` residual's specific structure (vs. random/permuted/zero control) causes any measured gain | open, no assumption granted yet | §XII | mandatory control battery (Gate 7, XII) | Until controls run and beat random-matched by a preregistered margin, treat any `E_8`-branch gain as unattributed |
| A12 | Pathwise rank-allocation score is a *sufficient* rank policy on its own | **rejected** — known false in the confirmatory design | §XIII | `applications/adaptive_tensor_network/results/LEVEL1_FINDINGS.md` (loses to `uniform`, `local_error_greedy` at equal budget) | Any rank controller that uses pathwise score alone as final policy contradicts already-collected confirmatory evidence; must combine features per §XIII |
| A13 | Pathwise majorant is an upper bound on true error | `NUMERICALLY_TESTED`, not proved | §XIII, contract correction note | `LEVEL1_FINDINGS.md`: ratio `true/majorant ∈ [0.35,0.93]`, never `>1`, on 100 measured triples | Holds in every case measured so far; still not a proof — must stay labeled `empirical_pathwise_majorant`, never `certified_upper_bound` |
| A14 (renamed A13-inv) | *(retired)* "majorant might not be an upper bound" — the design note flagged this as an open inconsistency | resolved, see contract §I correction | — | — | Superseded; A13 is the correct framing |
| A15 | Reciprocal-relation closure removes the head/tail asymmetry seen in v25's fixed-`E_8` law | conjectural motivation, **not proved** | §II | none yet — must be measured on the v26 reference oracle before claiming | If false, head/tail asymmetry must be diagnosed independently (per-branch scorer, dual evaluators), not assumed fixed by reciprocal closure alone |
| A16 | `‖e_t‖ ≤ C_E` (bounded entity norms) for the score-Lipschitz example | declared, architecture-dependent | §XIV (Proposition 29.1 example) | requires either a hard norm clip or a measured empirical bound per run | Without this, `L_ψ ≤ C_E` does not hold and the state→score bound in §XIV is unavailable |
| A17 | Margin `> 2ε` computed from a *certified* `ε = L_ψ B_state` (not an estimated one) before claiming rank/MRR certification | structural, must be enforced by the code path that emits `Coverage`/`MRR_cert` | §XIV, §XXXI of source note | must be a hard gate: only queries with `ε` traced to A3/A4/A6/A16-checked constants count toward `Q_cert` | Silently using an unchecked or estimated `ε` turns a certificate into an unlabeled heuristic — this is the highest-risk mislabeling path in the whole v26 design |
| A18 | `σ`-finite measure space / separability for the `L^2` kernel extension (§XXXII–XXXV of source note) | declared, only relevant if/when the continuous kernel extension is invoked for KGR | reused from `papers/kernel_integrated_laws_v5/main.tex` | Not needed for the finite discrete KG case; flag explicitly if a future KGR variant tries to invoke the analytic kernel results — the finite-graph measure space is automatically `σ`-finite (counting measure on a finite set), so this is usually free, but state it rather than skip it |
| A19 | Existence of the `t↓0` heat-trace limit defining spectral dimension `d_s` | **not granted**, explicit open hypothesis in the source paper | only relevant if spectral-dimension diagnostics are ever added to KGR | `papers/kernel_integrated_laws_v5/main.tex` remark | Do not compute a "spectral dimension" number for a KG without first checking this limit exists for the specific finite operator used |
| A20 | A finite decreasing sequence of multiscale transport-defect values implies a continuum limit | **rejected** | only relevant if multi-resolution/transfer experiments are added (§XIV of source note, ULTRA-style transfer) | `papers/kernel_integrated_laws_v5/main.tex` explicit remark | Never state a continuum/limit claim from finite-resolution transfer numbers alone |

## Assumptions this ledger deliberately does not grant

These appear as claims or implicit assumptions in the source design
note but are **not** added to the table above as usable assumptions —
they are either already falsified or have no supporting theorem, and
should be treated as `OPEN` in the claim matrix:

- That a low associator/FI/closure energy *causes* better link
  prediction (correlation-vs-causation gap explicitly flagged in the
  source note §VI "no debe suponerse causalidad" — no experiment in
  this repo yet separates KGE-only from KGE+geometric-loss ablations
  for link prediction specifically).
- That the subspace recovered by any single training run is canonical
  or unique — directly contradicted by `numerical_study`'s
  near-orthogonal-subspaces-at-comparable-loss finding.
- That GPU execution is faster than CPU for small/diagnostic-scale
  operations — contradicted by the measured 3.2–3.5× GPU slowdown in
  `numerical_study`'s 208-config sweep; device selection must be by
  problem size, not a CUDA-always-wins default (already encoded as a
  requirement in the v25 postmortem and carried into §IX of the
  Blackwell usage plan).

## Campaign gate12-closeout additions (Phases B3/B4)

| ID | Assumption | Kind | Where used | Checked by | Status |
|---|---|---|---|---|---|
| A21 | CP-factor operator norms (`‖A‖,‖B‖,‖C‖,‖O‖` via top singular value) submultiplicatively bound the CP ternary law's operator norm | structural, mathematically proved (elementwise-product Cauchy-Schwarz + linear operator-norm submultiplicativity — standard facts, not a new theorem) | `seion_kgr/certification.py::cp_law_operator_norm_bound` | `tests/kgr/test_certification.py::test_cp_law_operator_norm_bound_is_never_exceeded_empirically` (500 random unit-norm probes, bound never violated) | Granted — this is the one exact, checked constant the certification chain currently has |
| A22 | Closure-leakage operator norm (`rho_mu`) has no checked bound for a trained `StiefelProjector` at `rank < dim` | declared, explicitly NOT granted | `seion_kgr/certification.py::check_projector_assumptions` | always reports `passed=False` for this specific check when the projector is rank-reducing | Rejected by design — certification correctly refuses whenever this is the case, per A4 above (unchanged, now has live enforcing code) |
| A23 | The path reasoner's `LayerNorm(tanh(...))` envelope has no checked Lipschitz constant | declared, explicitly NOT granted | `seion_kgr/certification.py::check_nonlinear_envelope_assumptions` | always reports `passed=False` when `has_nonlinear_envelope=True` | Rejected by design, per A6 above (unchanged, now has live enforcing code) |
| A24 | A resume, retry, CPU-vs-GPU duplicate, or epoch-budget extension shares the same `configuration_id` as its parent run; only `seed`/`out_dir`/`resume`/run-control fields may differ | structural | `seion_kgr/reproducibility.py::config_identity_hash`, `RUN_CONTROL_FIELDS` | Live-tested: a legitimate resume-for-more-epochs correctly succeeds; a resume with a genuinely different architecture (`--dim` mismatch) correctly fails BEFORE `load_state_dict`, with a clear message | Granted, enforced |
| A25 | The near-zero-init residual gate (`sigmoid(gamma_raw)`, init `≈0.018`) opens meaningfully within a realistic training budget | assumed by the router design (contract §XX.4), NOT verified | none yet — a real 40-epoch run on a small synthetic graph showed the gate essentially unchanged from init | `campaigns/gate12/negative_controls_results.json` | **OPEN, flagged by this campaign** — this is a genuine open question for the Gate 12 confirmatory campaign, not resolved here. If the gate systematically fails to open within normal training budgets on real benchmark data, the entire path/seionic/E8 residual-router design would need revisiting, since a branch that never opens can never be shown to help |
