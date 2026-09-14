param(
    [string]$ManifestPath = 'research/projected_trees_v5/review/REVIEW_ARTIFACT_MANIFEST_2026-08-09.md'
)

$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
$manifest = if ([IO.Path]::IsPathRooted($ManifestPath)) {
    $ManifestPath
} else {
    Join-Path $repoRoot $ManifestPath
}

if (-not (Test-Path -LiteralPath $manifest -PathType Leaf)) {
    throw "Review manifest not found: $manifest"
}

$records = @()
foreach ($line in Get-Content -LiteralPath $manifest) {
    $match = [regex]::Match($line, '^\|\s+`([^`]+)`\s+\|\s+`([A-Fa-f0-9]{64})`\s+\|$')
    if ($match.Success) {
        $records += [pscustomobject]@{
            path = $match.Groups[1].Value
            expected = $match.Groups[2].Value.ToUpperInvariant()
        }
    }
}

$expectedRecordCount = 19
if ($records.Count -ne $expectedRecordCount) {
    throw "Expected $expectedRecordCount review hash rows, found $($records.Count)"
}

$seen = @{}
$mismatches = @()
foreach ($record in $records) {
    if ($seen.ContainsKey($record.path)) {
        $mismatches += "Duplicate manifest path: $($record.path)"
        continue
    }
    $seen[$record.path] = $true

    $target = Join-Path $repoRoot $record.path
    if (-not (Test-Path -LiteralPath $target -PathType Leaf)) {
        $mismatches += "Missing review input: $($record.path)"
        continue
    }

    $actual = (Get-FileHash -Algorithm SHA256 -LiteralPath $target).Hash.ToUpperInvariant()
    if ($actual -ne $record.expected) {
        $mismatches += "Hash mismatch: $($record.path) expected=$($record.expected) actual=$actual"
    }
}

if ($mismatches.Count -gt 0) {
    $mismatches | ForEach-Object { Write-Error $_ }
    exit 1
}

Write-Output "PASS: verified $($records.Count) frozen review artifact hashes"
