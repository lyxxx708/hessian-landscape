import numpy as np
from dln import *
np.set_printoptions(precision=4, suppress=True, linewidth=150)
L,d,N=12,10,32
for seed in [0,1,2]:
    rng=np.random.default_rng(seed)
    shp=shapes(d,[d]*(L-1),d); Ws=orth_init(shp,1.0,rng)
    X=rng.standard_normal((d,N)); T=rng.standard_normal((d,d))/np.sqrt(d); Y=T@X
    sizes=[d*d]*L
    G,JM=ggn(Ws,X,d); H=hessian(Ws,X,Y)
    V=gauge_basis(Ws); Pg,rg=proj(V)
    ev=np.linalg.eigvalsh(G); rankG=(ev>1e-10*ev.max()).sum()
    P0=np.eye(G.shape[0])-proj(JM.T)[0]
    print(f"\n=== seed {seed}: P={G.shape[0]} rank(GGN)={rankG} gauge dim={rg} ||P_null-P_gauge||={np.linalg.norm(P0-Pg):.2e}")
    bm=block_metrics(Pg,sizes); off=bm['norms'][~np.eye(L,dtype=bool)]
    print(" P_gauge offdiag block norms: min %.4f max %.4f (pred d/L=%.4f); diag %.4f (pred d(1-1/L)=%.4f)"%(off.min(),off.max(),d/L,bm['norms'][0,0],d*(1-1/L)))
    for lam in [1e-1,1e-3,1e-8]:
        RG=np.linalg.inv(G+lam*np.eye(G.shape[0])); b=block_metrics(RG,sizes)
        print(f" GGN  λ={lam:g}: rms ratio k=1..11 {b['rms_ratio'][1:]} offdiag mass {b['offdiag']:.4f}")
    lamH=np.linalg.eigvalsh(H)
    print(f" exact H: min eig {lamH.min():.3f}, #neg {np.sum(lamH< -1e-9)}, ||H-GGN||/||H|| {np.linalg.norm(H-G)/np.linalg.norm(H):.3f}")
    w,U=np.linalg.eigh(H); neg=U[:,w<-1e-9]
    print(f" fraction of negative-eigvec energy inside gauge tangent space: {np.linalg.norm(Pg@neg)**2/neg.shape[1]:.4f}")
    for lam in [1e-3,1e-1]:
        RH=np.linalg.inv(H+lam*np.eye(H.shape[0])); b=block_metrics(RH,sizes)
        print(f" H    λ={lam:g}: min|μ+λ|={np.abs(lamH+lam).min():.2e} rms ratio {b['rms_ratio'][1:]} offdiag {b['offdiag']:.4f}")
print("\nclosed form 1/(L-1) =",1/(L-1)," pure-projector offdiag mass 1/L =",1/L)
