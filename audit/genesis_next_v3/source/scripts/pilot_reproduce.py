"""Gate 2: reproduce NEXT v2 T32 line-search numerics on the two predeclared pilot states.
Pilot results are qualification only and are excluded from inference."""
import json
import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from genesis_next_v3 import env
env.configure_torch()
import torch
from genesis_next_v3.env import read_json, write_json, sha256_file
from genesis_next_v3.source import next_v2_states, load_state, weights_of
from genesis_next_v3.dln_kron import DLN
from genesis_next_v3.directions import compute_directions, dense_reference
from genesis_next_v3.alpha_grid import evaluate_direction, select_alpha, OLD_GRID

OUT = Path(sys.argv[1])
tol = read_json(env.V3_ROOT / 'configs' / 'pilot_tolerance.json')
states, _ = next_v2_states()
from genesis_next.solvers import cg, block_cg
from genesis_next.assay import loss_trials

report = {'tolerance_file_sha256': sha256_file(env.V3_ROOT / 'configs' / 'pilot_tolerance.json'),
          'inputs': env.verify_inputs(), 'states': [], 'class': 'QUALIFICATION_PILOT_EXCLUDED_FROM_INFERENCE'}
all_ok = True
A, B = tol['replay_A_next_v2_code_path'], tol['replay_B_v3_code_path']
for ps in tol['pilot_states']:
    st = [s for s in states if s['setting_id'] == ps['setting_id'] and s['seed_index'] == ps['seed_index']
          and s['checkpoint'] == ps['checkpoint']][0]
    t0 = time.perf_counter()
    op, val, pv, bundle, original, ids = load_state(st)
    old = read_json(st['next_v2_result'])
    m = DLN(weights_of(op), op.inputs, op.targets)
    dense = dense_reference(op)
    groups = op.layout.group_indices('coarse')
    line = original['config']['line_search']
    srow = {'state_id': st['state_id'], 'setting_id': st['setting_id'], 'role': ps['role'], 'conditions': []}
    for c in old['conditions']:
        lam = c['damping_absolute']
        g = op.gradient()
        Q = lambda v: op.matvec(v, lam)
        # ---- Replay A: NEXT v2 code path ----
        x, rr = cg(Q, -g, rtol=1e-8, max_iter=2000)
        b, br = block_cg(op, g, lam, rtol=1e-8, max_iter=2000)
        qb = Q(b)
        gp, bqb = float(g @ b), float(b @ qb)
        bl = loss_trials(op, val, (-gp / bqb) * b, line)
        fl = loss_trials(op, val, x, line)
        d8, c8 = cg(Q, -g, rtol=1e-8, max_iter=8)
        a8 = -float(g @ d8) / float(d8 @ c8['Qx'])
        l8 = loss_trials(op, val, a8 * d8, line)
        old8 = [r for r in c['comparators'] if r['name'] == 'cg_8'][0]['line_search']
        ra = {}
        for name, new, rec in (('Block', bl, c['block_ray_loss']), ('Full', fl, c['full_loss']), ('CG8', l8, old8)):
            dl = max(abs(p['loss'] - q['loss']) for p, q in zip(new['trials'], rec['trials']))
            ok = (new['selected_alpha'] == rec['selected_alpha'] and dl <= A['trial_loss_abs_tol']
                  and abs(new['train_gain'] - rec['train_gain']) <= A['train_gain_abs_tol']
                  and abs(new['validation_gain'] - rec['validation_gain']) <= A['validation_gain_abs_tol'])
            ra[name] = {'selected_alpha': new['selected_alpha'], 'recorded_alpha': rec['selected_alpha'],
                        'max_trial_loss_diff': dl, 'train_gain': new['train_gain'], 'recorded_train_gain': rec['train_gain'],
                        'validation_gain': new['validation_gain'], 'recorded_validation_gain': rec['validation_gain'],
                        'pass': ok}
            all_ok &= ok
        # ---- Replay B: v3 code path ----
        dirs, qrec, _ = compute_directions(op, m, lam, groups, dense['G'], dense['gradient'])
        pools = {'T32': (op.inputs, op.targets), 'V32': (val.inputs, val.targets)}
        rb = {'qualification': qrec['status'], 'delta_v3': qrec['delta'], 'delta_next_v2': c['delta']}
        okd = abs(qrec['delta'] - c['delta']) <= B['delta_abs_tol'] and qrec['status'] == 'QUALIFIED'
        rb['delta_pass'] = okd
        all_ok &= okd
        for name, rec in (('Block', c['block_ray_loss']), ('Full', c['full_loss']), ('CG8', old8)):
            ev = evaluate_direction(m.W, m.split(dirs[name]), pools, {}, OLD_GRID)
            a = select_alpha(ev['T32']['loss_naive'], OLD_GRID, OLD_GRID)
            i = OLD_GRID.index(a)
            tg, vg = -ev['T32']['dL'][i], -ev['V32']['dL'][i]
            tolg = lambda ref: B['gain_rel_tol'] * max(abs(ref), B['gain_abs_floor']) + B['gain_abs_floor']
            ok = (a == rec['selected_alpha'] and abs(tg - rec['train_gain']) <= tolg(rec['train_gain'])
                  and abs(vg - rec['validation_gain']) <= tolg(rec['validation_gain']))
            rb[name] = {'selected_alpha': a, 'recorded_alpha': rec['selected_alpha'], 'train_gain': tg,
                        'recorded_train_gain': rec['train_gain'], 'validation_gain': vg,
                        'recorded_validation_gain': rec['validation_gain'], 'pass': ok}
            all_ok &= ok
        srow['conditions'].append({'gamma': c['gamma'], 'lambda': lam, 'replay_A': ra, 'replay_B': rb, 'qualification': qrec})
    srow['wall_seconds'] = time.perf_counter() - t0
    report['states'].append(srow)
report['gate2_status'] = 'PASS' if all_ok else 'FAIL'
write_json(OUT / 'PILOT_REPRODUCTION.json', report)
print(json.dumps({'gate2': report['gate2_status'], 'states': [(s['setting_id'], [(c['gamma'], {k: c['replay_A'][k]['pass'] for k in c['replay_A']}, {k: c['replay_B'][k]['pass'] for k in ('Block', 'Full', 'CG8')}, c['replay_B']['delta_pass']) for c in s['conditions']]) for s in report['states']]}, indent=1))
