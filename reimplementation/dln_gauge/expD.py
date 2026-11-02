import numpy as np, scipy.optimize as so
from dln import *
np.set_printoptions(precision=3, suppress=True, linewidth=160)
din,dout,h,L,N=8,8,12,8,50
shp=shapes(din,[h]*(L-1),dout); sizes=[a*b for a,b in shp]; st=np.cumsum([0]+sizes)
for seed,target in [(0,5.3e-7),(0,1e-3)]:
    rng=np.random.default_rng(seed)
    Ws=orth_init(shp,0.95,rng); X=rng.standard_normal((din,N)); T=rng.standard_normal((dout,din))/np.sqrt(din); Y=T@X
    fg=lambda t: loss_grad(t,shp,X,Y)
    def cb(intermediate_result):
        if intermediate_result.fun<target: raise StopIteration
    r=so.minimize(fg,flat(Ws),jac=True,method='L-BFGS-B',callback=cb,options=dict(maxiter=20000,gtol=1e-14,ftol=1e-18))
    Ws=unflat(r.x,shp); f,g=fg(r.x)
    G,JM=ggn(Ws,X,dout); H=hessian(Ws,X,Y); w,U=np.linalg.eigh(H)
    Pg,_=proj(gauge_basis(Ws)); P0=np.eye(H.shape[0])-proj(JM.T)[0]
    print(f"\n=== seed {seed} loss {f:.2e}  |grad| {np.linalg.norm(g):.1e}")
    tiny=np.abs(w)<1e-10*np.abs(w).max()
    print(f" eigenvalues |mu|<1e-10*max: {tiny.sum()}  (largest such |mu| = {np.abs(w[tiny]).max() if tiny.any() else 0:.1e})")
    Z=U[:,tiny]
    if tiny.any():
        print(f" zero modes inside gauge space: {np.linalg.norm(Pg@Z)**2/Z.shape[1]:.4f}")
        bw=np.array([[np.linalg.norm(Z[st[i]:st[i+1],k])**2 for i in range(L)] for k in range(Z.shape[1])]).sum(0)
        print(" zero-mode energy by layer:", bw/bw.sum())
    gauge_mu=np.abs(w[(~tiny)&(np.einsum('ij,ij->j',U,Pg@U)>0.5)])
    print(f" gauge-sector |mu| (non-zero): min {gauge_mu.min():.1e}  median {np.median(gauge_mu):.1e}  max {gauge_mu.max():.1e}")
    print("   lambda    exactH rms(k=1)  rms(k=L-1)  ||lamR-P0||/||P0||   | GGN rms(k=1) ||lamR-P0||/||P0||")
    for lam in 10.0**np.arange(-10,0):
        R=np.linalg.inv(H+lam*np.eye(H.shape[0])); b=block_metrics(R,sizes)
        RG=np.linalg.inv(G+lam*np.eye(H.shape[0])); bg=block_metrics(RG,sizes)
        print(f"  {lam:7.0e}    {b['rms_ratio'][1]:8.4f}     {b['rms_ratio'][-1]:8.4f}     {np.linalg.norm(lam*R-P0)/np.linalg.norm(P0):9.2e}        | {bg['rms_ratio'][1]:8.4f}  {np.linalg.norm(lam*RG-P0)/np.linalg.norm(P0):9.2e}")
