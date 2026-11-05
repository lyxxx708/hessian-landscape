[CmdletBinding()]
param(
 [ValidateSet('Inspect','Reproduce','Plan','Freeze','Qualify','Run','Summarize','Test','Demo')]
 [string]$Mode = 'Inspect',
 [string]$Py = 'E:\GENESIS\venvs\hessian-landscape-v2\Scripts\python.exe',
 [string]$Bundle = 'E:\GENESIS\handoff\audit_snapshot_20261104_201035',
 [string]$RunRoot = 'E:\GENESIS\runs\genesis_full_v2',
 [string]$OutputRoot = 'E:\GENESIS\runs\genesis_next_v1',
 [ValidateSet('cpu','cuda:0')][string]$Device='cuda:0',
 [int]$MaxStates=1,
 [switch]$ApproveCompute
)
$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $Py -PathType Leaf)) { throw "Python not found: $Py" }
$names=@('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS','PYTHONDONTWRITEBYTECODE','PYTHONPATH')
$previous=@{}
foreach($name in $names) { $previous[$name]=[Environment]::GetEnvironmentVariable($name,'Process') }
Push-Location $PSScriptRoot
try {
 $env:OMP_NUM_THREADS='2'; $env:OPENBLAS_NUM_THREADS='2'; $env:MKL_NUM_THREADS='2'; $env:NUMEXPR_NUM_THREADS='2'
 $env:PYTHONDONTWRITEBYTECODE='1'; $env:PYTHONPATH=$PSScriptRoot
 if ($Mode -eq 'Test') {
   & $Py -B -m unittest discover -s tests -v
 } else {
   & $Py -B -m genesis_next verify-package
   if ($LASTEXITCODE -ne 0) { throw 'Delivery integrity verification failed.' }
   $command=$Mode.ToLowerInvariant()
   if ($Mode -eq 'Qualify') {$command='run'}
   $argsList=@('-B','-m','genesis_next',$command,'--bundle',$Bundle,'--run-root',$RunRoot,'--out',$OutputRoot)
   if ($Mode -eq 'Freeze') { $argsList+=@('--device',$Device) }
   if ($Mode -eq 'Run' -or $Mode -eq 'Qualify') {
      if (-not $ApproveCompute) {throw 'Real assays require -ApproveCompute. The script never stops v2.'}
      $argsList+=@('--device',$Device,'--max-states',[string]$MaxStates,'--approve-compute')
      if ($Mode -eq 'Qualify') {$argsList+='--qualification'}
   }
   & $Py @argsList
 }
 $code=$LASTEXITCODE
 if ($code -ne 0) {throw "GENESIS NEXT stopped with exit code $code. Read the BLOCKED reason; do not bypass checks."}
} finally {
 Pop-Location
 foreach($name in $names) { [Environment]::SetEnvironmentVariable($name,$previous[$name],'Process') }
}
