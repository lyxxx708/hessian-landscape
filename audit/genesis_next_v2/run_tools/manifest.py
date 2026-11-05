import csv,hashlib
from pathlib import Path
O=Path(r'E:\GENESIS\runs\genesis_next_v2')
rows=[]
for p in sorted(O.rglob('*')):
    if p.is_file() and p.name!='FILE_MANIFEST_SHA256.csv' and '__pycache__' not in p.parts:
        rows.append((p.relative_to(O).as_posix(),p.stat().st_size,hashlib.sha256(p.read_bytes()).hexdigest()))
with (O/'FILE_MANIFEST_SHA256.csv').open('w',newline='') as f:
    w=csv.writer(f);w.writerow(['path','bytes','sha256']);w.writerows(rows)
print(len(rows))
