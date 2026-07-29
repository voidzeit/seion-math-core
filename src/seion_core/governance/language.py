"""Conservative paper-language checks for epistemic overclaiming."""

from __future__ import annotations

import re
from pathlib import Path

from .models import GovernanceIssue


PROOF_VERBS = re.compile(r"\b(?:we prove|this proves|we establish|therefore this establishes)\b", re.I)
NUMERICAL_MARKERS = re.compile(r"\b(?:numerical|empirical|sampled|experiment|finite evidence|illustrative|observed)\b", re.I)


def lint_paper_language(repo_root: str | Path) -> list[GovernanceIssue]:
    root = Path(repo_root).resolve()
    issues: list[GovernanceIssue] = []
    sections = root / "paper" / "sections"
    if not sections.exists():
        return issues
    for path in sorted(sections.glob("*.tex")):
        text = path.read_text(encoding="utf-8", errors="replace")
        for paragraph in re.split(r"\n\s*\n", text):
            if PROOF_VERBS.search(paragraph) and NUMERICAL_MARKERS.search(paragraph):
                issues.append(
                    GovernanceIssue(
                        "warning",
                        "paper_language_needs_review",
                        "paragraph combines proof language with numerical/empirical markers; inspect claim status",
                        (path.relative_to(root).as_posix(),),
                    )
                )
    return issues
