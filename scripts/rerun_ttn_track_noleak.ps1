# Re-run the scientific TTN track under the non-leaking training-negative filter.
#
# B-0014: runs/TTN_FB15K237_* were produced while evaluation filter tables
# (TRAIN+VALID+TEST) were also masking training negatives, which exempts every
# held-out gold from negative gradient. This script reproduces the *scientific*
# runs -- headline, D128, and the nine-seed spread -- with identical
# hyperparameters and only `--negative-filter train_only` changed, so each new
# run pairs directly against its existing leaking counterpart.
#
# Smoke/diagnostic/canary/posttrain directories are deliberately NOT reproduced:
# they are infrastructure checks, not scientific results.
#
# Negative sampling runs on the device (`--gpu-negative-sampler`): the reference
# sampler is a per-row Python loop that pins a CPU core while the GPU idles.
# Distributionally equivalent, not bit-exact, and uniform across all 11 runs
# so the seed spread stays internally comparable.
#
# Application results are left untouched (`--skip-application-result`) so the
# original evidence is preserved; the corrected numbers live in the new run
# directories only.

$ErrorActionPreference = "Stop"
$stamp = "2026-08-11"
$common = @(
    "--train", "data/FB15K-237/train.txt",
    "--valid", "data/FB15K-237/valid.txt",
    "--test",  "data/FB15K-237/test.txt",
    "--negative-filter", "train_only",
    "--gpu-negative-sampler",
    "--skip-application-result"
)

function Invoke-TtnRun {
    param([string]$Name, [string[]]$Extra)
    $out = "runs/$Name"
    if (Test-Path $out) {
        Write-Host "SKIP (exists): $Name"
        return
    }
    Write-Host "=== $Name ==="
    $sw = [Diagnostics.Stopwatch]::StartNew()
    & python -m seion_kgr.run_ttn_fb15k237 @common @Extra --out-dir $out 2>&1 |
        Tee-Object -FilePath "runs/$Name.log" | Out-Null
    $code = $LASTEXITCODE
    $sw.Stop()
    Write-Host ("    exit {0} in {1:N1}s" -f $code, $sw.Elapsed.TotalSeconds)
    if ($code -ne 0) { throw "run failed: $Name (see runs/$Name.log)" }
}

# 1. Headline: D32 normed, full rank grid.
Invoke-TtnRun "TTN_FB15K237_BRANCHING_K3_FINAL_NORMED_E10_NOLEAK_$stamp" @(
    "--dim", "32", "--branch-dim", "32", "--epochs", "10", "--batch-size", "4096",
    "--neg-k", "32", "--lr", "1e-3", "--weight-decay", "1e-6",
    "--loss-temperature", "1000.0", "--embedding-max-norm", "1.0",
    "--core-max-fro", "1.0", "--root-max-fro", "1.0",
    "--tolerances", "0.1,0.01,0.001,0.0001,0.00001",
    "--calibration-triples", "8192", "--eval-queries", "32",
    "--candidate-sample", "256", "--seed", "42", "--rank-grid",
    "--budgets", "2,4,8,16,32,48,64"
)

# 2. D128 checkpoint -- the one the score-space analysis is built on.
Invoke-TtnRun "TTN_FB15K237_TTN_V2_D128_E10_NOLEAK_$stamp" @(
    "--dim", "128", "--branch-dim", "128", "--epochs", "10", "--batch-size", "4096",
    "--neg-k", "32", "--lr", "1e-3", "--weight-decay", "1e-6",
    "--loss-temperature", "1000.0", "--embedding-max-norm", "1.0",
    "--core-max-fro", "1.0", "--root-max-fro", "1.0",
    "--tolerances", "0.1,0.01,0.001,0.0001,0.00001",
    "--calibration-triples", "8192", "--eval-queries", "32",
    "--candidate-sample", "256", "--seed", "42",
    "--budgets", "2,4,8,16,32,64,96,128"
)

# 3. Nine-seed spread, matching the existing MULTISEED configuration.
foreach ($seed in 7, 17, 27, 37, 47, 57, 67, 77, 87) {
    Invoke-TtnRun "TTN_FB15K237_BRANCHING_K3_MULTISEED_S${seed}_NOLEAK_$stamp" @(
        "--dim", "32", "--branch-dim", "32", "--epochs", "10", "--batch-size", "4096",
        "--neg-k", "32", "--lr", "1e-3", "--weight-decay", "1e-6",
        "--loss-temperature", "1000.0", "--embedding-max-norm", "1.0",
        "--core-max-fro", "1.0", "--root-max-fro", "1.0",
        "--tolerances", "0.1,0.01,0.001,0.0001,0.00001",
        "--calibration-triples", "8192", "--eval-queries", "16",
        "--candidate-sample", "128", "--seed", "$seed",
        "--budgets", "2,8,16,32,64"
    )
}

Write-Host "TTN no-leak track complete."
