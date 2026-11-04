"""The v2 finite design: 26x5 S1 and 6x16 S2; no outcome-driven sampling."""
from __future__ import annotations
from dataclasses import asdict
from pathlib import Path
import hashlib
import math
import yaml
from genesis_gpu.contracts import ModelSpec, TrainSpec, RunSpec, object_sha


def setting_specs():
    settings = []
    for depth in (4, 8, 16):
        for balance in ('orthogonal_balanced', 'random_unbalanced'):
            for cond in (1, 100):
                sid = f'dln_d{depth}_w16_{balance}_c{cond}'
                m = ModelSpec('dln', depth, 16, 16, 16, balance=balance, covariance_condition=cond)
                settings.append((sid, m, TrainSpec(), 'synthetic_dln'))
    for depth in (4, 8, 16):
        settings.append((f'dln_d{depth}_w32_orthogonal_balanced_c1', ModelSpec('dln', depth, 32, 32, 32), TrainSpec(), 'synthetic_dln'))
    for depth in (3, 6, 12):
        for act in ('relu', 'tanh'):
            m = ModelSpec('mlp', depth, 128, 784, 10, activation=act, image_size=28, channels=1)
            t = TrainSpec('adamw', 'epochs', 20, 128, 32, .001, .0001)
            settings.append((f'mlp_d{depth}_{act}', m, t, 'mnist'))
    for depth in (8, 20):
        m = ModelSpec('resnet', depth, 16, 3072, 10, normalization='groupnorm')
        t = TrainSpec('sgd', 'epochs', 80, 128, 32, .1, .0005, augmentation=True)
        settings.append((f'resnet{depth}_gn', m, t, 'cifar10'))
    for depth in (2, 4, 8):
        m = ModelSpec('transformer', depth, 192, 192, 192, normalization='layernorm', heads=6, context=128, vocab_size=256)
        t = TrainSpec('adamw', 'tokens', 50_000_000, 64, 4, .0003, .01)
        settings.append((f'transformer_d{depth}', m, t, 'shakespeare'))
    assert len(settings) == 26
    return settings


def default_config(profile='full'):
    if profile not in {'full', 'smoke'}:
        raise ValueError('profile must be full or smoke')
    return {
        'schema_version': 2, 'profile': profile, 'study_id': 'genesis_full_v2' if profile == 'full' else 'genesis_smoke_v2',
        'root': r'E:\GENESIS\runs\genesis_full_v2' if profile == 'full' else 'local_artifacts/smoke_v2',
        'storage_root': r'E:\GENESIS' if profile == 'full' else 'local_artifacts',
        'device': 'cuda:0' if profile == 'full' else 'cpu',
        'seed_namespace': 'GENESIS_V2_20261102', 's1_seeds': 5 if profile == 'full' else 1,
        's2_seeds': 16 if profile == 'full' else 1,
        'damping_ratios': [.001, .01, .1] if profile == 'full' else [.1],
        'groups': ['coarse', 'fine'] if profile == 'full' else ['coarse'],
        'curvature_batch': 32 if profile == 'full' else 2,
        'curvature_microbatch': 4 if profile == 'full' else 2,
        'damping_floor': 1e-8, 'power_iterations': 30 if profile == 'full' else 8,
        'analysis_dtype': 'float32' if profile == 'full' else 'float64',
        'solver': {'rtol': 1e-5 if profile == 'full' else 1e-9, 'max_iter': 1000 if profile == 'full' else 160,
                   'stability_factor': .1, 'delta_stability': .005, 'dense_limit': 2048 if profile == 'full' else 256,
                   'preconditioner_probes': 8 if profile == 'full' else 0, 'short_cg_steps': 8},
        'probes': {'schedule': [16, 32, 64, 128, 256] if profile == 'full' else [4, 8],
                   'relative_halfwidth': .2 if profile == 'full' else 2., 'bootstrap': 1000 if profile == 'full' else 40,
                   'independent_final': True, 'deep_max': 256 if profile == 'full' else 8},
        'statistics': {'bootstrap': 2000 if profile == 'full' else 80, 'alpha': .05, 'delta_median': .05,
                       'delta_lower': .01, 'min_eligible_fraction': .8, 'tail_cv': .15, 'tail_amplitude': .02,
                       'auc': .75, 'auc_improvement': .10, 'spearman': .5, 'mae_improvement': .1},
        'resources': {'vram_target_gib': 9.5, 'thermal_pause_c': 85, 'disk_reserve_gib': 30 if profile == 'full' else 0,
                      'heartbeat_seconds': 15, 'stale_seconds': 300, 'max_retries': 2,
                      'microbatch_fallback': [32, 16, 8, 4, 2, 1]},
        'data': {'text_url': 'https://www.gutenberg.org/cache/epub/2270/pg2270.txt',
                 'text_license': 'Project Gutenberg eBook 2270; First Folio 1623; US catalog public-domain; local law and actual file notice require source review; no raw redistribution',
                 'text_expected_sha256': None, 'text_license_accepted': False,
                 'image_license_accepted': False, 'download_timeout_seconds': 120},
        'line_search': [0., .01, .03, .1, .3, 1., 3.],
        's3': {'enabled': True, 'seeds': 8, 'tuning_seeds': 3, 'lr_multipliers': [.3, 1., 3.],
               'baselines': ['adamw', 'layerwise_gn', 'same_cost_cg', 'gradient_smoothing', 'kfac', 'selective_krylov'],
               'target_loss_fraction': .5, 'time_improvement': .1, 'negative_control_steps': 32,
               'calibration_steps': 12, 'tuning_fraction': .1, 'evaluation_modes': ['samples', 'wall_time'],
               'window_strength': .1, 'damping_ratio': .01}
    }


def load_config(path: Path):
    with Path(path).open(encoding='utf-8') as f:
        cfg = yaml.safe_load(f)
    if not isinstance(cfg, dict):
        raise ValueError('Configuration must be a mapping')
    expected = default_config(cfg.get('profile', 'full'))
    unknown = set(cfg) - set(expected)
    missing = set(expected) - set(cfg)
    if unknown or missing:
        raise ValueError(f'Config schema mismatch; unknown={unknown}, missing={missing}')
    if cfg['schema_version'] != 2:
        raise ValueError('v1 configuration is not executable by v2')
    for group in ('solver', 'probes', 'statistics', 'resources', 'data', 's3'):
        if set(cfg[group]) != set(expected[group]):
            raise ValueError(f'Unknown/missing nested config key in {group}')
    if not cfg['damping_ratios'] or any(not math.isfinite(v) or v <= 0 for v in cfg['damping_ratios']):
        raise ValueError('Positive finite relative damping is required')
    if cfg['s1_seeds'] < 1 or cfg['s2_seeds'] < 1:
        raise ValueError('At least one independent seed')
    if not cfg['probes']['independent_final']:
        raise ValueError('v2 requires independent final probes after adaptive pilot selection')
    schedule=cfg['probes']['schedule']
    if not schedule or schedule!=sorted(set(schedule)) or any(not isinstance(v,int) or v<2 for v in schedule):
        raise ValueError('Probe schedule must be increasing positive counts >=2')
    for group,key in [('solver','rtol'),('solver','stability_factor'),('solver','delta_stability'),('probes','relative_halfwidth')]:
        if not math.isfinite(cfg[group][key]) or cfg[group][key]<=0:raise ValueError('Invalid finite numerical tolerance')
    if cfg['solver']['rtol']>=1 or cfg['solver']['stability_factor']>=1:raise ValueError('Invalid solver tolerance tightening')
    for group,key in [('solver','max_iter'),('probes','bootstrap'),('statistics','bootstrap'),('resources','heartbeat_seconds')]:
        if not isinstance(cfg[group][key],int) or cfg[group][key]<1:raise ValueError('Positive integer execution parameter required')
    if not math.isfinite(cfg['resources']['disk_reserve_gib']) or cfg['resources']['disk_reserve_gib']<0:raise ValueError('Invalid disk reserve')
    if cfg['analysis_dtype'] not in ('float32','float64'):raise ValueError('Curvature analysis forbids reduced precision')
    if not cfg['groups'] or any(s not in ('coarse','fine') for s in cfg['groups']):raise ValueError('Unknown parameter grouping')
    if cfg['profile'] == 'full':
        if cfg['s1_seeds'] != 5 or cfg['s2_seeds'] != 16:
            raise ValueError('Approved v2 full design fixes 5 S1 / 16 S2 seeds')
        if not cfg['device'].startswith('cuda'):
            raise ValueError('Production cannot silently fall back to CPU')
    return cfg


def seed_for(namespace: str, *parts) -> int:
    raw = '\0'.join([namespace, *map(str, parts)]).encode()
    return int.from_bytes(hashlib.sha256(raw).digest()[:8], 'big') % (2**63 - 1)


def smoke_specs():
    t = TrainSpec('adam', 'steps', 3, 4, 2, .005, save_every_steps=1, schedule='constant')
    return [
        ('smoke_dln', ModelSpec('dln', 3, 2, 2, 2), t, 'synthetic_dln'),
        ('smoke_mlp', ModelSpec('mlp', 3, 4, 4, 3, activation='tanh'), t, 'synthetic_classification'),
        ('smoke_resnet', ModelSpec('resnet', 8, 2, 192, 3, image_size=8, normalization='groupnorm'), t, 'synthetic_image'),
        ('smoke_transformer', ModelSpec('transformer', 2, 4, 4, 4, heads=1, context=4, vocab_size=7, normalization='layernorm', tie_weights=True), t, 'synthetic_text')
    ]


def expand_design(cfg) -> list[RunSpec]:
    settings = setting_specs() if cfg['profile'] == 'full' else smoke_specs()
    anchors = {'dln_d8_w16_random_unbalanced_c100', 'dln_d16_w16_random_unbalanced_c100',
               'mlp_d6_relu', 'resnet20_gn', 'transformer_d4', 'transformer_d8'}
    runs = []
    for stage in ('s1', 's2'):
        for sid, model, train, dataset in settings:
            if stage == 's2' and cfg['profile'] == 'full' and sid not in anchors:
                continue
            n = cfg['s1_seeds'] if stage == 's1' else cfg['s2_seeds']
            for i in range(n):
                seed = seed_for(cfg['seed_namespace'], stage, sid, i)
                rid = f'{stage}-{sid}-s{i:02d}-{seed:016x}'
                deep = i == 0 or (stage == 's2' and sid in {'resnet20_gn', 'transformer_d8'})
                runs.append(RunSpec(rid, sid, stage, seed, i, model, train, dataset, deep))
    if len({r.seed for r in runs}) != len(runs):
        raise ValueError('Seed collision; choose a new namespace BEFORE freeze')
    return runs


def measurement_tier(stage, checkpoint_index, gamma, deep):
    if deep and checkpoint_index in (0, 3):
        return 'C_DEEP'
    if checkpoint_index in (0, 3) and (abs(gamma - .01) < 1e-12 or (stage == 's2' and abs(gamma - .1) < 1e-12)):
        return 'C_BASE'
    return 'B'


def checkpoint_steps(total_steps: int, fractions=(0., 1/3, 2/3, 1.)) -> tuple[int, ...]:
    if total_steps < len(fractions) - 1:
        raise ValueError('Training too short for distinct frozen checkpoints')
    steps = tuple(round(total_steps * f) for f in fractions)
    if len(set(steps)) != len(steps):
        raise ValueError('Checkpoint collision; cannot count duplicate states')
    return steps
