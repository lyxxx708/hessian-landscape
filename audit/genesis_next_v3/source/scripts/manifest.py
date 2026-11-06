"""Write SHA-256 manifests and copy the public-safe evidence tables to E:\\GENESIS\\evidence\\genesis_next_v3.
python manifest.py <run_dir> <evidence_dir>. Private arrays (local pools, checkpoints) are never copied."""
import csv
import hashlib
import shutil
import sys
from pathlib import Path

run, ev = Path(sys.argv[1]), Path(sys.argv[2])
root = Path(__file__).resolve().parents[1]


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for c in iter(lambda: f.read(1 << 20), b''):
            h.update(c)
    return h.hexdigest()


TABLES = ['RUN_PLAN.json', 'PROTOCOL_LOCK.json', 'STATE_CONDITION_INDEX.csv', 'VALIDATION_ALPHA_GRID.jsonl',
          'DIRECTIONAL_SLOPE_AND_HVP.jsonl', 'VALIDATION_ATTRIBUTION.csv', 'BLOCK_REFERENCE_CHECKS.jsonl', 'BLOCK_CG_COST.csv',
          'BLOCK_CG_COMPARISON.csv', 'V4_INTERVENTION.csv', 'PAIRED_SEED_SUMMARY.csv', 'NUMERIC_QUALIFICATION.csv',
          'FAILURES.csv', 'ANALYSIS_SUMMARY.json', 'EXECUTION_LEDGER.jsonl', 'SCIENTIFIC_VERDICT.md', 'README_REPRODUCE.md']
ev.mkdir(parents=True, exist_ok=True)
for t in TABLES:
    if (run / t).exists():
        shutil.copy2(run / t, ev / t)
for sub in ('qualification',):
    for p in (run / sub).glob('*.json*'):
        (ev / sub).mkdir(exist_ok=True)
        shutil.copy2(p, ev / sub / p.name)
    if (run / sub / 'TESTS.log').exists():
        shutil.copy2(run / sub / 'TESTS.log', ev / sub / 'TESTS.log')
src = ev / 'source_snapshot'
if src.exists():
    shutil.rmtree(src)
for d in ('genesis_next_v3', 'scripts', 'tests', 'configs', 'docs'):
    shutil.copytree(root / d, src / d, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
for base, name in ((run, 'FILE_MANIFEST_SHA256.csv'), (ev, 'FILE_MANIFEST_SHA256.csv')):
    rows = [(str(p.relative_to(base)).replace('\\', '/'), p.stat().st_size, sha(p)) for p in sorted(base.rglob('*'))
            if p.is_file() and p.name != name]
    with open(base / name, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['path', 'bytes', 'sha256'])
        w.writerows(rows)
    print(base / name, len(rows))
