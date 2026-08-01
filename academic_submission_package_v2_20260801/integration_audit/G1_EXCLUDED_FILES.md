# G1 — Files intentionally left untracked/uncommitted

Verified as stale, incomplete residue in the main working tree — NOT committed.
Real, complete versions of this content exist on `research/spectral-a-to-n-v18`
(commit `8e09941`) and will enter `main` via the G3 branch merge instead.

## papers/a_to_n_certification_v18/, papers/software_reproducibility_v5/, papers/supplementary_visual_atlas_v18/
Contain only a compiled PDF + LaTeX aux/log files. No `.tex` source present
(verified: `ls papers/a_to_n_certification_v18/*.tex` -> No such file or directory).
Committing these would ship an unrebuildable PDF with no provenance.

## spectral/
536 files, but the `certification_v18/tests/` and `certification_v18/blocks/`
directories contain 0 real `.py` source files here — only `__pycache__/*.pyc`
compiled cache. The real branch worktree (`%TEMP%\swt`, detached at `8e09941`)
has 23 test source files and 16 block source files in the same paths. This
untracked copy is leftover bytecode cache from a session that ran the suite
without ever writing/tracking the sources into this working tree.

## Not excluded, no issue found
No secrets, credentials, private tokens, or absolute private paths found in
any candidate content (grep scan across academic_delivery_work/,
academic_submission_package/, docs/research/truth_audit_2026_07_29/, the two
new scripts, and the four modified scripts) — one benign match for the word
"secret" in prose (`gitleaks secret scanning`), not an actual secret.
