"""Exp B timing: 1 warm-up + 7 randomized paired repeats per state, 2 threads, fresh process per state.

Every task is an *online* computation from the common frozen checkpoint and T32 inputs. Method-exclusive work
(layer-input/downstream caches, Kronecker factor formation, eigensolves, GGNv, block solves) is inside the task.
Common work (gradient, base loss) is timed separately and added equally in end-to-end accounting.
Each timed sample repeats a task n times (n calibrated in the warm-up so a sample lasts >= TARGET_SAMPLE_S);
the reported cost is per call. CV over the 7 repeats > 10% -> TIMING_INCONCLUSIVE.
"""
from __future__ import annotations
import os
import random
import statistics
import time
import psutil
import torch
from .dln_kron import DLN, cg_lean

REPEATS, WARMUPS = 7, 1
TARGET_SAMPLE_S = 0.1
MAX_INNER = 2000
CV_LIMIT = 0.10
CG_KS = [1, 2, 4, 8, 16, 32, 64]
CG_RTOLS = [1e-1, 1e-2, 1e-3]   # practical non-oracle stop rules (relative recurrence residual), cap 2000
LINE_ALPHAS = [0.01, 0.03, 0.1, 0.3, 1.0, 3.0]  # v2 grid minus alpha=0 (base loss is common)


def contention_sample(own_pid=None):
    own_pid = own_pid or os.getpid()
    total = psutil.cpu_percent(interval=None)
    others = []
    for p in psutil.process_iter(['pid', 'name', 'cpu_percent']):
        try:
            if p.info['pid'] not in (0, own_pid) and (p.info['cpu_percent'] or 0) > 5:
                others.append((p.info['name'], round(p.info['cpu_percent'], 1)))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return {'system_cpu_percent': total, 'busy_other_processes': sorted(others, key=lambda x: -x[1])[:8]}


def build_tasks(op, W, X, Y, g, lams):
    """Return dict name -> (callable, metadata). Callables recompute everything method-exclusive."""
    tasks = {}

    def block_direct(lam_list):
        def run():
            m = DLN(W, X, Y)
            m.build_cache()
            m.build_factors()
            return [m.block_direct(g, l) for l in lam_list]
        return run

    def block_localcg(lam_list):
        def run():
            m = DLN(W, X, Y)
            m.build_cache()
            return [m.block_local_cg(g, l, rtol=1e-12, max_iter=5000)[0] for l in lam_list]
        return run

    def cg_explicit(lam_list, k=None, rtol=0.0):
        def run():
            m = DLN(W, X, Y)
            m.build_cache()
            out = []
            for l in lam_list:
                Q = lambda v: m.ggn_vec(v) + l * v
                out.append(cg_lean(Q, -g, k if k is not None else 2000, rtol=rtol)[0])
            return out
        return run

    def cg_ad(lam, k):
        def run():
            return [cg_lean(lambda v: op.matvec(v, lam), -g, k)[0]]
        return run

    def old_block(lam):
        from genesis_next.solvers import block_cg
        def run():
            return [block_cg(op, g, lam, rtol=1e-8, max_iter=2000)[0]]
        return run

    for gi, lam in enumerate(lams):
        tag = f'g{gi}'
        tasks[f'cold:{tag}:block_kron_direct'] = (block_direct([lam]), {'gamma_index': gi, 'mode': 'cold', 'method': 'block_kron_direct'})
        tasks[f'cold:{tag}:block_kron_localcg'] = (block_localcg([lam]), {'gamma_index': gi, 'mode': 'cold', 'method': 'block_kron_localcg'})
        tasks[f'cold:{tag}:old_block_cg'] = (old_block(lam), {'gamma_index': gi, 'mode': 'cold', 'method': 'old_block_cg'})
        for k in CG_KS:
            tasks[f'cold:{tag}:cg{k}'] = (cg_explicit([lam], k=k), {'gamma_index': gi, 'mode': 'cold', 'method': f'cg{k}', 'k': k})
            tasks[f'cold:{tag}:cg{k}_ad'] = (cg_ad(lam, k), {'gamma_index': gi, 'mode': 'cold', 'method': f'cg{k}_ad', 'k': k})
        for r in CG_RTOLS:
            tasks[f'cold:{tag}:cg_rtol{r:g}'] = (cg_explicit([lam], rtol=r), {'gamma_index': gi, 'mode': 'cold', 'method': f'cg_rtol{r:g}', 'rtol': r})
    tasks['warm:block_kron_direct'] = (block_direct(lams), {'mode': 'warm', 'method': 'block_kron_direct'})
    tasks['warm:block_kron_localcg'] = (block_localcg(lams), {'mode': 'warm', 'method': 'block_kron_localcg'})
    for k in CG_KS:
        tasks[f'warm:cg{k}'] = (cg_explicit(lams, k=k), {'mode': 'warm', 'method': f'cg{k}', 'k': k})
    for r in CG_RTOLS:
        tasks[f'warm:cg_rtol{r:g}'] = (cg_explicit(lams, rtol=r), {'mode': 'warm', 'method': f'cg_rtol{r:g}', 'rtol': r})
    # ---- separately timed shared components ----
    mref = DLN(W, X, Y)
    mref.build_cache()
    v = torch.ones_like(g) / g.numel() ** 0.5
    tasks['common:gradient_v2_operator'] = (lambda: op.gradient(), {'mode': 'common', 'method': 'gradient_v2_operator'})
    tasks['common:gradient_dln'] = (lambda: DLN(W, X, Y).gradient(), {'mode': 'common', 'method': 'gradient_dln'})
    tasks['common:base_loss'] = (lambda: mref.loss_at(), {'mode': 'common', 'method': 'base_loss'})
    th = mref.theta()
    tasks['common:line_search_T32'] = (lambda: min(mref.loss_at(th + a * v) for a in LINE_ALPHAS),
                                       {'mode': 'common', 'method': 'line_search_T32', 'evaluations': len(LINE_ALPHAS)})
    tasks['common:qd_explicit_cached'] = (lambda: float(v @ (mref.ggn_vec(v) + lams[0] * v)), {'mode': 'common', 'method': 'qd_explicit_cached'})
    tasks['common:qd_v2_operator'] = (lambda: float(v @ op.matvec(v, lams[0])), {'mode': 'common', 'method': 'qd_v2_operator'})
    tasks['common:dln_cache_build'] = (lambda: DLN(W, X, Y).build_cache(), {'mode': 'common', 'method': 'dln_cache_build'})
    return tasks


def time_tasks(tasks, seed):
    rng = random.Random(seed)
    names = list(tasks)
    inner = {}
    proc = psutil.Process()
    psutil.cpu_percent(interval=None)
    for n in names:  # warm-up and calibration
        fn = tasks[n][0]
        t = time.perf_counter()
        fn()
        dt = time.perf_counter() - t
        inner[n] = max(1, min(MAX_INNER, int(TARGET_SAMPLE_S / max(dt, 1e-7)) + 1))
    samples = {n: [] for n in names}
    cpu = {n: [] for n in names}
    contention = []
    for r in range(REPEATS):
        order = names[:]
        rng.shuffle(order)
        contention.append({'repeat': r, 'before': contention_sample()})
        for n in order:
            fn = tasks[n][0]
            k = inner[n]
            c0 = time.process_time()
            t0 = time.perf_counter()
            for _ in range(k):
                fn()
            samples[n].append((time.perf_counter() - t0) / k)
            cpu[n].append((time.process_time() - c0) / k)
        contention[-1]['after'] = contention_sample()
    out = {}
    for n in names:
        s = samples[n]
        mean = statistics.fmean(s)
        cv = statistics.pstdev(s) / mean if mean > 0 else float('inf')
        out[n] = {**tasks[n][1], 'inner_calls': inner[n], 'wall_samples_s': s, 'wall_median_s': statistics.median(s),
                  'wall_mean_s': mean, 'cv': cv, 'cpu_median_s': statistics.median(cpu[n]),
                  'timing_status': 'OK' if cv <= CV_LIMIT else 'TIMING_INCONCLUSIVE'}
    mem = proc.memory_info()
    meta = {'repeats': REPEATS, 'warmups': WARMUPS, 'torch_threads': torch.get_num_threads(),
            'cpu_affinity': proc.cpu_affinity() if hasattr(proc, 'cpu_affinity') else None,
            'peak_working_set_bytes': getattr(mem, 'peak_wset', None), 'rss_bytes': mem.rss,
            'contention': contention, 'order_seed': seed}
    return out, meta
