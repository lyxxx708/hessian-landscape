[CmdletBinding()]
param(
 [string]$Root='E:\GENESIS',
 [string]$PythonVersion='3.11',
 [ValidatePattern('^https://download\.pytorch\.org/whl/cu[0-9]+/?$')]
 [string]$TorchIndexUrl='https://download.pytorch.org/whl/cu128'
)
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'genesis_env.ps1') -Root $Root
$Repo=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
if ([IO.Path]::GetPathRoot($Repo) -ine 'E:\') { throw 'Extract/clone this source under E: before installation; existing C: files are left untouched.' }
Assert-NoReparseParent $Repo
$Venv=Join-Path $Root 'venvs\hessian-landscape-v2'
$VenvParent=$Venv
while (-not(Test-Path -LiteralPath $VenvParent)) { $VenvParent=Split-Path -Path $VenvParent -Parent }
Assert-NoReparseParent $VenvParent
if (-not(Test-Path -LiteralPath (Join-Path $Venv 'Scripts\python.exe'))) {
 & py "-$PythonVersion" -m venv $Venv
 if ($LASTEXITCODE -ne 0) { throw 'Python venv creation failed. Install a supported Python launcher; no global changes performed.' }
}
$Py=Join-Path $Venv 'Scripts\python.exe'
& nvidia-smi
if ($LASTEXITCODE -ne 0) { throw 'NVIDIA driver not available. Driver installation/update is not performed automatically.' }
& $Py -m pip install --upgrade pip setuptools wheel
if ($LASTEXITCODE -ne 0) { throw 'Packaging dependency install failed' }
# Official PyTorch archive pairs 2.10.0 with torchvision 0.25.0 for CUDA 12.8.
# This is a tested API baseline, NOT a claim that 2.10.0 is the newest release.
& $Py -m pip install 'torch==2.10.0' 'torchvision==0.25.0' --index-url $TorchIndexUrl
if ($LASTEXITCODE -ne 0) { throw 'CUDA torch install failed; inspect driver/runtime compatibility. No CPU fallback.' }
Push-Location $Repo
try {
 & $Py -m pip install -e '.[images,parquet,test]'
 if ($LASTEXITCODE -ne 0) { throw 'GENESIS dependency install failed' }
 & $Py -c "import torch; assert torch.cuda.is_available(), 'CUDA unavailable'; print(torch.__version__,torch.cuda.get_device_name(0))"
 if ($LASTEXITCODE -ne 0) { throw 'CUDA initialization failed. Do not run the full study.' }
 & $Py -m pytest tests_v2 -q
 if ($LASTEXITCODE -ne 0) { throw 'Software test gate failed' }
 & $Py -m genesis_gpu --config configs/study_v2.yaml doctor
 if ($LASTEXITCODE -ne 0) { throw 'Device/storage doctor failed; read the receipt' }
} finally { Pop-Location }
Write-Output "Installed to $Venv. CUDA numerical G0 is still mandatory; run genesis_launch.ps1 to execute the guarded pipeline."
