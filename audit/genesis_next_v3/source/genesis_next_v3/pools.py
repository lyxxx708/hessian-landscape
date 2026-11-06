"""One deterministic, hashed evaluation schedule per training seed (shared by checkpoints, gammas, methods).

Primary values: FP32-rounded then lifted to FP64 (same mathematical treatment as v2's batches).
Native-FP64 copies are kept only as a precision-sensitivity column.
"""
from __future__ import annotations
import math
import torch
from .env import object_sha

V8_GROUPS, V8_SIZE = 8, 128
E_GROUPS, E_SIZE = 8, 1024
T512 = 512
T_SUB = 32  # size of disjoint gradient-variance subsets
NS_T512 = 'GENESIS_NEXT_V3_T512_EXCLUDING_T32'
NS_V8 = 'GENESIS_NEXT_V3_V8x128_PERMUTATION'
NS_E = 'GENESIS_NEXT_V3_E8x1024_EVAL_POOL'


def lift(t):
    return t.float().double()


def tsha(t):
    from genesis_gpu.curvature.params import tensor_sha
    return tensor_sha(t)


def regenerate_teacher(run, bundle):
    """Re-run v2's synthetic generator prefix and verify it reproduces the frozen splits exactly."""
    from genesis_gpu.study.design import seed_for
    from genesis_gpu.curvature.params import tensor_dict_sha
    m = run['model']
    rng = torch.Generator()
    rng.manual_seed(seed_for('DATA', run['seed']))
    eig = torch.logspace(0, math.log10(m['covariance_condition']), m['input_dim'], dtype=torch.float64)
    eig = eig / eig.mean()
    rotation, _ = torch.linalg.qr(torch.randn(m['input_dim'], m['input_dim'], generator=rng, dtype=torch.float64))
    teacher = torch.randn(m['output_dim'], m['input_dim'], generator=rng, dtype=torch.float64) / math.sqrt(m['input_dim'])
    if tensor_dict_sha({'teacher': teacher}) != bundle.source['teacher_sha']:
        raise ValueError('Teacher regeneration mismatch')
    for name in ('train', 'validation', 'test'):
        X, Y = bundle.splits[name]
        x = (torch.randn(len(X), m['input_dim'], generator=rng, dtype=torch.float64) * eig.sqrt()) @ rotation.T
        if not (torch.equal(x, X) and torch.equal(x @ teacher.T, Y)):
            raise ValueError(f'Split regeneration mismatch: {name}')
    return eig, rotation, teacher


def build_pools(run, bundle, t32_ids):
    from genesis_gpu.study.design import seed_for
    seed = run['seed']
    eig, rotation, teacher = regenerate_teacher(run, bundle)
    Xtr, Ytr = bundle.splits['train']
    Xv, Yv = bundle.splits['validation']
    Xte, Yte = bundle.splits['test']
    excluded = set(int(i) for i in t32_ids.tolist())
    g = torch.Generator()
    g.manual_seed(seed_for(NS_T512, seed))
    perm = torch.randperm(len(Xtr), generator=g)
    t512 = torch.tensor([int(i) for i in perm.tolist() if int(i) not in excluded][:T512])
    g = torch.Generator()
    g.manual_seed(seed_for(NS_V8, seed))
    vperm = torch.randperm(len(Xv), generator=g)
    g = torch.Generator()
    g.manual_seed(seed_for(NS_E, seed))
    xe = (torch.randn(E_GROUPS * E_SIZE, eig.numel(), generator=g, dtype=torch.float64) * eig.sqrt()) @ rotation.T
    ye = xe @ teacher.T
    native = {'E8192': (xe, ye), 'V1024': (Xv[vperm], Yv[vperm]), 'Test1024': (Xte, Yte)}
    pools = {
        'T32': (lift(Xtr[t32_ids]), lift(Ytr[t32_ids])),
        'T512': (lift(Xtr[t512]), lift(Ytr[t512])),
        'T4096': (lift(Xtr), lift(Ytr)),
        'V1024': (lift(Xv[vperm]), lift(Yv[vperm])),
        'E8192': (lift(xe), lift(ye)),
        'Test1024': (lift(Xte), lift(Yte)),
    }
    groups = {'V8x128': [(i * V8_SIZE, (i + 1) * V8_SIZE) for i in range(V8_GROUPS)],
              'E8x1024': [(i * E_SIZE, (i + 1) * E_SIZE) for i in range(E_GROUPS)],
              'T512_sub32': [(i * T_SUB, (i + 1) * T_SUB) for i in range(8)]}
    identity = {
        'seed': seed, 'namespaces': {'T512': NS_T512, 'V8': NS_V8, 'E': NS_E},
        't32_indices': [int(i) for i in t32_ids.tolist()], 't32_unique': len(excluded),
        't512_indices_sha': object_sha([int(i) for i in t512.tolist()]),
        't512_overlap_with_t32': len(excluded & set(int(i) for i in t512.tolist())),
        'v_permutation_sha': object_sha([int(i) for i in vperm.tolist()]),
        'teacher_sha': bundle.source['teacher_sha'], 'data_fingerprint': bundle.fingerprint,
        'pool_sha': {k: object_sha([tsha(x), tsha(y)]) for k, (x, y) in pools.items()},
        'native_pool_sha': {k: object_sha([tsha(x), tsha(y)]) for k, (x, y) in native.items()},
        'groups': groups, 'input_policy': 'FP32_ROUNDED_LIFTED_TO_FP64 (primary); native FP64 (sensitivity)'}
    if identity['t512_overlap_with_t32']:
        raise ValueError('T512 overlaps T32')
    return pools, native, groups, identity, t512
