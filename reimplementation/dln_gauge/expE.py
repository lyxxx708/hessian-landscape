# Does the gauge "plateau" ever reach a gradient-sandwiched quantity (Newton step / influence score)?
import numpy as np, scipy.optimize as so
from dln import *
din,dout,h,L,N=8,8,12,8,50
shp=shapes(din,[h]*(L-1),dout)
rng=np.random.default_rng(0)
Ws=orth_init(shp,0.95,rng); X=rng.standard_normal((din,N)); T=rng.standard_normal((dout,din))/np.sqrt(din); Y=T@X
fg=lambda t: loss_grad(t,shp,X,Y)
def cb(intermediate_result):
    if intermediate_result.fun<5.3e-7: raise StopIteration
r=so.minimize(fg,flat(Ws),jac=True,method='L-BFGS-B',callback=cb,options=dict(maxiter=20000,gtol=1e-14,ftol=1e-18))
th=r.x; Ws=unflat(th,shp); f,g=fg(th)
G,JM=ggn(Ws,X,dout); H=hessian(Ws,X,Y); P=th.size
P0=np.eye(P)-proj(JM.T)[0]
# per-example gradients (train point i, test point = fresh sample)
def g_one(x,y): return loss_grad(th,shp,x[:,None],y[:,None])[1]
xt=rng.standard_normal(din); gt=g_one(xt,T@xt); gi=[g_one(X[:,i],Y[:,i]) for i in range(N)]
print(f"loss {f:.2e}; |P0 g|/|g| full-batch {np.linalg.norm(P0@g)/np.linalg.norm(g):.1e}, per-example max {max(np.linalg.norm(P0@q)/np.linalg.norm(q) for q in gi):.1e}")
print(" lambda | GGN: |P0 R g|/|R g|  | exact H: |P0 R g|/|R g|  influence corr(H vs GGN) over 50 train pts")
for lam in [1e-8,1e-6,1e-4,1e-2]:
    RG=np.linalg.inv(G+lam*np.eye(P)); RH=np.linalg.inv(H+lam*np.eye(P))
    sG=RG@g; sH=RH@g
    infG=np.array([gt@RG@q for q in gi]); infH=np.array([gt@RH@q for q in gi])
    rho=np.corrcoef(np.argsort(np.argsort(infG)),np.argsort(np.argsort(infH)))[0,1]
    print(f" {lam:6.0e} |      {np.linalg.norm(P0@sG)/np.linalg.norm(sG):8.1e}       |        {np.linalg.norm(P0@sH)/np.linalg.norm(sH):8.2f}          |  Spearman {rho:+.3f}")
