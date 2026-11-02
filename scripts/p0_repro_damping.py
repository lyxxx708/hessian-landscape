"""Diagnostic damping sweep at one fixed P0 DLN configuration.

Uses the same curvature matrix per target condition, changing only lambda.
This is a NEW synthetic reimplementation, not historical GENESIS replay.
"""
import argparse
import csv
from pathlib import Path
import numpy as np
from scripts.p0_repro import make_data, matrices, summarize


def sweep(seed, output):
    L,d,n,scale=12,10,32,.95
    output=Path(output)
    output.parent.mkdir(parents=True,exist_ok=True)
    w,x=make_data(seed,L,d,n,scale)
    pred=x.copy()
    for wi in w:pred=pred@wi.T
    lam_values=[1e-6,1e-4,1e-3,1e-2,1e-1,1.,1.1,2.]
    rows=[]
    for condition,goal in [('initial',x),('zero_residual',pred)]:
        _,_,_,H,_=matrices(w,x,goal)
        mu,U=np.linalg.eigh(H)
        for lam in lam_values:
            shifted=mu+lam
            inv=(U/shifted)@U.T
            _,ratio,mass=summarize(inv,L,d)
            err=np.linalg.norm((H+lam*np.eye(len(H)))@inv-np.eye(len(H)))/np.sqrt(len(H))
            rows.append((seed,condition,lam,float(mu.min()),float(min(abs(shifted))),
                         float(max(abs(shifted))/min(abs(shifted))),float(err),
                         float(1-mass[0]),float(min(ratio[1:])),float(max(ratio[1:])),
                         int(np.count_nonzero(shifted<=0))))
    with output.open('w',newline='') as f:
        writer=csv.writer(f)
        writer.writerow(['seed','condition','lambda','min_eig_H','min_abs_eig_H_plus_lambda',
                         'condition_2','solve_residual','offdiag_energy_mass','ratio_min_k_gt0',
                         'ratio_max_k_gt0','count_nonpositive_shifted_eig'])
        writer.writerows(rows)
    return rows


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--seed',type=int,default=20261026)
    p.add_argument('--output',default='results/p0_damping_sweep.csv')
    args=p.parse_args()
    rows=sweep(args.seed,args.output)
    print('completed',len(rows),'rows:',args.output)
