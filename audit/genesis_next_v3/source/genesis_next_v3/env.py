"""Thread pinning and read-only input verification. Must be imported before torch does real work."""
from __future__ import annotations
import hashlib
import json
import os
import sys
from pathlib import Path

THREAD_ENV = {'OMP_NUM_THREADS': '2', 'OPENBLAS_NUM_THREADS': '2', 'MKL_NUM_THREADS': '2',
              'CUBLAS_WORKSPACE_CONFIG': ':4096:8'}
for _k, _v in THREAD_ENV.items():
    os.environ[_k] = _v

V2_SOURCE = Path(r'E:\GENESIS\handoff\audit_snapshot_20261104_201035\07_SOURCE\executed_source')
V2_RUN = Path(r'E:\GENESIS\runs\genesis_full_v2')
NEXT_V2_SOURCE = Path(r'E:\GENESIS\worktrees\genesis-next-v2')
NEXT_V2_RUN = Path(r'E:\GENESIS\runs\genesis_next_v2')
V3_ROOT = Path(__file__).resolve().parents[1]
V2_PROTOCOL_LOCK_SHA = 'f9f4868297d359bf0538ac0ba6e64e3e8087911699150f6a0b33ed11fca41263'


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def object_sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def read_json(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(value, f, indent=1, sort_keys=True, allow_nan=False, default=_default)
    tmp.replace(path)


def _default(x):
    import numpy as np
    if isinstance(x, (np.floating,)):
        return float(x)
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, np.ndarray):
        return x.tolist()
    raise TypeError(type(x))


def configure_torch(threads=2):
    import torch
    torch.set_num_threads(threads)
    try:
        torch.set_num_interop_threads(1)
    except RuntimeError:
        pass
    torch.set_float32_matmul_precision('highest')
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    sys.dont_write_bytecode = True
    for p in (str(V2_SOURCE), str(NEXT_V2_SOURCE)):
        if p not in sys.path:
            sys.path.insert(0, p)


def verify_inputs():
    """Pin the executed v2 source and the NEXT v2 package by the hashes recorded in the NEXT v2 follow-up lock."""
    lock = read_json(NEXT_V2_RUN / 'FOLLOWUP_LOCK.json')
    if lock['inputs']['protocol_lock_sha256'] != V2_PROTOCOL_LOCK_SHA:
        raise RuntimeError('NEXT v2 lock refers to a different v2 protocol lock')
    if sha256_file(V2_RUN / 'protocol-lock.json') != V2_PROTOCOL_LOCK_SHA:
        raise RuntimeError('Original v2 protocol lock changed')
    bad = [e['path'] for e in lock['code']['files'] if sha256_file(NEXT_V2_SOURCE / e['path']) != e['sha256']]
    if bad:
        raise RuntimeError(f'NEXT v2 source hash mismatch: {bad}')
    manifest = read_json(V2_SOURCE / 'DELIVERY_MANIFEST.json') if (V2_SOURCE / 'DELIVERY_MANIFEST.json').exists() else None
    return {'next_v2_followup_lock_sha256': sha256_file(NEXT_V2_RUN / 'FOLLOWUP_LOCK.json'),
            'next_v2_freeze_sha': lock.get('freeze_sha'),
            'next_v2_code_files_verified': len(lock['code']['files']),
            'v2_protocol_lock_sha256': V2_PROTOCOL_LOCK_SHA,
            'v2_source_root': str(V2_SOURCE),
            'v2_source_files_sha256': {str(p.relative_to(V2_SOURCE)).replace('\\', '/'): sha256_file(p)
                                       for p in sorted((V2_SOURCE / 'genesis_gpu').rglob('*.py'))},
            'v2_delivery_manifest_present': manifest is not None,
            'threads_env': {k: os.environ.get(k) for k in THREAD_ENV}}


def v3_code_hashes():
    files = sorted(list((V3_ROOT / 'genesis_next_v3').glob('*.py')) + list((V3_ROOT / 'scripts').glob('*.py'))
                   + list((V3_ROOT / 'configs').glob('*.json')) + list((V3_ROOT / 'tests').glob('*.py')))
    return {str(p.relative_to(V3_ROOT)).replace('\\', '/'): sha256_file(p) for p in files}
