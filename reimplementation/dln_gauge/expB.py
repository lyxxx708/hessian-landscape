import numpy as np, scipy.optimize as so
from dln import *
np.set_printoptions(precision=4, suppress=True, linewidth=160)
din,dout,h,L,N=8,8,12,8,50
shp=shapes(din,[h]*(L-1),dout); sizes=[a*b for a,b in shp]
def run(seed, init, alpha=0.0):
    rng=np.random.default_rng(seed)
    Ws = orth_init(shp,0.95,rng) if init=='orth' else [rng.standard_normal(s)/np.sqrt(s[1]) for s in shp]
    X=rng.standard_normal((din,N)); T=rng.standard_normal((dout,din))/np.sqrt(din); Y=T@X
    def fg(t):
        f,g=loss_grad(t,shp,X,Y); return f+alpha*t@t, g+2*alpha*t
    r=so.minimize(fg,flat(Ws),jac=True,method='L-BFGS-B',options=dict(maxiter=20000,maxfun=40000,gtol=1e-13,ftol=1e-16))
    th=r.x; Ws=unflat(th,shp); f,g=fg(th)
    G,JM=ggn(Ws,X,dout); H=hessian(Ws,X,Y)+2*alpha*np.eye(th.size)
    ev=np.linalg.eigvalsh(H)
    Pg,rg=proj(gauge_basis(Ws)); Ph=proj(JM.T)[0]; P0=np.eye(th.size)-Ph
    print(f"\n--- seed {seed} init={init} alpha={alpha}: loss {f:.2e} |grad| {np.linalg.norm(g):.1e} rank J_M {np.linalg.matrix_rank(JM)} gauge dim {rg} ||P0-Pg|| {np.linalg.norm(P0-Pg):.1e}")
    print(f"  min eig H {ev.min():.3e}  ||H-GGN||/||H|| {np.linalg.norm(H-G)/np.linalg.norm(H):.2e}")
    b=block_metrics(P0,sizes); print("  P_null    rms ratio",b['rms_ratio'][1:],"offdiag %.4f"%b['offdiag'])
    for lam in [1e-4,1e-8]:
        for name,A in [('GGN',G),('H',H)]:
            R=np.linalg.inv(A+lam*np.eye(th.size)); b=block_metrics(R,sizes)
            print(f"  {name:3s} λ={lam:g} rms ratio",b['rms_ratio'][1:],"offdiag %.4f"%b['offdiag'], " ||λR-P0||/||P0|| %.2e"%(np.linalg.norm(lam*R-P0)/np.linalg.norm(P0)))
    # horizontal (gauge-fixed) part of GGN inverse
    R=np.linalg.inv(G+1e-8*np.eye(th.size)); Rh=Ph@R@Ph; b=block_metrics(Rh,sizes)
    print("  gauge-fixed Ph R Ph rms ratio",b['rms_ratio'][1:],"offdiag %.4f"%b['offdiag'])
    # Woodbury/low-rank capture of off-block part of H
    st=np.cumsum([0]+sizes); Hoff=H.copy()
    for i in range(L): Hoff[st[i]:st[i+1],st[i]:st[i+1]]=0
    s=np.linalg.svd(Hoff,compute_uv=False); cum=np.sqrt(np.cumsum(s**2)/np.sum(s**2))
    print("  H_off norm-capture at rank L-1=7: %.3f | rank 64: %.3f | rank 128: %.3f | rank 192: %.3f"%(cum[6],cum[63],cum[127],cum[191]))
    return Ws
for seed in [0,1]:
    run(seed,'orth')
run(0,'gauss')
run(0,'orth',alpha=1e-3)
