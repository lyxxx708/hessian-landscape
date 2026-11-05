"""Read-only real-checkpoint adapter for the inspected GENESIS v2 interfaces.
Requires the user's original data/checkpoints; never calls measure_job/run_stage/report.
"""
from __future__ import annotations
import copy
import json
import math
import sys
import time
from pathlib import Path
import numpy as np
import torch
from .io_utils import read_json,write_json,digest,safe_join,utc_now
from .solvers import cg,block_cg,public_receipt,sync
from .numerics import ray_utility,dense_geometry,hessian_diagnostics,gauge_diagnostic

def relative(a,b):
    return float((a-b).norm()/b.norm().clamp_min(torch.finfo(b.dtype).tiny))

def loss_trials(op,val,direction,steps):
    sync(direction);start=time.perf_counter();base=float(op.objective(op.theta));vb=float(val.objective(val.theta))
    values=[]
    with torch.no_grad():
        for alpha in steps:
            v=float(op.objective(op.theta+alpha*direction))
            values.append({'alpha':alpha,'loss':v if math.isfinite(v) else None})
        usable=[r for r in values if r['loss'] is not None]
        best=min(usable,key=lambda r:(r['loss'],r['alpha']))
        vv=float(val.objective(val.theta+best['alpha']*direction))
    sync(direction);gain=base-best['loss'];floor=100*torch.finfo(direction.dtype).eps*max(1.,abs(base))
    return {'train_loss':base,'train_gain':gain,'selected_alpha':best['alpha'],
            'validation_gain':vb-vv if math.isfinite(vv) else None,
            'gain_above_roundoff_heuristic':gain>floor,'roundoff_heuristic':floor,
            'trials':values,'wall_seconds':time.perf_counter()-start,'selection':'train_only'}

def dense_delta(G,g,lam,groups):
    Q=G+lam*np.eye(len(g));x=np.linalg.solve(Q,-g);b=np.zeros_like(g)
    for idx in groups:b[idx]=-np.linalg.solve(Q[np.ix_(idx,idx)],g[idx])
    u=ray_utility(Q,g,x,b);return u['delta']

def assay_state(lock,state,device,output,gammas=None):
    cfg=lock['config'];source=Path(lock['inputs']['source']);root=Path(lock['inputs']['run_root']);output=Path(output)
    torch.set_num_threads(cfg['threads'])
    torch.set_float32_matmul_precision('highest')
    torch.backends.cuda.matmul.allow_tf32=False
    torch.backends.cudnn.allow_tf32=False
    try:torch.set_num_interop_threads(1)
    except RuntimeError:pass
    sys.dont_write_bytecode=True;sys.path.insert(0,str(source))
    from genesis_gpu.runtime.measurement import rebuild_snapshot
    from genesis_gpu.curvature.operators import FrozenOperator
    from genesis_gpu.audit.independent_reference import dense_reference,independent_ggn_vector
    original=read_json(root/'protocol-lock.json');oldcfg=copy.deepcopy(original['config'])
    oldcfg.update(device=device,analysis_dtype='float64')
    payload={'run':state['run'],'checkpoint_index':state['checkpoint_index']}
    if payload['run']['stage']!='s1':raise ValueError('Never read S2 checkpoints in the follow-up')
    training_path=safe_join(root,'checkpoints/'+payload['run']['run_id']+'/training_receipt.json')
    if not training_path.is_file():raise FileNotFoundError('Planned S1 training receipt not available')
    train_before=digest(training_path)
    if read_json(training_path).get('status')!='COMPLETE':raise ValueError('Training is not COMPLETE')
    total_start=time.perf_counter()
    # PRIMARY: preserve the mathematical values of v2's actual FP32 batch.
    # Rebuilding directly in FP64 would use unrounded synthetic x/y and change
    # the mathematical problem, especially near zero residual.
    sourcecfg=copy.deepcopy(oldcfg);sourcecfg['analysis_dtype']='float32'
    source_op,source_val,pv=rebuild_snapshot(payload,sourcecfg,root)
    op=FrozenOperator(copy.deepcopy(source_op.model).double(),source_op.inputs,source_op.targets,
                      source_op.loss,microbatch=source_op.microbatch,dtype=torch.float64)
    val=FrozenOperator(copy.deepcopy(source_val.model).double(),source_val.inputs,source_val.targets,
                       source_val.loss,microbatch=source_val.microbatch,dtype=torch.float64)
    source_batch_identity=source_op.identity
    del source_op,source_val
    if len(op.theta)<=0 or op.theta.dtype!=torch.float64:raise ValueError('FP64 operator construction failed')
    if device.startswith('cuda'):torch.cuda.reset_peak_memory_stats(op.theta.device)
    sync(op.theta);gstart=time.perf_counter();g=op.gradient();sync(g);gradient_wall=time.perf_counter()-gstart
    result={'schema_version':1,'state_id':state['state_id'],'freeze_sha':lock['freeze_sha'],
      'created_at':utc_now(),'status':'EXECUTED','family':pv['model_spec']['family'],
      'setting_id':pv['setting_id'],'seed':str(pv['seed']),'seed_index':pv['seed_index'],
      'checkpoint':pv['checkpoint_index'],'provenance':pv,'training_receipt_sha256':train_before,
      'source_batch_identity':source_batch_identity,'analysis_operator_identity':op.identity,
      'reference_input_policy':cfg['reference_input_policy'],
      'device':str(op.theta.device),'dtype':str(op.theta.dtype),'gradient_norm_fp64':float(g.norm()),
      'gradient_wall_seconds':gradient_wall,'conditions':[]}
    # Write the exact analysis batch only in the NEW local output. Never publish this private file.
    inp=output/'local_inputs';inp.mkdir(parents=True,exist_ok=True);npz=inp/(state['state_id']+'.npz')
    if not npz.exists():np.savez_compressed(npz,train_x=op.inputs.cpu().numpy(),train_y=op.targets.cpu().numpy(),
                                         validation_x=val.inputs.cpu().numpy(),validation_y=val.targets.cpu().numpy())
    result['local_batch_archive']={'path':str(npz.relative_to(output)),'sha256':digest(npz),'public':False}
    if float(g.norm())<=cfg['zero_gradient_norm']:
        result.update(status='ZERO_GRADIENT_UNASSESSED',reason='Ratio metrics not numerically interpretable')
        return result
    if cfg.get('native_fp64_data_is_secondary') and result['family']=='dln':
        native,native_val,_=rebuild_snapshot(payload,oldcfg,root)
        native_g=native.gradient()
        native_op=native
        result['input_quantization_control']={
            'native_vs_lifted_gradient_relative_error':relative(native_g,g),
            'native_gradient_norm':float(native_g.norm()),
            'role':'SECONDARY: input quantization, not solver/arithmetic error'}
        del native_val,native_g
    # Same device AND same rounded batch mathematical values for FP32-vs-FP64.

    op32=FrozenOperator(copy.deepcopy(op.model).float(),op.inputs,op.targets,op.loss,
                        microbatch=op.microbatch,dtype=torch.float32)
    g32=op32.gradient().double();result['precision']={'gradient_relative_vector_error':relative(g32,g),
      'gradient_norm_fp32':float(g32.norm()),'same_device':True,'fp32_operator_errors':[]}
    gen=torch.Generator(device=op.theta.device);gen.manual_seed(20261105)
    probes=[(2*torch.randint(0,2,g.shape,generator=gen,device=g.device)-1).to(g.dtype) for _ in range(3)]
    # True alternate gradient path: full objective, not the operator's microbatch gradient loop.
    t=op.theta.detach().clone().requires_grad_(True)
    independent_g=torch.autograd.grad(op.objective(t),t)[0].detach()
    grad_error=relative(g,independent_g)
    result['reference_gradient_crosscheck']=grad_error
    operator_errors=[]
    for v in probes:
        primary=op.raw_ggn(v);alt=independent_ggn_vector(op,v)
        operator_errors.append(relative(primary,alt))
        result['precision']['fp32_operator_errors'].append(relative(op32.raw_ggn(v.float()).double(),primary))
    del op32,g32
    result['operator_crosscheck_errors']=operator_errors
    # Reconstruct the inspected v2 scheduler's deterministic IDs. Read EXACTLY
    # this S1 state's three coarse receipts; never enumerate/read S2 results.
    from genesis_gpu.contracts import object_sha
    scale_values=[]; recorded_values={}
    for gamma in cfg['gammas']:
        jid=object_sha([original['protocol_sha'],pv['run_id'],pv['checkpoint_index'],gamma,'coarse','measure'])
        p=safe_join(root,'measurements/'+jid+'/result.json')
        if not p.is_file():continue
        r=read_json(p);pr=r.get('provenance',{})
        if pr.get('stage')!='s1' or pr.get('run_id')!=pv['run_id'] or pr.get('checkpoint_index')!=pv['checkpoint_index']:
            raise ValueError('Measurement identity mismatch')
        if pr.get('checkpoint_integrity_sha')!=pv['checkpoint_integrity_sha']:
            raise ValueError('Measurement/checkpoint mismatch')
        v=r.get('spectral_scale',{}).get('value')
        if v is not None:scale_values.append(float(v))
        recorded_values[gamma]={'job_id':r['job_id'],'utility_status':r['utility']['status'],
                                'delta':r['utility'].get('delta'),'result_sha256':digest(p)}
    if not scale_values:raise FileNotFoundError('Frozen v2 spectral scale not yet measured for this state')
    if any(x!=scale_values[0] for x in scale_values):raise ValueError('Inconsistent recorded spectral scales')
    scale=scale_values[0];result['recorded_spectral_scale']=scale
    ids=op.layout.group_indices('coarse',device=g.device);groups=[x.cpu().numpy() for x in ids]
    dense=None;dense_start=time.perf_counter()
    if len(g)<=cfg['dense_parameter_limit'] and op.prediction.numel()<=cfg['dense_output_limit']:
        cpuop=FrozenOperator(copy.deepcopy(op.model).cpu().double(),op.inputs.cpu(),op.targets.cpu(),op.loss,
                             microbatch=op.microbatch,dtype=torch.float64)
        dense=dense_reference(cpuop,with_hessian=True,parameter_limit=cfg['dense_parameter_limit'],output_limit=cfg['dense_output_limit'])
        G=dense['G'].cpu().numpy();H=dense['H'].cpu().numpy();gd=dense['gradient'].cpu().numpy()
        result['dense_gradient_relative_error']=float(np.linalg.norm(g.cpu().numpy()-gd)/max(np.linalg.norm(gd),1e-300))
        G_eigensystem=np.linalg.eigh((G+G.T)/2);H_eigenvalues=np.linalg.eigvalsh((H+H.T)/2)
        result['hessian']=[hessian_diagnostics(G,H,tol,H_eigenvalues) for tol in cfg['rank_relative_tolerances']]
        # E4 inputs: dense G,g from (a) native FP64 data (input quantization) and (b) the same rounded data in FP32 arithmetic.
        e4={}
        try:
            cpu32=FrozenOperator(copy.deepcopy(op.model).cpu().float(),op.inputs.cpu().float(),op.targets.cpu().float(),op.loss,
                                 microbatch=op.microbatch,dtype=torch.float32)
            d32=dense_reference(cpu32,with_hessian=False,parameter_limit=cfg['dense_parameter_limit'],output_limit=cfg['dense_output_limit'])
            e4['fp32_arith']=(d32['G'].double().cpu().numpy(),d32['gradient'].double().cpu().numpy())
            del cpu32,d32
        except Exception as exc:e4['fp32_arith_error']=repr(exc)
        if 'native_op' in locals():
            try:
                nat=FrozenOperator(copy.deepcopy(native_op.model).cpu().double(),native_op.inputs.cpu(),native_op.targets.cpu(),native_op.loss,
                                   microbatch=native_op.microbatch,dtype=torch.float64)
                dn=dense_reference(nat,with_hessian=False,parameter_limit=cfg['dense_parameter_limit'],output_limit=cfg['dense_output_limit'])
                e4['native_input']=(dn['G'].cpu().numpy(),dn['gradient'].cpu().numpy())
                del nat,dn
            except Exception as exc:e4['native_input_error']=repr(exc)
    result['dense_reference_wall_seconds']=time.perf_counter()-dense_start
    def record_condition(condition):
        result['conditions'].append(condition)
        result['wall_seconds']=time.perf_counter()-total_start
        write_json(output/'partials'/f"{state['state_id']}.json",result)
        print(json.dumps({'state_id':state['state_id'],'gamma':condition['gamma'],'status':condition['status']}),flush=True)
    for gamma in (cfg['gammas'] if gammas is None else [x for x in cfg['gammas'] if x in gammas]):
        print(json.dumps({'state_id':state['state_id'],'gamma':gamma,'status':'STARTED'}),flush=True)
        lam=gamma*max(scale,original['config']['damping_floor']);Q=lambda v:op.matvec(v,lam)
        c={'gamma':gamma,'damping_absolute':lam,'status':'NUMERIC_UNRESOLVED','comparators':[],
           'original_v2_read_only':recorded_values.get(gamma)}
        x,rr=cg(Q,-g,rtol=cfg['reference_rtol'],max_iter=cfg['max_iterations'])
        c['full_solve']=public_receipt(rr)
        if not rr['converged']:
            c['reason']='PRIMARY_REFERENCE_NOT_CONVERGED';record_condition(c);continue
        if dense is not None:
            Qd=G+lam*np.eye(len(gd));xr=np.linalg.solve(Qd,-gd)
            xref=torch.as_tensor(xr,device=g.device,dtype=g.dtype)
            bref=np.zeros_like(gd)
            for group in groups:bref[group]=-np.linalg.solve(Qd[np.ix_(group,group)],gd[group])
            uref=ray_utility(Qd,gd,xr,bref)
            c['reference_class']='FP64_DENSE_REVERSE_AUTOGRAD'
            ev,V=G_eigensystem;invQ=(V*(1/(ev+lam)))@V.T
            c['geometry']=[dense_geometry(G,gd,lam,groups,tol,G_eigensystem,invQ) for tol in cfg['rank_relative_tolerances']]
        else:
            altQ=lambda v:independent_ggn_vector(op,v)+lam*v
            xref,ra=cg(altQ,-independent_g,rtol=cfg['reference_rtol'],max_iter=cfg['max_iterations'])
            c['alternate_full_solve']=public_receipt(ra)
            c['reference_class']='FP64_ALTERNATE_OPERATOR_CG_SHARED_MODEL'
            if not ra['converged']:
                c['reason']='ALTERNATE_REFERENCE_NOT_CONVERGED';record_condition(c);continue
        c['full_direction_relative_error']=relative(x,xref)
        if max(operator_errors)>cfg['operator_crosscheck_rtol'] or grad_error>cfg['operator_crosscheck_rtol'] or result.get('dense_gradient_relative_error',0.)>cfg['operator_crosscheck_rtol'] or c['full_direction_relative_error']>cfg['reference_solution_rtol']:
            c['reason']='INDEPENDENT_REFERENCE_DISAGREEMENT';record_condition(c);continue
        b,br=block_cg(op,g,lam,rtol=cfg['reference_rtol'],max_iter=cfg['max_iterations'])
        c['block_solve']=br
        if not br['converged']:
            c['reason']='BLOCK_SOLVE_NOT_CONVERGED';record_condition(c);continue
        sync(g);qstart=time.perf_counter();qb=Q(b);sync(g);qwall=time.perf_counter()-qstart
        F=float(-g@x-.5*x@rr['Qx']);gp=float(g@b);bqb=float(b@qb)
        if F<=0 or gp>=0 or bqb<=0:
            c['reason']='NONPOSITIVE_QUADRATIC_GAIN';record_condition(c);continue
        Fb=gp*gp/(2*bqb);delta=1-Fb/F
        c.update(delta=delta,F_star=F,F_block=Fb,absolute_block_gain_gap=F-Fb,
                 gradient_norm=float(g.norm()),Fstar_over_loss=F/max(abs(float(op.objective(op.theta))),1e-300))
        if not -1e-6<=delta<=1+1e-6:
            c['reason']='UTILITY_OUT_OF_BOUNDS';record_condition(c);continue
        if dense is not None:
            c['dense_delta']=uref['delta'];c['dense_delta_error']=abs(delta-uref['delta'])
            att={'delta_reference_fp64':uref['delta'],'v2_recorded_delta':(recorded_values.get(gamma) or {}).get('delta'),
                 'v2_recorded_status':(recorded_values.get(gamma) or {}).get('utility_status')}
            for key,label in (('native_input','delta_native_fp64_input'),('fp32_arith','delta_fp32_arithmetic_same_inputs')):
                if key in e4:
                    try:att[label]=dense_delta(e4[key][0],e4[key][1],lam,groups)
                    except Exception as exc:att[label]=None;att[label+'_error']=repr(exc)
                else:att[label]=None
            for label in ('native_input_error','fp32_arith_error'):
                if label in e4:att[label]=e4[label]
            if att['delta_native_fp64_input'] is not None:att['input_quantization_effect']=att['delta_native_fp64_input']-uref['delta']
            if att['delta_fp32_arithmetic_same_inputs'] is not None:att['fp32_arithmetic_effect']=att['delta_fp32_arithmetic_same_inputs']-uref['delta']
            if att['v2_recorded_delta'] is not None:att['v2_total_error']=att['v2_recorded_delta']-uref['delta']
            c['e4_delta_attribution']=att
            if c['dense_delta_error']>cfg['reference_delta_atol']:
                c['reason']='DENSE_DELTA_DISAGREEMENT';record_condition(c);continue
        c['status']='QUALIFIED'
        prior=recorded_values.get(gamma) or {}
        if prior.get('delta') is not None:c['original_v2_delta_difference']=float(prior['delta'])-delta
        block_ray=(-gp/bqb)*b
        c['block_ray_loss']=loss_trials(op,val,block_ray,original['config']['line_search'])
        c['full_loss']=loss_trials(op,val,x,original['config']['line_search'])
        c['block_solve_plus_Q_wall']=br['wall_seconds']+qwall
        # New explicit budget: exact block solves plus one Q action. Not the old v2 proxy budget.
        budget=br['matvecs']+1;c['matched_matvec_budget']=budget
        for name,k,maxmv in [(f'cg_{k}',k,None) for k in cfg['cg_steps']]+[('matched_matvec_cg',cfg['max_iterations'],budget)]:
            d,cr=cg(Q,-g,rtol=cfg['reference_rtol'],max_iter=k,max_matvecs=maxmv)
            gain=float(-g@d-.5*d@cr['Qx'])
            dq=float(d@cr['Qx']);dg=float(g@d)
            alpha=-dg/dq if dq>0 and dg<0 else 0.
            trial=loss_trials(op,val,alpha*d,original['config']['line_search'])
            c['comparators'].append({'name':name,'gain':gain,'gain_ratio':gain/F,
                'best_ray_scale':alpha,'solve':public_receipt(cr),'line_search':trial,
                'solve_wall_vs_block':cr['wall_seconds']/max(c['block_solve_plus_Q_wall'],1e-300),
                'end_to_end_wall':cr['wall_seconds']+trial['wall_seconds'],
                'matvec_budget_enforced':maxmv,'wall_time_equivalence_claimed':False})
        short_rows=[v for v in c['comparators'] if v['name'].startswith('cg_')]
        crossing=[v for v in short_rows if v['gain_ratio']>=cfg['utility_energy_target']]
        c['first_tested_cg_budget_ge99']=int(crossing[0]['name'].split('_')[1]) if crossing else None
        c['cg_budget_censoring']='OBSERVED_GRID_CROSSING_NOT_EXACT_K99' if crossing else 'NOT_REACHED_BY_MAX_TESTED_BUDGET'
        c['wall_timing_class']='DIAGNOSTIC_FIXED_ORDER_NOT_SPEEDUP_TRIAL'
        # DLN coordinate/gauge test; sparse prespecified subset, no new training.
        if dense is not None and result['family']=='dln' and pv['seed_index']==cfg['gauge_seed_index'] and pv['checkpoint_index']==cfg['gauge_checkpoint']:
            gauge=[]
            for s in cfg['gauge_scales']:
                tv=np.ones(len(gd))
                for entry in op.layout.entries:
                    if entry.name=='layers.0.weight':tv[entry.start:entry.stop]=s
                    if entry.name=='layers.1.weight':tv[entry.start:entry.stop]=1/s
                z=gauge_diagnostic(G,gd,lam,groups,tv)
                model=copy.deepcopy(op.model)
                with torch.no_grad():model.layers[0].weight.mul_(s);model.layers[1].weight.div_(s)
                changed=FrozenOperator(model,op.inputs,op.targets,op.loss,microbatch=op.microbatch,dtype=torch.float64)
                z.update(scale=s,actual_forward_relative_drift=relative(changed.prediction,op.prediction))
                tt=torch.as_tensor(tv,device=g.device,dtype=g.dtype)
                z['actual_gradient_covariance_error']=relative(changed.gradient(),g/tt)
                v=probes[0];z['actual_GGN_covariance_error']=relative(changed.raw_ggn(v),op.raw_ggn(v/tt)/tt)
                z['status']='PASS' if max(z['covariant_direction_error'],z['covariant_delta_error'],z['actual_forward_relative_drift'],z['actual_GGN_covariance_error'])<=cfg['gauge_coordinate_rtol'] else 'INCONCLUSIVE'
                gauge.append(z)
            c['gauge']=gauge
        record_condition(c)
    if digest(training_path)!=train_before:raise ValueError('Source training receipt changed during read-only assay')
    result['wall_seconds']=time.perf_counter()-total_start
    if device.startswith('cuda'):
        result['peak_allocated_gib']=torch.cuda.max_memory_allocated(op.theta.device)/2**30
        result['peak_reserved_gib']=torch.cuda.max_memory_reserved(op.theta.device)/2**30
        result['memory_within_target']=max(result['peak_allocated_gib'],result['peak_reserved_gib'])<=cfg['memory_target_gib']
    result['qualified_condition_n']=sum(c['status']=='QUALIFIED' for c in result['conditions'])
    return result
