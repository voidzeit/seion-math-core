$ErrorActionPreference = 'Stop'
python scripts/audit_v4.py
python -m seion_core.cli.main governance dedupe-runs
