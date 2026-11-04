"""Atomic checkpoint directories: JSON structure + safetensors, no pickle execution."""
from __future__ import annotations
from pathlib import Path
import os
import shutil
import uuid
import torch
from safetensors.torch import save_file,load_file
from genesis_gpu.runtime.atomic_io import atomic_json,file_receipt,verify_receipt,read_json,sha256_file


class IntegrityError(RuntimeError):
    pass


def _encode(value,tensors):
    if isinstance(value,torch.Tensor):
        key=f't{len(tensors):07d}';tensors[key]=value.detach().cpu().contiguous().clone()
        return {'__tensor__':key}
    if isinstance(value,dict):
        return {'__map__':[[_encode(k,tensors),_encode(v,tensors)] for k,v in value.items()]}
    if isinstance(value,tuple):return {'__tuple__':[_encode(v,tensors) for v in value]}
    if isinstance(value,list):return {'__list__':[_encode(v,tensors) for v in value]}
    if value is None or isinstance(value,(bool,str,int,float)):return value
    raise TypeError(f'Unsafe/unsupported checkpoint object {type(value).__name__}')


def _decode(value,tensors):
    if not isinstance(value,dict):return value
    if set(value)=={'__tensor__'}:return tensors[value['__tensor__']]
    if set(value)=={'__map__'}:return {_decode(k,tensors):_decode(v,tensors) for k,v in value['__map__']}
    if set(value)=={'__tuple__'}:return tuple(_decode(v,tensors) for v in value['__tuple__'])
    if set(value)=={'__list__'}:return [_decode(v,tensors) for v in value['__list__']]
    raise IntegrityError('Unknown checkpoint structure tag')


def save_state(path,state,metadata):
    path=Path(path)
    if path.exists():raise FileExistsError(f'Immutable checkpoint already exists: {path}')
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.parent/('.'+path.name+'.'+uuid.uuid4().hex+'.partial');tmp.mkdir()
    try:
        tensors={};tree=_encode(state,tensors)
        save_file(tensors,str(tmp/'tensors.safetensors'))
        # Windows rejects fsync() on a read-only descriptor. Reopen for update
        # so the same durability barrier works on both POSIX and Windows.
        with (tmp/'tensors.safetensors').open('r+b') as f:
            f.flush();os.fsync(f.fileno())
        atomic_json(tmp/'metadata.json',{'schema':2,'metadata':metadata,'tree':tree})
        receipt={'schema':2,'files':[file_receipt(tmp/'tensors.safetensors',tmp),file_receipt(tmp/'metadata.json',tmp)]}
        atomic_json(tmp/'integrity.json',receipt)
        os.replace(tmp,path)
    except BaseException:
        shutil.rmtree(tmp,ignore_errors=True)
        raise
    return {'path':str(path),'integrity_sha':sha256_file(path/'integrity.json')}


def load_state(path,expected_integrity_sha=None):
    path=Path(path)
    try:
        if expected_integrity_sha and sha256_file(path/'integrity.json')!=expected_integrity_sha:
            raise IntegrityError('Checkpoint integrity manifest SHA mismatch')
        receipt=read_json(path/'integrity.json')
        if receipt.get('schema')!=2 or not all(verify_receipt(path,r) for r in receipt['files']):
            raise IntegrityError('Checkpoint bytes changed or incomplete')
        meta=read_json(path/'metadata.json')
        mapped=load_file(str(path/'tensors.safetensors'),device='cpu')
        # safetensors maps files on Windows; retaining those mappings prevents
        # immutable-generation cleanup and tamper fixtures from replacing files.
        tensors={key:value.clone() for key,value in mapped.items()}
        del mapped
        return _decode(meta['tree'],tensors),meta['metadata']
    except IntegrityError:raise
    except Exception as exc:raise IntegrityError(f'Cannot load verified checkpoint {path}: {exc}') from exc


def save_resume(parent,state,metadata):
    """Versioned transient resume state; pointer commits last. Fixed science checkpoints never deleted."""
    parent=Path(parent);parent.mkdir(parents=True,exist_ok=True)
    old=read_json(parent/'latest.json') if (parent/'latest.json').exists() else None
    generation='g-'+uuid.uuid4().hex
    saved=save_state(parent/generation,state,metadata)
    atomic_json(parent/'latest.json',{'generation':generation,'integrity_sha':saved['integrity_sha']})
    if old:
        old_path=parent/old['generation']
        # Only our generated transient slot, never caller-supplied arbitrary paths.
        if old_path.parent==parent and old_path.name.startswith('g-') and old_path!=parent/generation:
            shutil.rmtree(old_path)


def load_resume(parent):
    parent=Path(parent)
    if not (parent/'latest.json').exists():return None
    pointer=read_json(parent/'latest.json');name=pointer['generation']
    if Path(name).name!=name or not name.startswith('g-'):raise IntegrityError('Unsafe resume pointer')
    return load_state(parent/name,pointer['integrity_sha'])
