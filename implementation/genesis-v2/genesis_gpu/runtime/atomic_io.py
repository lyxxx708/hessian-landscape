"""Same-volume atomic writes, strict JSON and content-addressed artifact checks."""
from __future__ import annotations
from pathlib import Path
import hashlib
import json
import os
import tempfile
from typing import Any


def canonical_json(obj: Any) -> bytes:
    return (json.dumps(obj, sort_keys=True, ensure_ascii=False, allow_nan=False, indent=2) + '\n').encode('utf-8')


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def atomic_bytes(path: Path, content: bytes) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(prefix='.' + path.name + '.', suffix='.tmp', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp, path)
    except BaseException:
        try:
            os.unlink(temp)
        except OSError:
            pass
        raise


def atomic_json(path: Path, obj: Any) -> None:
    atomic_bytes(path, canonical_json(obj))


def read_json(path: Path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def safe_relative(root: Path, target: Path) -> str:
    try:
        return Path(target).resolve().relative_to(Path(root).resolve()).as_posix()
    except ValueError as exc:
        raise ValueError('Artifact escapes root (including junction/symlink target)') from exc


def resolve_artifact(root: Path, relative: str) -> Path:
    from pathlib import PureWindowsPath
    if PureWindowsPath(relative).drive or Path(relative).is_absolute():
        raise ValueError('Artifact receipt must use a relative path')
    p = Path(root) / relative
    safe_relative(root, p)
    return p


def file_receipt(path: Path, root: Path) -> dict:
    return {'path': safe_relative(root, path), 'sha256': sha256_file(path), 'bytes': Path(path).stat().st_size}


def verify_receipt(root: Path, receipt: dict) -> bool:
    p = resolve_artifact(root, receipt['path'])
    return p.is_file() and p.stat().st_size == receipt['bytes'] and sha256_file(p) == receipt['sha256']


def append_jsonl(path: Path, value: Any):
    """Only call from the single worktree writer; final newline marks a committed record."""
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(value, sort_keys=True, allow_nan=False, ensure_ascii=False) + '\n'
    with path.open('a', encoding='utf-8', newline='\n') as f:
        f.write(line)
        f.flush()
        os.fsync(f.fileno())


def source_manifest(root: Path) -> dict:
    root = Path(root)
    paths = sorted(root.glob('genesis_gpu/**/*.py')) + sorted(root.glob('configs/*.yaml')) + sorted(root.glob('scripts/genesis_*.ps1'))
    paths += [root/'pyproject.toml']
    files = [file_receipt(p, root) for p in paths if p.is_file()]
    digest = hashlib.sha256(canonical_json(files)).hexdigest()
    return {'sha256': digest, 'files': files}
