# Provenance

- Source repository: `seion-math-core` (local; GitHub `voidzeit/seion-math-core`).
- Built from branch `integration/full-math-ai-package-v2` at commit `ee198a85a4bcdc142fc7aed8dc5c9d019c3a7daf`.
- This commit is itself the result of a non-fast-forward merge of four
  branches into `main` (see `integration_audit/MERGE_LEDGER.md` in this
  package) plus this session's own math-closure (M1-M7), AI-benchmark,
  clean-room, and manuscript work, each as a separate, individually
  reviewable commit — full `git log` available in the source repository.
- Package built: 2026-08-01 (UTC), same session as the commit above.
- Predecessor package: `academic_submission_package/` (untracked path
  name, no version suffix) remains unchanged in the source repository
  except for the specific paper 01/04/06 updates this session made
  directly to it (see git history) — this package is a superset
  snapshot, not a fork.
- Hardware used to produce this session's new numerical results: RTX
  PRO 5000 Blackwell (24GB VRAM, present but not required for any result
  in this package — all math-closure and Level 1-3 AI benchmarks ran on
  CPU), 24 logical CPUs, 128GB RAM, Windows 11.
- Software versions: Python 3.12.10, sympy 1.14.0, numpy (see
  `clean_room/reproduction_run/environment.json` for the exact clean-room
  container's `pip freeze`), MiKTeX 26.5 (pdfTeX 4.27) for manuscript
  builds, Docker Desktop 4.73.0 for the clean-room container.
