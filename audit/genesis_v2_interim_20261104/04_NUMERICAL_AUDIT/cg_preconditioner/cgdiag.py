import sys,json,sqlite3,time,copy
sys.path.insert(0,'E:/GENESIS/worktrees/genesis-v2-pr14/implementation/genesis-v2')
import torch;torch.set_num_threads(2)
from pathlib import Path
from genesis_gpu.study.design import load_config
from genesis_gpu.runtime.measurement import rebuild_snapshot
from genesis_gpu.solvers.cg import cg,hutchinson_diagonal
R='E:/GENESIS/runs/genesis_full_v2'
cfg=load_config(Path('E:/GENESIS/worktrees/genesis-v2-pr14/implementation/genesis-v2/configs/study_v2.yaml'))
cfg=dict(cfg);cfg['device']='cpu'
c=sqlite3.connect(f'file:{R}/run_status.sqlite?mode=ro',uri=True)
rows=[(json.loads(p),json.loads(r)) for p,r in c.execute("select payload,result from jobs where state='NUMERIC_UNRESOLVED'")]
want=[(2,'dln_d4_w16_orthogonal_balanced_c1'),(0,'dln_d4_w16_orthogonal_balanced_c1')]
for ci,sid in want:
    p,r=next((p,r) for p,r in rows if p['checkpoint_index']==ci and p['run']['setting_id']==sid)
    rc=json.load(open(R+'/'+r['receipt']['path']));lam=rc['lambda_absolute']
    for dt in ('float32','float64'):
        cfg['analysis_dtype']=dt
        op,val,pv=rebuild_snapshot(p,cfg,R)
        g=op.gradient();Q=lambda v:op.matvec(v,lam)
        d,_=hutchinson_diagonal(op,lam,8);pre=lambda v:v/d
        print(f'ckpt{ci} {dt} n={len(op.theta)} |g|={float(g.norm()):.2e} lam={lam:.2e}',flush=True)
        for name,kw in [('orig(pre,restart20)',dict(preconditioner=pre,true_every=20)),('nopre,restart20',dict(true_every=20)),('nopre,norestart',dict(true_every=10**9)),('pre,norestart',dict(preconditioner=pre,true_every=10**9))]:
            s=cg(Q,-g,rtol=1e-5,max_iter=1000,**kw)
            print(f'   {name:22s} status={s.status} it={s.iterations} rel={s.absolute_residual/float(g.norm()):.2e}',flush=True)
