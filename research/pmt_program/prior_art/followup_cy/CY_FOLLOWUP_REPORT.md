# PRIOR-ART-R-CY — follow-up report: tightness of heterogeneous composition constants for $m\ge3$ and $g_{\rm Box}$

```
DATE:     2026-09-14
PROTOCOL: PROTOCOL_CY.md (cy-v1, frozen 18:02; POST_HOC deviations in §9, hashes in FREEZE_CY.json)
GLOBAL:   NOVELTY_NOT_ESTABLISHED
ANSWER:   (i) NO_FOUND   (ii) PARTIAL: YES for full, uncapped discs (Chaffey–Forni–Sepulchre 2023, Thm 5); exact products of phase-capped
          regions only for a membership question with distance maximization left open (Yang–Chen–Qiu 2026 preprint); NO_FOUND for capped arcs + max distance
          (iii) NO_FOUND  ->  overall: no source found that proves m>=3 tightness of a heterogeneous composition constant or implies g_Box
          or placement independence; coverage caveats in §7
```

## 1. Priority question — answer with evidence

**(i) Tightness or sharpness of a heterogeneous composition constant for $m\ge3$: `NO_FOUND`.**

- HRY20 (arXiv v3, §3): Theorem 1 and Corollary 1 cover $N_{\alpha_1}N_{\alpha_2}$ only. §4 proves tightness for Davis–Yin, which involves three
  operators but is not a composition family. The text makes no statement about $m\ge3$ compositions (`L3_CY_huang2020.md`).
- None of the full texts read states tightness of the $m$-fold constant $\varphi$ of CY15 Prop. 2.5 (or its conic extensions):
  Giselsson–Moursi 2021 Thm 4.7, Bartz–Dao–Phan 2022 Thm 2.7, Combettes–Pesquet 2021 eq. (25), Song–Wang 2025 Prop. 3.6.
  Giselsson–Moursi Ex. 4.8 ($m=3$) shows that a hypothesis is needed; it is not an extremizer.
- Sharpness results that exist are for **two** factors: HRY20 Cor. 1; Bauschke–Bendit–Moursi 2023 Cor. 3.3 and Remark 3.4 (exact
  averagedness of $P_VP_U$ via the Friedrichs angle, optimality of Ogura–Yamada); Remark 3.7 there conjectures a further two-factor case.
- *Heuristic, ours, not a literature finding.* In the planar complex-scalar model, $\varphi$ appears to be tight for every $m$.
  Additivity of $\alpha/(1-\alpha)$ is second-order contact at $z=1$, and check (T) of `cy_numeric_check.py` gives a supremum approaching $\varphi$ from
  below for $m=3,4$. So $m\ge3$ tightness is probably elementary via SRG. It was not found stated, and **it would not bear on $g_{\rm Box}$** (§3).

**(ii) Minkowski products of $m\ge3$ SRG disks or arcs, maximizing a distance to a point: `PARTIAL`.**

- **Chaffey–Forni–Sepulchre 2023 (IEEE TAC; arXiv:2107.11272), Theorem 5.** The SRG of a cascade of $n$ output-strict incrementally positive
  systems is the exact product of $n$ discs $\gamma_iD(\tfrac12,\tfrac12)$. Boundary points of each disc are written $\gamma_i\cos\varphi_ie^{-j\varphi_i}$,
  i.e. $w(\varphi_i)$ up to scale and conjugation. The outer boundary is $\prod\gamma_i\cos^n(\theta/n)e^{-j\theta}$, by Jensen (equal angles). The authors
  state that the $n>2$ case is new, and use the region for distance-to-$(-1)$ gain bounds. With $\gamma_i=1$, the largest distance from 1 on this region
  equals $g_{\rm Box}(1,\dots,1)$: $2/\sqrt3$, $9/7$, $1.380901$ for $n=2,3,4$, recomputed here and matching `cy_numeric_check_output.txt`. The paper does not carry out
  that maximization, and it has **no per-factor angle caps**. With caps $\arcsin\eta_u<\pi/2$ that differ, the equal-angle description fails. That
  is exactly what H1/H4 (and the open H3) need.
- Farouki–Pottmann 2002 (N disks, heuristic) and Bünger–Rump 2019 ELA (n-fold products of disks centred at 1; membership, Theorem 1)
  treat disks, not capped arcs, and do not maximize $|1-z|$.
- Lee–Yi–Ryu 2025 (SIOPT) reduce tight DYS factors to a maximum modulus or distance of a three-variable polynomial image of SRG sets
  (Thm 2.1, Cor. 2.2): same technique, different sets and map.
- Guthrie–Mallada 2021 (ACC): outer approximations of Minkowski products of complex sets. **Abstract only** (bot check).
- **Yang–Chen–Qiu 2026 (arXiv:2608.12591, preprint; found only through the POST_HOC Semantic Scholar citation list), Theorem 5.** For every $N$,
  $I+\prod A_i$ is robustly nonsingular over heterogeneous **phase-capped** SRG regions $\mathcal R[\alpha_i,\beta_i,\gamma_i]$ if and only if $-1$ lies
  outside a Minkowski product of those regions. Necessity uses independent per-factor realizations. The regions are cone-over-disc sets, not capped
  arcs of $|z-\tfrac12|=\tfrac12$. The functional is membership of $-1$, and Remark 5 leaves the **maximization of the distance** to $-1$ open.
  Companion: Yang–Zhang–Chen–Qiu 2025 (arXiv:2510.06583), sufficient conditions via annular-sector products (`L3_CY_yang2026.md`).
  This is the closest structural analogue found for heterogeneous angle caps. It neither computes nor implies $g_{\rm Box}$.

**(iii) Anything implying $g_{\rm Box}$ or placement independence: `NO_FOUND`.** No source has per-factor angle caps along
$|z-\tfrac12|=\tfrac12$ with a sharp $\max|1-\prod|$, and none has a tree/placement statement for a sharp constant.

## 2. Coverage counts

| Item | Count |
|---|---|
| Frozen keyword queries | 22 (families CY1–CY4) |
| Keyword requests | OpenAlex 22/22 OK (550 records) · arXiv API 0/22 (4 queries BLOCKED after backoff in 5 requests, 18 DEFERRED by the circuit breaker) · Semantic Scholar search 0/22 (same pattern); supplemental `retry` pass **not run** (probe still HTTP 429 at 19:13) |
| Anchors verified (OpenAlex + Crossref) | 5/5 (CY15, HRY20, RHY22, OY02; Pates 2021 has no Crossref DOI) |
| OpenAlex forward citations (all pages) | CY15 113 (journal 112 + arXiv 1) · HRY20 12 (+0 arXiv record) · RHY22 19 · OY02 77 · Pates21 4 · union 186 |
| Semantic Scholar citations (POST_HOC) | CY15 116 · HRY20 18 · RHY22 64 · OY02 80 · Pates21 32; 67 citing works not in the OpenAlex pool |
| Co-citation $S_1$ (CY15 ∧ HRY20) | OpenAlex 3 · S2 2 · union 3 |
| Co-citation $S_2$ (HRY20 ∧ RHY22) | OpenAlex 6 · S2 11 · union 11 |
| Level 1 | 672 records (605 pool + 67 S2-only); 281 by title+abstract; threat histogram 0: 448 · 1: 209 · 2: 12 · 3: 3 (CY15, Chaffey 2023, Yang–Chen–Qiu 2026) |
| Level 2 | 16 flags; open full text read for 14 (abstract only: Guthrie–Mallada; title only: Bünger–Rump J. Geom.). Additional full-text greps outside the flags: Combettes–Pesquet 2020 (SIMODS), van den Eijnden et al. 2025 "On phase in scaled graphs", Zhang–Zhao–Braun–Chen 2026, Nauta–Pates 2025, Combettes 2024 (Acta Numerica) |
| Level 3 sheets | **12** files (`L3_CY_*.md`) covering 15 sources |
| L3 DOIs checked at Crossref | 10/10 match (`l3_dois_cy.json`); 3 arXiv-only |

## 3. CY15 constant vs $g_{\rm Box}$ (heuristic numerical check)

Script `cy_numeric_check.py`, output `cy_numeric_check_output.txt`. Constant: $\varphi/(1-\varphi)=\sum\alpha_i/(1-\alpha_i)$.

- Every point $w(\theta)$, $\theta\in(0,\pi/2]$, has minimal averagedness exactly $1/2$ (it lies on $\partial D(\tfrac12,\tfrac12)$). Averagedness therefore
  **cannot see the caps**.
- **(A) Containment** ($\alpha_u=1/2$): valid bound $g_{\rm Box}\le2m/(m+1)$. It is cap-blind, and tight only at $m=1$, $\eta=1$. Examples:
  $g_{\rm Box}(1,1,1)=9/7$ vs $1.5$; $g_{\rm Box}(0.05,0.05,0.05)=0.1497$ vs $1.5$.
- **(B) Single-factor matching** ($\alpha_u=\eta_u/2$): $2\varphi(\eta/2)$ is **not** a bound. It is below $g_{\rm Box}$ for 8 of 14 vectors (e.g.
  $(0.3,0.3,0.3)$: $0.692<0.833$), equal for $m=1$, and above for 4 (e.g. $(1,1,1)$: $1.5>1.286$). The two agree only to first order ($\approx\sum\eta_u$).
- **(D)** Even the exact $\max|1-z|$ over $\prod D(1-\alpha_i,\alpha_i)$ is strictly below $2\varphi$ (e.g. $9/7$ vs $3/2$). A sharp averagedness
  constant does not give a sharp distance-from-1 constant.
- **(T)** In the planar scalar model $\varphi$ is approached but not exceeded for $m=3,4$ (tightness heuristic; see §1(i)).

Conclusion (heuristic): CY15 is **unrelated** to $g_{\rm Box}$ except for a cap-blind valid upper bound and first-order agreement for small
defects. It measures second-order contact at $z=1$; $g_{\rm Box}$ is a global maximum distance over capped arcs.

## 4. Level-3 sheets

| Sheet | Source | Access | C1 | C2 | C3 | C4 | C5 | C6 | Threat |
|---|---|---|---|---|---|---|---|---|---|
| `L3_CY_chaffey2023.md` | Chaffey–Forni–Sepulchre, IEEE TAC 2023, Thm 5 | full (arXiv) | YES | PARTIAL (same angle, no caps) | YES (region) | YES (equal angles) | YES (trivial) | only all $\eta_u=1$ | **3** |
| `L3_CY_yang2026.md` | Yang–Chen–Qiu 2026 (arXiv preprint), Thm 5 (+ Yang–Zhang–Chen–Qiu 2025) | full (arXiv) | YES | PARTIAL (phase caps, different region shape) | PARTIAL (iff for membership of −1) | PARTIAL (independent realizations) | YES | NO | **3** (H4 structural analogue; 1 for H1/H2) |
| `L3_CY_combettes2015.md` | Combettes–Yamada, JMAA 2015, Prop. 2.5 | full (arXiv) | NO (SRG reform. YES) | NO | NO | NO | YES | NO | 3 (H1/H2 analogue; 1 for H4) |
| `L3_CY_huang2020.md` | Huang–Ryu–Yin, JMAA 2020 | full (arXiv) | YES | NO | NO ($m=2$) | YES ($m=2$) | YES | NO | 2 |
| `L3_CY_bauschke2023.md` | Bauschke–Bendit–Moursi, NFAO 2023 | full (arXiv) | NO | PARTIAL (Friedrichs angle per pair) | NO ($m=2$) | YES ($m=2$) | YES | NO | 2 |
| `L3_CY_giselsson2021.md` | Giselsson–Moursi, FPTA 2021 | full (arXiv) | PARTIAL | NO | NO | NO | PARTIAL | NO | 2 |
| `L3_CY_lee2025.md` | Lee–Yi–Ryu, SIOPT 2025 | full (arXiv) | PARTIAL | NO | NO | PARTIAL | PARTIAL | NO | 2 |
| `L3_CY_bartz2022.md` | Bartz–Dao–Phan, JOGO 2022 | full (arXiv) | NO | NO | NO | NO | PARTIAL | NO | 2 |
| `L3_CY_combettes2020.md` | Combettes–Pesquet, SIMODS 2020 (outside frozen pool) | full (arXiv) | NO | NO | NO | PARTIAL | NO | NO | 2 |
| `L3_CY_guthrie2021.md` | Guthrie–Mallada, ACC 2021 | **abstract only** | YES | unknown | NO | NO | trivial | NO | 2 (provisional) |
| `L3_CY_bunger2019.md` | Bünger–Rump, ELA 2019 (+ J. Geom. 2019 title only) | full (publisher OA) | YES | NO | NO | NO | PARTIAL | NO | 1 |
| `L3_CY_song2025.md` | Song–Wang, arXiv 2025 (outside frozen pool) | full (arXiv) | NO | NO | NO | NO | NO | NO | 1 |

No source has threat 4–5. **Two sources at threat 3 are new relative to the HET round:** Chaffey–Forni–Sepulchre 2023 (round-1 title screening had
scored it 1) and Yang–Chen–Qiu 2026 (arXiv preprint, not in OpenAlex; found only via the Semantic Scholar citation supplement).

## 5. Proposed status updates (do not apply to `CLAIM_NOVELTY_MATRIX_HET.md` without review)

| Claim | Current (HET) | Proposed | Reason |
|---|---|---|---|
| H1 | `CLOSE_PRIOR_ART` (non-sharp heterogeneous) · `NO_EQUIVALENT_FOUND` (sharp) | **unchanged**. Add Chaffey–Forni–Sepulchre 2023 Thm 5 to the closest prior art for the scalar step (exact uncapped $n$-disc product). | No capped-arc product; no operator-level statement for projected multilinear trees. |
| H4 | `NO_EQUIVALENT_FOUND` (sharpness) · `CLOSE_PRIOR_ART` (components) | **unchanged**. Components list gains Chaffey 2023 (equal-angle boundary of the uncapped product), Yang–Chen–Qiu 2026 Thm 5 (exact every-$N$ criterion over products of heterogeneous phase-capped SRG regions with independent realizations; membership functional; distance maximization open) and Bauschke–Bendit–Moursi 2023 (exact two-projection averagedness via angle). The HET §6 item 6 open question is answered: no $m\ge3$ tightness of CY15 was found, and a tightness proof would not transfer (C2 fails; §3). | |
| H2 | `CLOSE_PRIOR_ART` · `NO_EQUIVALENT_FOUND` (sharp form) | **unchanged** | Only commutativity of Minkowski products and symmetric non-sharp constants (CY15, Bartz–Dao–Phan). Combettes–Pesquet 2020 is order-dependent. |
| H3 | `KNOWN_IN_SPECIAL_CASE` (all $\eta_u=1$; FP02 heuristic, Jensen) | **`KNOWN_IN_SPECIAL_CASE`, with a rigorous peer-reviewed source**: Chaffey–Forni–Sepulchre 2023 Thm 5 (equal angles via Jensen for the uncapped product). Still `NO_EQUIVALENT_FOUND` for caps $<\pi/2$; mathematically OPEN. | |
| Round-1 R7(a) (uniform all-$\pi/2$) | `KNOWN_IN_SPECIAL_CASE` | Add Chaffey 2023 Thm 5 as a rigorous citation for the $n$-fold disc product boundary. | |

## 6. Permitted attribution sentences

> Heterogeneous composition constants for averaged operators that are symmetric in the per-factor parameters are classical
> (Ogura–Yamada 2002; Combettes–Yamada 2015, Prop. 2.5; conic extensions in Giselsson–Moursi 2021, Thm 4.7, and Bartz–Dao–Phan 2022, Thm 2.7).
> Their tightness is known for two factors (Huang–Ryu–Yin 2020, Cor. 1; for two projections, exactly in terms of the Friedrichs angle,
> Bauschke–Bendit–Moursi 2023, Cor. 3.3).

> The Minkowski product of $n$ copies of the disc $D(\tfrac12,\tfrac12)$, the scaled relative graph of a cascade of output-strict incrementally
> positive systems, has the boundary $\cos^n(\theta/n)e^{i\theta}$, obtained from the factorization $\prod_i\cos\varphi_ie^{i\varphi_i}$ by Jensen's
> inequality (Chaffey–Forni–Sepulchre 2023, Thm 5). With all defects equal to 1, our constant is the largest distance from 1 on this region. With
> per-node caps $\theta_u\le\arcsin\eta_u$ the factor sets are proper arcs of $|z-\tfrac12|=\tfrac12$, and we are not aware of a treatment of this capped
> product.

> Exact graphical criteria over Minkowski products of heterogeneous phase-bounded SRG regions have recently been given for robust nonsingularity
> of cyclic interconnections (Yang–Chen–Qiu 2026, Thm 5, preprint arXiv:2608.12591). They concern membership of $-1$, not the worst-case distance.

Constraints: do not write that $m\ge3$ tightness of CY15 is unknown (it was only *not found*); do not claim our heuristic tightness argument as a
result; do not describe Chaffey 2023 as containing $g_{\rm Box}$ (the max-distance computation and caps are absent). Keep *"We are not aware of an
equivalent sharp heterogeneous result; a systematic prior-art review is ongoing."*

## 7. Coverage limitations and manual actions

- arXiv API and Semantic Scholar **search** were rate-limited (HTTP 429) for the whole session. No keyword records come from them, and this is **not**
  zero results. Semantic Scholar **citation** lists did work and added 67 citing works, including the two Yang et al. preprints. arXiv preprints
  that are not indexed by OpenAlex and do not cite an anchor may be missed.
- OpenAlex keyword relevance was very noisy for CY2/CY3 (astronomy, materials, Lorentz–Minkowski geometry). Title-only screening of 391 records
  could miss uninformative titles.
- Level-1 reading, Level-2/3 extraction and the six-criteria answers are agent readings of text extracted from PDFs (`pdftotext`). Formulas were
  checked against the PDFs where extraction was garbled (Yang–Chen–Qiu region formula via arXiv HTML and a numerical check). Published
  numbering is unverified for TAC/SIOPT papers.
- Web searches (POST_HOC) surfaced Song–Wang 2025 and Combettes–Pesquet 2020 outside the frozen pool.

1. **Google Scholar "Cited by"** (all pages; OpenAlex counts are low: RHY22 19, HRY20 12): Huang–Ryu–Yin 2020; Ryu–Hannah–Yin 2022; Combettes–Yamada
   2015; Chaffey–Forni–Sepulchre 2023 (look for capped or sector-restricted cascade SRGs); Yang–Chen–Qiu 2026 and Yang–Zhang–Chen–Qiu 2025 (look for
   a solution of their Remark 5 / eq. (13), the distance maximization over products of phase-capped regions, which would raise the H1/H4 threat);
   Bauschke–Bendit–Moursi 2023 (any $m\ge3$ projection compositions); Giselsson–Moursi 2021. Scholar queries: `"composition of" "averaged operators" tight "m operators"`; `"scaled relative graph" cascade
   "product of"`; `"Minkowski product" "circular arcs"`; `"modulus of averagedness" composition projections`; `"θ-symmetric" "scaled relative graph" cascade`; `"segmental phase" cascade product`.
2. **Paywalled / blocked:** Guthrie–Mallada 2021 (ACC; author PDF behind bot check); Bünger–Rump 2019 J. Geom. "Complex disk products and Cartesian
   ovals"; published numbering of Chaffey–Forni–Sepulchre 2023 (TAC) and Lee–Yi–Ryu 2025 (SIOPT); Dong–Cho–He–Pardalos–Rassias 2021 book chapter
   "Notation and Mathematical Foundations" (cites CY15 and HRY20); Chaffey's PhD thesis (check for angle-restricted cascade SRGs); Ryu–Yin book
   *Large-Scale Convex Optimization* (Cambridge University Press; edition/year not verified), SRG chapter (check for an $m$-fold composition remark).
3. **MathSciNet:** `"averaged" AND composition AND (tight OR sharp OR optimal)` restricted to 2020–2026; citations of MR entries of HRY20 and
   Bauschke–Bendit–Moursi 2023; `"scaled relative graph"` all.
4. Re-run the deferred arXiv / Semantic Scholar keyword requests (`python cy_round.py retry`, the preregistered supplemental pass) when the rate limits clear.
   Then re-run `cy_round.py pool` and `screening_cy_L1_build.py`, and screen the new rows.
