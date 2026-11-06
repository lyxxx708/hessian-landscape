"""Read-only access to frozen v2 S1 DLN states, exactly as NEXT v2 constructed them."""
from __future__ import annotations
import copy
from pathlib import Path
import torch
from .env import V2_RUN, NEXT_V2_RUN, read_json, sha256_file, configure_torch


def next_v2_states():
    """The 38 NEXT v2 NUMERIC_VALID DLN states, with their payloads from the NEXT v2 follow-up plan."""
    lock = read_json(NEXT_V2_RUN / 'FOLLOWUP_LOCK.json')
    plan = {s['state_id']: s for s in lock['plan']['states']}
    out = []
    for p in sorted((NEXT_V2_RUN / 'results').glob('*.json')):
        r = read_json(p)
        s = plan[r['state_id']]
        out.append({'state_id': r['state_id'], 'run': s['run'], 'checkpoint_index': s['checkpoint_index'],
                    'setting_id': r['setting_id'], 'seed': int(r['seed']), 'seed_index': r['seed_index'],
                    'checkpoint': r['checkpoint'], 'next_v2_result': str(p), 'next_v2_result_sha256': sha256_file(p)})
    return out, list(plan.values())


def parent_panel():
    lock = read_json(NEXT_V2_RUN / 'FOLLOWUP_LOCK.json')
    rows = []
    for s in lock['plan']['states']:
        rp = V2_RUN / 'checkpoints' / s['run']['run_id'] / 'training_receipt.json'
        status = read_json(rp).get('status') if rp.is_file() else 'NO_RECEIPT'
        rows.append({'state_id': s['state_id'], 'setting_id': s['run']['setting_id'], 'seed_index': s['run']['seed_index'],
                     'checkpoint': s['checkpoint_index'], 'family': s['run']['model']['family'], 'training_status': status})
    return rows


def load_state(state):
    """Return (op FP64 lifted from v2 FP32 batch, val op, provenance, bundle, v2 config, T32 train indices)."""
    configure_torch()
    from genesis_gpu.runtime.measurement import rebuild_snapshot
    from genesis_gpu.curvature.operators import FrozenOperator
    from genesis_gpu.datasets.registry import load_bundle
    from genesis_gpu.contracts import RunSpec
    from genesis_gpu.study.design import seed_for
    if state['run']['stage'] != 's1':
        raise ValueError('S1 only; S2 is never read')
    original = read_json(V2_RUN / 'protocol-lock.json')
    cfg = copy.deepcopy(original['config'])
    cfg.update(device='cpu', analysis_dtype='float32')
    payload = {'run': state['run'], 'checkpoint_index': state['checkpoint_index']}
    receipt_path = V2_RUN / 'checkpoints' / state['run']['run_id'] / 'training_receipt.json'
    receipt_sha = sha256_file(receipt_path)
    src, srcval, pv = rebuild_snapshot(payload, cfg, V2_RUN)  # verifies data fingerprint + model SHA
    op = FrozenOperator(copy.deepcopy(src.model).double(), src.inputs, src.targets, src.loss,
                        microbatch=src.microbatch, dtype=torch.float64)
    val = FrozenOperator(copy.deepcopy(srcval.model).double(), srcval.inputs, srcval.targets, srcval.loss,
                         microbatch=srcval.microbatch, dtype=torch.float64)
    run = RunSpec.from_dict(payload['run'])
    bundle = load_bundle(run, cfg, V2_RUN)
    if bundle.fingerprint != pv['data_sha']:
        raise ValueError('Dataset fingerprint mismatch')
    # Reconstruct the T32 indices of v2's replacement sampling and verify them bit-exactly.
    gen = torch.Generator()
    gen.manual_seed(seed_for('BATCH', pv['batch_seed'], 'train', 0))
    ids = torch.randint(bundle.size('train'), (cfg['curvature_batch'],), generator=gen)
    Xtr, Ytr = bundle.splits['train']
    if not (torch.equal(Xtr[ids].float().double(), op.inputs) and torch.equal(Ytr[ids].float().double(), op.targets)):
        raise ValueError('Could not reproduce the v2 T32 curvature batch indices')
    gen = torch.Generator()
    gen.manual_seed(seed_for('BATCH', seed_for('FROZEN_VALIDATION_BATCH_V2', run.seed), 'validation', 0))
    vids = torch.randint(bundle.size('validation'), (cfg['curvature_batch'],), generator=gen)
    Xv, Yv = bundle.splits['validation']
    if not torch.equal(Xv[vids].float().double(), val.inputs):
        raise ValueError('Could not reproduce the v2 V32 validation batch indices')
    if sha256_file(receipt_path) != receipt_sha:
        raise ValueError('Training receipt changed during read')
    pv = dict(pv)
    pv['training_receipt_sha256'] = receipt_sha
    pv['v2_validation_batch_indices'] = vids.tolist()
    return op, val, pv, bundle, original, ids


def weights_of(op):
    params = op.layout.unflatten(op.theta)
    names = [e.name for e in op.layout.entries]
    expected = [f'layers.{i}.weight' for i in range(len(names))]
    if names != expected:
        raise ValueError(f'Unexpected DLN layout {names}')
    return [params[n] for n in names]
