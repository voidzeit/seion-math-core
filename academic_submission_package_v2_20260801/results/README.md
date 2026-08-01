# results/ — cross-cutting consolidation

Per-paper figures, tables, and raw data are not duplicated here — they
live under `sources/<paper>/{figures,tables,data}/` alongside the .tex
source that generates/references them, to keep provenance unambiguous
(one location per artifact, not two copies that could silently drift
apart). This directory holds only the cross-cutting registries that
several papers/certificates draw from:

- `constants_atlas_v3.csv` — the 7,065-row k=2/k=3 sharpness atlas.
- `level1_raw.json` / `level2_raw.json` / `level3_raw.json` — the AI
  benchmark's raw per-trial records (1,440 + 150 + 180).
- `level1_analysis.json` — the Level 1 statistical analysis.
- `math_closure_status_registry.yaml` — the M1-M7 terminal-status registry.
