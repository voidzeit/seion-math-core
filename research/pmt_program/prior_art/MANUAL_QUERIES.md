# Manual search steps (MathSciNet, Google Scholar)

These two sources cannot be queried automatically: MathSciNet needs a subscription, and Google
Scholar forbids automated access. The author runs them and appends **one row per query** to
`SEARCH_LOG.csv`:

- `database` = `mathscinet` or `google_scholar`
- `status` = `MANUAL_OK`
- `results_total`: the count shown by the site
- `records_saved`: how many were copied into `PRIOR_ART_MATRIX.csv`

Candidates found this way go into `PRIOR_ART_MATRIX.csv` with `sources=mathscinet` or
`sources=google_scholar` and are screened under §5 of the protocol.

## 1. MathSciNet — text queries

Use **Anywhere** unless noted. Cover every family A–N from `queries.json`. Recommended field
translations:

| Family | MathSciNet query |
|---|---|
| A | `Anywhere: "hierarchical Tucker" AND (truncation OR "error bound")` · `Anywhere: "tree tensor network"` · `Anywhere: "dimension tree" AND approximation` |
| B | `Anywhere: multilinear AND "error propagation"` · `Anywhere: "composition" AND "multilinear maps" AND perturbation` |
| C | `Anywhere: "product of projections" AND norm` · `Anywhere: "Friedrichs angle"` · `Review text: "principal angles" AND sharp` |
| D | `Anywhere: multilinear AND "best constant" AND "Hilbert space"` · `Anywhere: "projective tensor norm" AND angle` |
| E | `Anywhere: fidelity AND subnormalized` · `Anywhere: "purified distance"` · `Anywhere: "Bures" AND monotonicity` |
| F | `Anywhere: ("tree structure" OR "dimension tree") AND independent AND bound` |
| G | `Anywhere: extremal AND "two-dimensional" AND "Hilbert space" AND inequality` |
| H | `Anywhere: Lean AND formalization AND (inequality OR "functional analysis")` |
| I | `Anywhere: "alternating projections" AND ("rate of convergence" OR sharp)` · `Author: Kayalar` · `Author: Deutsch, F* AND Title: projections` |
| J | `Anywhere: "Zeno effect" AND projections` |
| K | `Anywhere: "gentle measurement"` |
| L | `Anywhere: "numerical range" AND products AND contractions` |
| M | `Anywhere: "matrix product states" AND truncation AND error` |
| N | *(low MathSciNet yield expected; run once and log)* `Anywhere: "neural network" AND pruning AND "error bound"` |

## 2. MathSciNet — MSC searches

MSC codes are taken **from the anchors** (zbMATH records carry them). After the first screening pass,
the recurring primary MSC codes are listed in `CLAIM_NOVELTY_MATRIX.md` §MSC.

For each such code, run `Primary MSC = <code>` combined with `Anywhere: projection AND
(multilinear OR tensor)`, restricted to 1980–present. Log every combination.

## 3. MathSciNet — anchor citation chasing

For every anchor in `anchors.json`: open its MR record → "Citations" (from references / from reviews)
→ screen the citing items and log each as `query = "cited-by MR<number>"`.

## 4. Google Scholar

1. Run every query string of `queries.json` verbatim. Screen the first 3 result pages (30 items).
2. For every anchor: "Cited by" → sort by relevance → screen the first 3 pages.
3. Record the date, because Scholar counts drift.

## 5. Dates

Re-run §1 and §4 for families A, B, C, I and J within two weeks before submission, then again
before the journal version (protocol §8, item 7).
