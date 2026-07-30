# Theorem-to-theorem novelty audit (SEION V5 Phase 9)

Exit-gate record for `PASS_NOVELTY_MATRIX_COMPLETE`. Per mission section
9 and this project's own governance model, **no verdict here is
self-approved** — every row's `human_decision` is `PENDING_HUMAN_REVIEW`.
This document assembles candidate verdicts from real primary-source
searches for human adjudication; it is evidence for that review, not a
substitute for it.

## Part 1 — Track T claims (existing search, verified this pass)

`claims/prior_art_registry_v3.yaml` (12 entries, dated 2026-07-29) already
covers most of the mission's Track T priority claims (projected-root
k-1 improvement, mixed-mask calculus, path-sum certificate, C_T^P(eta),
optimal telescoping, signed-forest cancellation). **Spot-checked 2 of 12
citations this pass** rather than trusting the registry blindly:

- `PA_V3_ABSTRACT_INTERPRETATION` -> Gehr et al., "AI2: Safety and
  Robustness Certification of Neural Networks with Abstract
  Interpretation," IEEE S&P 2018, pp. 3-18 — confirmed real, title/venue/
  page numbers match.
- `PA_V3_LAYERED_LIPSCHITZ` -> Combettes & Pesquet, "Lipschitz
  Certificates for Layered Network Structures Driven by Averaged
  Activation Operators," SIAM J. Mathematics of Data Science 2(2),
  529-557, 2020 — confirmed real, title/venue/pages match.

Both real, both accurately described. No red flags in this sample; the
remaining 10 entries were not independently re-verified this pass (a
larger spot-check is recommended before human sign-off, not a full
re-verification of every entry given time constraints this session).

**Existing verdicts, mostly `NOVELTY_NOT_ESTABLISHED`** (the registry's
own honest default — absence of an exact match is explicitly *not*
treated as evidence of novelty per its own stated policy) with 3 entries
at `KNOWN_BOUND_NEW_SPECIALIZATION` and 2 at
`STANDARD_RESTRICTION_RESULT`/`STANDARD_MULTILINEAR_BOUND`. None claim
outright `NOVEL`. This is consistent with, and should be read alongside,
this session's own Phase 6-8 findings that the core k/(k-1) theorem is
`PROVED_UNDER_ASSUMPTIONS` but sharpness remains open — a claim without
resolved sharpness is a weaker candidate for strong novelty language
regardless of what the literature search finds.

**Not independently re-run this pass**: claim 6 (signed-forest
cancellation-aware constants) predates this session's Phase 8 findings
(the `named_gji_variants` apparent identity, the Jacobiator `SHARP`
result). Those specific *numerical* findings have no corresponding
literature search entry yet — flagged as a gap below.

## Part 2 — SPECTRAL_LEGACY_TRACK / methodology claims (new searches, this pass)

These claims (mission's priority items 8, 9, 10) had **no prior literature
search anywhere in the SPECTRAL_LEGACY_TRACK's history**
(`NOVELTY_UNESTABLISHED` was the honest standing state per
`docs/research/spectral_a_to_n_v18/TRUTH_AND_NOVELTY_REPORT.md`). Real
searches run this pass:

### Claim 8 — Fail-closed A-N certification methodology (typed gate taxonomy, screening/certification tier separation enforced in code)

| Field | Value |
|---|---|
| SEION statement | 10 typed evidence states + critical-gate taxonomy where a gate's status is the minimum over contributing blocks (never averaged), enforced structurally so `eval_mode=screening` code paths cannot emit a certificate-tier status |
| Closest prior art found | Kim, "From Forecasting Leaderboards to Deployment Decisions: A Fail-Closed Certification Protocol," arXiv:2606.24996 (2026-06-25) — fail-closed evaluation gates as sufficient (not merely necessary) evidential conditions before deployment authorization, in a weather-forecasting deployment context. Separately: SLSA (Supply-chain Levels for Software Artifacts, OpenSSF) — typed provenance levels with fail-closed verification for software supply-chain artifacts. Separately: DO-178C/ISO 26262/IEC 61508 — typed evidence categories for safety-critical certification, requiring a shared ontology to map verification artifacts to standard-recognized evidence categories (a live, unsolved problem per the search results, not a solved one). |
| Object class | Different in every case — none of these apply typed fail-closed gates to *mathematical/scientific claim certification* specifically; forecasting deployment, software supply chain, and safety-critical hardware/software are all distinct domains from "is this numerical experiment result strong enough evidence for this theorem status." |
| Shared content | The core methodological pattern — typed states, minimum-not-average gate combination, fail-closed default, screening/certification separation preventing silent promotion — is structurally similar across all of these. |
| Candidate verdict | `KNOWN_TECHNIQUE_NEW_APPLICATION` — the fail-closed typed-gate pattern is not new in general (it recurs across at least 3 unrelated domains found in one search pass), but applying it specifically to certifying mathematical/numerical research claims (vs. deployment authorization, supply-chain provenance, or hardware safety) was not found in this search. |
| Confidence | Low-to-medium — single search pass, 2 queries, not exhaustive. A dedicated search of the ML reproducibility/registered-reports literature (which is closer in spirit) was not done this pass. |
| `human_decision` | `PENDING_HUMAN_REVIEW` |

### Claim 9 — Legacy-lineage reclassification methodology (reclassifying historical runs as screening/replay evidence via hash-based deduplication and scientific-instance-identity distinct from execution-identity)

| Field | Value |
|---|---|
| SEION statement | `scientific_instance_id` (the question) vs. `execution_id` (one attempt) vs. `optimizer_restart_id` (one resume) as three distinct identity levels, with automated deduplication collapsing repeated executions of the same scientific instance and a "resumed run with restored RNG is not an independent seed" invariant |
| Closest prior art found | MLflow2PROV and general ML pipeline provenance tooling (arXiv:2507.01075, ScienceDirect provenance-capture literature) — track lineage/versioning of ML artifacts through pipeline stages. None found that specifically distinguish "same scientific question, different execution attempt" from "same execution, different optimizer restart" as a formal identity hierarchy with fail-closed consequences (e.g., forbidding a restored-RNG resume from counting as a fresh independent seed). |
| Object class | General ML provenance tooling tracks artifacts/lineage for reproducibility and governance; it was not found to encode this specific 3-level scientific-identity distinction with epistemic consequences (what counts as independent replication vs. what doesn't). |
| Candidate verdict | `NEW_SPECIALIZATION` (tentative) — the general practice of provenance/lineage tracking is well-established and not claimed as novel; the specific 3-level identity hierarchy tied to epistemic validity (not just bookkeeping) was not found as a named, prior pattern in this search. |
| Confidence | Low — 1 search pass. The clinical-trials/registered-reports literature (which has a mature "pre-registration vs. replication vs. re-analysis of the same data" distinction) is a plausible closer match not yet searched. |
| `human_decision` | `PENDING_HUMAN_REVIEW` |

### Claim 10 — Capacity-versus-deployment distinction for Block B

| Field | Value |
|---|---|
| SEION statement | Block B's finding that `frozen_projector_train_law` reaches near-zero unexplained-residual with the projector *never trained* (a curve-fit through the law's own parameters), while the actual deployed joint-training regime fails outright — i.e. the model has the *capacity* to fit the explanation in isolation but the explanation does not hold once actually deployed/trained jointly |
| Closest prior art found | D'Amour et al., "Underspecification Presents Challenges for Credibility in Modern Machine Learning," JMLR 23 (2022) — directly on-point: an ML pipeline is underspecified when many predictors achieve equivalent held-out/training performance but behave very differently once stress-tested or deployed; explicitly distinct from ordinary train/deployment structural mismatch. This is a strong match in *pattern* (multiple equivalently-scoring explanations, one deployed regime breaks the tie) though D'Amour's setting is general supervised-learning deployment shift, not this specific frozen-projector/curve-fit mechanism. |
| Object class | D'Amour: broad empirical survey across vision/NLP/genomics pipelines, model-agnostic. SEION Block B: one specific mechanistic diagnosis (frozen-vs-trained projector ablation) within one specific finite-dimensional algebraic model. |
| Genuine difference | SEION's finding is mechanistic and ablation-based (identifies *which* component's freezing causes the spurious fit), not just an observational deployment-shift audit. |
| Candidate verdict | `KNOWN_RESULT_NEW_PROOF` / `NEW_SPECIALIZATION` boundary case — the underspecification *phenomenon* is established (D'Amour), but SEION's specific frozen-projector ablation as a *diagnostic mechanism* for identifying it in a finite algebraic model was not found elsewhere in this search. Genuinely closer to the literature than claims 8/9 above — this is the strongest candidate of the three new searches for being "the same known phenomenon, demonstrated by a new specific mechanism" rather than something wholly novel. |
| Confidence | Medium — the D'Amour match is strong and specific, found on the first search. |
| `human_decision` | `PENDING_HUMAN_REVIEW` |

## Part 3 — Gap not covered this pass

This session's own Phase 8 signed-forest findings (Jacobiator `SHARP`,
`named_gji_variants` apparent structural identity) have **no literature
search entry** — they are new numerical findings from *this session*,
not yet checked against prior art on Jacobi-identity/Filippov-identity
"sharpness" results in the non-associative algebra literature. This is
the single most concrete follow-up this document identifies: a targeted
search on "Filippov algebra fundamental identity constant," "Akivis
algebra defect bounds," and "n-Lie algebra Jacobiator sharpness" before
any human review of Phase 8's `SHARP`/`OPEN_WITH_CERTIFIED_GAP` verdicts.

## Summary

| Claim | Verdict (candidate) | Confidence | Human decision |
|---|---|---|---|
| 1-5, 7 (Track T core) | mostly `NOVELTY_NOT_ESTABLISHED`, some `KNOWN_BOUND_NEW_SPECIALIZATION` | pre-existing, 2/12 spot-checked this pass | `PENDING_HUMAN_REVIEW` |
| 6 (signed-forest constants) | not searched this pass — gap | — | `PENDING_HUMAN_REVIEW` |
| 8 (fail-closed A-N methodology) | `KNOWN_TECHNIQUE_NEW_APPLICATION` | low-medium | `PENDING_HUMAN_REVIEW` |
| 9 (legacy-lineage reclassification) | `NEW_SPECIALIZATION` (tentative) | low | `PENDING_HUMAN_REVIEW` |
| 10 (Block B capacity-vs-deployment) | `KNOWN_RESULT_NEW_PROOF`/`NEW_SPECIALIZATION` boundary | medium | `PENDING_HUMAN_REVIEW` |

No claim in this document is marked `NOVEL` outright — every candidate
verdict here identifies genuine prior art in the same neighborhood, which
is itself useful information (it means these claims should be positioned
as specializations/new applications/new mechanisms in any eventual paper,
not as "first ever" claims) rather than a failure of the search.
