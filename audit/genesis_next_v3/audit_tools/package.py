"""Assemble this audit package from the local run directories (byte-identical copies) and write its manifest.
python package.py <package_dir>. Copies; never edits a source file. Excludes checkpoints, datasets and arrays."""
import csv
import hashlib
import shutil
import sys
from pathlib import Path

pkg = Path(sys.argv[1])
SRC = Path(r'E:\GENESIS\worktrees\genesis-next-v3')
V3 = Path(r'E:\GENESIS\runs\genesis_next_v3')
A1 = Path(r'E:\GENESIS\runs\genesis_next_v3_pop_oracle')
SKIP = ('__pycache__', '*.pyc', '*.pt', '*.pth', '*.safetensors', '*.npy', '*.npz', '*.pkl')


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for c in iter(lambda: f.read(1 << 20), b''):
            h.update(c)
    return h.hexdigest()


for name, src in (('source', SRC), ('run_v3', V3), ('run_A1_population_oracle', A1)):
    dst = pkg / name
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns(*SKIP))
# byte-identity check against the local originals
bad = []
for name, src in (('source', SRC), ('run_v3', V3), ('run_A1_population_oracle', A1)):
    for p in (pkg / name).rglob('*'):
        if p.is_file() and sha(p) != sha(src / p.relative_to(pkg / name)):
            bad.append(str(p))
if bad:
    raise SystemExit(f'copy mismatch: {bad[:5]}')
out = pkg / 'FILE_MANIFEST_SHA256.csv'
rows = [(str(p.relative_to(pkg)).replace('\\', '/'), p.stat().st_size, sha(p)) for p in sorted(pkg.rglob('*'))
        if p.is_file() and p != out]
with open(out, 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['path', 'bytes', 'sha256'])
    w.writerows(rows)
print(len(rows), 'files', sum(r[1] for r in rows), 'bytes')
