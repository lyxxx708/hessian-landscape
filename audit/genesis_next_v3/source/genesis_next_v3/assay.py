"""Per-state v3 assay: Exp V (alpha-grid replay + slopes/curvatures), Exp B (quality + timing), V4 (T512 directions)."""
from __future__ import annotations
import math
import time
import traceback
import numpy as np
import torch
from .env import read_json, write_json, sha256_file, object_sha, V2_RUN
from .source import load_state, weights_of
from .pools import build_pools, lift
from .dln_kron import DLN, cg_lean, best_ray, quad_gain
from .directions import compute_directions, dense_reference, dense_from_dln, rel
from .alpha_grid import evaluate_direction, select_alpha, ALPHA_GRID, OLD_GRID, pool_gradient
from . import costs

V4_SETTINGS = ('dln_d4_w16_orthogonal_balanced_c1', 'dln_d8_w16_random_unbalanced_c100')
V4_COST_CAP_S = 900.0
V_DIRECTIONS = ('Full', 'Block', 'CG8')


def _pools_for_eval(pools, native, val):
    ev = {k: pools[k] for k in ('T32', 'T512', 'T4096', 'V1024', 'E8192', 'Test1024')}
    ev['V32_v2'] = (val.inputs, val.targets)
    nat = {k + '_native': v for k, v in native.items()}
    return ev, nat


def _quality(g, Qdense, d, line_losses_fn):
    """Quadratic quality of a direction under raw and best-ray policies (dense FP64 evaluation oracle, offline)."""
    Qd = Qdense(d)
    a, Fray = best_ray(g, d, Qd)
    Fraw = quad_gain(g, d, Qd)
    out = {'F_raw': Fraw, 'F_ray': Fray, 'best_ray_scale': a}
    for pol, vec in (('raw', d), ('ray', a * d)):
        losses = line_losses_fn(vec)
        alpha = select_alpha(losses, OLD_GRID, OLD_GRID)
        step = alpha * vec
        out[f'{pol}_T32_alpha'] = alpha
        out[f'{pol}_step_F'] = quad_gain(g, step, Qdense(step)) if alpha > 0 else 0.0
    return out


def run_state(state, cfg, out_dir, do_timing=True):
    t0 = time.perf_counter()
    rec = {'state_id': state['state_id'], 'setting_id': state['setting_id'], 'seed': state['seed'],
           'seed_index': state['seed_index'], 'checkpoint': state['checkpoint'], 'status': 'STARTED',
           'freeze_sha': cfg['freeze_sha'], 'conditions': [], 'failures': []}
    op, val, pv, bundle, original, ids = load_state(state)
    old = read_json(state['next_v2_result'])
    if sha256_file(state['next_v2_result']) != state['next_v2_result_sha256']:
        raise ValueError('NEXT v2 result changed')
    rec['provenance'] = {k: pv[k] for k in ('run_id', 'model_sha', 'data_sha', 'checkpoint_integrity_sha', 'checkpoint_step',
                                            'batch_seed', 'training_receipt_sha256', 'groups_sha', 'parameters')}
    rec['provenance'].update(v2_protocol_lock_sha256=sha256_file(V2_RUN / 'protocol-lock.json'),
                             recorded_spectral_scale=old['recorded_spectral_scale'], next_v2_result_sha256=state['next_v2_result_sha256'],
                             input_policy='V2_FP32_BATCH_LIFTED_TO_FP64', operator_identity=op.identity)
    W = weights_of(op)
    m = DLN(W, op.inputs, op.targets)
    pools, native, groups_idx, pool_identity, t512 = build_pools(state['run'], bundle, ids)
    rec['pool_identity'] = pool_identity
    evpools, natpools = _pools_for_eval(pools, native, val)
    egroups = {'V1024': groups_idx['V8x128'], 'E8192': groups_idx['E8x1024']}
    dense = dense_reference(op)
    G, gd = dense['G'].numpy(), dense['gradient']
    groups = op.layout.group_indices('coarse')
    lams = [c['damping_absolute'] for c in old['conditions']]
    gammas = [c['gamma'] for c in old['conditions']]
    for gam, lam, c in zip(gammas, lams, old['conditions']):
        if abs(lam - gam * max(old['recorded_spectral_scale'], original['config']['damping_floor'])) > 1e-12 * lam:
            raise ValueError('Absolute damping does not follow frozen spectral scale')
    alpha_rows, slope_rows = [], []
    T32dirs = {}
    for gam, lam, c in zip(gammas, lams, old['conditions']):
        cond = {'gamma': gam, 'lambda_absolute': lam, 'next_v2': {
            'delta': c['delta'], 'block_ray_loss': {k: c['block_ray_loss'][k] for k in ('selected_alpha', 'train_gain', 'validation_gain')},
            'full_loss': {k: c['full_loss'][k] for k in ('selected_alpha', 'train_gain', 'validation_gain')}}}
        try:
            dirs, q, g = compute_directions(op, m, lam, groups, dense['G'], gd, with_cg_v2=True)
            cond['qualification'] = q
            cond['status'] = q['status']
            T32dirs[gam] = dirs
            for name in V_DIRECTIONS:
                E = m.split(dirs[name])
                ev = evaluate_direction(W, E, evpools, egroups)
                ev.update(evaluate_direction(W, E, natpools, {}))
                d = dirs[name]
                dGd = float(d @ m.ggn_vec(d))
                sel = {}
                for pol, allowed in (('T32_oldgrid', OLD_GRID), ('T32_fullgrid', ALPHA_GRID), ('T512_oldgrid', OLD_GRID),
                                     ('T4096_oldgrid', OLD_GRID)):
                    src = pol.split('_')[0]
                    sel[pol] = select_alpha(ev[src]['loss_naive'], ALPHA_GRID, allowed)
                # validation-assisted (diagnostic): choose on V-half A (groups 0-3), report on V-half B / E / Test
                vA = [sum(gr['dL'][i] for gr in ev['V1024']['groups'][:4]) / 4 for i in range(len(ALPHA_GRID))]
                sel['VhalfA_oldgrid_DIAGNOSTIC'] = select_alpha(vA, ALPHA_GRID, OLD_GRID)
                sel['V1024_oracle_DIAGNOSTIC'] = select_alpha(ev['V1024']['dL'], ALPHA_GRID, ALPHA_GRID)
                sel['E8192_oracle_DIAGNOSTIC'] = select_alpha(ev['E8192']['dL'], ALPHA_GRID, ALPHA_GRID)
                alpha_rows.append({'state_id': state['state_id'], 'setting_id': state['setting_id'], 'seed': state['seed'],
                                   'checkpoint': state['checkpoint'], 'gamma': gam, 'lambda_absolute': lam,
                                   'direction': name, 'direction_batch': 'T32', 'condition_status': q['status'],
                                   'alpha_grid': ALPHA_GRID, 'selected_alpha': sel, 'pools': ev,
                                   'train_ggn_quadratic_T32': dGd, 'direction_norm': float(d.norm())})
                slope_rows.append({'state_id': state['state_id'], 'gamma': gam, 'direction': name, 'direction_batch': 'T32',
                                   **{p: {k: ev[p][k] for k in ('slope', 'slope_gradient_formula', 'slope_bound', 'curv_H', 'curv_GGN')}
                                      for p in ev}, 'train_ggn_quadratic_T32': dGd})
        except Exception as exc:
            cond['status'] = 'FAILED'
            cond['error'] = traceback.format_exc()
            rec['failures'].append({'stage': 'expV', 'gamma': gam, 'error': repr(exc)})
        rec['conditions'].append(cond)
    rec['expV_wall_s'] = time.perf_counter() - t0
    # ------------------------------ Exp B ------------------------------
    tb = time.perf_counter()
    g = op.gradient()
    try:
        tasks = costs.build_tasks(op, W, op.inputs, op.targets, g, lams)
        Qdense = lambda lam: (lambda v: torch.as_tensor((G + lam * np.eye(len(gd))) @ v.numpy()))
        line_fn = lambda vec: [m.loss_at(m.theta() + a * vec) for a in OLD_GRID]
        quality = {}
        for name, (fn, meta) in tasks.items():
            if meta['mode'] == 'common':
                continue
            outs = fn()
            lam_list = [lams[meta['gamma_index']]] if meta['mode'] == 'cold' else lams
            for li, (lam, d) in enumerate(zip(lam_list, outs)):
                gi = meta['gamma_index'] if meta['mode'] == 'cold' else li
                Fstar = rec['conditions'][gi]['qualification']['F_star']
                qd = _quality(gd, Qdense(lam), d, line_fn)
                qd.update({k + '_over_Fstar': qd[k] / Fstar for k in ('F_raw', 'F_ray', 'raw_step_F', 'ray_step_F')})
                ref_block = T32dirs[gammas[gi]]['Block_raw']
                if meta['method'].startswith('block') or meta['method'] == 'old_block_cg':
                    qd['vs_exact_block_direction'] = rel(d, ref_block)
                quality[f'{name}#{gi}'] = {**meta, 'gamma': gammas[gi], **qd}
        rec['expB_quality'] = quality
        if do_timing:
            timing, tmeta = costs.time_tasks(tasks, seed=int(object_sha(state['state_id'])[:8], 16))
            rec['expB_timing'] = timing
            rec['expB_timing_meta'] = tmeta
    except Exception as exc:
        rec['failures'].append({'stage': 'expB', 'error': repr(exc), 'trace': traceback.format_exc()})
    rec['expB_wall_s'] = time.perf_counter() - tb
    # ------------------------------ V4 ------------------------------
    if state['setting_id'] in V4_SETTINGS:
        tv = time.perf_counter()
        try:
            v4_alpha, v4 = run_v4(op, W, pools, groups_idx, evpools, natpools, egroups, groups, gammas, lams, T32dirs, state)
            alpha_rows.extend(v4_alpha)
            rec['V4'] = v4
        except Exception as exc:
            rec['V4'] = {'status': 'FAILED', 'error': repr(exc), 'trace': traceback.format_exc()}
            rec['failures'].append({'stage': 'V4', 'error': repr(exc)})
        rec['V4_wall_s'] = time.perf_counter() - tv
    rec['wall_s'] = time.perf_counter() - t0
    rec['status'] = 'EXECUTED' if not rec['failures'] else 'EXECUTED_WITH_FAILURES'
    return rec, alpha_rows, slope_rows


class Deadline(Exception):
    pass


def run_v4(op, W, pools, groups_idx, evpools, natpools, egroups, groups, gammas, lams, T32dirs, state):
    start = time.perf_counter()
    X5, Y5 = pools['T512']
    m5 = DLN(W, X5, Y5)
    from genesis_gpu.curvature.operators import FrozenOperator
    # v2 matrix-free AD operator on T512 (independent code path); one chunk = same mathematics as microbatch 4, fewer graphs
    op5 = FrozenOperator(op.model, X5, Y5, op.loss, microbatch=len(X5), dtype=torch.float64)
    g5 = op5.gradient()
    out = {'status': 'STARTED', 'cost_cap_s': V4_COST_CAP_S, 'conditions': []}
    out['gradient_dln_vs_v2'] = rel(m5.gradient(), g5)
    G5 = dense_from_dln(m5).numpy()
    gen = torch.Generator()
    gen.manual_seed(20261106)
    errs = []
    for _ in range(3):
        v = torch.randn(m5.n, generator=gen, dtype=torch.float64)
        a = op5.raw_ggn(v)
        errs.append({'dense_vs_v2_operator': rel(torch.as_tensor(G5 @ v.numpy()), a), 'dln_vs_v2_operator': rel(m5.ggn_vec(v), a)})
    out['operator_checks'] = errs
    # gradient variance on 8 disjoint T32-sized subsets of T512
    gE = torch.cat([x.reshape(-1) for x in pool_gradient(W, *pools['E8192'])])
    sub = []
    for lo, hi in groups_idx['T512_sub32']:
        sub.append(torch.cat([x.reshape(-1) for x in pool_gradient(W, X5[lo:hi], Y5[lo:hi])]))
    S = torch.stack(sub)
    gT32 = op.gradient()
    cos = lambda a, b: float(a @ b / (a.norm() * b.norm()))
    out['gradient_variance'] = {
        'subset_size': 32, 'subsets': len(sub), 'mean_norm': float(S.mean(0).norm()),
        'trace_cov_over_mean_norm2': float(S.var(0, unbiased=True).sum() / S.mean(0).norm() ** 2),
        'cos_subset_vs_E8192': [cos(s, gE) for s in sub], 'cos_T32_vs_E8192': cos(gT32, gE),
        'cos_T512_vs_E8192': cos(g5, gE), 'cos_T4096_vs_E8192': cos(torch.cat([x.reshape(-1) for x in pool_gradient(W, *pools['T4096'])]), gE),
        'note': '8 disjoint 32-example subsets of ONE training split; not independent training seeds'}
    m5.build_cache()
    m5.build_factors()
    rows = []
    for gam, lam in zip(gammas, lams):
        if time.perf_counter() - start > V4_COST_CAP_S:
            out['conditions'].append({'gamma': gam, 'status': 'RESOURCE_CENSORED'})
            continue
        c = {'gamma': gam, 'lambda_absolute': lam}
        Q5 = G5 + lam * np.eye(len(g5))
        full = torch.as_tensor(np.linalg.solve(Q5, -g5.numpy()))
        # Q0: matrix-free FP64 CG on the v2 AD operator, with the frozen cost cap
        deadline = start + V4_COST_CAP_S
        def Qmf(v):
            if time.perf_counter() > deadline:
                raise Deadline()
            return op5.matvec(v, lam)
        try:
            xmf, rmf = cg_lean(Qmf, -g5, 4000, rtol=1e-10)
            c['Q0_matrix_free_direction_error'] = rel(xmf, full)
            c['Q0_matvecs'] = rmf['matvecs']
        except Deadline:
            c['status'] = 'RESOURCE_CENSORED'
            out['conditions'].append(c)
            continue
        bK = m5.block_direct(g5, lam)
        bD = np.zeros(len(g5))
        for idx in groups:
            ii = idx.numpy()
            bD[ii] = -np.linalg.solve(Q5[np.ix_(ii, ii)], g5.numpy()[ii])
        c['block_kron_vs_dense'] = rel(bK, torch.as_tensor(bD))
        Qt = lambda v: torch.as_tensor(Q5 @ v.numpy())
        aB, FB = best_ray(g5, bK, Qt(bK))
        Fs = quad_gain(g5, full, Qt(full))
        x8, _ = cg_lean(lambda v: m5.ggn_vec(v) + lam * v, -g5, 8)
        a8, F8 = best_ray(g5, x8, Qt(x8))
        c.update(F_star_T512=Fs, F_block_T512=FB, delta_T512=1 - FB / Fs, block_ray_scale=aB, cg8_F_ratio=F8 / Fs,
                 full_T512_vs_full_T32_cos=cos(full, T32dirs[gam]['Full']) if gam in T32dirs else None,
                 block_T512_vs_block_T32_cos=cos(aB * bK, T32dirs[gam]['Block']) if gam in T32dirs else None)
        ok = (c['block_kron_vs_dense'] <= 1e-7 and c['Q0_matrix_free_direction_error'] <= 1e-6
              and max(max(e.values()) for e in errs) <= 1e-10 and out['gradient_dln_vs_v2'] <= 1e-10)
        c['status'] = 'QUALIFIED' if ok else 'NUMERIC_UNRESOLVED'
        for name, d in (('Full', full), ('Block', aB * bK), ('CG8', a8 * x8)):
            E = m5.split(d)
            ev = evaluate_direction(W, E, evpools, egroups)
            ev.update(evaluate_direction(W, E, natpools, {}))
            sel = {'T512_oldgrid': select_alpha(ev['T512']['loss_naive'], ALPHA_GRID, OLD_GRID),
                   'T32_oldgrid': select_alpha(ev['T32']['loss_naive'], ALPHA_GRID, OLD_GRID),
                   'T4096_oldgrid': select_alpha(ev['T4096']['loss_naive'], ALPHA_GRID, OLD_GRID)}
            rows.append({'state_id': state['state_id'], 'setting_id': state['setting_id'], 'seed': state['seed'],
                         'checkpoint': state['checkpoint'], 'gamma': gam, 'lambda_absolute': lam, 'direction': name,
                         'direction_batch': 'T512', 'condition_status': c['status'], 'alpha_grid': ALPHA_GRID,
                         'selected_alpha': sel, 'pools': ev, 'direction_norm': float(d.norm())})
        out['conditions'].append(c)
    out['wall_s'] = time.perf_counter() - start
    out['status'] = 'EXECUTED'
    return rows, out
