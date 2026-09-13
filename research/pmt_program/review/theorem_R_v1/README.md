# Theorem R — review version v1 (frozen)

Minimal package for independent review of the claim that, in the real class
PMT-A, the sharp projected-error constant of a projected multilinear tree
depends only on its number of internal vertices:
`C^P_T(η) = max_{θ ≤ arcsin η} |1 − (cos θ e^{iθ})^{k−1}| / η`.

Status: `ADVISORY_PROOF_DRAFT`. Author-side audit only. Do not edit these files;
corrections go to `theorem_R_v2/`.

| file | read |
|---|---|
| `REVIEW_PACKAGE_v1.md` | **the proof**, self-contained: class, Theorem U, Lemmas A–G, Theorem R |
| `TENSOR_ANGLE_INEQUALITY_v1.md` | Theorem T standalone, with sharpness |
| `AUDIT_v1.md` | hostile author-side audit: the four danger points, edge-case checklist, open limits |
| `THEOREM_R_DRAFT_v1.md` | verbatim copy of the source draft (`f80f4e8`) |
| `edge_cases.py`, `outputs/edge_cases.json` | numerical edge-case control (needs `numpy` and `research/pmt_program/lemma3/states.py`) |
| `FREEZE_v1.json` | base commit and SHA-256 of every frozen file |
