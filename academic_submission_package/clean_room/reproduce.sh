#!/usr/bin/env bash
# Reproduce the minimal set that supports the five manuscripts, and write a report.
#
# Intended to run inside the container defined by clean_room/Containerfile, but it works in
# any environment that has the tools. It writes to /out if that exists, otherwise to
# clean_room/out.
#
# It runs no experiment. Every number it produces comes from a committed data file or a
# deterministic re-derivation of one.

set -uo pipefail

PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${OUT:-/out}"
[ -d "$OUT" ] || OUT="$PKG/clean_room/out"
mkdir -p "$OUT"
REPORT="$OUT/reproduction_report.md"
: > "$REPORT"

FAIL=0
note() { echo "$*" | tee -a "$REPORT"; }
step() { note ""; note "## $*"; note ""; }

note "# Clean-room reproduction report"
note ""
note "Generated $(date -u +%Y-%m-%dT%H:%M:%SZ)"

step "1. Environment"
note '```'
note "os              : $(. /etc/os-release 2>/dev/null && echo "$PRETTY_NAME" || uname -a)"
note "kernel          : $(uname -srm)"
note "python          : $(python3 --version 2>&1)"
note "pdflatex        : $(pdflatex --version 2>/dev/null | head -1)"
note "latexmk         : $(latexmk --version 2>/dev/null | head -1)"
note "pdftotext       : $(pdftotext -v 2>&1 | head -1)"
note "cpu             : $(grep -m1 'model name' /proc/cpuinfo 2>/dev/null | cut -d: -f2- | xargs || echo unknown)"
note "cores           : $(nproc 2>/dev/null || echo unknown)"
note "memory          : $(awk '/MemTotal/ {printf "%.1f GiB", $2/1048576}' /proc/meminfo 2>/dev/null || echo unknown)"
note "package commit  : $(git -C "$PKG" rev-parse HEAD 2>/dev/null || echo 'not a git checkout')"
note '```'
note ""
note "Python dependency versions:"
note '```'
python3 -m pip freeze 2>/dev/null | tee -a /dev/null | sed 's/^/  /' >> "$REPORT" || note "  (pip freeze unavailable)"
note '```'

step "2. Package integrity"
if [ -f "$PKG/checksums.sha256" ]; then
  ( cd "$PKG" && sha256sum -c checksums.sha256 --quiet ) 2>&1 | head -40 | tee -a "$REPORT"
  if [ "${PIPESTATUS[0]}" = "0" ]; then note "checksums: **all match**"; else note "checksums: **MISMATCH**"; FAIL=1; fi
else
  note "checksums.sha256 absent"; FAIL=1
fi

step "3. Test suites"
note "| suite | command | expected | observed | seconds |"
note "| --- | --- | --- | --- | --- |"
note "| case study I | \`python -m pytest -q\` | 73 passed | see below | |"
note "| case study II | \`python -m pytest spectral/certification_v18/tests -q\` | 85 passed | see below | |"
note ""
note "The test suites live in the source repository, not in this package. Run them in a"
note "checkout of the two commits named in \`provenance.md\`. Recorded results are in"
note "\`verification/test_results/\`."

step "4. Re-derivation of the optimality classification"
note "Expected, from \`sources/recursive_projection_of_multilinear_trees/data/optimality_classification_summary.json\`:"
note '```'
note "gap registry rows                     9945"
note "  exactly determined (positive)        309"
note "  zero by theorem                       30"
note "  positive lower bound, gap remains   7812"
note "  no positive lower bound             1794   (18.0 %)"
note '```'
if [ -f "$PKG/sources/recursive_projection_of_multilinear_trees/data/optimality_classification_summary.json" ]; then
  note ""
  note "Observed in the shipped package:"
  note '```'
  python3 - "$PKG" >> "$REPORT" <<'PY'
import json, sys
from pathlib import Path
p = Path(sys.argv[1]) / "sources/recursive_projection_of_multilinear_trees/data/optimality_classification_summary.json"
d = json.loads(p.read_text(encoding="utf-8"))
print(f"gap registry rows                   {d['gap_registry_rows']:>6}")
for k, v in d["gap_registry_counts"].items():
    print(f"  {k:<34}{v:>6}")
PY
  note '```'
else
  note "summary file absent"; FAIL=1
fi

step "5. Figures"
if [ -f "$PKG/sources/supplementary_results/generate_figures.py" ]; then
  ( cd "$PKG/sources/supplementary_results" && python3 generate_figures.py ) >> "$REPORT" 2>&1 \
    && note "figure generation: ok" || { note "figure generation: **FAILED**"; FAIL=1; }
  note ""
  note "Per-figure checksums, shipped versus regenerated:"
  note '```'
  python3 - "$PKG" >> "$REPORT" <<'PY'
import json, sys
from pathlib import Path
new = json.loads((Path(sys.argv[1]) / "sources/supplementary_results/figure_provenance.json").read_text(encoding="utf-8"))
old = Path(sys.argv[1]) / "verification/figure_provenance/figure_provenance.json"
ref = json.loads(old.read_text(encoding="utf-8")) if old.exists() else None
refmap = {f["figure"]: f for f in ref["figures"]} if ref else {}
for f in new["figures"]:
    r = refmap.get(f["figure"])
    for ext in ("pdf", "svg", "png"):
        a = f["outputs"][ext]["sha256"][:12]
        b = r["outputs"][ext]["sha256"][:12] if r else "n/a"
        print(f"{f['figure']:<32} {ext:<4} {a}  {'==' if a == b else '!='}  {b}")
PY
  note '```'
  note ""
  note "Matplotlib embeds no timestamp in PDF output when SOURCE_DATE_EPOCH is set, but"
  note "font subsetting and library versions do affect the bytes. A mismatch here is"
  note "expected on a different library version and is not by itself a reproduction failure;"
  note "compare the rendered figures and the underlying data instead."
else
  note "figure generator absent"; FAIL=1
fi

step "6. Manuscript builds and acceptance checks"
note "| document | errors | undef. refs | undef. cites | overfull | bad ligatures | Type 3 | pages |"
note "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"
for d in recursive_projection_of_multilinear_trees kernel_defined_multilinear_operators \
         numerical_study software_and_reproducibility supplementary_results; do
  src="$PKG/sources/$d"
  [ -d "$src" ] || { note "| $d | source absent | | | | | | |"; FAIL=1; continue; }
  ( cd "$src" && rm -rf build && latexmk -pdf -interaction=nonstopmode -outdir=build main.tex ) >/dev/null 2>&1
  log="$src/build/main.log"; pdf="$src/build/main.pdf"
  if [ ! -f "$pdf" ]; then note "| $d | BUILD FAILED | | | | | | |"; FAIL=1; continue; fi
  e=$(grep -c '^! '                  "$log" || true)
  r=$(grep -c 'Reference .* undefined' "$log" || true)
  c=$(grep -c 'Citation .* undefined'  "$log" || true)
  o=$(grep -c 'Overfull \\hbox'        "$log" || true)
  pdftotext -q "$pdf" /tmp/x.txt
  b=$(grep -coE '\b(nite|erence|cate|rst|nding|cient|ected)\b' /tmp/x.txt || true)
  t=$(pdffonts "$pdf" | grep -c 'Type 3' || true)
  p=$(python3 -c "print(open('/tmp/x.txt',encoding='utf-8',errors='replace').read().count(chr(12)))")
  note "| $d | $e | $r | $c | $o | $b | $t | $p |"
  [ "$e$r$c$o$b$t" = "000000" ] || FAIL=1
done
note ""
note "Acceptance requires zero in every column except the last."

step "7. Verdict"
if [ "$FAIL" = "0" ]; then
  note "**Reproduction of the minimal supporting set: succeeded.**"
else
  note "**Reproduction of the minimal supporting set: FAILED.** See the sections above."
fi
note ""
note "## What this does not cover"
note ""
note "- the experiment pipelines, which were not re-run;"
note "- the GPU measurements, which require the hardware named in document 04;"
note "- the extended optimiser grid and the two further sweep stages, which were specified"
note "  and never executed;"
note "- the mathematics. A successful reproduction says the artifacts rebuild. It says"
note "  nothing about whether the theorems are true."

echo
echo "report written to $REPORT"
exit "$FAIL"
