"""PRIOR-ART-R-CY: Crossref check of every DOI cited in the L3_CY sheets (title / first author / year recorded).

Writes l3_dois_cy.json and logs to SEARCH_LOG_CY.csv. arXiv-only records (no DOI) are listed with doi=null.
Usage: python cy_verify_l3.py
"""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse

import cy_round as C

EXPECT = [
    ("L3_CY_chaffey2023", "10.1109/TAC.2023.3234016", "Graphical Nonlinear System Analysis", "Chaffey"),
    ("L3_CY_bauschke2023", "10.1080/01630563.2023.2270308", "How Averaged is the Composition of Two Linear Projections?", "Bauschke"),
    ("L3_CY_giselsson2021", "10.1186/s13663-021-00709-0", "On compositions of special cases of Lipschitz continuous operators", "Giselsson"),
    ("L3_CY_lee2025", "10.1137/23M1621320", "Convergence Analyses of Davis–Yin Splitting via Scaled Relative Graphs", "Lee"),
    ("L3_CY_lee2025 (companion)", "10.1080/02331934.2025.2544700", "Convergence analyses of Davis–Yin splitting via scaled relative graphs II: convex optimization problems", "Yi"),
    ("L3_CY_combettes2020", "10.1137/19M1272780", "Lipschitz Certificates for Layered Network Structures Driven by Averaged Activation Operators", "Combettes"),
    ("L3_CY_bartz2022", "10.1007/s10898-021-01057-4", "Conical averagedness and convergence analysis of fixed point algorithms", "Bartz"),
    ("L3_CY_guthrie2021", "10.23919/ACC50511.2021.9482940", "Outer Approximations of Minkowski Operations on Complex Sets via Sum-of-Squares Optimization", "Guthrie"),
    ("L3_CY_bunger2019", "10.13001/1081-3810.3910", "The determinant of a complex matrix and Gershgorin circles", "Bünger"),
    ("L3_CY_bunger2019 (companion)", "10.1007/s00022-019-0502-2", "Complex disk products and Cartesian ovals", "Bünger"),
]
NO_DOI = [("L3_CY_song2025", "arXiv:2507.19533"), ("L3_CY_yang2026", "arXiv:2608.12591"), ("L3_CY_yang2026 (companion)", "arXiv:2510.06583")]


def main() -> None:
    out = []
    for sheet, doi, title, fa in EXPECT:
        rec = {"sheet": sheet, "doi": doi}
        try:
            m = C.get_json("https://api.crossref.org/works/" + urllib.parse.quote(doi, safe="/"))["message"]
            ct = (m.get("title") or [""])[0]
            auth = ((m.get("author") or [{}])[0]).get("family", "")
            rec.update({"crossref_title": ct, "first_author": auth,
                        "year": ((m.get("issued") or {}).get("date-parts") or [[None]])[0][0],
                        "container": (m.get("container-title") or [""])[0],
                        "title_match": C.norm(ct) == C.norm(title), "first_author_match": fa.lower() in auth.lower()})
            st = "OK"
        except urllib.error.HTTPError as e:
            rec["error"], st = f"HTTP {e.code}", f"HTTP{e.code}"
        except Exception as e:  # noqa: BLE001
            rec["error"], st = f"{type(e).__name__}: {str(e)[:120]}", "ERROR"
        C.log_row({"timestamp": C.now(), "database": "crossref-verify", "family": sheet, "query": doi, "request": "",
                   "status": st, "results_total": "", "records_saved": "", "notes": "L3 DOI check"})
        print(sheet, doi, st, rec.get("title_match"), rec.get("first_author_match"), flush=True)
        out.append(rec)
        time.sleep(1)
    out += [{"sheet": s, "doi": None, "identifier": i, "note": "NO_DOI (arXiv only)"} for s, i in NO_DOI]
    (C.HERE / "l3_dois_cy.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
