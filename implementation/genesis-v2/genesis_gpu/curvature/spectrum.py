import torch


def power_scale(op,iterations=30,seed=9001,callback=None):
    generator=torch.Generator(device=op.theta.device);generator.manual_seed(seed)
    v=torch.randn(op.theta.shape,device=op.theta.device,dtype=op.theta.dtype,generator=generator)
    v=v/v.norm();value=0.
    for _ in range(iterations):
        if callback:callback()
        w=op.raw_ggn(v);norm=float(w.norm())
        if norm==0:
            return {'value':0.,'ritz_residual':0.,'iterations':iterations,'certified_upper_bound':False}
        v=w/norm
    w=op.raw_ggn(v);value=float(v@w)
    if value < -1e-8*max(1.,float(w.norm())):
        raise ArithmeticError('GGN power iteration found negative quadratic form')
    return {'value':max(value,0.),'ritz_residual':float((w-value*v).norm()),'iterations':iterations,'certified_upper_bound':False}


def lanczos(apply,prototype,steps=32,seed=991,callback=None):
    rng=torch.Generator(device=prototype.device);rng.manual_seed(seed)
    q=torch.randn(prototype.shape,device=prototype.device,dtype=prototype.dtype,generator=rng);q/=q.norm()
    basis=[];a=[];b=[];previous=torch.zeros_like(q);beta=0.
    for k in range(min(steps,len(q))):
        if callback:callback()
        basis.append(q)
        w=apply(q)-beta*previous
        alpha=float(q@w);w-=alpha*q
        for v in basis: w-=torch.dot(v,w)*v
        a.append(alpha);newbeta=float(w.norm())
        if newbeta<1e-10:break
        if k<min(steps,len(q))-1:b.append(newbeta)
        previous=q;q=w/newbeta;beta=newbeta
    T=torch.diag(torch.tensor(a,dtype=torch.float64))
    if b:
        off=torch.tensor(b[:len(a)-1],dtype=torch.float64)
        T+=torch.diag(off,1)+torch.diag(off,-1)
    eig=torch.linalg.eigvalsh(T)
    return {'ritz_values':eig.tolist(),'krylov_dimension':len(a),
            'not_full_spectrum':len(a)<len(prototype),'not_spd_certificate':True}
