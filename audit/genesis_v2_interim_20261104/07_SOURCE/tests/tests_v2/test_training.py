import importlib
from dataclasses import replace
from pathlib import Path
import pytest
import torch
from genesis_gpu.study.design import default_config,expand_design
from genesis_gpu.runtime.atomic_io import read_json,sha256_file


def mod(name):
    try:return importlib.import_module('genesis_gpu.'+name)
    except ModuleNotFoundError as exc:pytest.fail(f'Required module missing: {name}: {exc}')


def small_run(family='dln'):
    cfg=default_config('smoke')
    return cfg,next(r for r in expand_design(cfg) if r.stage=='s1' and r.model.family==family)


def test_synthetic_fixed_teacher_and_deterministic_batch(tmp_path):
    cfg,r=small_run()
    data=mod('datasets.registry').load_bundle(r,cfg,tmp_path)
    x,y=data.batch('train',step=2,count=4,seed=r.seed)
    x2,y2=data.batch('train',step=2,count=4,seed=r.seed)
    assert torch.equal(x,x2) and torch.equal(y,y2)
    assert not torch.equal(data.batch('validation',step=2,count=4,seed=r.seed)[0],x)
    assert data.fingerprint
    assert data.source['evidence_class']=='SMOKE_SYNTHETIC_NOT_RESEARCH'


def test_safe_checkpoint_roundtrip_and_tamper(tmp_path):
    checkpoints=mod('training.checkpoint')
    state={'weights':{'a':torch.arange(6).reshape(2,3)},'optimizer':{0:{'exp_avg':torch.ones(2)}},'step':3,
           'rng':torch.get_rng_state(),'tuple':(1,'ok',None)}
    path=tmp_path/'check'
    checkpoints.save_state(path,state,{'run_id':'demo','step':3})
    restored,meta=checkpoints.load_state(path)
    assert restored['step']==3 and restored['tuple']==(1,'ok',None)
    assert torch.equal(restored['weights']['a'],state['weights']['a'])
    assert torch.equal(restored['optimizer'][0]['exp_avg'],torch.ones(2))
    assert meta['run_id']=='demo'
    p=path/'tensors.safetensors';p.write_bytes(p.read_bytes()[:-2]+b'!!')
    with pytest.raises(checkpoints.IntegrityError):checkpoints.load_state(path)


def test_resume_is_identical_to_uninterrupted(tmp_path):
    trainer=mod('training.trainer');checkpoint=mod('training.checkpoint')
    cfg,run=small_run('mlp')
    a=tmp_path/'a';b=tmp_path/'b'
    full=trainer.train_run(run,cfg,a)
    partial=trainer.train_run(run,cfg,b,stop_after_step=1)
    assert partial['status']=='INTERRUPTED'
    resumed=trainer.train_run(run,cfg,b)
    assert full['status']==resumed['status']=='COMPLETE'
    state_a,_=checkpoint.load_state(a/full['checkpoints'][-1]['path'])
    state_b,_=checkpoint.load_state(b/resumed['checkpoints'][-1]['path'])
    for name,v in state_a['model'].items():
        assert torch.equal(v,state_b['model'][name]),name
    assert [c['step'] for c in full['checkpoints']]==[0,1,2,3]
    again=trainer.train_run(run,cfg,b)
    assert again['checkpoints']==resumed['checkpoints']


@pytest.mark.parametrize('family',['dln','resnet','transformer'])
def test_each_model_trains_and_reloads_checkpoint(tmp_path,family):
    trainer=mod('training.trainer');checkpoint=mod('training.checkpoint')
    cfg,run=small_run(family)
    receipt=trainer.train_run(run,cfg,tmp_path)
    assert receipt['status']=='COMPLETE'
    assert receipt['steps']==3
    assert len(receipt['checkpoints'])==4
    state,meta=checkpoint.load_state(tmp_path/receipt['checkpoints'][-1]['path'])
    assert meta['run_id']==run.run_id and state['step']==3
    assert receipt['training_units']>0
    assert receipt['total_wall_seconds']>=0


def test_public_data_not_silently_replaced_with_synthetic(tmp_path):
    data=mod('datasets.registry')
    cfg=default_config('full')
    # Isolate this missing-data guard from any owner-imported full datasets on E:.
    cfg['storage_root']=str(tmp_path/'isolated-storage')
    run=next(r for r in expand_design(cfg) if r.dataset=='mnist')
    with pytest.raises(data.DatasetUnavailable):data.load_bundle(run,cfg,tmp_path)


def test_masked_text_budget_exact(tmp_path):
    data=mod('datasets.registry');cfg,r=small_run('transformer')
    bundle=data.load_bundle(r,cfg,tmp_path)
    x,y=bundle.batch('train',step=1,count=4,seed=r.seed,max_tokens=7)
    assert x.shape==(4,4)
    assert int((y!=-100).sum())==7
