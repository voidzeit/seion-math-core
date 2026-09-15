"""PRIOR-ART-R-CY — POST_HOC coverage supplements (PROTOCOL_CY.md section 9).

  oa_preprints  OpenAlex records of the arXiv versions of HRY20 and RHY22 (DataCite DOIs), verified by title and
                first author, then all-page `cites:` into raw/forward_<KEY>_<Wid>.json (so `cy_round.py cocite`
                includes them). Reason: the exact-title search in `verify` returned only the journal records for these two.
  s2_cites      Semantic Scholar citation lists (all pages, limit 1000) for the five anchors into raw/s2cites_<KEY>.json,
                and co-citation sets by DOI / arXiv id / normalized title into cocitation_cy_s2.csv.
                Reason: OpenAlex citation counts for SRG papers are low (e.g. RHY22: 19).

Uses harvest.py / cy_round.py helpers unchanged. Usage: python cy_supplement.py oa_preprints|s2_cites|s2_cocite
"""
from __future__ import annotations

import csv
import json
import sys
import time
import urllib.parse

import cy_round as C

PREPRINTS = {"HRY20": ("10.48550/arxiv.1912.01593", "Tight coefficients of averaged operators via scaled relative graph", "Huang"),
             "RHY22": ("10.48550/arxiv.1902.09788", "Scaled relative graphs: nonexpansive operators via 2D Euclidean geometry", "Ryu")}
S2_IDS = {"CY15": "DOI:10.1016/j.jmaa.2014.11.044", "HRY20": "DOI:10.1016/j.jmaa.2020.124211",
          "RHY22": "DOI:10.1007/s10107-021-01639-w", "OY02": "DOI:10.1081/NFA-120003674", "PAT21": "ARXIV:2106.05650"}


def cmd_oa_preprints() -> None:
    anchors = json.loads((C.HERE / "anchors_cy.json").read_text(encoding="utf-8"))
    for key, (doi, title, fa) in PREPRINTS.items():
        try:
            w = C.get_json("https://api.openalex.org/works/doi:" + urllib.parse.quote(doi, safe="/"))
            status = "OK"
        except Exception as e:  # noqa: BLE001
            w, status = {}, f"ERROR {type(e).__name__}: {str(e)[:120]}"
        wid = (w.get("id") or "").rsplit("/", 1)[-1]
        auths = [x["author"]["display_name"] for x in w.get("authorships", [])]
        match = bool(w) and C.norm(w.get("title") or "") == C.norm(title) and bool(auths) and fa.lower() in auths[0].lower()
        C.log_row({"timestamp": C.now(), "database": "openalex-verify", "family": key, "query": doi,
                   "request": wid, "status": status.split()[0], "results_total": 1 if w else 0, "records_saved": 1 if w else 0,
                   "notes": f"POST_HOC preprint record; title+first-author match={match}; title={w.get('title')!r}"})
        print(key, doi, wid, match, flush=True)
        for a in anchors:
            if a["key"] == key:
                a.setdefault("post_hoc_preprint_ids", []).append({"openalex_id": wid, "doi": doi, "match": match})
                if match and wid not in a["openalex_ids"]:
                    a["openalex_ids"].append(wid)
        if not match:
            continue
        cursor, recs, page, total = "*", [], 0, None
        while cursor:
            d = C.get_json("https://api.openalex.org/works?" + urllib.parse.urlencode(
                {"filter": f"cites:{wid}", "per-page": 200, "cursor": cursor}))
            total = d.get("meta", {}).get("count")
            recs.extend(C.to_rec(x) for x in d.get("results", []))
            cursor = d.get("meta", {}).get("next_cursor") if d.get("results") else None
            page += 1
            time.sleep(1)
        (C.RAW / f"forward_{key}_{wid}.json").write_text(json.dumps(
            {"anchor": key, "work": wid, "meta_count": total, "records": recs, "post_hoc": True},
            ensure_ascii=False, indent=1), encoding="utf-8")
        C.log_row({"timestamp": C.now(), "database": "openalex-cites", "family": key, "query": f"cites:{wid}",
                   "request": f"pages={page}", "status": "OK", "results_total": total, "records_saved": len(recs),
                   "notes": "POST_HOC preprint record"})
        print(key, wid, total, len(recs), flush=True)
    (C.HERE / "anchors_cy.json").write_text(json.dumps(anchors, ensure_ascii=False, indent=1), encoding="utf-8")


def cmd_s2_cites() -> None:
    for key, pid in S2_IDS.items():
        recs, offset, status, note = [], 0, "OK", ""
        while True:
            url = (f"https://api.semanticscholar.org/graph/v1/paper/{urllib.parse.quote(pid, safe=':/')}/citations?"
                   + urllib.parse.urlencode({"fields": "title,year,venue,externalIds,authors,abstract",
                                             "limit": 1000, "offset": offset}))
            try:
                d = C.get_json(url)
            except Exception as e:  # noqa: BLE001
                status, note = "BLOCKED" if "429" in str(e) else "ERROR", f"offset {offset}: {type(e).__name__}: {str(e)[:150]}"
                break
            for c in d.get("data", []) or []:
                p = c.get("citingPaper") or {}
                ext = p.get("externalIds") or {}
                recs.append({"title": p.get("title") or "", "year": p.get("year"), "venue": p.get("venue") or "",
                             "doi": (ext.get("DOI") or ""), "arxiv": ext.get("ArXiv") or "",
                             "authors": "; ".join(a.get("name", "") for a in (p.get("authors") or [])[:6]),
                             "abstract": (p.get("abstract") or "")[:2000], "openalex": "", "source": "s2cites"})
            if d.get("next") is None:
                break
            offset = d["next"]
            time.sleep(6)
        (C.RAW / f"s2cites_{key}.json").write_text(json.dumps({"anchor": key, "paper": pid, "status": status,
                                                                "records": recs}, ensure_ascii=False, indent=1),
                                                    encoding="utf-8")
        C.log_row({"timestamp": C.now(), "database": "semanticscholar-cites", "family": key, "query": pid, "request": "",
                   "status": status, "results_total": len(recs) if status == "OK" else "", "records_saved": len(recs),
                   "notes": ("POST_HOC " + note).strip()})
        print(key, status, len(recs), note[:80], flush=True)
        time.sleep(8)
    cmd_s2_cocite()


def ident(r: dict) -> str:
    return (r.get("doi") or "").lower() or (("arxiv:" + r["arxiv"]) if r.get("arxiv") else "") or C.norm(r.get("title", ""))


def cmd_s2_cocite() -> None:
    by: dict[str, dict[str, dict]] = {}
    for p in sorted(C.RAW.glob("s2cites_*.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        by[d["anchor"]] = {C.norm(r["title"]): r for r in d["records"] if r.get("title")}
    sets = {"S1_CY15_and_HRY20": ("CY15", "HRY20"), "S2_HRY20_and_RHY22": ("HRY20", "RHY22"),
            "info_PAT21_and_HRY20": ("PAT21", "HRY20")}
    with (C.HERE / "cocitation_cy_s2.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["set", "year", "title", "authors", "venue", "doi", "arxiv", "abstract"])
        for name, (a, b) in sets.items():
            for t in sorted(set(by.get(a, {})) & set(by.get(b, {}))):
                r = by[a][t]
                w.writerow([name, r["year"], r["title"], r["authors"], r["venue"], r["doi"], r["arxiv"], r["abstract"]])
    print({k: len(v) for k, v in by.items()},
          {n: len(set(by.get(a, {})) & set(by.get(b, {}))) for n, (a, b) in sets.items()})


if __name__ == "__main__":
    {"oa_preprints": cmd_oa_preprints, "s2_cites": cmd_s2_cites, "s2_cocite": cmd_s2_cocite}[sys.argv[1]]()
