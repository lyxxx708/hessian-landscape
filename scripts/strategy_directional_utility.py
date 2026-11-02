"""Reproducible synthetic diagnostic for GENESIS strategy review (not training).

Uses the same QR-scaled depth-12, width-10 initialization, Gaussian inputs,
identity target, and mean squared loss as P0. Computes GN oracle and the
optimally-scaled ray of a block-diagonal GN update. No exact Hessian is needed.
No original 2025 checkpoints are loaded. Pure NumPy; set OPENBLAS_NUM_THREADS=2.

Run: python pilot_gradient_utility.py --out pilot_gradient_utility.csv
"""
import argparse
import csv
import math
import hashlib
from pathlib import Path
import numpy as np


def make(seed, L=12, d=10, n=32, scale=.95):
    rng=np.random.default_rng(seed)
    ws=[]
    for _ in range(L):
        q,r=np.linalg.qr(rng.standard_normal((d,d)))
        ws.append(scale*q@np.diag(np.where(np.diag(r)<0.,-1.,1.)))
    x=np.random.default_rng(seed+104729).standard_normal((n,d))
    return np.stack(ws),x


def jacobian(ws,x):
    L,d,_=ws.shape;M=len(x)*d
    prefix=[np.eye(d)]
    for w in ws:prefix.append(w@prefix[-1])
    suffix=[None]*(L+1);suffix[L]=np.eye(d)
    for i in range(L-1,-1,-1):suffix[i]=suffix[i+1]@ws[i]
    hidden=[x@f.T for f in prefix]
    J=np.concatenate([np.einsum('oa,nb->noab',suffix[i+1],hidden[i]).reshape(M,d*d)
                      for i in range(L)],axis=1)
    return J,hidden[-1]


def block_solve(J,g,lam=0.001,d=10):
    M=J.shape[0];b=d*d
    out=np.empty_like(g)
    for i in range(len(g)//b):
        sl=slice(i*b,(i+1)*b)
        ji=J[:,sl]
        out[sl]=np.linalg.solve(ji.T@ji/M+lam*np.eye(b),g[sl])
    return out


def run_seed(seed,lam=0.001):
    ws,x=make(seed)
    J,pred=jacobian(ws,x)
    M=len(x)*x.shape[1]
    g=J.T@((pred-x).ravel())/M
    if np.linalg.norm(g)<1e-10:raise ValueError('gradient near zero; no valid oracle utility')
    # Exact full GGN inverse for this gradient, via 320x320 dual solve.
    p_full=-J.T@np.linalg.solve(J@J.T+M*lam*np.eye(M),(pred-x).ravel())
    p_layer=-block_solve(J,g,lam=lam)
    def Q_times(v):return J.T@(J@v)/M+lam*v
    qp=Q_times(p_layer)
    alpha=-float(g@p_layer)/float(p_layer@qp)
    gain_full=-.5*float(g@p_full)
    gain_ray=.5*float(g@p_layer)**2/float(p_layer@qp)
    eta=gain_ray/gain_full
    residual=g+alpha*qp
    # proxy = norm_{D^-1}(g + alpha Q p_layer) / norm_{D^-1}(g)
    norm_g= float(g@(-p_layer))
    rho=math.sqrt(max(0.,float(residual@block_solve(J,residual,lam))/norm_g))
    G=J.T@J/M
    b=100
    diag_energy=sum(float(np.sum(G[i*b:(i+1)*b,i*b:(i+1)*b]**2)) for i in range(12))
    offdiag=1-diag_energy/float(np.sum(G*G))
    relative_full_res=float(np.linalg.norm(Q_times(p_full)+g)/np.linalg.norm(g))
    return {'seed':seed,'matrix_object':'GGN_plus_lambda_I','condition':'initial_nonzero_residual',
            'lambda':lam,'rank_J_bound':100,'offdiag_GGN_energy_mass':offdiag,
            'gradient_norm':float(np.linalg.norm(g)),
            'full_layer_cosine':float(p_full@p_layer/(np.linalg.norm(p_full)*np.linalg.norm(p_layer))),
            'layer_full_norm_ratio':float(np.linalg.norm(p_layer)/np.linalg.norm(p_full)),
            'oracle_scale_alpha':alpha,'oracle_utility_eta':eta,'oracle_regret_delta':1-eta,
            'cheap_residual_proxy_rho':rho,'full_GN_relative_residual':relative_full_res,
            'evidence':'SYNTHETIC_DIAGNOSTIC_NOT_HISTORICAL_OR_TRAINING'}


def counterexample(coupling=.9):
    Q=np.array([[1.,coupling],[coupling,1.]])
    def eta(g):
        inv_g=np.linalg.solve(Q,g)
        return float((g@g)**2/((g@Q@g)*(g@inv_g)))
    return {'coupling':coupling,'offdiag_energy_mass':coupling**2/(1+coupling**2),
            'gradient_eigenvector_eta':eta(np.ones(2)),
            'gradient_axis_eta':eta(np.array([1.,0.])),
            'axis_eta_exact_formula':1-coupling**2}


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--out',default='pilot_gradient_utility.csv')
    args=p.parse_args()
    rows=[run_seed(s) for s in [20261026,20261027,20261028]]
    dest=Path(args.out);dest.parent.mkdir(parents=True,exist_ok=True)
    with dest.open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]))
        writer.writeheader();writer.writerows(rows)
    ex=counterexample()
    assert abs(ex['gradient_eigenvector_eta']-1.)<1e-12
    assert abs(ex['gradient_axis_eta']-ex['axis_eta_exact_formula'])<1e-12
    for r in rows:
        assert 0<r['oracle_utility_eta']<=1+1e-12
        assert r['full_GN_relative_residual']<1e-8
    print('Synthetic P0:')
    for r in rows:
        print(r['seed'], 'coupling energy',round(r['offdiag_GGN_energy_mass'],7),
              'eta',round(r['oracle_utility_eta'],9),'cos',round(r['full_layer_cosine'],9),
              'rho',round(r['cheap_residual_proxy_rho'],9))
    print('2x2 analytic counterexample:',ex)
    print('CSV sha256',hashlib.sha256(dest.read_bytes()).hexdigest())

if __name__=='__main__':main()