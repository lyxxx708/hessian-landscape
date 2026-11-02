import numpy as np, scipy.optimize as so
from dln import *
np.set_printoptions(precision=3, suppress=True, linewidth=160)
din,dout,h,L,N=8,8,12,8,50
shp=shapes(din,[h]*(L-1),dout); sizes=[a*b for a,b in shp]
print("seed target_loss  loss     min_eig_H   neg_in_gauge  ||H-GGN||/||H||  exactH λ=1e-8 rms_ratio(k=1..7)   min|mu+lam|")
for seed in range(4):
  for target in [1e-3,5.3e-7]:
    rng=np.random.default_rng(seed)
    Ws=orth_init(shp,0.95,rng); X=rng.standard_normal((din,N)); T=rng.standard_normal((dout,din))/np.sqrt(din); Y=T@X
    fg=lambda t: loss_grad(t,shp,X,Y)
    def cb(intermediate_result):
        if intermediate_result.fun<target: raise StopIteration
    r=so.minimize(fg,flat(Ws),jac=True,method='L-BFGS-B',callback=cb,options=dict(maxiter=20000,gtol=1e-14,ftol=1e-18))
    Ws=unflat(r.x,shp); f,_=fg(r.x)
    G,_=ggn(Ws,X,dout); H=hessian(Ws,X,Y); w,U=np.linalg.eigh(H)
    Pg,_=proj(gauge_basis(Ws)); neg=U[:,w<0]
    fr=np.linalg.norm(Pg@neg)**2/max(neg.shape[1],1)
    R=np.linalg.inv(H+1e-8*np.eye(H.shape[0])); b=block_metrics(R,sizes)
    print(f"{seed:3d}  {target:8.1e}  {f:8.2e}  {w.min():10.3e}  {fr:6.3f} ({neg.shape[1]} neg)  {np.linalg.norm(H-G)/np.linalg.norm(H):9.2e}   {b['rms_ratio'][1:]}  {np.abs(w+1e-8).min():.1e}")
