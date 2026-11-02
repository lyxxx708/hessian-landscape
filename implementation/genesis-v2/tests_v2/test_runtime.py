import importlib
import os
import time
from pathlib import Path
import pytest
from genesis_gpu.study.design import default_config,expand_design
from genesis_gpu.runtime.atomic_io import atomic_json,read_json


def mod(name):
    try:return importlib.import_module('genesis_gpu.'+name)
    except ModuleNotFoundError as exc:pytest.fail(f'Required runtime missing: {name}: {exc}')


def test_queue_idempotency_dependencies_and_immutable_completion(tmp_path):
    Store=mod('runtime.queue').JobStore
    store=Store(tmp_path/'q.sqlite')
    store.enqueue('a','s1','train',{'x':1},[])
    store.enqueue('a','s1','train',{'x':1},[])
    store.enqueue('b','s1','measure',{'x':2},['a'])
    assert store.claim('s1')['id']=='a'
    assert store.claim('s1') is None
    store.finish('a','COMPLETE',{'ok':True})
    assert store.claim('s1')['id']=='b'
    store.finish('b','NUMERIC_UNRESOLVED',{'reason':'tolerance'})
    assert store.counts('s1')=={'COMPLETE':1,'NUMERIC_UNRESOLVED':1}
    with pytest.raises(RuntimeError):store.finish('a','FAILED',{'wrong':True})
    with pytest.raises(RuntimeError):store.enqueue('a','s1','train',{'x':2},[])


def test_queue_no_stealing_from_live_process(tmp_path):
    Store=mod('runtime.queue').JobStore
    store=Store(tmp_path/'q.sqlite');store.enqueue('a','s1','train',{},[])
    store.claim('s1')
    assert store.recover_interrupted(force_dead_only=True)==0
    store.interrupt_owned()
    assert store.claim('s1')['id']=='a'


def test_single_writer_lock(tmp_path):
    Lock=mod('runtime.resources').StudyLock
    with Lock(tmp_path):
        with pytest.raises(RuntimeError):
            with Lock(tmp_path):pass
    with Lock(tmp_path):pass


def test_freeze_requires_g0_and_rejects_cfg_change(tmp_path):
    lifecycle=mod('study.freeze');g0=mod('audit.g0')
    cfg=default_config('smoke');cfg['root']=str(tmp_path);cfg['storage_root']=str(tmp_path/'storage')
    with pytest.raises(RuntimeError):lifecycle.freeze_protocol(cfg,tmp_path)
    receipt=g0.run_g0(cfg,tmp_path)
    assert receipt['status']=='CPU_SMOKE_G0_VALID'
    frozen=lifecycle.freeze_protocol(cfg,tmp_path)
    assert frozen['profile']=='smoke'
    assert len(frozen['runs'])==8
    lifecycle.verify_lock(cfg,tmp_path)
    changed={**cfg,'damping_ratios':[.2]}
    with pytest.raises(RuntimeError):lifecycle.verify_lock(changed,tmp_path)


def test_production_refuses_cpu_and_earlier_g0(tmp_path):
    lifecycle=mod('study.freeze')
    cfg=default_config('full')
    atomic_json(tmp_path/'audit'/'g0_receipt.json',{'status':'CPU_SMOKE_G0_VALID','config_sha':'fake'})
    with pytest.raises(RuntimeError):lifecycle.freeze_protocol(cfg,tmp_path)


def test_s2_unlock_not_a_flag_bypass(tmp_path):
    lifecycle=mod('study.freeze')
    with pytest.raises(RuntimeError):lifecycle.require_stage_access(tmp_path,'s2')
    with pytest.raises(RuntimeError):lifecycle.require_stage_access(tmp_path,'s3')
