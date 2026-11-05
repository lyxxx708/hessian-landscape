"""Independent NumPy diagnostics. Dense-only: never allocate these on large models."""
from __future__ import annotations
import numpy as np

def partition(n,groups):
    groups=[np.asarray(x,dtype=int) for x in groups]
    all_ids=np.concatenate(groups) if groups else np.array([],dtype=int)
    if sorted(all_ids.tolist())!=list(range(n)):
        raise ValueError('Groups must form an exact disjoint partition')
    return groups

def ray_utility(Q,g,full,block,zero=1e-12):
    Q,g,full,block=map(np.asarray,(Q,g,full,block))
    if any(not np.isfinite(x).all() for x in (Q,g,full,block)):raise ValueError('Nonfinite input')
    gn=float(np.linalg.norm(g))
    if gn<=zero:return {'status':'ZERO_GRADIENT_UNASSESSED','delta':None,'F_star':None}
    residual=float(np.linalg.norm(Q@full+g)/gn)
    if residual>1e-5:raise ValueError('Full direction is not a qualified reference')
    F=float(-g@full-.5*full@Q@full); gp=float(g@block);bqb=float(block@Q@block)
    if F<=0 or bqb<=0 or gp>=0:raise ValueError('Nonpositive descent/gain')
    Fb=gp*gp/(2*bqb);delta=1-Fb/F
    if delta< -1e-6 or delta>1+1e-6:raise ValueError('Utility outside feasible interval')
    return {'status':'VALID','delta':float(delta),'F_star':F,'F_block':Fb,
            'alpha_block':-gp/bqb,'full_relative_residual':residual,
            'absolute_block_gain_gap':F-Fb}

def offdiag_energy(M,groups):
    gs=partition(len(M),groups);total=float(np.square(M).sum())
    diagonal=sum(float(np.square(M[np.ix_(g,g)]).sum()) for g in gs)
    return (total-diagonal)/total if total>0 else None

def dense_geometry(G,g,damping,groups,rank_rtol=1e-8,eigensystem=None,inverse=None):
    G=np.asarray(G,dtype=float);g=np.asarray(g,dtype=float);n=len(g)
    if damping<=0 or G.shape!=(n,n):raise ValueError('Invalid dense operator')
    partition(n,groups)
    e,V=eigensystem if eigensystem is not None else np.linalg.eigh((G+G.T)/2)
    scale=max(float(np.max(np.abs(e))),np.finfo(float).tiny)
    tol=rank_rtol*scale
    if e.min()< -max(tol,1e-12):raise ValueError('GGN not PSD within tolerance')
    # Eigenvalues near 0 are numerical-null candidates, not certified exact zeros.
    near=np.abs(e)<=tol; inv=1/(e+damping)
    if np.any(e+damping<=0):raise ValueError('Damped operator is not SPD')
    R=inverse if inverse is not None else (V*inv)@V.T
    P=(V[:,near]@V[:,near].T)
    Rn=(V[:,near]*inv[near])@V[:,near].T
    Ra=R-Rn;gn=float(np.linalg.norm(g));coef=V.T@g
    energies=np.maximum(0.,coef*coef*inv)
    weights=energies/energies.sum() if energies.sum()>0 else np.zeros(n)
    order=np.argsort(weights)[::-1];cum=np.cumsum(weights[order])
    n99=int(np.searchsorted(cum,.99)+1) if energies.sum()>0 else None
    total=float(np.square(R).sum())
    return {'rank_rtol':rank_rtol,'rank_threshold':tol,'rank':int((~near).sum()),'dimension':n,
            'nullity':int(near.sum()),'min_eigenvalue':float(e.min()),'max_eigenvalue':float(e.max()),
            'null_energy_fraction':float(np.square(Rn).sum()/total),
            'gradient_null_fraction':float(np.linalg.norm(P@g)/gn) if gn else None,
            'inverse_offdiag_fraction':offdiag_energy(R,groups),
            'null_offdiag_fraction':offdiag_energy(Rn,groups),
            'active_offdiag_fraction':offdiag_energy(Ra,groups),
            'gradient_weighted_n99':n99,'spectral_gain_weights_sum':float(weights.sum()),
            'effective_gain_directions':float(1/np.square(weights).sum()) if np.square(weights).sum()>0 else None,
            'meaning':'threshold-defined near-null; n99 is descriptive, not a CG-iteration theorem'}

def hessian_diagnostics(G,H,relative_tol=1e-8,eigenvalues=None):
    G,H=np.asarray(G),np.asarray(H);H=(H+H.T)/2;G=(G+G.T)/2
    eig=eigenvalues if eigenvalues is not None else np.linalg.eigvalsh(H)
    scale=max(float(np.max(np.abs(eig))),np.finfo(float).tiny)
    tol=relative_tol*scale
    return {'relative_H_G_fro':float(np.linalg.norm(H-G)/max(np.linalg.norm(H),np.finfo(float).tiny)),
            'negative_certified_count':int((eig< -tol).sum()),'ambiguous_count':int((np.abs(eig)<=tol).sum()),
            'negative_mass_fraction':float(np.abs(eig[eig< -tol]).sum()/max(np.abs(eig).sum(),np.finfo(float).tiny)),
            'minimum_eigenvalue':float(eig.min()),'threshold':float(tol),
            'word_certified_means':'relative to chosen numerical tolerance; not interval-arithmetic proof'}

def gauge_diagnostic(G,g,damping,groups,scales):
    G,g=np.asarray(G),np.asarray(g);t=np.asarray(scales,dtype=float)
    if np.any(t<=0) or t.shape!=g.shape:raise ValueError('Positive diagonal coordinate map required')
    gs=partition(len(g),groups);Q=G+damping*np.eye(len(g));x=-np.linalg.solve(Q,g)
    def block(A,b):
        out=np.zeros_like(b)
        for idx in gs:out[idx]=-np.linalg.solve(A[np.ix_(idx,idx)],b[idx])
        return out
    base=ray_utility(Q,g,x,block(Q,g));Gp=G/t[:,None]/t[None,:];gp=g/t
    cov=Gp+np.diag(damping/t**2);iso=Gp+damping*np.eye(len(g))
    xc=-np.linalg.solve(cov,gp);xi=-np.linalg.solve(iso,gp)
    uc=ray_utility(cov,gp,xc,block(cov,gp));ui=ray_utility(iso,gp,xi,block(iso,gp))
    xn=max(float(np.linalg.norm(x)),np.finfo(float).tiny)
    return {'covariant_direction_error':float(np.linalg.norm(xc/t-x)/xn),
            'isotropic_direction_error':float(np.linalg.norm(xi/t-x)/xn),
            'covariant_delta_error':abs(uc['delta']-base['delta']),
            'isotropic_delta_change':ui['delta']-base['delta'],
            'delta_base':base['delta'],'delta_covariant':uc['delta'],'delta_isotropic':ui['delta'],
            'base_inverse_offdiag':offdiag_energy(np.linalg.inv(Q),groups),
            'isotropic_inverse_offdiag':offdiag_energy(np.linalg.inv(iso),groups),
            'interpretation':'coordinate congruence test; actual DLN forward invariance checked separately'}
