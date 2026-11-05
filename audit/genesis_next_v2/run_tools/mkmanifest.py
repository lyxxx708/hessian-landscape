import json,hashlib
from pathlib import Path
W=Path(r'E:\GENESIS\worktrees\genesis-next-v2')
files=[p for p in sorted(W.rglob('*')) if p.is_file() and '__pycache__' not in p.parts and p.name!='PACKAGE_MANIFEST.json']
m={'schema':1,'package':'GENESIS_NEXT_v2','files':[{'path':p.relative_to(W).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in files]}
(W/'PACKAGE_MANIFEST.json').write_text(json.dumps(m,indent=2))
print(len(files))
