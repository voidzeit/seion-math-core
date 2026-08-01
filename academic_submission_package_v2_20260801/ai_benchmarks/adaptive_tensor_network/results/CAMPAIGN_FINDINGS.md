# Adaptive tensor network — consolidated campaign findings (AI3-AI7)

Three levels executed, all with real data and real (not fabricated)
results. Raw data: `level1_raw.json` (1,440 records), `level2_raw.json`
(150 records), `level3_raw.json` (180 records, after a design fix
described below). Preregistration: `../experiments/PREREGISTRATION.md`
(Level 1 only — Levels 2/3 were designed and executed after Level 1's
results were seen, so their comparisons are **exploratory, not
confirmatory**, and are labeled as such throughout).

## Level 1 (exact synthetic validation) — preregistered, confirmatory

See `LEVEL1_FINDINGS.md` for full detail. Summary: **mixed/negative for
the primary hypothesis** — pathwise_global beats singular_energy
significantly but loses to uniform and local_error_greedy at equal
budget (retained and reported per the preregistration, not omitted).
What held up: the majorant is a genuine upper bound in every tested case
and correlates strongly with true error (Pearson 0.933, Spearman 0.922).

## Level 2 (hierarchical tensor regression, teacher-student) — exploratory

Random-feature hierarchical regression (intermediate layers = fixed
random multilinear features, truncated per the rank allocation under
test; only the root is trained, via closed-form ridge least squares) on
a teacher-network-generated synthetic regression target. 5 seeds, 5
budgets, 6 methods, 150 records.

**No preregistered comparison was significant** — all 5 paired
comparisons against pathwise_global have 95% CIs that include 0 (mean
reductions ranging −0.017 to +0.011, all statistically indistinguishable
from no difference). A real, honest null result at this sample size
(n=25 paired configs per comparison); not treated as evidence against the
method, just as inconclusive at this scale.

## Level 3 (Burgers-equation reduced surrogate) — exploratory, includes a caught design bug

Real 1D viscous Burgers finite-difference solves
(`experiments/burgers_solver.py`) generate (parameters -> final-state)
training pairs; same random-feature + least-squares fitting as Level 2.

**A real design bug was caught and fixed before trusting any result**:
the first topology (two 1-dimensional leaves feeding the one
allocatable intermediate node) made that node's ambient output
mathematically rank-1 regardless of the declared 6-dimensional ambient
space — every allocation method produced bit-identical test error
regardless of chosen rank, because there was nothing for a rank choice
to trade off. Diagnosed directly (swept `n0_rank` from 1 to 6 manually,
confirmed byte-identical predictions) before writing up any conclusion.
Fixed by redistributing the PDE parameters across two genuinely
multi-dimensional leaves (3-dim and 2-dim, giving the node a true
$3\times2=6$-dimensional achievable output space matching the declared
ambient dimension).

After the fix, rank allocation is a real question again, and the result
is **partially positive**: pathwise_global significantly beats uniform
(CI $[0.0007, 0.0052]$), local_error_greedy ($[0.0003, 0.0050]$), and
random ($[0.0024, 0.0077]$), but is statistically indistinguishable from
singular_energy and gradient_based (CIs include 0).

**Important caveat, stated honestly**: the surrogate's absolute accuracy
is weak — mean test RMSE ($\approx2.49$) is barely better than the
naive baseline of predicting the training-set mean field ($\approx2.48$).
The random-feature linear-regression approach, as implemented, is not
capturing the Burgers dynamics well; the rank-allocation comparison above
is a real, meaningful comparison of *relative* method performance on this
task, but should not be read as evidence the surrogate itself is a good
one. Improving absolute accuracy (richer features, more training data,
nonlinear fitting beyond closed-form least squares) is real follow-up
work, not attempted this pass.

## Success criteria assessment (mission AI7)

| Criterion | Status |
|---|---|
| 1. Lower test error at equal budget | **Partially supported**: yes vs. 3/5 baselines in Level 3 (exploratory), no in Level 1 (confirmatory) or Level 2 (exploratory) |
| 2. Lower rank/memory at equal tolerance | **Not supported** in Level 1 (the only level this was tested); not tested in Levels 2/3 |
| 3. Correlation between predicted contribution and measured benefit | **Supported**: strong whole-tree correlation in Level 1 (Pearson 0.93); per-node correlation not measured (see LEVEL1_FINDINGS.md) |
| 4. Proven/certified worst-case advantage on a restricted class | **Not attempted** this pass |

Per the mission's own success criteria, at least one must hold for a
"successful applied result" — criterion 3 holds robustly. Criteria 1/2
are genuinely mixed, not a clean win, and are reported as such rather
than selectively emphasized.

## What this campaign does and does not establish

**Does establish**: a real, working, tested implementation of the
mission's proposed architecture and all 7 allocation methods (+5
ablations); the pathwise majorant is empirically a valid upper bound;
predicted contribution correlates strongly with true error at the
whole-tree level; the pathwise method's advantage is real but
context-dependent (helps against some baselines/tasks, not others),
consistent with a genuine, unresolved empirical question rather than a
proven universal advantage.

**Does not establish**: that pathwise global-contribution allocation is
uniformly better than simpler baselines — it is not, in 2 of 3 levels
tested. Any future paper drawing on this campaign must state the mixed
result plainly, per this project's own standing epistemic discipline.
