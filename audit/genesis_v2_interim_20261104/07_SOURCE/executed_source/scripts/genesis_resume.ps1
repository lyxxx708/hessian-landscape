[CmdletBinding()]
param([string]$Root='E:\GENESIS',[string]$RunRoot='E:\GENESIS\runs\genesis_full_v2',[string]$Config='',[switch]$Foreground)
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'genesis_env.ps1') -Root $Root
if (-not(Test-Path (Join-Path $RunRoot 'protocol-lock.json'))) { throw 'No frozen protocol to resume. Use genesis_launch.ps1 for first run.' }
& (Join-Path $PSScriptRoot 'genesis_launch.ps1') -Root $Root -RunRoot $RunRoot -Config $Config -Foreground:$Foreground
