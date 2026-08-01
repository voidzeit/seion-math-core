#!/usr/bin/env bash
# Rebuild every deliverable of this package from its sources.
#
# Requirements: a TeX distribution providing latexmk, pdflatex, bibtex and the packages
# named in each preamble; Python 3.12 with numpy, pandas, pyarrow and matplotlib;
# pdftotext and pdffonts (poppler) for the PDF verification step.
#
# The script is deterministic and idempotent: running it twice produces the same output.
# It does not run any experiment. Every number in the manuscripts comes either from a
# committed data file or from a re-derivation of a committed data file, and this script
# performs those re-derivations but no new computation.
#
# Usage:  bash rebuild_all.sh  [from the package root]

set -euo pipefail

PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$PKG/.." && pwd)"
SRC="$PKG/sources"
PAPERS="$PKG/papers"
VERIF="$PKG/verification"

echo "== package root: $PKG"
mkdir -p "$PAPERS" "$VERIF/build_logs" "$VERIF/test_results" "$VERIF/rendered_pages"

# ---------------------------------------------------------------------------
# 1. Re-derive the optimality classification from the recorded certified bounds.
#    This is a pure function of data already on disk; no experiment is re-run.
# ---------------------------------------------------------------------------
echo "== re-deriving the optimality classification"
python "$REPO/scripts/regenerate_optimality_classification.py"

# ---------------------------------------------------------------------------
# 2. Replace implementation vocabulary in the generated tables.
#    Headings and labels only; numeric values are never touched. Fails if any
#    forbidden token survives.
# ---------------------------------------------------------------------------
echo "== rewriting generated table vocabulary"
python "$REPO/scripts/sanitize_generated_tables.py"

# ---------------------------------------------------------------------------
# 3. Regenerate every supplementary figure, in PDF, SVG and PNG, with a manifest.
# ---------------------------------------------------------------------------
echo "== regenerating figures"
( cd "$SRC/supplementary_results" && python generate_figures.py )
cp "$SRC/supplementary_results/figure_provenance.json" "$VERIF/figure_provenance/"

# ---------------------------------------------------------------------------
# 4. Build each manuscript from a clean directory and check the log.
# ---------------------------------------------------------------------------
build_one() {
  local dir="$1" out="$2"
  echo "== building $dir"
  ( cd "$SRC/$dir" \
    && rm -rf build \
    && latexmk -pdf -interaction=nonstopmode -outdir=build main.tex >/dev/null )

  local log="$SRC/$dir/build/main.log"
  cp "$log" "$VERIF/build_logs/$out.log"

  local refs cites over errs
  refs=$(grep -c 'Reference .* undefined' "$log" || true)
  cites=$(grep -c 'Citation .* undefined' "$log" || true)
  over=$(grep -c 'Overfull \\hbox' "$log" || true)
  errs=$(grep -c '^! ' "$log" || true)
  echo "   undefined refs=$refs  undefined cites=$cites  overfull=$over  errors=$errs"
  if [ "$refs" != "0" ] || [ "$cites" != "0" ] || [ "$over" != "0" ] || [ "$errs" != "0" ]; then
    echo "   FAILED acceptance criteria" >&2
    return 1
  fi

  cp "$SRC/$dir/build/main.pdf" "$PAPERS/$out.pdf"

  # Text extraction must recover ligatures. A nonzero count here means the text
  # fonts were embedded as Type 3 bitmaps and the PDF is not searchable.
  pdftotext -q "$PAPERS/$out.pdf" "$VERIF/rendered_pages/$out.txt"
  local bad
  bad=$(grep -coE '\b(nite|erence|cate|rst|nding|cient|ected)\b' \
        "$VERIF/rendered_pages/$out.txt" || true)
  local t3
  t3=$(pdffonts "$PAPERS/$out.pdf" | grep -c 'Type 3' || true)
  echo "   corrupted ligature stems=$bad  Type 3 fonts=$t3"
  if [ "$bad" != "0" ] || [ "$t3" != "0" ]; then
    echo "   FAILED PDF text-extraction criteria" >&2
    return 1
  fi
}

build_one recursive_projection_of_multilinear_trees 01_recursive_projection_of_multilinear_trees
build_one kernel_defined_multilinear_operators      02_kernel_defined_multilinear_operators
build_one numerical_study                           03_numerical_study_of_projected_multilinear_models
build_one software_and_reproducibility              04_software_and_reproducibility
build_one supplementary_results                     05_supplementary_numerical_results

# ---------------------------------------------------------------------------
# 5. Tests. Passing tests establish implementation consistency only.
# ---------------------------------------------------------------------------
echo "== running the test suite for case study I"
( cd "$REPO" && python -m pytest -q ) | tee "$VERIF/test_results/case_study_I.txt"

echo "== case study II tests require a checkout of the branch that carries them;"
echo "   see provenance.md. The recorded result is in verification/test_results/."

# ---------------------------------------------------------------------------
# 6. Checksums.
# ---------------------------------------------------------------------------
echo "== writing checksums"
( cd "$PKG" && find papers sources verification -type f \
    ! -path '*/build/*' -print0 | sort -z | xargs -0 sha256sum ) > "$PKG/checksums.sha256"

echo
echo "== done. PDFs are in papers/, logs and extraction checks in verification/."
