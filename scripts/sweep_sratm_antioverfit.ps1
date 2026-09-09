# Anti-overfitting sweep for the sealed SRATM trainer.
#
# The 2h V2 campaign peaked at VALID MRR 0.20571 (step 1678) and then declined
# monotonically to 0.17564 by step 17763 while training loss fell to 0.031.
# That is overfitting, not undertraining, so more steps cannot help; this sweep
# moves the regularization levers instead.
#
# Fixed step budget (not wall clock) so cheaper architectures are not rewarded
# merely for being cheaper -- every configuration gets the same number of
# optimizer steps, with a wall-clock cap only as a safety net.
#
# Every run is sealed: TRAIN+VALID only, TRAIN-only mining filter (B-0014),
# fail-closed TEST sentinel. TEST is not opened anywhere in this sweep.

$ErrorActionPreference = "Stop"
$stamp = "2026-08-11"
$steps = 1500          # ~1.4 epochs; the V2 peak sat at step 1678
$capSeconds = 620

$base = @(
    "--train", "data/FB15K-237/train.txt",
    "--valid", "data/FB15K-237/valid.txt",
    "--batch-size", "512", "--candidate-block", "14541", "--entity-block", "4096",
    "--max-steps", "$steps", "--max-seconds", "$capSeconds", "--epochs", "100",
    "--scheduler", "cosine", "--warmup-steps", "100", "--min-lr-ratio", "0.05",
    "--eval-every-seconds", "120", "--eval-queries", "2048",
    "--checkpoint-every", "$steps",
    "--max-vram-gb", "23.0", "--seed", "42",
    "--fast-miner", "--mining-filter", "train_only"
)

# name                     extra flags (deviation from the V2 reference config)
$configs = @(
    @{ n = "A_ref";            f = @() },
    @{ n = "B_wd1e2";          f = @("--weight-decay", "1e-2") },
    @{ n = "C_wd1e3";          f = @("--weight-decay", "1e-3") },
    @{ n = "D_wd1e4";          f = @("--weight-decay", "1e-4") },
    @{ n = "E_d128_wd1e3";     f = @("--weight-decay", "1e-3", "--dim", "128", "--relation-dim", "128") },
    @{ n = "F_hardk32_wd1e3";  f = @("--weight-decay", "1e-3", "--hard-k", "32") },
    @{ n = "G_temp02_wd1e3";   f = @("--weight-decay", "1e-3", "--temperature", "0.2") },
    @{ n = "H_small_wd1e3";    f = @("--weight-decay", "1e-3", "--dim", "128", "--relation-dim", "128",
                                     "--experts", "4", "--expert-rank", "32", "--hard-k", "64") }
)

foreach ($c in $configs) {
    $out = "runs/SRATM_SWEEP_${stamp}_$($c.n)"
    if (Test-Path $out) { Write-Host "SKIP $($c.n)"; continue }
    Write-Host "=== $($c.n) ==="
    $sw = [Diagnostics.Stopwatch]::StartNew()
    & python -m seion_kgr.train_sratm_sealed @base @($c.f) --out-dir $out `
        > "runs/SRATM_SWEEP_${stamp}_$($c.n).log" 2>&1
    $code = $LASTEXITCODE
    $sw.Stop()
    Write-Host ("    exit {0} in {1:N0}s" -f $code, $sw.Elapsed.TotalSeconds)
    if ($code -ne 0) { Write-Host "    FAILED - preserved for inspection, continuing" }
}

Write-Host "sweep complete."
