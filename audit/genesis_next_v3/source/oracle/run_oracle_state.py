"""Addendum A1, one state in a fresh process: python oracle/run_oracle_state.py <state_id> <out_dir> [--allow-unfrozen]

Recomputes the frozen v3 directions (T32: Full, Block, CG8; V4 settings also T512: Full, Block, CG8), verifies them
against the v3 records, and evaluates every train-only step choice against the exact population risk."""
import json
import math
import sys
import time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'oracle'))
from genesis_next_v3 import env
env.configure_torch()
import numpy as np
import torch
from genesis_next_v3.env import read_json, write_json, sha256_file, v3_code_hashes
from genesis_next_v3.source import next_v2_states, load_state, weights_of
from genesis_next_v3.pools import build_pools, regenerate_teacher
from genesis_next_v3.dln_kron import DLN, cg_lean, best_ray
from genesis_next_v3.directions import compute_directions, dense_reference, dense_from_dln, rel
from genesis_next_v3.alpha_grid import ALPHA_GRID, OLD_GRID
from genesis_next_v3.assay import V4_SETTINGS
import pop_oracle as po

V3_RUN = Path(r'E:\GENESIS\runs\genesis_next_v3')
REPLAY_NORM_RTOL = {'T32': 1e-12, 'T512': 1e-9}   # T512: v3 used the AD gradient, here the closed-form one
RISK_PATH_RTOL = 1e-12
POP_GRADIENT_RTOL = 1e-10
ROOT_RTOL = 1e-4   # derivative-root minimiser vs Brent on direct values (Brent limited by flatness, ~sqrt(eps))


def oracle_code_hashes():
    files = sorted((ROOT / 'oracle').glob('*.py')) + sorted((ROOT / 'oracle').glob('*.md'))
    return {str(p.relative_to(ROOT)).replace('\\', '/'): sha256_file(p) for p in files}


def main():
    sid, out = sys.argv[1], Path(sys.argv[2])
    lock_path = out / 'ORACLE_LOCK.json'
    if lock_path.exists():
        lock = read_json(lock_path)
        changed = [k for k, v in {**lock['oracle_code_sha256'], **lock['v3_code_sha256']}.items()
                   if {**oracle_code_hashes(), **v3_code_hashes()}.get(k) != v]
        if changed:
            raise SystemExit(f'Code changed after freeze: {changed}')
        freeze = lock['freeze_sha']
    elif '--allow-unfrozen' in sys.argv:
        freeze = 'UNFROZEN_QUALIFICATION_ONLY'
    else:
        raise SystemExit('No ORACLE_LOCK.json: refusing to produce results before freeze')
    t0 = time.perf_counter()
    state = [s for s in next_v2_states()[0] if s['state_id'] == sid][0]
    v3res = read_json(V3_RUN / 'results' / f'{sid}.json')
    v3rows = [json.loads(l) for l in open(V3_RUN / 'alpha_grid' / f'{sid}.jsonl', encoding='utf-8')]
    v3idx = {(r['gamma'], r['direction'], r['direction_batch']): r for r in v3rows}
    op, val, pv, bundle, original, ids = load_state(state)
    W = weights_of(op)
    m = DLN(W, op.inputs, op.targets)
    pools, native, groups_idx, pool_identity, t512 = build_pools(state['run'], bundle, ids)
    if pool_identity['pool_sha'] != v3res['pool_identity']['pool_sha']:
        raise ValueError('Pools differ from the v3 run')
    eig, rotation, teacher = regenerate_teacher(state['run'], bundle)
    pop = po.Population(eig, rotation, teacher)
    rec = {'state_id': sid, 'setting_id': state['setting_id'], 'seed': state['seed'], 'checkpoint': state['checkpoint'],
           'freeze_sha': freeze, 'v3_freeze_sha': v3res['freeze_sha'],
           'v3_result_sha256': sha256_file(V3_RUN / 'results' / f'{sid}.json'),
           'v3_alpha_grid_sha256': sha256_file(V3_RUN / 'alpha_grid' / f'{sid}.jsonl'),
           'teacher_sha': bundle.source['teacher_sha'], 'population': {
               'definition': 'x = R diag(sqrt(eig)) z, z~N(0,I); y = A x (noise-free); R = ||(M-A) R D^1/2||_F^2/(2 d_out)',
               'covariance_condition': float(eig.max() / eig.min()), 'd_in': pop.din, 'd_out': pop.dout},
           'checks': {}, 'directions': [], 'failures': []}
    # ---- population oracle self-checks ----
    Wg = [w.clone().requires_grad_(True) for w in W]
    D = (po.product(Wg) - pop.A) @ pop.B
    Rt = D.square().sum() / (2 * pop.dout)
    ag = torch.autograd.grad(Rt, Wg)
    cg = pop.gradient(W)
    rec['checks']['risk_trace_vs_dln_path'] = abs(pop.risk(W) - pop.risk_via_dln(W)) / pop.risk(W)
    rec['checks']['pop_gradient_closed_vs_autograd'] = rel(torch.cat([c.reshape(-1) for c in cg]),
                                                          torch.cat([a.reshape(-1) for a in ag]))
    rec['checks']['R0_population'] = pop.risk(W)
    objs = {'POP': pop, 'T32': po.Pool(*pools['T32']), 'T512': po.Pool(*pools['T512']), 'T4096': po.Pool(*pools['T4096']),
            'E8192': po.Pool(*pools['E8192']), 'E8192_native': po.Pool(*native['E8192'])}
    for k in ('T32', 'T512', 'T4096', 'E8192'):
        rec['checks'][f'L0_{k}_vs_v3'] = abs(objs[k].risk(W) - v3idx[(v3res['conditions'][0]['gamma'], 'Full', 'T32')]['pools'][k]['L0'])
    dense = dense_reference(op)
    groups = op.layout.group_indices('coarse')
    gammas = [c['gamma'] for c in v3res['conditions']]
    lams = [c['lambda_absolute'] for c in v3res['conditions']]
    dirsets = []
    for gam, lam in zip(gammas, lams):
        dirs, q, g = compute_directions(op, m, lam, groups, dense['G'], dense['gradient'], with_cg_v2=False)
        for name in ('Full', 'Block', 'CG8'):
            dirsets.append((gam, lam, name, 'T32', dirs[name], q['status']))
    if state['setting_id'] in V4_SETTINGS:
        X5, Y5 = pools['T512']
        m5 = DLN(W, X5, Y5)
        g5 = m5.gradient()
        G5 = dense_from_dln(m5).numpy()
        m5.build_factors()
        for gam, lam in zip(gammas, lams):
            Q5 = G5 + lam * np.eye(len(g5))
            Qt = lambda v: torch.as_tensor(Q5 @ v.numpy())
            full = torch.as_tensor(np.linalg.solve(Q5, -g5.numpy()))
            bK = m5.block_direct(g5, lam)
            aB, _ = best_ray(g5, bK, Qt(bK))
            x8, _ = cg_lean(lambda v: m5.ggn_vec(v) + lam * v, -g5, 8)
            a8, _ = best_ray(g5, x8, Qt(x8))
            for name, d in (('Full', full), ('Block', aB * bK), ('CG8', a8 * x8)):
                dirsets.append((gam, lam, name, 'T512', d, 'QUALIFIED'))
    # population-Newton diagnostic direction (same absolute damping), never used for any selection
    mP = DLN(W, pop.X_eff, pop.Y_eff)
    GP = pop.din * dense_from_dln(mP).numpy()
    gP = pop.din * mP.gradient()
    rec['checks']['pop_gradient_dln_vs_closed'] = rel(gP, torch.cat([c.reshape(-1) for c in cg]))
    for gam, lam in zip(gammas, lams):
        dP = torch.as_tensor(np.linalg.solve(GP + lam * np.eye(len(gP)), -gP.numpy()))
        dirsets.append((gam, lam, 'Full', 'POP_DIAGNOSTIC', dP, 'DIAGNOSTIC'))
    curves = []
    for gam, lam, name, batch, d, dstatus in dirsets:
        E = m.split(d)
        row = {'gamma': gam, 'lambda_absolute': lam, 'direction': name, 'direction_batch': batch,
               'direction_status': dstatus, 'direction_norm': float(d.norm())}
        v3r = v3idx.get((gam, name, batch))
        if v3r is not None:
            row['replay_direction_norm_rel'] = abs(row['direction_norm'] - v3r['direction_norm']) / v3r['direction_norm']
            row['replay_T32_curve_max_abs'] = max(abs(objs['T32'].risk(po.ray(W, E, a)) - v3r['pools']['T32']['loss_naive'][i])
                                                  for i, a in enumerate(ALPHA_GRID))
            row['replay_ok'] = row['replay_direction_norm_rel'] <= REPLAY_NORM_RTOL[batch]
            row['v3_selected_alpha'] = v3r['selected_alpha']
        opt = {k: po.minimize_on_ray(o, W, E) for k, o in objs.items()}
        row['continuous_optimum'] = {k: {kk: vv for kk, vv in v.items() if kk != 'coefficients'} for k, v in opt.items()}
        row['population_polynomial'] = opt['POP']['coefficients']
        ap = opt['POP']['alpha_opt']
        R0 = opt['POP']['R0']
        gpop = pop.gradient(W)
        row['population_slope_closed_form'] = -float(sum((a * e).sum() for a, e in zip(gpop, E)))
        policies = {}
        if v3r is not None:
            for k, a in v3r['selected_alpha'].items():
                policies[f'grid:{k}'] = a
        for k in ('T32', 'T512', 'T4096', 'E8192'):
            policies[f'continuous:{k}'] = opt[k]['alpha_opt']
        policies['population_optimum'] = ap
        ev = {}
        for k, a in policies.items():
            Ra = pop.risk(po.ray(W, E, a))
            ev[k] = {'alpha': a, 'pop_gain': R0 - Ra, 'pop_gain_bound': po.gain_bound(R0, Ra),
                     'pop_gain_over_R0': (R0 - Ra) / R0, 'pop_regret': Ra - opt['POP']['R_opt'],
                     'pop_regret_over_max_gain': (Ra - opt['POP']['R_opt']) / opt['POP']['max_gain'] if opt['POP']['max_gain'] > 0 else None,
                     'log10_alpha_over_pop': math.log10(a / ap) if a > 0 and ap > 0 else None}
        row['policies'] = ev
        row['mc_agreement_E8192_native'] = po.mc_agreement(pop, objs['E8192_native'], W, E, ALPHA_GRID)
        row['mc_agreement_E8192_fp32lifted'] = po.mc_agreement(pop, objs['E8192'], W, E, ALPHA_GRID)
        o = opt['POP']
        ok = ((o['alpha_opt'] == 0 or o['alpha_brent_rel_disagreement'] <= ROOT_RTOL)
              and o['R_brent_minus_R_opt'] >= -1e-13 * o['R0'] and not o['at_upper_boundary'])
        row['oracle_status'] = 'QUALIFIED' if ok and row.get('replay_ok', True) else 'NUMERIC_UNRESOLVED'
        rec['directions'].append(row)
        curves.append({'state_id': sid, 'gamma': gam, 'direction': name, 'direction_batch': batch,
                       'alphas': po.CURVE_ALPHAS, 'population_risk': [pop.risk(po.ray(W, E, a)) for a in po.CURVE_ALPHAS],
                       'T32_loss': [objs['T32'].risk(po.ray(W, E, a)) for a in po.CURVE_ALPHAS],
                       'T512_loss': [objs['T512'].risk(po.ray(W, E, a)) for a in po.CURVE_ALPHAS],
                       'E8192_loss': [objs['E8192'].risk(po.ray(W, E, a)) for a in po.CURVE_ALPHAS]})
    ck = rec['checks']
    state_ok = (ck['risk_trace_vs_dln_path'] <= RISK_PATH_RTOL and ck['pop_gradient_closed_vs_autograd'] <= POP_GRADIENT_RTOL
                and ck['pop_gradient_dln_vs_closed'] <= POP_GRADIENT_RTOL
                and max(ck[f'L0_{k}_vs_v3'] for k in ('T32', 'T512', 'T4096', 'E8192')) <= 1e-15)
    rec['state_checks_ok'] = state_ok
    rec['status'] = 'QUALIFIED' if state_ok and all(r['oracle_status'] == 'QUALIFIED' for r in rec['directions']) else 'NUMERIC_UNRESOLVED'
    rec['wall_s'] = time.perf_counter() - t0
    for d in ('results', 'curves'):
        (out / d).mkdir(parents=True, exist_ok=True)
    with open(out / 'curves' / f'{sid}.jsonl', 'w', encoding='utf-8') as f:
        for c in curves:
            f.write(json.dumps(c, allow_nan=False) + '\n')
    write_json(out / 'results' / f'{sid}.json', rec)
    print(json.dumps({'state_id': sid, 'status': rec['status'], 'wall_s': round(rec['wall_s'], 1), 'n_dirs': len(rec['directions'])}))


if __name__ == '__main__':
    main()
