"""v2.1 four-way qualification: frozen preconditioner, FP32 plain, FP64 plain, independent reference.

States are read-only: S1 DLN checkpoints and G0 preflight checkpoints of the frozen v2
root, plus reduced-budget dev states from the qualification root. CPU only.

Residual fields: true_residual=||Qx-b||_2/||b||_2 (dimensionless, b is the solve's own
right-hand side, so block solves use their block norm); absolute_residual=||Qx-b||_2 (gradient
units); history=recursive ||r_k||_2/||b||_2.
"""
import argparse,copy,json,math,sys,time,traceback
from dataclasses import replace
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
import psutil
import torch
from scipy.sparse.linalg import LinearOperator,cg as scipy_cg
from genesis_gpu.audit.independent_reference import independent_ggn_vector
from genesis_gpu.contracts import LossSpec,RunSpec
from genesis_gpu.curvature.operators import FrozenOperator
from genesis_gpu.curvature.spectrum import power_scale
from genesis_gpu.datasets.registry import load_bundle
from genesis_gpu.models.registry import build_model
from genesis_gpu.runtime.measurement import rebuild_snapshot
from genesis_gpu.science.utility import evaluate_utility,quadratic_utility
from genesis_gpu.solvers import cg as cg_module
from genesis_gpu.study.design import expand_design,load_config,seed_for,setting_specs
from genesis_gpu.training.checkpoint import load_state

VARIANTS={'V0_frozen_precond_fp32':(8,'periodic','float32'),'V1_plain_fp32':(0,'periodic','float32'),
          'V3_plain_fp64':(0,'periodic','float64'),'V2_plain_ondrift_fp32':(0,'on_drift','float32'),'V4_plain_ondrift_fp64':(0,'on_drift','float64')}


class WallCap(Exception):pass


def preflight_builder(family,cfg,root):
    """Rebuild the G0-excluded checkpoint exactly as audit/g0.py defined its batch."""
    chosen={}
    for sid,m,t,data in setting_specs():
        if m.family not in chosen or m.depth*m.width>chosen[m.family][1].depth*chosen[m.family][1].width:chosen[m.family]=(sid,m,t,data)
    sid,m,t,data=chosen[family];seed=seed_for('HARDWARE_G0_ONLY',sid);run=RunSpec('g0-'+sid,sid,'g0',seed,0,m,t,data)
    state,_=load_state(Path(root)/'audit'/'preflight_checkpoints'/family)
    def build(dtype):
        dt=getattr(torch,dtype);bundle=load_bundle(run,cfg,root)
        model=build_model(m,seed).to(dtype=dt);model.load_state_dict(state['model'],strict=True)
        x,y=bundle.batch('train',step=0,count=cfg['curvature_batch'],seed=seed,dtype=dt)
        xv,yv=bundle.batch('validation',step=0,count=cfg['curvature_batch'],seed=seed_for('V21_PREFLIGHT_VALIDATION',sid),dtype=dt)
        loss=LossSpec('mse' if family=='dln' else 'ce');micro=cfg['curvature_microbatch']
        return FrozenOperator(model,x,y,loss,microbatch=micro),FrozenOperator(model,xv,yv,loss,microbatch=micro)
    return {'label':f'preflight:{family}:{sid}','class':'FROZEN_V2_G0_PREFLIGHT_ONE_STEP','family':family,'setting':sid,'build':build,'seed':seed,'index':0}


def snapshot_builder(run,index,cfg,root,klass):
    payload={'run':run.to_dict(),'checkpoint_index':index}
    def build(dtype):
        local=dict(cfg);local['analysis_dtype']=dtype
        op,val,_=rebuild_snapshot(payload,local,root);return op,val
    return {'label':f'{run.run_id}:ck{index}','class':klass,'family':run.model.family,'setting':run.setting_id,'build':build,'seed':run.seed,'index':index}


def precision_probe(op32,op64,lam,seed=20261104,count=3):
    rng=torch.Generator();rng.manual_seed(seed);ggn=[];q=[]
    for _ in range(count):
        v=(2*torch.randint(0,2,op64.theta.shape,generator=rng)-1).to(torch.float64)
        a=op64.raw_ggn(v);b=op32.raw_ggn(v.float()).double()
        ggn.append(float((a-b).norm()/a.norm().clamp_min(1e-300)))
        q.append(float(((a+lam*v)-(b+lam*v)).norm()/(a+lam*v).norm()))
    g64=op64.gradient();g32=op32.gradient().double()
    return {'ggn_matvec_rel_err_fp32_vs_fp64':ggn,'Q_matvec_rel_err_fp32_vs_fp64':q,'gradient_rel_err_fp32_vs_fp64':float((g32-g64).norm()/g64.norm().clamp_min(1e-300)),
            'gradient_norm_fp64':float(g64.norm()),'theta_rel_err':float((op32.theta.double()-op64.theta).norm()/op64.theta.norm())}


def independent_reference(op64,lam,cap,ids):
    """Independent autograd GGN action and SciPy CG in FP64, disjoint from genesis cg()/raw_ggn()."""
    start=time.perf_counter();g=op64.gradient()
    def check(_=None):
        if time.perf_counter()-start>cap:raise WallCap
    def solve(rhs,idx=None):
        n=len(rhs)
        def mv(a):
            check();t=torch.as_tensor(a,dtype=torch.float64)
            if idx is None:return (independent_ggn_vector(op64,t)+lam*t).numpy()
            full=torch.zeros_like(op64.theta);full[idx]=t
            return (independent_ggn_vector(op64,full)[idx]+lam*t).numpy()
        out,info=scipy_cg(LinearOperator((n,n),matvec=mv,dtype=np.float64),rhs.numpy(),rtol=1e-9,maxiter=20000)
        return torch.as_tensor(out,dtype=torch.float64),info
    full,info=solve(-g);block=torch.zeros_like(g);infos=[info]
    for idx in ids:
        block[idx],i=solve(-g[idx],idx);infos.append(i)
    qb=independent_ggn_vector(op64,block)+lam*block
    return {'full':full,'block':block,'utility':quadratic_utility(g,full,block,qb),'info':[int(i) for i in infos],'wall':time.perf_counter()-start}


def run_state(state,args,cfg,out):
    solver=cfg['solver'];build=state['build']
    op32,_=build('float32');op64,_=build('float64')
    assert op32.theta.dtype==torch.float32 and op64.theta.dtype==torch.float64 and op64.inputs.dtype in (torch.float64,torch.long,torch.int64,torch.int32)
    scale=power_scale(op32,cfg['power_iterations'],seed_for('POWER',state['seed'],state['index']))['value']
    for gamma in args.gammas:
        lam=gamma*max(scale,cfg['damping_floor']);base={k:state[k] for k in ('label','class','family','setting')};base.update(checkpoint=state['index'],gamma=gamma,**{'lambda':lam},parameters=len(op64.theta))
        base.update(precision=precision_probe(op32,op64,lam))
        ids=op64.layout.group_indices('coarse',device=op64.theta.device);reference=None
        if args.reference:
            try:reference=independent_reference(op64,lam,args.reference_cap,ids)
            except WallCap:base['reference_status']='WALL_CAP'
            except Exception:base['reference_status']=traceback.format_exc()[-400:]
            else:base.update(reference_status='OK',reference_info=reference['info'],reference_wall=reference['wall'],reference_delta=reference['utility'].get('delta'),reference_utility_status=reference['utility']['status'])
        for name in args.variants:
            probes,restart,dtype=VARIANTS[name];cg_module.cg.__kwdefaults__['restart']=restart
            op,val=build(dtype);row={**base,'variant':name,'dtype':dtype,'restart':restart,'preconditioner_probes':probes,'theta_dtype':str(op.theta.dtype)}
            t=time.perf_counter();rss0=psutil.Process().memory_info().rss
            def cap():
                if time.perf_counter()-t>args.cap:raise WallCap
            try:
                u,vec=evaluate_utility(op,lam,schema='coarse',rtol=solver['rtol'],max_iter=solver['max_iter'],validation=val,line_search=cfg['line_search'],stability_factor=solver['stability_factor'],
                    delta_stability=solver['delta_stability'],preconditioner_probes=probes,short_steps=solver['short_cg_steps'],callback=cap)
            except WallCap:row.update(status='WALL_CAP',reason=f'exceeded {args.cap}s')
            except Exception:row.update(status='EXCEPTION',reason=traceback.format_exc()[-500:])
            else:
                sol=lambda k:(u.get(k) or {})
                matched=sol('matched_cg').get('solve',{}) if u.get('matched_cg') else {}
                row.update(status=u['status'],reason=u.get('reason'),delta=u.get('delta'),delta_stability=u.get('delta_stability'),alpha_Q=u.get('alpha_Q'),E_task=u.get('E_task'),E_val=u.get('E_val'),
                    cheap_rho=u.get('cheap_rho'),short_gain=u.get('short_cg_quadratic_gain'),matched_gain=u.get('matched_cg_quadratic_gain'),F_star=u.get('F_star'),gradient_norm=u.get('gradient_norm'),
                    matched_budget=sol('matched_cg').get('matvec_budget'),matched_matvecs=matched.get('matvecs'),matched_status=matched.get('status'),matvecs_total=u.get('matvecs_total'),
                    full_iterations=sol('full_solve').get('iterations'),full_true_residual=sol('full_solve').get('true_residual'),full_absolute_residual=sol('full_solve').get('absolute_residual'),full_status=sol('full_solve').get('status'),
                    tight_iterations=sol('tight_full_solve').get('iterations'),tight_true_residual=sol('tight_full_solve').get('true_residual'),tight_status=sol('tight_full_solve').get('status'),
                    block_iterations=[s['iterations'] for s in u.get('block_solves',[])],block_true_residual=[s['true_residual'] for s in u.get('block_solves',[])],
                    tight_block_status=[s['status'] for s in u.get('tight_block_solves',[])],tight_block_true_residual=[s['true_residual'] for s in u.get('tight_block_solves',[])])
                if vec and reference:
                    row['full_err_vs_reference']=float((vec['full'].double()-reference['full']).norm()/reference['full'].norm())
                    row['block_err_vs_reference']=float((vec['block'].double()-reference['block']).norm()/reference['block'].norm())
                if vec:
                    # Evaluate this variant's direction with the FP64 operator: separates solver error from FP32 operator noise.
                    x=vec['full'].double();q=op64.matvec(x,lam);row['full_true_residual_under_fp64']=float((q+op64.gradient()).norm()/op64.gradient().norm())
            row.update(wall=time.perf_counter()-t,rss_delta_bytes=psutil.Process().memory_info().rss-rss0)
            if not args.no_probes and state['index'] in (0,3) and gamma==args.gammas[0]:
                # Same RHS class as the structural inverse probes: plain Rademacher, no preconditioner, tight rtol, 2*max_iter.
                rng=torch.Generator();rng.manual_seed(20261105);probes_out=[];tp=time.perf_counter()
                rtol=max(solver['rtol']*solver['stability_factor'],5*torch.finfo(op.theta.dtype).eps)
                for _ in range(args.probe_count):
                    z=(2*torch.randint(0,2,op.theta.shape,generator=rng)-1).to(op.theta.dtype)
                    s=cg_module.cg(lambda v:op.matvec(v,lam),z,rtol=rtol,max_iter=solver['max_iter']*2)
                    probes_out.append({'status':s.status,'iterations':s.iterations,'true_residual':s.true_residual})
                row.update(probe_solves=probes_out,probe_wall=time.perf_counter()-tp)
            out.write(json.dumps(row)+'\n');out.flush()


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--config',required=True);ap.add_argument('--root',required=True);ap.add_argument('--qual-root',default='E:/GENESIS/runs/v21_qualification');ap.add_argument('--out',required=True)
    ap.add_argument('--preflight',nargs='*',default=[]);ap.add_argument('--dev',nargs='*',default=[],help='setting:budget');ap.add_argument('--checkpoints',nargs='+',type=int,default=[3])
    ap.add_argument('--gammas',nargs='+',type=float,default=[.001,.01,.1]);ap.add_argument('--variants',nargs='+',default=['V0_frozen_precond_fp32','V1_plain_fp32','V3_plain_fp64','V4_plain_ondrift_fp64'])
    ap.add_argument('--threads',type=int,default=3);ap.add_argument('--cap',type=float,default=2400);ap.add_argument('--reference',action='store_true');ap.add_argument('--reference-cap',type=float,default=3600)
    ap.add_argument('--no-probes',action='store_true');ap.add_argument('--probe-count',type=int,default=2);args=ap.parse_args()
    torch.set_num_threads(args.threads)
    cfg=dict(load_config(Path(args.config)));cfg.update(device='cpu',profile='v21_qualification')
    with open(args.out,'a',encoding='utf-8') as out:
        for family in args.preflight:run_state(preflight_builder(family,cfg,args.root),args,cfg,out)
        for spec in args.dev:
            sid,budget=spec.split(':');budget=int(budget);full=dict(cfg);full['profile']='full'
            template=next(r for r in expand_design({**cfg,'profile':'full'}) if r.setting_id==sid and r.stage=='s1');seed=seed_for('V21_SOLVER_QUALIFICATION',sid)
            run=replace(template,run_id=f'q21-{sid}-b{budget}-{seed:016x}',seed=seed,seed_index=0,train=replace(template.train,budget=budget))
            for index in args.checkpoints:run_state(snapshot_builder(run,index,cfg,args.qual_root,'DEV_REDUCED_BUDGET_NON_PROTOCOL'),args,cfg,out)


if __name__=='__main__':main()
