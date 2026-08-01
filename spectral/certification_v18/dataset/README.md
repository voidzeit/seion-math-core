# A-N track dataset (SEION V5 Phase 10)

Scope: `SPECTRAL_LEGACY_TRACK` only (`research/spectral-a-to-n-v18`). This
is **not** a cross-track "immutable dataset" spanning Track T and
CANONICAL_FINITE_CORE as well — those tracks live on separate,
as-yet-unmerged branches (`research/projected-tree-theory-v5`,
`program/seion-canonical-repository-v4`), and building one combined
dataset directory that references files across branches would either
duplicate content or contain dangling paths until a merge is explicitly
authorized. Each track's dataset lives on its own branch for now; a true
cross-track integration is release/`seion-integrated-v5`'s job, once a
merge decision is made (a human call, not this document's).

## Structure

```
dataset/
  manifests/        figure_index.json — index of every generated figure + its manifest
  scientific_instances/   (reserved; populated as Phase 4 stages complete)
  screening/         pointers to eval_mode=screening run data (pilot_sweep/, phase4_s1_broad_screening/)
  certification/     (empty — no certification-tier run has been executed in this campaign)
  exact/             (empty — I/L are the only EXACT_CERTIFICATE-tier blocks; see block findings)
  interval/          (empty — no interval-arithmetic certification run yet for A-N; cf. Track T's atlas)
  statistical/        Block G's 2000-sample distribution (STATISTICALLY_VALIDATED_PASS)
  counterexamples/    Block D's gap-closing counterexample (eps=1.2)
  failures/          pilot_failures.jsonl, s1_failures.jsonl (both empty this campaign — 0 real failures)
  figures/           PNG (300dpi) + SVG per figure
  tables/            source JSON/CSV backing each figure, machine-readable
  hashes/            one sha256 manifest per figure, tying png+svg+source together
```

## What is real here, and what is not yet built

Real, generated from actual computed data (not fabricated):
- `figures/21_gate_status_overview.*` — the 8 A-N critical gates' computed
  typed status, straight from `final_gate_evaluation.py`.
- `figures/22_block_status_summary.*` — all 14 blocks' typed status, same
  source.
- `figures/25_s1_gpu_cpu_crossover.*` (once the Phase 4 S1 sweep
  completes) — real wall-time data across n in {12,24,48,96}.

Not yet built: the mission's full ~25-30-figure atlas list (per-block
ablation landscapes, closure adversarial maxima distributions, precision
sensitivity, sweep coverage maps, etc.) requires either data this
campaign doesn't yet have (e.g. a certification-tier rerun) or
substantially more figure-generation work than this pass produced. This
directory is a real, honest start — a skeleton with real content in it —
not a complete atlas.

## Reproducing

```
python -m spectral.certification_v18.dataset.generate_atlas_figures
```

Idempotent: re-running regenerates every figure from the same source
data and overwrites the hash manifests (the manifests record what the
figures currently contain, not what they contained historically — for
a historical record, the git commit each figure was added in is the
provenance record).
