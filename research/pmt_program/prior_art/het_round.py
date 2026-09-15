"""PRIOR-ART-R-HET: thin wrapper that re-runs the round-1 scripts on the heterogeneous round.

The round-1 scripts (harvest.py, snowball.py, merge_pool.py, build_matrix.py, build_bib.py) are
imported unchanged. Only their module-level path globals are redirected, so round-1 behaviour
(query logic, rubric, dedup keys, error handling) is identical and round-1 outputs are never
overwritten.

  round-1 file              -> het file
  queries.json              -> queries_het.json
  raw/                      -> raw/het/
  SEARCH_LOG.csv            -> SEARCH_LOG_HET.csv
  candidates.csv            -> candidates_het.csv
  anchors.json              -> anchors_het.json
  pool.csv                  -> pool_het.csv          (+ columns seen_in_round1, het_score)
  screening/level1_results  -> screening/het_level1.csv
  screening/level2_*.csv    -> screening/het_level2.csv
  l3_verdicts.json          -> l3_verdicts_het.json
  PRIOR_ART_MATRIX.csv      -> PRIOR_ART_MATRIX_HET.csv
  bibliography/references   -> bibliography/references_het.bib

Preregistered additions (SEARCH_PROTOCOL_HET.md section 4-5):
  * `retry`: one supplemental pass for arXiv / Semantic Scholar queries that were SKIPPED or ERROR
    in the main harvest, with exponential backoff (30, 60, 120 s); raw files `*_retry_*.json`.
  * `merge`: after merge_pool, records of the retry pass are added with the same dedup key and
    rubric; `seen_in_round1` (key in round-1 pool.csv) and an informational `het_score` are
    appended. `het_score` only orders reading inside a tier; tiers are the round-1 tiers.

Usage:  python het_round.py harvest|retry|snowball|merge|matrix|bib
"""
from __future__ import annotations

import csv
import datetime as dt
import json
import re
import sys
import time
import urllib.error
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import harvest as H  # noqa: E402

MAP = {
    "queries.json": "queries_het.json",
    "candidates.csv": "candidates_het.csv",
    "anchors.json": "anchors_het.json",
    "pool.csv": "pool_het.csv",
    "l3_verdicts.json": "l3_verdicts_het.json",
    "PRIOR_ART_MATRIX.csv": "PRIOR_ART_MATRIX_HET.csv",
    "level1_results.csv": "het_level1.csv",
    "level2_*.csv": "het_level2.csv",
}


class Redirect:
    """Path stand-in: `Redirect(base) / name` maps round-1 file names to het file names."""

    def __init__(self, base: Path):
        self.base = base

    def __truediv__(self, name: str) -> Path:
        if name.startswith("snowball_candidates_"):
            return self.base / name
        return self.base / MAP.get(name, name)


RAW_HET = HERE / "raw" / "het"
LOG_HET = HERE / "SEARCH_LOG_HET.csv"
HET_RX = [r"heterogen", r"non-?uniform", r"node-?(wise|dependent)", r"local (error|tolerance|truncation)",
          r"budget", r"allocat", r"toleranc", r"different (angles|radii|parameters)",
          r"minkowski product", r"water-?filling", r"fidelit"]


def het_score(text: str) -> int:
    t = (text or "").lower()
    return sum(1 for p in HET_RX if re.search(p, t))


def patch_harvest() -> None:
    RAW_HET.mkdir(parents=True, exist_ok=True)
    H.RAW = RAW_HET
    H.LOG = LOG_HET
    H.CANDS = HERE / "candidates_het.csv"
    H.HERE = Redirect(HERE)


def cmd_harvest() -> None:
    patch_harvest()
    H.main()


def cmd_retry() -> None:
    patch_harvest()
    qs = json.loads((HERE / "queries_het.json").read_text(encoding="utf-8"))
    rows = list(csv.DictReader(LOG_HET.open(encoding="utf-8")))
    todo = []
    for fam, spec in qs["families"].items():
        for qi, q in enumerate(spec["queries"]):
            for src in ("arxiv", "semanticscholar"):
                hits = [r for r in rows if r["database"] == src and r["family"] == fam and r["query"] == q]
                if not hits or all(r["status"] in ("SKIPPED", "ERROR") for r in hits):
                    todo.append((fam, qi, q, src))
    blocked: set[str] = set()
    for fam, qi, q, src in todo:
        now = dt.datetime.now().isoformat(timespec="seconds")
        if src in blocked:
            H.log_row({"timestamp": now, "database": src, "family": fam, "query": q, "request": "",
                       "status": "SKIPPED", "results_total": "", "records_saved": 0,
                       "notes": "retry pass: still rate limited after backoff 30/60/120 s"})
            continue
        fn = H.q_arxiv if src == "arxiv" else H.q_s2
        url, total, recs, status, note = "", "", [], "ERROR", ""
        for wait in (0, 30, 60, 120):
            if wait:
                time.sleep(wait)
            try:
                url, total, recs = fn(q)
                status, note = "OK", f"retry pass (waited {wait}s before success)" if wait else "retry pass"
                break
            except Exception as e:  # logged
                note = f"retry pass: {type(e).__name__}: {str(e)[:160]}"
                if not re.search(r"429|503|timed out", note):
                    break
        if status != "OK" and re.search(r"429|503|timed out", note):
            blocked.add(src)
        for r in recs:
            r.update({"source": src, "family": fam, "query": q})
        (RAW_HET / f"{src}_retry_{fam}_{qi}.json").write_text(
            json.dumps({"query": q, "url": url, "total": total, "records": recs}, ensure_ascii=False, indent=1),
            encoding="utf-8")
        H.log_row({"timestamp": now, "database": src, "family": fam, "query": q, "request": url,
                   "status": status, "results_total": total, "records_saved": len(recs), "notes": note})
        print(src, fam, qi, status, total, len(recs), note[:80], flush=True)
        time.sleep(4 if src == "arxiv" else 6)


def cmd_snowball() -> None:
    patch_harvest()
    import snowball as S
    S.HERE = Redirect(HERE)
    sys.argv = [sys.argv[0], "het"] + sys.argv[2:]
    S.main()


def cmd_merge() -> None:
    patch_harvest()
    import merge_pool as MP
    MP.HERE = Redirect(HERE)
    MP.main()
    path = HERE / "pool_het.csv"
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    keys = {r["key"] for r in rows}
    # add retry-pass records (same dedup key and rubric as harvest.py / merge_pool.py)
    added = 0
    for p in sorted(RAW_HET.glob("*_retry_*.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        for r in d["records"]:
            k = MP.key_of(r)
            if not k:
                continue
            if k in keys:
                m = next(x for x in rows if x["key"] == k)
                srcs = set(filter(None, m["sources"].split(";"))) | {r["source"]}
                m["sources"] = ";".join(sorted(srcs))
                fams = set(filter(None, m["families"].split(";"))) | {r["family"]}
                m["families"] = ";".join(sorted(fams))
                if not m["abstract"] and r.get("abstract"):
                    m["abstract"] = r["abstract"][:1200]
                continue
            text = f"{r['title']} {r['abstract']}"
            sc = H.score(text)
            rf = bool(H.RED_FLAG.search(text))
            rows.append({"key": k, "screen_tier": "T1" if (rf or sc >= 7) else ("T2" if sc >= 5 else "T3"),
                         "score": sc, "red_flag": rf, "origin": "harvest_retry", "families": r["family"],
                         "sources": r["source"], "via": "", "title": r["title"], "year": r["year"],
                         "authors": r["authors"], "venue": r["venue"], "doi": r["doi"], "arxiv": r.get("arxiv", ""),
                         "openalex": "", "zbmath": "", "msc": "", "cited_by": r.get("cited_by", ""),
                         "abstract": (r["abstract"] or "")[:1200]})
            keys.add(k)
            added += 1
    r1 = {r["key"] for r in csv.DictReader((HERE / "pool.csv").open(encoding="utf-8"))}
    r1_titles = {H.norm_title(r["title"]) for r in csv.DictReader((HERE / "pool.csv").open(encoding="utf-8"))}
    for r in rows:
        r["seen_in_round1"] = (r["key"] in r1) or (H.norm_title(r["title"]) in r1_titles and bool(H.norm_title(r["title"])))
        r["het_score"] = het_score(f"{r['title']} {r['abstract']}")
    rows.sort(key=lambda x: (x["screen_tier"], -int(x["score"]), -int(x["het_score"])))
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    from collections import Counter
    print("pool_het", len(rows), "retry_added", added, Counter(r["screen_tier"] for r in rows),
          "seen_in_round1", sum(r["seen_in_round1"] for r in rows))


def cmd_matrix() -> None:
    import build_matrix as BM
    BM.HERE = Redirect(HERE)
    BM.S = Redirect(HERE / "screening")
    BM.main()


def cmd_bib() -> None:
    import build_bib as BB
    BB.HERE = Redirect(HERE)
    BB.OUT = HERE / "bibliography" / "references_het.bib"
    BB.main()


if __name__ == "__main__":
    {"harvest": cmd_harvest, "retry": cmd_retry, "snowball": cmd_snowball, "merge": cmd_merge,
     "matrix": cmd_matrix, "bib": cmd_bib}[sys.argv[1]]()
