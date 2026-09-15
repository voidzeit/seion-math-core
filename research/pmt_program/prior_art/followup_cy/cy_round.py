"""PRIOR-ART-R-CY: targeted follow-up on tightness of heterogeneous composition constants (m >= 3).

Imports the round-1 `harvest.py` query functions unchanged (q_openalex, q_arxiv, q_s2, http_get,
openalex_abstract, norm_title). Round-1 / HET outputs are never written: all paths live in followup_cy/.

Commands (see PROTOCOL_CY.md):
  verify   resolve anchors_cy_spec.json via OpenAlex + Crossref, write anchors_cy.json
  forward  all-page OpenAlex `cites:` for every verified anchor work id -> raw/forward_*.json
  cocite   co-citation sets -> cocitation_cy.csv, forward_citations_cy.csv
  harvest  queries_cy.json on OpenAlex, arXiv, Semantic Scholar (backoff 30/60/120 s, per request)
  retry    supplemental pass for BLOCKED / ERROR keyword requests
  pool     merge forward + keyword records -> pool_cy.csv (cy_score orders reading only)

No personal data is sent (no mailto / API keys). SSL verification is never disabled.
Usage: python cy_round.py verify|forward|cocite|harvest|retry|pool
"""
from __future__ import annotations

import csv
import datetime as dt
import json
import re
import sys
import time
import urllib.error
import urllib.parse
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import harvest as H  # noqa: E402  (unchanged round-1 module)

RAW = HERE / "raw"
LOG = HERE / "SEARCH_LOG_CY.csv"
FIELDS = ["timestamp", "database", "family", "query", "request", "status", "results_total",
          "records_saved", "notes"]


def now() -> str:
    return dt.datetime.now().isoformat(timespec="seconds")


def log_row(row: dict) -> None:
    new = not LOG.exists()
    with LOG.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if new:
            w.writeheader()
        w.writerow(row)


def get_json(url: str) -> dict:
    last = None
    for wait in (0, 30, 60, 120):
        if wait:
            time.sleep(wait)
        try:
            return json.loads(H.http_get(url))
        except Exception as e:  # noqa: BLE001
            last = e
            if not re.search(r"429|503|timed out", str(e)):
                raise
    raise last  # type: ignore[misc]


def norm(t: str) -> str:
    return H.norm_title(t)


# ---------------------------------------------------------------- verify
def cmd_verify() -> None:
    spec = json.loads((HERE / "anchors_cy_spec.json").read_text(encoding="utf-8"))
    out = []
    for a in spec:
        rec = {**a, "openalex_ids": [], "checks": []}
        cands = []
        try:
            if a["id"].startswith("title:"):
                t = a["id"][6:]
                url = "https://api.openalex.org/works?" + urllib.parse.urlencode(
                    {"filter": "title.search:" + re.sub(r"[^A-Za-z0-9 ]", " ", t), "per-page": 25})
                d = get_json(url)
                cands = d.get("results", [])
            else:
                url = "https://api.openalex.org/works/doi:" + urllib.parse.quote(a["id"], safe="/")
                cands = [get_json(url)]
                # also look for other OpenAlex records (preprint versions) with the same title
                url2 = "https://api.openalex.org/works?" + urllib.parse.urlencode(
                    {"filter": "title.search:" + re.sub(r"[^A-Za-z0-9 ]", " ", a["expect_title"]),
                     "per-page": 25})
                cands += get_json(url2).get("results", [])
            status = "OK"
        except Exception as e:  # noqa: BLE001
            status = f"ERROR {type(e).__name__}: {str(e)[:150]}"
        log_row({"timestamp": now(), "database": "openalex-verify", "family": a["key"], "query": a["id"],
                 "request": "", "status": status.split()[0], "results_total": len(cands),
                 "records_saved": len(cands), "notes": status})
        seen = set()
        for w in cands:
            wid = w.get("id", "").rsplit("/", 1)[-1]
            if not wid or wid in seen:
                continue
            seen.add(wid)
            title_ok = norm(w.get("title") or "") == norm(a["expect_title"])
            auths = [x["author"]["display_name"] for x in w.get("authorships", [])]
            fa_ok = bool(auths) and a["expect_first_author"].lower() in auths[0].lower()
            yr_ok = w.get("publication_year") in a["expect_year"]
            chk = {"openalex_id": wid, "title": w.get("title"), "first_author": auths[0] if auths else "",
                   "year": w.get("publication_year"), "doi": (w.get("doi") or "").replace("https://doi.org/", ""),
                   "type": w.get("type"), "cited_by_count": w.get("cited_by_count"),
                   "title_match": title_ok, "first_author_match": fa_ok, "year_match": yr_ok}
            rec["checks"].append(chk)
            if title_ok and fa_ok:
                rec["openalex_ids"].append(wid)
        # Crossref check of every DOI found on matching OpenAlex records
        dois = {c["doi"] for c in rec["checks"] if c["title_match"] and c["first_author_match"] and c["doi"]}
        if not a["id"].startswith("title:"):
            dois.add(a["id"])
        rec["crossref"] = []
        for doi in sorted(dois):
            try:
                d = get_json("https://api.crossref.org/works/" + urllib.parse.quote(doi, safe="/"))
                m = d.get("message", {})
                ct = (m.get("title") or [""])[0]
                fa = ((m.get("author") or [{}])[0]).get("family", "")
                yr = ((m.get("issued") or {}).get("date-parts") or [[None]])[0][0]
                rec["crossref"].append({"doi": doi, "title": ct, "first_author": fa, "year": yr,
                                        "container": (m.get("container-title") or [""])[0],
                                        "title_match": norm(ct) == norm(a["expect_title"]),
                                        "first_author_match": a["expect_first_author"].lower() in fa.lower()})
                st = "OK"
            except urllib.error.HTTPError as e:
                rec["crossref"].append({"doi": doi, "error": f"HTTP {e.code}"})
                st = f"HTTP{e.code}"
            except Exception as e:  # noqa: BLE001
                rec["crossref"].append({"doi": doi, "error": f"{type(e).__name__}: {str(e)[:120]}"})
                st = "ERROR"
            log_row({"timestamp": now(), "database": "crossref-verify", "family": a["key"], "query": doi,
                     "request": "", "status": st, "results_total": "", "records_saved": "", "notes": ""})
            time.sleep(1)
        rec["verified"] = bool(rec["openalex_ids"]) and all(
            c.get("title_match") and c.get("first_author_match") for c in rec["crossref"]
            if c["doi"] == a["id"]) if not a["id"].startswith("title:") else bool(rec["openalex_ids"])
        out.append(rec)
        print(a["key"], "verified" if rec["verified"] else "NOT VERIFIED", rec["openalex_ids"], flush=True)
        time.sleep(1)
    (HERE / "anchors_cy.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")


# ---------------------------------------------------------------- forward
def to_rec(w: dict) -> dict:
    ids = w.get("ids") or {}
    loc = w.get("locations") or []
    arx = ""
    for l in loc:
        u = (l.get("landing_page_url") or "") + " " + (l.get("pdf_url") or "")
        m = re.search(r"arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5})", u)
        if m:
            arx = m.group(1)
            break
    return {"title": w.get("title") or "", "year": w.get("publication_year"),
            "venue": ((w.get("primary_location") or {}).get("source") or {}).get("display_name") or "",
            "doi": (w.get("doi") or "").replace("https://doi.org/", ""), "arxiv": arx,
            "authors": "; ".join(a["author"]["display_name"] for a in w.get("authorships", [])[:6]),
            "abstract": H.openalex_abstract(w.get("abstract_inverted_index"))[:2000],
            "cited_by": w.get("cited_by_count"), "openalex": (w.get("id") or "").rsplit("/", 1)[-1],
            "type": w.get("type"), "oa_url": ((w.get("open_access") or {}).get("oa_url") or "")}


def cmd_forward() -> None:
    anchors = json.loads((HERE / "anchors_cy.json").read_text(encoding="utf-8"))
    RAW.mkdir(exist_ok=True)
    for a in anchors:
        if not a.get("verified"):
            log_row({"timestamp": now(), "database": "openalex-cites", "family": a["key"], "query": a["id"],
                     "request": "", "status": "SKIPPED", "results_total": "", "records_saved": 0,
                     "notes": "anchor not verified"})
            continue
        for wid in a["openalex_ids"]:
            cursor, recs, page, total = "*", [], 0, None
            status, note = "OK", ""
            while cursor:
                url = "https://api.openalex.org/works?" + urllib.parse.urlencode(
                    {"filter": f"cites:{wid}", "per-page": 200, "cursor": cursor})
                try:
                    d = get_json(url)
                except Exception as e:  # noqa: BLE001
                    status, note = "ERROR", f"page {page}: {type(e).__name__}: {str(e)[:150]}"
                    break
                total = d.get("meta", {}).get("count")
                recs.extend(to_rec(w) for w in d.get("results", []))
                cursor = d.get("meta", {}).get("next_cursor") if d.get("results") else None
                page += 1
                time.sleep(1)
            (RAW / f"forward_{a['key']}_{wid}.json").write_text(json.dumps(
                {"anchor": a["key"], "work": wid, "meta_count": total, "records": recs},
                ensure_ascii=False, indent=1), encoding="utf-8")
            log_row({"timestamp": now(), "database": "openalex-cites", "family": a["key"],
                     "query": f"cites:{wid}", "request": f"pages={page}", "status": status,
                     "results_total": total, "records_saved": len(recs), "notes": note})
            print(a["key"], wid, status, total, len(recs), flush=True)


# ---------------------------------------------------------------- cocite
def load_forward() -> dict[str, dict[str, dict]]:
    by: dict[str, dict[str, dict]] = {}
    for p in sorted(RAW.glob("forward_*.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        s = by.setdefault(d["anchor"], {})
        for r in d["records"]:
            s[r["openalex"]] = r
    return by


def cmd_cocite() -> None:
    by = load_forward()
    allw: dict[str, dict] = {}
    for k, s in by.items():
        for wid, r in s.items():
            allw.setdefault(wid, {**r, "cites": set()})["cites"].add(k)
    with (HERE / "forward_citations_cy.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["openalex", "cites", "year", "title", "authors", "venue", "doi", "arxiv", "type", "cited_by",
                    "oa_url", "abstract"])
        for wid, r in sorted(allw.items(), key=lambda x: (-len(x[1]["cites"]), str(x[1]["year"]))):
            w.writerow([wid, ";".join(sorted(r["cites"])), r["year"], r["title"], r["authors"], r["venue"],
                        r["doi"], r["arxiv"], r["type"], r["cited_by"], r["oa_url"], r["abstract"]])
    sets = {
        "S1_CY15_and_HRY20": set(by.get("CY15", {})) & set(by.get("HRY20", {})),
        "S2_HRY20_and_RHY22": set(by.get("HRY20", {})) & set(by.get("RHY22", {})),
        "info_HRY20_and_OY02": set(by.get("HRY20", {})) & set(by.get("OY02", {})),
        "info_PAT21_and_HRY20": set(by.get("PAT21", {})) & set(by.get("HRY20", {})),
        "info_CY15_and_OY02": set(by.get("CY15", {})) & set(by.get("OY02", {})),
    }
    with (HERE / "cocitation_cy.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["set", "openalex", "cites_all", "year", "title", "authors", "venue", "doi", "arxiv", "oa_url",
                    "abstract"])
        for name, s in sets.items():
            for wid in sorted(s, key=lambda x: str(allw[x]["year"])):
                r = allw[wid]
                w.writerow([name, wid, ";".join(sorted(r["cites"])), r["year"], r["title"], r["authors"], r["venue"],
                            r["doi"], r["arxiv"], r["oa_url"], r["abstract"]])
    print({k: len(v) for k, v in by.items()}, {k: len(v) for k, v in sets.items()},
          "S1uS2", len(sets["S1_CY15_and_HRY20"] | sets["S2_HRY20_and_RHY22"]), "union_all", len(allw))


# ---------------------------------------------------------------- harvest
def run_query(src: str, q: str):
    fn = {"openalex": H.q_openalex, "arxiv": H.q_arxiv, "semanticscholar": H.q_s2}[src]
    last = ""
    for wait in (0, 30, 60, 120):
        if wait:
            time.sleep(wait)
        try:
            url, total, recs = fn(q)
            return "OK", url, total, recs, (f"after backoff {wait}s" if wait else "")
        except Exception as e:  # noqa: BLE001
            last = f"{type(e).__name__}: {str(e)[:160]}"
            if not re.search(r"429|503|timed out|Remote end closed|reset", last):
                return "ERROR", "", "", [], last
    return "BLOCKED", "", "", [], "still failing after backoff 30/60/120 s: " + last


def harvest_pass(todo, tag: str) -> None:
    RAW.mkdir(exist_ok=True)
    for fam, qi, q, src in todo:
        status, url, total, recs, note = run_query(src, q)
        for r in recs:
            r.update({"source": src, "family": fam, "query": q})
        (RAW / f"kw{tag}_{src}_{fam}_{qi}.json").write_text(json.dumps(
            {"query": q, "url": url, "status": status, "total": total, "records": recs},
            ensure_ascii=False, indent=1), encoding="utf-8")
        log_row({"timestamp": now(), "database": src, "family": fam, "query": q, "request": url,
                 "status": status, "results_total": total, "records_saved": len(recs),
                 "notes": (tag.strip("_") + " " + note).strip()})
        print(src, fam, qi, status, total, len(recs), note[:70], flush=True)
        time.sleep({"openalex": 1, "arxiv": 4, "semanticscholar": 6}[src])


def cmd_harvest() -> None:
    qs = json.loads((HERE / "queries_cy.json").read_text(encoding="utf-8"))
    todo = [(fam, qi, q, src) for fam, spec in qs["families"].items() for qi, q in enumerate(spec["queries"])
            for src in ("openalex", "arxiv", "semanticscholar")]
    harvest_pass(todo, "")


def cmd_retry() -> None:
    qs = json.loads((HERE / "queries_cy.json").read_text(encoding="utf-8"))
    rows = list(csv.DictReader(LOG.open(encoding="utf-8")))
    todo = []
    for fam, spec in qs["families"].items():
        for qi, q in enumerate(spec["queries"]):
            for src in ("openalex", "arxiv", "semanticscholar"):
                hits = [r for r in rows if r["database"] == src and r["family"] == fam and r["query"] == q]
                if hits and not any(r["status"] == "OK" for r in hits):
                    todo.append((fam, qi, q, src))
    print("retry todo", len(todo))
    harvest_pass(todo, "_retry")


# ---------------------------------------------------------------- pool
CY_GROUPS = [r"averaged|averagedness|firmly nonexpansive|nonexpansive|\bconic",
             r"composition|compositions|\bproduct of|products of",
             r"\btight|sharp|optimal (constant|coefficient|rate)|exact (region|value)|best (possible )?constant",
             r"scaled relative graph|\bsrgs?\b",
             r"minkowski",
             r"\bdisks?\b|\bdiscs?\b|\barcs?\b|circle|cartesian oval",
             r"projection|projector"]


def cy_score(text: str) -> int:
    t = (text or "").lower()
    return sum(1 for p in CY_GROUPS if re.search(p, t))


def cmd_pool() -> None:
    pool: dict[str, dict] = {}

    def key(r: dict) -> str:
        return (r.get("doi") or "").lower() or (("arxiv:" + r["arxiv"]) if r.get("arxiv") else "") \
            or (("oa:" + r["openalex"]) if r.get("openalex") else "") or norm(r.get("title", ""))

    title_index: dict[str, str] = {}

    def add(r: dict, origin: str, top10: bool) -> None:
        k = key(r)
        nt = norm(r.get("title", ""))
        if nt and nt in title_index:
            k = title_index[nt]
        if not k:
            return
        m = pool.setdefault(k, {"key": k, "title": r.get("title", ""), "year": r.get("year"),
                                "authors": r.get("authors", ""), "venue": r.get("venue", ""),
                                "doi": r.get("doi", ""), "arxiv": r.get("arxiv", ""),
                                "openalex": r.get("openalex", ""), "abstract": r.get("abstract", ""),
                                "origins": set(), "top10": False})
        if nt:
            title_index.setdefault(nt, k)
        m["origins"].add(origin)
        m["top10"] = m["top10"] or top10
        for fld in ("abstract", "doi", "arxiv", "openalex", "venue", "authors"):
            if not m.get(fld) and r.get(fld):
                m[fld] = r[fld]

    for p in sorted(RAW.glob("forward_*.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        for r in d["records"]:
            add(r, "fwd:" + d["anchor"], False)
    for p in sorted(RAW.glob("kw*.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        for i, r in enumerate(d["records"]):
            add(r, f"kw:{r.get('source', '')}:{r.get('family', '')}", i < 10)
    rows = []
    for k, m in pool.items():
        rows.append({**m, "origins": ";".join(sorted(m["origins"])),
                     "cy_score": cy_score(f"{m['title']} {m['abstract']}")})
    rows.sort(key=lambda x: (-x["cy_score"], x["title"]))
    with (HERE / "pool_cy.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["key", "cy_score", "top10", "origins", "year", "title", "authors", "venue",
                                          "doi", "arxiv", "openalex", "abstract"])
        w.writeheader()
        for r in rows:
            w.writerow({k: r[k] for k in w.fieldnames})
    print("pool_cy", len(rows), "cy>=2", sum(r["cy_score"] >= 2 for r in rows), "top10", sum(r["top10"] for r in rows))


if __name__ == "__main__":
    {"verify": cmd_verify, "forward": cmd_forward, "cocite": cmd_cocite, "harvest": cmd_harvest,
     "retry": cmd_retry, "pool": cmd_pool}[sys.argv[1]]()
