"""PRIOR-ART-R-CY Level-1 recorder (PROTOCOL_CY.md 3.5).

Judgments were made by reading titles (and abstracts where the protocol requires) of pool_cy.csv. They are recorded here
as explicit overrides matched by normalized title. Every other row gets a threat from a published keyword rule that
encodes the screener's title reading: 1 for operator-theory / SRG / Minkowski-product / projection-algorithm topics,
0 otherwise. `read_level` states whether the row was in the title+abstract reading set (co-citation S1/S2, forward
citations of HRY20 or PAT21, cy_score >= 2, or top-10 of a keyword request) or title-only.

Output: screening_cy_L1.csv (key, title, year, origins, cy_score, read_level, threat, flag_L2, l3_file, reason)
"""
from __future__ import annotations

import csv
import re
from pathlib import Path

import cy_round as C

HERE = Path(__file__).resolve().parent

# (title substring, normalized) -> (threat, flag_L2, l3_file, reason)
OVERRIDES = {
    "Graphical Nonlinear System Analysis": (3, True, "L3_CY_chaffey2023.md", "Thm 5: exact SRG of a cascade of n discs gamma_i D(1/2,1/2); boundary cos^n(theta/n)e^{-i theta} via Jensen; no caps"),
    "How Averaged is the Composition of Two Linear Projections?": (2, True, "L3_CY_bauschke2023.md", "exact averagedness modulus of P_V P_U via Friedrichs angle; OY bound optimal; m=2"),
    "On compositions of special cases of Lipschitz continuous operators": (2, True, "L3_CY_giselsson2021.md", "Thm 4.7 m-fold conic composition constant (CY form); tightness only m=2 examples"),
    "Convergence Analyses of Davis–Yin Splitting via Scaled Relative Graphs": (2, True, "L3_CY_lee2025.md", "max modulus of DYS polynomial over SRG sets; three operators, not a composition family"),
    "Convergence analyses of Davis–Yin splitting via scaled relative graphs II: convex optimization problems": (1, False, "", "same machinery as Lee-Yi-Ryu; contraction factors for convex problems (abstract)"),
    "Tight coefficients of averaged operators via scaled relative graph": (2, True, "L3_CY_huang2020.md", "anchor; m=2 tightness; no m>=3 statement"),
    "Tight Coefficients of Averaged Operators via Scaled Relative Graph": (2, True, "L3_CY_huang2020.md", "arXiv record of HRY20"),
    "Compositions and convex combinations of averaged nonexpansive operators": (3, True, "L3_CY_combettes2015.md", "anchor; Prop 2.5 heterogeneous m-fold constant"),
    "Compositions and Convex Combinations of Averaged Nonexpansive Operators": (3, True, "L3_CY_combettes2015.md", "arXiv record of CY15"),
    "Conical averagedness and convergence analysis of fixed point algorithms": (2, True, "L3_CY_bartz2022.md", "Thm 2.7 m-fold conic composition constant; no tightness"),
    "Outer Approximations of Minkowski Operations on Complex Sets via Sum-of-Squares Optimization": (2, True, "L3_CY_guthrie2021.md", "Minkowski products of complex sets, outer approximations (abstract only; PDF behind bot check)"),
    "The determinant of a complex matrix and Gershgorin circles": (1, True, "L3_CY_bunger2019.md", "n-fold products of disks centred at 1; membership"),
    "Complex Disk Products and Cartesian Ovals": (2, True, "L3_CY_bunger2019.md", "title only; paywalled; two-disk exact products (presumed)"),
    "Exact Minkowski Products of N Complex Disks": (2, False, "", "round-1/HET L3 exists (L3_farouki2002, L3_HET_huang2020); heuristic N-disk boundary"),
    "Scaled relative graphs: nonexpansive operators via 2D Euclidean geometry": (2, False, "", "anchor; round-1 L3_ryu2022 (Thm 7 product; two-factor tightness)"),
    "Scaled relative graphs for system analysis": (1, True, "", "L2 full text arXiv:2103.13971v2: SRG/Nyquist link, incremental passivity via SRG; no n-fold cascade products or composition constants (those appear later in Chaffey-Forni-Sepulchre 2023 Thm 5)"),
    "Scaled Relative Graph of Normal Matrices": (1, False, "", "single normal matrix SRG; full text grep: no compositions"),
    "Fixed Point Strategies in Data Science": (1, True, "", "survey; full text grep: recalls CY15/HRY20 two-operator constant (eq. (26)); no m>=3 tightness"),
    "Notation and Mathematical Foundations": (1, False, "", "book chapter (Dong et al.); background; paywalled"),
    "A rolled-off passivity theorem": (1, False, "", "feedback of two systems; SRG"),
    "Circuit Model Reduction with Scaled Relative Graphs": (1, False, "", "series/parallel chains; SRG approximation error; no composition constants"),
    "Scaled graphs for reset control system analysis": (1, False, "", "SRG approximation for reset controllers"),
    "Monotone One-Port Circuits": (1, False, "", "circuits; monotone operators"),
    "The Singular Angle of Nonlinear Systems": (2, False, "", "angle notion for systems; small angle theorem (angles add in loops); H-dev technique only"),
    "Mixed Small Gain and Phase Theorem: A new view using Scale Relative Graphs": (1, False, "", "phase/SRG feedback stability; two systems"),
    "Scaled Relative Graph Analysis of Lur’e Systems and the Generalized Circle Criterion": (1, False, "", "SRG + Nyquist; Lur'e"),
    "Decomposition of Scaled Relative Graphs: A Mixed Systems Approach": (1, False, "", "input-specific SRGs"),
    "Scaled relative graphs for pairs of operators beyond classical monotonicity": (1, False, "", "SRG for pairs of operators; no abstract; title"),
    "Scaled relative graphs for nonmonotone operators with applications in circuit theory": (1, False, "", "nonmonotone SRG; no abstract; title"),
    "Nonlinear Bandwidth and Bode Diagrams based on Scaled Relative Graphs": (1, False, "", "SRG gain bounds"),
    "Stability Analysis of Power-Electronics-Dominated Grids Using Scaled Relative Graphs": (0, False, "", "application"),
    "A Homotopy Theorem for Incremental Stability": (0, False, "", "incremental stability"),
    "Convergence of the preconditioned proximal point method and Douglas–Rachford splitting in the absence of monotonicity": (1, False, "", "DRS nonmonotone; SRG-type"),
    "Short Communication: FISTA Iterates Converge Linearly for Denoiser-Driven Regularization": (0, False, "", "application"),
    "On the optimal relaxation parameters of Krasnosel'ski–Mann iteration": (1, False, "", "KM relaxation; single operator"),
    "Tight Global Linear Convergence Rate Bounds for Operator Splitting Methods": (1, False, "", "tight rates for splitting (two-operator)"),
    "Tight global linear convergence rate bounds for Douglas–Rachford splitting": (1, False, "", "two-operator DRS"),
    "Operator Splitting Performance Estimation: Tight Contraction Factors and Optimal Parameter Selection": (1, False, "", "PEP tight factors for DRS (two operators)"),
    "Deep Neural Network Structures Solving Variational Inequalities": (1, True, "", "L2 full text (author PDF svva5): averagedness conditions for layered composites; no tightness/sharpness statement"),
    "On the Minimal Displacement Vector of Compositions and Convex Combinations of Nonexpansive Mappings": (1, False, "", "displacement vectors, not constants"),
    "Strict pseudocontractions and demicontractions, their properties, and applications": (1, False, "", "composition of strict pseudocontractions: parameter conditions; abstract"),
    "On $\\alpha$-Firmly Nonexpansive Operators in $r$-Uniformly Convex Spaces": (1, False, "", "compositions in Banach spaces; not sharp"),
    "On $$\\alpha $$-Firmly Nonexpansive Operators in r-Uniformly Convex Spaces": (1, False, "", "duplicate record"),
    "$α$-Firmly Nonexpansive Operators on Metric Spaces": (1, False, "", "metric-space generalization"),
    "Generalized monotone operators and their averaged resolvents": (1, False, "", "conic nonexpansiveness; resolvents"),
    "Linear and strong convergence of algorithms involving averaged\\n nonexpansive operators": (1, False, "", "regularity; cyclic iterations"),
    "Generalized Composed Alternating Relaxed Projection Algorithm for Two-Set Feasibility Problem": (1, False, "", "two-set; principal angles; spectral characterization"),
    "Exact Optimal Accelerated Complexity for Fixed-Point Iterations": (1, False, "", "complexity lower bounds; single operator"),
    "A Cascade of Systems and the Product of Their θ-Symmetric Scaled Relative Graphs": (2, True, "L3_CY_yang2026.md", "N-fold products of theta-symmetric SRGs; sufficient nonsingularity criteria; annular-sector products (phases add, gains multiply)"),
    "The $\\theta$-Symmetric SRG with Applications to Stability of Cactus Dynamic Networks": (3, True, "L3_CY_yang2026.md", "Thm 5: iff robust nonsingularity over N-fold products of heterogeneous phase-capped regions R[alpha_i,beta_i,gamma_i]; distance maximization open (Remark 5)"),
    "Symmetry Is Almost All You Need: Robust Stability with Uncertainty Induced by Symmetric SRG Regions": (2, False, "", "L2 grep: necessary+sufficient matrix robust nonsingularity for symmetric SRG regions (feedback of two components); angle-bounded systems; no N-fold sharp constant"),
    "On phase in scaled graphs": (1, False, "", "signed scaled graph; phase lead/lag; interconnection results (abstract + grep)"),
    "Computable Characterisations of Scaled Relative Graphs of Closed Operators": (1, False, "", "L2 grep: SRG of single closed linear operators"),
    "How averaged is the projection?": (1, False, "", "withdrawn arXiv:2312.15421 (Song); superseded by Song-Wang 2025"),
    "Loop Shaping with Scaled Relative Graphs": (1, False, "", "control design with SRGs"),
    "Scaled Relative Graph Analysis of General Interconnections of SISO Nonlinear Systems": (1, False, "", "interconnection SRG bounds (title)"),
    "A Dissipativity Framework for Constructing Scaled Graphs": (1, False, "", "constructing SGs (title)"),
    "The Phantom of Davis-Wielandt Shell: A Unified Framework for Graphical Stability Analysis of MIMO LTI Systems": (1, False, "", "DW shell; graphical stability (title)"),
    "Scaled Relative Graphs in Normed Spaces": (1, False, "", "SRG generalization (title)"),
    "Soft and Hard Scaled Relative Graphs for Nonlinear Feedback Stability": (1, False, "", "feedback stability (title)"),
    "Lipschitz Certificates for Layered Network Structures Driven by Averaged Activation Operators": (2, True, "L3_CY_combettes2020.md", "m-layer heterogeneous Lipschitz constant; exact only in degenerate cases"),
    "On Bauschke-Bendit-Moursi modulus of averagedness and classifications of averaged nonexpansive operators": (1, True, "L3_CY_song2025.md", "m-fold: only lower bound 1/2"),
    "Line Search For Generalized Alternating Projections": (1, False, "", "GAP line search"),
    "Line search for generalized alternating projections": (1, False, "", "duplicate"),
    "Convergence properties of dynamic string-averaging projection methods in the presence of perturbations": (1, False, "", "products of infinitely many operators; rates"),
    "On a notion of averaged operators in CAT(0) spaces": (1, False, "", "CAT(0)"),
    "On a Notion of Averaged Mappings in $$\\operatorname{CAT}(0)$$ Spaces": (1, False, "", "CAT(0)"),
}
RULE1 = re.compile(r"averag|nonexpansive|firmly|monoton|splitting|fixed.point|scaled relative|minkowski product|complex dis[ck]|"
                   r"cartesian oval|projection (method|algorithm)|alternating projection|cyclic projection|proximal|"
                   r"krasnosel|douglas|resolvent|feasibility", re.I)


def main() -> None:
    pool = list(csv.DictReader((HERE / "pool_cy.csv").open(encoding="utf-8")))
    cocite = {r["openalex"] for r in csv.DictReader((HERE / "cocitation_cy.csv").open(encoding="utf-8"))
              if r["set"].startswith("S")}
    ov = {C.norm(k): v for k, v in OVERRIDES.items()}
    used = set()
    out = []
    for r in pool:
        nt = C.norm(r["title"])
        in_read = (r["openalex"] in cocite or "fwd:HRY20" in r["origins"] or "fwd:PAT21" in r["origins"]
                   or int(r["cy_score"]) >= 2 or r["top10"] == "True")
        if nt in ov:
            t, f, l3, reason = ov[nt]
            used.add(nt)
            src = "override"
        else:
            t = 1 if RULE1.search(r["title"]) else 0
            f, l3, reason, src = False, "", "keyword rule on title (broad field)" if t else "keyword rule on title (off-topic)", "rule"
        out.append({"key": r["key"], "title": r["title"], "year": r["year"], "origins": r["origins"],
                    "cy_score": r["cy_score"], "read_level": "title+abstract" if in_read else "title",
                    "threat": t, "flag_L2": f, "l3_file": l3, "judgment": src, "reason": reason})
    # POST_HOC: Semantic Scholar citing works (raw/s2cites_*.json) that are not in pool_cy.csv (forward citations,
    # read at title+abstract level as required for forward citations of HRY20/PAT21; titles for the rest)
    import json
    pool_titles = {C.norm(r["title"]) for r in pool}
    s2 = {}
    for pth in sorted((HERE / "raw").glob("s2cites_*.json")):
        d = json.loads(pth.read_text(encoding="utf-8"))
        for rec in d["records"]:
            nt = C.norm(rec.get("title", ""))
            if nt and nt not in pool_titles:
                s2.setdefault(nt, [rec, set()])[1].add(d["anchor"])
    for nt, (rec, anchors) in sorted(s2.items()):
        if nt in ov:
            t, f, l3, reason = ov[nt]
            used.add(nt)
            src = "override"
        else:
            t = 1 if RULE1.search(rec["title"]) else 0
            f, l3, reason, src = False, "", "keyword rule on title (broad field)" if t else "keyword rule on title (off-topic)", "rule"
        out.append({"key": (rec.get("doi") or "").lower() or ("arxiv:" + rec["arxiv"] if rec.get("arxiv") else nt),
                    "title": rec["title"], "year": rec["year"], "origins": ";".join("s2cites:" + a for a in sorted(anchors)),
                    "cy_score": C.cy_score(rec["title"] + " " + (rec.get("abstract") or "")),
                    "read_level": "title+abstract" if (anchors & {"HRY20", "PAT21", "RHY22"}) else "title",
                    "threat": t, "flag_L2": f, "l3_file": l3, "judgment": src, "reason": reason + " [S2-only record, POST_HOC]"})
    with (HERE / "screening_cy_L1.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0].keys()))
        w.writeheader()
        w.writerows(out)
    from collections import Counter
    print("rows", len(out), Counter(o["threat"] for o in out), "flag_L2", sum(o["flag_L2"] for o in out),
          "read_set", sum(o["read_level"] != "title" for o in out))
    print("overrides not matched in pool:", [k for k in OVERRIDES if C.norm(k) not in used])


if __name__ == "__main__":
    main()
