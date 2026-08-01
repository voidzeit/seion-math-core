# Track T terminal status for k=2 and k=3 (SEION V5 Phase 6/7)

This document is the exit-gate record for mission Phase 6 (k=2) and
Phase 7 (k=3). It does not present new mathematics — it verifies and
formally synthesizes prior work already committed to this repository
(`research/nodewise-tree-constants-v3` lineage, merged into this branch's
history at commit `a39de80`), which was left as an open, honestly-labeled
blocker (`BLOCK-V4-MATH-SHARPNESS` in
`artifacts/release_v4/final_canonical_handoff.md`) rather than a vague
"still exploring" state. This document replaces that vague label with the
mission's precise typed terminal states.

**Verified before writing this document**: read
`docs/theorems_v3/homogeneous_constants.md` in full; ran
`pytest tests/research_v3/` (30/30 passed); recomputed the exact/lower/gap
statistics below directly from `artifacts/index/constants_atlas_v3.csv`
(7,065 rows) rather than trusting a prior summary.

## 1. The proved general theorem

`THM_V3_HOMOGENEOUS_AMBIENT_K` and `THM_V3_PROJECTED_ROOT_K_MINUS_ONE`
(`claims/theorem_registry_v3.yaml`), proved in
`docs/theorems_v3/homogeneous_constants.md` by induction on tree
structure (multilinear telescoping + contractive-projection bound at
each node): for any finite typed tree `T` with heterogeneous laws/types/
arities, node-law operator norm bound `M`, node-closure norm bound `rho`,
`k = k(T)` internal nodes, `L_T = prod_leaf ||z_leaf||`:

```
E_T^amb    <= k(T)     * rho * M^(k(T)-1) * L_T
E_T^proj = E_T^red <= (k(T)-1) * rho * M^(k(T)-1) * L_T
E_T^normal <= k(T)     * rho * M^(k(T)-1) * L_T
```

**Epistemic status**: `PROVED_UNDER_ASSUMPTIONS` (bounded `M`, bounded
`rho`). This is unconditional for k=0 (all errors zero) and k=1
(projected/reduced error exactly zero) — those base cases are exact, not
merely bounded.

**What the proof explicitly does not claim** (stated in its own "What
this proves — and what it does not" section, confirmed by re-reading):
that `k` or `k-1` is *attained* (sharp) at any fixed `eta = rho/M > 0`,
dimension, rank, topology, or repeated-law class. Fixed-`eta` optimality
is stated as "an optimization problem," not resolved.

## 2. k=2 — certified sharpness landscape (513 atlas rows, block A)

Recomputed directly from the atlas (not asserted from memory):

| error_type | rows | rows at `global_optimum_certified=True` | min relative gap (non-exact rows) | max relative gap |
|---|---|---|---|---|
| projected | 75 | 6 | 0.0 (exact rows excluded) | 1.0 |
| ambient | 75 | 0 | 3.75e-7 | 1.0 |
| normal | 75 | 0 | 5.00e-7 | 1.0 |

Interpretation, consistent with the proof's own caveat: the certified
lower-bound construction (`rotation_extremizer` /
`src/seion_core/research_v3/extremizers.py`, an explicit gated planar
rotation with certified multilinear operator norm exactly 1 and closure
norm exactly `eta`) reaches the *exact* `k-1` optimal constant
(`EXACT_OPTIMAL_CONSTANT`, gap 0) for 6 of 75 projected-error
configurations — specific `(eta, dimension, projector_rank)` triples in
the homogeneous single-repeated-law regime. For the remaining
configurations, and for the ambient/normal error types entirely, the
certified gap ranges from near-zero (as `eta -> 0`, matching the proof's
own asymptotic remark) up to a full 100% relative gap at larger `eta` /
different topologies. No row anywhere reaches
`global_optimum_certified=True` for ambient or normal error at k=2.

**Terminal state: `OPEN_K2_WITH_CERTIFIED_GAP`.**

Precise frontier: the ambient/normal `k` coefficient and the general
(non-homogeneous-rotation, general-topology) projected `k-1` coefficient
are proved as universal upper bounds and are NOT proved sharp; a
certified numerical gap exists between the proved upper bound and the
best certified lower construction, and that gap is configuration-
dependent (shrinks toward 0 as `eta -> 0`, grows toward the full bound at
larger `eta`). The projected `k-1` coefficient IS proved exactly sharp
(gap 0, `EXACT_OPTIMAL_CONSTANT`) in the specific homogeneous
gated-rotation construction at the 6 certified configurations. This is
not `PROVED_EXACT_K2_CONSTANT` (sharpness is not universal) and not
`REFUTED_K2_STRONG_FORM_WITH_CORRECT_REPLACEMENT` (no counterexample to
the k/k-1 upper bound itself was found — every one of the 7,065 atlas
rows is consistent with it).

## 3. k=3 — certified sharpness landscape (1,053 atlas rows)

| error_type | rows | rows at `global_optimum_certified=True` | min relative gap | max relative gap |
|---|---|---|---|---|
| projected | 255 | 0 | 0.350 | 1.0 |
| ambient | 255 | 0 | 8.33e-7 | 1.0 |
| normal | 255 | 0 | 1.33e-6 | 1.0 |

At k=3 the certified lower-bound construction never reaches the proved
upper bound for *any* configuration or error type — the projected-error
gap floor rises sharply (minimum 35%, vs. exact matches available at
k=2), consistent with the single-topology gated-rotation construction not
generalizing cleanly across the additional composition step at k=3
without further extremizer work per topology (mission Phase 7 explicitly
calls for enumerating every nonisomorphic k=3 topology separately — that
per-topology enumeration was not re-derived in this pass; the atlas's 255
projected rows span the topologies the v3 pipeline already generated,
not a from-scratch new enumeration).

**Terminal state: `OPEN_K3_WITH_CERTIFIED_TOPOLOGY_GAPS`.**

## 4. What this document changes and does not change

Changes: replaces the vague `BLOCK-V4-MATH-SHARPNESS` ("not complete")
with the mission's exact typed terminal states above, backed by
re-verified numbers.

Does not change: `claims/theorem_registry_v3.yaml`'s
`approval_status: PENDING_HUMAN_REVIEW` on both underlying theorems is
left untouched — per this project's own governance model, no AI process
self-approves a theorem or novelty verdict (mission section 9 states this
explicitly). This document is evidence for that human review, not a
substitute for it. It also does not attempt a new sharpness proof or
refutation — narrowing or closing this gap further is real, unsolved,
nontrivial mathematics (an extremal optimization problem at fixed `eta`
per topology) that was not attempted in this pass rather than rushed.

## 5. Immediate next steps if this track is resumed

1. A genuine attempt at either (a) proving fixed-`eta` sharpness via a
   sharper extremizer construction, or (b) proving a strictly-better
   upper bound than `k`/`k-1` at fixed `eta`, would be the actual
   mathematical content needed to move off `OPEN_WITH_CERTIFIED_GAP`.
2. k=3's per-topology enumeration (left comb / right comb / balanced /
   mixed-arity / repeated vs. heterogeneous laws) as mission Phase 7
   specifies should be checked against `tree_enumeration.py`'s actual
   output to confirm topology coverage is complete, not merely that 1,053
   rows exist.
3. Signed-forest cancellation-aware bounds (mission Phase 8) are a
   separate, not-yet-attempted improvement over these triangle-inequality
   `k`/`k-1` bounds specifically for the associator/Jacobiator/GJI family.
