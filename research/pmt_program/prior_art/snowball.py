"""PRIOR-ART-R snowballing via the OpenAlex citation graph.

Input : anchors.json  — list of {"id": "Wxxxx" or DOI, "family": "A", "why": "..."}
Output: raw/snowball_*.json, rows appended to SEARCH_LOG.csv, snowball_candidates.csv
        (backward = referenced works; forward = citing works, top 50 by citation count).
The same rubric as harvest.py orders candidates; nothing is excluded automatically.

Run:  python research/pmt_program/prior_art/snowball.py [round_label]
"""
from __future__ import annotations

import csv
import datetime as dt
import json
import sys
import time
import urllib.parse
from pathlib import Path

import harvest as H

HERE = Path(__file__).resolve().parent


def oa(url: str) -> dict:
    return json.loads(H.http_get(url))


def work(id_or_doi: str) -> dict:
    if id_or_doi.upper().startswith("W"):
        return oa(f"https://api.openalex.org/works/{id_or_doi}")
    return oa("https://api.openalex.org/works/doi:" + urllib.parse.quote(id_or_doi, safe="/"))


def to_rec(w: dict) -> dict:
    return {
        "title": w.get("title") or "", "year": w.get("publication_year"),
        "venue": ((w.get("primary_location") or {}).get("source") or {}).get("display_name") or "",
        "doi": (w.get("doi") or "").replace("https://doi.org/", ""), "arxiv": "",
        "authors": "; ".join(a["author"]["display_name"] for a in w.get("authorships", [])[:6]),
        "abstract": H.openalex_abstract(w.get("abstract_inverted_index"))[:2000],
        "cited_by": w.get("cited_by_count"), "openalex": w.get("id", ""), "zbmath": "", "msc": "",
    }


def batch(ids: list[str]) -> list[dict]:
    out = []
    for i in range(0, len(ids), 50):
        chunk = [x.rsplit("/", 1)[-1] for x in ids[i:i + 50]]
        url = "https://api.openalex.org/works?" + urllib.parse.urlencode(
            {"filter": "openalex_id:" + "|".join(chunk), "per-page": 50})
        out.extend(oa(url).get("results", []))
        time.sleep(1)
    return out


def main() -> None:
    label = sys.argv[1] if len(sys.argv) > 1 else "round1"
    anchors = json.loads((HERE / "anchors.json").read_text(encoding="utf-8"))
    if len(sys.argv) > 2:  # optional comma-separated subset of anchor ids
        subset = set(sys.argv[2].split(","))
        anchors = [a for a in anchors if a["id"] in subset]
    rows: dict[str, dict] = {}
    for a in anchors:
        now = dt.datetime.now().isoformat(timespec="seconds")
        try:
            w = work(a["id"])
            wid = w["id"].rsplit("/", 1)[-1]
            back = batch(w.get("referenced_works", []))
            fwd_url = "https://api.openalex.org/works?" + urllib.parse.urlencode(
                {"filter": f"cites:{wid}", "per-page": 50, "sort": "cited_by_count:desc"})
            fwd_d = oa(fwd_url)
            fwd = fwd_d.get("results", [])
            status, note = "OK", ""
        except Exception as e:
            back, fwd, status, note, wid = [], [], "ERROR", f"{type(e).__name__}: {str(e)[:200]}", a["id"]
            fwd_d = {}
        for direction, lst in (("backward", back), ("forward", fwd)):
            recs = [to_rec(x) for x in lst]
            (H.RAW / f"snowball_{label}_{wid}_{direction}.json").write_text(
                json.dumps({"anchor": a, "direction": direction, "records": recs},
                           ensure_ascii=False, indent=1), encoding="utf-8")
            H.log_row({"timestamp": now, "database": "openalex-citations", "family": a["family"],
                       "query": f"{label} {direction} of {a['id']}", "request": wid,
                       "status": status,
                       "results_total": (len(w.get("referenced_works", [])) if direction == "backward" and status == "OK"
                                         else (fwd_d.get("meta", {}).get("count") if status == "OK" else "")),
                       "records_saved": len(recs), "notes": note})
            for r in recs:
                key = r["doi"].lower() or H.norm_title(r["title"])
                if not key:
                    continue
                m = rows.setdefault(key, {**r, "via": set(), "families": set()})
                m["via"].add(f"{direction}:{a['id']}")
                m["families"].add(a["family"])
        print(f"{a['id']} {status} back={len(back)} fwd={len(fwd)} {note[:80]}", flush=True)
        time.sleep(1)
    existing = set()
    cands = HERE / "candidates.csv"
    if cands.exists():
        with cands.open(encoding="utf-8") as f:
            existing = {r["key"] for r in csv.DictReader(f)}
    out = []
    for key, m in rows.items():
        text = f"{m['title']} {m['abstract']}"
        out.append({"key": key, "new_vs_harvest": key not in existing, "score": H.score(text),
                    "red_flag": bool(H.RED_FLAG.search(text)), "families": ";".join(sorted(m["families"])),
                    "via": ";".join(sorted(m["via"])), "title": m["title"], "year": m["year"],
                    "authors": m["authors"], "venue": m["venue"], "doi": m["doi"],
                    "openalex": m["openalex"], "cited_by": m["cited_by"], "abstract": m["abstract"]})
    out.sort(key=lambda x: (-int(x["red_flag"]), -x["score"]))
    path = HERE / f"snowball_candidates_{label}.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys()) if out else ["key"])
        w.writeheader()
        w.writerows(out)
    print(f"snowball {label}: unique={len(out)} new={sum(r['new_vs_harvest'] for r in out)}")


if __name__ == "__main__":
    main()
