"""PRIOR-ART-R-CY — POST_HOC harvest scheduler (see PROTOCOL_CY.md section 9, entry "harvest scheduling").

Reason: in the frozen interleaved order (openalex, arxiv, semanticscholar per query) arXiv and Semantic Scholar
returned HTTP 429 from the first query on; with per-request backoff 30/60/120 s each blocked request costs ~4 min and
repeated attempts keep the IP rate-limited (projected run time ~3 h). This scheduler does NOT change queries, query
functions (harvest.py, unchanged) or the per-request backoff (cy_round.run_query, frozen). It only changes the ORDER
(all OpenAlex requests first, then Semantic Scholar, then arXiv) and adds a circuit breaker: after 2 consecutive
BLOCKED requests on a source, wait 600 s once and continue; after 2 further consecutive BLOCKED requests the remaining
requests of that source are logged DEFERRED (not attempted; never counted as zero results) for the `retry` pass.

Every request already logged OK in SEARCH_LOG_CY.csv is skipped. Raw files: raw/kw_v2_<src>_<fam>_<qi>.json.
Usage: python cy_harvest_v2.py [openalex|semanticscholar|arxiv ...]
"""
from __future__ import annotations

import csv
import json
import sys
import time

import cy_round as C


def main() -> None:
    sources = sys.argv[1:] or ["openalex", "semanticscholar", "arxiv"]
    qs = json.loads((C.HERE / "queries_cy.json").read_text(encoding="utf-8"))
    rows = list(csv.DictReader(C.LOG.open(encoding="utf-8"))) if C.LOG.exists() else []
    ok = {(r["database"], r["family"], r["query"]) for r in rows if r["status"] == "OK"}
    for src in sources:
        todo = [(fam, qi, q, src) for fam, spec in qs["families"].items() for qi, q in enumerate(spec["queries"])
                if (src, fam, q) not in ok]
        consecutive, cooled, deferred = 0, False, False
        for fam, qi, q, s in todo:
            if deferred:
                C.log_row({"timestamp": C.now(), "database": s, "family": fam, "query": q, "request": "",
                           "status": "DEFERRED", "results_total": "", "records_saved": 0,
                           "notes": "v2 circuit breaker: source still rate limited after 600 s cool-down; left for retry pass"})
                print(s, fam, qi, "DEFERRED", flush=True)
                continue
            status, url, total, recs, note = C.run_query(s, q)
            for r in recs:
                r.update({"source": s, "family": fam, "query": q})
            (C.RAW / f"kw_v2_{s}_{fam}_{qi}.json").write_text(json.dumps(
                {"query": q, "url": url, "status": status, "total": total, "records": recs},
                ensure_ascii=False, indent=1), encoding="utf-8")
            C.log_row({"timestamp": C.now(), "database": s, "family": fam, "query": q, "request": url,
                       "status": status, "results_total": total, "records_saved": len(recs),
                       "notes": ("v2 " + note).strip()})
            print(s, fam, qi, status, total, len(recs), note[:70], flush=True)
            consecutive = consecutive + 1 if status == "BLOCKED" else 0
            if consecutive >= 2:
                if not cooled:
                    print(s, "cool-down 600 s", flush=True)
                    time.sleep(600)
                    cooled, consecutive = True, 0
                else:
                    deferred = True
            time.sleep({"openalex": 1, "arxiv": 4, "semanticscholar": 6}[s])


if __name__ == "__main__":
    main()
