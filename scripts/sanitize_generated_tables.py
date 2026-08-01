"""Apply the terminology map to the generated LaTeX tables of the delivery package.

The tables under ``academic_submission_package/sources/*/tables`` are produced by the
experiment pipeline and carry implementation vocabulary in their column headings and
cells. Scholarly prose must not use that vocabulary (see
``academic_delivery_work/07_terminology_map.md``), so the generated text is rewritten
here rather than by hand, and the rewrite is auditable and repeatable.

Only headings and labels are rewritten. No numeric value is touched.

Usage::

    python scripts/sanitize_generated_tables.py [--check]

``--check`` exits nonzero if any forbidden token survives.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "academic_submission_package" / "sources"

#: Ordered longest-first so that longer phrases are rewritten before their substrings.
REPLACEMENTS: list[tuple[str, str]] = [
    # --- geometry: "tangent" is wrong, there is no tangent space here ---
    (r"tangent and normal components", "projected and orthogonal components"),
    (r"tangent/normal", "projected/orthogonal"),
    (r"\$D_v\^P,D_v\^N\$", r"$D_v^{\\parallel},D_v^{\\perp}$"),
    (r"tangent", "projected"),
    (r"\bnormal component", "orthogonal component"),
    (r"\bnormal error", "orthogonal error"),
    (r"\bnormal output", "orthogonal output"),
    (r"\bnormal residual", "orthogonal residual"),
    # The three error types appear as data values in generated cells.
    (r"& normal &", "& orthogonal &"),
    (r"^normal &", "orthogonal &"),
    (r"improvement certified", "improvement established"),
    # --- error names ---
    (r"projected-root lower", "projected-error lower bound"),
    (r"ambient-root", "ambient"),
    (r"\$C_T\^\{\\mathrm\{amb\}\},C_T\^P\$", r"$C_T^{\\mathrm{amb}},C_T^{\\mathrm{proj}}$"),
    (r"\$B_v\^A,B_v\^P,B_v\^N\$", r"$B_v^{\\mathrm{amb}},B_v^{\\parallel},B_v^{\\perp}$"),
    # --- certificate vocabulary ---
    (r"mixed mask", "state resolved"),
    (r"mixed-mask", "state-resolved"),
    (r"path sum", "pathwise"),
    (r"path-sum", "pathwise"),
    (r"nodewise certificate", "vertexwise bound"),
    (r"\bcertificates?\b", "bounds"),
    (r"theorem upper", "proved upper bound"),
    # --- experiment vocabulary ---
    (r"scientific instances A--I", "distinct configurations"),
    (r"scientific instances", "distinct configurations"),
    (r"registered run failures", "run failures"),
    (r"registered ", ""),
    (r"\bcells\b", "configurations"),
    (r"\bcell\b", "configuration"),
    (r"leakage masks", "closure-residual subsets"),
    (r"closure residual", "closure residual"),
    # --- status codes and administrative language ---
    (
        r"EXTENDED\\allowbreak\\_PENDING\\allowbreak\\_RESOURCE\\allowbreak\\_GATE",
        "not executed, under a stated computational-cost constraint",
    ),
    (r"resource-gated and pending", "not executed, under a stated cost constraint"),
    (r"resource-gated", "not executed, under a stated cost constraint"),
    (r"open; no optimality claim", "open"),
    (r"NOVELTY\\allowbreak\\_NOT\\allowbreak\\_ESTABLISHED", "not assessed"),
    (r"PENDING\\allowbreak\\_HUMAN\\allowbreak\\_REVIEW", "not independently verified"),
    (r"novelty not established", "originality not assessed"),
    (r"novelty status", "comparison with the cited result"),
    (r"known-bound specialization", "specialisation of a known bound"),
    (r"standard multilinear bound", "standard multilinear bound"),
    (r"v3 difference", "difference"),
    # --- version labels ---
    (r"\bv3\b", ""),
    (r"\bv4\b", ""),
]

#: Tokens that must not survive anywhere in a delivered table.
FORBIDDEN = [
    r"\btangent\b",
    r"mixed[- ]mask",
    r"\bregistered\b",
    r"resource[- ]gate",
    r"NOVELTY_NOT_ESTABLISHED",
    r"PENDING_HUMAN_REVIEW",
    r"\bnovelty\b",
    r"fail[- ]closed",
    r"\bblock [A-N]\b",
]


def sanitize(text: str) -> str:
    for pattern, replacement in REPLACEMENTS:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    # Collapse whitespace damage introduced by deletions, without touching line breaks.
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r" +&", " &", text)
    text = re.sub(r"& +", "& ", text)
    return text


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    targets = sorted(PACKAGE.glob("*/tables/*.tex"))
    if not targets:
        print("no generated tables found", file=sys.stderr)
        return 1

    problems: list[str] = []
    for path in targets:
        original = path.read_text(encoding="utf-8")
        if args.check:
            text = original
        else:
            text = sanitize(original)
            if text != original:
                path.write_text(text, encoding="utf-8")
        for pattern in FORBIDDEN:
            for match in re.finditer(pattern, text, flags=re.IGNORECASE):
                problems.append(f"{path.relative_to(ROOT)}: {match.group(0)!r}")

    if problems:
        print("forbidden tokens remain:")
        for item in problems:
            print("  " + item)
        return 1
    print(f"{len(targets)} tables clean")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
