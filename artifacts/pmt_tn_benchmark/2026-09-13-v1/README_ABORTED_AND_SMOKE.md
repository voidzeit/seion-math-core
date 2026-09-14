# Aborted and smoke runs (kept as evidence, not results)

* `F1-ABORTED-nondeterministic-seeds/`: first full F1+F5 launch, stopped by hand before completion.
  Instance seeds were derived with Python `hash()` of tuples containing strings, which is salted per
  process (PYTHONHASHSEED), so these instances cannot be regenerated. Not used in any analysis.
* `F1-quick-smoke-...`, `F2-quick-smoke-...`: `--quick` smoke tests of the runner, with the same
  seeding defect. Not used in any analysis.

Fix: `stable_seed()` in `research/pmt_program/tn_benchmark/seeding.py` (CRC32 of the parameter tuple),
recorded in the preregistration amendment of 2026-09-13.
