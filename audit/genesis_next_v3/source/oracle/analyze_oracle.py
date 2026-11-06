"""Addendum A1 frozen analysis: python oracle/analyze_oracle.py <oracle_run_dir>"""
import csv
import json
import math
import random
import statistics
import sys
from collections import defaultdict
from pathlib import Path

run = Path(sys.argv[1])
V3 = Path(r'E:\GENESIS\runs\genesis_next_v3')
OLD_GRID_INDEX = {a: i for i, a in enumerate([0.0, 1e-05, 0.0001, 0.001, 0.003, 0.01, 0.03, 0.1, 0.3, 1.0, 3.0])}
BOOT, BOOT_SEED = 2000, 20261106


def med(x):
    x = [v for v in x if v is not None]
    return statistics.median(x) if x else None


def lr(a, b):
    return math.log10(a / b) if a and b and a > 0 and b > 0 else None


def sign(v, b):
    return 1 if v > b else (-1 if v < -b else 0)


plan = json.load(open(V3 / 'RUN_PLAN.json', encoding='utf-8'))
ledger = [json.loads(l) for l in open(run / 'EXECUTION_LEDGER.jsonl', encoding='utf-8')] if (run / 'EXECUTION_LEDGER.jsonl').exists() else []
rows, qual, mc = [], [], []
for st in plan['states']:
    p = run / 'results' / f"{st['state_id']}.json"
    if not p.exists():
        qual.append({'state_id': st['state_id'], 'status': 'MISSING'})
        continue
    r = json.load(open(p, encoding='utf-8'))
    v3rows = {(x['gamma'], x['direction'], x['direction_batch']): x
              for x in map(json.loads, open(V3 / 'alpha_grid' / f"{st['state_id']}.jsonl", encoding='utf-8'))}
    qual.append({'state_id': r['state_id'], 'status': r['status'], **{k: v for k, v in r['checks'].items()}})
    for d in r['directions']:
        o = d['continuous_optimum']
        P = d['policies']
        ap = o['POP']['alpha_opt']
        row = {'state_id': r['state_id'], 'setting_id': r['setting_id'], 'seed': r['seed'], 'checkpoint': r['checkpoint'],
               'gamma': d['gamma'], 'direction': d['direction'], 'direction_batch': d['direction_batch'],
               'oracle_status': d['oracle_status'], 'replay_norm_rel': d.get('replay_direction_norm_rel'),
               'R0_pop': o['POP']['R0'], 'pop_slope': o['POP']['slope_at_0'], 'pop_slope_closed': d['population_slope_closed_form'],
               'alpha_pop': ap, 'max_pop_gain': o['POP']['max_gain'], 'n_local_minima_pop': o['POP']['n_local_minima']}
        for k in ('T32', 'T512', 'T4096', 'E8192'):
            row[f'alpha_cont_{k}'] = o[k]['alpha_opt']
        for k, v in P.items():
            t = k.replace('grid:', 'g_').replace('continuous:', 'c_').replace('_oldgrid', '').replace('_DIAGNOSTIC', '_diag')
            row[f'{t}_alpha'] = v['alpha']
            row[f'{t}_pop_gain'] = v['pop_gain']
            row[f'{t}_pop_gain_sign'] = sign(v['pop_gain'], v['pop_gain_bound'])
            row[f'{t}_regret'] = v['pop_regret']
            row[f'{t}_regret_over_max'] = v['pop_regret_over_max_gain']
            row[f'{t}_log10_over_pop'] = v['log10_alpha_over_pop']
        v3r = v3rows.get((d['gamma'], d['direction'], d['direction_batch']))
        if v3r is not None and 'T32_oldgrid' in v3r['selected_alpha']:
            a = v3r['selected_alpha']['T32_oldgrid']
            e = v3r['pools']['E8192']
            row['v3_E8192_sign_at_T32'] = e['sign_gain'][OLD_GRID_INDEX[a]]
            row['v3_E8192_slope_sign'] = sign(e['slope'], e['slope_bound'])
        rows.append(row)
        for tag in ('E8192_native', 'E8192_fp32lifted'):
            for x in d[f'mc_agreement_{tag}']:
                if x['alpha'] > 0:
                    mc.append({'state_id': r['state_id'], 'gamma': d['gamma'], 'direction': d['direction'],
                               'direction_batch': d['direction_batch'], 'pool': tag, **x})


def write_csv(name, data):
    if not data:
        return
    keys = []
    for d in data:
        for k in d:
            if k not in keys:
                keys.append(k)
    with open(run / name, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(data)


write_csv('ORACLE_STEP_TABLE.csv', rows)
write_csv('ORACLE_QUALIFICATION.csv', qual)
write_csv('ORACLE_MC_AGREEMENT.csv', mc)

ok = [r for r in rows if r['oracle_status'] == 'QUALIFIED']


def by_seed(sel, f):
    s = defaultdict(list)
    for r in sel:
        v = f(r)
        if v is not None:
            s[r['seed']].append(v)
    return {k: med(v) for k, v in s.items() if v}


def boot(seed_vals):
    vals = list(seed_vals.values())
    if not vals:
        return None
    rng = random.Random(BOOT_SEED)
    meds = sorted(statistics.median([rng.choice(vals) for _ in vals]) for _ in range(BOOT))
    return [meds[int(0.025 * BOOT)], meds[int(0.975 * BOOT) - 1]]


def stat(sel, f, pred):
    s = by_seed(sel, f)
    n_true = sum(1 for v in s.values() if pred(v))
    lab = ('SUPPORTED_WITHIN_DLN_EXPLORATION' if n_true * 2 > len(s) else
           'INCONCLUSIVE' if n_true * 2 == len(s) else 'CONTRADICTED_WITHIN_DLN_EXPLORATION') if s else 'NOT_TESTED'
    return {'seeds': len(s), 'seeds_true': n_true, 'median_of_seed_medians': med(list(s.values())), 'ci95': boot(s), 'label': lab}


def ad(x):
    return abs(x) if x is not None else None


def diff(a, b):
    return a - b if a is not None and b is not None else None


summary = {'coverage': {'parent_states': 80, 'parent_conditions': 240, 'states_planned': len(plan['states']),
                        'states_with_results': sum(q['status'] != 'MISSING' for q in qual),
                        'states_qualified': sum(q['status'] == 'QUALIFIED' for q in qual),
                        'direction_rows': len(rows), 'direction_rows_qualified': sum(r['oracle_status'] == 'QUALIFIED' for r in rows),
                        'ledger_entries': len(ledger), 'ledger_non_exit0': [l for l in ledger if l.get('status') != 'EXIT_0']},
           'statements': {}, 'descriptive': {}}
for dname in ('Full', 'Block', 'CG8'):
    T = [r for r in ok if r['direction'] == dname and r['direction_batch'] == 'T32']
    F = [r for r in ok if r['direction'] == dname and r['direction_batch'] == 'T512']
    S = summary['statements'].setdefault(dname, {})
    S['P1_T32_overshoots_pop'] = stat(T, lambda r: r['c_T32_log10_over_pop'], lambda v: v > 0)
    S['P1_grid_T32_above_pop'] = stat(T, lambda r: (1.0 if r['g_T32_alpha'] > r['alpha_pop'] else 0.0), lambda v: v > 0.5)
    S['P2a_T512_closer_continuous'] = stat(T, lambda r: diff(ad(r['c_T512_log10_over_pop']), ad(r['c_T32_log10_over_pop'])), lambda v: v < 0)
    S['P2b_T512_lower_regret_grid'] = stat(T, lambda r: diff(r['g_T512_regret'], r['g_T32_regret']), lambda v: v < 0)
    a = by_seed(T, lambda r: diff(ad(r['c_T512_log10_over_pop']), ad(r['c_T32_log10_over_pop'])))
    b = by_seed(T, lambda r: diff(r['g_T512_regret'], r['g_T32_regret']))
    both = sum(1 for k in a if k in b and a[k] < 0 and b[k] < 0)
    S['P2_joint'] = {'seeds': len(a), 'seeds_true': both,
                     'label': 'SUPPORTED_WITHIN_DLN_EXPLORATION' if both * 2 > len(a) else
                     ('INCONCLUSIVE' if both * 2 == len(a) else 'CONTRADICTED_WITHIN_DLN_EXPLORATION')}
    if F:
        S['P3_T512dir_same_batch_overshoot'] = stat(F, lambda r: r['c_T512_log10_over_pop'], lambda v: v > 0)
        S['P3_T512dir_same_minus_independent'] = stat(F, lambda r: diff(r['c_T512_log10_over_pop'], r['c_T32_log10_over_pop']), lambda v: v > 0)
        V4seeds = {r['seed'] for r in F}
        TV = [r for r in T if r['seed'] in V4seeds]
        S['P3_T32dir_same_minus_independent_V4seeds'] = stat(TV, lambda r: diff(r['c_T32_log10_over_pop'], r['c_T512_log10_over_pop']), lambda v: v > 0)
        a3 = by_seed(F, lambda r: r['c_T512_log10_over_pop'])
        b3 = by_seed(F, lambda r: diff(r['c_T512_log10_over_pop'], r['c_T32_log10_over_pop']))
        j = sum(1 for k in a3 if k in b3 and a3[k] > 0 and b3[k] > 0)
        S['P3_joint'] = {'seeds': len(a3), 'seeds_true': j,
                         'label': 'SUPPORTED_WITHIN_DLN_EXPLORATION' if j * 2 > len(a3) else
                         ('INCONCLUSIVE' if j * 2 == len(a3) else 'CONTRADICTED_WITHIN_DLN_EXPLORATION')}
    # descriptive
    D = summary['descriptive'].setdefault(dname, {})
    for batch, sel in (('T32', T), ('T512', F)):
        if not sel:
            continue
        e = {'n': len(sel), 'median_alpha_pop': med([r['alpha_pop'] for r in sel])}
        for pol in ('g_T32', 'g_T512', 'g_T4096', 'c_T32', 'c_T512', 'c_T4096', 'c_E8192', 'g_E8192_oracle_diag'):
            if f'{pol}_alpha' not in sel[0]:
                continue
            e[pol] = {'median_alpha': med([r[f'{pol}_alpha'] for r in sel]),
                      'median_log10_over_pop': med([r[f'{pol}_log10_over_pop'] for r in sel]),
                      'frac_above_pop': sum(r[f'{pol}_alpha'] > r['alpha_pop'] for r in sel) / len(sel),
                      'pop_gain_neg': sum(r[f'{pol}_pop_gain_sign'] < 0 for r in sel),
                      'pop_gain_pos': sum(r[f'{pol}_pop_gain_sign'] > 0 for r in sel),
                      'median_regret_over_max_gain': med([r[f'{pol}_regret_over_max'] for r in sel]),
                      'median_gain_fraction_captured': med([1 - r[f'{pol}_regret_over_max'] for r in sel if r[f'{pol}_regret_over_max'] is not None])}
        e['pop_slope_neg'] = sum(r['pop_slope'] < 0 for r in sel)
        e['exact_step_overshoot'] = sum(r['pop_slope'] > 0 and r['g_T32_pop_gain_sign'] < 0 for r in sel)
        e['exact_first_order_conflict_with_neg_gain'] = sum(r['pop_slope'] < 0 and r['g_T32_pop_gain_sign'] < 0 for r in sel)
        e['multiple_local_minima'] = sum(r['n_local_minima_pop'] > 1 for r in sel)
        if batch == 'T32':
            agree = [r for r in sel if r.get('v3_E8192_sign_at_T32') not in (None, 0)]
            e['P4_pop_vs_v3_E8192_sign_agreement'] = sum(r['g_T32_pop_gain_sign'] == r['v3_E8192_sign_at_T32'] for r in agree) / len(agree) if agree else None
            e['P5_pop_vs_v3_E8192_slope_sign_agreement'] = (sum((r['pop_slope'] > 0) == (r['v3_E8192_slope_sign'] > 0) for r in sel) / len(sel))
        D[batch] = e
P = [r for r in ok if r['direction_batch'] == 'POP_DIAGNOSTIC']
summary['descriptive']['POP_DIAGNOSTIC'] = {'n': len(P), 'median_alpha_pop': med([r['alpha_pop'] for r in P]),
                                            'median_max_gain_over_R0': med([r['max_pop_gain'] / r['R0_pop'] for r in P])}
# max attainable gain of T512 vs T32 direction (direction quality without step confounding)
key = lambda r: (r['state_id'], r['gamma'], r['direction'])
T32m = {key(r): r for r in ok if r['direction_batch'] == 'T32'}
dq = defaultdict(list)
for r in ok:
    if r['direction_batch'] == 'T512' and key(r) in T32m:
        dq[r['direction']].append((r['seed'], r['max_pop_gain'] / T32m[key(r)]['max_pop_gain'] if T32m[key(r)]['max_pop_gain'] > 0 else None))
summary['descriptive']['T512_vs_T32_direction_max_pop_gain_ratio'] = {
    d: {'n': len(v), 'median_ratio': med([x for _, x in v]), 'frac_T512_better': sum(1 for _, x in v if x and x > 1) / len(v)} for d, v in dq.items()}
zs = [abs(x['z_gain']) for x in mc if x['pool'] == 'E8192_native']
zl = [abs(x['z_loss']) for x in mc if x['pool'] == 'E8192_native']
summary['mc_agreement_E8192_native'] = {'n': len(zs), 'median_abs_z_gain': med(zs), 'frac_abs_z_gain_gt3': sum(z > 3 for z in zs) / len(zs) if zs else None,
                                        'median_abs_z_loss': med(zl), 'frac_abs_z_loss_gt3': sum(z > 3 for z in zl) / len(zl) if zl else None,
                                        'note': 'z within one state are strongly correlated across alphas and directions (same 8192 samples)'}
with open(run / 'ORACLE_SUMMARY.json', 'w', encoding='utf-8') as f:
    json.dump(summary, f, indent=1, sort_keys=True)
print(json.dumps(summary['coverage']))
