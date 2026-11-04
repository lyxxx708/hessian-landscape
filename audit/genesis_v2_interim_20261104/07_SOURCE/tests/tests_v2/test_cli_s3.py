import json
from pathlib import Path
from dataclasses import replace
import pytest
import torch
from genesis_gpu.study.design import default_config,expand_design
from genesis_gpu.runtime.atomic_io import atomic_json


def test_cli_help_and_finite_plan(tmp_path,capsys):
    from genesis_gpu.cli import main
    with pytest.raises(SystemExit) as e:main(['--help'])
    assert e.value.code==0
    cfg=default_config('smoke');cfg['root']=str(tmp_path);cfg['storage_root']=str(tmp_path/'storage')
    import yaml
    conf=tmp_path/'test.yaml';conf.write_text(yaml.safe_dump(cfg))
    assert main(['--config',str(conf),'plan','--stage','s1','--dry-run'])==0
    output=capsys.readouterr().out
    assert 'training_runs' in output and 'measurement_jobs' in output


def test_s3_no_go_is_evidence_bound_not_fake_benchmark(tmp_path):
    from genesis_gpu.training.benchmark import run_benchmark
    cfg=default_config('smoke')
    atomic_json(tmp_path/'protocol-lock.json',{'protocol_sha':'test','runs':[]})
    atomic_json(tmp_path/'audit'/'s2_adjudication.json',{'protocol_sha':'test','execution_complete':True,'s3_gate_pass':False})
    r=run_benchmark(cfg,tmp_path)
    assert r['status']=='S3_NO_GO'
    assert r['optimizer_speedup_claim'] is False
    assert r['negative_control']['executed']


def test_budget_censor_is_not_training_completion(tmp_path):
    from genesis_gpu.training.trainer import train_run
    cfg=default_config('smoke');cfg['storage_root']=str(tmp_path)
    run=expand_design(cfg)[0]
    r=train_run(run,cfg,tmp_path,wall_budget_seconds=0.)
    assert r['status']=='BUDGET_CENSORED'
    assert r['steps']<run.train.budget
    assert r['final_checkpoint']


def test_cpu_g0_failure_cannot_leave_stale_green_receipt(tmp_path,monkeypatch):
    from genesis_gpu.audit.g0 import run_g0
    import genesis_gpu.audit.g0 as g0
    cfg=default_config('smoke');cfg['storage_root']=str(tmp_path)
    atomic_json(tmp_path/'audit'/'g0_receipt.json',{'status':'CPU_SMOKE_G0_VALID'})
    def broken(*a,**k):raise RuntimeError('injected derivative defect')
    monkeypatch.setattr(g0,'dense_reference',broken)
    with pytest.raises(RuntimeError):run_g0(cfg,tmp_path)
    assert json.loads((tmp_path/'audit'/'g0_receipt.json').read_text())['status']=='G0_FAILED'


def test_final_report_cannot_declare_science_without_qa(tmp_path):
    from genesis_gpu.reporting.report import generate_report
    cfg=default_config('smoke')
    atomic_json(tmp_path/'protocol-lock.json',{'protocol_sha':'fixture','profile':'smoke','runs':[]})
    result=generate_report(cfg,tmp_path)
    assert result['state']=='INCOMPLETE_BLOCKED_EVIDENCE'
    assert (tmp_path/'reports'/'SCIENTIFIC_VERDICT.md').exists()


def test_repeat_report_manifest_never_contains_stale_receipt(tmp_path):
    from genesis_gpu.reporting.report import generate_report
    from genesis_gpu.runtime.atomic_io import sha256_file
    cfg=default_config('smoke')
    atomic_json(tmp_path/'protocol-lock.json',{'protocol_sha':'fixture','profile':'smoke','runs':[]})
    generate_report(cfg,tmp_path)
    atomic_json(tmp_path/'audit'/'INDEPENDENT_VERIFIER_RECEIPT.json',{'status':'QA_FAILED','errors':['new injected error']})
    generate_report(cfg,tmp_path)
    for line in (tmp_path/'manifest_sha256.txt').read_text().splitlines():
        expected,path=line.split('  ',1)
        assert sha256_file(tmp_path/path)==expected,path


def test_report_fails_closed_on_stale_qa_ledger(tmp_path):
    from genesis_gpu.reporting.report import generate_report
    from genesis_gpu.runtime.atomic_io import file_receipt
    from genesis_gpu.runtime.queue import JobStore
    cfg=default_config('smoke');atomic_json(tmp_path/'protocol-lock.json',{'protocol_sha':'fixture','profile':'smoke','runs':[]})
    store=JobStore(tmp_path/'run_status.sqlite')
    for stage in ['s1','s2']:
        path=tmp_path/f'{stage}.json';atomic_json(path,{'run_id':stage,'checkpoints':[]})
        store.enqueue(stage,stage,'train',{'run':{'run_id':stage}},[]);store.claim(stage)
        store.finish(stage,'COMPLETE',{'receipt':file_receipt(path,tmp_path)})
        atomic_json(tmp_path/'audit'/f'{stage}_adjudication.json',{'verdict':'ENGINEERING_SMOKE_ONLY','utility':{'conditions':[]},'structure':{'verdict':'NOT_IDENTIFIED'},'mechanism':{'verdict':'NOT_IDENTIFIED'},'prediction':{'status':'NOT_RUN'},'jobs_digest':store.evidence_digest(stage)})
    store.close()
    atomic_json(tmp_path/'audit'/'s3_receipt.json',{'status':'S3_NO_GO'})
    atomic_json(tmp_path/'audit'/'INDEPENDENT_VERIFIER_RECEIPT.json',{'status':'CPU_SMOKE_QA_PASSED','replay_enabled':True,'errors':[],'jobs_digest':{'s1':'STALE','s2':'STALE'}})
    result=generate_report(cfg,tmp_path)
    assert result['state']=='INCOMPLETE_BLOCKED_EVIDENCE'


def test_optimizer_advantage_checks_strongest_baseline_not_only_adam():
    from genesis_gpu.training.benchmark import compare_trials
    cfg=default_config('smoke');cfg['s3']['baselines']=['adamw','same_cost_cg','selective_krylov'];cfg['s3']['seeds']=8
    rows=[]
    for sid in ['vision','text']:
        for seed in range(8):
            for method,t in [('adamw',100.),('same_cost_cg',30.),('selective_krylov',60.)]:
                for mode in ['samples','wall_time']:
                    rows.append({'setting_id':sid,'seed':seed,'method':method,'stage':'s3_eval','status':'COMPLETE',
                      'evaluation_mode':mode,'time_to_target_lower_seconds':t-1,'time_to_target_upper_seconds':t,
                      'final_validation_loss':.1,'actual_steps':10})
    decision=compare_trials(rows,['vision','text'],cfg)
    assert not decision['optimizer_gate_pass']
    assert any(c['baseline']=='same_cost_cg' and not c['pass'] for c in decision['comparisons'])


def test_censoring_cannot_be_silently_dropped_for_speedup():
    from genesis_gpu.training.benchmark import compare_trials
    cfg=default_config('smoke');cfg['s3']['baselines']=['adamw','selective_krylov'];cfg['s3']['seeds']=8
    rows=[]
    for sid in ['vision','text']:
        for seed in range(8):
            for method,t in [('adamw',100.),('selective_krylov',30.)]:
                for mode in ['samples','wall_time']:
                    rows.append({'setting_id':sid,'seed':seed,'method':method,'stage':'s3_eval','status':'COMPLETE',
                      'evaluation_mode':mode,'time_to_target_lower_seconds':t-1,'time_to_target_upper_seconds':None if method=='selective_krylov' and seed==7 else t,
                      'final_validation_loss':.1,'actual_steps':10})
    decision=compare_trials(rows,['vision','text'],cfg)
    assert not decision['optimizer_gate_pass']
    assert all(c['paired_uncensored_seeds']==7 for c in decision['comparisons'])
