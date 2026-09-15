"""PRIOR-ART-R-HET Level 1: write screening/het_level1.csv from pool_het.csv.

Every row of pool_het.csv was read by the screener (titles for all rows; title+abstract for T1/T2,
het_score >= 2, and every override below). Judgments with threat >= 2 are explicit overrides
(matched by normalized title substring). All other rows receive 0 or 1 by a transparent rule that
encodes the screener's title judgment "no heterogeneous error / sharp-constant content indicated":
threat 1 if the title/abstract is in the broad field (tensor formats, projections/operator splitting,
quantum simulation fidelity, Minkowski/complex-set arithmetic, water-filling allocation), else 0.
Overrides with threat 1 are used where a borderline title was checked and judged background.

Run:  python research/pmt_program/prior_art/screening/het_level1_build.py
"""
from __future__ import annotations

import csv
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
POOL = HERE.parent / "pool_het.csv"
OUT = HERE / "het_level1.csv"

BROAD = re.compile(r"tensor|matrix product|dmrg|hierarchical tucker|tucker|low-rank|low rank|projection|projector|"
                   r"nonexpansive|averaged|splitting|monotone|fidelity|quantum circuit|minkowski|complex (set|disk|interval)|"
                   r"circular arithmetic|water-?fill|truncation|numerical range|renormalization group|entanglement", re.I)


def n(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


# (title substring, or '=' + exact normalized title, threat, claims, reason)
OV = [
    # ---- threat 3: forwarded to Level 2 / Level 3
    ("errortransportationinsvdbasedtensortrain", 3, "H1;H2",
     "Local SVD truncations transported through general dimension trees with node-wise (heterogeneous) local errors; tree-dependent conditioning factors (contrast H2); exact Pythagorean identity only for chains; abstract only"),
    ("hierarchicalsingularvaluedecompositionoftensors", 3, "H1;H2",
     "HSVD: error of product of node-wise projections bounded by root-sum-square of heterogeneous node tails in any order (placement/order-independent, non-sharp sqrt(2d-3)); linear tensor setting"),
    ("compositionsandconvexcombinationsofaveragednonexpansive", 3, "H1;H2;H4",
     "Averagedness constant of compositions of m operators with heterogeneous alpha_i, symmetric in the alpha_i (order-independent); tight for m=2 (Ogura-Yamada/HRY); different functional and linear-composition model"),
    ("tightcoefficientsofaveragedoperatorsviascaledrelativegraph", 3, "H4;H1",
     "Tightness of heterogeneous two-factor composition constant via Minkowski product of two different disks (Cartesian oval); heterogeneous sharpness for n=2 in a different functional"),
    # ---- threat 2
    ("rankadaptivetimeintegrationoftreetensornetworks", 2, "H1;H2",
     "Thm A.1 tree-shape-independent (d-1) truncation bound with uniform node tolerance (root tolerance may differ); telescoping; non-sharp"),
    ("whatlimitsthesimulationofquantumcomputers", 2, "H1;H2",
     "Eq. (17): multi-qubit fidelity approx. product of heterogeneous per-gate truncation fidelities (heuristic, verified numerically); no bound"),
    ("densitymatrixrenormalizationgroupalgorithmforsimulatingquantumcircuitswithafinitefidelity", 2, "H1",
     "Per-step fidelity accounting for truncated circuit simulation; empirical/heuristic multiplicativity"),
    ("oncompositionsofspecialcasesoflipschitzcontinuousoperators", 2, "H4;H1",
     "Compositions of different special Lipschitz classes with tight examples; heterogeneous composition constants, different functional"),
    ("complexdiskproductsandcartesianovals", 2, "H1;H4",
     "Bunger-Rump: exact products of two complex disks via Cartesian ovals; scalar heterogeneous product geometry, full disks not arcs"),
    ("algorithmsforminkowskiproductsandimplicitlydefinedcomplexsets", 2, "H1;H4",
     "Minkowski products of complex sets, boundary via logarithmic Gauss map; no box-constrained arcs or |1-z| objective"),
    ("=minkowskigeometricalgebraofcomplexsets", 2, "H1;H4", "MGA framework (round-1 L3: two-disk ovals); heterogeneous products of complex sets"),
    ("constructionofvaluesetforrobustnessanalysisviacirculararithmetic", 2, "H1;H4",
     "Value set of product of uncertain factors with disk uncertainty (heterogeneous radii); round-1 L3 abstract only"),
    ("complexintervalarithmeticusingpolarform", 2, "H1;H4",
     "Polar complex intervals: exact products where argument ranges add and moduli multiply; heterogeneous angle boxes but no cos(theta)e^{i theta} coupling"),
    ("minkowskiproductofconvexsetsandproductnumericalrange", 2, "H1", "Minkowski products of convex complex sets and product numerical range; heterogeneous factors, no error functional"),
    ("waterfillingageometricapproach", 2, "H3", "Geometric water-filling incl. individual peak-power caps (GWFPP): capped-level allocation min(cap, level); H3 technique only"),
    ("newviewpointandalgorithmsforwaterfillingsolutions", 2, "H3", "Unified water-filling variants incl. bounded (capped) levels; H3 technique only"),
    ("onareductionforaclassofresourceallocationproblems", 2, "H3", "Separable convex resource allocation with bound constraints (breakpoint solutions); H3 technique only"),
    ("aclassofconvexquadraticnonseparableresourceallocationproblemswithgeneralizedboundconstraints", 1, "H3", "Resource allocation with generalized bounds; quadratic, background"),
    ("treeadaptiveapproximationinthehierarchicaltensorformat", 1, "H1", "Abstract checked: agglomerative choice of dimension tree with rank-adaptive cross approximation; no node-wise error theorem indicated"),
    ("iterativemethodsbasedonsoftthresholdingofhierarchicaltensors", 2, "H1;H2", "Node-wise soft thresholding in HT with global error estimates in terms of node thresholds; non-sharp"),
    ("=tensortraindecomposition", 2, "H1;H2", "TT-SVD: error <= sqrt(sum eps_k^2) with heterogeneous unfolding errors; tolerance eps/sqrt(d-1) per core (uniform allocation); non-sharp"),
    ("tensorspacesandnumericaltensorcalculus", 2, "H1;H2", "Monograph: HOSVD truncation in HT, error <= sqrt(sum over nodes of discarded tails) (Thm 11.58); heterogeneous, non-sharp"),
    ("amultilinearsingularvaluedecomposition", 1, "H1", "HOSVD per-mode tails sum bound; background"),
    ("adaptivehierarchicalsubtensorpartitioningfortensorcompression", 2, "H2;H3", "Allocation of a global error budget across subtensors/nodes; additive budget"),
    ("approximatelyoptimalcoreshapesfortensordecompositions", 2, "H2;H3", "Rank (core shape) allocation under size constraint with reconstruction-error guarantees extended to tree tensor networks; additive tail budgets"),
    ("simulatingquantumcircuitsusingtreetensornetworks", 2, "H1", "Truncated TTN circuit simulation with per-truncation fidelity estimates"),
    ("operatorsplittingperformanceestimationtightcontractionfactors", 2, "H4", "Tight contraction factors of compositions via performance estimation; sharpness methodology, different functional"),
    ("tightgloballinearconvergenceratebounds foroperatorsplittingmethods".replace(" ", ""), 1, "H4", "Abstract checked (Banjac-Goulart): tight linear rate bounds for strongly quasi-nonexpansive splitting operators; background"),
    ("scaledrelativegraphsnonexpansiveoperatorsvia2deuclideangeometry", 2, "H1;H4", "SRG of composition contained in product of SRGs with heterogeneous factors; 'angles add, lengths multiply' (round-1 L3)"),
    ("themethodofalternatingprojectionsandthemethodofsubspacecorrections", 2, "H1;H4", "Xu-Zikatanov identity for norm of product of heterogeneous (I-P_j); exact but different quantity"),
    ("efficientclassicalsimulationofslightlyentangledquantumcomputations", 2, "H1;H2", "Per-step truncation errors accumulate additively in TEBD-type simulation (heterogeneous, first-order)"),
    ("efficientsimulationofonedimensionalquantummanybodysystems", 2, "H1;H2", "TEBD truncation errors add over steps (heterogeneous additive budget)"),
    ("activelearningoftreetensornetworksusingoptimalleastsquares", 2, "H1;H2", "Tree-based PCA with rank adaptation to a prescribed error; error bound in expectation built from node-wise contributions; non-sharp"),
    ("calibratingtheclassicalhardnessofthequantumapproximateoptimizationalgorithm", 1, "H1", "MPS fidelity vs bond dimension for QAOA; per-gate fidelity model, background"),
    ("recursivewaterfillingforwirelesslinks", 1, "H3", "Water-filling with cumulative caps; background"),
    ("optimumpowerallocationforparallelgaussianchannelswitharbitraryinput", 1, "H3", "Mercury water-filling; background"),
    ("waterfillingisuniversallyminimaxoptimal", 1, "H3", "Online water-filling; background"),
    ("modulusofconicallyaveragedmappings", 1, "H1", "Conical averagedness modulus and Friedrichs/Dixmier angles for two subspaces; background"),
    ("productnumericalrangeinaspacewithtensorproductstructure", 1, "H1", "Product numerical range; background"),
    ("outerapproximationsofminkowskioperationsoncomplexsets", 1, "H1", "SOS outer approximations of Minkowski operations; background"),
    ("certifiedquantumschr", 1, "H1", "Fixed-rank HT truncation as bounded perturbation in closed-loop control; background"),
]


def main() -> None:
    rows = list(csv.DictReader(POOL.open(encoding="utf-8")))
    out = []
    used = set()
    for r in rows:
        t = n(r["title"])
        hit = next((o for o in OV if (t == o[0][1:] if o[0].startswith("=") else o[0] in t)), None)
        basis = "abs" if (r["screen_tier"] in ("T1", "T2") or int(r["het_score"]) >= 2 or hit) else "title"
        if hit:
            used.add(hit[0])
            thr, claims, reason = hit[1], hit[2], hit[3]
        else:
            thr = 1 if BROAD.search(f"{r['title']} {r['abstract'][:300] if basis == 'abs' else ''}") else 0
            claims = ""
            reason = ("same broad field; no heterogeneous/nodewise error bound, sharp constant or placement statement indicated"
                      if thr else "unrelated to H1-H4")
        out.append({"key": r["key"], "threat": thr, "claims": claims,
                    "reason": f"[{basis}] {reason}" + (" [seen_in_round1]" if r["seen_in_round1"] == "True" else ""),
                    "level2": "yes" if thr >= 3 else "no"})
    unused = [o[0] for o in OV if o[0] not in used]
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["key", "threat", "claims", "reason", "level2"])
        w.writeheader()
        w.writerows(out)
    from collections import Counter
    print("L1 rows", len(out), Counter(o["threat"] for o in out), "unmatched overrides:", unused)


if __name__ == "__main__":
    main()
