# Dot-source from every launcher. Process-local only; no registry/global changes.
[CmdletBinding()]
param([string]$Root='E:\GENESIS')
$ErrorActionPreference='Stop'
$Root=[IO.Path]::GetFullPath($Root)
if ([IO.Path]::GetPathRoot($Root) -ine 'E:\' -or -not(Test-Path -LiteralPath 'E:\')) { throw 'STORAGE_BLOCKED: E: is mandatory. No C: fallback.' }
function Assert-NoReparseParent([string]$Path) {
    $p=[IO.Path]::GetFullPath($Path)
    while ($p -and (Test-Path -LiteralPath $p)) {
        $item=Get-Item -LiteralPath $p -Force
        if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw "Refusing reparse/junction bulk path: $p" }
        $parent=Split-Path -Path $p -Parent
        if ($parent -eq $p) { break }; $p=$parent
    }
}
# Check all existing ancestors even when the final directory does not yet exist.
$ancestor=$Root
while (-not(Test-Path -LiteralPath $ancestor)) { $ancestor=Split-Path -Path $ancestor -Parent }
Assert-NoReparseParent $ancestor
$mapping=@{
    TEMP='tmp'; TMP='tmp'; TMPDIR='tmp'; PIP_CACHE_DIR='cache\pip'; UV_CACHE_DIR='cache\uv';
    HF_HOME='cache\huggingface'; HF_HUB_CACHE='cache\huggingface\hub'; HF_DATASETS_CACHE='cache\huggingface\datasets';
    TORCH_HOME='cache\torch'; TORCH_EXTENSIONS_DIR='cache\torch_extensions'; TRITON_CACHE_DIR='cache\triton';
    CUDA_CACHE_PATH='cache\cuda'; NUMBA_CACHE_DIR='cache\numba'; MPLCONFIGDIR='cache\matplotlib';
    PYTHONPYCACHEPREFIX='cache\pycache'; XDG_CACHE_HOME='cache\xdg'
}
foreach ($name in $mapping.Keys) {
    $path=Join-Path $Root $mapping[$name]
    $parent=$path; while (-not(Test-Path -LiteralPath $parent)) { $parent=Split-Path $parent -Parent }
    Assert-NoReparseParent $parent
    New-Item -ItemType Directory -Path $path -Force | Out-Null
    [Environment]::SetEnvironmentVariable($name,$path,[EnvironmentVariableTarget]::Process)
}
$env:GENESIS_ROOT=$Root
$env:CUBLAS_WORKSPACE_CONFIG=':4096:8'
$env:OMP_NUM_THREADS='2'
$env:OPENBLAS_NUM_THREADS='2'
