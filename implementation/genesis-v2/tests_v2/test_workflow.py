import json
import numpy as np
import pytest
from genesis_gpu.study.design import default_config, expand_design
from genesis_gpu.runtime.atomic_io import atomic_json, read_json


def test_work_plan_counts_and_c_density():
    from genesis_gpu.runtime.scheduler import plan_jobs
    cfg=default_config('full');runs=expand_design(cfg)
    lock={'protocol_sha':'test-only','runs':[r.to_dict() for r in runs]}
    s1=plan_jobs(cfg,lock,'s1');s2=plan_jobs(cfg,lock,'s2')
    assert sum(j['kind']=='train' for j in s1)==130
    assert sum(j['kind']=='train' for j in s2)==96
    assert sum(j['kind']=='measure' for j in s1)==130*4*3*2
    assert len({j['id'] for j in s1+s2})==len(s1)+len(s2)
    assert all(j['payload']['checkpoint_index'] in (0,3) for j in s1 if j['kind']=='measure' and j['payload']['tier'].startswith('C'))
    assert all(j['dependencies'] for j in s1 if j['kind']=='measure')


def test_one_real_checkpoint_measurement_and_replay(tmp_path):
    from genesis_gpu.training.trainer import train_run
    from genesis_gpu.runtime.measurement import measure_job, rebuild_snapshot
    cfg=default_config('smoke');cfg['root']=str(tmp_path);cfg['storage_root']=str(tmp_path)
    run=expand_design(cfg)[0];receipt=train_run(run,cfg,tmp_path)
    payload={'run':run.to_dict(),'checkpoint_index':1,'gamma':.1,'schema':'coarse','tier':'B'}
    result=measure_job(payload,cfg,tmp_path,'b-test','protocol-test')
    assert result['status'] in ('NUMERIC_VALID','NUMERIC_UNRESOLVED','INELIGIBLE_ZERO_GRADIENT')
    assert result['provenance']['checkpoint_integrity_sha']==receipt['checkpoints'][1]['integrity_sha']
    assert result['provenance']['protocol_sha']=='protocol-test'
    op,val,meta=rebuild_snapshot(payload,cfg,tmp_path)
    assert meta['data_sha']==result['provenance']['data_sha']
    assert result['utility']['validation_alpha_source']=='train_only'
    assert result['tier']=='B' and result['structure'] is None


def test_structural_job_keeps_all_probe_evidence(tmp_path):
    from genesis_gpu.training.trainer import train_run
    from genesis_gpu.runtime.measurement import measure_job
    cfg=default_config('smoke');cfg['root']=str(tmp_path);cfg['storage_root']=str(tmp_path)
    run=expand_design(cfg)[0];train_run(run,cfg,tmp_path)
    payload={'run':run.to_dict(),'checkpoint_index':0,'gamma':.1,'schema':'coarse','tier':'C_DEEP'}
    r=measure_job(payload,cfg,tmp_path,'c-test','proto')
    assert r['structure'] is not None
    assert r['mechanism']['exact_reference']['rank_G']<=4
    assert r['structure']['raw_profile']['layers']==3
    assert r['structure']['probe_artifact']['sha256']
    assert r['mechanism']['gauge_controls']


def test_statistics_aggregate_seeds_not_checkpoint_rows():
    from genesis_gpu.study.statistics import summarize_utility
    cfg=default_config('full')
    rows=[]
    for seed in range(16):
        for gamma in cfg['damping_ratios']:
            for ckpt in (1,2,3):
                rows.append({'stage':'s2','setting_id':'mlp_d6_relu','family':'mlp','seed':seed,'checkpoint_index':ckpt,
                             'gamma':gamma,'schema':'coarse','status':'NUMERIC_VALID','delta':.10+seed*.001})
    out=summarize_utility(rows,cfg,planned_counts={'mlp_d6_relu':16})
    assert out['conditions'][0]['independent_seed_n']==16
    assert out['conditions'][0]['pass']
    assert len(out['conditions'][0]['by_gamma'])==3
    assert not out['utility_gate_pass']  # Need two conditions, not one duplicated by gamma.


def test_invalid_and_missing_cannot_become_negative_confirmation():
    from genesis_gpu.study.statistics import summarize_utility
    cfg=default_config('full')
    rows=[{'stage':'s2','setting_id':'transformer_d8','family':'transformer','seed':1,'checkpoint_index':3,
           'gamma':.01,'schema':'coarse','status':'NUMERIC_UNRESOLVED','delta':None}]
    out=summarize_utility(rows,cfg,planned_counts={'transformer_d8':16})
    assert not out['utility_gate_pass']
    assert out['conditions'][0]['status']=='INSUFFICIENT_VALID_SEEDS'


def test_s2_adjudication_cannot_be_written_before_execution(tmp_path):
    from genesis_gpu.study.adjudication import adjudicate
    cfg=default_config('smoke')
    atomic_json(tmp_path/'protocol-lock.json',{'protocol_sha':'p','profile':'smoke','runs':[]})
    with pytest.raises(RuntimeError,match='not complete'):
        adjudicate(cfg,tmp_path,'s2')
