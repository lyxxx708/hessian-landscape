"""Freeze addendum A1: python oracle/freeze_oracle.py <oracle_run_dir>. Refuses to overwrite an existing lock."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'oracle'))
from genesis_next_v3.env import write_json, sha256_file, object_sha, v3_code_hashes, read_json
from run_oracle_state import oracle_code_hashes, V3_RUN, REPLAY_NORM_RTOL, RISK_PATH_RTOL, POP_GRADIENT_RTOL, ROOT_RTOL
import pop_oracle as po

out = Path(sys.argv[1])
lock = out / 'ORACLE_LOCK.json'
if lock.exists():
    raise SystemExit('ORACLE_LOCK.json exists; refusing to overwrite')
v3lock = read_json(V3_RUN / 'PROTOCOL_LOCK.json')
now = v3_code_hashes()
if any(now.get(k) != v for k, v in v3lock['code_sha256'].items()):
    raise SystemExit('v3 code differs from its own frozen lock')
body = {'addendum': 'A1_ANALYTIC_POPULATION_STEP_ORACLE', 'evidence_class': 'POSTHOC_S1_EXPLORATORY_NOT_CONFIRMATION',
        'v3_freeze_sha': v3lock['freeze_sha'], 'v3_protocol_lock_sha256': sha256_file(V3_RUN / 'PROTOCOL_LOCK.json'),
        'v3_manifest_sha256': sha256_file(V3_RUN / 'FILE_MANIFEST_SHA256.csv'),
        'v3_code_sha256': now, 'oracle_code_sha256': oracle_code_hashes(),
        'tests_log_sha256': sha256_file(out / 'qualification' / 'TESTS.log'),
        'tolerances': {'replay_norm_rtol': REPLAY_NORM_RTOL, 'risk_path_rtol': RISK_PATH_RTOL,
                       'pop_gradient_rtol': POP_GRADIENT_RTOL, 'brent_location_rtol': ROOT_RTOL},
        'search': {'alpha_hi': po.ALPHA_HI, 'scan_points': po.SCAN_POINTS, 'stored_curve_points': len(po.CURVE_ALPHAS)},
        'states': [s['state_id'] for s in read_json(V3_RUN / 'RUN_PLAN.json')['states']]}
body['freeze_sha'] = object_sha(body)
write_json(lock, body)
print(body['freeze_sha'])
