$ErrorActionPreference = 'Stop'
python scripts/prepare_papers_v4.py
& "$PSScriptRoot/build_papers_v4.ps1"
