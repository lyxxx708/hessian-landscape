import importlib
from pathlib import Path, PureWindowsPath
import os
import json
import pytest
import torch


def mod(name):
    try:
        return importlib.import_module('genesis_gpu.' + name)
    except ModuleNotFoundError as exc:
        pytest.fail(f'Required v2 module not implemented: {name}: {exc}')


def test_mse_and_ce_loss_contract():
    LossSpec = mod('contracts').LossSpec
    x = torch.tensor([[1., 2.], [3., 4.]], dtype=torch.float64)
    y = torch.zeros_like(x)
    assert LossSpec('mse').value(x, y).item() == pytest.approx(3.75)
    logits = torch.randn(2, 3, 4, dtype=torch.float64)
    target = torch.tensor([[1, -100, 2], [0, 1, -100]])
    spec = LossSpec('ce')
    want = torch.nn.functional.cross_entropy(logits.reshape(-1, 4), target.reshape(-1), ignore_index=-100)
    assert torch.allclose(spec.value(logits, target), want)
    shift = torch.ones_like(logits)
    assert spec.output_metric(logits, target, shift).abs().max() < 1e-14
    with pytest.raises(ValueError):
        spec.value(logits, torch.full_like(target, -100))


def test_loss_metric_matches_dense_output_hessian():
    spec = mod('contracts').LossSpec('ce')
    torch.manual_seed(42)
    z = torch.randn(2, 3, dtype=torch.float64)
    y = torch.tensor([1, -100])
    v = torch.randn_like(z)
    H = torch.autograd.functional.hessian(lambda a: spec.value(a.reshape_as(z), y), z.flatten())
    assert torch.allclose(spec.output_metric(z, y, v).flatten(), H @ v.flatten(), atol=1e-12)


def test_plan_counts_and_seed_isolation():
    d = mod('study.design')
    cfg = d.default_config('full')
    runs = d.expand_design(cfg)
    assert sum(r.stage == 's1' for r in runs) == 130
    assert sum(r.stage == 's2' for r in runs) == 96
    assert len({r.run_id for r in runs}) == 226
    s1 = {r.seed for r in runs if r.stage == 's1'}
    s2 = {r.seed for r in runs if r.stage == 's2'}
    assert not s1 & s2
    anchors = [r for r in runs if r.stage == 's2' and r.model.family == 'transformer']
    assert {r.model.depth for r in anchors} == {4, 8}
    assert len(anchors) == 32
    assert d.measurement_tier('s1', 0, .01, False) == 'C_BASE'
    assert d.measurement_tier('s1', 1, .1, False) == 'B'
    assert d.measurement_tier('s2', 3, .1, False) == 'C_BASE'


def test_atomic_artifact_hash_tamper(tmp_path):
    io = mod('runtime.atomic_io')
    p = tmp_path / 'a.json'
    io.atomic_json(p, {'v': 1})
    receipt = io.file_receipt(p, tmp_path)
    assert io.verify_receipt(tmp_path, receipt)
    p.write_text('{"v":2}')
    assert not io.verify_receipt(tmp_path, receipt)
    with pytest.raises(ValueError):
        io.safe_relative(tmp_path, tmp_path.parent / 'escape')


def test_storage_guard_rejects_C_and_posix_full(tmp_path):
    guard = mod('env.storage_guard')
    with pytest.raises(guard.StorageBlocked):
        guard.check_windows_bulk_path(r'C:\GENESIS')
    assert guard.check_windows_bulk_path(r'E:\GENESIS') == PureWindowsPath(r'E:\GENESIS')
    if os.name != 'nt':
        with pytest.raises(guard.StorageBlocked):
            guard.prepare_storage(tmp_path, production=True)
    else:
        paths = guard.prepare_storage(tmp_path, production=True, min_free_bytes=0)
        assert paths['run'].exists()
    paths = guard.prepare_storage(tmp_path, production=False, min_free_bytes=0)
    assert paths['run'].exists()


def test_json_rejects_nan_and_path_escape(tmp_path):
    io = mod('runtime.atomic_io')
    with pytest.raises(ValueError):
        io.atomic_json(tmp_path/'bad.json', {'x': float('nan')})
    with pytest.raises(ValueError):
        io.resolve_artifact(tmp_path, '../private')
