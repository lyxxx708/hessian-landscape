"""Gradient-conditioned quadratic utility and loss-curvature task response."""
import math
import torch
from genesis_gpu.solvers.cg import cg, block_solve, hutchinson_diagonal


def quadratic_utility(g,full,block,q_block):
    if not all(torch.isfinite(t).all() for t in (g,full,block,q_block)):
        return {'status':'NUMERIC_UNRESOLVED','delta':None,'eta':None,'reason':'NONFINITE'}
    if float(g.norm())<=1e-12:
        return {'status':'INELIGIBLE_ZERO_GRADIENT','delta':None,'eta':None}
    gp=float(g@block);gfull=float(g@full);bqb=float(block@q_block)
    if bqb<=0 or gfull>=0 or gp>=0:
        return {'status':'NUMERIC_UNRESOLVED','delta':None,'eta':None,'reason':'NONPOSITIVE_GAIN'}
    Fstar=-gfull/2;Fblock=gp*gp/(2*bqb);eta=Fblock/Fstar
    if not math.isfinite(eta) or eta>1+1e-6 or eta<0:
        return {'status':'NUMERIC_UNRESOLVED','delta':None,'eta':None,'reason':'UTILITY_OUT_OF_BOUNDS','eta_raw':eta}
    return {'status':'NUMERIC_VALID','eta':min(1.,eta),'eta_raw':eta,'delta':max(0.,1-eta),
            'alpha_Q':-gp/bqb,'F_star':Fstar,'F_block':Fblock,
            'raw_g_dot_full':gfull,'raw_g_dot_block':gp,'raw_block_dot_Qblock':bqb}


def task_response_metrics(op,full,block,validation=None):
    u=op.jvp(full);v=op.jvp(block)
    wv=op.metric_action(v);uu=float((u*op.metric_action(u)).sum());vv=float((v*wv).sum())
    if min(uu,vv)<=1e-24:
        return {'alpha_task':None,'E_task':None,'E_val':None,'task_status':'NOT_ELIGIBLE'}
    alpha=max(0.,float((u*wv).sum())/vv)
    error=u-alpha*v;ee=float((error*op.metric_action(error)).sum())
    if ee< -1e-10*uu:
        return {'alpha_task':alpha,'E_task':None,'E_val':None,'task_status':'NUMERIC_UNRESOLVED'}
    result={'alpha_task':alpha,'E_task':math.sqrt(max(0.,ee)/uu),'E_val':None,
            'raw_train_uWu':uu,'raw_train_vWv':vv,'raw_train_uWv':float((u*wv).sum()),
            'task_status':'ELIGIBLE','raw_logit_error_secondary':float(error.norm()/u.norm().clamp_min(1e-30))}
    if validation is not None:
        uv=validation.jvp(full);vb=validation.jvp(block);e=uv-alpha*vb
        denom=float((uv*validation.metric_action(uv)).sum());num=float((e*validation.metric_action(e)).sum())
        if denom>1e-24 and num>=-1e-10*denom:
            result['E_val']=math.sqrt(max(0.,num)/denom)
        result.update(raw_val_error_We=num,raw_val_uWu=denom,validation_alpha_source='train_only')
    return result


def line_search(op,direction,steps,validation=None,callback=None):
    base=float(op.objective(op.theta));best=base;best_step=0.;records=[]
    with torch.no_grad():
        for alpha in steps:
            if callback:callback()
            loss=float(op.objective(op.theta+alpha*direction))
            finite=math.isfinite(loss)
            records.append({'step':alpha,'loss':loss if finite else None,'finite':finite})
            if finite and loss<best:best=loss;best_step=alpha
        val_gain=None
        if validation is not None:
            val_base=float(validation.objective(validation.theta))
            val_new=float(validation.objective(validation.theta+best_step*direction))
            val_gain=val_base-val_new if math.isfinite(val_new) else None
    return {'initial_loss':base,'best_loss':best,'gain':base-best,'step':best_step,'validation_gain':val_gain,'trials':records}


def cheap_block_energy(op,schema='coarse',probes=2,seed=20261102,callback=None):
    """Small matched-cost stochastic GGN energy proxy, NOT an inverse oracle.

    Each global probe and each restricted diagonal action is charged. The ratio
    is noisy, possibly negative, and is not clipped or advertised as unbiased.
    """
    ids=op.layout.group_indices(schema,device=op.theta.device);rng=torch.Generator(device=op.theta.device)
    rng.manual_seed(seed);start=op.matvec_count;total=[];diagonal=[]
    for _ in range(probes):
        if callback:callback()
        z=(2*torch.randint(0,2,op.theta.shape,generator=rng,device=op.theta.device)-1).to(op.theta.dtype)
        gz=op.raw_ggn(z);total.append(float(gz.square().sum()));diag=0.
        for i,idx in enumerate(ids):
            if callback:callback()
            diag+=float(op.block_matvec(i,z[idx],schema=schema).square().sum())
        diagonal.append(diag)
    denominator=sum(total)
    return {'offdiag_fraction_proxy':1-sum(diagonal)/denominator if denominator>1e-30 else None,
            'raw_total_energy':total,'raw_diagonal_energy':diagonal,'probe_seed':seed,
            'matvecs':op.matvec_count-start,'uses_full_inverse':False,
            'qualification':'cheap stochastic ratio, not unbiased; retain negative noisy estimates'}


def evaluate_utility(op,damping,*,schema='coarse',rtol=1e-5,max_iter=1000,validation=None,
                     line_search=(0.,.01,.03,.1,.3,1.,3.),stability_factor=.1,delta_stability=.005,
                     preconditioner_probes=0,short_steps=8,callback=None):
    if damping<=0:raise ValueError('Positive SPD damping required')
    g=op.gradient();start_count=op.matvec_count
    if float(g.norm())<=1e-12:
        return {'status':'INELIGIBLE_ZERO_GRADIENT','delta':None,'eta':None},{}
    diagonal=None;pre_receipt=None
    if preconditioner_probes:
        diagonal,pre_receipt=hutchinson_diagonal(op,damping,preconditioner_probes)
    pre=None if diagonal is None else lambda v:v/diagonal
    Q=lambda v:op.matvec(v,damping)
    first=cg(Q,-g,rtol=rtol,max_iter=max_iter,preconditioner=pre,callback=callback)
    block1,br1=block_solve(op,-g,damping,schema,rtol=rtol,max_iter=max_iter,diagonal=diagonal,callback=callback)
    receipt={'full_solve':first.receipt(),'block_solves':[s.receipt() for s in br1],'preconditioner':pre_receipt}
    if not first.converged or not all(s.converged for s in br1):
        return {**receipt,'status':'NUMERIC_UNRESOLVED','reason':'ORACLE_SOLVE_FAILED','delta':None,'eta':None},{}
    v1=quadratic_utility(g,first.direction,block1,Q(block1))
    tight=max(rtol*stability_factor,5*torch.finfo(g.dtype).eps)
    second=cg(Q,-g,rtol=tight,max_iter=max_iter*2,preconditioner=pre,callback=callback)
    block2,br2=block_solve(op,-g,damping,schema,rtol=tight,max_iter=max_iter*2,diagonal=diagonal,callback=callback)
    receipt.update(tight_full_solve=second.receipt(),tight_block_solves=[s.receipt() for s in br2],tight_rtol=tight)
    if not second.converged or not all(s.converged for s in br2):
        return {**receipt,'status':'NUMERIC_UNRESOLVED','reason':'TIGHT_ORACLE_FAILED','delta':None,'eta':None},{}
    full=second.direction;block=block2;qb=Q(block)
    result=quadratic_utility(g,full,block,qb)
    if result['delta'] is None or v1['delta'] is None:
        return {**receipt,**result,'reason':'INVALID_UTILITY'},{}
    stability=abs(result['delta']-v1['delta'])
    result.update(receipt,delta_stability=stability,gradient_norm=float(g.norm()),parameter_norm=float(op.theta.norm()),damping=damping,schema=schema)
    if stability>delta_stability:
        result.update(status='NUMERIC_UNRESOLVED',reason='TOLERANCE_SENSITIVITY')
    result.update(task_response_metrics(op,full,block,validation))
    residual=g+result['alpha_Q']*qb
    dinv_res,rr=block_solve(op,residual,damping,schema,rtol=tight,max_iter=max_iter*2,diagonal=diagonal,callback=callback)
    den=float(-g@block);num=float(residual@dinv_res)
    result['cheap_rho']=math.sqrt(max(0.,num)/den) if all(s.converged for s in rr) and num>=-1e-12*den else None
    result['rho_block_solve_receipts']=[s.receipt() for s in rr]
    short=cg(Q,-g,rtol=tight,max_iter=short_steps,callback=callback)
    result['short_cg']=short.receipt()
    result['short_cg_quadratic_gain']=float(-g@short.direction-.5*short.direction@Q(short.direction))
    # A separate reference receives the measured matvec budget of the precise
    # layerwise direction plus its rho proxy. The full-GN oracle cost is NOT free
    # online information and is excluded. Periodic and final residual checks count.
    energy_proxy=cheap_block_energy(op,schema,callback=callback)
    result['block_energy_proxy']=energy_proxy
    budget=max(4,sum(r.matvecs for r in br2)+sum(r.matvecs for r in rr)+2+short.matvecs+energy_proxy['matvecs'])
    matched_iters=max(1,int((budget-2)*20/21))
    matched=cg(Q,-g,rtol=tight,max_iter=matched_iters,callback=callback,true_every=20)
    result['matched_cg']={'matvec_budget':budget,'solve':matched.receipt(),
                          'budget_definition':'tight block solves + rho block solves + short CG + block-energy proxy + two Q actions',
                          'wall_clock_equivalence_claimed':False}
    result['matched_cg_quadratic_gain']=float(-g@matched.direction-.5*matched.direction@Q(matched.direction))
    scales=[float(op.theta[ids].norm()) for ids in op.layout.group_indices(schema,device=g.device)]
    result['layer_scale_cv']=float(torch.tensor(scales).std(unbiased=False)/torch.tensor(scales).mean().clamp_min(1e-30))
    # Same fixed number of trial losses per comparator. Scalar fitting uses training data only.
    search_fn=globals()['line_search']
    result['line_search_full']=search_fn(op,full,line_search,validation,callback)
    result['line_search_block']=search_fn(op,block,line_search,validation,callback)
    result['line_search_short_cg']=search_fn(op,short.direction,line_search,validation,callback)
    result['line_search_matched_cg']=search_fn(op,matched.direction,line_search,validation,callback)
    result['matvecs_total']=op.matvec_count-start_count
    vectors={'gradient':g,'full':full,'block':block,'Qblock':qb,'short_cg':short.direction,'matched_cg':matched.direction}
    return result,vectors
