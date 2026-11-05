from __future__ import annotations
from pathlib import Path
import importlib.metadata
import platform
import os
from .io_utils import read_json,write_json,digest,object_digest,safe_join,code_digest,assert_separate,utc_now

def validate_config(cfg):
    if cfg.get('source_stage')!='s1':raise ValueError('Only S1 follow-up is permitted')
    if cfg.get('reference_input_policy')!='V2_FP32_BATCH_LIFTED_TO_FP64':raise ValueError('Primary oracle must preserve v2 rounded-batch values')
    if cfg.get('analysis_dtype')!='float64':raise ValueError('Follow-up reference must use full FP64 operator')
    if cfg.get('group_schema')!='coarse':raise ValueError('No duplicated fine partition')
    if cfg.get('checkpoints')!=[1,3]:raise ValueError('This version preselects checkpoints 1 and 3')
    if cfg.get('gammas')!=[.001,.01,.1]:raise ValueError('Do not change the damping panel after inspection')
    if cfg.get('threads')!=2:raise ValueError('DLN source data require the recorded two-thread environment')
    if any(x<=0 for x in cfg['cg_steps']):raise ValueError('Invalid CG steps')
    return cfg

def make_plan(lock,cfg):
    if cfg.get('source_stage')!='s1':raise ValueError('S2 is sealed to follow-up selection')
    states=[]
    for sid in cfg['settings']:
        for si in cfg['seed_indices']:
            matches=[r for r in lock['runs'] if r['stage']=='s1' and r['setting_id']==sid and r['seed_index']==si]
            if len(matches)!=1:raise ValueError(f'Missing/duplicate predeclared S1 run {sid} seed index {si}')
            r=matches[0]
            for ck in cfg['checkpoints']:
                item={'run':r,'checkpoint_index':ck}
                states.append({'state_id':object_digest(item)[:24],**item})
    return {'status':'PLANNED_NOT_EXECUTED','states':states,'state_count':len(states),
            'condition_count':len(states)*len(cfg['gammas']),'missing_policy':'No replacement',
            'interpretation':'S1 reuse is exploratory, not independent confirmation'}

def verify_source(source,lock):
    source=Path(source).resolve();files=lock.get('source',{}).get('files',[])
    if not files:raise ValueError('Source manifest absent from protocol lock')
    bad=[]
    for r in files:
        p=safe_join(source,r['path'])
        if not p.is_file() or digest(p)!=r['sha256']:bad.append(r['path'])
    if bad:raise ValueError('Executed-source identity mismatch: '+', '.join(bad[:8]))
    return {'checked':len(files),'source_manifest_sha':object_digest(files)}

def environment():
    versions={}
    for pkg in ('numpy','torch','scipy','safetensors','scikit-learn'):
        try:versions[pkg]=importlib.metadata.version(pkg)
        except importlib.metadata.PackageNotFoundError:versions[pkg]=None
    return {'python':platform.python_version(),'platform':platform.platform(),'packages':versions,
            'thread_environment':{k:os.environ.get(k) for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','CUBLAS_WORKSPACE_CONFIG')}}

def freeze(bundle,source,run_root,output,config,package,device="cuda:0"):
    bundle,source,run_root,output=map(lambda p:Path(p).resolve(),(bundle,source,run_root,output))
    assert_separate(output,[bundle,source,run_root,package]);cfg=validate_config(read_json(config))
    lockpath=bundle/'01_PROTOCOL/protocol_lock/protocol-lock.json';lock=read_json(lockpath)
    verify_source(source,lock);plan=make_plan(lock,cfg)
    live_lock=run_root/'protocol-lock.json'
    if not live_lock.is_file() or digest(live_lock)!=digest(lockpath):
        raise ValueError('Live protocol-lock bytes differ from the immutable audit snapshot')
    payload={'schema':1,'study_id':cfg['study_id'],'created_at':utc_now(),'config':cfg,
             'inputs':{'bundle':str(bundle),'source':str(source),'run_root':str(run_root),
                       'protocol_lock_sha256':digest(lockpath),'bundle_manifest_sha256':digest(bundle/'09_MANIFEST/FILE_MANIFEST_SHA256.csv')},
             'code':code_digest(package),'environment':environment(),'plan':plan,
             'execution_device':device,'evidence_class':'EXPLORATORY_S1_FOLLOWUP_NOT_ORIGINAL_V2'}
    payload['freeze_sha']=object_digest(payload)
    path=output/'FOLLOWUP_LOCK.json'
    if path.exists():
        existing=read_json(path)
        # A fresh timestamp must not silently revise a freeze. Return only if inputs/settings/code match.
        for k in ('config','inputs','code','environment','plan','execution_device'):
            if existing[k]!=payload[k]:raise ValueError('Existing follow-up lock differs; use a new output root')
        return existing
    write_json(path,payload);return payload

def validate_freeze(output,package):
    lock=read_json(Path(output)/'FOLLOWUP_LOCK.json')
    if object_digest({k:v for k,v in lock.items() if k!='freeze_sha'})!=lock['freeze_sha']:
        raise ValueError('Follow-up lock was modified')
    if code_digest(package)!=lock['code']:raise ValueError('Runner source changed after freeze')
    if environment()!=lock['environment']:raise ValueError('Follow-up environment changed; no silent fallback')
    i=lock['inputs'];live=Path(i['run_root'])/'protocol-lock.json'
    if digest(live)!=i['protocol_lock_sha256']:raise ValueError('Original v2 protocol identity changed')
    original=read_json(live);verify_source(i['source'],original)
    return lock

def validate_result_identity(result,freeze_sha,state_id):
    if result.get('freeze_sha')!=freeze_sha or result.get('state_id')!=state_id:
        raise ValueError('Result identity mismatch; do not overwrite/reuse')
