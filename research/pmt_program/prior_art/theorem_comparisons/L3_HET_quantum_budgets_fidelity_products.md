# L3-HET comparison: per-step error budgets in quantum simulation and hybrid arguments (Zhou–Stoudenmire–Waintal 2020; Verstraete–Cirac 2006; BBBV 1997 / Dohotaru–Høyer 2009)

Prepared 2026-09-14 (PRIOR-ART-R-HET). This is a Level-3 comparison of one cluster (families O3 and O6) against H1, H2, H4 and the proof device.
Everything is paraphrased.

## 1. Bibliographic records

| Key | Record | Status |
|---|---|---|
| ZSW20 | Y. Zhou, E. M. Stoudenmire, X. Waintal, "What limits the simulation of quantum computers?", Phys. Rev. X 10 (2020) 041038. DOI 10.1103/PhysRevX.10.041038. arXiv:2002.07730 | VERIFIED (OpenAlex W3006255022 + Crossref; used as snowball anchor) |
| VC06 | F. Verstraete, J. I. Cirac, "Matrix product states represent ground states faithfully", Phys. Rev. B 73 (2006) 094423. DOI 10.1103/PhysRevB.73.094423. arXiv:cond-mat/0505140 | Round-1 anchor. The arXiv text was read in this round. |
| BBBV97 | C. H. Bennett, E. Bernstein, G. Brassard, U. Vazirani, SIAM J. Comput. 26(5) (1997). DOI 10.1137/S0097539796300933 | Round 1 VERIFIED. The arXiv text quant-ph/9701001 was re-read (Thm 3.3). |
| DH09 | C. Dohotaru, P. Høyer, Quantum Inf. Comput. 9 (2009). DOI 10.26421/QIC9.5-6-12 | Round 1 L3 (Lemmas 2 and 4). |
| AYR23 | T. Ayral et al., PRX Quantum 4 (2023) 020304. DOI 10.1103/PRXQuantum.4.020304 | VERIFIED (anchor). Abstract only. |

## 2. Access level

ZSW20: FULL_TEXT §IV.A. VC06: FULL_TEXT (Lemma 1). BBBV97: FULL_TEXT §3.1. DH09: round-1 FULL_TEXT. AYR23: ABSTRACT_ONLY.

## 3. Relevant results (paraphrased)

- **ZSW20 §IV.A, Eqs. (16)–(18).** The N-qubit fidelity after n truncated gates is approximated by the *product* of the per-gate
  truncation fidelities, $F(n)\approx\prod_i f_i$. It is supported by an analytical argument and numerics, not stated as a bound. In the stationary
  regime $F\approx f_\infty^n$.
- **VC06 Lemma 1.** There is an MPS of bond dimension D with $\lVert\psi-\psi_D\rVert^2\le2\sum_\alpha\epsilon_\alpha(D)$. Here $\epsilon_\alpha(D)$ is the discarded weight at
  bond α. This is heterogeneous per bond, additive in the squared error, and not sharp.
- **BBBV97 Thm 3.3.** If the total query magnitude on a set of (time, string) pairs is at most $\varepsilon^2/T$, changing the oracle there moves the
  final state by at most ε. The proof telescopes heterogeneous per-step errors (triangle inequality plus unitary invariance) and applies Cauchy–Schwarz.
- **DH09 Lemma 4 (round 1).** This is the angle version of the hybrid argument. Per-step angles $\theta_i=\arcsin\lVert\Pi_y\Psi_i\rVert$ are heterogeneous, and the
  final angle is at most their sum. **Lemma 2** maximizes $\sum\theta_i$ under $\theta_i\in[0,\pi/2]$ and a quadratic budget.

## 4. Comparison table

| Claim | Implied? | Explanation |
|---|---|---|
| H1 | NO (CLOSE_PRIOR_ART in form, non-sharp or heuristic) | Per-step heterogeneous budgets are standard: additive in norm (BBBV97, VC06), additive in angle (DH09), and multiplicative in fidelity (ZSW20, heuristic). None gives the worst-case constant for complex-phase accumulation $\lvert1-\prod\cos\theta_ue^{i\theta_u}\rvert$. None concerns projections after bounded multilinear maps. |
| H2 | NO (ANALOGUE) | Sums and products of per-step quantities are order-independent, so the budgets depend only on the multiset. This is non-sharp or approximate. |
| H4 | NO | No extremal constructions for the budgets. |
| H3 | NO | DH09 Lemma 2 is an equal-angle extremality under a *different* (quadratic) budget. It is related in spirit only. |
| Proof device (lifted angle, subadditivity with heterogeneous per-node angle bounds) | KNOWN_IN_SPECIAL_CASE (technique) | DH09 Lemma 4 adds heterogeneous per-step angles bounded by arcsin of a local leakage. This is the unit-vector, unitary-step analogue of heterogeneous angle subadditivity. The sub-normalized lift is the round-1 R6 attribution (Tomamichel–Colbeck–Renner). The uniform π/Θ scaling is not found. |

## 5. Threat score

**2 / 5** for the cluster. This includes DH09 at the technique level.

## 6. How to cite

> Heterogeneous per-step error budgets are standard in quantum simulation and query complexity: additive in norm (Bennett et al. 1997,
> Thm 3.3; Verstraete–Cirac 2006, Lemma 1), additive in angle (Dohotaru–Høyer 2009, Lemma 4) and, heuristically, multiplicative in
> fidelity (Zhou–Stoudenmire–Waintal 2020, Eq. (17)). The present heterogeneous constant is a sharp worst-case form that keeps the
> phase, $\lvert1-\prod_u\cos\theta_ue^{i\theta_u}\rvert$, for projected multilinear trees.
