# Final delivery report — spectral A-N v18 campaign (2026-07-30)

## Scope and boundary

Track A-N (cyclic CP law / projector / multiscale audit) only. Track T
(projected n-ary tree mathematics) was explicitly deferred by an accepted
mid-campaign checkpoint and is untouched — see
`.ai/SPECTRAL_TRACK_ROADMAP.md` and
`docs/research/spectral_a_to_n_v18/PAPER_2_DEFERRAL_DECISION.md`. Nothing
in this campaign edits or is certified by `CANONICAL_FINITE_CORE`
(`src/seion_core`), which keeps its own separate, pre-existing status.

## Branch and commits

Branch `program/seion-canonical-repository-v4`, three new commits on top
of the accepted `427ad52` handoff:

1. `d7b9941` — Phase 0 legacy ingestion + `SPECTRAL_LEGACY_TRACK` scope class.
2. `5c102af` — v18 certification suite (typed gates, all 14 blocks, fail-closed evaluation).
3. `558a590` — Release products (3 papers, atlas, truth report, CI workflow).

No force-push, no history rewrite, no destructive operation. Pre-existing
uncommitted changes at session start (`.obsidian/*`,
`docs/governance/reference_practice_review.md`, `docs/graph/README.md`,
`docs/research/truth_audit_2026_07_29/`) were left untouched and unstaged,
not mine to commit. The two original legacy files at `spectral/` root and
`spectral/runs/` remain untracked and unmodified, per the mission's own
"preserve without modifying originals" instruction — their hash-verified
copies live at `spectral/legacy/v17/`.

## Hardware and compute

Intel Core Ultra 9 285HX (24 logical cores), 128 GB RAM, NVIDIA RTX PRO
5000 Blackwell Laptop GPU (24 GB VRAM, CUDA 12.8, driver 573.49) — all
confirmed by direct query, not assumed. Actual usage this pass: CPU
dominant (every block's experiments ran on CPU by explicit device
choice, since problem sizes were small, n<=24); one real GPU dispatch
performed (Block A/B CPU-vs-CUDA parity check, wall time 835 ms on GPU
vs 19 ms on CPU — GPU kernel-launch overhead dominates at this scale, an
honest finding, not a success to oversell). Total GPU-seconds used this
pass: well under 1 second of actual kernel time. **This is a real gap**:
mission section 4 asked for aggressive, batched GPU use for screening
sweeps; this pass validated GPU correctness (parity) but did not exploit
GPU throughput at scale, because no large sweep was executed (see "Sweep
coverage" below).

## Test and experiment counts

- 85 automated tests, all passing (`pytest spectral/certification_v18/tests`).
- 14 blocks (A-N) each have a dedicated module, findings doc, and test file.
- 3 blocks (B, E/J/M) received the deepest treatment: a 7-regime ablation
  matrix (Block B) and a 3-independent-resolution transport + persistence
  experiment (Block E, reused for J and M).
- Legacy evidence: 19 unique historical runs ingested, hashed, lineage-
  reconstructed, and reclassified.

## Screening vs certification

**Every experiment in this pass ran in the screening-tier sense**: single
seed per configuration (except where explicitly noted — Block B's
capacity test used 5 seeds, its held-out ablation used 30+20 instances),
float64 throughout but without the full certification-mode discipline
(held-out seeds distinct from training, strict/restored-RNG resume) wired
through every experiment script — only `config.py`'s contract and the
`hardware/certification_mode.py` TF32/determinism enforcement were
actually exercised end-to-end (in the CPU/GPU parity check). **No result
in this pass claims `VALIDATED_NUMERICAL_CERTIFICATE` or
`EXACT_CERTIFICATE` for any scientific (non-structural, non-formula)
claim** — consistent with the mission's own rule that a screening run may
never emit certificate language, enforced in code by
`gates.py:assign_block_status`.

## Block-by-block final verdict

See `docs/research/spectral_a_to_n_v18/TRUTH_AND_NOVELTY_REPORT.md` for
the full table (status + basis per block) and
`papers/a_to_n_certification_v18/main.pdf` for the full writeup. Summary:

- **Refuted (scientific claim fails)**: B (commutator explanation, worse
  than zero predictor in all 15 real checkpoints), E (interscale
  transport, no signal beyond baselines), J (tensor interscale, same
  experiment), M (persistent factorization, rank-inconsistent across
  resolutions, one unexplained aligned mode).
- **Structural identity / exact (true by construction or exact
  computation, not a scientific claim)**: A (projector idempotence), N
  (symmetrized cyclic defect; GJI formula cross-validated to 1e-16), I
  (rational small case), L (residual-gauge detection logic).
- **Empirical / statistically validated (real but limited evidence)**: C,
  D, F, G, H, K — single-configuration or single-seed results, explicitly
  not certified.
- **Open**: Block H's associator-constant sharpness (bound 2, best found
  0.452), Block N's GJI-ratio supremum (adversarial max 5.98, not shown
  bounded), Block M's one anomalous aligned mode.

## B/J/M final diagnosis

**B**: not malformed, not capacity-limited in isolation (drives residual
to ~0 alone), yet worse than zero in every real deployed checkpoint. The
7-regime ablation matrix identifies the mechanism precisely: genuine
conflict with the associator/GJI-family objective (~100x degradation when
trained jointly vs isolated), and the fit is substantially a `Phi`
curve-fit independent of the learned subspace (`frozen_projector_train_law`
reaches exactly 0 with `U` never trained). Not gradient starvation (staged
training recovers quickly), not scale imbalance alone (conflict appears
even at equal weight).

**J/M**: real, non-circular three-resolution experiment (independently
trained, frozen transfer, principal angles, random + interpolation
baselines) finds no persistence signal — all transport angles near
maximal orthogonality, rank inconsistent across scales — except one
single aligned mode (12-vs-18, mode 2, angle 1.5e-8 rad) left as an
explicit open anomaly, not smoothed into either a pass or a uniform fail.

## Counterexamples and negative controls that fired correctly

- Block D: an explicit gap-closing perturbation (`eps=1.2`) reproduces
  rank misrecovery, confirming the Davis-Kahan-style gap condition is
  necessary.
- Block A: a deliberately broken (non-conjugate-transpose) "projector" is
  confirmed to fail self-adjointness.
- Block K/M: an independent random-tensor / random-subspace null is
  confirmed to score worse (or tie) the real structure, as required.
- **Block M's own development caught a real bug**: an early comparison
  tool (free-unitary Procrustes on subspace bases) is mathematically
  vacuous and silently passed independent random tensors as
  gauge-equivalent. Caught by the block's own required negative control,
  fixed with principal angles, documented prominently in `gauge_utils.py`
  so it cannot recur in block L.
- Block F: an early gauge-invariance test loss was NOT actually
  gauge-invariant (0.87% discrepancy caught by the test), fixed by
  summing the residual over all columns instead of one.
- Block N: a deliberate sign mutation in the GJI formula is confirmed
  detected by the cross-check against an independent implementation.

## Sweep coverage — explicit, not silently capped

**No adaptive multi-cell sweep was executed this pass.** Every block's
result is single-configuration (or a handful of seeds), not a swept grid
across arity/dimension/rank/CP-rank/eta as mission sections 5-6 describe.
This is the single largest gap between what was asked and what was
delivered: the infrastructure to run one (job queue, certification-mode
contract, hardware inventory) is built and tested, but it was not pointed
at a real multi-cell campaign. Tracked in `.ai/SPECTRAL_TRACK_ROADMAP.md`
as explicit follow-up, not hidden behind aggregate language.

## Figures and papers

- `papers/a_to_n_certification_v18/main.pdf` — 4 pages, compiled, every
  page inspected visually.
- `papers/software_reproducibility_v5/main.pdf` — 3 pages, compiled,
  inspected.
- `papers/supplementary_visual_atlas_v18/main.pdf` — 6 pages, 7 figures,
  compiled, inspected; explicitly lists what a fuller 20-figure atlas
  would still need (topology/dimension/eta surfaces, gauge-orbit atlas,
  GJI permutation atlas, multi-block precision-parity grid).
- Paper 2 (finite projected n-ary mathematics) deliberately not written —
  see `PAPER_2_DEFERRAL_DECISION.md`.

## CI, packaging, security

- Added `.github/workflows/spectral-v18.yml` (new CPU test workflow for
  this track; none existed before this pass). Not verified against an
  actual GitHub Actions run (no push to a remote was requested or made).
- Did not inspect or attempt to repair the repository's other,
  pre-existing workflows (`canonical-v4.yml`, `numerical.yml`,
  `reproducibility.yml`, `scheduled-v4.yml`, `symbolic.yml`, `docs.yml`)
  — those belong to the separate `CANONICAL_FINITE_CORE` track and no
  evidence was gathered this pass about whether they currently pass or
  fail; fixing them would be out of this track's scope regardless.
- No SBOM or dependency audit was generated for this track specifically.

## Final fail-closed gate decision

Computed, not narrated — `python -m spectral.certification_v18.final_gate_evaluation`,
output in `spectral/certification_v18/artifacts/final_gate_evaluation.json`:

```
final_state: FAIL_CLOSED_PROJECTOR_GATE_NOT_ESTABLISHED
passed_gates: [gauge_gate, mathematical_proof_gate]
failing_gates: [projector_gate, algebra_gate, dynamic_explanation_gate,
                interscale_gate, persistence_gate, reproducibility_gate]
```

Six of eight critical gates fall below the screening-tier passing minimum.
Note a genuinely informative, non-obvious consequence of the typed-state
ranking: `projector_gate` and `algebra_gate` fail not because anything in
them is wrong, but because their evidence is partly
`STRUCTURAL_IDENTITY_PASS` (Blocks A, N) — which the taxonomy correctly
does NOT treat as sufficient for a scientific screening-tier claim, exactly
matching those blocks' own documented non-implication ("this certifies
construction, not scientific relevance"). This is the fail-closed design
working as intended, not a defect. `reproducibility_gate` is `WARN`
because this pass's own experiments were largely single-seed and the
legacy lineage is non-strict-resume throughout — an honest self-assessment,
not exempted from its own standard.

**No process in this campaign self-issues `PASS_A_TO_N_FULL_CERTIFICATION`.**
That state does not exist as a reachable output of
`evaluate_global_certificate` at all. The most this pass could ever
produce is `PASS_A_TO_N_PARTIAL_CERTIFICATION`, and the actual computed
result is a `FAIL_CLOSED_*` state, pending human review, exactly as the
mission's own governing rule requires.

## What was established, what was refuted, what remains unknown

**Established** (exact or near-exact, no floating-point tolerance
involved beyond machine epsilon): the commutator/rank identities in
`model.py`; the GJI formula's internal consistency (two independent
implementations, 1e-16 agreement); the Hessian/GGN distinction and the
gauge-flat-direction identity; the Pythagorean associator decomposition;
that principal angles (not free-unitary Procrustes) are the correct
subspace-comparison tool, demonstrated both by where Procrustes fails and
where principal angles correctly pass a within-subspace-rotation control.

**Refuted**: the coherent-dynamic-curvature explanation as a real,
deployed-regime phenomenon (Block B); interscale subspace and tensor
persistence under a closure-only objective across three independent
resolutions (Blocks E/J/M); single-objective basin stability (Block F).
Each refutation is treated as a completed, successful scientific result,
not a failure of this campaign.

**Remains unknown**: whether Blocks E/J/M's negative results persist under
the full historical multi-objective loss (not reproduced this pass);
Block H's associator-constant sharpness; Block N's GJI-ratio supremum;
Block M's one anomalous aligned mode; whether any methodological
correction made here (principal angles over Procrustes, the gauge-
invariant loss fix) constitutes genuine novelty (no literature search was
performed — `NOVELTY_UNESTABLISHED` throughout); the entirety of Track T.
