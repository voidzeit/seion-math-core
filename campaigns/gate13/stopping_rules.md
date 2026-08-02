# Gate 13 stopping rules

## Sequencing (mandate §12, verbatim order)

`activar -> vectorizar -> atribuir -> certificar -> ablar -> confirmar -> comparar`

Concretely: 13.0 (freeze) -> 13.1 (router) -> 13.2 (reasoner) -> 13.3
(attribution) -> 13.4 (certification) -> 13.5 (screening) -> 13.6
(confirmatory) -> 13.7 (E8 block) -> 13.8 (rank/Pareto) -> 13.9
(generalization) -> 13.10 (SOTA comparison).

No gate may be skipped. Each gate below must reach its named `PASS_*`
condition, checked by an executable test in `tests/kgr/`, before the next
gate's code is exercised against a real dataset (unit-level implementation
work for a later gate may proceed in parallel, but its benchmark execution
does not start early).

## Per-gate stop/go conditions

- **13.1 Router activation** — stop condition: `PASS_ROUTER_ACTIVATION`
  (see `hypotheses.yaml` / `preregistration.md` §3). If the synthetic
  path-required task fails to move the gate even with a 5-10x router
  learning-rate multiplier, do not proceed to 13.5 — instead widen the
  synthetic task or increase the multiplier and re-test; this is an
  engineering gate, not a statistical one, so it can be iterated on
  directly (unlike H1-H4, which are frozen at preregistration).
- **13.2 Vectorized reasoner** — stop condition: `PASS_PATH_SCALING`
  (parity + full-epoch completion, see `preregistration.md` §4).
- **13.3 Attribution** — stop condition: `PASS_ATTRIBUTION_CONSERVATION`
  (telescoping sum reconstructs the observed error exactly; Shapley
  efficiency holds; a corrupted module concentrates attribution; an
  identical module receives zero attribution).
- **13.4 Certification** — stop condition: `CERTIFIED_COMPRESSED_COVERAGE >
  0` on at least one real compressed-model configuration, with zero
  observed violations among certified queries.
- **13.5 Screening** — validation-only, 3 seeds, no test-set inspection;
  finalist selection uses Gate 12 mandate §C4's rule verbatim.
- **13.6 Confirmatory** — 5 seeds, 2 datasets, full filtered evaluation,
  paired bootstrap + Holm correction; pass condition is
  `LCB_95%(delta_MRR) > 0` per comparison, `median(delta_MRR) >= 0.005`.
- **13.7-13.10** — as specified in the mission brief §6-§11.

## Global stop conditions (apply at any gate)

- A negative control that should degrade performance does not (leakage
  suspected) -> halt, investigate, do not report any result from that run
  as valid until resolved.
- A protocol mismatch between arms being compared (different data size,
  epoch budget, evaluator, or device) -> halt that comparison, log as a
  deviation, do not draw a causal conclusion from it (this is exactly the
  Gate 12 A0/A3 confound this campaign exists to prevent from recurring).
- Session compute budget exhausted -> stop at the current gate, mark
  everything past it `OPEN` with the exact commands needed to resume, per
  the same honest-disclosure convention as Gate 12 preregistration §0.

## What ends the campaign (mandate §14)

Gate 13 (and the project) is "terminado" not when every row is `PASS`, but
when every claim in the mission brief's §13 matrix has an executed
verdict — `PASS`, `FAIL`, `INCONCLUSIVE`, or `OPEN` — with reproducible
evidence, including negative results reported as such rather than omitted.
