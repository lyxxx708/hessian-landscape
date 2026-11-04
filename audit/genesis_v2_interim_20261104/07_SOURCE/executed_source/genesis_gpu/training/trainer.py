"""True fixed-target training, exact effective-batch reduction, transactional resume."""
from __future__ import annotations
from dataclasses import asdict
from pathlib import Path
import math
import time
import torch
from genesis_gpu.contracts import LossSpec,object_sha
from genesis_gpu.models.registry import build_model
from genesis_gpu.datasets.registry import load_bundle
from genesis_gpu.study.design import checkpoint_steps
from genesis_gpu.curvature.params import tensor_dict_sha
from genesis_gpu.runtime.atomic_io import atomic_json,read_json,sha256_file,safe_relative,append_jsonl
from .checkpoint import save_state,load_state,save_resume,load_resume,IntegrityError


class StopRequested(RuntimeError):
    pass


def training_budget(run,bundle):
    t=run.train
    if t.budget_kind=='steps':return t.budget,t.budget*t.effective_batch,'examples'
    if t.budget_kind=='epochs':
        units=t.budget*bundle.size('train')
        return math.ceil(units/t.effective_batch),units,'examples'
    units=t.budget
    return math.ceil(units/(t.effective_batch*run.model.context)),units,'tokens'


def ordinary_optimizer(model,train):
    if train.optimizer=='adam':return torch.optim.Adam(model.parameters(),lr=train.learning_rate,weight_decay=train.weight_decay)
    if train.optimizer=='adamw':return torch.optim.AdamW(model.parameters(),lr=train.learning_rate,weight_decay=train.weight_decay)
    if train.optimizer=='sgd':return torch.optim.SGD(model.parameters(),lr=train.learning_rate,weight_decay=train.weight_decay,momentum=train.momentum)
    raise ValueError(f'Unknown base optimizer {train.optimizer}')


def _optimizer_to(optimizer,device):
    for state in optimizer.state.values():
        for key,value in state.items():
            if torch.is_tensor(value):state[key]=value.to(device)


def train_run(run,cfg,root,*,stop_after_step=None,callback=None,optimizer_factory=None,wall_budget_seconds=None):
    root=Path(root);base=root/'checkpoints'/run.run_id;base.mkdir(parents=True,exist_ok=True)
    receipt_path=base/'training_receipt.json'
    bundle=load_bundle(run,cfg,root)
    expected={'run_spec_sha':object_sha(run),'data_sha':bundle.fingerprint,'profile':cfg['profile'],'wall_budget_seconds':wall_budget_seconds}
    if receipt_path.exists():
        receipt=read_json(receipt_path)
        if any(receipt[k]!=v for k,v in expected.items()):raise IntegrityError('Completed training provenance mismatch')
        for ckpt in receipt['checkpoints']+[receipt['final_checkpoint']]:load_state(root/ckpt['path'],ckpt['integrity_sha'])
        return receipt
    device=torch.device(cfg['device'])
    if cfg['profile']=='full' and (device.type!='cuda' or not torch.cuda.is_available()):
        raise RuntimeError('CUDA_REQUIRED: no silent CPU fallback')
    dtype=torch.float64 if cfg['profile']=='smoke' else torch.float32
    torch.manual_seed(run.seed)
    if device.type=='cuda':torch.cuda.manual_seed_all(run.seed)
    model=build_model(run.model,run.seed).to(device=device,dtype=dtype)
    optimizer=ordinary_optimizer(model,run.train) if optimizer_factory is None else optimizer_factory(model)
    loss=LossSpec('mse' if run.model.family=='dln' else 'ce')
    steps,total_units,unit_kind=training_budget(run,bundle)
    pins=checkpoint_steps(steps,run.train.checkpoint_fractions)
    previous=load_resume(base/'resume')
    pinned=[];step=0;units=0;accumulated=0.;micro=run.train.microbatch
    if previous:
        state,meta=previous
        if any(meta.get(k)!=v for k,v in expected.items()):raise IntegrityError('Resume provenance mismatch')
        model.load_state_dict(state['model'],strict=True);optimizer.load_state_dict(state['optimizer']);_optimizer_to(optimizer,device)
        torch.set_rng_state(state['rng'])
        if device.type=='cuda' and state['cuda_rng']:torch.cuda.set_rng_state_all(state['cuda_rng'])
        step=state['step'];units=state['units'];pinned=state['pinned'];accumulated=state['elapsed'];micro=state['microbatch']
    started=time.perf_counter();log=root/'logs'/f'{run.run_id}.jsonl';log.parent.mkdir(parents=True,exist_ok=True)
    def sync():
        if device.type=='cuda':torch.cuda.synchronize(device)
    def state_now():
        sync()
        return {'model':model.state_dict(),'optimizer':optimizer.state_dict(),'rng':torch.get_rng_state(),
                'cuda_rng':torch.cuda.get_rng_state_all() if device.type=='cuda' else [],'step':step,'units':units,
                'pinned':list(pinned),'elapsed':accumulated+time.perf_counter()-started,'microbatch':micro}
    def meta_now():
        return {**expected,'run_id':run.run_id,'step':step,'units':units,'model_spec':asdict(run.model),
                'loss_spec':asdict(loss),'model_sha':tensor_dict_sha(model.state_dict()),'training_mode':True,
                'weight_decay':run.train.weight_decay,'diagnostic_objective':'deterministic data loss, not decoupled weight decay',
                'actual_microbatch':micro,'device':str(device),'dtype':str(dtype),'torch_version':str(torch.__version__)}
    def pin():
        path=base/f'step_{step:09d}'
        if path.exists():
            _,meta=load_state(path)
            if meta['model_sha']!=tensor_dict_sha(model.state_dict()):raise IntegrityError('Checkpoint replay differs; do not overwrite')
            integrity=sha256_file(path/'integrity.json')
        else:integrity=save_state(path,state_now(),meta_now())['integrity_sha']
        if not any(p['step']==step for p in pinned):
            pinned.append({'step':step,'index':pins.index(step),'path':safe_relative(root,path),'integrity_sha':integrity,
                           'model_sha':tensor_dict_sha(model.state_dict())})
    if step==0 and not pinned:
        pin();save_resume(base/'resume',state_now(),meta_now())
    model.train();budget_censored=False
    try:
        while step<steps:
            if wall_budget_seconds is not None and accumulated+time.perf_counter()-started>=wall_budget_seconds:
                budget_censored=True;break
            if callback:callback()
            remaining=total_units-units
            count=run.train.effective_batch
            tokens=None
            if unit_kind=='tokens':
                tokens=min(remaining,count*run.model.context);count=math.ceil(tokens/run.model.context)
            elif run.train.budget_kind=='epochs':count=min(count,remaining)
            x,y=bundle.batch('train',step=step,count=count,seed=run.seed,device=device,dtype=dtype,max_tokens=tokens,
                            augment=run.train.augmentation,offset=units if run.train.budget_kind=='epochs' else None)
            denom=y.numel() if loss.kind=='mse' else int((y!=loss.ignore_index).sum())
            lr=run.train.learning_rate
            if run.train.schedule=='cosine':lr*=.5*(1+math.cos(math.pi*step/steps))
            for group in optimizer.param_groups:group['lr']=lr
            if hasattr(optimizer,'set_batch'):optimizer.set_batch(x,y,loss,step)
            while True:
                optimizer.zero_grad(set_to_none=True);loss_value=0.
                try:
                    for start in range(0,count,micro):
                        if callback:callback()
                        xm,ym=x[start:start+micro],y[start:start+micro]
                        if loss.kind=='ce' and not (ym!=loss.ignore_index).any():continue
                        pred=model(xm);part=loss.value(pred,ym,denominator=denom)
                        if not torch.isfinite(part):raise ArithmeticError('Nonfinite training loss')
                        part.backward();loss_value+=float(part.detach())
                    break
                except torch.cuda.OutOfMemoryError:
                    optimizer.zero_grad(set_to_none=True)
                    candidates=[v for v in cfg['resources']['microbatch_fallback'] if v<micro]
                    if not candidates:raise
                    micro=max(candidates);torch.cuda.empty_cache()
                    append_jsonl(log,{'event':'OOM_MICROBATCH_RETRY','step':step,'new_microbatch':micro,'effective_batch_unchanged':count})
            if not all(p.grad is None or torch.isfinite(p.grad).all() for p in model.parameters()):
                raise ArithmeticError('Nonfinite gradient; do not save as valid checkpoint')
            optimizer.step();step+=1;units+=tokens if unit_kind=='tokens' else count
            sync()
            append_jsonl(log,{'event':'TRAIN_STEP','run_id':run.run_id,'step':step,'units':units,'loss':loss_value,'lr':lr,
                             'microbatch':micro,'elapsed':accumulated+time.perf_counter()-started,
                             'optimizer_receipt':getattr(optimizer,'last_receipt',None)})
            if step in pins:pin()
            if step%run.train.save_every_steps==0 or step in pins or step==steps:
                save_resume(base/'resume',state_now(),meta_now())
            if stop_after_step is not None and step>=stop_after_step:
                save_resume(base/'resume',state_now(),meta_now())
                return {**expected,'status':'INTERRUPTED','step':step,'checkpoints':pinned}
    except StopRequested:
        # Optimizer updates commit only at step boundaries. Reload the last transaction on resume.
        return {**expected,'status':'INTERRUPTED','step':step,'checkpoints':pinned}
    sync()
    final_path=base/f'final_step_{step:09d}'
    if not final_path.exists():save_state(final_path,state_now(),meta_now())
    final_checkpoint={'path':safe_relative(root,final_path),'integrity_sha':sha256_file(final_path/'integrity.json')}
    receipt={**expected,'status':'BUDGET_CENSORED' if budget_censored else 'COMPLETE','run_id':run.run_id,'steps':step,'training_units':units,'unit_kind':unit_kind,
             'checkpoints':pinned,'final_checkpoint':final_checkpoint,'planned_steps':steps,'total_wall_seconds':accumulated+time.perf_counter()-started,
             'peak_vram_allocated':torch.cuda.max_memory_allocated(device) if device.type=='cuda' else None,
             'dtype':str(dtype),'device':str(device),'source':bundle.source,
             'evidence_class':'ENGINEERING_SMOKE_ONLY' if cfg['profile']=='smoke' else 'FRESH_TRAINING_TRAJECTORY_NOT_SCIENCE_VERDICT'}
    atomic_json(receipt_path,receipt)
    return receipt
