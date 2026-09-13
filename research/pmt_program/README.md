# PMT sharp-constant program

Branch `research/pmt-sharp-program` (from `codex/pmt-k4-chain-gram@bf366e5`).
Started 2026-09-12. All proofs here are **ADVISORY_PROOF_DRAFT** until an
independent human review; numerical results are `NUMERICAL_OBSERVATION`;
exact certificates are machine-checked at the stated points only.

## Central question

> **Determine `C_T^P(η)` and characterize its dependence on depth, leakage, and topology.**

with `C_T^P(η)` always taken in the frozen class
[`PMT-A`](ADMISSIBLE_CLASS_PMT_A.md) (real, orthogonal projectors, independent
laws, projected-input closure over whole subspaces, projecting root, all
dimensions and ranks). The complex variant `PMT-A[C]` is tracked separately.

## Current answer in one formula

```
C_T^P(η)  =?  C_k(η) := max_{0 ≤ θ ≤ arcsin η} |1 − (cos θ · e^{iθ})^{k−1}| / η          (Conjecture R)
```

| what | status | where |
|---|---|---|
| `C_T^P(η) ≥ C_k(η)` for every tree (explicit witness, fixes the M18/M19 leaf defect) | proof draft | `K4_TOPOLOGY.md` §2 |
| `C_T^P(η) ≤ k − 1`, `lim_{η↓0} C_T^P(η) = k−1` | proved (canonical §9) + witness | Paper I |
| `C_2 = 1`, `C_3 = W_3` for all 3-vertex skeletons | proved (canonical, M14–M16) | Paper I |
| **chains, every `k`: `C_{k,chain} = C_k`** | proof draft (generalizes k=4 audit) | `CHAIN_ALL_K.md` |
| **k = 4, all four skeletons: `C_T^P = C_4`** — topology does not matter at k=4 | proof draft | `K4_TOPOLOGY.md` §3 |
| bilinear root fed by two chains of any lengths | proof draft | `K4_TOPOLOGY.md` §3.2 |
| chain SDP `=` `C_k` exactly at 7 rational points (k=3,4,5) | **certified** (stdlib verifier) | `EXACT_CERTIFICATES.md` |
| `a_k = (k−1)(k−2)(k+6)/24` (chains; all trees if Conjecture R) | proof draft + SDP + exact series | `CHAIN_ALL_K.md` C.1 |
| `a_k = (k−2)(2k−3)/4` | **refuted** at `k=5` (`11/2 ≠ 21/4`) | same |
| chain recursion `z ↦ z·w(θ)` on the Thales arc | proof draft | `RECURSION.md` §1 |
| multiplicative state for all trees | conjecture; proved k ≤ 4 | `RECURSION.md` §2 |
| complex class: BBR/STAR at k=4, field dependence at k=5 | open (retention obstruction proved) | `K4_TOPOLOGY.md` §6 |

Depth: `a_k ~ k³/24`; critical leakage `η_c(k)` decreases
(`0.816, 0.655, 0.543, 0.463, …`); saturated absolute error
`G^max_k = 1, 1.155, 1.286, 1.381, 1.453, … → 2` (limit proved, monotonicity observed only; `η_c(k) ≤ sin(π/(k−1)) → 0` proved).
Leakage: two regimes (budget-limited `η ≤ η_c`, geometry-limited `η ≥ η_c`) at
every depth. Topology: no dependence through `k = 4` in PMT-A.

## Files

| file | content |
|---|---|
| `ADMISSIBLE_CLASS_PMT_A.md` | the single canonical class definition cited by every sharp claim |
| `CHAIN_ALL_K.md` | Theorem C (chains, all k), closed forms, `a_k`, refutation |
| `K4_TOPOLOGY.md` | Theorem U (universal witness), MIXED/BBR/STAR proofs, LP controls, complex caveat, k=5 frontier |
| `EXACT_CERTIFICATES.md` | Gram model validity (Lemma V), dual recursion, reconstruction, results |
| `RECURSION.md` | state recursion, Conjecture R, R′, dual recursion, DAG conjecture |
| `certificates/` | 7 certificate JSONs, `verify_certificates.py` (stdlib), `generate_certificate.py` |
| `experiments/` | scripts + `outputs/` (SDP scan, LP sweeps, constants table, field and k=5 searches) |
| `../../papers/pmt_I_sharp_stability/` | Paper I LaTeX draft |

## Reproduce

```bash
python research/pmt_program/certificates/verify_certificates.py
```

```bash
python research/pmt_program/experiments/chain_constants_table.py
```

The SDP/LP scripts need `numpy scipy sympy cvxpy clarabel` (Python 3.12 was
used; `cvxpy 1.9.2`, Clarabel solver).

## Publication plan

Each paper cites `PMT-A` and carries its own claim budget. Nothing below is
submitted; novelty is not established (see `papers/projected_multilinear_trees/PRIOR_ART_MATRIX.md`,
and the Scaled Relative Graph literature noted in `CHAIN_GRAM_REPORT.md` §10,
which contains the spherical angle mechanism).

### Paper I — *Sharp Stability for Projected Multilinear Trees*

Self-contained; no k ≥ 4 sharp constants beyond the universal witness.

1. PMT-A definitions, scaling, leaf freezing.
2. Stability lemma (subtree norms) → ambient discrepancy `k ρ M^{k−1}L` → projected bound `(k−1)ρM^{k−1}L`; Pythagorean split.
3. `C_1 = 0`; `C_2 = 1` with the saturation characterization and extremizer.
4. Gram lemma; `W_3` for the chain (SOS identity, monotonicity, two regimes); branching via nuclear duality; universality over all 3-vertex trees.
5. Extremizers and equality geometry; `η_c = √(2/3)` vs the envelope point `η_⋆`.
6. Universal witness ⇒ `C_T^P(η) ≥ max_θ |1 − w(θ)^{k−1}|/η` ⇒ `lim_{η↓0} C_T^P = k−1`.
7. Field remarks; open problems pointing to Paper III.

Draft: `papers/pmt_I_sharp_stability/main.tex`.

### Paper II — *Rebracketing and Certified Error Propagation*

`J_2, H_2, S_2` (M40–M42), source/route expansions, DAG path formula and
`K(G)`, Gram-SDP models and exact rational certificates (the machinery of
`EXACT_CERTIFICATES.md` as a general method), DAG extension with Conjecture
R-DAG. Needs its own frozen class (DAG slot multiplicities, shared values).

### Paper III — *Higher-Depth Extremal Theory*

Theorem C for chains of every depth; `a_k`; the Thales-arc recursion; k = 4
topology independence (MIXED, BBR, STAR); certificates as independent checks;
the k = 5 frontier and Conjecture R; the complex class and the retention
obstruction.

## Next work, in priority order

1. Independent review of `CHAIN_ALL_K.md` §2 and `K4_TOPOLOGY.md` §3.3–3.4
   (the two new proofs everything else leans on).
2. k = 5 skeleton `1,2 → 3 → 4 → r`: complete the outer search with the exact
   inner SDP (`experiments/k5_cherry_chain_search.py`, first runs recorded), then
   attempt Conjecture R′.
3. Complex class: optimize the explicit complex BBR family; settle whether
   `a_BBR[C] = 5/2`; compute the first-order gain for `1,2 → 3 → 4 → r` over `ℂ`
   (`experiments/first_order_field.py`).
4. Parametric (in `t`) certificate for the chain dual recursion (Question D).
5. Freeze the DAG class for Paper II and test Conjecture R-DAG on the diamond.
