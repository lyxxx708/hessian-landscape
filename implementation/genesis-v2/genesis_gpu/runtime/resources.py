"""Process-safe ownership, cooperative cancellation and local resource receipts."""
from pathlib import Path
import os
import time
import uuid
import subprocess
import shutil
import psutil
from genesis_gpu.runtime.atomic_io import atomic_json,read_json
from genesis_gpu.env.storage_guard import ensure_space,StorageBlocked
from genesis_gpu.training.trainer import StopRequested


class ResourcePause(StopRequested):
    pass


class StudyLock:
    def __init__(self,root):
        self.root=Path(root);self.handle=None;self.token=uuid.uuid4().hex

    def __enter__(self):
        self.root.mkdir(parents=True,exist_ok=True)
        self.handle=(self.root/'.writer.lock').open('a+b');self.handle.seek(0)
        if (self.root/'.writer.lock').stat().st_size==0:self.handle.write(b'0');self.handle.flush()
        try:
            if os.name=='nt':
                import msvcrt
                self.handle.seek(0);msvcrt.locking(self.handle.fileno(),msvcrt.LK_NBLCK,1)
            else:
                import fcntl
                fcntl.flock(self.handle.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        except OSError as exc:
            self.handle.close();self.handle=None
            raise RuntimeError('Another worker holds this study lock; no duplicate GPU job') from exc
        self.identity={'pid':os.getpid(),'process_started':psutil.Process().create_time(),'token':self.token,
                       'root':str(self.root.resolve()),'active':True,'time':time.time()}
        atomic_json(self.root/'worker.json',self.identity)
        return self

    def __exit__(self,*args):
        if self.handle:
            atomic_json(self.root/'worker.json',{**self.identity,'active':False,'time':time.time()})
            if os.name=='nt':
                import msvcrt
                self.handle.seek(0);msvcrt.locking(self.handle.fileno(),msvcrt.LK_UNLCK,1)
            else:
                import fcntl
                fcntl.flock(self.handle.fileno(),fcntl.LOCK_UN)
            self.handle.close();self.handle=None


def nvidia_status(index=0):
    try:
        result=subprocess.run(['nvidia-smi',f'--id={index}',
            '--query-gpu=name,memory.total,memory.used,temperature.gpu,power.draw,utilization.gpu',
            '--format=csv,noheader,nounits'],capture_output=True,text=True,timeout=8,check=True)
        fields=[x.strip() for x in result.stdout.splitlines()[0].split(',')]
        def number(v):
            try:return float(v)
            except ValueError:return None
        return dict(zip(['name','total_mib','used_mib','temperature_c','power_w','utilization_pct'],[fields[0],*map(number,fields[1:])]))
    except (OSError,subprocess.SubprocessError,IndexError):return {'status':'NVIDIA_SMI_UNAVAILABLE'}


class ResourceGuard:
    def __init__(self,cfg,root,store=None,job_id=None):
        self.cfg=cfg;self.root=Path(root);self.store=store;self.job_id=job_id;self.last=0.

    def __call__(self):
        control=self.root/'control.json'
        if control.exists():
            request=read_json(control)
            if request.get('action') in ('stop','pause'):raise StopRequested(request['action'])
        if time.monotonic()-self.last<self.cfg['resources']['heartbeat_seconds']:return
        self.last=time.monotonic()
        if self.store and self.job_id:self.store.heartbeat(self.job_id)
        reserve=int(self.cfg['resources']['disk_reserve_gib']*1024**3)
        try:free=ensure_space(self.root,reserve)
        except StorageBlocked as exc:raise ResourcePause('STORAGE_BLOCKED: '+str(exc)) from exc
        status={'timestamp':time.time(),'pid':os.getpid(),'root_free_bytes':free,'ram_available':psutil.virtual_memory().available,
                'process_rss':psutil.Process().memory_info().rss,'job_id':self.job_id}
        if self.cfg['device'].startswith('cuda'):
            import torch
            device=torch.device(self.cfg['device']);index=device.index or 0
            status['gpu']=nvidia_status(index)
            status['allocated']=torch.cuda.memory_allocated(device);status['reserved']=torch.cuda.memory_reserved(device)
            status['peak_allocated']=torch.cuda.max_memory_allocated(device);status['peak_reserved']=torch.cuda.max_memory_reserved(device)
            temp=status['gpu'].get('temperature_c')
            if temp is not None and temp>=self.cfg['resources']['thermal_pause_c']:
                atomic_json(self.root/'resource_status.json',status)
                raise ResourcePause('THERMAL_PAUSE: configured temperature threshold reached')
        if os.name=='nt':
            status['volume_free_bytes']={d:shutil.disk_usage(d+'\\').free for d in ('C:','E:') if Path(d+'\\').exists()}
        atomic_json(self.root/'resource_status.json',status)


class DeviceLock:
    """One worker per physical device across different study roots (process-safe)."""
    def __init__(self,storage_root,device,enabled=True):
        import hashlib
        name=hashlib.sha256(str(device).encode()).hexdigest()[:12]
        self.lock=StudyLock(Path(storage_root)/'device_locks'/name) if enabled else None
    def __enter__(self):
        if self.lock:self.lock.__enter__()
        return self
    def __exit__(self,*args):
        if self.lock:self.lock.__exit__(*args)
