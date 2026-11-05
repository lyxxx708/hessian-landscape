import json
from pathlib import Path
W=Path(r'E:\GENESIS\worktrees\genesis-next-v2')

p=W/'genesis_next/safety.py'; s=p.read_text(encoding='utf-8')
s=s.replace("""def require_exclusive(device):
    busy=source_processes(process_inventory())""","""def require_exclusive(device):
    # CPU assays only read COMPLETE v2 receipts and cannot contend for the v2 GPU: no process gate needed.
    if not device.startswith('cuda'):return {'v2_processes':'NOT_CHECKED_CPU_READ_ONLY','gpu_check':'CPU_ONLY'}
    busy=source_processes(process_inventory())""")
p.write_text(s,encoding='utf-8')

(W/'genesis_next/ledger.py').write_text('''"""Per-(state,gamma) condition ledger. Committed results are never rewritten."""
from __future__ import annotations

def condition_ledger(lock,results,source_ready,running=()):
    rows=[]
    for st in lock['plan']['states']:
        sid=st['state_id'];r=results.get(sid);run=st['run']
        by={float(c['gamma']):c for c in (r or {}).get('conditions',[])}
        for g in lock['config']['gammas']:
            c=by.get(float(g))
            if c is not None:
                status='NUMERIC_VALID' if c['status']=='QUALIFIED' else 'NUMERIC_UNRESOLVED'
            elif r is not None and r.get('status')=='TIMEOUT_INCONCLUSIVE':status='TIMEOUT_INCONCLUSIVE'
            elif r is not None and r.get('status')=='EXECUTION_ERROR':status='FAILED'
            elif r is not None and r.get('status')=='EXECUTED':status='READY'
            elif sid in running:status='RUNNING'
            elif not source_ready.get(sid,False):status='SOURCE_NOT_READY'
            else:status='READY'
            rows.append({'state_id':sid,'family':run['model']['family'],'setting_id':run['setting_id'],
                         'seed_index':run['seed_index'],'checkpoint':st['checkpoint_index'],'gamma':g,'status':status,
                         'reason':(c or {}).get('reason') or (r or {}).get('reason')})
    return rows
''',encoding='utf-8')

p=W/'genesis_next/cli.py'; s=p.read_text(encoding='utf-8')
s=s.replace("PACKAGE=Path(__file__).resolve().parents[1]","PACKAGE=Path(__file__).resolve().parents[1]\nOUT=Path(r'E:\\GENESIS\\runs\\genesis_next_v2')")
s=s.replace("default=Path(r'E:\\GENESIS\\runs\\genesis_next_v1')","default=OUT").replace("PACKAGE/'configs/protocol.json'","PACKAGE/'configs/protocol_v2.json'")
s=s.replace("'freeze','run','summarize'","'freeze','run','drive','summarize'")
s=s.replace("if name in ('run','_child','freeze'):","if name in ('run','drive','_child','freeze'):")
s=s.replace("        if name=='_child':s.add_argument('--state-id',required=True)","""        if name=='drive':
            s.add_argument('--workers',type=int,default=4);s.add_argument('--deadline-epoch',type=float,default=None)
        if name=='_child':
            s.add_argument('--state-id',required=True);s.add_argument('--gammas',default='')""")
NEW='''def qualified_conditions(lock,output):
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
    logdir=out/'logs';logdir.mkdir(parents=True,exist_ok=True);stop=out/'STOP';running={};events=[]
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
                if committed(sid) or sid in running or not source_ready(lock,state):continue
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

def run(args):'''
s=s.replace("def run(args):",NEW,1)
s=s.replace("    state=matches[0];dest=args.out/'results'/f'{args.state_id}.json'","    state=matches[0];dest=args.out/'results'/f'{args.state_id}.json'\n    allowed=[float(x) for x in args.gammas.split(',') if x] or None")
s=s.replace("result=assay_state(lock,state,args.device,args.out)","result=assay_state(lock,state,args.device,args.out,gammas=allowed)")
s=s.replace("        elif args.command=='run':answer=run(args)","        elif args.command=='run':answer=run(args)\n        elif args.command=='drive':answer=drive(args)")
p.write_text(s,encoding='utf-8')

c=json.load(open(W/'configs/protocol.json'))
c['study_id']='genesis_next_v2';c['state_timeout_seconds']=1800;c['max_states_per_invocation']=80
c['evidence_class_note']='POSTHOC_S1_EXPLORATORY_NOT_CONFIRMATION; inherits NEXT v1 sample frame; no S2'
json.dump(c,open(W/'configs/protocol_v2.json','w'),indent=2)
print('patched')
