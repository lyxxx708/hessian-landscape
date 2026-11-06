"""Frozen analysis: python analyze.py <run_dir>. Builds all required tables from results/, alpha_grid/, slopes/."""
import csv
import json
import math
import statistics
import sys
from collections import defaultdict
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
from genesis_next_v3.env import read_json, write_json

OUT = Path(sys.argv[1])
lock = read_json(OUT / 'PROTOCOL_LOCK.json')
CFG = lock['config']
GRID = CFG['alpha_grid']
OLD = CFG['train_selection_grid']
PRIMARY = ('V1024', 'E8192')
GROUPS = {'V1024': 'V8x128', 'E8192': 'E8x1024'}
BOOT = CFG['bootstrap']


def sgn(v, b):
    return 1 if v > b else (-1 if v < -b else 0)


def write_csv(name, rows):
    if not rows:
        (OUT / name).write_text('', encoding='utf-8')
        return
    keys = []
    for r in rows:
        for k in r:
            if k not in keys:
                keys.append(k)
    with open(OUT / name, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)


def boot_median(vals, seed=BOOT['seed'], reps=BOOT['replicates']):
    vals = [v for v in vals if v is not None and not (isinstance(v, float) and math.isnan(v))]
    if not vals:
        return None, None, None
    rng = np.random.default_rng(seed)
    a = np.asarray(vals, float)
    bs = [np.median(rng.choice(a, len(a), replace=True)) for _ in range(reps)]
    return float(np.median(a)), float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))


def med(x):
    x = [v for v in x if v is not None]
    return statistics.median(x) if x else None


# ---------------- load ----------------
results = {p.stem: read_json(p) for p in sorted((OUT / 'results').glob('*.json'))}
alpha_rows = [json.loads(l) for p in sorted((OUT / 'alpha_grid').glob('*.jsonl')) for l in open(p, encoding='utf-8')]
slope_rows = [json.loads(l) for p in sorted((OUT / 'slopes').glob('*.jsonl')) for l in open(p, encoding='utf-8')]
plan = read_json(OUT / 'RUN_PLAN.json')
with open(OUT / 'VALIDATION_ALPHA_GRID.jsonl', 'w', encoding='utf-8') as f:
    for r in alpha_rows:
        f.write(json.dumps(r) + '\n')
with open(OUT / 'DIRECTIONAL_SLOPE_AND_HVP.jsonl', 'w', encoding='utf-8') as f:
    for r in slope_rows:
        f.write(json.dumps(r) + '\n')

# ---------------- coverage / qualification / failures ----------------
qual_rows, fail_rows, ref_rows = [], [], []
cond_status = {}
for st in plan['states']:
    sid = st['state_id']
    r = results.get(sid)
    if r is None:
        for gam in (0.001, 0.01, 0.1):
            qual_rows.append({'state_id': sid, 'setting_id': st['setting_id'], 'seed': st['seed'], 'checkpoint': st['checkpoint'],
                              'gamma': gam, 'status': 'TIMEOUT_INCONCLUSIVE_OR_NOT_RUN'})
        continue
    for f in r['failures']:
        fail_rows.append({'state_id': sid, **{k: str(v) for k, v in f.items() if k != 'trace'}})
    for c in r['conditions']:
        q = c.get('qualification', {})
        cond_status[(sid, c['gamma'])] = c['status']
        qual_rows.append({'state_id': sid, 'setting_id': r['setting_id'], 'seed': r['seed'], 'checkpoint': r['checkpoint'],
                          'gamma': c['gamma'], 'lambda_absolute': c['lambda_absolute'], 'status': c['status'],
                          'block_kron_direct_vs_dense': q.get('block_kron_direct_vs_dense'),
                          'block_kron_localcg_vs_dense': q.get('block_kron_localcg_vs_dense'),
                          'max_block_condition': max(q['block_condition_numbers']) if q.get('block_condition_numbers') else None,
                          'max_operator_error': max(max(e.values()) for e in q['operator_checks']) if q.get('operator_checks') else None,
                          'full_dense_relative_residual': q.get('full_dense_relative_residual'),
                          'full_cg_v2_operator_direction_error': q.get('full_cg_v2_operator_direction_error'),
                          'F_block_agreement': q.get('F_block_agreement'), 'delta_v3': q.get('delta'),
                          'delta_next_v2': c['next_v2']['delta'],
                          'delta_abs_diff': abs(q['delta'] - c['next_v2']['delta']) if q.get('delta') is not None else None,
                          'cg8_vs_next_v2': q.get('cg8', {}).get('vs_next_v2_cg8_direction')})
        ref_rows.append({'state_id': sid, 'gamma': c['gamma'], 'status': c['status'], **q})
    if 'V4' in r:
        for c in r['V4'].get('conditions', []):
            qual_rows.append({'state_id': sid, 'setting_id': r['setting_id'], 'seed': r['seed'], 'checkpoint': r['checkpoint'],
                              'gamma': c['gamma'], 'status': 'V4:' + c.get('status', '?'),
                              'block_kron_direct_vs_dense': c.get('block_kron_vs_dense'),
                              'full_cg_v2_operator_direction_error': c.get('Q0_matrix_free_direction_error')})
write_csv('NUMERIC_QUALIFICATION.csv', qual_rows)
write_csv('FAILURES.csv', fail_rows or [{'state_id': None, 'stage': None, 'error': 'NONE_RECORDED'}])
with open(OUT / 'BLOCK_REFERENCE_CHECKS.jsonl', 'w', encoding='utf-8') as f:
    for r in ref_rows:
        f.write(json.dumps(r) + '\n')


# ---------------- Exp V attribution ----------------
def at(entry, i):
    return -entry['dL'][i], entry['bound'][i]


def attribution(row, pool, alpha_key):
    e = row['pools'][pool]
    a = row['selected_alpha'][alpha_key]
    i = GRID.index(a)
    gain, b = at(e, i)
    s, sb = e['slope'], e['slope_bound']
    q2 = a * s - 0.5 * a * a * e['curv_H']
    smaller = [(-e['dL'][j], e['bound'][j]) for j in range(1, i)]
    out = {'pool': pool, 'alpha_policy': alpha_key, 'alpha': a, 'L0': e['L0'], 'gain': gain, 'gain_bound': b,
           'gain_sign': sgn(gain, b), 'gain_over_L0': gain / e['L0'] if e['L0'] else None,
           'slope': s, 'slope_bound': sb, 'slope_sign': sgn(s, sb), 'curv_H': e['curv_H'], 'curv_GGN': e['curv_GGN'],
           'pred1_gain': a * s, 'pred2_gain': q2,
           'rel_mismatch_2nd': abs(gain - q2) / max(abs(gain), abs(q2), 1e-300),
           'smaller_alpha_resolved_positive': any(sgn(v, bb) == 1 for v, bb in smaller),
           'best_gain_on_pool_grid': max(-x for x in e['dL'])}
    if 'groups' in e:
        sg = [sgn(-gr['dL'][i], gr['bound'][i]) for gr in e['groups']]
        out.update(groups_pos=sg.count(1), groups_neg=sg.count(-1), groups_indet=sg.count(0),
                   groups_slope_neg=sum(sgn(gr['slope'], gr['slope_bound']) == -1 for gr in e['groups']))
    labels = []
    if pool in PRIMARY and out['gain_sign'] == -1:
        if out['slope_sign'] == -1:
            labels.append('FIRST_ORDER_CONFLICT')
        if out['slope_sign'] == 1 and out['smaller_alpha_resolved_positive']:
            labels.append('STEP_OVERSHOOT')
        if q2 > 0:
            labels.append('CURVATURE_OR_HIGHER_ORDER_MISMATCH')
        if 'groups' in e and out['groups_pos'] > 0 and out['groups_neg'] > 0:
            labels.append('BATCH_HETEROGENEITY')
        if not labels:
            labels.append('INCONCLUSIVE')
    elif pool in PRIMARY and out['gain_sign'] == 0:
        labels.append('NUMERICALLY_INDETERMINATE')
    out['labels'] = '|'.join(labels)
    return out


attr = []
for row in alpha_rows:
    if row['direction_batch'] != 'T32':
        continue
    base = {k: row[k] for k in ('state_id', 'setting_id', 'seed', 'checkpoint', 'gamma', 'direction', 'condition_status')}
    for pool in row['pools']:
        attr.append({**base, **attribution(row, pool, 'T32_oldgrid')})
    # validation-assisted diagnostic (choose on V-half A, report on held-out halves/pools)
    a = row['selected_alpha']['VhalfA_oldgrid_DIAGNOSTIC']
    i = GRID.index(a)
    vb = row['pools']['V1024']['groups'][4:]
    attr.append({**base, 'pool': 'VhalfB', 'alpha_policy': 'VALIDATION_ASSISTED_DIAGNOSTIC', 'alpha': a,
                 'gain': -sum(gr['dL'][i] for gr in vb) / 4, 'gain_bound': sum(gr['bound'][i] for gr in vb) / 4})
    for pool in ('E8192', 'Test1024'):
        g, b = at(row['pools'][pool], i)
        attr.append({**base, 'pool': pool, 'alpha_policy': 'VALIDATION_ASSISTED_DIAGNOSTIC', 'alpha': a, 'gain': g,
                     'gain_bound': b, 'gain_sign': sgn(g, b)})
    for key, pool in (('V1024_oracle_DIAGNOSTIC', 'V1024'), ('E8192_oracle_DIAGNOSTIC', 'E8192')):
        a = row['selected_alpha'][key]
        g, b = at(row['pools'][pool], GRID.index(a))
        attr.append({**base, 'pool': pool, 'alpha_policy': 'ORACLE_UPPER_BOUND_' + pool, 'alpha': a, 'gain': g,
                     'gain_bound': b, 'gain_sign': sgn(g, b)})
for r in attr:
    r['gain_sign'] = r.get('gain_sign', sgn(r['gain'], r['gain_bound']))
write_csv('VALIDATION_ATTRIBUTION.csv', attr)

# ---------------- V4 ----------------
v4rows = []
by = defaultdict(dict)
for row in alpha_rows:
    by[(row['state_id'], row['gamma'], row['direction'])][row['direction_batch']] = row
for (sid, gam, d), rr in sorted(by.items()):
    if 'T512' not in rr or 'T32' not in rr:
        continue
    r32, r512 = rr['T32'], rr['T512']
    rec = {'state_id': sid, 'setting_id': r32['setting_id'], 'seed': r32['seed'], 'checkpoint': r32['checkpoint'],
           'gamma': gam, 'direction': d, 'T512_status': r512['condition_status'],
           'alpha_T32dir_T32sel': r32['selected_alpha']['T32_oldgrid'], 'alpha_T32dir_T512sel': r32['selected_alpha']['T512_oldgrid'],
           'alpha_T512dir_T512sel': r512['selected_alpha']['T512_oldgrid']}
    for pool in ('E8192', 'V1024', 'Test1024'):
        for tag, row, key in (('a_original', r32, 'T32_oldgrid'), ('b_steponly', r32, 'T512_oldgrid'), ('c_direction', r512, 'T512_oldgrid')):
            i = GRID.index(row['selected_alpha'][key])
            g, b = at(row['pools'][pool], i)
            rec[f'{pool}_{tag}_gain'] = g
            rec[f'{pool}_{tag}_sign'] = sgn(g, b)
        rec[f'{pool}_slope_T32dir'] = r32['pools'][pool]['slope']
        rec[f'{pool}_slope_T512dir'] = r512['pools'][pool]['slope']
        rec[f'{pool}_slope_sign_T32dir'] = sgn(r32['pools'][pool]['slope'], r32['pools'][pool]['slope_bound'])
        rec[f'{pool}_slope_sign_T512dir'] = sgn(r512['pools'][pool]['slope'], r512['pools'][pool]['slope_bound'])
    v4rows.append(rec)
write_csv('V4_INTERVENTION.csv', v4rows)

# ---------------- Exp B cost ----------------
cost = []
for sid, r in results.items():
    T, Qy = r.get('expB_timing'), r.get('expB_quality')
    if not T or not Qy:
        continue
    t = lambda name: T[name]['wall_median_s']
    common = t('common:gradient_v2_operator') + t('common:line_search_T32')
    qd = t('common:qd_explicit_cached')
    qd_ad = t('common:qd_v2_operator')
    lams = [c['gamma'] for c in r['conditions']]
    for key, q in Qy.items():
        name = key.split('#')[0]
        gi = int(key.split('#')[1])
        tm = T[name]
        mode, method = tm['mode'], tm['method']
        nl = 1 if mode == 'cold' else 3
        q_add = qd_ad if method in ('old_block_cg',) or method.endswith('_ad') else qd
        cond = r['conditions'][gi]
        Fs, FB = cond['qualification']['F_star'], cond['qualification']['F_block']
        cost.append({'state_id': sid, 'setting_id': r['setting_id'], 'seed': r['seed'], 'checkpoint': r['checkpoint'],
                     'gamma': q['gamma'], 'mode': mode, 'method': method, 'k': tm.get('k'), 'rtol': tm.get('rtol'),
                     'timing_status': tm['timing_status'], 'cv': tm['cv'], 'inner_calls': tm['inner_calls'],
                     'method_wall_s': tm['wall_median_s'], 'method_cpu_s': tm['cpu_median_s'],
                     'method_wall_per_gamma_s': tm['wall_median_s'] / nl,
                     'raw_policy_e2e_per_gamma_s': tm['wall_median_s'] / nl + common,
                     'ray_policy_e2e_per_gamma_s': tm['wall_median_s'] / nl + q_add + common,
                     'ray_policy_method_plus_qd_per_gamma_s': tm['wall_median_s'] / nl + q_add,
                     'common_gradient_plus_linesearch_s': common,
                     'F_raw_over_Fstar': q['F_raw_over_Fstar'], 'F_ray_over_Fstar': q['F_ray_over_Fstar'],
                     'raw_step_F_over_Fstar': q['raw_step_F_over_Fstar'], 'ray_step_F_over_Fstar': q['ray_step_F_over_Fstar'],
                     'F_block_over_Fstar': FB / Fs, 'best_ray_scale': q['best_ray_scale'],
                     'vs_exact_block_direction': q.get('vs_exact_block_direction')})
write_csv('BLOCK_CG_COST.csv', cost)

# comparisons per (state, gamma) cold and per state warm
cmp_rows = []
idx = defaultdict(dict)
for c in cost:
    idx[(c['state_id'], c['gamma'], c['mode'])][c['method']] = c
for (sid, gam, mode), mm in sorted(idx.items()):
    if 'block_kron_direct' not in mm:
        continue
    B = mm['block_kron_direct']
    FBr = B['F_block_over_Fstar']
    tol = CFG['gain_matching_tolerance_Fstar']
    out = {'state_id': sid, 'setting_id': B['setting_id'], 'seed': B['seed'], 'checkpoint': B['checkpoint'], 'gamma': gam, 'mode': mode,
           'F_block_over_Fstar': FBr, 'block_direct_method_s': B['method_wall_per_gamma_s'],
           'block_direct_timing': B['timing_status']}
    for pol, Fk, tk in (('raw', 'raw_step_F_over_Fstar', 'raw_policy_e2e_per_gamma_s'),
                        ('ray', 'F_ray_over_Fstar', 'ray_policy_e2e_per_gamma_s'),
                        ('ray_method_only', 'F_ray_over_Fstar', 'ray_policy_method_plus_qd_per_gamma_s')):
        target = (FBr if pol != 'raw' else B[Fk]) - tol
        ks = sorted([m for m in mm if m.startswith('cg') and m[2:].isdigit()], key=lambda m: int(m[2:]))
        hit = next((m for m in ks if mm[m][Fk] >= target), None)
        out[f'{pol}_cg_first_k_reaching_block'] = int(hit[2:]) if hit else None
        out[f'{pol}_cost_ratio_cg_vs_block_direct'] = mm[hit][tk] / B[tk] if hit else None
        out[f'{pol}_timing_ok'] = (hit is not None and mm[hit]['timing_status'] == 'OK' and B['timing_status'] == 'OK')
        hit99 = next((m for m in ks if mm[m][Fk] >= 0.99), None)
        out[f'{pol}_cg_first_k_099'] = int(hit99[2:]) if hit99 else None
        out[f'{pol}_block_099_status'] = 'QUALITY_TARGET_UNATTAINABLE' if B[Fk] < 0.99 else 'ATTAINED'
        out[f'{pol}_cost_ratio_cg099_vs_block_direct'] = mm[hit99][tk] / B[tk] if hit99 else None
    if 'old_block_cg' in mm:
        O = mm['old_block_cg']
        out['old_block_over_block_direct_method'] = O['method_wall_s'] / B['method_wall_s']
        ks_ad = [m for m in mm if m.endswith('_ad')]
        hit_ad = next((m for m in sorted(ks_ad, key=lambda m: int(m[2:-3])) if mm[m]['F_ray_over_Fstar'] >= FBr - tol), None)
        out['historical_cg_ad_vs_old_block_method'] = (mm[hit_ad]['method_wall_s'] + 0) / O['method_wall_s'] if hit_ad else None
    if 'block_kron_localcg' in mm:
        out['localcg_over_direct_method'] = mm['block_kron_localcg']['method_wall_s'] / B['method_wall_s']
    for r_ in CFG['timing']['cg_rtols']:
        m = mm.get(f'cg_rtol{r_:g}')
        if m:
            out[f'cg_rtol{r_:g}_raw_F'] = m['raw_step_F_over_Fstar']
            out[f'cg_rtol{r_:g}_raw_cost_ratio'] = m['raw_policy_e2e_per_gamma_s'] / B['raw_policy_e2e_per_gamma_s']
    cmp_rows.append(out)
write_csv('BLOCK_CG_COMPARISON.csv', cmp_rows)

# ---------------- seed-level paired summary ----------------
seed_rows = []
settings = sorted({r['setting_id'] for r in results.values()})
summary = {'coverage': {}, 'expV': {}, 'V4': {}, 'expB': {}}
qualified = {k for k, v in cond_status.items() if v == 'QUALIFIED'}
summary['coverage'] = {'parent_states': 80, 'parent_conditions': 240, 'states_planned': len(plan['states']),
                       'states_with_results': len(results), 'conditions_qualified': len(qualified),
                       'conditions_numeric_unresolved': sum(v == 'NUMERIC_UNRESOLVED' for v in cond_status.values()),
                       'conditions_failed': sum(v == 'FAILED' for v in cond_status.values()),
                       'conditions_source_not_ready': 240 - 3 * len(plan['states'])}
A = [a for a in attr if a['alpha_policy'] == 'T32_oldgrid' and (a['state_id'], a['gamma']) in qualified]
for d in ('Full', 'Block', 'CG8'):
    for pool in ('T32', 'T512', 'T4096', 'V32_v2', 'V1024', 'E8192', 'Test1024', 'V1024_native', 'E8192_native', 'Test1024_native'):
        rows = [a for a in A if a['direction'] == d and a['pool'] == pool]
        if not rows:
            continue
        key = f'{d}:{pool}'
        lab = defaultdict(int)
        for a in rows:
            for l in (a.get('labels') or '').split('|'):
                if l:
                    lab[l] += 1
        summary['expV'][key] = {'n': len(rows), 'gain_neg': sum(a['gain_sign'] == -1 for a in rows),
                                'gain_pos': sum(a['gain_sign'] == 1 for a in rows), 'gain_indet': sum(a['gain_sign'] == 0 for a in rows),
                                'slope_neg': sum(a['slope_sign'] == -1 for a in rows), 'slope_pos': sum(a['slope_sign'] == 1 for a in rows),
                                'slope_indet': sum(a['slope_sign'] == 0 for a in rows), 'labels': dict(lab),
                                'median_gain_over_L0': med([a['gain_over_L0'] for a in rows])}
        for st in settings:
            for seed in sorted({a['seed'] for a in rows if a['setting_id'] == st}):
                rs = [a for a in rows if a['setting_id'] == st and a['seed'] == seed]
                seed_rows.append({'analysis': 'expV', 'setting_id': st, 'seed': seed, 'direction': d, 'pool': pool,
                                  'n_conditions': len(rs), 'frac_gain_neg': sum(a['gain_sign'] == -1 for a in rs) / len(rs),
                                  'frac_slope_neg': sum(a['slope_sign'] == -1 for a in rs) / len(rs),
                                  'frac_overshoot': sum('STEP_OVERSHOOT' in (a.get('labels') or '') for a in rs) / len(rs),
                                  'frac_first_order_conflict': sum('FIRST_ORDER_CONFLICT' in (a.get('labels') or '') for a in rs) / len(rs),
                                  'median_gain': med([a['gain'] for a in rs]), 'median_gain_over_L0': med([a['gain_over_L0'] for a in rs]),
                                  'median_alpha': med([a['alpha'] for a in rs])})
# per-setting seed-cluster bootstrap of the seed-level negative fraction (E8192, V1024)
for d in ('Full', 'Block', 'CG8'):
    for pool in ('V1024', 'E8192'):
        for st in settings + ['ALL']:
            vals = [r['frac_gain_neg'] for r in seed_rows if r['analysis'] == 'expV' and r['direction'] == d and r['pool'] == pool
                    and (st == 'ALL' or r['setting_id'] == st)]
            m_, lo, hi = boot_median(vals)
            summary['expV'].setdefault('seed_level_frac_neg', {})[f'{d}:{pool}:{st}'] = {'n_seeds': len(vals), 'median': m_, 'ci95': [lo, hi]}
# V4 seed-level
for d in ('Full', 'Block', 'CG8'):
    rows = [r for r in v4rows if r['direction'] == d and r['T512_status'] == 'QUALIFIED' and (r['state_id'], r['gamma']) in qualified]
    for pool in ('E8192', 'V1024'):
        neg_a = [r for r in rows if r[f'{pool}_a_original_sign'] == -1]
        summary['V4'][f'{d}:{pool}'] = {
            'n': len(rows), 'a_neg': len(neg_a), 'b_neg': sum(r[f'{pool}_b_steponly_sign'] == -1 for r in rows),
            'c_neg': sum(r[f'{pool}_c_direction_sign'] == -1 for r in rows),
            'repaired_by_direction_among_a_neg': sum(r[f'{pool}_c_direction_sign'] >= 0 for r in neg_a),
            'repaired_by_steponly_among_a_neg': sum(r[f'{pool}_b_steponly_sign'] >= 0 for r in neg_a),
            'steponly_alpha_zero_among_a_neg': sum(r['alpha_T32dir_T512sel'] == 0 for r in neg_a),
            'direction_alpha_zero_among_a_neg': sum(r['alpha_T512dir_T512sel'] == 0 for r in neg_a),
            'repaired_by_direction_with_positive_gain': sum(r[f'{pool}_c_direction_sign'] == 1 for r in neg_a),
            'repaired_by_steponly_with_positive_gain': sum(r[f'{pool}_b_steponly_sign'] == 1 for r in neg_a),
            'slope_neg_T32dir': sum(r[f'{pool}_slope_sign_T32dir'] == -1 for r in rows),
            'slope_neg_T512dir': sum(r[f'{pool}_slope_sign_T512dir'] == -1 for r in rows),
            'median_gain_a': med([r[f'{pool}_a_original_gain'] for r in rows]),
            'median_gain_b': med([r[f'{pool}_b_steponly_gain'] for r in rows]),
            'median_gain_c': med([r[f'{pool}_c_direction_gain'] for r in rows])}
        seeds = sorted({(r['setting_id'], r['seed']) for r in rows})
        sl = []
        for st, seed in seeds:
            rs = [r for r in rows if r['setting_id'] == st and r['seed'] == seed]
            na = [r for r in rs if r[f'{pool}_a_original_sign'] == -1]
            rec = {'analysis': 'V4', 'setting_id': st, 'seed': seed, 'direction': d, 'pool': pool, 'n_conditions': len(rs),
                   'a_neg': len(na), 'c_repairs': sum(r[f'{pool}_c_direction_sign'] >= 0 for r in na),
                   'b_repairs': sum(r[f'{pool}_b_steponly_sign'] >= 0 for r in na),
                   'median_gain_a': med([r[f'{pool}_a_original_gain'] for r in rs]),
                   'median_gain_b': med([r[f'{pool}_b_steponly_gain'] for r in rs]),
                   'median_gain_c': med([r[f'{pool}_c_direction_gain'] for r in rs])}
            rec['seed_direction_repairs_majority'] = rec['a_neg'] > 0 and rec['c_repairs'] > rec['a_neg'] / 2
            rec['seed_steponly_repairs_majority'] = rec['a_neg'] > 0 and rec['b_repairs'] > rec['a_neg'] / 2
            seed_rows.append(rec)
            sl.append(rec)
        summary['V4'][f'{d}:{pool}']['seeds'] = len(sl)
        summary['V4'][f'{d}:{pool}']['seeds_with_a_neg'] = sum(r['a_neg'] > 0 for r in sl)
        summary['V4'][f'{d}:{pool}']['seeds_direction_repairs_majority'] = sum(r['seed_direction_repairs_majority'] for r in sl)
        summary['V4'][f'{d}:{pool}']['seeds_steponly_repairs_majority'] = sum(r['seed_steponly_repairs_majority'] for r in sl)
# Exp B seed-level
for mode in ('cold', 'warm'):
    for pol in ('raw', 'ray', 'ray_method_only'):
        rows = [c for c in cmp_rows if c['mode'] == mode and (c['state_id'], c['gamma']) in qualified]
        ok = [c for c in rows if c[f'{pol}_timing_ok']]
        for st in settings + ['ALL']:
            seeds = sorted({(c['setting_id'], c['seed']) for c in ok if st == 'ALL' or c['setting_id'] == st})
            vals = []
            for s_ in seeds:
                v = [c[f'{pol}_cost_ratio_cg_vs_block_direct'] for c in ok if (c['setting_id'], c['seed']) == s_
                     and c[f'{pol}_cost_ratio_cg_vs_block_direct'] is not None]
                if v:
                    vals.append(statistics.median(v))
                    if st == 'ALL':
                        seed_rows.append({'analysis': f'expB:{mode}:{pol}', 'setting_id': s_[0], 'seed': s_[1],
                                          'median_cost_ratio_cg_reaching_FB_vs_block_direct': statistics.median(v),
                                          'n_conditions': len(v)})
            m_, lo, hi = boot_median(vals)
            summary['expB'][f'{mode}:{pol}:{st}'] = {'n_conditions': len([c for c in rows if st == 'ALL' or c['setting_id'] == st]),
                                                     'n_timing_ok': len([c for c in ok if st == 'ALL' or c['setting_id'] == st]),
                                                     'n_seeds': len(vals), 'median_seed_ratio': m_, 'ci95': [lo, hi],
                                                     'cg_never_reaches_block': sum(c[f'{pol}_cg_first_k_reaching_block'] is None for c in rows
                                                                                   if st == 'ALL' or c['setting_id'] == st),
                                                     'median_first_k': med([c[f'{pol}_cg_first_k_reaching_block'] for c in rows
                                                                            if st == 'ALL' or c['setting_id'] == st])}
cold = [c for c in cmp_rows if c['mode'] == 'cold']
summary['expB']['historical'] = {
    'median_old_block_over_block_direct': med([c.get('old_block_over_block_direct_method') for c in cold]),
    'median_cg_ad_reaching_FB_over_old_block': med([c.get('historical_cg_ad_vs_old_block_method') for c in cold]),
    'median_localcg_over_direct': med([c.get('localcg_over_direct_method') for c in cold]),
    'timing_inconclusive_tasks': sum(1 for r in results.values() for t in (r.get('expB_timing') or {}).values() if t['timing_status'] != 'OK'),
    'timing_tasks': sum(len(r.get('expB_timing') or {}) for r in results.values()),
    'block_099_unattainable_conditions': sum(c['ray_block_099_status'] == 'QUALITY_TARGET_UNATTAINABLE' for c in cold)}
write_csv('PAIRED_SEED_SUMMARY.csv', seed_rows)
write_json(OUT / 'ANALYSIS_SUMMARY.json', summary)
print(json.dumps(summary['coverage']))
