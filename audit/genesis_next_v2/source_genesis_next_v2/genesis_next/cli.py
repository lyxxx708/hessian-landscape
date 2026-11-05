from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback
from .io_utils import read_json,write_json,verify_bundle,assert_separate,digest,utc_now
from .planning import make_plan,verify_source,freeze,validate_freeze,validate_result_identity,environment

PACKAGE=Path(__file__).resolve().parents[1]
OUT=Path(r'E:\GENESIS\runs\genesis_next_v2')

def parser():
    p=argparse.ArgumentParser(description='GENESIS NEXT: immutable S1 follow-up, no v2 writes')
    sub=p.add_subparsers(dest='command',required=True)
    for name in ('inspect','reproduce','plan','freeze','run','drive','summarize','demo','_child','verify-package'):
        s=sub.add_parser(name)
        s.add_argument('--bundle',type=Path,default=Path(r'E:\GENESIS\handoff\audit_snapshot_20261104_201035'))
        s.add_argument('--source',type=Path)
        s.add_argument('--run-root',type=Path,default=Path(r'E:\GENESIS\runs\genesis_full_v2'))
        s.add_argument('--out',type=Path,default=OUT)
        s.add_argument('--config',type=Path,default=PACKAGE/'configs/protocol_v2.json')
        if name in ('run','drive','_child','freeze'):
            s.add_argument('--device',choices=['cpu','cuda:0'],default='cuda:0')
            s.add_argument('--approve-compute',action='store_true')
        if name=='run':
            s.add_argument('--qualification',action='store_true')
            s.add_argument('--max-states',type=int,default=1)
        if name=='drive':
            s.add_argument('--workers',type=int,default=4);s.add_argument('--deadline-epoch',type=float,default=None)
        if name=='_child':
            s.add_argument('--state-id',required=True);s.add_argument('--gammas',default='')
    return p

def package_check():
    m=PACKAGE/'PACKAGE_MANIFEST.json'
    if not m.exists():raise ValueError('PACKAGE_MANIFEST.json absent')
    bad=[];obj=read_json(m)
    from .io_utils import safe_join
    for r in obj['files']:
        path=safe_join(PACKAGE,r['path'])
        if not path.is_file() or digest(path)!=r['sha256']:bad.append(r['path'])
    if bad:raise ValueError('Delivery modified or incomplete: '+str(bad))
    return {'status':'PACKAGE_HASHES_PASS','files':len(obj['files'])}

def qualify_ids(lock):
    first={}
    for state in lock['plan']['states']:
        r=state['run'];fam=r['model']['family']
        if r['seed_index']==1 and state['checkpoint_index']==3 and fam not in first:first[fam]=state['state_id']
    return first

def qualified_families(lock,output):
    passed=[]
    for fam,sid in qualify_ids(lock).items():
        path=Path(output)/'results'/f'{sid}.json'
        if path.exists():
            r=read_json(path);validate_result_identity(r,lock['freeze_sha'],sid)
            device=lock['execution_device']
            device_ok=r.get('device')==device and r.get('status')=='EXECUTED'
            memory_ok=(not device.startswith('cuda') or
                (r.get('memory_within_target') is True and
                 r.get('peak_allocated_gib',float('inf'))<=lock['config']['memory_target_gib'] and
                 r.get('peak_reserved_gib',float('inf'))<=lock['config']['memory_target_gib']))
            if device_ok and memory_ok and len(r.get('conditions',[]))==len(lock['config']['gammas']) and all(c['status']=='QUALIFIED' for c in r['conditions']):passed.append(fam)
    return passed

def is_ancestor(pid):
    """True if pid is this process's parent or an earlier ancestor (venv launchers add a shim process)."""
    import psutil
    try:return any(a.pid==pid for a in psutil.Process().parents())
    except psutil.Error:return False

def qualified_conditions(lock,output):
    passed=set()
    for fam,sid in qualify_ids(lock).items():
        path=Path(output)/'results'/f'{sid}.json'
        if not path.exists():continue
        r=read_json(path);validate_result_identity(r,lock['freeze_sha'],sid)
        device=lock['execution_device']
        if r.get('device')!=device or r.get('status')!='EXECUTED':continue
        if device.startswith('cuda') and not (r.get('memory_within_target') is True and
            r.get('peak_allocated_gib',float('inf'))<=lock['config']['memory_target_gib'] and
            r.get('peak_reserved_gib',float('inf'))<=lock['config']['memory_target_gib']):continue
        for c in r.get('conditions',[]):
            if c['status']=='QUALIFIED':passed.add((fam,float(c['gamma'])))
    return passed

def source_ready(lock,state):
    receipt=Path(lock['inputs']['run_root'])/'checkpoints'/state['run']['run_id']/'training_receipt.json'
    try:return receipt.is_file() and read_json(receipt).get('status')=='COMPLETE'
    except Exception:return False

def drive(args):
    """Unattended OS-process driver: parallel children, per-state timeout, heartbeat, cooperative STOP file."""
    if not args.approve_compute:raise ValueError('Real assays require --approve-compute')
    from .safety import require_exclusive,execution_lock
    lock=validate_freeze(args.out,PACKAGE)
    if args.device!=lock['execution_device']:raise ValueError('Device differs from freeze')
    require_exclusive(args.device)
    out=args.out.resolve();assert_separate(out,[lock['inputs']['source'],lock['inputs']['bundle'],lock['inputs']['run_root'],PACKAGE])
    qids=qualify_ids(lock);planned=lock['plan']['states'];timeout=lock['config']['state_timeout_seconds']
    logdir=out/'logs';logdir.mkdir(parents=True,exist_ok=True);stop=out/'STOP';running={};events=[];skipped=set()
    def committed(sid):return (out/'results'/f'{sid}.json').exists()
    def launch(state,gammas):
        sid=state['state_id'];cmd=[sys.executable,'-B','-m','genesis_next','_child','--out',str(out),'--state-id',sid,
             '--device',args.device,'--approve-compute','--gammas',','.join(str(g) for g in gammas)]
        env=os.environ.copy();env['PYTHONPATH']=str(PACKAGE);env['PYTHONDONTWRITEBYTECODE']='1'
        log=(logdir/f'{sid}.log').open('w',encoding='utf-8')
        proc=subprocess.Popen(cmd,cwd=str(PACKAGE),env=env,stdout=log,stderr=subprocess.STDOUT)
        running[sid]={'proc':proc,'log':log,'start':time.monotonic(),'state':state,'pid':proc.pid}
    def reap():
        for sid in list(running):
            r=running[sid];proc=r['proc'];elapsed=time.monotonic()-r['start'];state=r['state'];dest=out/'results'/f'{sid}.json'
            code=proc.poll()
            if code is None and elapsed>timeout:
                proc.kill();proc.wait();code='TIMEOUT'
            if code is None:continue
            r['log'].close()
            partial0=out/'partials'/f'{sid}.json'
            if not dest.exists() and code not in (0,'TIMEOUT') and not partial0.exists() and elapsed<20:
                # Launch/infrastructure failure before any assay work: not a scientific measurement, never committed.
                write_json(out/'infra_failures'/f'{sid}-{time.time_ns()}.json',{'state_id':sid,'exit':code,'log':str(logdir/f'{sid}.log')})
                skipped.add(sid);events.append({'state_id':sid,'status':'INFRA_FAILURE_NOT_COMMITTED'});del running[sid];continue
            if not dest.exists():
                status='TIMEOUT_INCONCLUSIVE' if code=='TIMEOUT' else 'EXECUTION_ERROR'
                failure={'state_id':sid,'freeze_sha':lock['freeze_sha'],'status':status,'reason':f'child exit {code} after {elapsed:.0f}s',
                         'setting_id':state['run']['setting_id'],'family':state['run']['model']['family'],
                         'seed':str(state['run']['seed']),'checkpoint':state['checkpoint_index'],'conditions':[],'wall_seconds':elapsed}
                partial=out/'partials'/f'{sid}.json'
                if partial.exists():
                    saved=read_json(partial);validate_result_identity(saved,lock['freeze_sha'],sid)
                    failure={**saved,**{k:v for k,v in failure.items() if k!='conditions'}}
                write_json(dest,failure)
            events.append({'state_id':sid,'status':read_json(dest)['status'],'wall_seconds':elapsed})
            del running[sid]
    with execution_lock(out):
        write_json(out/'DRIVER.json',{'pid':os.getpid(),'started':utc_now(),'workers':args.workers,'device':args.device,
                                        'argv':sys.argv,'stop':'create STOP file in output root'})
        last=0.
        while True:
            reap()
            halting=stop.exists() or bool(args.deadline_epoch and time.time()>args.deadline_epoch)
            ok=qualified_conditions(lock,out)
            todo=[]
            for state in planned:
                sid=state['state_id']
                if committed(sid) or sid in running or sid in skipped or not source_ready(lock,state):continue
                fam=state['run']['model']['family']
                if sid in qids.values():todo.append((state,list(lock['config']['gammas'])));continue
                gam=[g for g in lock['config']['gammas'] if (fam,float(g)) in ok]
                if gam:todo.append((state,gam))
            # Q0 states first so families are released early; otherwise frozen plan order (stable sort).
            todo.sort(key=lambda t:t[0]['state_id'] not in qids.values())
            if not halting:
                for state,gam in todo:
                    if len(running)>=args.workers:break
                    launch(state,gam)
            if time.time()-last>10:
                write_json(out/'DRIVER_HEARTBEAT.json',{'pid':os.getpid(),'time':time.time(),'running':{k:v['pid'] for k,v in running.items()},
                    'committed':len(list((out/'results').glob('*.json'))),'halting':halting,'queue_remaining':len(todo)})
                last=time.time()
            if not running and (halting or not todo):break
            time.sleep(1)
        write_json(out/'invocations'/f'{time.time_ns()}.json',{'events':events,'qualified_conditions':sorted(map(list,qualified_conditions(lock,out)))})
    return {'executed_states':len(events),'events':events[-5:],'halted_by_stop_or_deadline':stop.exists()}

def run(args):
    if not args.approve_compute:raise ValueError('Real assays require --approve-compute; no source process is stopped automatically')
    if args.max_states<1:raise ValueError('--max-states must be positive')
    from .safety import require_exclusive,execution_lock
    lock=validate_freeze(args.out,PACKAGE)
    if args.device!=lock['execution_device']:raise ValueError('Device differs from follow-up freeze; use a separate execution root')
    require_exclusive(args.device)
    out=args.out.resolve();assert_separate(out,[lock['inputs']['source'],lock['inputs']['bundle'],lock['inputs']['run_root'],PACKAGE])
    planned=lock['plan']['states'];qids=set(qualify_ids(lock).values());eligible=qualified_families(lock,out)
    count=0;events=[]
    with execution_lock(out):
        for state in planned:
            sid=state['state_id'];dest=out/'results'/f'{sid}.json'
            if dest.exists():
                validate_result_identity(read_json(dest),lock['freeze_sha'],sid);continue
            if args.qualification and sid not in qids:continue
            if not args.qualification and state['run']['model']['family'] not in eligible:
                events.append({'state_id':sid,'status':'WAITING_FAMILY_QUALIFICATION'});continue
            receipt=Path(lock['inputs']['run_root'])/'checkpoints'/state['run']['run_id']/'training_receipt.json'
            if not receipt.is_file() or read_json(receipt).get('status')!='COMPLETE':
                events.append({'state_id':sid,'status':'SOURCE_TRAINING_NOT_READY_NO_REPLACEMENT'});continue
            require_exclusive(args.device)
            logdir=out/'logs';logdir.mkdir(parents=True,exist_ok=True)
            cmd=[sys.executable,'-B','-m','genesis_next','_child','--out',str(out),
                 '--state-id',sid,'--device',args.device,'--approve-compute']
            env=os.environ.copy();env['PYTHONPATH']=str(PACKAGE);env['PYTHONDONTWRITEBYTECODE']='1'
            start=time.monotonic()
            with (logdir/f'{sid}.log').open('w',encoding='utf-8') as log:
                try:
                    completed=subprocess.run(cmd,cwd=str(PACKAGE),env=env,stdout=log,stderr=subprocess.STDOUT,
                                             timeout=lock['config']['state_timeout_seconds'])
                    if completed.returncode!=0 and not dest.exists():raise RuntimeError('Child failed; see '+str(logdir/f'{sid}.log'))
                except (subprocess.TimeoutExpired,RuntimeError) as exc:
                    # subprocess.run kills only its own assay child on timeout; never source v2 processes.
                    failure={'state_id':sid,'freeze_sha':lock['freeze_sha'],'status':'TIMEOUT_INCONCLUSIVE' if isinstance(exc,subprocess.TimeoutExpired) else 'EXECUTION_ERROR',
                             'reason':str(exc),'setting_id':state['run']['setting_id'],'family':state['run']['model']['family'],
                             'seed':str(state['run']['seed']),'checkpoint':state['checkpoint_index'],'conditions':[],
                             'wall_seconds':time.monotonic()-start}
                    partial=out/'partials'/f'{sid}.json'
                    if partial.exists():
                        saved=read_json(partial);validate_result_identity(saved,lock['freeze_sha'],sid)
                        failure={**saved,**{k:v for k,v in failure.items() if k!='conditions'}}
                    write_json(dest,failure)
            count+=1;events.append({'state_id':sid,'status':read_json(dest)['status'] if dest.exists() else 'NO_RESULT'})
            if count>=min(args.max_states,lock['config']['max_states_per_invocation']):break
        stamp=time.time_ns();write_json(out/'invocations'/f'{stamp}.json',{'events':events,'executed':count,'qualified_families':qualified_families(lock,out)})
    return {'executed_states':count,'events':events,'qualified_families':qualified_families(lock,out),
            'note':'Missing source states retained; no replacement. Subsequent invocations resume only untouched states.'}

def child(args):
    if not args.approve_compute:raise ValueError('Child requires compute authorization')
    active=args.out/'ACTIVE.lock'
    if not active.exists() or not is_ancestor(read_json(active).get('pid')):
        raise ValueError('Internal child must be launched by the verified, exclusive parent runner')
    lock=validate_freeze(args.out,PACKAGE)
    if args.device!=lock['execution_device']:raise ValueError('Child device differs from freeze')
    matches=[s for s in lock['plan']['states'] if s['state_id']==args.state_id]
    if len(matches)!=1:raise ValueError('Unknown state ID')
    state=matches[0];dest=args.out/'results'/f'{args.state_id}.json'
    allowed=[float(x) for x in args.gammas.split(',') if x] or None
    if dest.exists():raise ValueError('Never overwrite a committed follow-up result')
    try:
        from .assay import assay_state
        result=assay_state(lock,state,args.device,args.out,gammas=allowed)
    except Exception as e:
        traceback.print_exc()
        result={'state_id':args.state_id,'freeze_sha':lock['freeze_sha'],'status':'EXECUTION_ERROR',
                'reason':repr(e),'setting_id':state['run']['setting_id'],'family':state['run']['model']['family'],
                'seed':str(state['run']['seed']),'checkpoint':state['checkpoint_index'],'conditions':[]}
    partial=args.out/'partials'/f'{args.state_id}.json'
    if result['status']=='EXECUTION_ERROR' and partial.exists():
        saved=read_json(partial);validate_result_identity(saved,lock['freeze_sha'],args.state_id)
        result={**saved,**{k:v for k,v in result.items() if k!='conditions'}}
    write_json(dest,result);return {'state_id':args.state_id,'status':result['status']}

def main(argv=None):
    args=parser().parse_args(argv)
    try:
        if args.command=='verify-package':answer=package_check()
        elif args.command=='demo':
            from .demo import demonstrate
            assert_separate(args.out,[PACKAGE,args.bundle,args.run_root]);answer=demonstrate(args.out)
        elif args.command in ('inspect','plan','reproduce','freeze'):
            source=args.source or args.bundle/'07_SOURCE/executed_source'
            manifest=verify_bundle(args.bundle)
            if manifest['status']!='PASS':raise ValueError('Bundle SHA failure: '+str(manifest['bad'][:10]))
            original=read_json(args.bundle/'01_PROTOCOL/protocol_lock/protocol-lock.json')
            verify_source(source,original)
            cfg=read_json(args.config);plan=make_plan(original,cfg)
            assert_separate(args.out,[args.bundle,source,args.run_root,PACKAGE])
            if args.command=='inspect':
                from .safety import process_inventory,source_processes
                try:processes={'workers':source_processes(process_inventory())}
                except Exception as e:processes={'status':'UNKNOWN','reason':str(e)}
                answer={'bundle':manifest,'environment':environment(),'plan_states':plan['state_count'],
                        'plan_conditions':plan['condition_count'],'process_check':processes,'local_run_exists':args.run_root.exists(),
                        'action':'NO_COMPUTE_STARTED'}
            elif args.command=='plan':
                write_json(args.out/'PLANNED_STATES.json',plan);answer={k:v for k,v in plan.items() if k!='states'}
            elif args.command=='reproduce':
                from .snapshot import reanalyze
                target=args.out/'e0'/str(time.time_ns());answer=reanalyze(args.bundle,target);answer['output']=str(target)
            else:
                f=freeze(args.bundle,source,args.run_root,args.out,args.config,PACKAGE,args.device)
                answer={'freeze_sha':f['freeze_sha'],'states':f['plan']['state_count'],'conditions':f['plan']['condition_count']}
        elif args.command=='run':answer=run(args)
        elif args.command=='drive':answer=drive(args)
        elif args.command=='_child':answer=child(args)
        elif args.command=='summarize':
            validate_freeze(args.out,PACKAGE)
            from .reporting import report
            answer=report(args.out)
        print(json.dumps(answer,ensure_ascii=False,indent=2,allow_nan=False));return 0
    except Exception as e:
        print('BLOCKED: '+str(e),file=sys.stderr)
        return 2
