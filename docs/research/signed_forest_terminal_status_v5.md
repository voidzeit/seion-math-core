# Signed forests and associator constants — terminal status (SEION V5 Phase 8)

Exit-gate record for `PASS_SIGNED_FOREST_THEORY_TERMINAL`. Builds on
existing infrastructure (`src/seion_core/research_v3/polynomial_forests.py`,
already implementing `SignedForest`/exact syntactic cancellation/the five
priority identities named in the mission) and an existing but explicitly
incomplete computation (`artifacts/research_v3/block_G.csv`, produced by
`scripts/tree_constants_v3_pipeline.py::_block_g()`, whose
`gradient_adversarial_constant`/`derivative_free_constant`/
`certified_small_case_constant` columns were all `NaN` with
`optimizer_status="EXTENDED_PENDING_RESOURCE_GATE"` — an honestly-labeled
gap, not a silently dropped one).

## What was actually run this pass

New `scripts/signed_forest_adversarial_search_v5.py`: for each of the 5
priority named forests, 4,000 random-tensor trials (operator norm
numerically normalized to ~1, dimension 2, projector rank 1 — same
natural units as the existing pipeline) plus 200 derivative-free local
refinement steps around the best trial found, filling in the
`derivative_free_constant` the existing pipeline left blank. Real
computation, not a placeholder: verified against a positive control
(non-degenerate nonzero results for 4 of 5 forests) and cross-checked the
one surprising negative-control-shaped result (see "Structural finding"
below) against 5 independent random seeds and both leaf-input regimes
(identical and distinct-random) before reporting it.

**Important methodological correction found while doing this**: the
existing pipeline's `_evaluate_forest_ratio` used *identical* unit leaf
inputs (`np.array([1.0])` at every leaf) — a highly symmetric, non-generic
point that can trivially collapse permutation-antisymmetric terms toward
zero regardless of the law. This script uses independently-drawn random
leaf inputs by default, and separately re-tested the one all-zero result
against identical inputs too, to confirm it was not an artifact of either
input regime specifically (see below).

## Per-forest results

| Forest | Triangle bound | New empirical lower bound | Ratio | Verdict |
|---|---|---|---|---|
| `five_input_ternary_associator` | 2.0 | 1.373 | 0.686 | `IMPROVABLE_WITH_EXACT_CONSTANT_OPEN` |
| `anchored_associator` | 2.0 | 1.658 | 0.829 | `IMPROVABLE_WITH_EXACT_CONSTANT_OPEN` |
| `jacobiator_variants` | 3.0 | 2.983 | 0.994 | `SHARP` |
| `filippov_fundamental_identity` | 4.0 | 1.664 | 0.416 | `OPEN_WITH_CERTIFIED_GAP` |
| `named_gji_variants` (`ternary_declared_gji`) | 6.0 | ~0 (6.7e-16) | ~0 | see "Structural finding" below |

Syntactic-cancellation bound (`combined_terms()`, level 1 of the mission's
three-tier cancellation scheme) equals the triangle bound exactly for all
5 forests — confirmed by direct inspection (`combined_terms()` returns
the same number of terms as the input for every one of them), consistent
with `docs/theorems_v3/signed_forests.md`'s existing honest statement.
None of these identities have accidentally-repeated syntactic subtrees to
cancel; any improvement over the triangle bound has to come from level 2
(shared-subtree DAG) or level 3 (adversarial whole-forest optimization,
what this pass adds) — not from level 1.

## The associator constant "2" (mission's explicit priority)

Both associator-type forests (`five_input_ternary_associator`,
`anchored_associator`) have triangle bound exactly 2.0, matching the
mission's named constant. This pass's adversarial search reaches 69% and
83% of that bound respectively — substantially tighter empirical lower
bounds than the prior single-construction result (the fixed
gated-rotation law used in `block_G.csv` topped out at 25% of the bound
at its best-tested eta), but still strictly below 2 in both cases.

**Terminal verdict: `OPEN_WITH_CERTIFIED_GAP`** for constant 2 — neither
`SHARP` (a gap of 0.34-0.63 remains, well outside numerical noise) nor
`IMPROVABLE_WITH_EXACT_CONSTANT` (no tighter proved upper bound was
derived this pass, only a better empirical lower construction). This is
consistent with, and sharpens, the existing A-N Block H finding for the
same underlying triangle-inequality constant (`PHASE5_TERMINAL_CLASSIFICATION.md`
§H): both the single-tree (Block H) and multi-tree signed (this document)
versions of "coefficient 2" remain unresolved but bounded, in the same
direction (best-observed ratios well below 1, i.e. below the bound,
across every construction tried anywhere in this repository's history).

## Jacobiator: SHARP

`jacobiator_variants` (the 3-term cyclic Jacobiator sum) reaches 99.4% of
its triangle bound of 3 — within plausible numerical-optimizer noise of
exactly matching it. **Terminal verdict: `SHARP`.** This means the plain
triangle inequality is (empirically) not improvable for the Jacobiator
under this projected-error metric — cancellation-aware reasoning does not
help here, a real and useful negative result (tells future work not to
spend effort trying to prove a Jacobiator-specific improvement over the
naive bound).

## Structural finding: `named_gji_variants` appears to be an identity, not a bound

The declared 6-term alternating GJI construction (`ternary_declared_gji`
— 3 even + 3 odd permutations of the ternary-insertion tree, signed
`(+,+,+,-,-,-)`) evaluated to machine-precision zero (ambient, projected,
**and** normal error all in the 1e-16 to 1e-21 range) across every one of
4,000 random-tensor trials plus 5 independently-reseeded spot checks,
under both identical and independently-random leaf inputs. This is not
what "sharp" or "open with gap" mean in this document's vocabulary — a
sharp/gapped bound presumes the quantity being bounded is genuinely
nonzero for some law. This looks instead like a **formal combinatorial
identity**: this particular signed permutation pattern telescopes to
zero for *any* ternary law, not just special ones, the same way Block
N's symmetrized cyclic defect is a `STRUCTURAL_IDENTITY_PASS` rather than
learned evidence.

**This is flagged, not resolved.** Two live possibilities, not
adjudicated here:
1. `ternary_declared_gji`'s specific permutation/sign convention is
   simply not a useful residual to certify a bound for — it was already
   hedged in its own docstring ("no equivalence to another author's
   convention is inferred without a permutation/sign comparison"), and
   this numerical finding is consistent with it having been constructed
   in a way that happens to vanish identically.
2. There is a genuine, previously-unnoticed combinatorial theorem here
   (a full S_3-antisymmetrization of ternary insertions vanishes
   identically) — which would itself be worth stating and proving
   symbolically (small-case `sympy`/exact-rational check, the same
   pattern Block N used to cross-validate its GJI formula at machine
   precision) before any claim of novelty.

**Terminal state for `named_gji_variants`: `NOT_CERTIFIABLE_AS_DEFINED`**
(borrowing the A-N taxonomy's own vocabulary for exactly this situation —
mission section 1's `NOT_CERTIFIABLE_AS_DEFINED`: "the check as currently
specified cannot in principle distinguish a true positive from a false
positive for this claim... a spec problem, not a temporary data
problem"). A sharpness verdict for this specific declared variant cannot
be produced until it is first established whether it measures anything
at all.

## What remains open after this pass

- Level 2 (shared-subtree expression-DAG) cancellation was not attempted
  for any forest — only level 1 (syntactic) and level 3 (adversarial
  search over general laws) were exercised.
- No certified *upper* bound tighter than the plain triangle inequality
  was derived for any forest — every improvement here is on the lower
  (construction) side.
- `named_gji_variants`'s apparent identity was not verified symbolically
  (exact rational/sympy small case); only numerically, across finite
  trials.
- `filippov_fundamental_identity` has the widest remaining gap (58% of
  its triangle bound unaccounted for) and received the same trial budget
  as the others — a dedicated, larger search specifically for this
  identity is the most promising next step if this track is resumed.
