"""Gated paired-seed optimizer experiments, real clock accounting, no oracle speedup claims."""
from __future__ import annotations
from dataclasses import replace
from pathlib import Path
import math
import json
import time
import numpy as np
import torch
from genesis_gpu.contracts import RunSpec,LossSpec,TrainSpec,object_sha
from genesis_gpu.models.registry import build_model
from genesis_gpu.datasets.registry import load_bundle
from genesis_gpu.study.design import setting_specs,smoke_specs,seed_for
from genesis_gpu.study.freeze import require_stage_access,verify_lock,set_state
from genesis_gpu.runtime.atomic_io import atomic_json,read_json,file_receipt,verify_receipt
from genesis_gpu.runtime.resources import StudyLock,ResourceGuard,DeviceLock
from genesis_gpu.runtime.queue import JobStore
from genesis_gpu.training.trainer import train_run,training_budget,StopRequested
from genesis_gpu.training.checkpoint import load_state
from genesis_gpu.training.optimizers import ResearchOptimizer
from genesis_gpu.study.statistics import bootstrap_median,holm
from scipy.stats import binomtest


def _trial(run,method,cfg,root,predictor=None,wall_budget=None,matched_matvecs=None,guard=None):
    bundle=load_bundle(run,cfg,root);device=cfg['device'];dtype=torch.float64 if cfg['profile']=='smoke' else torch.float32
    xv,yv=bundle.batch('validation',step=0,count=cfg['curvature_batch'],seed=seed_for('S3VAL',run.seed),device=device,dtype=dtype)
    loss=LossSpec('mse' if run.model.family=='dln' else 'ce');base=build_model(run.model,run.seed).to(device=device,dtype=dtype).eval()
    with torch.no_grad():initial=float(loss.value(base(xv),yv))
    total_steps,_,_=training_budget(run,bundle);interval=max(1,total_steps//100)
    def factory(model):
        opt=ResearchOptimizer(model,method,run.train.learning_rate,run.train.weight_decay,cfg,predictor=predictor,callback=guard)
        opt.validation_probe=(xv,yv,loss);opt.evaluation_interval=interval;opt.matched_matvec_budget=matched_matvecs
        return opt
    receipt=train_run(run,cfg,root,optimizer_factory=factory,callback=guard,wall_budget_seconds=wall_budget)
    if receipt['status']=='INTERRUPTED':raise StopRequested('optimizer trial safely interrupted')
    state,meta=load_state(Path(root)/receipt['final_checkpoint']['path'],receipt['final_checkpoint']['integrity_sha'])
    base.load_state_dict(state['model']);base.eval()
    with torch.no_grad():final=float(loss.value(base(xv),yv))
    # Test is evaluated only for final evaluation arms, never for tuning or online decisions.
    test_loss=None
    if run.stage=='s3_eval':
        xt,yt=bundle.batch('test',step=0,count=cfg['curvature_batch'],seed=seed_for('S3TEST',run.seed),device=device,dtype=dtype)
        with torch.no_grad():test_loss=float(loss.value(base(xt),yt))
    path=Path(root)/'logs'/f'{run.run_id}.jsonl';rows=[]
    if path.exists():
        for line in path.read_text().splitlines():
            row=json.loads(line)
            if row.get('event')=='TRAIN_STEP' and row['step']<=receipt['steps']:rows.append(row)
    # Rollback logs can contain duplicate attempts; use latest committed step record.
    bystep={r['step']:r for r in rows};rows=[bystep[k] for k in sorted(bystep)]
    target=initial*cfg['s3']['target_loss_fraction'];time_to_target=None;previous_time=0.;crossing_interval=None
    for row in rows:
        value=(row.get('optimizer_receipt') or {}).get('validation_loss')
        if value is not None:
            if value<=target and time_to_target is None:
                time_to_target=row['elapsed'];crossing_interval=[previous_time,row['elapsed']]
            previous_time=row['elapsed']
    report={'run_id':run.run_id,'method':method,'seed':run.seed,'stage':run.stage,'setting_id':run.setting_id,
            'initial_validation_loss':initial,'final_validation_loss':final,'final_test_probe_loss':test_loss,'target_loss':target,
            'time_to_target_upper_seconds':time_to_target,'time_to_target_lower_seconds':crossing_interval[0] if crossing_interval else None,'crossing_interval_seconds':crossing_interval,
            'target_censored':time_to_target is None,'total_wall_seconds':receipt['total_wall_seconds'],
            'training_units':receipt['training_units'],'planned_steps':receipt['planned_steps'],'actual_steps':receipt['steps'],
            'budget_status':receipt['status'],'wall_budget_seconds':wall_budget,
            'matvecs':sum((r.get('optimizer_receipt') or {}).get('matvecs',0) for r in rows),
            'matched_cg_budget_from_calibration':matched_matvecs,
            'training_receipt':file_receipt(Path(root)/'checkpoints'/run.run_id/'training_receipt.json',root),
            'validation_policy':'same fixed validation probe, identical measurement frequency; included in wall clock; test only final eval',
            'qualification':'reference baselines, not claimed reproduction of published optimizer benchmark'}
    out=Path(root)/'benchmark'/'trials'/f'{run.run_id}.json';atomic_json(out,report);return report


def _negative_control(cfg,root):
    spec=smoke_specs()[0];sid,m,t,data=spec
    t=replace(t,budget=cfg['s3']['negative_control_steps'],checkpoint_fractions=(0.,1/3,2/3,1.))
    seed=seed_for('S3_NEGATIVE_CONTROL',cfg['seed_namespace']);subroot=Path(root)/'benchmark'/'negative_control'
    # Explicitly small synthetic numerical control, separate from real nonlinear claim population.
    control_cfg={**cfg,'profile':'smoke','device':cfg['device']}
    results=[]
    for method in ('adamw','gradient_smoothing'):
        run=RunSpec('s3-negative-'+method,'negative_dln','s3_negative',seed,0,m,t,data)
        results.append(_trial(run,method,control_cfg,subroot))
    return {'executed':True,'classification':'SMALL_SYNTHETIC_NEGATIVE_SANITY_NOT_OPTIMIZER_BENCHMARK',
            'paired_seed':seed,'results':results,'artifacts_root':str(subroot)}


def compare_trials(results,setting_ids,cfg):
    """Conservative paired inference against EVERY baseline, not Adam alone.

    Exact crossing times are interval-censored: candidate upper / baseline lower
    is a conservative bound. No speedup promotion when even one planned pair is
    missing/right-censored. Wall-budget quality must also be noninferior under
    the pre-fixed 1% loss margin. All comparison p-values receive Holm control.
    """
    comparisons=[];planned=cfg['s3']['seeds'];threshold=cfg['s3']['time_improvement']
    for sid in setting_ids:
        for method in cfg['s3']['baselines']:
            if method=='selective_krylov':continue
            def select(name,mode):
                return {r['seed']:r for r in results if r.get('setting_id')==sid and
                        r.get('stage')=='s3_eval' and r.get('method')==name and
                        r.get('evaluation_mode')==mode and r.get('status')!='FAILED'}
            base=select(method,'samples');candidate=select('selective_krylov','samples')
            base_wall=select(method,'wall_time');candidate_wall=select('selective_krylov','wall_time')
            gains=[];quality=[];complete_pairs=[]
            for seed in sorted(set(base)&set(candidate)):
                b,c=base[seed],candidate[seed]
                lower=b.get('time_to_target_lower_seconds');upper=c.get('time_to_target_upper_seconds')
                if lower is None and b.get('crossing_interval_seconds'):lower=b['crossing_interval_seconds'][0]
                if lower is not None and lower>0 and upper is not None and upper>0:
                    gains.append(1-upper/lower);complete_pairs.append(seed)
                    quality.append(c['final_validation_loss']<=1.01*b['final_validation_loss'])
            wall_pairs=set(base_wall)&set(candidate_wall)
            wall_ok=len(wall_pairs)==planned and all(candidate_wall[k]['final_validation_loss']<=1.01*base_wall[k]['final_validation_loss'] for k in wall_pairs)
            summary=bootstrap_median(gains,cfg['statistics']['bootstrap']) if gains else None
            p=float(binomtest(sum(g>threshold for g in gains),len(gains),.5,alternative='greater').pvalue) if len(gains)==planned else 1.
            effect=(len(gains)==planned and summary['median']>=threshold and summary['interval'][0]>0 and all(quality) and wall_ok)
            comparisons.append({'setting':sid,'baseline':method,'paired_uncensored_seeds':len(gains),'planned_seeds':planned,
                                'paired_seed_ids':complete_pairs,'conservative_time_improvement':summary,
                                'wall_budget_quality_noninferior':bool(wall_ok),'p_sign_above_threshold':p,'effect_gate':bool(effect),'pass':False,
                                'censoring_policy':'candidate upper / baseline lower; missing or censored planned pairs prohibit promotion'})
    adjusted=holm([c['p_sign_above_threshold'] for c in comparisons]) if comparisons else []
    for c,p in zip(comparisons,adjusted):c['holm_p']=p;c['pass']=c['effect_gate'] and p<cfg['statistics']['alpha']
    return {'comparisons':comparisons,'optimizer_gate_pass':len(setting_ids)>=2 and bool(comparisons) and all(c['pass'] for c in comparisons),
            'scope':'Reference implementations on tested tasks only; not a universal or published-baseline reproduction claim.'}


def run_benchmark(cfg,root):
    root=Path(root);lock=read_json(root/'protocol-lock.json');ap=root/'audit'/'s2_adjudication.json'
    if not ap.exists():raise RuntimeError('S2 adjudication required for S3')
    decision=read_json(ap)
    if decision['protocol_sha']!=lock['protocol_sha'] or not decision['execution_complete']:
        raise RuntimeError('S2 evidence mismatch')
    out=root/'audit'/'s3_receipt.json'
    if out.exists():
        previous=read_json(out)
        if previous['s2_decision_sha']!=file_receipt(ap,root)['sha256']:raise RuntimeError('S2 changed after S3 decision')
        return previous
    if not decision['s3_gate_pass'] or not cfg['s3']['enabled']:
        with DeviceLock(cfg['storage_root'],cfg['device'],cfg['device'].startswith('cuda')), StudyLock(root):
            control=_negative_control(cfg,root)
            receipt={'status':'S3_NO_GO','protocol_sha':lock['protocol_sha'],'s2_decision_sha':file_receipt(ap,root)['sha256'],
                     'optimizer_speedup_claim':False,'reason':'Prerecorded utility+prediction gates not satisfied, or S3 disabled',
                     'negative_control':control,'full_optimizer_trials_executed':False}
            atomic_json(out,receipt);set_state(root,'S3_NO_GO',scientific_complete=False)
        return receipt
    require_stage_access(root,'s3');verify_lock(cfg,root)
    predictor=read_json(root/'audit'/'predictor_frozen_s1.json')
    specs=[s for s in setting_specs() if s[0] in ('resnet20_gn','transformer_d4')]
    results=[];choices=[];calibrations=[]
    with DeviceLock(cfg['storage_root'],cfg['device'],cfg['device'].startswith('cuda')), StudyLock(root):
        store=JobStore(root/'run_status.sqlite');store.recover_interrupted()
        try:
            for sid,m,t,data in specs:
                stage_root=root/'benchmark'/sid;stage_root.mkdir(parents=True,exist_ok=True)
                calibration_path=stage_root/'calibration.json'
                if calibration_path.exists():calibration=read_json(calibration_path)
                else:
                    ctrain=replace(t,budget_kind='steps',budget=max(3,cfg['s3']['calibration_steps']),schedule='constant')
                    cseed=seed_for('S3_COST_CALIBRATION',sid)
                    cr=RunSpec('s3-calibrate-'+sid,sid,'s3_calibration',cseed,0,m,ctrain,data)
                    guard=ResourceGuard(cfg,root)
                    adam=_trial(cr,'adamw',cfg,stage_root,predictor,guard=guard)
                    # One excluded current-state selective update measures comparable Gv budget.
                    pr=replace(cr,run_id=cr.run_id+'-matvec',train=replace(ctrain,budget=3))
                    selective=_trial(pr,'selective_krylov',cfg,stage_root,predictor,guard=guard)
                    bundle=load_bundle(cr,cfg,root);fullrun=replace(cr,train=t)
                    nsteps,_,_=training_budget(fullrun,bundle)
                    sec_per_step=adam['total_wall_seconds']/adam['actual_steps']
                    calibration={'setting_id':sid,'seconds_per_adam_step':sec_per_step,'full_steps':nsteps,
                                 'matched_matvecs':max(cfg['solver']['short_cg_steps'],math.ceil(selective['matvecs']/selective['actual_steps'])),
                                 'common_wall_budget':1.2*sec_per_step*nsteps,'calibration_seed_excluded':cseed,
                                 's1_s2_never_used_for_tuning':True,'trials':[adam,selective]}
                    atomic_json(calibration_path,calibration)
                calibrations.append(calibration)
                wall=calibration['common_wall_budget'];matched=calibration['matched_matvecs']
                method_choices={}
                def execute(run,method,cap,mode):
                    identity=object_sha([lock['protocol_sha'],run.to_dict(),method,cap,mode])
                    payload={'run':run.to_dict(),'method':method,'wall_budget':cap,'mode':mode}
                    stage='s3-'+sid+'-'+method+'-'+run.stage+'-'+mode+'-'+str(run.seed_index)
                    store.enqueue(identity,stage,'optimizer',payload,[])
                    old=next(r for r in store.rows(stage) if r['id']==identity)
                    if old['state']=='COMPLETE':
                        if not verify_receipt(root,old['result']['receipt']):raise RuntimeError('Optimizer artifact corrupt')
                        return read_json(root/old['result']['receipt']['path'])
                    job=store.claim(stage)
                    if job is None:return {'method':method,'status':'FAILED','run_id':run.run_id}
                    guard=ResourceGuard(cfg,root,store,identity)
                    try:
                        r=_trial(run,method,cfg,root,predictor,cap,matched,guard)
                        r['evaluation_mode']=mode;path=root/'benchmark'/'trials'/f'{run.run_id}.json';atomic_json(path,r)
                        store.finish(identity,'COMPLETE',{'receipt':file_receipt(path,root)});return r
                    except (StopRequested,KeyboardInterrupt):store.finish(identity,'INTERRUPTED',{'reason':'safe cancellation'});raise
                    except Exception as exc:
                        store.finish(identity,'FAILED',{'error':repr(exc)});return {'method':method,'status':'FAILED','run_id':run.run_id,'error':repr(exc)}
                for method in cfg['s3']['baselines']:
                    by_lr=[]
                    for multiplier in cfg['s3']['lr_multipliers']:
                        scores=[]
                        for i in range(cfg['s3']['tuning_seeds']):
                            seed=seed_for('S3_TUNING',sid,i)
                            train=replace(t,learning_rate=t.learning_rate*multiplier)
                            run=RunSpec(f's3-tune-{sid}-{method}-lr{multiplier}-s{i}',sid,'s3_tune',seed,i,m,train,data)
                            r=execute(run,method,wall*cfg['s3']['tuning_fraction'],'equal_wall_tuning');results.append(r)
                            scores.append(r.get('final_validation_loss',float('inf')))
                        by_lr.append((float(np.mean(scores)),multiplier))
                    score,multiplier=min(by_lr)
                    method_choices[method]={'lr_multiplier':multiplier,'score':score if math.isfinite(score) else None,'qualified':math.isfinite(score)}
                choices.append({'setting':sid,'choices':method_choices})
                atomic_json(stage_root/'hyperparameter_selection.json',{'source':'S3 dedicated tuning seeds, not S2','choices':method_choices})
                for method,choice in method_choices.items():
                    if not choice['qualified']:continue
                    for mode in cfg['s3']['evaluation_modes']:
                        for i in range(cfg['s3']['seeds']):
                            seed=seed_for('S3_EVALUATION',sid,i)
                            train=replace(t,learning_rate=t.learning_rate*choice['lr_multiplier'])
                            run=RunSpec(f's3-eval-{sid}-{method}-{mode}-s{i}',sid,'s3_eval',seed,i,m,train,data)
                            results.append(execute(run,method,wall if mode=='wall_time' else None,mode))
            comparison=compare_trials(results,[sid for sid,_,_,_ in specs],cfg)
            all_baselines_complete=all(r.get('status')!='FAILED' for r in results)
            receipt={'status':'S3_EXECUTED' if all_baselines_complete else 'S3_INCOMPLETE_BASELINE_FAILURES',
                     'protocol_sha':lock['protocol_sha'],'s2_decision_sha':file_receipt(ap,root)['sha256'],'calibrations':calibrations,
                     'choices':choices,'trials':results,'comparisons':comparison['comparisons'],'optimizer_speedup_claim':bool(all_baselines_complete and comparison['optimizer_gate_pass']),
                     'reason':'Paired conservative time bounds against every reference baseline, Holm correction, full planned coverage and fixed-wall quality gate; independent raw-evidence audit still required.',
                     'tuning_budget_policy':'Equal calibration-defined wall budget per method/seed/LR; runtime checks occur at safe step boundaries, overshoot is reported',
                     'evaluation_policy':'Both matched sample/token budget and matched wall-clock budget; target observations are interval-censored'}
            atomic_json(out,receipt);set_state(root,'S3_DONE' if all_baselines_complete else 'INCOMPLETE_BLOCKED_EVIDENCE',scientific_complete=False)
            return receipt
        finally:store.interrupt_owned();store.close()
