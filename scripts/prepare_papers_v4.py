"""Create the v4 paper/companion/supplement source trees from registered v3 artifacts."""
from __future__ import annotations

import shutil
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def clone(src: str, dst: str) -> None:
    source, target = ROOT / src, ROOT / dst
    target.mkdir(parents=True, exist_ok=True)
    for item in source.iterdir():
        if item.name == "build":
            continue
        dest = target / item.name
        if item.is_dir():
            shutil.copytree(item, dest, dirs_exist_ok=True)
        else:
            shutil.copy2(item, dest)


def main() -> int:
    clone("papers/tree_stability_v3", "papers/tree_stability_v4")
    clone("papers/software_v3", "papers/software_v4")
    main = ROOT / "papers/tree_stability_v4/main.tex"
    text = main.read_text(encoding="utf-8")
    text = text.replace("Nodewise Error Certificates for\nRecursively Projected", "Structure-Preserving Reduction of Finite-Dimensional\nN-Ary Laws: Nodewise Error Certificates for\nRecursively Projected", 1)
    text = text.replace("\\title[Nodewise tree error certificates]", "\\title[Structure-preserving reduction of finite-dimensional N-ary laws]", 1)
    text = re.sub(r"\\title\[.*?\]\{.*?\}\n\\author", r"\\title[Structure-preserving reduction of finite-dimensional N-ary laws]{Structure-Preserving Reduction of Finite-Dimensional N-Ary Laws: Exact Functoriality, Associator Stability, and Projection Error Bounds}\n\\author", text, count=1, flags=re.S)
    text = text.replace("\\date{29 July 2026}", "\\date{29 July 2026 -- v4 canonical research draft}")
    text = text.replace("\\end{document}", """\\section{v4 theorem program and epistemic boundary}
The canonical v4 repository separates a proved exact-invariance path from the unresolved approximate program. For an isometry \\(Q:W\\hookrightarrow V\\), \\(P=QQ^\\ast\\), and an exactly invariant multilinear law, the definition \\(\\bar\\mu=Q^\\ast\\mu(Q\\cdot,\\ldots,Q\\cdot)\\) commutes with declared partial compositions by direct substitution; consequently every implemented multilinear polynomial identity descends. The repository records this as a conditional theorem candidate and requires an independent proof audit before a `PROVED` transition.

Approximate closure, spectral snapping, sharpness extremizers, cancellation-aware FI/GJI/Jacobiator constants, and theorem-level novelty are not declared complete in this release. Numerical certificates test finite-dimensional formulas but cannot replace their proofs. The exact status and blockers are in `claims/`, `docs/research/`, and `artifacts/release\\_v4/`.
\\end{document}""", 1)
    main.write_text(text, encoding="utf-8")
    companion = ROOT / "papers/software_v4/main.tex"
    ctext = companion.read_text(encoding="utf-8")
    ctext = ctext.replace("SEION Math Core v3:", "SEION Math Core v4:")
    ctext = ctext.replace("pdftitle={SEION Math Core v3:", "pdftitle={SEION Math Core v4:")
    ctext = ctext.replace("\\date{29 July 2026}", "\\date{29 July 2026 -- v4 canonical software companion}")
    companion.write_text(ctext, encoding="utf-8")
    supp = ROOT / "papers/supplement_v4/main.tex"
    supp.parent.mkdir(parents=True, exist_ok=True)
    supp.write_text(r"""\documentclass[10pt]{article}
\usepackage[margin=1in]{geometry}
\usepackage{amsmath,amssymb,booktabs,graphicx,hyperref,xcolor}
\title{SEION Math Core v4 Supplementary Atlas}
\author{Eliuth Chavero Jasso\\Independent Researcher, Apizaco, Tlaxcala, Mexico}
\date{29 July 2026}
\begin{document}\maketitle
\begin{abstract}This atlas records the finite-dimensional evidence, artifact contracts, negative controls, and reproducibility boundaries associated with the canonical SEION Math Core v4 research draft. It is a companion record, not an independent proof of universal or continuum statements.\end{abstract}
\section{Scope and authority}
The mathematical paper separates definitions, conditional results, observed numerical residuals, and unresolved claims. The authority ladder is recorded in \texttt{governance/AUTHORITY\_LADDER.yaml}; the machine graph and source hashes are in \texttt{.ai/machine}.
\section{Canonical artifact map}
\begin{center}\begin{tabular}{ll}\toprule
Artifact family & Authority\\\midrule
Theorem/proof & theorem registry and proof source\\
Executed result & run manifest, metrics, certificate, hashes\\
Experiment design & registered experiment matrix\\
Figure/table & generated output with provenance\\
Release status & independent gate report and human decisions\\\bottomrule
\end{tabular}\end{center}
\section{Required controls}
The registry distinguishes known invariant projectors, random projectors, PCA/SVD, spectral projectors, and closure-minimizing projectors. Exact dense laws and CP rank sweeps are controls; negative spectral-gap controls remain mandatory. Repeated executions are deduplicated by scientific-instance identity and are not counted as independent experiments.
\section{Mathematical blockers}
The v4 program does not silently promote the current tree-level certificates to a universal theorem. Sharpness extremizers, a complete prior-art novelty audit, cancellation-aware FI/GJI/Jacobiator constants, and a full extended optimizer grid remain explicit blockers until independently completed.
\section{Reproducibility manifest}
\begin{verbatim}
python -m pytest -q
python scripts/build_v4_foundation.py
python scripts/seion_campaign_v4.ps1
\end{verbatim}
    The last command is a PowerShell orchestrator; all stages report status and preserve failed evidence.
\section{Selected figures}
Figures are generated from registered v3 runs and copied into the v4 paper tree. Their captions state the metric, seed count, baseline, and limitation. No categorical dtype progression is treated as a continuous variable.
\section{Reviewer checklist}
\begin{itemize}
\item Claims map to theorem, experiment, counterexample, or blocker records.
\item No numerical residual upgrades a claim to \texttt{PROVED}.
\item Tables obey lower/upper and operator/Frobenius metric invariants.
\item PDF and source checksums are emitted by the release script.
\item Human review remains a required external decision.
\end{itemize}
\end{document}
""", encoding="utf-8")
    (ROOT / "papers/tree_stability_v4/README.md").write_text("# Canonical mathematical paper v4\n\nDerived from registered finite-dimensional v3 artifacts by `scripts/prepare_papers_v4.py`. Mathematical novelty and unresolved blockers are recorded in `docs/research/` and `artifacts/release_v4/`.\n", encoding="utf-8")
    (ROOT / "papers/software_v4/README.md").write_text("# SEION Math Core software companion v4\n\nThis companion documents repository architecture, typed governance, artifact contracts, run indexes, reproducibility commands, and release gates. It is not a mathematical novelty claim.\n", encoding="utf-8")
    print("prepared papers/tree_stability_v4, papers/software_v4, papers/supplement_v4")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
