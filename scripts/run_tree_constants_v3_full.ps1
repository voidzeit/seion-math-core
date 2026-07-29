[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$QaRoot = Join-Path $RepoRoot "artifacts/qa_v3"
New-Item -ItemType Directory -Force -Path $QaRoot | Out-Null
$env:PYTHONPATH = Join-Path $RepoRoot "src"
Push-Location $RepoRoot
try {
    function Invoke-V3Stage {
        param(
            [int]$Number,
            [string]$Name,
            [scriptblock]$Action
        )
        Write-Host ("[{0:00}/15] {1}" -f $Number, $Name)
        & $Action
        if ($LASTEXITCODE -ne 0) {
            throw "Stage $Number failed: $Name"
        }
    }

    Invoke-V3Stage 1 "Validate checkpointed repository state" {
        $RequiredCheckpoint = @(
            "artifacts/checkpoints/pre_v3_worktree.patch",
            "artifacts/checkpoints/pre_v3_status.txt",
            "artifacts/checkpoints/pre_v3_diff_stat.txt",
            "artifacts/checkpoints/pre_v3_file_hashes.json"
        )
        foreach ($Path in $RequiredCheckpoint) {
            if (-not (Test-Path -LiteralPath $Path)) {
                throw "Missing preservation checkpoint: $Path"
            }
        }
        $Branch = git branch --show-current
        if ($Branch -ne "research/nodewise-tree-constants-v3") {
            throw "Expected v3 branch, found $Branch"
        }
        git status --short | Out-File -Encoding utf8 (Join-Path $QaRoot "canonical_preflight_status.txt")
    }
    Invoke-V3Stage 2 "Inventory hardware" {
        python -c "import json; from pathlib import Path; from seion_core.research_v3.run_schema import hardware_inventory; Path(r'artifacts/qa_v3/hardware_v3.json').write_text(json.dumps(hardware_inventory(), indent=2, sort_keys=True)+'\n', encoding='utf-8')"
    }
    Invoke-V3Stage 3 "Validate CUDA" {
        python -m pytest -q tests/research_v3/gpu/test_cuda_parity.py --junitxml=artifacts/qa_v3/pytest_cuda_v3.xml
    }
    Invoke-V3Stage 4 "Run complete test suite" {
        python -m pytest -q --junitxml=artifacts/qa_v3/pytest_v3.xml
    }
    Invoke-V3Stage 5 "Enumerate exact tree grammars" {
        python scripts/tree_constants_v3_pipeline.py budget
        if ($LASTEXITCODE -ne 0) { throw "Budget calibration failed." }
        python scripts/tree_constants_v3_pipeline.py enumerate
    }
    Invoke-V3Stage 6 "Run exact certification atlas" {
        python scripts/tree_constants_v3_pipeline.py exact
    }
    Invoke-V3Stage 7 "Run complete A-I base numerical matrix" {
        python scripts/tree_constants_v3_pipeline.py smoke
        if ($LASTEXITCODE -ne 0) { throw "Smoke calibration failed." }
        python scripts/tree_constants_v3_pipeline.py full
    }
    Invoke-V3Stage 8 "Resume and reconcile extended schedule" {
        python scripts/tree_constants_v3_extended.py plan
        if ($LASTEXITCODE -ne 0) { throw "Extended schedule generation failed." }
        python scripts/tree_constants_v3_extended.py run --max-trajectories 0
    }
    Invoke-V3Stage 9 "Aggregate and benchmark scientific instances" {
        python scripts/benchmark_tree_constants_v3.py
    }
    Invoke-V3Stage 10 "Generate scientific tables" {
        python scripts/build_tree_constants_v3_tables.py
    }
    Invoke-V3Stage 11 "Generate all vector figures" {
        python scripts/figures_v3/build.py
    }
    Invoke-V3Stage 12 "Compile mathematical and software papers" {
        & (Join-Path $PSScriptRoot "build_tree_constants_v3_paper.ps1")
    }
    Invoke-V3Stage 13 "Render and inspect every PDF page" {
        python scripts/tree_constants_v3_audit.py render
        if ($LASTEXITCODE -ne 0) { throw "PDF render failed." }
        python scripts/tree_constants_v3_audit.py visual-signoff --status PASS --inspector "automated layout preflight" --notes "All pages rendered and passed blank-page, text extraction, and page-geometry checks; independent human editorial approval remains pending."
    }
    Invoke-V3Stage 14 "Run adversarial reviews and technical audits" {
        python scripts/tree_constants_v3_audit.py reviews
        if ($LASTEXITCODE -ne 0) { throw "Review generation failed." }
        python scripts/tree_constants_v3_audit.py audit
    }
    Write-Host "[15/15] Emit strict release-gate status"
    python scripts/tree_constants_v3_audit.py report
    $GateExit = $LASTEXITCODE
    if ($GateExit -eq 2) {
        Write-Host "Canonical execution completed; publication remains fail-closed by design."
        exit 2
    }
    if ($GateExit -ne 0) {
        throw "Release gate failed operationally with exit code $GateExit."
    }
    exit 0
}
finally {
    Pop-Location
}
