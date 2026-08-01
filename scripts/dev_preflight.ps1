$ErrorActionPreference = 'Stop'
python -m seion_core.cli.main governance audit --json
python scripts/build_v4_foundation.py
python scripts/audit_v4.py
