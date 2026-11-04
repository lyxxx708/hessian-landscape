"""Offline image import QA. Fixtures are generated locally; no network/data download."""
import gzip
import hashlib
import pickle
import struct

import numpy as np
import pytest
import torch

from genesis_gpu.datasets import offline_import as imp
from genesis_gpu.cli import parser
from genesis_gpu.runtime.atomic_io import read_json


def test_mnist_gzip_idx_parse_and_malformed_count(tmp_path):
    imgs=tmp_path/'images.gz';labs=tmp_path/'labels.gz'
    with gzip.open(imgs,'wb') as f:
        f.write(struct.pack('>IIII',2051,2,28,28)+bytes([7])*1568)
    with gzip.open(labs,'wb') as f:
        f.write(struct.pack('>II',2049,2)+bytes([0,9]))
    x=imp._read_idx_gz(imgs,2051,2)
    y=imp._read_idx_gz(labs,2049,2)
    assert x.shape==(2,1,28,28) and x.dtype==torch.uint8
    assert y.tolist()==[0,9]
    with pytest.raises(imp.OfflineImportError):
        imp._read_idx_gz(imgs,2051,3)


def test_cifar_restricted_pickle_and_shape(tmp_path):
    path=tmp_path/'data_batch_1'
    with path.open('wb') as f:
        pickle.dump({'data':np.zeros((2,3072),dtype=np.uint8),'labels':[1,2]},f,protocol=2)
    x,y=imp._read_cifar_batch(path,2)
    assert x.shape==(2,3,32,32) and y.tolist()==[1,2]
    with path.open('wb') as f:
        pickle.dump({'data':np.zeros((2,3072),dtype=np.float32),'labels':[1,2]},f,protocol=2)
    with pytest.raises(imp.OfflineImportError):
        imp._read_cifar_batch(path,2)
    with path.open('wb') as f:
        pickle.dump({'data':__import__('os').system,'labels':[]},f,protocol=2)
    with pytest.raises(imp.OfflineImportError):
        imp._read_cifar_batch(path,2)


def test_unqualified_cifar_md5_is_rejected_before_unpickling(tmp_path):
    (tmp_path/'data_batch_1').write_bytes(b'not a canonical CIFAR file')
    with pytest.raises(imp.OfflineImportError):
        imp._verify_source_dir(tmp_path,{'data_batch_1':imp.CIFAR_MD5['data_batch_1']})


def test_fixed_split_seed_no_train_validation_overlap():
    x=torch.arange(10000).reshape(10000,1)
    y=torch.zeros(10000,dtype=torch.long)
    tx=x[:100];ty=y[:100]
    a=imp._standard_split(x,y,tx,ty)
    b=imp._standard_split(x,y,tx,ty)
    assert len(a['train_y'])==5000 and len(a['validation_y'])==5000
    assert set(a['train_ids'].tolist()).isdisjoint(set(a['validation_ids'].tolist()))
    assert torch.equal(a['train_ids'],b['train_ids'])
    assert len(a['test_y'])==100


def test_full_offline_import_receipt_reimport_and_source_preservation(tmp_path,monkeypatch):
    mnist=tmp_path/'original'/'MNIST'/'raw'
    cifar=tmp_path/'original'/'cifar-10-batches-py'
    mnist.mkdir(parents=True);cifar.mkdir(parents=True)
    for directory,expected in [(mnist,imp.MNIST_MD5),(cifar,imp.CIFAR_MD5)]:
        for name in expected:
            (directory/name).write_bytes(('fixture_'+name).encode())
    monkeypatch.setattr(imp,'MNIST_MD5',{name:hashlib.md5((mnist/name).read_bytes()).hexdigest() for name in imp.MNIST_MD5})
    monkeypatch.setattr(imp,'CIFAR_MD5',{name:hashlib.md5((cifar/name).read_bytes()).hexdigest() for name in imp.CIFAR_MD5})
    def tensors():
        x=torch.zeros(10,1,28,28,dtype=torch.uint8);y=torch.arange(10).long()
        return {'train_x':x[:6].contiguous(),'train_y':y[:6].contiguous(),
                'validation_x':x[6:8].contiguous(),'validation_y':y[6:8].contiguous(),
                'test_x':x[8:].contiguous(),'test_y':y[8:].contiguous(),
                'train_ids':torch.arange(6),'validation_ids':torch.arange(6,8)}
    monkeypatch.setattr(imp,'_mnist_data',lambda _:tensors())
    monkeypatch.setattr(imp,'_cifar_data',lambda _:tensors())
    cfg={'profile':'smoke','storage_root':str(tmp_path/'E')}
    run_root=tmp_path/'E'/'runs'/'smoke'
    result=imp.import_local_images(cfg,run_root,mnist_raw=mnist,cifar_batches=cifar,
                                    authorized_local_use=True,production=False)
    assert result['status']=='IMAGE_DATASETS_READY_TEXT_PENDING'
    assert all(r['status']=='IMPORTED_VERIFIED' for r in result['datasets'])
    for name in ('mnist','cifar10'):
        prepared=tmp_path/'E'/'datasets'/'genesis_v2'/name
        assert (prepared/'data.safetensors').is_file()
        meta=read_json(prepared/'manifest.json')
        assert meta['license_receipt']['owner_confirmed']
        assert meta['source_uri'].startswith('owner-supplied')
    assert (mnist/'train-images-idx3-ubyte.gz').read_bytes()==b'fixture_train-images-idx3-ubyte.gz'
    repeat=imp.import_local_images(cfg,run_root,mnist_raw=mnist,cifar_batches=cifar,
                                    authorized_local_use=True,production=False)
    assert all(r['status']=='ALREADY_IMPORTED_VERIFIED' for r in repeat['datasets'])
    # Tampering with a prepared E: dataset does not trigger silent replacement.
    data=tmp_path/'E'/'datasets'/'genesis_v2'/'mnist'/'data.safetensors'
    with data.open('ab') as f:f.write(b'CORRUPTION')
    with pytest.raises(imp.OfflineImportError):
        imp.import_local_images(cfg,run_root,mnist_raw=mnist,cifar_batches=cifar,
                                 authorized_local_use=True,production=False)


def test_rights_attestation_and_cli_arguments(tmp_path):
    cfg={'profile':'smoke','storage_root':str(tmp_path/'E')}
    with pytest.raises(imp.OfflineImportError):
        imp.import_local_images(cfg,tmp_path/'E'/'runs',mnist_raw=tmp_path/'none',cifar_batches=tmp_path/'none',
                                 authorized_local_use=False,production=False)
    assert not (tmp_path/'E').exists()
    args=parser().parse_args(['--config','configs/study_v2.yaml','import-local-images',
                              '--mnist-raw','C:/example/MNIST/raw','--cifar-batches','C:/example/cifar-10-batches-py',
                              '--confirm-authorized-local-use'])
    assert args.command=='import-local-images' and args.confirm_authorized_local_use
    assert args.mnist_raw.name=='raw'
