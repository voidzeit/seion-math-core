"""Build bibliography/references.bib from PRIOR_ART_MATRIX.csv using Crossref canonical metadata.

Only rows with `cite_in_paper == yes` are included. For rows with a DOI, BibTeX comes from Crossref
content negotiation, then is cleaned (no url/abstract/keywords/file/month fields; consistent keys).
Rows without a DOI are emitted from the matrix fields and flagged `% NO_DOI` for manual MR Lookup.

Run:  python research/pmt_program/prior_art/build_bib.py
"""
from __future__ import annotations

import csv
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "bibliography" / "references.bib"
DROP = {"url", "abstract", "keywords", "file", "month", "publisher_url", "ISSN", "issn"}


def crossref_bibtex(doi: str) -> str:
    url = "https://api.crossref.org/works/" + urllib.parse.quote(doi, safe="/") + \
          "/transform/application/x-bibtex"
    req = urllib.request.Request(url, headers={"User-Agent": "PRIOR-ART-R/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8")


def clean(entry: str, key: str) -> str:
    m = re.match(r"\s*@(\w+)\{[^,]*,(.*)\}\s*$", entry, re.S)
    if not m:
        return entry
    etype, body = m.group(1).lower(), m.group(2)
    fields = re.findall(r"(\w+)\s*=\s*(\{(?:[^{}]|\{[^{}]*\})*\}|\"[^\"]*\"|\d+)", body)
    keep = [(k.lower(), v) for k, v in fields if k.lower() not in DROP]
    lines = [f"@{etype}{{{key},"] + [f"  {k:<8} = {v}," for k, v in keep] + ["}"]
    return "\n".join(lines)


def main() -> None:
    rows = list(csv.DictReader((HERE / "PRIOR_ART_MATRIX.csv").open(encoding="utf-8")))
    OUT.parent.mkdir(exist_ok=True)
    entries = []
    for r in rows:
        if (r.get("cite_in_paper") or "").strip().lower() != "yes":
            continue
        key = r["citation_key"].strip()
        doi = (r.get("doi") or "").strip()
        if doi:
            try:
                entries.append(f"% class: {r.get('bib_class','')} | threat {r.get('threat_final','')}\n"
                               + clean(crossref_bibtex(doi), key))
            except Exception as e:
                entries.append(f"% CROSSREF_ERROR {doi}: {type(e).__name__}\n@misc{{{key},\n"
                               f"  title = {{{r['title']}}},\n  year = {{{r['year']}}},\n}}")
            time.sleep(1)
        else:
            ident = f"arXiv:{r['arxiv']}" if r.get("arxiv") else ""
            entries.append(f"% NO_DOI — verify with MR Lookup\n@misc{{{key},\n"
                           f"  author = {{{r['authors'].replace('; ', ' and ')}}},\n"
                           f"  title  = {{{r['title']}}},\n  year   = {{{r['year']}}},\n"
                           f"  note   = {{{ident}}},\n}}")
    OUT.write_text("\n\n".join(entries) + "\n", encoding="utf-8")
    print(f"wrote {len(entries)} entries to {OUT}")


if __name__ == "__main__":
    main()
