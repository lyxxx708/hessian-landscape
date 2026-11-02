"""SPD-only CG / PCG with recomputed true residual and explicit invalid states."""
from __future__ import annotations
import time
import torch
from genesis_gpu.contracts import SolveResult


def cg(apply, rhs, *, rtol=1e-5, max_iter=1000, preconditioner=None, x0=None, callback=None, true_every=20):
    if rhs.ndim!=1 or not rhs.numel() or not torch.isfinite(rhs).all() or not 0<rtol<1 or max_iter<1:
        raise ValueError('Invalid CG inputs')
    started=time.perf_counter(); calls=0
    def A(v):
        nonlocal calls
        q=apply(v).detach();calls+=1
        if q.shape!=rhs.shape or not torch.isfinite(q).all():
            raise ArithmeticError('Nonfinite or wrong-shaped operator result')
        return q
    def M(v):
        q=v.clone() if preconditioner is None else preconditioner(v).detach()
        if q.shape!=v.shape or not torch.isfinite(q).all():
            raise ArithmeticError('Invalid preconditioner')
        return q
    x=torch.zeros_like(rhs) if x0 is None else x0.detach().clone()
    norm_b=float(rhs.norm());history=[]
    if norm_b==0:
        return SolveResult(torch.zeros_like(rhs),True,0.,0,'ZERO_RHS',wall_time=time.perf_counter()-started)
    r=rhs-A(x) if x0 is not None else rhs.clone()
    z=M(r);rz=float(r@z);p=z.clone()
    if float(r.norm())/norm_b<=rtol:
        err=float((A(x)-rhs).norm())
        return SolveResult(x,err/norm_b<=rtol,err/norm_b,0,'CONVERGED',err,time.perf_counter()-started,calls)
    status='ITERATION_LIMIT';it=0
    if rz<=0:
        status='INVALID_PRECONDITIONER'
    else:
        for it in range(1,max_iter+1):
            if callback is not None:callback()
            ap=A(p);pap=float(p@ap)
            if pap<=0:
                status='NON_SPD';break
            alpha=rz/pap
            x=x+alpha*p;r=r-alpha*ap
            estimated=float(r.norm())/norm_b
            history.append(estimated)
            # Refresh residual periodically. On unreliable residual convergence, restart direction.
            refresh=estimated<=rtol or it%true_every==0
            if refresh:
                r=rhs-A(x)
                true=float(r.norm())/norm_b
                if true<=rtol:
                    status='CONVERGED';break
            z=M(r);new_rz=float(r@z)
            if new_rz<=0:
                status='BREAKDOWN';break
            p=z.clone() if refresh else z+(new_rz/rz)*p
            rz=new_rz
    absolute=float((A(x)-rhs).norm())
    rel=absolute/norm_b
    success=rel<=rtol and status not in ('NON_SPD','INVALID_PRECONDITIONER')
    if success:status='CONVERGED'
    return SolveResult(x.detach(),success,rel,it,status,absolute,time.perf_counter()-started,calls,history)


def block_solve(op,rhs,damping,schema='coarse',*,rtol=1e-5,max_iter=1000,diagonal=None,callback=None):
    if damping<=0:raise ValueError('Block GGN oracle requires positive damping')
    result=torch.empty_like(rhs);receipts=[]
    for i,ids in enumerate(op.layout.group_indices(schema,device=rhs.device)):
        pre=None if diagonal is None else (lambda v,ids=ids:v/diagonal[ids])
        sol=cg(lambda v,i=i:op.block_matvec(i,v,damping,schema),rhs[ids],rtol=rtol,max_iter=max_iter,preconditioner=pre,callback=callback)
        result[ids]=sol.direction;receipts.append(sol)
    return result,receipts


def hutchinson_diagonal(op,damping,probes=8,seed=20261102):
    if probes<1:raise ValueError('Positive number of preconditioner probes required')
    rng=torch.Generator(device=op.theta.device);rng.manual_seed(seed)
    diagonal=torch.zeros_like(op.theta)
    for _ in range(probes):
        z=(2*torch.randint(2,op.theta.shape,generator=rng,device=op.theta.device)-1).to(op.theta.dtype)
        diagonal+=z*op.raw_ggn(z)/probes
    clipped=(diagonal<0)
    # Clipping an approximate PRECONDITIONER does not alter Q or its true-residual qualification.
    d=diagonal.clamp_min(0)+damping
    return d,{'probes':probes,'seed':seed,'negative_estimate_fraction':float(clipped.float().mean()),'role':'iteration_preconditioner_only'}
