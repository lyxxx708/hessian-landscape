"""v2.1 offline qualification on non-DLN families.

Trains reduced-budget, non-protocol checkpoints under separate seeds in a separate
root (CPU only), then compares solver variants. These states qualify solver behavior
only: they are not S1/S2 trajectories and never enter any scientific estimand.
"""
import argparse,json,sys,time
from dataclasses import replace
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]));sys.path.insert(0,str(Path(__file__).resolve().parent))
import torch
from genesis_gpu.curvature.spectrum import power_scale
from genesis_gpu.runtime.measurement import rebuild_snapshot
from genesis_gpu.science.utility import evaluate_utility
from genesis_gpu.solvers import cg as cg_module
from genesis_gpu.study.design import expand_design,load_config,seed_for
from genesis_gpu.training.trainer import train_run
from solver_compare import VARIANTS,probe_solves


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--config',required=True);ap.add_argument('--root',required=True);ap.add_argument('--out',required=True)
    ap.add_argument('--setting',required=True);ap.add_argument('--budget',type=int,required=True);ap.add_argument('--threads',type=int,default=2)
    ap.add_argument('--checkpoints',nargs='+',type=int,default=[1,3]);ap.add_argument('--gammas',nargs='+',type=float,default=[.001,.01,.1])
    ap.add_argument('--variants',nargs='+',default=list(VARIANTS));args=ap.parse_args()
    torch.set_num_threads(args.threads)
    cfg=dict(load_config(Path(args.config)));solver=cfg['solver']
    template=next(r for r in expand_design(cfg) if r.setting_id==args.setting and r.stage=='s1')
    # Profile is not 'full': the CUDA-required production branch must not apply to this CPU-only assay.
    cfg.update(device='cpu',profile='v21_qualification')
    seed=seed_for('V21_SOLVER_QUALIFICATION',args.setting)
    run=replace(template,run_id=f'q21-{args.setting}-b{args.budget}-{seed:016x}',seed=seed,seed_index=0,train=replace(template.train,budget=args.budget))
    root=Path(args.root);root.mkdir(parents=True,exist_ok=True);t=time.perf_counter()
    receipt=train_run(run,cfg,root)
    print('trained',args.setting,receipt['status'],f'{time.perf_counter()-t:.0f}s',flush=True)
    with open(args.out,'a',encoding='utf-8') as out:
        for index in args.checkpoints:
            payload={'run':run.to_dict(),'checkpoint_index':index}
            scale=None
            for gamma in args.gammas:
                for name in args.variants:
                    probes,restart,dtype=VARIANTS[name];local=dict(cfg);local['analysis_dtype']=dtype
                    cg_module.cg.__kwdefaults__['restart']=restart
                    op,val,pv=rebuild_snapshot(payload,local,root)
                    if scale is None:scale=power_scale(op,cfg['power_iterations'],seed_for('POWER',seed,index))['value']
                    lam=gamma*max(scale,cfg['damping_floor']);t=time.perf_counter()
                    u,vec=evaluate_utility(op,lam,schema='coarse',rtol=solver['rtol'],max_iter=solver['max_iter'],validation=val,line_search=cfg['line_search'],
                        stability_factor=solver['stability_factor'],delta_stability=solver['delta_stability'],preconditioner_probes=probes,short_steps=solver['short_cg_steps'])
                    row={'setting':args.setting,'family':run.model.family,'budget':args.budget,'parameters':pv['parameters'],'checkpoint':index,'gamma':gamma,'lambda':lam,'variant':name,
                         'status':u['status'],'reason':u.get('reason'),'wall':time.perf_counter()-t,'delta':u.get('delta'),'delta_stability':u.get('delta_stability'),
                         'cheap_rho':u.get('cheap_rho'),'matched_budget':(u.get('matched_cg') or {}).get('matvec_budget'),'matched_gain':u.get('matched_cg_quadratic_gain'),
                         'short_gain':u.get('short_cg_quadratic_gain'),'F_star':u.get('F_star'),'E_task':u.get('E_task'),'matvecs_total':u.get('matvecs_total'),'gradient_norm':float(op.gradient().norm()),
                         'full_it':(u.get('full_solve') or {}).get('iterations'),'full_rel':(u.get('full_solve') or {}).get('true_residual'),
                         'tight_it':(u.get('tight_full_solve') or {}).get('iterations'),'tight_rel':(u.get('tight_full_solve') or {}).get('true_residual'),
                         'block_it':[s['iterations'] for s in u.get('block_solves',[])]}
                    if index==args.checkpoints[-1]:row['probe_solves']=probe_solves(op,lam,cfg,count=2)
                    out.write(json.dumps(row)+'\n');out.flush()


if __name__=='__main__':main()
