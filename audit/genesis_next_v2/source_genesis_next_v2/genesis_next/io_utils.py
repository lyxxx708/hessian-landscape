from __future__ import annotations
import csv
import hashlib
import json
import os
from pathlib import Path
from datetime import datetime, timezone

def utc_now(): return datetime.now(timezone.utc).isoformat()

def digest(path: Path) -> str:
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024), b''): h.update(block)
    return h.hexdigest()

def object_digest(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(',',':'),allow_nan=False).encode()).hexdigest()

def read_json(path):
    with Path(path).open(encoding='utf-8-sig') as f:return json.load(f)

def jsonl(path):
    with Path(path).open(encoding='utf-8-sig') as f:
        for i,line in enumerate(f,1):
            if line.strip():
                try:yield json.loads(line)
                except Exception as e: raise ValueError(f'{path}: invalid JSON at line {i}') from e

def csv_rows(path):
    with Path(path).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def write_json(path, obj):
    path=Path(path); encoded=json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False).encode('utf-8')+b'\n'
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name(path.name+'.tmp')
    with tmp.open('wb') as f:f.write(encoded);f.flush();os.fsync(f.fileno())
    os.replace(tmp,path)

def write_csv(path,rows):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    rows=list(rows)
    fields=list(dict.fromkeys(k for r in rows for k in r))
    with path.open('w',encoding='utf-8',newline='') as f:
        if fields:
            writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(rows)

def safe_join(root: Path, relative: str) -> Path:
    root=Path(root).resolve()
    # Block both Windows and POSIX absolute/traversal forms on either platform.
    rel=relative.replace('\\','/')
    if rel.startswith('/') or ':' in rel or '..' in rel.split('/'):
        raise ValueError(f'Unsafe relative path: {relative}')
    p=(root/rel).resolve()
    if p==root or root not in p.parents:raise ValueError(f'Path escapes root: {relative}')
    return p

def assert_separate(output, inputs):
    out=Path(output).resolve()
    for root in inputs:
        if root is None:continue
        src=Path(root).resolve()
        if out==src or src in out.parents or out in src.parents:
            raise ValueError(f'Output and protected input overlap: {out} / {src}')

def verify_bundle(bundle, full=True):
    bundle=Path(bundle).resolve();man=bundle/'09_MANIFEST/FILE_MANIFEST_SHA256.csv'
    rows=csv_rows(man);bad=[];missing_local=[];checked=0
    for r in rows:
        p=safe_join(bundle,r['path'])
        if not p.exists():
            if r['on_github']=='yes':bad.append({'path':r['path'],'reason':'MISSING_PUBLIC'})
            else:missing_local.append(r['path'])
            continue
        if p.stat().st_size!=int(r['bytes']):bad.append({'path':r['path'],'reason':'SIZE'})
        elif full and digest(p)!=r['sha256']:bad.append({'path':r['path'],'reason':'SHA256'})
        checked+=1
    return {'status':'PASS' if not bad else 'FAIL','manifest_sha256':digest(man),
            'checked_files':checked,'bad':bad,'not_public_and_absent':missing_local}

def code_digest(package: Path):
    paths=sorted((package/'genesis_next').glob('*.py'))
    return {'files':[{'path':str(p.relative_to(package)).replace('\\','/'),'sha256':digest(p)} for p in paths]}
