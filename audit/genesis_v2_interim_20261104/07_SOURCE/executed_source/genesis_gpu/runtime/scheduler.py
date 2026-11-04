"""Finite deterministic scheduler; one OS process, no per-job LLM calls."""
from pathlib import Path
import gc
import traceback
import time
import torch
from genesis_gpu.contracts import RunSpec,object_sha
from genesis_gpu.study.design import measurement_tier
from genesis_gpu.study.freeze import verify_lock,require_stage_access,set_state
from genesis_gpu.runtime.atomic_io import atomic_json,read_json,file_receipt,verify_receipt
from genesis_gpu.runtime.queue import JobStore
from genesis_gpu.runtime.resources import StudyLock,ResourceGuard,ResourcePause,DeviceLock
from genesis_gpu.training.trainer import train_run,StopRequested
from genesis_gpu.runtime.measurement import measure_job
from genesis_gpu.env.reproducibility import configure_determinism
from genesis_gpu.env.storage_guard import prepare_storage


def plan_jobs(cfg,lock,stage):
    if stage not in ('s1','s2'):raise ValueError('Use the gated optimizer runner for S3')
    jobs=[]
    for spec in lock['runs']:
        run=RunSpec.from_dict(spec)
        if run.stage!=stage:continue
        trainid=object_sha([lock['protocol_sha'],run.run_id,'train'])
        jobs.append({'id':trainid,'stage':stage,'kind':'train','payload':{'run':spec},'dependencies':[]})
        for i in range(4):
            for gamma in cfg['damping_ratios']:
                for schema in cfg['groups']:
                    tier=measurement_tier(stage,i,gamma,run.deep)
                    payload={'run':spec,'checkpoint_index':i,'gamma':gamma,'schema':schema,'tier':tier}
                    jid=object_sha([lock['protocol_sha'],run.run_id,i,gamma,schema,'measure'])
                    jobs.append({'id':jid,'stage':stage,'kind':'measure','payload':payload,'dependencies':[trainid]})
    return jobs


def enqueue_plan(store,cfg,lock,stage):
    jobs=plan_jobs(cfg,lock,stage)
    for job in jobs:store.enqueue(**job)
    return jobs


def status(root):
    root=Path(root);store=JobStore(root/'run_status.sqlite')
    try:
        result={'counts':store.counts(),'stages':{s:store.counts(s) for s in ('s1','s2','s3')},
                'state':read_json(root/'study-state.json') if (root/'study-state.json').exists() else {'state':'NOT_STARTED'},
                'worker':read_json(root/'worker.json') if (root/'worker.json').exists() else None,
                'resources':read_json(root/'resource_status.json') if (root/'resource_status.json').exists() else None}
        atomic_json(root/'status.json',result);return result
    finally:store.close()


def run_stage(cfg,root,stage,*,max_jobs=None,resume=False):
    root=Path(root);prepare_storage(root,production=cfg['profile']=='full',min_free_bytes=int(cfg['resources']['disk_reserve_gib']*1024**3));lock=verify_lock(cfg,root);require_stage_access(root,stage)
    configure_determinism();processed=0;interrupted=False
    with DeviceLock(cfg['storage_root'],cfg['device'],cfg['device'].startswith('cuda')), StudyLock(root):
        control=root/'control.json'
        if control.exists():
            if not resume and read_json(control).get('action') in ('pause','stop'):
                raise StopRequested('Paused: use resume explicitly')
            if resume:atomic_json(control,{'action':'run','time':time.time()})
        store=JobStore(root/'run_status.sqlite')
        try:
            store.recover_interrupted();enqueue_plan(store,cfg,lock,stage)
            set_state(root,stage.upper()+'_RUNNING',scientific_complete=False)
            while max_jobs is None or processed<max_jobs:
                job=store.claim(stage)
                if job is None:break
                guard=ResourceGuard(cfg,root,store,job['id'])
                try:
                    if job['attempts']>cfg['resources']['max_retries']+1:
                        raise RuntimeError('Retry budget exhausted; retain explicit failed coverage')
                    guard()
                    if job['kind']=='train':
                        run=RunSpec.from_dict(job['payload']['run']);r=train_run(run,cfg,root,callback=guard)
                        if r['status']=='INTERRUPTED':
                            store.finish(job['id'],'INTERRUPTED',{'reason':'SAFE_TRAINING_PAUSE','run_receipt':r});interrupted=True;break
                        path=root/'checkpoints'/run.run_id/'training_receipt.json';state='COMPLETE'
                    else:
                        r=measure_job(job['payload'],cfg,root,job['id'],lock['protocol_sha'],guard)
                        path=root/'measurements'/job['id']/'result.json'
                        state='COMPLETE' if r['status']=='NUMERIC_VALID' else 'NUMERIC_UNRESOLVED'
                    receipt=file_receipt(path,root)
                    if not verify_receipt(root,receipt):raise RuntimeError('Artifact commit readback failed')
                    store.finish(job['id'],state,{'receipt':receipt,'measurement_status':r['status']})
                except (StopRequested,KeyboardInterrupt) as exc:
                    store.finish(job['id'],'INTERRUPTED',{'reason':type(exc).__name__,'detail':str(exc)})
                    atomic_json(root/'control.json',{'action':'pause','reason':str(exc),'time':time.time()});interrupted=True;break
                except Exception as exc:
                    trace=root/'logs'/f"failure-{job['id']}-{job['attempts']}.txt"
                    trace.parent.mkdir(parents=True,exist_ok=True);trace.write_text(traceback.format_exc(),encoding='utf-8')
                    # A deterministic scientific/numerical failure is recorded, not retried with altered seeds.
                    store.finish(job['id'],'FAILED',{'error':type(exc).__name__,'reason':str(exc),'trace':file_receipt(trace,root)})
                finally:
                    gc.collect()
                    if torch.cuda.is_available():torch.cuda.empty_cache()
                processed+=1
                atomic_json(root/'heartbeat.json',{'stage':stage,'processed_this_invocation':processed,'counts':store.counts(stage),'time':time.time()})
            complete=store.stage_complete(stage)
            if complete:set_state(root,stage.upper()+'_EXECUTED',scientific_complete=False,execution_counts=store.counts(stage))
            elif interrupted:set_state(root,'INTERRUPTED',interrupted_stage=stage,scientific_complete=False)
            return {'stage':stage,'execution_complete':complete,'interrupted':interrupted,'processed':processed,'counts':store.counts(stage)}
        finally:store.interrupt_owned();store.close();status(root)
