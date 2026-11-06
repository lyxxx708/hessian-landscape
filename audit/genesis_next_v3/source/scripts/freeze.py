"""Gate 4: freeze the v3 protocol, analysis plan, code and run plan before any main measurement.
python freeze.py <run_dir>   (refuses to overwrite an existing lock)"""
import csv
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from genesis_next_v3 import env
env.configure_torch()
from genesis_next_v3.env import read_json, write_json, sha256_file, object_sha, v3_code_hashes, V3_ROOT
from genesis_next_v3.source import next_v2_states, parent_panel
from genesis_next_v3 import alpha_grid, costs, assay, directions, pools

out = Path(sys.argv[1])
if (out / 'PROTOCOL_LOCK.json').exists():
    raise SystemExit('PROTOCOL_LOCK.json exists; a frozen protocol is never overwritten')
pilot = read_json(out / 'qualification' / 'PILOT_REPRODUCTION.json')
if pilot['gate2_status'] != 'PASS':
    raise SystemExit('Gate 2 (pilot reproduction) did not pass')
tests_log = out / 'qualification' / 'TESTS.log'
if not tests_log.exists() or 'OK' not in tests_log.read_text(encoding='utf-8').splitlines()[-1]:
    raise SystemExit('Gate 3 reference tests log missing or not OK')
states, _ = next_v2_states()
panel = parent_panel()
ready = {s['state_id'] for s in states}
rows = []
for p in panel:
    status = 'PLANNED' if p['state_id'] in ready else 'SOURCE_NOT_READY'
    for gam in (0.001, 0.01, 0.1):
        rows.append({**p, 'gamma': gam, 'v3_status': status,
                     'v4_member': status == 'PLANNED' and p['setting_id'] in assay.V4_SETTINGS})
with open(out / 'STATE_CONDITION_INDEX.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
plan = {'study': 'GENESIS_NEXT_v3', 'states_parent': len(panel), 'conditions_parent': len(rows),
        'states_planned': len(states), 'conditions_planned': 3 * len(states),
        'seeds_planned': len({(s['setting_id'], s['seed']) for s in states}),
        'v4_states': sum(s['setting_id'] in assay.V4_SETTINGS for s in states),
        'order': 'sequential, sorted by state_id; one fresh process per state; state timeout 3600 s',
        'states': [{k: s[k] for k in ('state_id', 'setting_id', 'seed', 'seed_index', 'checkpoint', 'next_v2_result_sha256')} for s in sorted(states, key=lambda s: s['state_id'])]}
write_json(out / 'RUN_PLAN.json', plan)
config = {
    'alpha_grid': alpha_grid.ALPHA_GRID, 'train_selection_grid': alpha_grid.OLD_GRID, 'sign_safety_factor': alpha_grid.SAFETY,
    'direction_rtol': directions.DIRECTION_RTOL, 'FB_rel_tol': directions.FB_REL_TOL, 'FB_abs_tol': directions.FB_ABS_TOL,
    'operator_rtol': directions.OPERATOR_RTOL, 'operator_probe_seed': directions.OPERATOR_PROBE_SEED,
    'timing': {'repeats': costs.REPEATS, 'warmups': costs.WARMUPS, 'target_sample_s': costs.TARGET_SAMPLE_S,
               'cv_limit': costs.CV_LIMIT, 'cg_ks': costs.CG_KS, 'cg_rtols': costs.CG_RTOLS, 'threads': 2},
    'gain_matching_tolerance_Fstar': 1e-4, 'quality_target_Fstar': 0.99,
    'v4': {'settings': list(assay.V4_SETTINGS), 'cost_cap_s': assay.V4_COST_CAP_S, 'batch': 512},
    'pools': {'V8': [pools.V8_GROUPS, pools.V8_SIZE], 'E': [pools.E_GROUPS, pools.E_SIZE], 'T512': pools.T512,
              'namespaces': [pools.NS_T512, pools.NS_V8, pools.NS_E]},
    'bootstrap': {'replicates': 2000, 'seed': 20261106}, 'state_timeout_s': 3600}
lock = {'study': 'GENESIS_NEXT_v3', 'evidence_class': 'POSTHOC_S1_EXPLORATORY_NOT_CONFIRMATION',
        'design_sha256': {p.name: sha256_file(p) for p in sorted((V3_ROOT / 'docs' / 'design_input').iterdir())},
        'analysis_plan_sha256': sha256_file(V3_ROOT / 'docs' / 'ANALYSIS_PLAN.md'),
        'code_sha256': v3_code_hashes(), 'config': config, 'inputs': env.verify_inputs(),
        'run_plan_sha256': sha256_file(out / 'RUN_PLAN.json'),
        'state_condition_index_sha256': sha256_file(out / 'STATE_CONDITION_INDEX.csv'),
        'gates': {'gate2_pilot_reproduction': pilot['gate2_status'], 'pilot_sha256': sha256_file(out / 'qualification' / 'PILOT_REPRODUCTION.json'),
                  'gate3_tests_log_sha256': sha256_file(tests_log)},
        'safety': {'no_old_v2_writes': True, 'no_S2_reads': True, 'no_replacement_seeds': True,
                   'no_gpu_preemption': True, 'no_new_training': True, 'device': 'cpu', 'dtype': 'float64'}}
lock['freeze_sha'] = object_sha(lock)
write_json(out / 'PROTOCOL_LOCK.json', lock)
print(lock['freeze_sha'])
