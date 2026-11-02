"""Read-only frozen-checkpoint assays with replayable scalar raw evidence."""
from __future__ import annotations
from dataclasses import asdict
from pathlib import Path
import time
import copy
import io
import numpy as np
import torch
from safetensors.torch import save as safe_tensor_bytes
from genesis_gpu.contracts import RunSpec,LossSpec,object_sha
from genesis_gpu.models.registry import build_model
from genesis_gpu.datasets.registry import load_bundle
from genesis_gpu.training.checkpoint import load_state,IntegrityError
from genesis_gpu.curvature.operators import FrozenOperator
from genesis_gpu.curvature.params import tensor_dict_sha,tensor_sha
from genesis_gpu.curvature.spectrum import power_scale,lanczos
from genesis_gpu.science.utility import evaluate_utility
from genesis_gpu.science.mechanism import dense_mechanism,dln_gauge_controls
from genesis_gpu.science.controls import order_null
from genesis_gpu.solvers.cg import cg
from genesis_gpu.sketches.block_probe import estimate_blocks
from genesis_gpu.study.design import seed_for
from genesis_gpu.runtime.atomic_io import atomic_json,atomic_bytes,read_json,file_receipt,verify_receipt


def rebuild_snapshot(payload,cfg,root):
    """Same dataset hash, fixed loss/batch and exact logical parameters for every assay."""
    root=Path(root);run=RunSpec.from_dict(payload['run'])
    receipt=read_json(root/'checkpoints'/run.run_id/'training_receipt.json')
    if receipt['status']!='COMPLETE' or receipt['run_spec_sha']!=object_sha(run):
        raise IntegrityError('A completed matching training trajectory is required')
    selected=[c for c in receipt['checkpoints'] if c['index']==payload['checkpoint_index']]
    if len(selected)!=1:raise IntegrityError('Missing or duplicate fixed checkpoint')
    checkpoint=selected[0]
    state,meta=load_state(root/checkpoint['path'],checkpoint['integrity_sha'])
    bundle=load_bundle(run,cfg,root)
    if bundle.fingerprint!=receipt['data_sha'] or meta['model_sha']!=tensor_dict_sha(state['model']):
        raise IntegrityError('Checkpoint/data SHA mismatch')
    device=torch.device(cfg['device']);dtype=getattr(torch,cfg['analysis_dtype'])
    model=build_model(run.model,run.seed).to(device=device,dtype=dtype)
    model.load_state_dict(state['model'],strict=True)
    batch_seed=seed_for('FROZEN_CURVATURE_BATCH_V2',run.seed)
    x,y=bundle.batch('train',step=0,count=cfg['curvature_batch'],seed=batch_seed,device=device,dtype=dtype,augment=False)
    xv,yv=bundle.batch('validation',step=0,count=cfg['curvature_batch'],seed=seed_for('FROZEN_VALIDATION_BATCH_V2',run.seed),device=device,dtype=dtype)
    loss=LossSpec(**meta['loss_spec'])
    op=FrozenOperator(model,x,y,loss,microbatch=cfg['curvature_microbatch'])
    val=FrozenOperator(model,xv,yv,loss,microbatch=cfg['curvature_microbatch'])
    provenance={'run_id':run.run_id,'setting_id':run.setting_id,'stage':run.stage,'seed':run.seed,'seed_index':run.seed_index,
                'checkpoint_index':payload['checkpoint_index'],'checkpoint_step':checkpoint['step'],
                'checkpoint_path':checkpoint['path'],'checkpoint_integrity_sha':checkpoint['integrity_sha'],
                'model_sha':checkpoint['model_sha'],'data_sha':bundle.fingerprint,'batch_seed':batch_seed,
                'operator_identity':op.identity,'validation_identity':val.identity,
                'model_spec':asdict(run.model),'loss_spec':asdict(loss),'weight_decay_training':run.train.weight_decay,
                'analysis_objective':'deterministic data loss, excludes optimizer weight decay',
                'groups_sha':object_sha(op.layout.schemas),'parameters':len(op.theta)}
    return op,val,provenance


def _cached_scale(op,provenance,cfg,root,callback):
    key=object_sha({'snapshot':op.identity,'iterations':cfg['power_iterations']})
    path=Path(root)/'measurements'/'spectral_scales'/f'{key}.json'
    if path.exists():
        receipt=read_json(path)
        if receipt['snapshot_sha']!=object_sha(op.identity):raise IntegrityError('Spectral scale identity mismatch')
        if not verify_receipt(root,receipt['value_receipt']):raise IntegrityError('Spectral scale data corrupted')
        return read_json(Path(root)/receipt['value_receipt']['path'])
    value=power_scale(op,cfg['power_iterations'],seed_for('POWER',provenance['seed'],provenance['checkpoint_index']),callback)
    vp=path.with_name(key+'_value.json');atomic_json(vp,value)
    atomic_json(path,{'snapshot_sha':object_sha(op.identity),'value_receipt':file_receipt(vp,root)})
    return value


def measure_job(payload,cfg,root,job_id,protocol_sha,callback=None):
    root=Path(root);destination=root/'measurements'/job_id;result_file=destination/'result.json'
    if result_file.exists():
        r=read_json(result_file)
        if r['provenance']['protocol_sha']!=protocol_sha or r['payload_sha']!=object_sha(payload):
            raise IntegrityError('Measurement identity changed')
        for entry in r['artifacts']:
            if not verify_receipt(root,entry):raise IntegrityError('Committed measurement artifact corrupted')
        return r
    start=time.perf_counter();op,val,pv=rebuild_snapshot(payload,cfg,root)
    if callback:callback()
    scale=_cached_scale(op,pv,cfg,root,callback)
    damping=payload['gamma']*max(scale['value'],cfg['damping_floor'])
    pv.update(protocol_sha=protocol_sha,source_config_sha=object_sha(cfg))
    solver=cfg['solver']
    utility,vectors=evaluate_utility(op,damping,schema=payload['schema'],rtol=solver['rtol'],max_iter=solver['max_iter'],
        validation=val,line_search=cfg['line_search'],stability_factor=solver['stability_factor'],delta_stability=solver['delta_stability'],
        preconditioner_probes=solver['preconditioner_probes'],short_steps=solver['short_cg_steps'],callback=callback)
    destination.mkdir(parents=True,exist_ok=True);artifacts=[]
    # Scalar identities are sufficient for every quadratic metric; keep vector subset for independent replay.
    save_vectors=payload['tier']=='C_DEEP' or payload['checkpoint_index']==3 and pv['seed_index']==0
    if save_vectors and vectors:
        path=destination/'directions.safetensors'
        atomic_bytes(path,safe_tensor_bytes({k:v.detach().cpu().contiguous() for k,v in vectors.items()}))
        artifacts.append(file_receipt(path,root))
    structure=None;mechanism=None
    if payload['tier'].startswith('C'):
        ids=op.layout.group_indices(payload['schema'],device=op.theta.device)
        rtol=max(solver['rtol']*solver['stability_factor'],5*torch.finfo(op.theta.dtype).eps)
        solve=lambda z:cg(lambda v:op.matvec(v,damping),z,rtol=rtol,max_iter=solver['max_iter']*2,callback=callback)
        probe_seed=seed_for('INVERSE_BLOCK_PROBES_V2',pv['seed'],pv['checkpoint_index'],payload['gamma'],payload['schema'])
        schedule=cfg['probes']['schedule']
        sketch=estimate_blocks(solve,op.raw_ggn,ids,damping,dtype=op.theta.dtype,device=op.theta.device,seed=probe_seed,
                              schedule=schedule,relative_halfwidth=cfg['probes']['relative_halfwidth'],bootstrap=cfg['probes']['bootstrap'],
                              independent_final=cfg['probes']['independent_final'],callback=callback)
        probes={'pilot':sketch.pop('pilot_records',[]),'final':sketch.pop('probe_records',[])}
        path=destination/'probes.json';atomic_json(path,probes);pr=file_receipt(path,root);artifacts.append(pr)
        structure={'status':sketch['status'],'raw_profile':sketch.pop('profile',None),
                   'correction_profile':sketch.pop('correction_profile',None),'probe_artifact':pr,'probe_seed':probe_seed,
                   'group_sizes':op.layout.group_sizes(payload['schema']),**sketch}
        if structure.get('energy_mean') is not None:
            structure['order_null']=order_null(structure['energy_mean'],structure['group_sizes'],
                                              permutations=199 if cfg['profile']=='full' else 19,seed=probe_seed%2**32)
        if payload['tier']=='C_DEEP':
            mechanism={'exact_reference':None,'gauge_controls':[],'GGN_ritz':None,'Hessian_ritz':None}
            if len(op.theta)<=solver['dense_limit']:
                # CPU FP64 reference avoids consumer GPU double-precision performance bias.
                refop=FrozenOperator(copy.deepcopy(op.model).cpu().double(),op.inputs.cpu(),op.targets.cpu(),op.loss,
                                     microbatch=op.microbatch,dtype=torch.float64)
                mechanism['exact_reference']=dense_mechanism(refop,[g*max(scale['value'],cfg['damping_floor']) for g in cfg['damping_ratios']],solver['dense_limit'])
                mechanism['gauge_controls']=dln_gauge_controls(refop)
            else:
                mechanism['exact_reference']={'status':'NOT_APPLICABLE_DENSE_SIZE_LIMIT','parameters':len(op.theta),'limit':solver['dense_limit']}
                mechanism['GGN_ritz']=lanczos(op.raw_ggn,op.theta,steps=24,callback=callback)
                mechanism['Hessian_ritz']=lanczos(op.hvp,op.theta,steps=24,callback=callback)
                if pv['model_spec']['family']=='dln':mechanism['gauge_controls']=dln_gauge_controls(op)
    if op.theta.device.type=='cuda':torch.cuda.synchronize(op.theta.device)
    result={'schema_version':2,'job_id':job_id,'payload_sha':object_sha(payload),'payload':payload,
            'profile':cfg['profile'],'tier':payload['tier'],'status':utility['status'],
            'provenance':pv,'gamma':payload['gamma'],'lambda_absolute':damping,'spectral_scale':scale,
            'schema':payload['schema'],'family':pv['model_spec']['family'],
            'state_observations':{'loss':float(op.objective(op.theta)),'validation_loss':float(val.objective(val.theta)),
                                  'gradient_norm':float(op.gradient().norm()),'parameter_norm':float(op.theta.norm()),
                                  'operator_diagnostics':op.diagnostics()},
            'utility':utility,'structure':structure,'mechanism':mechanism,'artifacts':artifacts,
            'wall_seconds':time.perf_counter()-start,'total_GGN_matvecs':op.matvec_count,
            'evidence_class':'ENGINEERING_SMOKE_ONLY' if cfg['profile']=='smoke' else 'RECORDED_MEASUREMENT_PENDING_INDEPENDENT_QA'}
    atomic_json(result_file,result)
    return result
