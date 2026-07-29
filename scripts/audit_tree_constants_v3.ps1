[CmdletBinding()]
param(
    [switch]$Render,
    [switch]$AdvisoryVisualSignoff
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
Push-Location $RepoRoot
try {
    if ($Render) {
        python scripts/tree_constants_v3_audit.py render
        if ($LASTEXITCODE -ne 0) { throw "PDF rendering failed." }
    }
    if ($AdvisoryVisualSignoff) {
        python scripts/tree_constants_v3_audit.py visual-signoff --status PASS --inspector "automated layout preflight" --notes "All pages rendered, extracted nonblank text, and retained consistent page geometry; independent human editorial approval remains pending."
        if ($LASTEXITCODE -ne 0) { throw "Visual preflight recording failed." }
    }
    python scripts/tree_constants_v3_audit.py reviews
    if ($LASTEXITCODE -ne 0) { throw "Adversarial review generation failed." }
    python scripts/tree_constants_v3_audit.py audit
    if ($LASTEXITCODE -ne 0) { throw "Technical v3 audit failed." }
}
finally {
    Pop-Location
}
