"""Merge harvest candidates and (non-quarantined) snowball records into pool.csv.

Deduplicates by DOI / normalized title, keeps provenance (families, sources, via-anchors),
applies the fixed rubric, and assigns screening batches. Nothing is excluded; `screen_tier`
only decides the order in which Level-1 screening happens:
  T1 = red flag or score >= 7;  T2 = score 5-6;  T3 = rest (screened by title only).

Run:  python research/pmt_program/prior_art/merge_pool.py
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import harvest as H

HERE = Path(__file__).resolve().parent


def key_of(r: dict) -> str:
    return ((r.get("doi") or "").lower()) or (("arxiv:" + r["arxiv"]) if r.get("arxiv") else "") \
        or H.norm_title(r.get("title", ""))


def main() -> None:
    pool: dict[str, dict] = {}
    with (HERE / "candidates.csv").open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            k = r["key"]
            pool[k] = {**r, "via": "", "origin": "harvest"}
    for p in sorted(H.RAW.glob("snowball_*.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        a = d["anchor"]
        for r in d["records"]:
            k = key_of(r)
            if not k:
                continue
            tag = f"{d['direction']}:{a['id']}"
            if k in pool:
                m = pool[k]
                m["via"] = ";".join(sorted(set(filter(None, m["via"].split(";"))) | {tag}))
                fams = set(filter(None, m["families"].split(";"))) | {a["family"]}
                m["families"] = ";".join(sorted(fams))
                if "snowball" not in m["origin"]:
                    m["origin"] += "+snowball"
                for fld in ("abstract", "doi", "openalex", "venue", "authors"):
                    if not m.get(fld) and r.get(fld):
                        m[fld] = r[fld]
            else:
                pool[k] = {"key": k, "families": a["family"], "sources": "openalex-citations",
                           "title": r["title"], "year": r["year"], "authors": r["authors"],
                           "venue": r["venue"], "doi": r["doi"], "arxiv": r.get("arxiv", ""),
                           "openalex": r["openalex"], "zbmath": "", "msc": "",
                           "cited_by": r["cited_by"], "abstract": r["abstract"], "via": tag,
                           "origin": "snowball"}
    rows = []
    for k, m in pool.items():
        text = f"{m['title']} {m['abstract']}"
        sc = H.score(text)
        rf = bool(H.RED_FLAG.search(text))
        tier = "T1" if (rf or sc >= 7) else ("T2" if sc >= 5 else "T3")
        rows.append({"key": k, "screen_tier": tier, "score": sc, "red_flag": rf,
                     "origin": m["origin"], "families": m["families"], "sources": m.get("sources", ""),
                     "via": m["via"], "title": m["title"], "year": m["year"], "authors": m["authors"],
                     "venue": m["venue"], "doi": m["doi"], "arxiv": m.get("arxiv", ""),
                     "openalex": m.get("openalex", ""), "zbmath": m.get("zbmath", ""),
                     "msc": m.get("msc", ""), "cited_by": m.get("cited_by", ""),
                     "abstract": (m["abstract"] or "")[:1200]})
    rows.sort(key=lambda x: (x["screen_tier"], -x["score"]))
    with (HERE / "pool.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    from collections import Counter
    print("pool", len(rows), Counter(r["screen_tier"] for r in rows),
          "red_flags", sum(r["red_flag"] for r in rows))


if __name__ == "__main__":
    main()
