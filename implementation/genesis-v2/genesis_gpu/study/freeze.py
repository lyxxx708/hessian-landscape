"""Content hashes gate execution; earlier CPU/v1 receipts never authorize production."""
from pathlib import Path
import time
from genesis_gpu.contracts import object_sha
from genesis_gpu.runtime.atomic_io import atomic_json,read_json,sha256_file,source_manifest,verify_receipt,append_jsonl
from genesis_gpu.env.reproducibility import code_root
from genesis_gpu.study.design import expand_design


def set_state(root,state,**extra):
    root=Path(root)
    old=read_json(root/'study-state.json') if (root/'study-state.json').exists() else {}
    value={**old,'state':state,'timestamp':time.time(),**extra}
    atomic_json(root/'study-state.json',value)
    append_jsonl(root/'logs'/'lifecycle.jsonl',{'state':state,'timestamp':value['timestamp'],**extra})
    return value


def freeze_protocol(cfg,root):
    root=Path(root);path=root/'protocol-lock.json'
    if path.exists():return verify_lock(cfg,root)
    gp=root/'audit'/'g0_receipt.json'
    if not gp.exists():raise RuntimeError('G0_REQUIRED: run numerical/device preflight before freeze')
    g0=read_json(gp);expected='CUDA_G0_NUMERIC_VALID' if cfg['profile']=='full' else 'CPU_SMOKE_G0_VALID'
    if g0.get('status')!=expected:raise RuntimeError('G0 class does not qualify this execution profile')
    from genesis_gpu.env.reproducibility import runtime_abi
    if g0.get('environment',{}).get('runtime_abi')!=runtime_abi():
        raise RuntimeError('G0 runtime differs from current environment; re-run before freeze')
    code=source_manifest(code_root())
    if g0.get('config_sha')!=object_sha(cfg) or g0.get('source_sha')!=code['sha256']:
        raise RuntimeError('G0 ran a different source/config; re-run it before freeze')
    if not all(verify_receipt(root,r) for r in g0['reference_artifacts']):raise RuntimeError('G0 evidence corrupted')
    dp=root/'datasets'/'manifest.json'
    if cfg['profile']=='full' and not dp.exists():raise RuntimeError('Prepared public data manifest required')
    datasets=read_json(dp) if dp.exists() else {'status':'SMOKE_SYNTHETIC_ONLY'}
    runs=expand_design(cfg)
    lock={'schema_version':2,'profile':cfg['profile'],'config':cfg,'config_sha':object_sha(cfg),'source':code,
          'runtime_abi':runtime_abi(),'g0_sha':sha256_file(gp),'datasets':datasets,'dataset_manifest_sha':sha256_file(dp) if dp.exists() else None,
          'runs':[r.to_dict() for r in runs], 'seed_sha':object_sha([r.seed for r in runs]),
          'scientific_scope':'ENGINEERING_SMOKE_ONLY' if cfg['profile']=='smoke' else 'PROSPECTIVE_FROZEN_STUDY'}
    lock['protocol_sha']=object_sha(lock)
    atomic_json(path,lock);atomic_json(root/'seed-manifest.json',{'protocol_sha':lock['protocol_sha'],'runs':[{'run_id':r.run_id,'seed':r.seed,'stage':r.stage} for r in runs]})
    set_state(root,'PROTOCOL_FROZEN',profile=cfg['profile'],protocol_sha=lock['protocol_sha'])
    return lock


def verify_lock(cfg,root):
    root=Path(root);path=root/'protocol-lock.json'
    if not path.exists():raise RuntimeError('PROTOCOL_NOT_FROZEN')
    lock=read_json(path);payload={k:v for k,v in lock.items() if k!='protocol_sha'}
    if object_sha(payload)!=lock['protocol_sha']:raise RuntimeError('Protocol lock tampered')
    if object_sha(cfg)!=lock['config_sha']:raise RuntimeError('Config changed after freeze')
    from genesis_gpu.env.reproducibility import runtime_abi
    if lock.get('runtime_abi')!=runtime_abi():raise RuntimeError('runtime changed after freeze; new G0/protocol required')
    if source_manifest(code_root())['sha256']!=lock['source']['sha256']:raise RuntimeError('Source changed after freeze; no silent scientific revision')
    if sha256_file(root/'audit'/'g0_receipt.json')!=lock['g0_sha']:raise RuntimeError('G0 receipt changed after freeze')
    if lock['dataset_manifest_sha']:
        if sha256_file(root/'datasets'/'manifest.json')!=lock['dataset_manifest_sha']:raise RuntimeError('Dataset manifest changed')
    return lock


def require_stage_access(root,stage):
    root=Path(root)
    if stage=='s1':
        if not (root/'protocol-lock.json').exists():raise RuntimeError('Freeze first')
        return
    if stage not in ('s2','s3'):raise ValueError('Unknown study stage')
    previous='s1' if stage=='s2' else 's2';path=root/'audit'/f'{previous}_adjudication.json'
    if not path.exists():raise RuntimeError(f'{stage.upper()}_SEALED: prior adjudication missing')
    lock=read_json(root/'protocol-lock.json');receipt=read_json(path)
    if receipt.get('protocol_sha')!=lock['protocol_sha'] or not receipt.get('execution_complete'):
        raise RuntimeError('Prior evidence not complete under this protocol')
    from genesis_gpu.runtime.queue import JobStore
    store=JobStore(root/'run_status.sqlite')
    try:
        if not store.stage_complete(previous) or store.evidence_digest(previous)!=receipt['jobs_digest']:
            raise RuntimeError('Prior work ledger does not match adjudication')
    finally:store.close()
    if stage=='s3' and not receipt.get('s3_gate_pass',False):
        raise RuntimeError('S3_NO_GO: utility AND prediction gates did not pass')
