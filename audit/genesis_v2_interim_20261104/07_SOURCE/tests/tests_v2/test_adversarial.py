import json
from pathlib import Path
import os
import pytest
import torch
import numpy as np
from genesis_gpu.study.design import default_config,load_config
from genesis_gpu.runtime.atomic_io import atomic_json,read_json


def test_production_rejects_unqualified_probe_policy(tmp_path):
    import yaml
    cfg=default_config('full');cfg['probes']['independent_final']=False
    path=tmp_path/'bad.yaml';path.write_text(yaml.safe_dump(cfg))
    with pytest.raises(ValueError):load_config(path)


def test_invalid_solver_settings_rejected_before_gpu(tmp_path):
    import yaml
    for group,key,value in [('solver','rtol',float('nan')),('probes','schedule',[16,8]),('resources','disk_reserve_gib',-1)]:
        cfg=default_config('smoke');cfg[group][key]=value
        path=tmp_path/'bad.yaml';path.write_text(yaml.safe_dump(cfg))
        with pytest.raises(ValueError):load_config(path)


def test_seed_coverage_failure_never_becomes_structural_pass():
    from genesis_gpu.study.statistics import summarize_structure
    cfg=default_config('full');records=[]
    for gamma in cfg['damping_ratios']:
        records.append({'provenance':{'setting_id':'transformer_d8','checkpoint_index':3,'seed':42},'schema':'coarse','gamma':gamma,
                        'structure':{'status':'NUMERIC_VALID','raw_profile':{'tail_status':'ELIGIBLE','tail_amplitude':.5,'tail_cv':.0},
                                     'order_null':{'p_flatness':.001}}})
    r=summarize_structure(records,cfg,planned_counts={'transformer_d8':16})
    assert not r['structure_gate_pass']
    assert r['conditions'][0]['coverage_qualified'] is False


def test_scheduler_detects_live_global_device_ownership(tmp_path):
    from genesis_gpu.runtime.resources import DeviceLock
    with DeviceLock(tmp_path,device='test-device',enabled=True):
        with pytest.raises(RuntimeError):
            with DeviceLock(tmp_path,device='test-device',enabled=True):pass


def test_ggn_flat_tail_norm_algebraic_identity():
    from genesis_gpu.science.structure import profile
    L=12;c=.09;E=np.full((L,L),c*c);np.fill_diagonal(E,1.)
    p=profile(E,[1]*L)
    assert p['offdiag_mass']==pytest.approx(11*c*c/(1+11*c*c))
    assert p['tail_cv']<1e-12


def test_bootstrap_does_not_resample_checkpoints_as_seeds():
    from genesis_gpu.study.statistics import bootstrap_median
    a=bootstrap_median([.01,.02,.03],100,seed=1)
    assert a['n']==3 and a['median']==.02
    assert len(a['interval'])==2


def test_kfac_conv_gradient_capture_works_and_factors_are_finite(tmp_path):
    from genesis_gpu.training.optimizers import ResearchOptimizer
    from genesis_gpu.study.design import expand_design
    from genesis_gpu.datasets.registry import load_bundle
    from genesis_gpu.models.registry import build_model
    from genesis_gpu.contracts import LossSpec
    cfg=default_config('smoke');cfg['storage_root']=str(tmp_path)
    run=expand_design(cfg)[2];b=load_bundle(run,cfg,tmp_path)
    m=build_model(run.model,run.seed).double();x,y=b.batch('train',step=0,count=2,seed=run.seed,dtype=torch.float64)
    o=ResearchOptimizer(m,'kfac',.001,.001,cfg);l=LossSpec('ce');o.set_batch(x,y,l,0)
    l.value(m(x),y).backward();o.step()
    assert o.factors and all(torch.isfinite(f['A']).all() and torch.isfinite(f['B']).all() for f in o.factors.values())


@pytest.mark.cuda
@pytest.mark.skipif(not torch.cuda.is_available(),reason='Actual CUDA device required; not replaced by CPU')
def test_real_cuda_ggn_against_independent_reference():
    from genesis_gpu.models.registry import build_model
    from genesis_gpu.contracts import ModelSpec,LossSpec
    from genesis_gpu.curvature.operators import FrozenOperator
    from genesis_gpu.audit.independent_reference import dense_reference
    model=build_model(ModelSpec('mlp',3,4,3,2,activation='tanh'),5).cuda().double()
    x=torch.randn(2,3,device='cuda',dtype=torch.float64);y=torch.tensor([0,1],device='cuda')
    op=FrozenOperator(model,x,y,LossSpec('ce'));ref=dense_reference(op)
    v=torch.ones_like(op.theta)
    torch.testing.assert_close(op.raw_ggn(v),ref['G']@v,atol=1e-9,rtol=1e-8)


def test_runtime_versions_bound_to_freeze(tmp_path,monkeypatch):
    from genesis_gpu.audit.g0 import run_g0
    from genesis_gpu.study.freeze import freeze_protocol,verify_lock
    cfg=default_config('smoke');cfg['root']=str(tmp_path);cfg['storage_root']=str(tmp_path)
    run_g0(cfg,tmp_path);freeze_protocol(cfg,tmp_path)
    import genesis_gpu.env.reproducibility as rep
    original=rep.runtime_abi
    def changed():return {**original(),'torch':'injected-other-version'}
    monkeypatch.setattr(rep,'runtime_abi',changed)
    with pytest.raises(RuntimeError,match='runtime'):verify_lock(cfg,tmp_path)


def test_budget_matched_cg_is_separate_from_fixed_short_baseline(tmp_path):
    from genesis_gpu.study.design import expand_design
    from genesis_gpu.models.registry import build_model
    from genesis_gpu.datasets.registry import load_bundle
    from genesis_gpu.curvature.operators import FrozenOperator
    from genesis_gpu.contracts import LossSpec
    from genesis_gpu.science.utility import evaluate_utility
    cfg=default_config('smoke');run=expand_design(cfg)[0]
    data=load_bundle(run,cfg,tmp_path);x,y=data.batch('train',step=0,count=2,seed=run.seed,dtype=torch.float64)
    op=FrozenOperator(build_model(run.model,run.seed).double(),x,y,LossSpec('mse'))
    result,_=evaluate_utility(op,.1,rtol=1e-9,max_iter=200)
    assert result['matched_cg']['matvec_budget']>=result['matched_cg']['solve']['matvecs']
    assert 'matched_cg_quadratic_gain' in result


def test_g0_includes_independent_random_estimator_calibration(tmp_path):
    from genesis_gpu.audit.g0 import run_g0
    cfg=default_config('smoke');cfg['root']=str(tmp_path);cfg['storage_root']=str(tmp_path)
    r=run_g0(cfg,tmp_path)
    c=next((c for c in r['checks'] if c.get('case')=='block_estimator_ensemble'),None)
    assert c is not None and c['passed']
    assert c['replicates']>=8 and c['exact_reference']


def test_gauge_control_reports_curvature_change_not_just_function():
    from genesis_gpu.science.mechanism import dln_gauge_controls
    from genesis_gpu.models.registry import build_model
    from genesis_gpu.contracts import ModelSpec,LossSpec
    from genesis_gpu.curvature.operators import FrozenOperator
    torch.manual_seed(871)
    m=build_model(ModelSpec('dln',3,2,2,2),7).double()
    op=FrozenOperator(m,torch.randn(3,2,dtype=torch.float64),torch.randn(3,2,dtype=torch.float64),LossSpec('mse'))
    rows=dln_gauge_controls(op,scales=(2.,))
    assert rows[0]['relative_output_drift']<1e-12
    assert rows[0]['curvature_control']['GGNv_relative_change']>1e-3
    assert rows[0]['curvature_control']['same_damping'] is True
