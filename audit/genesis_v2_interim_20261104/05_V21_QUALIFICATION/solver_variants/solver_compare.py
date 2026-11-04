"""v2.1 offline qualification: old vs candidate solvers on frozen v2 checkpoints.

Read-only with respect to the v2 run root. CPU only, so it cannot contend for the
GPU worker. Diagnostic output never replaces a protocol measurement.
"""
import argparse,json,sqlite3,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import torch
from genesis_gpu.contracts import LossSpec
from genesis_gpu.curvature.operators import FrozenOperator
from genesis_gpu.runtime.measurement import rebuild_snapshot
from genesis_gpu.science.mechanism import dense_reference
from genesis_gpu.science.utility import evaluate_utility,quadratic_utility
from genesis_gpu.solvers import cg as cg_module
from genesis_gpu.study.design import load_config

VARIANTS={'V0_frozen':(8,'periodic','float32'),'V1_noprecond':(0,'periodic','float32'),'V2_noprecond_ondrift':(0,'on_drift','float32'),
          'V3_noprecond_f64':(0,'periodic','float64'),'V4_noprecond_ondrift_f64':(0,'on_drift','float64')}


def receipts(root,settings,seeds,checkpoints):
    db=sqlite3.connect(f'file:{root}/run_status.sqlite?mode=ro',uri=True)
    for state,result,payload in db.execute("SELECT state,result,payload FROM jobs WHERE kind='measure' AND state IN ('COMPLETE','NUMERIC_UNRESOLVED') ORDER BY ordinal"):
        p=json.loads(payload)
        if p['schema']=='coarse' and p['run']['setting_id'] in settings and p['run']['seed_index'] in seeds and p['checkpoint_index'] in checkpoints:
            yield state,json.loads(result),p


def dense_truth(p,cfg,root,dampings):
    local=dict(cfg);local['analysis_dtype']='float64'
    op,_,_=rebuild_snapshot(p,local,root)
    ref=dense_reference(op,with_hessian=False,parameter_limit=cfg['solver']['dense_limit'])
    G=(ref['G']+ref['G'].T)/2;g=ref['gradient'];ids=op.layout.group_indices('coarse',device=g.device)
    eig=torch.linalg.eigvalsh(G);out={}
    for lam in dampings:
        A=G+lam*torch.eye(len(g),dtype=g.dtype)
        full=torch.linalg.solve(A,-g);block=torch.zeros_like(g)
        for idx in ids:block[idx]=torch.linalg.solve(A[idx][:,idx],-g[idx])
        out[lam]={'full':full,'block':block,'utility':quadratic_utility(g,full,block,A@block),'cond':float((eig.max()+lam)/(eig.clamp_min(0).min()+lam))}
    return out,{'rank_tol_1e-10':int((eig>1e-10*eig.max()).sum()),'n':len(g)}


def probe_solves(op,lam,cfg,seed=20261103,count=3):
    rng=torch.Generator();rng.manual_seed(seed);out=[]
    rtol=max(cfg['solver']['rtol']*cfg['solver']['stability_factor'],5*torch.finfo(op.theta.dtype).eps)
    for _ in range(count):
        z=(2*torch.randint(0,2,op.theta.shape,generator=rng)-1).to(op.theta.dtype)
        s=cg_module.cg(lambda v:op.matvec(v,lam),z,rtol=rtol,max_iter=cfg['solver']['max_iter']*2)
        out.append({'status':s.status,'iterations':s.iterations,'rel':s.true_residual})
    return out


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',required=True);ap.add_argument('--config',required=True);ap.add_argument('--out',required=True)
    ap.add_argument('--settings',nargs='+',required=True);ap.add_argument('--seeds',nargs='+',type=int,default=[1,3]);ap.add_argument('--checkpoints',nargs='+',type=int,default=[0,1,3])
    ap.add_argument('--threads',type=int,default=4);args=ap.parse_args()
    torch.set_num_threads(args.threads)
    cfg=dict(load_config(Path(args.config)));cfg['device']='cpu';solver=cfg['solver'];root=args.root
    truths={}
    with open(args.out,'a',encoding='utf-8') as out:
        for state,result,p in receipts(root,set(args.settings),set(args.seeds),set(args.checkpoints)):
            rc=json.load(open(Path(root)/result['receipt']['path'],encoding='utf-8'));lam=rc['lambda_absolute']
            key=(p['run']['run_id'],p['checkpoint_index'])
            if key not in truths:
                # All three dampings on this state share the same power-iteration scale.
                truths[key]=dense_truth(p,cfg,root,[lam*g/p['gamma'] for g in cfg['damping_ratios']])
            dense,meta=truths[key];truth=min(dense.items(),key=lambda kv:abs(kv[0]-lam))[1]
            base={'setting':p['run']['setting_id'],'seed_index':p['run']['seed_index'],'checkpoint':p['checkpoint_index'],'gamma':p['gamma'],'lambda':lam,
                  'v2_state':state,'dense_meta':meta,'dense_cond':truth['cond'],'dense_delta':truth['utility'].get('delta'),'dense_status':truth['utility']['status']}
            for name,(probes,restart,dtype) in VARIANTS.items():
                local=dict(cfg);local['analysis_dtype']=dtype
                cg_module.cg.__kwdefaults__['restart']=restart
                op,val,_=rebuild_snapshot(p,local,root);t=time.perf_counter()
                u,vec=evaluate_utility(op,lam,schema='coarse',rtol=solver['rtol'],max_iter=solver['max_iter'],validation=val,line_search=cfg['line_search'],
                    stability_factor=solver['stability_factor'],delta_stability=solver['delta_stability'],preconditioner_probes=probes,short_steps=solver['short_cg_steps'])
                row={**base,'variant':name,'status':u['status'],'reason':u.get('reason'),'wall':time.perf_counter()-t,'delta':u.get('delta'),'delta_stability':u.get('delta_stability'),
                     'alpha_Q':u.get('alpha_Q'),'E_task':u.get('E_task'),'E_val':u.get('E_val'),'cheap_rho':u.get('cheap_rho'),'short_gain':u.get('short_cg_quadratic_gain'),
                     'matched_gain':u.get('matched_cg_quadratic_gain'),'matched_budget':(u.get('matched_cg') or {}).get('matvec_budget'),'matvecs_total':u.get('matvecs_total'),
                     'F_star':u.get('F_star'),'gradient_norm':u.get('gradient_norm'),'full_it':(u.get('full_solve') or {}).get('iterations'),'full_rel':(u.get('full_solve') or {}).get('true_residual'),
                     'tight_it':(u.get('tight_full_solve') or {}).get('iterations'),'tight_rel':(u.get('tight_full_solve') or {}).get('true_residual'),'tight_status':(u.get('tight_full_solve') or {}).get('status'),
                     'block_it':[s['iterations'] for s in u.get('block_solves',[])]}
                if vec:
                    row['full_err_vs_dense']=float((vec['full'].double()-truth['full']).norm()/truth['full'].norm())
                    row['block_err_vs_dense']=float((vec['block'].double()-truth['block']).norm()/truth['block'].norm())
                if p['checkpoint_index']==3:row['probe_solves']=probe_solves(op,lam,cfg)
                out.write(json.dumps(row)+'\n');out.flush()


if __name__=='__main__':main()
