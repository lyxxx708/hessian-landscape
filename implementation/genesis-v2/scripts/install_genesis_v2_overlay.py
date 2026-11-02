"""Safe additive overlay onto a separately checked-out repository.

Default is dry-run. Production copies target E: only and never overwrites a
conflicting file, historical README/AGENTS, or existing pyproject. No Git mutation.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path,PureWindowsPath
import shutil

ROOT_FILES={'pyproject.toml','README_GENESIS_V2.md','CODEX_EXECUTE_V2.md','.github/workflows/genesis-v2-cpu.yml'}
PREFIXES=('genesis_gpu','tests_v2','configs','scripts','docs','validation')
SKIP={'__pycache__','.pytest_cache','.git','build','dist','.venv'}


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def install(source,target,*,apply=False,portable_test=False):
    source=Path(source).resolve();target=Path(target).resolve()
    if not portable_test:
        if os.name!='nt' or PureWindowsPath(str(target)).drive.upper()!='E:':
            raise ValueError('Production overlay must target E: on Windows. No C: fallback.')
    if source==target:raise ValueError('Source package and target repository must differ')
    files=[];identical=0
    for path in sorted(source.rglob('*')):
        rel=path.relative_to(source)
        if any(p in SKIP or p.endswith('.egg-info') for p in rel.parts):continue
        if path.is_symlink():raise ValueError('Refuse symbolic-link source: '+str(rel))
        if not path.is_file():continue
        if path.suffix in ('.pyc','.sqlite','.sqlite3','.pt','.pth','.npz','.safetensors'):continue
        if rel.parts[0] not in PREFIXES and rel.as_posix() not in ROOT_FILES:continue
        dest=target/rel
        resolved=dest.resolve()
        if not resolved.is_relative_to(target):raise ValueError('Target path escapes through symlink/junction: '+str(rel))
        if dest.exists():
            if not dest.is_file() or digest(path)!=digest(dest):
                raise FileExistsError('Conflicting existing file; no files replaced: '+str(dest))
            identical+=1
        else:files.append((path,dest,rel))
    # Validate the entire overlay BEFORE any write. Existing policy/docs are untouched.
    copied=0
    if apply:
        for src,dest,rel in files:
            dest.parent.mkdir(parents=True,exist_ok=True)
            # Exclusive create avoids racing another writer. Already-created new files
            # remain as exact additive copies if interrupted; an identical retry is safe.
            with dest.open('xb') as out,src.open('rb') as inp:shutil.copyfileobj(inp,out)
            if digest(src)!=digest(dest):raise IOError('Copy verification failed: '+str(rel))
            copied+=1
        ignore=target/'.gitignore'
        if ignore.is_symlink() or not ignore.resolve().is_relative_to(target):raise ValueError('Unsafe gitignore path')
        existing=ignore.read_text(encoding='utf-8') if ignore.exists() else ''
        additions=[p for p in ['local_artifacts/','build/','dist/','*.egg-info/','__pycache__/','.pytest_cache/','*.sqlite','*.safetensors'] if p not in existing.splitlines()]
        if additions:
            with ignore.open('a',encoding='utf-8') as out:out.write('\n# GENESIS v2 generated artifacts\n'+'\n'.join(additions)+'\n')
    return {'target':str(target),'dry_run':not apply,'new_files':len(files),'copied':copied,'identical':identical,
            'historical_files_replaced':0,'git_commands_executed':0}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,default=Path(__file__).resolve().parents[1]);p.add_argument('--target',type=Path,required=True)
    p.add_argument('--apply',action='store_true');p.add_argument('--portable-test',action='store_true',help='Explicit non-production test only')
    a=p.parse_args();print(json.dumps(install(a.source,a.target,apply=a.apply,portable_test=a.portable_test),indent=2))


if __name__=='__main__':main()
