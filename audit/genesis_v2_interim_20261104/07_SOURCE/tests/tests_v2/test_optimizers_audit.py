import numpy as np
import pytest
import torch
from genesis_gpu.study.design import default_config,expand_design
from genesis_gpu.models.registry import build_model
from genesis_gpu.contracts import LossSpec
from genesis_gpu.datasets.registry import load_bundle


def test_window_smoothing_preserves_sum_and_constant_updates():
    from genesis_gpu.training.optimizers import window_smooth
    x=[torch.tensor([float(i)]) for i in range(4)]
    y=window_smooth(x,.2)
    assert torch.allclose(torch.stack(x).sum(),torch.stack(y).sum())
    assert y[0].item()==pytest.approx(.1)
    assert y[1].item()==pytest.approx(1.)
    with pytest.raises(ValueError):window_smooth(x,1.)
    z=window_smooth([torch.ones(2)]*3,.4)
    assert all(torch.equal(v,torch.ones(2)) for v in z)


@pytest.mark.parametrize('name',['adamw','gradient_smoothing','kfac','layerwise_gn','short_cg','selective_krylov'])
def test_online_baselines_take_real_step_and_roundtrip_state(tmp_path,name):
    from genesis_gpu.training.optimizers import ResearchOptimizer
    cfg=default_config('smoke');cfg['storage_root']=str(tmp_path)
    run=expand_design(cfg)[1];bundle=load_bundle(run,cfg,tmp_path)
    model=build_model(run.model,run.seed).double();loss=LossSpec('ce')
    x,y=bundle.batch('train',step=0,count=4,seed=run.seed,dtype=torch.float64)
    opt=ResearchOptimizer(model,name,.003,.001,cfg)
    before=[p.detach().clone() for p in model.parameters()]
    opt.set_batch(x,y,loss,0);opt.zero_grad();loss.value(model(x),y).backward();opt.step()
    assert any(not torch.equal(a,b) for a,b in zip(before,model.parameters()))
    assert all(torch.isfinite(p).all() for p in model.parameters())
    assert opt.last_receipt['method']==name
    saved=opt.state_dict();other=ResearchOptimizer(model,name,.003,.001,cfg);other.load_state_dict(saved)
    assert other.state_dict()['version']==1


def test_independent_artifact_audit_detects_tampering(tmp_path):
    from genesis_gpu.audit.verify import verify_study
    from genesis_gpu.runtime.atomic_io import atomic_json,file_receipt
    from genesis_gpu.runtime.queue import JobStore
    cfg=default_config('smoke');cfg['root']=str(tmp_path)
    artifact=tmp_path/'sample.json';atomic_json(artifact,{'a':1});receipt=file_receipt(artifact,tmp_path)
    atomic_json(tmp_path/'protocol-lock.json',{'protocol_sha':'fixture','runs':[],'profile':'smoke'})
    store=JobStore(tmp_path/'run_status.sqlite');store.enqueue('x','s1','train',{},[]);store.claim('s1')
    store.finish('x','COMPLETE',{'receipt':receipt});store.close()
    artifact.write_text('{"a":2}')
    result=verify_study(cfg,tmp_path,replay=False)
    assert result['status']=='QA_FAILED'
    assert result['errors']
