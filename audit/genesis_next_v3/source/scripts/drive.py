"""Sequential driver: one fresh process per planned state; preserves every failure/timeout; never re-runs a committed state.
python drive.py <run_dir> [--limit N]"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from genesis_next_v3.env import read_json, write_json, THREAD_ENV

out = Path(sys.argv[1])
limit = int(sys.argv[sys.argv.index('--limit') + 1]) if '--limit' in sys.argv else None
lock = read_json(out / 'PROTOCOL_LOCK.json')
plan = read_json(out / 'RUN_PLAN.json')
timeout = lock['config']['state_timeout_s']
log = out / 'logs'
log.mkdir(exist_ok=True)
ledger_path = out / 'EXECUTION_LEDGER.jsonl'
env = {**os.environ, **THREAD_ENV, 'PYTHONUTF8': '1'}
done = 0
for st in plan['states']:
    sid = st['state_id']
    if (out / 'results' / f'{sid}.json').exists():
        continue
    if limit is not None and done >= limit:
        break
    t0 = time.time()
    cmd = [sys.executable, '-B', '-W', 'ignore', str(Path(__file__).with_name('run_state.py')), sid, str(out)]
    with open(log / f'{sid}.log', 'w', encoding='utf-8') as lf:
        try:
            p = subprocess.run(cmd, stdout=lf, stderr=subprocess.STDOUT, env=env, timeout=timeout)
            status = 'EXIT_0' if p.returncode == 0 else f'EXIT_{p.returncode}'
        except subprocess.TimeoutExpired:
            status = 'TIMEOUT_INCONCLUSIVE'
    entry = {'state_id': sid, 'setting_id': st['setting_id'], 'status': status, 'wall_s': time.time() - t0,
             'finished_at': time.strftime('%Y-%m-%dT%H:%M:%S'), 'result_written': (out / 'results' / f'{sid}.json').exists()}
    with open(ledger_path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry) + '\n')
    print(json.dumps(entry), flush=True)
    done += 1
print('DRIVER_DONE', flush=True)
