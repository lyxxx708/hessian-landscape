"""Sequential driver for addendum A1, fresh process per state: python oracle/drive_oracle.py <oracle_run_dir>"""
import json
import subprocess
import sys
import time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
TIMEOUT_S = 1800

out = Path(sys.argv[1])
lock = json.load(open(out / 'ORACLE_LOCK.json', encoding='utf-8'))
(out / 'logs').mkdir(exist_ok=True)
for sid in lock['states']:
    if (out / 'results' / f'{sid}.json').exists():
        continue
    t = time.time()
    with open(out / 'logs' / f'{sid}.log', 'w', encoding='utf-8') as log:
        try:
            p = subprocess.run([sys.executable, '-B', str(ROOT / 'oracle' / 'run_oracle_state.py'), sid, str(out)],
                               stdout=log, stderr=subprocess.STDOUT, timeout=TIMEOUT_S, cwd=str(ROOT))
            status = f'EXIT_{p.returncode}'
        except subprocess.TimeoutExpired:
            status = 'TIMEOUT'
    entry = {'state_id': sid, 'status': status, 'wall_s': time.time() - t,
             'finished_at': time.strftime('%Y-%m-%dT%H:%M:%S'), 'result_written': (out / 'results' / f'{sid}.json').exists()}
    with open(out / 'EXECUTION_LEDGER.jsonl', 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry) + '\n')
    print(json.dumps(entry), flush=True)
print('DRIVER_DONE', flush=True)
