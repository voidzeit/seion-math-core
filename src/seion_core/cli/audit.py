from __future__ import annotations

from pathlib import Path

from ..certification.claims import claims_lint
from ..certification.report import write_claims_report


def audit(repo_root: str | Path) -> dict:
    root = Path(repo_root)
    result = claims_lint(root)
    write_claims_report(root)
    return result

