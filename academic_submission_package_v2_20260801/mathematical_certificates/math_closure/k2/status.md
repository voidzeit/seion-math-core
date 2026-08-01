# M2 status — k=2 classification

**Class A (general, any law/topology/dimension/rank at k=2):**
`OPEN_WITH_CERTIFIED_GAP` (unchanged from
`docs/research/track_t_v5_terminal_status_k2_k3.md` — re-verification,
not new closure). Universal upper bound
$E_T^{\mathrm{proj}} \le \eta M L_T$ proved; certified lower constructions
reach it exactly in 6/75 tested projected-error configurations (atlas),
strictly below it otherwise; no counterexample to the upper bound found
anywhere in 513 rows.

**Class B (homogeneous chain, gated-planar-rotation law): `PROVED`.**
New this pass: $E_T^{\mathrm{proj}}(\eta) = \eta^2$ exactly, for all
$\eta\in[0,1]$, independent of dimension $n\ge2$ and rank
$1\le r\le n-1$ — proved by exact symbolic substitution through the
repository's own evaluator (not a hand-reconstructed one), cross-checked
at 4 distinct $(n,r)$ pairs and against floating-point evaluation at 5
$\eta$ values. Consequently this construction saturates the universal
bound if and only if $\eta=1$, with a linear (not merely asymptotic)
approach for $\eta<1$ — the exact mechanism behind the atlas's 6
previously-unexplained exact-match rows (all at $\eta=1$).

**Not attempted this pass:** independent (non-repeated) laws per node;
complex field; non-coordinate (non-block-diagonal) projectors; any
attempt to prove or disprove that some other law could exceed $\eta^2$
while remaining within the $\eta M L_T$ universal bound — that remains
the open extremal question for class $A$.

## Files

- `admissible_classes.tex` — full parameter declaration for classes A/B.
- `classification_theorem.tex` — both theorems with the closed-form proof.
- `exact_examples/chain_gated_rotation_eta_squared.py` — reproducible,
  self-contained verification script (run directly: `python
  research/math_closure/k2/exact_examples/chain_gated_rotation_eta_squared.py`).
- `certified_enclosures/README.md` — provenance of the class-A enclosure data.
- `computational_registry.parquet` — 513-row k=2 extract of the existing
  verified atlas (no new data generated, no values altered).
