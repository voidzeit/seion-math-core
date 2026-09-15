"""Build PRIOR_ART_MATRIX.csv from pool.csv + Level-1/2 screening + adjudicated verdicts.

Precedence for threat_final: l3_verdicts.json (adjudicated) > Level-2 CSV > Level-1 (audited).
Mismatches between an adjudicated entry and a Level-2 CSV threat are printed and recorded in
`adjudication_note`.

Run:  python research/pmt_program/prior_art/build_matrix.py
"""
from __future__ import annotations

import csv
import glob
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
S = HERE / "screening"

FIELDS = ["citation_key", "key", "doi", "arxiv", "openalex", "title", "year", "authors", "venue",
          "families", "origin", "level_reached", "threat_final", "threat_L1", "threat_L2", "access",
          "theorem_location", "claims", "verdict", "cite_in_paper", "bib_class", "evidence_file",
          "adjudication_note"]


def norm(s: str) -> str:
    return (s or "").strip().lower()


def main() -> None:
    pool = {r["key"]: r for r in csv.DictReader((HERE / "pool.csv").open(encoding="utf-8"))}
    l1 = {r["key"]: r for r in csv.DictReader((S / "level1_results.csv").open(encoding="utf-8"))}
    l2 = {}
    for f in sorted(glob.glob(str(S / "level2_*.csv"))):
        if f.endswith("level2_queue.csv"):
            continue
        for r in csv.DictReader(open(f, encoding="utf-8")):
            r["_file"] = Path(f).name
            l2[r["key"]] = r
    adj = json.loads((HERE / "l3_verdicts.json").read_text(encoding="utf-8"))["sources"]

    rows: dict[str, dict] = {}
    for k, p in pool.items():
        r1 = l1.get(k, {})
        r2 = l2.get(k)
        row = {f: "" for f in FIELDS}
        row.update({"key": k, "doi": p["doi"], "arxiv": p.get("arxiv", ""), "openalex": p.get("openalex", ""),
                    "title": p["title"], "year": p["year"], "authors": p["authors"], "venue": p["venue"],
                    "families": p["families"], "origin": p["origin"], "threat_L1": r1.get("threat", ""),
                    "claims": r1.get("claims", ""), "verdict": r1.get("reason", ""), "level_reached": "L1",
                    "threat_final": r1.get("threat", ""), "cite_in_paper": "no"})
        if r2:
            row.update({"threat_L2": r2["threat_L2"], "access": r2["access"],
                        "theorem_location": r2["theorem_location"], "claims": r2["claims_affected"],
                        "verdict": r2["verdict"], "level_reached": "L2", "threat_final": r2["threat_L2"],
                        "evidence_file": "screening/" + r2["_file"]})
        rows[k] = row

    # match adjudicated entries to pool rows by DOI / arXiv / title
    by_doi = {norm(r["doi"]): k for k, r in rows.items() if r["doi"]}
    by_arx = {}
    for k, r in rows.items():
        a = norm(r["arxiv"]) or (norm(r["doi"]).split("arxiv.")[-1] if "arxiv." in norm(r["doi"]) else "")
        if a:
            by_arx[a] = k
    mismatches = []
    for a in adj:
        k = (a.get("pool_key") if a.get("pool_key") in rows else None) \
            or by_doi.get(norm(a.get("doi"))) or by_arx.get(norm(a.get("arxiv")))
        if k is None:
            k = "adjudicated:" + a["citation_key"]
            rows[k] = {f: "" for f in FIELDS}
            rows[k].update({"key": k, "origin": "adjudicated_only", "threat_L1": "", "threat_L2": ""})
        row = rows[k]
        note = a.get("threat_note", "")
        if row.get("threat_L2") not in ("", None) and str(row["threat_L2"]) != str(a["threat_final"]):
            note = (note + f" | L2 CSV threat {row['threat_L2']} vs adjudicated {a['threat_final']}").strip(" |")
            mismatches.append((a["citation_key"], row["threat_L2"], a["threat_final"]))
        row.update({"citation_key": a["citation_key"], "doi": a.get("doi") or row.get("doi", ""),
                    "arxiv": a.get("arxiv") or row.get("arxiv", ""), "title": a.get("title") or row.get("title", ""),
                    "year": a.get("year") or row.get("year", ""), "authors": a.get("authors") or row.get("authors", ""),
                    "level_reached": a["level"], "threat_final": a["threat_final"],
                    "access": a.get("access", row.get("access", "")), "claims": a.get("claims", ""),
                    "verdict": a["verdict"], "cite_in_paper": a["cite"], "bib_class": a["bib_class"],
                    "evidence_file": ("theorem_comparisons/" + a["file"]) if a.get("file", "").startswith("L3_") else a.get("file", ""),
                    "adjudication_note": note})

    out = sorted(rows.values(), key=lambda r: (-int(r["threat_final"] or 0), r["citation_key"] == "", r["title"]))
    with (HERE / "PRIOR_ART_MATRIX.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(out)
    print("rows", len(out), "threat_final", Counter(str(r["threat_final"]) for r in out))
    print("levels", Counter(r["level_reached"] for r in out), "cite", sum(r["cite_in_paper"] == "yes" for r in out))
    print("L2-vs-adjudicated mismatches:", mismatches)


if __name__ == "__main__":
    main()
