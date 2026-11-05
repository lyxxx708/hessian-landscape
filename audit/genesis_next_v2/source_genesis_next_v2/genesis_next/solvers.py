"""Plain CG with explicit matvec accounting and a final true-residual check.
No preconditioner, no random probes, no assumed equality between wall time and matvecs.
"""
from __future__ import annotations
import math
import time
import torch

def sync(tensor):
    if tensor.device.type=='cuda':torch.cuda.synchronize(tensor.device)

def cg(A,b,*,rtol=1e-8,max_iter=2000,max_matvecs=None):
    if rtol<0 or max_iter<0:raise ValueError('Invalid CG limits')
    cap=max_matvecs if max_matvecs is not None else max_iter+1
    if cap<1:raise ValueError('Need at least one matvec for verified residual')
    sync(b);start=time.perf_counter();n=0
    def mv(x):
        nonlocal n
        if n>=cap:raise RuntimeError('Internal matvec budget violation')
        n+=1;return A(x)
    x=torch.zeros_like(b);r=b.clone();p=r.clone();rr=torch.dot(r,r);bn=float(b.norm());status='ITERATION_LIMIT';steps=0
    if not torch.isfinite(b).all():raise ValueError('Nonfinite RHS')
    for k in range(min(max_iter,max(0,cap-1))):
        if bn==0 or float(r.norm())<=rtol*bn:status='RECURRENCE_TOLERANCE';break
        Ap=mv(p);curv=float(p@Ap)
        if not math.isfinite(curv) or curv<=0:status='NONPOSITIVE_CURVATURE';break
        alpha=rr/curv;x=x+alpha*p;r=r-alpha*Ap;rr2=r@r;steps=k+1
        if not torch.isfinite(x).all() or not torch.isfinite(r).all():status='NONFINITE';break
        if float(rr)==0:break
        p=r+(rr2/rr)*p;rr=rr2
    qx=mv(x);res=b-qx;relative=float(res.norm())/bn if bn else float(res.norm())
    converged=math.isfinite(relative) and relative<=rtol and status not in ('NONPOSITIVE_CURVATURE','NONFINITE')
    sync(b)
    return x,{'status':'CONVERGED' if converged else status,'converged':converged,
              'iterations':steps,'matvecs':n,'relative_true_residual':relative,
              'absolute_true_residual':float(res.norm()),'rhs_norm':bn,
              'wall_seconds':time.perf_counter()-start,'Qx':qx}

def public_receipt(receipt):
    return {k:(None if isinstance(v,float) and not math.isfinite(v) else v)
            for k,v in receipt.items() if k!='Qx'}

def block_cg(op,g,damping,*,rtol,max_iter,schema='coarse'):
    ids=op.layout.group_indices(schema,device=g.device)
    x=torch.zeros_like(g);receipts=[]
    sync(g);start=time.perf_counter()
    for i,idx in enumerate(ids):
        d,r=cg(lambda v:op.block_matvec(i,v,damping,schema),-g[idx],rtol=rtol,max_iter=max_iter)
        x[idx]=d;receipts.append(public_receipt(r))
    sync(g)
    return x,{'converged':all(x['converged'] for x in receipts),
              'matvecs':sum(x['matvecs'] for x in receipts),'blocks':receipts,
              'wall_seconds':time.perf_counter()-start}
