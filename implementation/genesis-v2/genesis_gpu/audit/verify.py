"""Readback and alternate-algorithm audit; never calls the main summary writer."""
from __future__ import annotations
from pathlib import Path
import math
import json
import hashlib
import numpy as np
import torch
from scipy.sparse.linalg import LinearOperator,cg as scipy_cg
from genesis_gpu.runtime.queue import JobStore
from genesis_gpu.runtime.atomic_io import read_json,atomic_json,verify_receipt,file_receipt,source_manifest,sha256_file
from genesis_gpu.training.checkpoint import load_state
from genesis_gpu.runtime.measurement import rebuild_snapshot
from genesis_gpu.audit.independent_reference import independent_ggn_vector,dense_reference
from genesis_gpu.env.reproducibility import code_root
from genesis_gpu.contracts import object_sha


def _relative(a,b):return float((a-b).norm()/b.norm().clamp_min(1e-30))


def _verify_scalar_identities(record):
    u=record['utility'];errors=[]
    if u.get('delta') is not None and all(k in u for k in ('raw_g_dot_full','raw_g_dot_block','raw_block_dot_Qblock')):
        a=u['raw_g_dot_full'];b=u['raw_g_dot_block'];c=u['raw_block_dot_Qblock']
        eta=(b*b/c)/(-a);delta=max(0.,1-eta)
        if abs(delta-u['delta'])>1e-8 or abs(eta-u['eta_raw'])>1e-8:errors.append('quadratic value disagrees with raw dot products')
    if u.get('E_task') is not None:
        uu,vv,uv=u['raw_train_uWu'],u['raw_train_vWv'],u['raw_train_uWv'];alpha=max(0,uv/vv)
        val=math.sqrt(max(0,(uu-2*alpha*uv+alpha*alpha*vv)/uu))
        if abs(alpha-u['alpha_task'])>1e-7 or abs(val-u['E_task'])>5e-6:errors.append('weighted task projection disagrees')
    s=record.get('structure')
    if s and s.get('energy_mean'):
        E=np.asarray(s['energy_mean']);sizes=np.asarray(s['group_sizes']);L=len(E)
        bins=[];entries=[]
        for k in range(L):
            pairs=[(i,j) for i in range(L) for j in range(L) if abs(i-j)==k]
            bins.append(sum(E[i,j] for i,j in pairs));entries.append(sum(sizes[i]*sizes[j] for i,j in pairs))
        c=np.sqrt(np.asarray(bins)/entries);c=c/c[0]
        stored=s['raw_profile']
        if not np.allclose(c,stored['normalized_element_rms'],rtol=1e-9,atol=1e-12):errors.append('distance profile disagrees with raw block energies')
        if abs(sum(bins[1:])/sum(bins)-stored['offdiag_mass'])>1e-9:errors.append('offdiagonal energy identity failed')
    return errors


def _replay(record,cfg,root):
    op,val,provenance=rebuild_snapshot(record['payload'],cfg,root)
    if provenance['operator_identity']!=record['provenance']['operator_identity']:raise RuntimeError('Independent snapshot identity changed')
    generator=torch.Generator(device=op.theta.device);generator.manual_seed(918273)
    v=torch.randn(op.theta.shape,dtype=op.theta.dtype,device=op.theta.device,generator=generator)
    alt=independent_ggn_vector(op,v);direct=op.raw_ggn(v);error=_relative(direct,alt)
    tolerance=1e-7 if op.theta.dtype==torch.float64 else 2e-3
    receipt={'job_id':record['job_id'],'independent_GGNv_relative':error,'operator_agreement':error<tolerance,
             'method':'reverse-over-reverse JVP plus manually reduced loss-output Hessian, independent of functional JVP implementation',
             'probe_replay':None}
    structure=record.get('structure')
    if structure and structure.get('probe_artifact'):
        path=Path(root)/structure['probe_artifact']['path'];raw=read_json(path)
        probes=raw['final']
        if probes:
            sample=probes[0];ids=op.layout.group_indices(record['schema'],device=op.theta.device)
            rng=torch.Generator(device=op.theta.device);rng.manual_seed(sample['seed'])
            z=torch.zeros_like(op.theta);idx=ids[sample['source']]
            z[idx]=(torch.randint(0,2,(len(idx),),device=z.device,generator=rng)*2-1).to(z.dtype)
            lam=record['lambda_absolute'];n=len(z)
            if n<=cfg['solver']['dense_limit'] and op.prediction.numel()<=4096:
                ref=dense_reference(op,with_hessian=False,parameter_limit=cfg['solver']['dense_limit'])
                solution=torch.linalg.solve(ref['G']+lam*torch.eye(n,device=z.device,dtype=z.dtype),z);info=0
                method='independent reverse-autograd dense GGN + direct solve'
            else:
                def mv(a):
                    t=torch.as_tensor(a,device=z.device,dtype=z.dtype)
                    return (independent_ggn_vector(op,t)+lam*t).cpu().double().numpy()
                A=LinearOperator((n,n),matvec=mv,dtype=np.float64)
                array,info=scipy_cg(A,z.cpu().double().numpy(),rtol=cfg['solver']['rtol'],maxiter=cfg['solver']['max_iter']*3)
                solution=torch.as_tensor(array,device=z.device,dtype=z.dtype);method='SciPy CG with independently differentiated GGN action'
            energies=np.array([float(solution[ii].square().sum()) for ii in ids]);old=np.array(sample['energy'])
            allowance=np.array(sample['energy_error_bound'])+np.maximum(abs(old)*5e-3,1e-12)
            raw_g=independent_ggn_vector(op,z)
            g_energies=np.array([float(raw_g[ii].square().sum()) for ii in ids])
            good_g=np.allclose(g_energies,sample['GGN_energy'],rtol=3e-3 if z.dtype==torch.float32 else 1e-7,atol=1e-10)
            good=info==0 and bool(np.all(abs(energies-old)<=allowance)) and bool(good_g)
            receipt['probe_replay']={'method':method,'source':sample['source'],'seed':sample['seed'],'solver_info':int(info),
                                     'energy':energies.tolist(),'saved_energy':old.tolist(),'absolute_tolerance':allowance.tolist(),'raw_GGN_energies_match':bool(good_g),'passed':good}
    receipt['passed']=receipt['operator_agreement'] and (receipt['probe_replay'] is None or receipt['probe_replay']['passed'])
    return receipt


def verify_study(cfg,root,*,replay=True,all_records=True):
    root=Path(root);errors=[];checks=[];replays=[];references=[]
    lock=read_json(root/'protocol-lock.json');store=JobStore(root/'run_status.sqlite')
    try:rows=store.rows();counts=store.counts();digests={s:store.evidence_digest(s) for s in ('s1','s2')}
    finally:store.close()
    # Strict binding when a real lock (rather than a corruption test fixture) is present.
    if 'source' in lock:
        from genesis_gpu.study.freeze import verify_lock
        try: verify_lock(cfg,root)
        except Exception as exc: errors.append('Frozen execution identity invalid: '+repr(exc))
        if source_manifest(code_root())['sha256']!=lock['source']['sha256']:errors.append('Source drift since protocol freeze')
        if object_sha(cfg)!=lock['config_sha']:errors.append('Config drift since protocol freeze')
        if object_sha({k:v for k,v in lock.items() if k!='protocol_sha'})!=lock['protocol_sha']:errors.append('Lock content hash invalid')
    seeds={};selected={}
    for run in lock['runs']:
        if run['seed'] in seeds:errors.append('Repeated independent training seed')
        seeds[run['seed']]=run['stage']
    for row in rows:
        result=row.get('result') or {};entry=result.get('receipt')
        if row['state']=='COMPLETE' and not entry:errors.append('Completed job lacks receipt '+row['id'])
        if not entry:continue
        if not verify_receipt(root,entry):errors.append('Hash mismatch '+entry['path']);continue
        references.append(entry);record=read_json(root/entry['path'])
        try:
            if row['kind']=='train':
                for ck in record['checkpoints']:
                    state,meta=load_state(root/ck['path'],ck['integrity_sha'])
                    if meta['run_id']!=row['payload']['run']['run_id']:errors.append('Checkpoint run identity mismatch')
            elif row['kind']=='measure':
                if record['provenance']['protocol_sha']!=lock['protocol_sha']:errors.append('Measurement protocol mismatch')
                for artifact in record['artifacts']:
                    if not verify_receipt(root,artifact):errors.append('Raw measurement corruption '+artifact['path'])
                errors.extend(f"{row['id']}: {e}" for e in _verify_scalar_identities(record))
                checks.append({'job_id':row['id'],'scalar_identities_checked':True,'status':record['status']})
                key=(record['provenance']['stage'],record['family'])
                # Deterministic predeclared first completed deep checkpoint per family/stage.
                if key not in selected or record.get('structure') and not selected[key].get('structure'):selected[key]=record
        except Exception as exc:errors.append(f"{row['id']}: {type(exc).__name__}: {exc}")
    if replay:
        for key,record in sorted(selected.items()):
            try:
                receipt=_replay(record,cfg,root);replays.append(receipt)
                if not receipt['passed']:errors.append('Independent numerical replay failed '+record['job_id'])
            except Exception as exc:errors.append('Independent replay exception '+record['job_id']+': '+repr(exc))
    if any(r['state'] in ('PENDING','RUNNING','INTERRUPTED') for r in rows):errors.append('Execution ledger incomplete')
    both_stages=all(any(r['stage']==s for r in rows) for s in ('s1','s2'))
    if not both_stages:errors.append('Both S1 and S2 must be represented for final QA')
    for stage in ('s1','s2'):
        ap=root/'audit'/f'{stage}_adjudication.json'
        if ap.exists():
            a=read_json(ap)
            if a['jobs_digest']!=digests[stage]:errors.append('Adjudication/ledger drift '+stage)
        else:errors.append('Missing adjudication '+stage)
    receipt={'status':'QA_FAILED' if errors else ('CPU_SMOKE_QA_PASSED' if cfg['profile']=='smoke' else 'INDEPENDENT_NUMERICAL_QA_PASSED'),
             'profile':cfg['profile'],'protocol_sha':lock['protocol_sha'],'errors':errors,'counts':counts,
             'raw_scalar_checks':checks,'independent_replays':replays,'replay_enabled':replay,
             'artifact_count':len(references),'artifacts_verified':references,'jobs_digest':digests,
             'reviewer_type':'independent code path executed; author self-review, not a separate human/model reviewer',
             'scientific_conclusion_certified':False}
    if not replay and not errors:receipt['status']='HASH_ONLY_NOT_INDEPENDENT_QA'
    atomic_json(root/'audit'/'INDEPENDENT_VERIFIER_RECEIPT.json',receipt)
    return receipt
