# Dot-source in the SAME PowerShell session that launches the experiment:
#   . .\scripts\prepare_local_e_drive.ps1
# Process-local environment only; never edits global Windows settings or C:.
[CmdletBinding()]
param(
    [string]$Root = 'E:\GENESIS',
    [double]$MinFreeGiB = 1
)
$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath 'E:\' -PathType Container)) {
    throw 'E: is not available. Refusing to use C: as fallback.'
}
$fullRoot = [System.IO.Path]::GetFullPath($Root)
if ([System.IO.Path]::GetPathRoot($fullRoot) -ine 'E:\') {
    throw "Expected an E: root, got '$fullRoot'. Refusing fallback."
}
$drive = [System.IO.DriveInfo]::new('E')
if (-not $drive.IsReady) {
    throw 'E: exists but is not ready.'
}
$freeGiB = $drive.AvailableFreeSpace / 1GB
if ($freeGiB -lt $MinFreeGiB) {
    throw "E: free space $([math]::Round($freeGiB,2)) GiB is below minimum $MinFreeGiB GiB. No C: fallback."
}
$paths = @{
    worktrees = (Join-Path $fullRoot 'worktrees')
    venvs = (Join-Path $fullRoot 'venvs')
    datasets = (Join-Path $fullRoot 'datasets')
    downloads = (Join-Path $fullRoot 'downloads')
    cache = (Join-Path $fullRoot 'cache')
    tmp = (Join-Path $fullRoot 'tmp')
    runs = (Join-Path $fullRoot 'runs\genesis_full_20261102')
}
$envPaths = @{
    TEMP = $paths.tmp
    TMP = $paths.tmp
    TMPDIR = $paths.tmp
    PIP_CACHE_DIR = (Join-Path $paths.cache 'pip')
    UV_CACHE_DIR = (Join-Path $paths.cache 'uv')
    HF_HOME = (Join-Path $paths.cache 'huggingface')
    HF_HUB_CACHE = (Join-Path $paths.cache 'huggingface\hub')
    HF_DATASETS_CACHE = (Join-Path $paths.cache 'huggingface\datasets')
    TORCH_HOME = (Join-Path $paths.cache 'torch')
    TORCH_EXTENSIONS_DIR = (Join-Path $paths.cache 'torch_extensions')
    TRITON_CACHE_DIR = (Join-Path $paths.cache 'triton')
    NUMBA_CACHE_DIR = (Join-Path $paths.cache 'numba')
    MPLCONFIGDIR = (Join-Path $paths.cache 'matplotlib')
    PYTHONPYCACHEPREFIX = (Join-Path $paths.cache 'python_bytecode')
    CUDA_CACHE_PATH = (Join-Path $paths.cache 'cuda')
    XDG_CACHE_HOME = (Join-Path $paths.cache 'xdg')
}
foreach ($dir in ($paths.Values + $envPaths.Values + @(
    (Join-Path $paths.runs 'checkpoints'),
    (Join-Path $paths.runs 'logs'),
    (Join-Path $paths.runs 'reports')
))) {
    New-Item -ItemType Directory -Path $dir -Force | Out-Null
}
foreach ($key in $envPaths.Keys) {
    [Environment]::SetEnvironmentVariable($key, $envPaths[$key], [EnvironmentVariableTarget]::Process)
}
[Environment]::SetEnvironmentVariable('GENESIS_ROOT', $fullRoot, [EnvironmentVariableTarget]::Process)
[Environment]::SetEnvironmentVariable('GENESIS_RUN_DIR', $paths.runs, [EnvironmentVariableTarget]::Process)
[Environment]::SetEnvironmentVariable('GENESIS_DATA_DIR', $paths.datasets, [EnvironmentVariableTarget]::Process)
[Environment]::SetEnvironmentVariable('WANDB_DIR', (Join-Path $paths.runs 'logs'), [EnvironmentVariableTarget]::Process)
$cFree = $null
if (Test-Path -LiteralPath 'C:\') {
    $cFree = [math]::Round(([System.IO.DriveInfo]::new('C')).AvailableFreeSpace / 1GB, 2)
}
$receipt = [ordered]@{
    storage_policy = 'E_DRIVE_FIRST'
    root = $fullRoot
    worktree_directory = $paths.worktrees
    venv_directory = $paths.venvs
    datasets_directory = $paths.datasets
    run_directory = $paths.runs
    E_free_gib_at_setup = [math]::Round($freeGiB, 2)
    C_free_gib_at_setup = $cFree
    process_only = $true
    no_C_fallback = $true
    timestamp = (Get-Date).ToString('o')
}
$receipt | ConvertTo-Json -Depth 3 | Set-Content -Encoding UTF8 -Path (Join-Path $paths.runs 'storage_preflight.json')
Write-Host "GENESIS E:-first environment set for this PowerShell process. Root=$fullRoot; E: free $([math]::Round($freeGiB,2)) GiB. No C: fallback."
