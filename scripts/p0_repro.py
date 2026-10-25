"""Reproducible GENESIS P0 benchmark (NEW REIMPLEMENTATION, not historical replay).

Only NumPy required; see P0_REPORT.md for exact definitions and evidence limits.
Usage: OPENBLAS_NUM_THREADS=2 python -m scripts.p0_repro --out results/repro
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import numpy as np


def make_data(seed, L=12, d=10, n=32, scale=.95):
    r=np.random.default_rng(seed)
    weights=[]
    for _ in range(L):
        q,R=np.linalg.qr(r.standard_normal((d,d)))
        weights.append(scale*(q*np.where(np.diag(R)<0,-1.,1.)[None,:]))
    weights=np.stack(weights)
    x=np.random.default_rng(seed+104729).standard_normal((n,d))
    return weights,x


def matrices(weights,x,target):
    L,d,_=weights.shape
    n=len(x); M=n*d; P=L*d*d
    prefix=[np.eye(d)]
    for w in weights: prefix.append(w@prefix[-1])
    suffix=[None]*(L+1);suffix[L]=np.eye(d)
    for i in range(L-1,-1,-1):suffix[i]=suffix[i+1]@weights[i]
    hidden=[x@u.T for u in prefix]
    resid=hidden[-1]-target
    J=np.concatenate([np.einsum('oa,nb->noab',suffix[i+1],hidden[i]).reshape(M,d*d)
                      for i in range(L)],axis=1)
    G=J.T@J/M
    S=np.zeros((P,P))
    for i in range(L):
        bridge=np.eye(d)
        for j in range(i+1,L):
            cross=(hidden[i].T@(resid@suffix[j+1]))/M
            blk=np.einsum('da,bc->abcd',bridge,cross).reshape(d*d,d*d)
            si=slice(i*d*d,(i+1)*d*d);sj=slice(j*d*d,(j+1)*d*d)
            S[si,sj]=blk;S[sj,si]=blk.T
            bridge=weights[j]@bridge
    return J,G,S,G+S,resid


def summarize(A,L,d):
    block=d*d
    B=A.reshape(L,block,L,block)
    norms=np.sqrt(np.einsum('iajb,iajb->ij',B,B))
    E=norms**2
    e=np.array([sum(E[i,j] for i in range(L) for j in range(L)
                    if abs(i-j)==k) for k in range(L)])
    count=np.array([L]+[2*(L-k) for k in range(1,L)])
    rms=np.sqrt(e/count)
    rel=rms/rms[0]
    mass=e/e.sum()
    maxrel=float(max(rel[1:]))
    bound=(L-1)*maxrel**2/(1+(L-1)*maxrel**2)
    assert abs(mass.sum()-1)<1e-12
    assert 1-mass[0]<=bound+1e-10
    return norms,rel,mass


def go(seed,condition,out,L=12,d=10,n=32,scale=.95,lam=.001,save_full=False):
    if lam<=0: raise ValueError('lam must be positive')
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    w,x=make_data(seed,L,d,n,scale)
    pred=x.copy()
    for wi in w:pred=pred@wi.T
    target=x if condition=='initial' else pred.copy()
    J,G,S,H,resid=matrices(w,x,target)
    eigen,V=np.linalg.eigh(H)
    shifted=eigen+lam
    inv=(V/shifted)@V.T
    rnorm,ratios,mass=summarize(inv,L,d)
    hnorm,_,_=summarize(H,L,d)
    gnorm,_,_=summarize(G,L,d)
    singular=np.linalg.svd(J,compute_uv=False)
    tol=np.finfo(float).eps*max(J.shape)*singular[0]
    rank=int((singular>tol).sum())
    assert rank<=d*d
    assert np.linalg.norm(H-G-S)/max(np.linalg.norm(H),1e-15)<1e-12
    err=float(np.linalg.norm((H+lam*np.eye(len(H)))@inv-np.eye(len(H)))/np.sqrt(len(H)))
    assert err<1e-7
    name=f'P0_L{L}_d{d}_B{n}_s{seed}_{condition}'
    values={
        'evidence':'NEW_INDEPENDENT_REIMPLEMENTATION_NOT_HISTORICAL_REPLAY',
        'seed':seed,'condition':condition,'L':L,'d':d,'n':n,'scale':scale,'lambda':lam,
        'target':'identity' if condition=='initial' else 'predictions_at_same_weights',
        'loss':'0.5*mean((prediction-target)**2)',
        'rank_J':rank,'num_parameters':L*d*d,
        'H_min_eig':float(eigen[0]),
        'H_negative_eigenvalues':int((eigen<-1e-10*max(1.,max(abs(eigen)))).sum()),
        'H_GGN_gap_fro':float(np.linalg.norm(S)/max(np.linalg.norm(H),1e-15)),
        'cond_shifted_H_2':float(max(abs(shifted))/min(abs(shifted))),
        'min_abs_shifted_eig':float(min(abs(shifted))),
        'relative_solve_residual':err,'offdiag_energy_mass':float(1-mass[0]),
        'distance_ratios':ratios.tolist(),'distance_energy_mass':mass.tolist(),
        'block_width':d*d,'sha256_script':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    with (out/(name+'_distance.csv')).open('w',newline='') as f:
        wr=csv.writer(f);wr.writerow(['k','RMS_normalized','energy_mass'])
        wr.writerows((k,repr(float(ratios[k])),repr(float(mass[k]))) for k in range(L))
    for label,arr in [('R',rnorm),('H',hnorm),('GGN',gnorm)]:
        np.savetxt(out/(name+'_'+label+'_block_norms.csv'),arr,delimiter=',',fmt='%.17g')
    eigg=np.zeros(len(eigen));eigg[-rank:]=np.sort(singular[:rank]**2/(n*d))
    np.savetxt(out/(name+'_spectrum.csv'),np.column_stack((eigen,eigg)),delimiter=',',fmt='%.17g',
               header='eigen_H,eigen_GGN_via_J_SVD',comments='')
    if save_full:
        np.savez_compressed(out/(name+'_matrices.npz'),W=w,X=x,target=target,J=J,GGN=G,S=S,H=H,R=inv)
    values['artifacts_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest()
                                for p in sorted(out.glob(name+'_*'))}
    (out/(name+'_summary.json')).write_text(json.dumps(values,indent=2,allow_nan=False)+'\n')
    return values


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',default='results/repro')
    p.add_argument('--seed',type=int,default=20261026)
    p.add_argument('--condition',choices=['initial','zero_residual'],default='initial')
    p.add_argument('--all',action='store_true',help='all three seeds and both conditions')
    p.add_argument('--save-full',action='store_true')
    a=p.parse_args()
    runs=[(s,c) for s in (20261026,20261027,20261028)
          for c in ('initial','zero_residual')] if a.all else [(a.seed,a.condition)]
    for seed,cond in runs:
        z=go(seed,cond,a.out,save_full=a.save_full)
        print(f"{seed} {cond}: rankJ={z['rank_J']} negativeEigH={z['H_negative_eigenvalues']} offdiag={z['offdiag_energy_mass']:.6f} residual={z['relative_solve_residual']:.3g}")

if __name__=='__main__':main()
