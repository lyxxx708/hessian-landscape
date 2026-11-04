"""E-drive fail-closed production I/O; explicitly separated portable test mode."""
from pathlib import Path, PureWindowsPath
import os
import shutil


class StorageBlocked(RuntimeError):
    pass


def check_windows_bulk_path(path):
    p = PureWindowsPath(str(path))
    if not p.is_absolute() or p.drive.upper() != 'E:' or '..' in p.parts:
        raise StorageBlocked(f'Bulk path must be absolute on E:, no fallback: {path}')
    return p


def ensure_space(path: Path, reserve_bytes: int, projected_bytes: int = 0):
    probe = Path(path)
    while not probe.exists() and probe.parent != probe:
        probe = probe.parent
    free = shutil.disk_usage(probe).free
    required = max(reserve_bytes, int(projected_bytes * .2)) + projected_bytes
    if free < required:
        raise StorageBlocked(f'Need {required} free bytes, found {free}; no C: fallback')
    return free


def prepare_storage(root: Path, *, production: bool, min_free_bytes: int = 30 * 1024**3):
    root = Path(root)
    if production:
        check_windows_bulk_path(root)
        if os.name != 'nt':
            raise StorageBlocked('Production config is Windows E:-first; use smoke profile only for portable tests')
        if not Path('E:/').is_dir():
            raise StorageBlocked('E: missing')
        check_windows_bulk_path(root.resolve())
    ensure_space(root, min_free_bytes)
    root.mkdir(parents=True, exist_ok=True)
    result = {'run': root}
    for name in ['config-locks', 'datasets', 'checkpoints', 'measurements', 'probes', 'tables', 'logs', 'audit', 'reports', 'figures', 'manifests', 'tmp']:
        p = root/name
        if production:
            check_windows_bulk_path(p.resolve())
        p.mkdir(parents=True, exist_ok=True)
        result[name] = p
    return result


def configure_process_environment(storage_root: Path, production: bool):
    if production:
        check_windows_bulk_path(storage_root)
        if os.name != 'nt' or not Path('E:/').exists():
            raise StorageBlocked('E: unavailable; cannot install or write caches')
    cache = Path(storage_root)/'cache'
    mapping = {
        'TEMP': Path(storage_root)/'tmp', 'TMP': Path(storage_root)/'tmp', 'TMPDIR': Path(storage_root)/'tmp',
        'PIP_CACHE_DIR': cache/'pip', 'UV_CACHE_DIR': cache/'uv', 'HF_HOME': cache/'hf',
        'HF_HUB_CACHE': cache/'hf'/'hub', 'HF_DATASETS_CACHE': cache/'hf'/'datasets',
        'TORCH_HOME': cache/'torch', 'TORCH_EXTENSIONS_DIR': cache/'torch_extensions',
        'TRITON_CACHE_DIR': cache/'triton', 'NUMBA_CACHE_DIR': cache/'numba',
        'CUDA_CACHE_PATH': cache/'cuda', 'MPLCONFIGDIR': cache/'matplotlib',
        'PYTHONPYCACHEPREFIX': cache/'pycache', 'XDG_CACHE_HOME': cache/'xdg'
    }
    for name, p in mapping.items():
        if production:
            check_windows_bulk_path(p.resolve())
        p.mkdir(parents=True, exist_ok=True)
        os.environ[name] = str(p)
    return {k: str(v) for k, v in mapping.items()}
