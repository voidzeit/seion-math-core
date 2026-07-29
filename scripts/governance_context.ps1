[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)]
  [string]$Task,
  [string]$Output
)

$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location $root

$arguments = @('-m', 'seion_core.cli.main', 'governance', 'context', '--task', $Task)
if ($Output) { $arguments += @('--output', $Output) }
python @arguments
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
