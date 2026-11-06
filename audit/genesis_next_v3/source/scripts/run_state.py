"""Run ONE state in a fresh process: python run_state.py <state_id> <out_dir> [--no-timing] [--allow-unfrozen]"""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from genesis_next_v3 import env
env.configure_torch()
from genesis_next_v3.env import read_json, write_json, sha256_file, v3_code_hashes
from genesis_next_v3.source import next_v2_states
from genesis_next_v3.assay import run_state

sid, out = sys.argv[1], Path(sys.argv[2])
timing = '--no-timing' not in sys.argv
lock_path = out / 'PROTOCOL_LOCK.json'
if lock_path.exists():
    lock = read_json(lock_path)
    now = v3_code_hashes()
    changed = [k for k, v in lock['code_sha256'].items() if now.get(k) != v]
    if changed:
        raise SystemExit(f'Code changed after freeze: {changed}')
    cfg = {'freeze_sha': lock['freeze_sha']}
elif '--allow-unfrozen' in sys.argv:
    cfg = {'freeze_sha': 'UNFROZEN_QUALIFICATION_ONLY'}
else:
    raise SystemExit('No PROTOCOL_LOCK.json: refusing to produce scientific results before freeze')
state = [s for s in next_v2_states()[0] if s['state_id'] == sid][0]
rec, alpha_rows, slope_rows = run_state(state, cfg, out, do_timing=timing)
rec['inputs'] = env.verify_inputs()
for d in ('results', 'alpha_grid', 'slopes'):
    (out / d).mkdir(parents=True, exist_ok=True)
with open(out / 'alpha_grid' / f'{sid}.jsonl', 'w', encoding='utf-8') as f:
    for r in alpha_rows:
        f.write(json.dumps(r, allow_nan=False) + '\n')
with open(out / 'slopes' / f'{sid}.jsonl', 'w', encoding='utf-8') as f:
    for r in slope_rows:
        f.write(json.dumps(r, allow_nan=False) + '\n')
write_json(out / 'results' / f'{sid}.json', rec)
print(json.dumps({'state_id': sid, 'status': rec['status'], 'wall_s': round(rec['wall_s'], 1),
                  'conditions': [c.get('status') for c in rec['conditions']], 'failures': rec['failures']}))
