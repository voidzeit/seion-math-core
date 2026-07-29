[CmdletBinding()]
param(
  [switch]$Strict
)

$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location $root

$arguments = @('-m', 'seion_core.cli.main', 'governance', 'audit', '--json')
if ($Strict) { $arguments += '--strict' }
python @arguments
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
