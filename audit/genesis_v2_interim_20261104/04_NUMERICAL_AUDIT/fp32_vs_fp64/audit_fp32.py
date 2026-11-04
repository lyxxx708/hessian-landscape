"""Read-only FP32 numeric qualification audit of v2 results. See AUDIT_PROTOCOL.md.

Imports the frozen source tree; run with `python -B -I` so nothing is written there.
"""
import argparse,collections,json,sqlite3,sys,time
from pathlib import Path
FROZEN='E:/GENESIS/worktrees/genesis-v2-pr14/implementation/genesis-v2'
sys.path.insert(0,FROZEN)
import torch
from genesis_gpu.runtime.measurement import rebuild_snapshot
from genesis_gpu.science.mechanism import dense_reference
from genesis_gpu.science.utility import evaluate_utility,quadratic_utility
from genesis_gpu.study.design import load_config

TOL,MATERIAL=.005,.01
FIELDS=('delta','E_task','E_val','cheap_rho','F_star')


def classify(v2,ref,dense_delta):
    if ref['status']!='NUMERIC_VALID' or ref.get('delta') is None:return 'UNAUDITABLE'
    if dense_delta is not None and abs(ref['delta']-dense_delta)>TOL:return 'UNAUDITABLE'
    if v2['status']!=ref['status'] or v2.get('task_status')!=ref.get('task_status'):return 'STATUS_CHANGE'
    D=max(abs(v2[k]-ref[k]) for k in ('delta','E_task','E_val'))
    return 'AGREE' if D<=TOL else 'DIVERGENT' if D<=MATERIAL else 'MATERIAL'


def gradient_check(payload,cfg,root):
    op32,_,_=rebuild_snapshot(payload,{**cfg,'analysis_dtype':'float32'},root)
    op64,_,_=rebuild_snapshot(payload,{**cfg,'analysis_dtype':'float64'},root)
    g32,g64=op32.gradient().double(),op64.gradient()
    return {'grad_rel_err':float((g32-g64).norm()/g64.norm()),'grad_cos':float(g32@g64/(g32.norm()*g64.norm())),
            'grad_norm_fp64':float(g64.norm()),'grad_norm_fp32_cpu':float(g32.norm()),'parameters':len(g64)}


def dense_state(payload,cfg,root):
    op,_,_=rebuild_snapshot(payload,{**cfg,'analysis_dtype':'float64'},root)
    if len(op.theta)>cfg['solver']['dense_limit']:return None
    ref=dense_reference(op,with_hessian=False,parameter_limit=cfg['solver']['dense_limit'])
    return (ref['G']+ref['G'].T)/2,ref['gradient'],op


def dense_delta(state,schema,lam):
    if state is None:return None
    G,g,op=state
    A=G+lam*torch.eye(len(g),dtype=g.dtype);full=torch.linalg.solve(A,-g);block=torch.zeros_like(g)
    for idx in op.layout.group_indices(schema,device=g.device):block[idx]=torch.linalg.solve(A[idx][:,idx],-g[idx])
    return quadratic_utility(g,full,block,A@block).get('delta')


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',required=True);ap.add_argument('--config',required=True);ap.add_argument('--out',required=True)
    ap.add_argument('--threads',type=int,default=3);ap.add_argument('--limit',type=int);args=ap.parse_args()
    torch.set_num_threads(args.threads)
    cfg=dict(load_config(Path(args.config)));cfg['device']='cpu';solver=cfg['solver'];root=Path(args.root)
    out=Path(args.out);done=set()
    if out.exists():done={json.loads(l)['job_id'] for l in open(out,encoding='utf-8')}
    db=sqlite3.connect(f'file:{root.as_posix()}/run_status.sqlite?mode=ro',uri=True)
    jobs=db.execute("SELECT id,result,payload FROM jobs WHERE kind='measure' AND state='COMPLETE' ORDER BY ordinal").fetchall();db.close()
    states=collections.defaultdict(list)
    for job_id,result,payload in jobs:
        if job_id in done:continue
        p=json.loads(payload);states[(p['run']['run_id'],p['checkpoint_index'])].append((job_id,json.loads(result),p))
    count=0
    with open(out,'a',encoding='utf-8') as sink:
        for key,items in states.items():
            first=items[0][2];grad=gradient_check(first,cfg,root);dense=dense_state(first,cfg,root)
            for job_id,result,p in items:
                rc=json.load(open(root/result['receipt']['path'],encoding='utf-8'));v2=rc['utility'];lam=rc['lambda_absolute']
                if v2['status']!='NUMERIC_VALID':continue
                op,val,_=rebuild_snapshot(p,{**cfg,'analysis_dtype':'float64'},root);t=time.perf_counter()
                ref,_=evaluate_utility(op,lam,schema=p['schema'],rtol=solver['rtol'],max_iter=solver['max_iter'],validation=val,line_search=cfg['line_search'],
                    stability_factor=solver['stability_factor'],delta_stability=solver['delta_stability'],preconditioner_probes=0,short_steps=solver['short_cg_steps'])
                dd=dense_delta(dense,p['schema'],lam)
                row={'job_id':job_id,'setting':p['run']['setting_id'],'seed_index':p['run']['seed_index'],'checkpoint':p['checkpoint_index'],'gamma':p['gamma'],'schema':p['schema'],'lambda':lam,
                     **grad,'grad_norm_v2_gpu':v2.get('gradient_norm'),'dense_delta':dd,'wall':time.perf_counter()-t,'ref_status':ref['status'],'ref_reason':ref.get('reason'),
                     'v2_delta_stability':v2.get('delta_stability'),'ref_task_status':ref.get('task_status'),'v2_task_status':v2.get('task_status'),'class':classify(v2,ref,dd)}
                for k in FIELDS:row[f'v2_{k}']=v2.get(k);row[f'ref_{k}']=ref.get(k)
                sink.write(json.dumps(row)+'\n');sink.flush();count+=1
                if args.limit and count>=args.limit:return


if __name__=='__main__':main()
