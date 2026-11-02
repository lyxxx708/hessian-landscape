"""Offline, owner-attested MNIST/CIFAR-10 import into GENESIS v2 on E:.

Read local source files only. Verify canonical torchvision MD5 plus new SHA256,
archive exact originals on E:, prepare the UNCHANGED 20261102 split, commit
safetensors atomically, and never interpret image readiness as text readiness.
No automatic network request, C: write, source removal or science claim.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import gzip
import hashlib
import os
import pickle
import shutil
import struct
import uuid

import numpy as np
import torch

from genesis_gpu.curvature.params import tensor_dict_sha
from genesis_gpu.datasets.registry import data_root, _write_dataset, DatasetUnavailable
from genesis_gpu.env.storage_guard import check_windows_bulk_path, ensure_space
from genesis_gpu.runtime.atomic_io import atomic_json, read_json, sha256_file

# Canonical file identities published by torchvision.datasets.MNIST / CIFAR10.
MNIST_MD5 = {
    'train-images-idx3-ubyte.gz': 'f68b3c2dcbeaaa9fbdd348bbdeb94873',
    'train-labels-idx1-ubyte.gz': 'd53e105ee54ea40749a09fcbcd1e9432',
    't10k-images-idx3-ubyte.gz': '9fb629c4189551a2d022fa330f9573f3',
    't10k-labels-idx1-ubyte.gz': 'ec29112dd5afa0611ce80d1b7f02629c',
}
CIFAR_MD5 = {
    'data_batch_1': 'c99cafc152244af753f735de768cd75f',
    'data_batch_2': 'd4bba439e000b95fd0a9bffe97cbabec',
    'data_batch_3': '54ebc095f3ab1f0389bbae665268c751',
    'data_batch_4': '634d18415352ddfa80567beed471001a',
    'data_batch_5': '482c414d41f54cd18b22e5b47cb7c3cb',
    'test_batch': '40351d587109b95175f43aff81a1287e',
    'batches.meta': '5ff9c542aee3614f3951f8cda6e48888',
}


class OfflineImportError(DatasetUnavailable):
    """Source integrity, permissions or prepared dataset state is unqualified."""


def _file_digests(path):
    md5, sha = hashlib.md5(), hashlib.sha256()
    size = 0
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            size += len(block)
            md5.update(block)
            sha.update(block)
    return {'md5': md5.hexdigest(), 'sha256': sha.hexdigest(), 'bytes': size}


def _verify_source_dir(folder, expected):
    folder = Path(folder)
    if not folder.is_dir() or folder.is_symlink():
        raise OfflineImportError('Dataset source directory is missing or symlinked')
    result = {}
    for name, canonical_md5 in expected.items():
        path = folder / name
        if not path.is_file() or path.is_symlink():
            raise OfflineImportError('Missing or symlinked original source file: ' + name)
        values = _file_digests(path)
        if values['md5'] != canonical_md5:
            raise OfflineImportError('Noncanonical torchvision source MD5: ' + name)
        result[name] = values
    return result


def _copy_verified_sources(source, dest, receipts):
    dest.mkdir(parents=True, exist_ok=True)
    for name, expected in receipts.items():
        existing = dest / name
        if existing.exists():
            if existing.is_symlink() or not existing.is_file() or _file_digests(existing) != expected:
                raise OfflineImportError('E: original exists with different bytes: ' + name)
            continue
        temp = dest / ('.' + name + '.' + uuid.uuid4().hex + '.partial')
        try:
            with (source / name).open('rb') as inp, temp.open('xb') as out:
                shutil.copyfileobj(inp, out, length=1024 * 1024)
                out.flush()
                os.fsync(out.fileno())
            if _file_digests(temp) != expected:
                raise OfflineImportError('File changed while copying from C: to E: ' + name)
            os.replace(temp, existing)
        finally:
            if temp.exists():
                temp.unlink()  # Only own temporary E: file; never delete a source.
    return receipts


def _read_idx_gz(path, magic, count):
    expected = 16 + count * 28 * 28 if magic == 2051 else 8 + count
    with gzip.open(path, 'rb') as inp:
        raw = inp.read(expected + 1)  # Hard decompression limit.
    if len(raw) != expected:
        raise OfflineImportError('Compressed IDX size mismatch: ' + path.name)
    got_magic, got_count = struct.unpack_from('>II', raw)
    if (got_magic, got_count) != (magic, count):
        raise OfflineImportError('Unexpected IDX type/count: ' + path.name)
    if magic == 2051:
        if struct.unpack_from('>II', raw, 8) != (28, 28):
            raise OfflineImportError('MNIST image dimensions are not 28x28')
        values = np.frombuffer(raw, dtype=np.uint8, offset=16).reshape(count, 1, 28, 28)
    elif magic == 2049:
        values = np.frombuffer(raw, dtype=np.uint8, offset=8)
        if (values > 9).any():
            raise OfflineImportError('MNIST label is outside 0..9')
    else:
        raise OfflineImportError('Unqualified IDX type')
    return torch.from_numpy(values.copy())


class _RestrictedCIFARUnpickler(pickle.Unpickler):
    """Reject arbitrary pickle imports even after canonical MD5 validation."""
    ALLOWED = {
        ('_codecs', 'encode'), ('codecs', 'encode'),
        ('numpy', 'ndarray'), ('numpy', 'dtype'),
        ('numpy.core.multiarray', '_reconstruct'),
        ('numpy._core.multiarray', '_reconstruct'),
        ('numpy.core.multiarray', 'scalar'),
        ('numpy._core.multiarray', 'scalar'),
    }

    def find_class(self, module, name):
        if (module, name) not in self.ALLOWED:
            raise OfflineImportError(f'Forbidden CIFAR pickle global: {module}.{name}')
        return super().find_class(module, name)

    def persistent_load(self, pid):
        raise OfflineImportError('Persistent pickle objects are forbidden')


def _read_cifar_batch(path, count=10000):
    with Path(path).open('rb') as stream:
        obj = _RestrictedCIFARUnpickler(stream, encoding='latin1').load()
    if not isinstance(obj, dict):
        raise OfflineImportError('CIFAR batch is not a dict')
    def get(k):
        return obj.get(k, obj.get(k.encode('ascii')))
    data, labels = get('data'), get('labels')
    if not isinstance(data, np.ndarray) or data.dtype != np.uint8 or data.shape != (count, 3072):
        raise OfflineImportError('CIFAR expected uint8 (10000,3072) image data')
    if not isinstance(labels, (list, tuple)) or len(labels) != count:
        raise OfflineImportError('CIFAR labels malformed')
    if any(type(x) is not int or x < 0 or x > 9 for x in labels):
        raise OfflineImportError('CIFAR label outside 0..9')
    return (torch.from_numpy(np.ascontiguousarray(data.reshape(count, 3, 32, 32))),
            torch.tensor(labels, dtype=torch.long))


def _standard_split(train_x, train_y, test_x, test_y):
    if len(train_x) != len(train_y) or len(test_x) != len(test_y):
        raise OfflineImportError('Image/label count mismatch')
    gen = torch.Generator().manual_seed(20261102)
    shuffled = torch.randperm(len(train_x), generator=gen)
    training, validation = shuffled[:-5000], shuffled[-5000:]
    return {
        'train_x': train_x[training].contiguous(),
        'train_y': train_y[training].contiguous(),
        'validation_x': train_x[validation].contiguous(),
        'validation_y': train_y[validation].contiguous(),
        'test_x': test_x.contiguous(), 'test_y': test_y.contiguous(),
        'train_ids': training, 'validation_ids': validation,
    }


def _mnist_data(folder):
    images = _read_idx_gz(folder / 'train-images-idx3-ubyte.gz', 2051, 60000)
    labels = _read_idx_gz(folder / 'train-labels-idx1-ubyte.gz', 2049, 60000).long()
    t_images = _read_idx_gz(folder / 't10k-images-idx3-ubyte.gz', 2051, 10000)
    t_labels = _read_idx_gz(folder / 't10k-labels-idx1-ubyte.gz', 2049, 10000).long()
    return _standard_split(images, labels, t_images, t_labels)


def _cifar_data(folder):
    images, labels = [], []
    for i in range(1, 6):
        x, y = _read_cifar_batch(folder / f'data_batch_{i}')
        images.append(x)
        labels.append(y)
    t_x, t_y = _read_cifar_batch(folder / 'test_batch')
    return _standard_split(torch.cat(images), torch.cat(labels), t_x, t_y)


def import_local_images(cfg, run_root, *, mnist_raw, cifar_batches,
                        authorized_local_use=False, production=True):
    if not authorized_local_use:
        raise OfflineImportError('Explicit local-dataset rights confirmation is required')
    if production and cfg['profile'] != 'full':
        raise OfflineImportError('Full production dataset profile is required')
    root, run_root = data_root(cfg), Path(run_root)
    if production:
        for path in (root, root.resolve(), run_root, run_root.resolve()):
            check_windows_bulk_path(path)
    ensure_space(root, 30 * 1024**3 if production else 0,
                 projected_bytes=2 * 1024**3 if production else 0)
    sources = {
        'mnist': (Path(mnist_raw), MNIST_MD5),
        'cifar10': (Path(cifar_batches), CIFAR_MD5),
    }
    # Check BOTH sources in full before staging any new files.
    receipts = {name: _verify_source_dir(folder, expected)
                for name, (folder, expected) in sources.items()}
    records = []
    for name, (source, _) in sources.items():
        originals = root / 'offline_originals' / ('MNIST/raw' if name == 'mnist' else 'cifar-10-batches-py')
        if production:
            check_windows_bulk_path(originals.resolve())
        _copy_verified_sources(source, originals, receipts[name])
        dest = root / name
        if dest.exists():
            meta_path, data_path = dest / 'manifest.json', dest / 'data.safetensors'
            if not meta_path.is_file() or not data_path.is_file():
                raise OfflineImportError('Existing prepared dataset is incomplete: ' + name)
            meta = read_json(meta_path)
            if (meta.get('raw_source_sha256') != {k: v['sha256'] for k, v in receipts[name].items()}
                    or sha256_file(data_path) != meta.get('data_sha')):
                raise OfflineImportError('Prepared dataset has conflicting provenance: ' + name)
            records.append({'dataset': name, 'status': 'ALREADY_IMPORTED_VERIFIED',
                            'prepared_sha256': meta['data_sha']})
            continue
        stage = root / ('offline-stage-' + uuid.uuid4().hex)
        stage.mkdir(parents=True, exist_ok=False)
        tensors = _mnist_data(originals) if name == 'mnist' else _cifar_data(originals)
        ids = torch.randperm(60000 if name == 'mnist' else 50000,
                             generator=torch.Generator().manual_seed(20261102))
        sha_map = {k: v['sha256'] for k, v in receipts[name].items()}
        source_meta = {
            'dataset': name,
            'source_uri': 'owner-supplied canonical torchvision files (offline)',
            'license': 'Owner attests permission for local academic research; raw redistribution prohibited',
            'license_receipt': {'owner_confirmed': True, 'scope': 'local research only',
                                'utc': datetime.now(timezone.utc).isoformat()},
            'raw_source_sha256': sha_map, 'raw_source_md5_matched_torchvision': True,
            'raw_source_archived_on_E': str(originals),
            'split_seed': 20261102,
            'split_sha': tensor_dict_sha({'train': ids[:-5000], 'validation': ids[-5000:]}),
            'transform': ('uint8 CHW MNIST (x/255-.1307)/.3081' if name == 'mnist'
                          else 'uint8 CHW CIFAR (x/255-.5)/.5') + '; curvature no augmentation',
            'input_counts': [60000, 10000] if name == 'mnist' else [50000, 10000],
            'final_counts': [len(tensors['train_y']), len(tensors['validation_y']), len(tensors['test_y'])],
            'publication_policy': 'Never push source data, raw images, labels, or prepared safetensors',
        }
        _write_dataset(stage, name, tensors, source_meta)
        prepared = stage / name
        meta = read_json(prepared / 'manifest.json')
        if sha256_file(prepared / 'data.safetensors') != meta['data_sha']:
            raise OfflineImportError('Staged prepared data SHA256 failed')
        if dest.exists():
            raise OfflineImportError('Concurrent prepared dataset detected; refusing overwrite')
        prepared.rename(dest)  # Atomic rename on the E: filesystem.
        records.append({'dataset': name, 'status': 'IMPORTED_VERIFIED',
                        'raw_sha256': sha_map, 'prepared_sha256': meta['data_sha'],
                        'counts': source_meta['final_counts']})
    result = {'status': 'IMAGE_DATASETS_READY_TEXT_PENDING',
              'source': 'LOCAL_EXISTING_FILES_NO_NETWORK',
              'C_originals_modified': False, 'E_originals_preserved': True,
              'datasets': records, 'text_corpus': 'STILL_REQUIRES_OWN_SOURCE_REVIEW',
              'cuda_g0': 'NOT_RUN_BY_THIS_COMMAND', 'S1_S2': 'NOT_RUN_BY_THIS_COMMAND'}
    atomic_json(run_root / 'datasets' / 'local_image_import_receipt.json', result)
    return result
