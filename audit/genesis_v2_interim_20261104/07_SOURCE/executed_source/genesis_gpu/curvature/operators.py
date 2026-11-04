"""Frozen loss-specific GGN and exact Hessian-vector operators.

A new graph is built per matvec/microbatch and detached before returning.
Stochastic model state is disabled and the source model/input is deep-copied.
"""
from __future__ import annotations
import copy
import torch
from torch import Tensor
from torch.func import functional_call, jvp, vjp, grad
from genesis_gpu.contracts import LossSpec, object_sha
from .params import ParamLayout, tensor_sha, tensor_dict_sha


class FrozenOperator:
    def __init__(self,model,inputs,targets,loss: LossSpec,*,microbatch=None,jvp_mode='forward',dtype=None):
        if jvp_mode not in ('forward','reverse'):
            raise ValueError('Explicit qualified JVP mode required')
        self.model=copy.deepcopy(model).eval()
        if dtype is not None:
            self.model=self.model.to(dtype=dtype)
        self.layout=ParamLayout(self.model)
        self.theta=self.layout.flatten(self.model).detach()
        self.inputs=inputs.detach().clone().to(self.theta.device)
        if self.inputs.is_floating_point():
            self.inputs=self.inputs.to(self.theta.dtype)
        self.targets=targets.detach().clone().to(self.theta.device)
        if self.targets.is_floating_point():
            self.targets=self.targets.to(self.theta.dtype)
        self.buffers={n:b.detach().clone() for n,b in self.model.named_buffers()}
        self.loss=loss;self.jvp_mode=jvp_mode
        self.microbatch=microbatch or len(inputs)
        if self.microbatch<=0 or len(inputs)!=len(targets):
            raise ValueError('Invalid microbatch')
        self.matvec_count=0
        self.prediction=self.forward(self.theta).detach()
        self.count=loss.count(self.prediction,self.targets)
        self.identity={'parameter_layout_sha':self.layout.sha,'params_sha':tensor_sha(self.theta),
                       'buffers_sha':tensor_dict_sha(self.buffers),'batch_sha':object_sha([tensor_sha(self.inputs),tensor_sha(self.targets)]),
                       'loss_sha':object_sha(loss),'dtype':str(self.theta.dtype),'jvp_mode':jvp_mode,
                       'training_mode':False,'objective':'deterministic data loss (decoupled training weight decay excluded)'}

    def _function(self,x):
        def f(theta):
            buffers={k:v.clone() for k,v in self.buffers.items()}
            return functional_call(self.model,(self.layout.unflatten(theta),buffers),(x,),tie_weights=True,strict=True)
        return f

    def forward(self,theta=None,inputs=None):
        theta=self.theta if theta is None else theta
        x=self.inputs if inputs is None else inputs
        return self._function(x)(theta)

    def objective(self,theta):
        return self.loss.value(self.forward(theta),self.targets)

    def chunks(self):
        for start in range(0,len(self.inputs),self.microbatch):
            x=self.inputs[start:start+self.microbatch]
            y=self.targets[start:start+self.microbatch]
            if self.loss.kind=='ce' and not (y!=self.loss.ignore_index).any():
                continue
            yield x,y

    def _jvp(self,f,v):
        if self.jvp_mode=='forward':
            return jvp(f,(self.theta,),(v,))[1]
        # Explicit qualified fallback; never a silent change selected from science results.
        return torch.autograd.functional.jvp(f,self.theta,v,create_graph=False,strict=False)[1]

    def raw_ggn(self,v:Tensor):
        if v.shape!=self.theta.shape or not torch.isfinite(v).all():
            raise ValueError('Invalid GGN vector')
        total=torch.zeros_like(self.theta)
        for x,y in self.chunks():
            f=self._function(x)
            pred,pullback=vjp(f,self.theta)
            u=self._jvp(f,v)
            w=self.loss.output_metric(pred,y,u,denominator=self.count)
            total=total+pullback(w.detach())[0].detach()
        self.matvec_count+=1
        return total.detach()

    def matvec(self,v,damping=0.):
        if damping<0:
            raise ValueError('GGN shift cannot be negative')
        return self.raw_ggn(v)+damping*v

    def gradient(self):
        g=torch.zeros_like(self.theta)
        for x,y in self.chunks():
            f=self._function(x)
            part=grad(lambda t:self.loss.value(f(t),y,denominator=self.count))(self.theta)
            g+=part.detach()
        return g

    def hvp(self,v):
        h=torch.zeros_like(self.theta)
        for x,y in self.chunks():
            f=self._function(x)
            objective=lambda t:self.loss.value(f(t),y,denominator=self.count)
            if self.jvp_mode=='forward':
                part=jvp(grad(objective),(self.theta,),(v,))[1]
            else:
                part=torch.autograd.functional.hvp(objective,self.theta,v,create_graph=False)[1]
            h+=part.detach()
        return h

    def jvp(self,v):
        return self._jvp(self._function(self.inputs),v).detach()

    def vjp(self,u):
        _,pb=vjp(self._function(self.inputs),self.theta)
        return pb(u)[0].detach()

    def metric_action(self,u):
        return self.loss.output_metric(self.prediction,self.targets,u)

    def block_matvec(self,block_id,u,damping=0.,schema='coarse'):
        ids=self.layout.group_indices(schema,device=self.theta.device)[block_id]
        if len(u)!=len(ids):
            raise ValueError('Block vector has wrong size')
        v=torch.zeros_like(self.theta).index_copy(0,ids,u)
        return self.raw_ggn(v)[ids]+damping*u

    def validation_operator(self,x,y):
        return FrozenOperator(self.model,x,y,self.loss,microbatch=self.microbatch,jvp_mode=self.jvp_mode,dtype=self.theta.dtype)

    def diagnostics(self,seed=1729):
        rng=torch.Generator(device=self.theta.device);rng.manual_seed(seed)
        a=torch.randn(self.theta.shape,device=self.theta.device,dtype=self.theta.dtype,generator=rng)
        b=torch.randn(self.theta.shape,device=self.theta.device,dtype=self.theta.dtype,generator=rng)
        ga,gb=self.raw_ggn(a),self.raw_ggn(b)
        scale=max(float(a.norm()*gb.norm()+b.norm()*ga.norm()),1e-30)
        return {**self.identity,'adjoint_symmetry_relative':abs(float(a@gb-b@ga))/scale,
                'probe_psd_quadratic':float(a@ga),'n_parameters':len(self.theta),
                'logical_groups':{s:self.layout.group_sizes(s) for s in ('coarse','fine')},
                'psd_statement':'GGN PSD by validated loss construction; random probes alone are not a certificate'}
