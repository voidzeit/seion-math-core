# M34 — the interaction decides almost every single step, and almost none of the trajectory

**EXPLORATORY, NOT CONFIRMATORY.** Six states per cell; the trends below are
suggestive, not established.

Raw: `interaction_decision_value_raw.json` (42 states). Analysis:
`interaction_decision_value_analysis.json`.

Measured at a **single base state** (not a trajectory), heterogeneous regime,
D = 16, over a shared candidate pool so every method searches the same set.
`C_I = (E_FO − E_pair) / (E_FO − E_oracle)` is the fraction of the
post-first-order headroom the pairwise term recovers.

## m sweep, b = 3

| m | pool | headroom (rel) | C_I | C_I (low-rank) | flip FO | flip pair | oracle-rank of FO's pick | R_flip median |
|---|---|---|---|---|---|---|---|---|
| 8 | 56 | 0.0078 | **1.000** | 1.000 | 0.33 | 0.00 | 2.3 | 0.95 |
| 14 | 364 | 0.0019 | **0.939** | 0.605 | 0.50 | 0.17 | 1.0 | 1.28 |
| 23 | 1500 | 0.0086 | **1.000** | 1.000 | 0.67 | 0.00 | 12.3 | 3.23 |
| 31 | 1500 | 0.0037 | **1.000** | 0.928 | 0.83 | 0.00 | **29.0** | **6.84** |

## b sweep, m = 23

| b | headroom (rel) | gain (rel) | C_I | flip FO | oracle-rank of FO | R_flip median |
|---|---|---|---|---|---|---|
| 2 | 0.0039 | 0.0039 | 1.000 | 0.50 | 0.8 | 0.84 |
| 3 | 0.0086 | 0.0086 | 1.000 | 0.67 | 12.3 | 3.23 |
| 5 | 0.0150 | 0.0113 | 0.756 | 0.83 | 32.8 | 0.70 |
| 8 | **0.0188** | 0.0121 | **0.696** | 0.83 | 40.0 | 2.95 |

## The apparent contradiction with M33, and its resolution

M33 reported `C_I ≈ 0.24` at m = 14. This pass reports `C_I = 0.939` at the
same m, with the full 364-bundle enumeration — no sampling. Both are correct;
they measure different things.

**M33 measured a six-round trajectory. M34 measures one decision.** Per step,
the pairwise surrogate recovers essentially all of the available headroom and
picks the true optimum in 5 of 6 states. Over six rounds that advantage
collapses to a quarter.

The explanation is that **re-measurement substitutes for modelling**. First
order re-measures `U_v` at every new state, so a suboptimal choice in round `t`
is diagnosed and partly repaired at round `t+1`. Per-step losses do not
compound; the greedy loop is self-correcting. Modelling the interaction buys a
better decision now, and the loop would have recovered most of it anyway.

That is a stronger and more useful statement than either pass alone: the value
of second-order information is real at the level of a single decision and
largely redundant with iteration.

## First order degrades with m — the mechanism is visible

Three independent statistics move together as m grows from 8 to 31:

- `P(argmin_FO ≠ argmin_oracle)` rises **0.33 → 0.83**;
- the oracle-rank of first order's pick rises **2.3 → 29.0** (still inside the
  top 2% of 1500 candidates, but far from optimal);
- `R_flip`, the ratio of the interaction gap to the first-order margin on the
  two leading candidates, rises **0.95 → 6.84**.

`R_flip` is the mechanism M33 could not see. Below 1 the interaction is too
small to reorder the leaders and cannot change the decision; above 1 it can. It
crosses 1 between m = 8 and m = 14 and reaches ~7 at m = 31. As m grows there
are more near-tied first-order candidates and the interaction increasingly
decides among them.

The pairwise surrogate meanwhile finds the pool optimum in every state at
m = 8, 23 and 31 (`flip_pair = 0`).

## b matters differently from m

Growing the bundle raises the stakes but lowers the fraction captured: from
b = 2 to b = 8 the headroom grows 4.8× (0.0039 → 0.0188) while `C_I` falls
1.000 → 0.696. The absolute gain still grows (0.0039 → 0.0121). A bundle of
size b contains `C(b,2)` interacting pairs — 1 at b = 2, 28 at b = 8 — and the
second-order model becomes progressively inadequate as third-order terms enter,
exactly the failure mode M32B found for multi-unit steps.

So the two sweeps say different things: **larger m makes the interaction more
decisive; larger b makes the second-order model less sufficient.**

## What this does and does not license

The decisive question M33 left open — is the small value of `I` structural or
an artifact of m = 14 — now has a two-part answer. **Per decision it is an
artifact**: `C_I ≈ 1` at every m, and first order's decisions get materially
worse with scale. **Per trajectory it may still be structural**, because
iteration repairs the difference, and that was only tested at m = 14.

The decisive follow-up is therefore a **trajectory comparison at m = 31**,
where first order's per-step pick is the 29th best rather than the 1st. If the
self-correction still holds there, the `O(m)` measured-marginal allocator is
the answer and the low-rank machinery is scientifically interesting but
operationally unnecessary. If it does not, the crossover has been located.

## Caveats

- **Six states per cell.** A flip rate of 0.83 is 5 of 6. The monotone trends
  across m are consistent across three statistics, which is reassuring, but no
  single cell is precisely estimated.
- **The oracle is a pool oracle.** At m = 14 the pool is the complete
  enumeration (364 of 364); at m = 23, b = 3 it is 1500 of 1771 (85%); at
  m = 31 it is 1500 of 4495 (33%). Every method searches the same pool so the
  comparison is internally fair, but `E_oracle` at m = 31 is not the global
  optimum, which if anything flatters `C_I`.
- **The headroom is small in absolute terms** — 0.19% to 1.9% of the base
  error. Even a perfect decision rule gains a few percent here. `C_I` is a
  ratio within that band.
- `R_flip` is heavy-tailed (p90 reaches 18–64), so the medians above summarize
  a very skewed distribution.
