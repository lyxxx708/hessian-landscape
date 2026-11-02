"""Executable research baselines, explicitly reference reimplementations.

Window smoothing: Meng/Sugolov/Papyan 2026, arXiv:2606.30813 Eq.(2).
K-FAC here is a transparent sampled-model-Fisher, layer-factored reference with
EMA and factored damping; it is NOT the precise block-GGN scientific oracle.
Unsupported non-affine parameters retain AdamW; coverage is always reported.
"""
from __future__ import annotations
import re
import math
import time
import torch
import torch.nn.functional as F
from genesis_gpu.curvature.params import ParamLayout
from genesis_gpu.curvature.operators import FrozenOperator
from genesis_gpu.curvature.spectrum import power_scale
from genesis_gpu.solvers.cg import cg,block_solve
from genesis_gpu.science.predictor import FEATURES,predict
from genesis_gpu.science.utility import cheap_block_energy


def window_smooth(updates,strength=.1):
    if not 0<=strength<1:raise ValueError('Smoothing strength must lie in [0,1)')
    if len(updates)<2:return [x.clone() for x in updates]
    if any(x.shape!=updates[0].shape for x in updates):raise ValueError('Only homologous equal-shape updates can be smoothed')
    out=[]
    for i,x in enumerate(updates):
        left=updates[max(0,i-1)];right=updates[min(len(updates)-1,i+1)]
        out.append((1-strength)*x+strength/2*(left+right))
    return out


def _homologous_parameters(model):
    """Only repeated affine/block coordinates; not arbitrary equal-size tensors."""
    groups={}
    for name,p in model.named_parameters():
        m=re.match(r'^(blocks|layers)\.(\d+)\.(.+)$',name)
        if m:
            key=(m[1],m[3],tuple(p.shape));groups.setdefault(key,[]).append((int(m[2]),name))
    # Do not smooth across shape-changing gaps in a ResNet stage.
    result=[]
    for seq in groups.values():
        seq.sort();segment=[];last=None
        for index,name in seq:
            if last is not None and index!=last+1:
                if len(segment)>1:result.append(segment)
                segment=[]
            segment.append(name);last=index
        if len(segment)>1:result.append(segment)
    return result


class ResearchOptimizer:
    def __init__(self,model,method,lr,weight_decay,cfg,*,predictor=None,callback=None):
        allowed={'adamw','gradient_smoothing','kfac','layerwise_gn','short_cg','same_cost_cg','selective_krylov'}
        if method not in allowed:raise ValueError('Unknown research baseline')
        self.model=model;self.method=method;self.cfg=cfg;self.predictor=predictor;self.callback=callback
        self.base=torch.optim.AdamW(model.parameters(),lr=lr,weight_decay=weight_decay)
        self.param_groups=self.base.param_groups;self.state=self.base.state
        self.validation_probe=None;self.evaluation_interval=1;self.matched_matvec_budget=None
        self.layout=ParamLayout(model);self.factors={};self.steps=0;self.batch=None;self.last_receipt={}

    def set_batch(self,x,y,loss,step):self.batch=(x.detach(),y.detach(),loss,step)
    def zero_grad(self,set_to_none=True):self.base.zero_grad(set_to_none=set_to_none)
    def state_dict(self):return {'version':1,'method':self.method,'base':self.base.state_dict(),'factors':self.factors,'steps':self.steps}
    def load_state_dict(self,state):
        if state['version']!=1 or state['method']!=self.method:raise ValueError('Optimizer state identity changed')
        self.base.load_state_dict(state['base']);self.param_groups=self.base.param_groups;self.state=self.base.state
        self.factors=state['factors'];self.steps=state['steps']

    def _copy_direction(self,old,direction,lr,wd):
        params=dict(self.model.named_parameters())
        with torch.no_grad():
            for e in self.layout.entries:
                params[e.name].copy_(old[e.name]*(1-lr*wd)+lr*direction[e.start:e.stop].reshape(e.shape))

    def _kfac_directions(self,old):
        x,y,loss,step=self.batch;device=x.device;dtype=next(self.model.parameters()).dtype
        inputs={};outputs={};handles=[]
        modules={name:m for name,m in self.model.named_modules() if isinstance(m,(torch.nn.Linear,torch.nn.Conv2d)) and not isinstance(m,torch.nn.Conv2d) or isinstance(m,torch.nn.Conv2d) and m.groups==1}
        # Avoid duplicated logical tied parameters: eligible weight appears once.
        seen=set();modules={n:m for n,m in modules.items() if not (id(m.weight) in seen or seen.add(id(m.weight)))}
        def hook(name):
            def capture(module,args,out):
                inputs[name]=args[0].detach()
                if out.requires_grad:out.register_hook(lambda grad:outputs.__setitem__(name,grad.detach()))
            return capture
        for name,m in modules.items():handles.append(m.register_forward_hook(hook(name)))
        saved_grads={n:p.grad.detach().clone() if p.grad is not None else None for n,p in self.model.named_parameters()}
        try:
            # A separate model-Fisher draw: targets sampled from model, never empirical labels.
            self.model.zero_grad(set_to_none=True)
            count=min(len(x),self.cfg['curvature_microbatch']);xb=x[:count];yb=y[:count]
            pred=self.model(xb)
            generator=torch.Generator(device=device);generator.manual_seed((step+1)*7919)
            if loss.kind=='ce':
                probabilities=pred.detach().softmax(-1)
                sampled=torch.multinomial(probabilities.reshape(-1,pred.shape[-1]),1,generator=generator).reshape(pred.shape[:-1])
                sampled=sampled.masked_fill(yb==loss.ignore_index,loss.ignore_index)
                denominator=loss.count(pred,sampled);loss.value(pred,sampled).backward()
            else:
                sampled=pred.detach()+torch.randn(pred.shape,device=device,dtype=dtype,generator=generator)
                denominator=loss.count(pred,sampled);loss.value(pred,sampled).backward()
            for name,m in modules.items():
                if name not in inputs or name not in outputs:continue
                a=inputs[name];g=outputs[name]*denominator
                if isinstance(m,torch.nn.Conv2d):
                    patches=F.unfold(a,m.kernel_size,dilation=m.dilation,padding=m.padding,stride=m.stride)
                    spatial=patches.shape[-1];a=patches.transpose(1,2).reshape(-1,patches.shape[1]);g=g.permute(0,2,3,1).reshape(-1,m.out_channels)
                else:
                    spatial=1;a=a.reshape(-1,a.shape[-1]);g=g.reshape(-1,g.shape[-1])
                if m.bias is not None:a=torch.cat([a,torch.ones(len(a),1,device=device,dtype=dtype)],1)
                A=(a.T@a)/len(a);B=(g.T@g)/len(g)*spatial
                previous=self.factors.get(name)
                if previous:
                    A=.95*previous['A'].to(device)+.05*A;B=.95*previous['B'].to(device)+.05*B
                self.factors[name]={'A':A.detach(),'B':B.detach()}
        finally:
            for handle in handles:handle.remove()
            for n,p in self.model.named_parameters():p.grad=saved_grads[n]
        updates={};covered=0
        for name,m in modules.items():
            if name not in self.factors:continue
            prefix=name+'.' if name else '';weight_name=prefix+'weight';bias_name=prefix+'bias'
            gradient=saved_grads.get(weight_name)
            if gradient is None:continue
            gradmatrix=gradient.reshape(gradient.shape[0],-1)
            if m.bias is not None:
                bias=saved_grads.get(bias_name)
                if bias is None:continue
                gradmatrix=torch.cat([gradmatrix,bias[:,None]],1)
            A=self.factors[name]['A'].to(device);B=self.factors[name]['B'].to(device)
            # Factored damping is explicitly an approximation, not exact damped GGN.
            damping=math.sqrt(.01)
            left=torch.linalg.solve(B+damping*torch.eye(len(B),device=device,dtype=dtype),gradmatrix)
            direction=-torch.linalg.solve(A+damping*torch.eye(len(A),device=device,dtype=dtype),left.T).T
            updates[weight_name]=direction[:,:m.weight.numel()//len(direction)].reshape_as(m.weight);covered+=m.weight.numel()
            if m.bias is not None:updates[bias_name]=direction[:,-1];covered+=m.bias.numel()
        return updates,covered

    def step(self):
        if self.batch is None:raise RuntimeError('Set the exact training batch before optimizer step')
        started=time.perf_counter();lr=self.param_groups[0]['lr'];wd=self.param_groups[0]['weight_decay']
        old={n:p.detach().clone() for n,p in self.model.named_parameters()};matvecs=0;triggered=False
        if self.method in ('adamw','gradient_smoothing','kfac'):
            replacements={};coverage=0
            if self.method=='kfac':replacements,coverage=self._kfac_directions(old)
            self.base.step()
            if self.method=='gradient_smoothing':
                parameters=dict(self.model.named_parameters())
                # Separate weight decay from the Adam moment update; only smooth the latter.
                updates={n:(old[n]*(1-lr*wd)-p.detach())/max(lr,1e-30) for n,p in parameters.items()}
                with torch.no_grad():
                    for names in _homologous_parameters(self.model):
                        smoothed=window_smooth([updates[n] for n in names],self.cfg['s3']['window_strength'])
                        for n,u in zip(names,smoothed):parameters[n].copy_(old[n]*(1-lr*wd)-lr*u)
                coverage=sum(parameters[n].numel() for group in _homologous_parameters(self.model) for n in group)
            if self.method=='kfac':
                parameters=dict(self.model.named_parameters())
                with torch.no_grad():
                    for name,d in replacements.items():parameters[name].copy_(old[name]*(1-lr*wd)+lr*d)
        else:
            x,y,loss,step=self.batch
            op=FrozenOperator(self.model,x,y,loss,microbatch=self.cfg['curvature_microbatch'])
            scale=power_scale(op,self.cfg['power_iterations'],seed=step+11,callback=self.callback)
            gamma=self.cfg['s3']['damping_ratio'];lam=gamma*max(scale['value'],self.cfg['damping_floor']);g=op.gradient();Q=lambda v:op.matvec(v,lam)
            solve=self.cfg['solver'];rtol=solve['rtol'];maximum=solve['max_iter']
            if self.method in ('short_cg','same_cost_cg'):
                budget=solve['short_cg_steps'] if self.method=='short_cg' else max(1,int((self.matched_matvec_budget or solve['short_cg_steps'])-2)*20//21)
                direction=cg(Q,-g,rtol=rtol,max_iter=budget,callback=self.callback).direction
            else:
                direction,parts=block_solve(op,-g,lam,rtol=rtol,max_iter=maximum,callback=self.callback)
                if not all(s.converged for s in parts):raise ArithmeticError('Online precise layerwise baseline failed numerical qualification')
                qb=Q(direction);den=float(direction@qb)
                unscaled_gain=float(-g@direction)
                alpha=-float(g@direction)/den if den>0 else 0.;direction=alpha*direction
                if self.method=='selective_krylov':
                    residual=g+Q(direction);dr,rr=block_solve(op,residual,lam,rtol=rtol,max_iter=maximum,callback=self.callback)
                    rho=math.sqrt(max(0.,float(residual@dr))/max(unscaled_gain,1e-30)) if all(s.converged for s in rr) else float('inf')
                    if self.predictor and self.predictor.get('status')=='FROZEN_S1_ONLY':
                        import numpy as np
                        short=cg(Q,-g,rtol=rtol,max_iter=solve['short_cg_steps'],callback=self.callback)
                        gain=float(-g@short.direction-.5*short.direction@Q(short.direction));norm=float(g.norm())
                        energy=cheap_block_energy(op,callback=self.callback)
                        budget=max(4,sum(r.matvecs for r in parts)+sum(r.matvecs for r in rr)+2+short.matvecs+energy['matvecs'])
                        matched=cg(Q,-g,rtol=rtol,max_iter=max(1,int((budget-2)*20/21)),callback=self.callback)
                        matched_gain=float(-g@matched.direction-.5*matched.direction@Q(matched.direction))
                        scales=torch.stack([op.theta[ids].norm() for ids in op.layout.group_indices(device=g.device)])
                        f=np.array([[math.log10(gamma),math.log10(max(norm,1e-30)),float(scales.std(unbiased=False)/scales.mean()),
                                     math.log10(1+scale['value']/lam),gain/max(norm**2,1e-30),rho,matched_gain/max(norm**2,1e-30),energy['offdiag_fraction_proxy']]])
                        if self.predictor['feature_names']!=list(FEATURES):raise RuntimeError('Frozen predictor feature schema mismatch')
                        if not np.isfinite(f).all():raise ArithmeticError('Predictor diagnostics not numerically qualified')
                        model=self.predictor['models']['candidate'];pred=float(predict(model,f[:,model['columns']])[0])
                        triggered=pred>self.cfg['statistics']['delta_median']
                    else:
                        if self.cfg['profile']=='full':raise RuntimeError('No S1-frozen predictor: online adaptation blocked')
                        triggered=rho>.05  # Explicit smoke-only policy exercises implementation, not research.
                    if triggered:direction=cg(Q,-g,x0=direction,rtol=rtol,max_iter=solve['short_cg_steps'],callback=self.callback).direction
            if not torch.isfinite(direction).all():raise ArithmeticError('Nonfinite online direction')
            self._copy_direction(old,direction,lr,wd);matvecs=op.matvec_count;coverage=len(op.theta)
        self.steps+=1
        self.last_receipt={'method':self.method,'step':self.steps,'matvecs':matvecs,'triggered':triggered,
                           'wall_seconds':time.perf_counter()-started,'covered_parameters':coverage if self.method!='adamw' else sum(p.numel() for p in self.model.parameters()),
                           'reference_implementation':True,'kfac_variant':'sampled-model Fisher EMA, factored damping; non-affine AdamW fallback' if self.method=='kfac' else None}

        if self.validation_probe is not None and (self.steps==1 or self.steps%self.evaluation_interval==0):
            xval,yval,lossval=self.validation_probe
            training=self.model.training;self.model.eval()
            with torch.no_grad():self.last_receipt['validation_loss']=float(lossval.value(self.model(xval),yval))
            self.model.train(training)
