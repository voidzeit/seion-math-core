"""PRIOR-ART-R automated harvest (Level 0).

Runs every query in queries.json against OpenAlex, arXiv, zbMATH Open and Semantic Scholar,
logs every request to SEARCH_LOG.csv, stores raw responses in raw/, and writes a deduplicated,
rubric-ranked candidates.csv. The rubric only orders candidates; it never excludes them.

No personal data is sent (no mailto / API keys). SSL verification is never disabled; zbMATH is
fetched through PowerShell (Windows certificate store) when Python's store rejects its chain.

Run:  python research/pmt_program/prior_art/harvest.py
"""
from __future__ import annotations

import csv
import datetime as dt
import json
import re
import subprocess
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
RAW = HERE / "raw"
LOG = HERE / "SEARCH_LOG.csv"
CANDS = HERE / "candidates.csv"
UA = {"User-Agent": "PRIOR-ART-R/1.0 (research literature review)"}

STOP = {"of", "the", "a", "an", "and", "in", "on", "for", "to", "with", "between", "through",
        "under", "via", "by"}


def http_get(url: str, timeout: int = 60) -> bytes:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def ps_get(url: str) -> bytes:
    cmd = ["powershell", "-NoProfile", "-Command",
           f"(Invoke-WebRequest -UseBasicParsing -TimeoutSec 60 -Uri '{url}').Content"]
    out = subprocess.run(cmd, capture_output=True, timeout=120)
    if out.returncode != 0:
        raise RuntimeError(out.stderr.decode("utf-8", "replace")[:300])
    return out.stdout


def log_row(row: dict) -> None:
    new = not LOG.exists()
    with LOG.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["timestamp", "database", "family", "query", "request",
                                          "status", "results_total", "records_saved", "notes"])
        if new:
            w.writeheader()
        w.writerow(row)


def openalex_abstract(inv: dict | None) -> str:
    if not inv:
        return ""
    pos = {}
    for word, idxs in inv.items():
        for i in idxs:
            pos[i] = word
    return " ".join(pos[i] for i in sorted(pos))


def q_openalex(query: str):
    url = "https://api.openalex.org/works?" + urllib.parse.urlencode(
        {"search": query, "per-page": 25})
    d = json.loads(http_get(url))
    recs = []
    for w in d.get("results", []):
        recs.append({
            "title": w.get("title") or "",
            "year": w.get("publication_year"),
            "venue": ((w.get("primary_location") or {}).get("source") or {}).get("display_name") or "",
            "doi": (w.get("doi") or "").replace("https://doi.org/", ""),
            "arxiv": "",
            "authors": "; ".join(a["author"]["display_name"] for a in w.get("authorships", [])[:6]),
            "abstract": openalex_abstract(w.get("abstract_inverted_index"))[:2000],
            "cited_by": w.get("cited_by_count"),
            "openalex": w.get("id", ""),
            "zbmath": "", "msc": "",
        })
    return url, d.get("meta", {}).get("count"), recs


def arxiv_query_string(query: str) -> str:
    parts = re.findall(r'"[^"]+"|\S+', query)
    toks = [p for p in parts if p.strip('"').lower() not in STOP]
    return " AND ".join(f"all:{t}" if t.startswith('"') else f"all:{t}" for t in toks)


def q_arxiv(query: str):
    url = "https://export.arxiv.org/api/query?" + urllib.parse.urlencode(
        {"search_query": arxiv_query_string(query), "max_results": 25})
    root = ET.fromstring(http_get(url, timeout=90))
    ns = {"a": "http://www.w3.org/2005/Atom", "o": "http://a9.com/-/spec/opensearch/1.1/"}
    total = root.findtext("o:totalResults", default="", namespaces=ns)
    recs = []
    for e in root.findall("a:entry", ns):
        aid = (e.findtext("a:id", default="", namespaces=ns) or "").rsplit("/abs/", 1)[-1]
        doi_el = e.find("{http://arxiv.org/schemas/atom}doi")
        recs.append({
            "title": " ".join((e.findtext("a:title", default="", namespaces=ns) or "").split()),
            "year": (e.findtext("a:published", default="", namespaces=ns) or "")[:4],
            "venue": "arXiv",
            "doi": doi_el.text if doi_el is not None else "",
            "arxiv": re.sub(r"v\d+$", "", aid),
            "authors": "; ".join(a.findtext("a:name", default="", namespaces=ns)
                                 for a in e.findall("a:author", ns)[:6]),
            "abstract": " ".join((e.findtext("a:summary", default="", namespaces=ns) or "").split())[:2000],
            "cited_by": "", "openalex": "", "zbmath": "", "msc": "",
        })
    return url, total, recs


def q_zbmath(query: str):
    url = "https://api.zbmath.org/v1/document/_search?" + urllib.parse.urlencode(
        {"search_string": query, "page": 0, "results_per_page": 25})
    try:
        raw = http_get(url)
        note = ""
    except urllib.error.HTTPError as e:
        if e.code == 404:  # zbMATH answers 404 "No results found" for empty result sets
            return url, 0, [], "no results (HTTP 404 from zbMATH)"
        raise
    except Exception:
        try:
            raw = ps_get(url)
        except RuntimeError as e:
            if "No results found" in str(e) or "Entry not found" in str(e):
                return url, 0, [], "no results (zbMATH 'Entry not found'; via PowerShell)"
            raise
        note = "fetched via PowerShell (certificate chain)"
    d = json.loads(raw)
    recs = []
    for r in d.get("result", []) or []:
        title = r.get("title") or {}
        src = (r.get("source") or {})
        links = r.get("links") or []
        doi = next((l.get("identifier") for l in links if l.get("type") == "doi"), "") or ""
        arx = next((l.get("identifier") for l in links if l.get("type") == "arxiv"), "") or ""
        msc = ";".join(m.get("code", "") for m in (r.get("msc") or []))
        abstract = ""
        for c in r.get("editorial_contributions") or []:
            if c.get("text"):
                abstract = c["text"]
                break
        recs.append({
            "title": title.get("title", "") if isinstance(title, dict) else str(title),
            "year": r.get("year"),
            "venue": ((src.get("series") or [{}])[0].get("title") if src.get("series") else "")
                     or "",
            "doi": doi, "arxiv": arx,
            "authors": "; ".join(a.get("name", "") for a in ((r.get("contributors") or {}).get("authors") or [])[:6]),
            "abstract": re.sub(r"\s+", " ", abstract)[:2000],
            "cited_by": "", "openalex": "", "zbmath": str(r.get("id", "")), "msc": msc,
        })
    total = (d.get("status") or {}).get("nr_total_results")
    return url, total, recs, note


def q_s2(query: str):
    url = "https://api.semanticscholar.org/graph/v1/paper/search?" + urllib.parse.urlencode(
        {"query": query, "limit": 10,
         "fields": "title,year,venue,externalIds,authors,abstract,citationCount"})
    d = json.loads(http_get(url))
    recs = []
    for p in d.get("data", []) or []:
        ext = p.get("externalIds") or {}
        recs.append({
            "title": p.get("title") or "", "year": p.get("year"), "venue": p.get("venue") or "",
            "doi": ext.get("DOI", "") or "", "arxiv": ext.get("ArXiv", "") or "",
            "authors": "; ".join(a.get("name", "") for a in (p.get("authors") or [])[:6]),
            "abstract": (p.get("abstract") or "")[:2000], "cited_by": p.get("citationCount"),
            "openalex": "", "zbmath": "", "msc": "",
        })
    return url, d.get("total"), recs


RUBRIC = [
    (r"multilinear", 3), (r"sharp|best (possible )?constant|optimal constant", 3),
    (r"projection|projector", 2), (r"\btree|hierarchical|dimension tree", 2),
    (r"worst[- ]case", 2), (r"extrem(al|izer|izers|um)", 2), (r"error (bound|estimate)", 2),
    (r"angle|friedrichs", 2), (r"truncation", 1), (r"contraction|contractive", 1),
    (r"fidelity|purified distance|bures", 1), (r"zeno", 1), (r"cos(ine)?\b", 1),
    (r"tensor", 1), (r"accumulat|amplif|propagat", 1),
]
RED_FLAG = re.compile(r"(?=.*multilinear)(?=.*projection)(?=.*(tree|hierarch))|"
                      r"(?=.*sharp)(?=.*projection)(?=.*error)", re.I | re.S)


def score(text: str) -> int:
    t = text.lower()
    return sum(wt for pat, wt in RUBRIC if re.search(pat, t))


def norm_title(t: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (t or "").lower())[:120]


def main() -> None:
    qs = json.loads((HERE / "queries.json").read_text(encoding="utf-8"))
    RAW.mkdir(exist_ok=True)
    allrecs = []
    s2_blocked = False
    arxiv_blocked = False
    for fam, spec in qs["families"].items():
        for qi, query in enumerate(spec["queries"]):
            for src in ("openalex", "arxiv", "zbmath", "semanticscholar"):
                if src == "arxiv" and arxiv_blocked:
                    log_row({"timestamp": dt.datetime.now().isoformat(timespec="seconds"),
                             "database": src, "family": fam, "query": query, "request": "",
                             "status": "SKIPPED", "results_total": "", "records_saved": 0,
                             "notes": "arXiv API rate limited (HTTP 429) earlier in this run; preprints covered via OpenAlex"})
                    continue
                if src == "semanticscholar" and s2_blocked:
                    log_row({"timestamp": dt.datetime.now().isoformat(timespec="seconds"),
                             "database": src, "family": fam, "query": query, "request": "",
                             "status": "SKIPPED", "results_total": "", "records_saved": 0,
                             "notes": "rate limited earlier in this run"})
                    continue
                note = ""
                url = ""
                try:
                    if src == "openalex":
                        url, total, recs = q_openalex(query)
                        time.sleep(1)
                    elif src == "arxiv":
                        try:
                            url, total, recs = q_arxiv(query)
                        except urllib.error.HTTPError as e:
                            if e.code in (429, 503):
                                time.sleep(30)
                                url, total, recs = q_arxiv(query)
                            else:
                                raise
                        time.sleep(4)
                    elif src == "zbmath":
                        url, total, recs, note = q_zbmath(query)
                        time.sleep(1)
                    else:
                        try:
                            url, total, recs = q_s2(query)
                        except urllib.error.HTTPError as e:
                            if e.code == 429:
                                time.sleep(15)
                                url, total, recs = q_s2(query)
                            else:
                                raise
                        time.sleep(5)
                    status = "OK"
                except Exception as e:  # logged, never silently dropped
                    total, recs, status = "", [], "ERROR"
                    note = f"{type(e).__name__}: {str(e)[:200]}"
                    if src == "semanticscholar" and "429" in note:
                        s2_blocked = True
                    if src == "arxiv" and ("429" in note or "503" in note or "timed out" in note):
                        arxiv_blocked = True
                for r in recs:
                    r.update({"source": src, "family": fam, "query": query})
                allrecs.extend(recs)
                (RAW / f"{src}_{fam}_{qi}.json").write_text(
                    json.dumps({"query": query, "url": url, "total": total, "records": recs},
                               ensure_ascii=False, indent=1), encoding="utf-8")
                log_row({"timestamp": dt.datetime.now().isoformat(timespec="seconds"),
                         "database": src, "family": fam, "query": query, "request": url,
                         "status": status, "results_total": total, "records_saved": len(recs),
                         "notes": note})
                print(f"{src:16s} {fam} {qi} {status} total={total} saved={len(recs)} {note[:60]}",
                      flush=True)
    # dedupe
    merged: dict[str, dict] = {}
    for r in allrecs:
        key = (r["doi"].lower() if r["doi"] else "") or (("arxiv:" + r["arxiv"]) if r["arxiv"] else "") \
              or norm_title(r["title"])
        if not key:
            continue
        m = merged.setdefault(key, {**r, "families": set(), "sources": set(), "queries": set()})
        m["families"].add(r["family"])
        m["sources"].add(r["source"])
        m["queries"].add(r["query"])
        for fld in ("abstract", "doi", "arxiv", "venue", "msc", "zbmath", "openalex", "authors"):
            if not m.get(fld) and r.get(fld):
                m[fld] = r[fld]
    rows = []
    for key, m in merged.items():
        text = f"{m['title']} {m['abstract']}"
        rows.append({
            "key": key, "score": score(text), "red_flag": bool(RED_FLAG.search(text)),
            "n_families": len(m["families"]), "families": ";".join(sorted(m["families"])),
            "sources": ";".join(sorted(m["sources"])), "title": m["title"], "year": m["year"],
            "authors": m["authors"], "venue": m["venue"], "doi": m["doi"], "arxiv": m["arxiv"],
            "openalex": m["openalex"], "zbmath": m["zbmath"], "msc": m["msc"],
            "cited_by": m["cited_by"], "abstract": m["abstract"],
        })
    rows.sort(key=lambda x: (-int(x["red_flag"]), -x["score"], -x["n_families"]))
    with CANDS.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"records={len(allrecs)} unique_candidates={len(rows)} red_flags={sum(r['red_flag'] for r in rows)}")


if __name__ == "__main__":
    main()
