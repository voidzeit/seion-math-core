# M30 — low-rank survives branching; the modes are not explained by tree topology

**EXPLORATORY, NOT CONFIRMATORY.**

Raw: `branching_interaction_raw.json` (400 configs). Analysis:
`branching_interaction_analysis.json`, by
`../experiments/analyze_branching_interaction.py`.

Four topology families, **internal-node count held fixed at 15 and leaf count
at 16**, so the spectra are directly comparable:

| family | ancestor–descendant pairs | different-branch pairs |
|---|---|---|
| chain | 105 (100%) | 0 |
| balanced binary (16 leaves) | 34 | 71 (68%) |
| asymmetric (depth-11 + depth-3 arms) | 72 | 33 |
| random binary | 69 | 36 |

The chain's 0 different-branch pairs is precisely the confound M29 could not
resolve.

## Gate: the low-rank structure survives branching, decisively

| family | regime | ‖I‖/‖U‖ | R1 | R2 | R4 | r_eff | r_eff/m |
|---|---|---|---|---|---|---|---|
| chain | iid | 3.90 | 0.407 | 0.726 | **0.907** | 6.15 | 0.439 |
| balanced | iid | 2.60 | 0.412 | 0.736 | **0.905** | 6.13 | 0.438 |
| asymmetric | iid | 3.23 | 0.419 | 0.745 | **0.899** | 6.21 | 0.443 |
| random | iid | 2.45 | 0.411 | 0.717 | **0.895** | 6.29 | 0.449 |
| chain | het | 1.60 | 0.471 | 0.806 | **0.948** | 4.96 | 0.354 |
| balanced | het | 1.67 | 0.467 | 0.806 | **0.952** | 4.74 | 0.339 |
| asymmetric | het | 1.87 | 0.500 | 0.842 | **0.957** | 4.59 | 0.328 |
| random | het | 2.80 | 0.461 | 0.817 | **0.956** | 4.79 | 0.342 |

Four modes carry 89.5–95.7% of the interaction energy in **every** family, and
the whole spectrum is nearly invariant across topologies — R1 within ±0.05,
R4 within ±0.012 inside each regime. The low rank is **not an artifact of
chains**. This was the gate, and it passes.

It does not yet follow that low rank is a property of the problem in general.
Every configuration here has ambient dimension `D = 6`, and the measured
`r_eff` is 4.6–6.3 — the same order as `D`. The interaction could look
low-rank simply because the whole phenomenon is mediated by a small vector
space. Separating latent interaction rank from ambient dimensionality requires
a `D` sweep and is deferred to M31A; until then this finding is stated as
topology-invariance, not as dimension-independence.

The interaction still dominates the gradient everywhere (‖I‖/‖U‖ = 1.6–3.9),
reproducing M29 on branched trees.

## Driver: neither distance nor shared downstream — both hypotheses refuted

Spearman correlation of `|I_uv|` against each candidate, and partial
correlations controlling for the other (n = 9,100 pairs per family):

| family | ρ(&#124;I&#124;, distance) | ρ(&#124;I&#124;, shared downstream) | partial dist &#124; shared | partial shared &#124; dist |
|---|---|---|---|---|
| chain | −0.067 | +0.019 | −0.065 | −0.013 |
| balanced | +0.007 | +0.066 | +0.078 | +0.101 |
| asymmetric | −0.063 | +0.009 | −0.072 | −0.035 |
| random | −0.047 | +0.061 | −0.018 | +0.044 |

Everything is within ±0.10 of zero, precisely estimated at n=9,100. The
conjecture that **shared downstream geometry would be more explanatory than
topological distance is refuted**: neither explains `|I_uv|`. Mean `|I_uv|` by
relation class tells the same story — ancestor–descendant versus
different-branch differ by a factor of 0.99 in the balanced family and only
1.44–1.48 in asymmetric and random.

So M29's "not local" now holds on genuinely branched trees, and in a stronger
form: the pairwise interaction magnitude is essentially **blind to the tree
geometry tested here** — distance, ancestry relation, and shared downstream.

This is not the claim that the modes are non-geometric. It rules out
*topological* geometry only. The modes may still be geometric in another
sense — in the geometry of the operators, of the residual vectors, of the
projected subspaces, or of the singular directions of the effective slot maps.
Those are untested and are the subject of M31C.

## Mechanism: the cancellation account is NOT demonstrated

This hypothesis was tested and largely failed; it is reported rather than
dropped.

The test defined `c_v` as the root residual when **only** node `v` is
truncated, so that `c_u` for `u ≠ v` is independent of `r_v` and bumping `r_v`
splits the change exactly into `delta_self` and `delta_cross`.

**First failure — the decomposition is not valid.** The linearity residual
`‖Σ_v c_v − E_total‖ / ‖E_total‖` has median **2.523** and p90 **8.463**. The
single-source contributions do not superpose: their sum overshoots the true
error by a factor of ~3.5 on average. Truncation errors compose
multiplicatively through the tree, so a per-source additive picture does not
hold at these rank levels. (This says nothing against the source-resolved
*bounds* of M12 or the M24/M25 certificates, which are inequalities and remain
sound; what fails is the linear approximation `E ≈ Σ_v c_v`.)

**Second failure — the signature does not discriminate enough.**

| group | n | delta_self < 0 | delta_cross > 0 | cross > &#124;self&#124; | both |
|---|---|---|---|---|---|
| negative marginals | 2,461 | 91.7% | 25.9% | 21.8% | **18.0%** |
| positive marginals | 3,139 | 94.1% | 14.4% | 10.1% | 8.0% |

`delta_self < 0` occurs in ~92% of *both* groups, so it does not discriminate
at all. The predicted signature — own contribution improves, cross term
destroys a cancellation and dominates — appears in 18.0% of negative marginals
against an 8.0% base rate. That is a real ~2.2× enrichment in the predicted
direction, but it accounts for under a fifth of the phenomenon. **The
cancellation mechanism is supported as a contributing factor and rejected as
the explanation.**

## Status

- M29's low-rank finding: **confirmed and strengthened** across four topology
  families.
- M29's non-locality: **confirmed on branched trees**, and sharpened to
  position-blindness.
- The shared-downstream conjecture: **refuted**.
- The cancellation mechanism for negative marginals: **not demonstrated**;
  explains ~18% against an 8% baseline, and the additive decomposition it rests
  on is itself invalid here.

What this leaves: the modes are real, stable in dimension across topologies,
and unexplained. Interpreting them — regressing the leading eigenvectors
against node depth, residual magnitude, path amplification, the M24 gain and
the M25 normal/tangential split — is the next measurement, and unlike the
geometric hypotheses tested here it is not yet contradicted by data.

## Scope

Binary trees, 15 internal nodes, ambient dimension 6, synthetic cores,
`uniform` base allocation, Δrank = +1, one base point per budget, 10 seeds per
family×regime. `I` is a finite difference at Δ=1. Mode *stability* across
budgets and seeds (principal angles between the leading subspaces) was not
measured this pass — only the dimension of the spectrum, not the identity of
the modes.
