[CmdletBinding()]
param(
 [string]$Root='E:\GENESIS',
 [string]$RunRoot='E:\GENESIS\runs\genesis_full_v2',
 [string]$Config='',
 [switch]$AcceptPublicDataLicenses,
 [switch]$Foreground
)
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'genesis_env.ps1') -Root $Root
$Repo=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
Assert-NoReparseParent $Repo
$Py=Join-Path $Root 'venvs\hessian-landscape-v2\Scripts\python.exe'
if (-not(Test-Path -LiteralPath $Py)) { throw 'Run genesis_bootstrap.ps1 first' }
Assert-NoReparseParent (Split-Path -Path $Py -Parent)
if ([IO.Path]::GetPathRoot([IO.Path]::GetFullPath($RunRoot)) -ine 'E:\') { throw 'E: output required; no fallback.' }
$RunParent=[IO.Path]::GetFullPath($RunRoot)
while (-not(Test-Path -LiteralPath $RunParent)) { $RunParent=Split-Path -Path $RunParent -Parent }
Assert-NoReparseParent $RunParent
if (-not $Config) { $Config=Join-Path $Repo 'configs\study_v2.yaml' }
if (-not $AcceptPublicDataLicenses -and -not(Test-Path (Join-Path $RunRoot 'protocol-lock.json'))) {
 throw 'First run needs -AcceptPublicDataLicenses after inspecting dataset provenance. No private/paid data is used.'
}
New-Item -ItemType Directory -Path (Join-Path $RunRoot 'logs') -Force | Out-Null
$Arguments=@('-m','genesis_gpu','--config',"`"$Config`"",'--root',"`"$RunRoot`"",'pipeline')
if ($AcceptPublicDataLicenses) { $Arguments+='--accept-licenses' }
Push-Location $Repo
try {
 if ($Foreground) {
  # Invocation operator does not need the Start-Process quoting layer.
  $Direct=@('-m','genesis_gpu','--config',$Config,'--root',$RunRoot,'pipeline')
  if ($AcceptPublicDataLicenses) { $Direct+='--accept-licenses' }
  & $Py @Direct
  if ($LASTEXITCODE -ne 0) { throw 'Pipeline blocked or incomplete; inspect status/receipts, not a fabricated success.' }
 } else {
  $Stamp=Get-Date -Format 'yyyyMMdd-HHmmss'
  $Process=Start-Process -FilePath $Py -ArgumentList $Arguments -WorkingDirectory $Repo -PassThru `
   -RedirectStandardOutput (Join-Path $RunRoot "logs\launcher-$Stamp.out.log") `
   -RedirectStandardError (Join-Path $RunRoot "logs\launcher-$Stamp.err.log")
  [ordered]@{pid=$Process.Id; started=$Process.StartTime.ToString('o'); run_root=$RunRoot; repo=$Repo} |
   ConvertTo-Json | Set-Content -Encoding UTF8 (Join-Path $RunRoot 'launcher.json')
  Write-Output "Started local process PID $($Process.Id); it is independent of Codex chat. Use genesis_status.ps1 and genesis_stop.ps1."
 }
} finally { Pop-Location }
