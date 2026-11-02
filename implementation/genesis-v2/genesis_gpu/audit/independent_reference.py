"""Independent math path: reverse autograd Jacobian + explicit output Hessian.

Does not call FrozenOperator.raw_ggn, gradient, hvp or science utility aggregators.
"""
import copy
import torch
import torch.nn.functional as F
from torch.func import functional_call


def dense_reference(op,*,with_hessian=True,parameter_limit=2048,output_limit=4096):
    if len(op.theta)>parameter_limit or op.prediction.numel()>output_limit:
        raise ValueError('Independent dense oracle exceeds declared resource limit')
    theta=op.theta.detach().clone().requires_grad_(True)
    model=copy.deepcopy(op.model)
    buffers={k:v.clone() for k,v in op.buffers.items()}
    entries=[(e.name,e.shape,e.start,e.stop) for e in op.layout.entries]
    def f(t):
        params={name:t[a:b].reshape(shape) for name,shape,a,b in entries}
        return functional_call(model,(params,{k:v.clone() for k,v in buffers.items()}),(op.inputs,),tie_weights=True,strict=True)
    def loss(t):
        z=f(t)
        if op.loss.kind=='mse':
            return (z-op.targets).square().sum()/(2*z.numel())
        mask=op.targets.reshape(-1)!=op.loss.ignore_index
        return F.cross_entropy(z.reshape(-1,z.shape[-1])[mask],op.targets.reshape(-1)[mask],reduction='mean')
    output=f(theta)
    # autograd.functional uses a reverse-mode Jacobian, not the main torch.func operator.
    J=torch.autograd.functional.jacobian(lambda t:f(t).reshape(-1),theta,vectorize=False).detach()
    if op.loss.kind=='mse':
        W=torch.eye(output.numel(),dtype=theta.dtype,device=theta.device)/output.numel()
    else:
        probabilities=output.detach().reshape(-1,output.shape[-1]).softmax(-1)
        valid=(op.targets.reshape(-1)!=op.loss.ignore_index)
        n=int(valid.sum())
        blocks=[(torch.diag(p)-p[:,None]*p[None,:])/n if bool(v) else torch.zeros(len(p),len(p),dtype=p.dtype,device=p.device)
                for p,v in zip(probabilities,valid)]
        W=torch.block_diag(*blocks)
    gradient=torch.autograd.grad(loss(theta),theta)[0].detach()
    result={'J':J,'W':W,'G':J.T@W@J,'gradient':gradient}
    if with_hessian:
        result['H']=torch.autograd.functional.hessian(loss,theta,vectorize=False).detach()
    return result


def independent_ggn_vector(op,vector):
    """Large-snapshot alternate reverse-over-reverse JVP + elementary softmax metric."""
    t=op.theta.detach().clone().requires_grad_(True)
    model=copy.deepcopy(op.model)
    entries=[(e.name,e.shape,e.start,e.stop) for e in op.layout.entries]
    def f(theta):
        p={name:theta[a:b].reshape(shape) for name,shape,a,b in entries}
        return functional_call(model,(p,{k:v.clone() for k,v in op.buffers.items()}),(op.inputs,),tie_weights=True,strict=True)
    pred=f(t)
    u=torch.autograd.functional.jvp(f,t,vector,strict=False)[1]
    if op.loss.kind=='mse':
        w=u/pred.numel()
    else:
        probs=pred.detach().softmax(-1)
        mask=op.targets!=op.loss.ignore_index
        w=(probs*u-probs*(probs*u).sum(-1,keepdim=True))*mask.unsqueeze(-1)/mask.sum()
    return torch.autograd.grad(pred,t,grad_outputs=w.detach())[0].detach()
