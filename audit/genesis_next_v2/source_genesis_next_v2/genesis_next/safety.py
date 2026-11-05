from __future__ import annotations
from contextlib import contextmanager
from pathlib import Path
import json,os,subprocess

def process_inventory():
    if os.name=='nt':
        command="Get-CimInstance Win32_Process | Where-Object {$_.Name -match 'python|pwsh|powershell'} | Select-Object ProcessId,CreationDate,CommandLine | ConvertTo-Json -Depth 3 -Compress"
        r=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-Command',command],capture_output=True,text=True,timeout=30)
        if r.returncode!=0:raise RuntimeError('Cannot establish process ownership; refusing real assays')
        value=json.loads(r.stdout or '[]')
        return value if isinstance(value,list) else [value]
    r=subprocess.run(['ps','-eo','pid=,args='],capture_output=True,text=True,check=True,timeout=15)
    rows=[]
    for line in r.stdout.splitlines():
        s=line.strip().split(None,1)
        if len(s)==2:rows.append({'ProcessId':int(s[0]),'CommandLine':s[1]})
    return rows

def source_processes(processes):
    out=[]
    for p in processes:
        c=(p.get('CommandLine') or '').lower()
        # Match actual module invocations; a shell command quoting this check does not qualify.
        if ('-m genesis_gpu ' in c or '-m genesis_gpu\" ' in c) and int(p.get('ProcessId',0))!=os.getpid():out.append(p)
    return out

def require_exclusive(device):
    # CPU assays only read COMPLETE v2 receipts and cannot contend for the v2 GPU: no process gate needed.
    if not device.startswith('cuda'):return {'v2_processes':'NOT_CHECKED_CPU_READ_ONLY','gpu_check':'CPU_ONLY'}
    busy=source_processes(process_inventory())
    if busy:raise RuntimeError('v2 worker is active. This kit will NOT stop it. PIDs: '+str([x['ProcessId'] for x in busy]))
    if device.startswith('cuda'):
        r=subprocess.run(['nvidia-smi','--query-compute-apps=pid,process_name','--format=csv,noheader'],capture_output=True,text=True,timeout=15)
        if r.returncode!=0:raise RuntimeError('Cannot verify GPU process ownership')
        # Driver WDDM may not expose VRAM/PIDs completely; explicit user approval is also required.
        if r.stdout.strip():raise RuntimeError('GPU has existing compute applications: '+r.stdout.strip()[:500])
    return {'v2_processes':[],'gpu_check':'NO_LISTED_COMPUTE_APPS' if device.startswith('cuda') else 'CPU_ONLY'}

@contextmanager
def execution_lock(root):
    root=Path(root);root.mkdir(parents=True,exist_ok=True);p=root/'ACTIVE.lock'
    try:
        f=p.open('x',encoding='utf-8')
    except FileExistsError as e:raise RuntimeError('Follow-up ACTIVE.lock exists; inspect its owner before recovery') from e
    try:
        with f:json.dump({'pid':os.getpid(),'purpose':'GENESIS NEXT only'},f)
        yield
    finally:
        p.unlink(missing_ok=True)
