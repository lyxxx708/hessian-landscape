[CmdletBinding()]
param([string]$Root='E:\GENESIS',[string]$RunRoot='E:\GENESIS\runs\genesis_full_v2',[string]$Config='')
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'genesis_env.ps1') -Root $Root
$Repo=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
if (-not $Config) { $Config=Join-Path $Repo 'configs\study_v2.yaml' }
$Py=Join-Path $Root 'venvs\hessian-landscape-v2\Scripts\python.exe'
# Cooperative safe boundary only. Never kill unrelated Python/Codex processes.
& $Py -m genesis_gpu --config $Config --root $RunRoot stop
exit $LASTEXITCODE
