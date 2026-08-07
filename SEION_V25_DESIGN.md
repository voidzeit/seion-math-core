# SEION Train v25

## Purpose

`seion_train_v25.py` is a clean KGE trainer intended to replace the scientific role of the legacy v20 path without inheriting its evaluator, FI-gradient, ablation, and provenance problems.

## Architecture

The model exposes four explicit modes:

- `bilinear`: independent baseline.
- `fixed`: fixed structural-kernel SEION star.
- `cp`: learned CP-Star generator.
- `hybrid`: calibrated three-way mixture.

The hybrid score is

\[
s(h,r,t)=\sum_{j\in\{f,cp,b\}}g_j(r)\,[a_j s_j(h,r,t)+b_j],
\]

where branch scales and biases are learned separately, and the relation gate can be global or relation-specific.

The CP generator is

\[
F_r(h)=s\,O\,\operatorname{Norm}[(Ah)\odot(Br)\odot(Cc_r)]+\rho h.
\]

## Correctness gates

The built-in `--self_test` checks:

1. positive score equals the gold score through both head and tail candidate paths;
2. blocked filtered evaluation equals full-candidate evaluation;
3. FI has non-zero gradient with respect to trainable embeddings and CP factors.

## Run contract

Every run writes:

- `config.json`
- `command.txt`
- `environment.json`
- `hardware.json`
- `dataset_manifest.json`
- `kernel_manifest.json`
- `git_manifest.json`
- `source_manifest.json`
- an exact `source_snapshot_seion_train_v25.py`
- `metrics.jsonl`
- `best.pt`
- `last.pt`
- `final_metrics.json`
- `run_manifest.json`

## Recommended scientific sequence

1. `bilinear`, seeds 42/43/44.
2. `hybrid`, same seeds, geometry penalties off.
3. `cp`, same seeds.
4. `geometry`, only after the first three are complete.
5. E8 versus scale-matched random kernel under the same seeds and exact config.

Do not treat the geometry run as confirmatory until the clean architecture baselines are closed.
