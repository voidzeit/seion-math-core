# Claim novelty matrix — heterogeneous Theorem R (PRIOR-ART-R-HET, mini-round)

```
DATE:    2026-09-14
GLOBAL:  NOVELTY_NOT_ESTABLISHED   (targeted mini-round; arXiv/S2/zbMATH coverage nil; manual steps pending)
INPUTS:  PRIOR_ART_MATRIX_HET.csv (1188 rows = 1178 pooled + 10 adjudicated-only) · screening/het_level1.csv,
         het_level2.csv · theorem_comparisons/L3_HET_*.md (8 files; 14 sources adjudicated at L3) · l3_verdicts_het.json · SEARCH_LOG_HET.csv
RESULT:  no source with threat 4–5; 4 distinct sources at threat 3 (Combettes–Yamada 2015; Grasedyck 2010;
         Bachmayr–Nouy–Schneider 2021; Zniyed–Boyer 2026, abstract only); none states a sharp heterogeneous
         constant or placement independence of a sharp constant for projected multilinear trees or a model containing them
```

Claims follow `SEARCH_PROTOCOL_HET.md` §1. Notation: $w(\theta)=\cos\theta e^{i\theta}$, $\alpha_u=\arcsin\eta_u$.

## 1. Per-claim status

| ID | Claim | Status | Closest prior art (exact locators) | What is known |
|---|---|---|---|---|
| H1 | $E\le\Lambda_T\,G_{\rm box}(\eta)$ | `CLOSE_PRIOR_ART` (non-sharp heterogeneous bounds) · `NO_EQUIVALENT_FOUND` (sharp constant in the PMT model) | Combettes–Yamada 2015, Prop. 2.5 + Remark 2.7 (DOI 10.1016/j.jmaa.2014.11.044) · Grasedyck 2010, Lemma 3.10, Thm 3.11 (DOI 10.1137/090764189; preprint numbering) · Bachmayr–Nouy–Schneider 2021, Lemma 4.9, Prop. 4.7 (arXiv:2112.01474, NO_DOI) · also Oseledets 2011 (TT-SVD, numbering unverified); Hackbusch 2012, Thm 11.58; Verstraete–Cirac 2006, Lemma 1; BBBV 1997, Thm 3.3; Zhou–Stoudenmire–Waintal 2020, Eq. (17) | Node-wise heterogeneous budgets are standard in several forms. They can be root-sum-square and order-free (HT/TT), additive and level-weighted (tree compositions), additive per step (hybrid argument, MPS), or heuristically multiplicative in fidelity (circuit MPS). Heterogeneous symmetric composition constants that beat the worst-parameter constant exist for averaged operators. None is shown to be sharp for three or more factors in the sources read, and none involves projections after bounded multilinear maps or the phase-retaining functional $\lvert1-\prod w(\theta_u)\rvert$. |
| H4 | $\sup E/\Lambda_T=G_{\rm box}(\eta)$, planar witness with independent angles | `NO_EQUIVALENT_FOUND` (sharpness) · `CLOSE_PRIOR_ART` (components) | Huang–Ryu–Yin 2020, Thm 1 + Cor. 1 (DOI 10.1016/j.jmaa.2020.124211): sharp **two-factor** heterogeneous constant, different functional · Oikhberg 1999, Lemma 2(a) (DOI 10.1090/S0002-9939-99-05255-7): planar chain of line projections with arbitrary angles, acting as $\prod w(\theta_j)$, used only as a construction · Farouki–Pottmann 2002, Prop. 4.1 (DOI 10.1023/A:1014737602641): N disks with different radii, heuristic | Sharp heterogeneous constants are known for two-factor compositions (averagedness), and the independent-angle planar chain is a known construction. Extremality of that chain for a heterogeneous error functional with angle caps was not found. Disk-radius heterogeneity does not map to angle caps (L3_HET_huang2020). |
| H2 | Sharp constant depends only on the multiset of non-root defects | `CLOSE_PRIOR_ART` (non-sharp / uniform) · `NO_EQUIVALENT_FOUND` (sharp form) | Grasedyck 2010, Lemma 3.10 ("any order", multiset-only root-sum-square bound) · Combettes–Yamada 2015, Prop. 2.5 ($\varphi$ symmetric in the $\alpha_i$, chains only, sharp only for m = 2) · Ceruti–Lubich–Sulz 2023, Thm A.1 (DOI 10.1137/22M1473790; uniform tolerance, depends on vertex count only) · contrast: Bachmayr–Nouy–Schneider 2021 Lemma 4.9 (level-dependent); Zniyed–Boyer 2026 (tree-dependent factors, abstract only) | Order- and placement-free heterogeneous bounds are common, but they are non-sharp or cover chains only. Some tree bounds are explicitly placement-dependent. Placement/topology/arity independence of a **sharp** heterogeneous constant was not found. |
| H3 (OPEN) | $G_{\rm box}(\eta)=\max_\tau\lvert1-\prod_uw(\min(\alpha_u,\tau))\rvert$ | `KNOWN_IN_SPECIAL_CASE` (all $\eta_u=1$) · `NO_EQUIVALENT_FOUND` otherwise · **mathematically OPEN** | Farouki–Pottmann 2002 §5 (all caps π/2, heuristic; also Jensen, round-1 R7(a)) · He–Zhao–Zhou–Niu 2013 (DOI 10.1109/TWC.2013.061713.130278; capped water-filling, abstract only) · Palomar–Fonollosa 2005, Prop. 1 (DOI 10.1109/TSP.2004.840816; background) | Capped water-filling gives $\min(\alpha_u,\tau)$ as the *maximum-modulus* allocation at fixed total angle. This is a known ingredient, and it is not sufficient, because the minimum-modulus branch and the phase must also be controlled (L3_HET_waterfilling). No source states H3. |
| H-dev | Lifted angle subadditive along multilinear contractions; π/Θ scaling | `KNOWN_IN_SPECIAL_CASE` (technique) | Round-1 R6 (Tomamichel–Colbeck–Renner 2010) · Dohotaru–Høyer 2009, Lemma 4 (heterogeneous per-step angles, DOI 10.26421/QIC9.5-6-12) · Ryu–Hannah–Yin 2022, Thm 7 (DOI 10.1007/s10107-021-01639-w) | Heterogeneous angle addition is known for unit vectors and unitary steps, and for SRGs. The π/Θ uniform scaling was not found. |

## 2. Sources at threat 3 (none implies an H claim)

| Source | Level | Why 3 | Open action |
|---|---|---|---|
| Combettes–Yamada 2015 | L3, full text (arXiv) | Heterogeneous, symmetric composition constant; improves the worst-parameter constant; tight for m = 2 | Check (Scholar forward citations of HRY20) whether tightness for m ≥ 3 is known |
| Grasedyck 2010 | L3, full text (preprint) | Heterogeneous node-wise, order-free root-sum-square bound on trees | Verify published numbering |
| Bachmayr–Nouy–Schneider 2021 | L3, full text (arXiv v1) | Additive node-wise tree accumulation | Find journal version / DOI |
| Zniyed–Boyer 2026 | L3, **abstract only** | Error transport of local truncations through trees | **Manual PDF download**; re-score |

Threat histogram (`PRIOR_ART_MATRIX_HET.csv`, rows): 0: 720 · 1: 429 · 2: 33 · 3: 6 (4 distinct; 2 duplicate records) · 4–5: 0.

## 3. Permitted attribution sentences

> Heterogeneous, node-wise error budgets for truncations along trees are classical: root-sum-square and order-independent for
> hierarchical and tensor-train formats (Grasedyck 2010, Lemma 3.10 and Thm 3.11; Oseledets 2011; Hackbusch 2012, Thm 11.58),
> additive with level-dependent weights for trees of compositions (Bachmayr–Nouy–Schneider 2021, Lemma 4.9), additive per step in
> quantum simulation and query complexity (Verstraete–Cirac 2006, Lemma 1; Bennett et al. 1997, Thm 3.3; Dohotaru–Høyer 2009, Lemma 4),
> and heuristically multiplicative in fidelity (Zhou–Stoudenmire–Waintal 2020, Eq. (17)). Heterogeneous composition constants that
> depend symmetrically on per-factor parameters are known for averaged operators (Ogura–Yamada 2002; Combettes–Yamada 2015, Prop. 2.5),
> with tightness for two factors (Huang–Ryu–Yin 2020, Cor. 1). What the present argument adds is the sharp constant
> $G_{\rm box}(\eta)$ for projected multilinear trees with node-wise defects, its attainment by a planar witness with independent
> angles, and its independence of the tree placement of the defects.

> The planar chain of projections onto lines at successive, independent angles, acting as $\prod_j\cos\theta_je^{i\theta_j}$, is a
> classical construction (Oikhberg 1999, Lemma 2(a)); we use it as the extremal witness.

Constraints: do not write "only uniform bounds were known" (Combettes–Yamada, Grasedyck and Bachmayr–Nouy–Schneider contradict it). Do
not cite water-filling as support for H3, and do not state H3 as a result. Keep the internal wording *"We are not aware of an equivalent
sharp heterogeneous result; a systematic prior-art review is ongoing."* until the manual steps are done.

## 4. Search coverage and limitations

- **Queries:** 30 (O1–O6, 5 each). OpenAlex 30/30 OK (702 harvest records incl. 10 from S2; 639 unique). zbMATH 30/30 answered with 0 results (HTTP 404).
  arXiv API blocked (429, then 503 in the retry pass). Semantic Scholar 1/30 OK.
- **Snowball:** 7 verified anchors, one hop, 596 records (566 unique, 539 new vs harvest).
- **Pool:** 1178 unique (193 seen in round 1). **L1:** 1178 (84 by abstract, 1094 by title). **L2:** 15 pool rows (3 duplicate records) plus adjudicated
  records. **L3:** 8 files; 14 sources adjudicated at L3 (19 discussed).
- The OpenAlex relevance search returned much off-topic material for families O2, O5 and O6. Title-only screening can miss uninformative titles.
  Missing arXiv, zbMATH and Semantic Scholar coverage is the main gap.

## 5. Stop criterion (protocol §8)

| # | Criterion | Status |
|---|---|---|
| 1 | All 30 queries on OpenAlex + zbMATH; arXiv/S2 retry logged | Met (coverage of zbMATH/arXiv/S2 nil; logged) |
| 2 | One snowball hop from 4–8 verified anchors | Met (7) |
| 3 | L1 of all pooled rows | Met |
| 4 | Every threat ≥3 at L3 | Met (Zniyed–Boyer abstract only) |
| 5 | Every claim has a status | Met (§1) |

## 6. Manual actions for the author

1. **Zniyed–Boyer 2026:** download hal-05554951 in a browser (bot check). Re-score H1/H2. Add the HAL id to `references_het.bib` (the generated entry has an empty note).
2. **MathSciNet** (log in `SEARCH_LOG_HET.csv`): `Anywhere: "averaged" AND composition AND (tight OR sharp)` · `Anywhere: "Minkowski product" AND (arc OR disk)` · `Anywhere: "hierarchical Tucker" AND tolerance` · `Anywhere: "product of projections" AND angles` · MSC 47H09, 47A30, 15A69, 65F55, 15A60 combined with `heterogeneous OR nonuniform`.
3. **Google Scholar:** forward citations of Huang–Ryu–Yin 2020, Combettes–Yamada 2015, Oikhberg 1999, Farouki–Pottmann 2002 and Grasedyck 2010 (first 3 pages each). Queries: "tight averagedness" composition "m operators"; "Minkowski product" "circular arcs"; "error budget" "tree tensor network"; "product of cosines" "phase" worst case.
4. Re-run the arXiv and Semantic Scholar parts (`python het_round.py retry`) when the rate limits clear. Run zbMATH with short (1–3 word) queries by hand.
5. Paywalled or unverified: Oseledets 2011 (theorem numbers), Hackbusch 2012 Thm 11.58 (book), Bünger–Rump 2019 (J. Geom.; read before submission), published numbering of Grasedyck 2010, and the journal version of Bachmayr–Nouy–Schneider.
6. Open question found during screening: is the Combettes–Yamada heterogeneous constant tight for m ≥ 3? If it is, and the tightness construction uses planar independent angles, re-assess H4 (possible threat increase).
