"""Deterministic data sources. Real datasets never silently become synthetic data."""
from __future__ import annotations
from pathlib import Path
from dataclasses import dataclass
import json
import urllib.request
from urllib.parse import urlparse
import math
import numpy as np
import torch
from safetensors.torch import save_file,load_file
from genesis_gpu.contracts import object_sha
from genesis_gpu.curvature.params import tensor_dict_sha
from genesis_gpu.study.design import seed_for
from genesis_gpu.runtime.atomic_io import atomic_json,atomic_bytes,sha256_file,read_json


class DatasetUnavailable(RuntimeError):
    pass


@dataclass
class DataBundle:
    splits: dict
    source: dict
    family: str
    context: int = 1
    channels: int = 1

    @property
    def fingerprint(self):return self.source['fingerprint']

    def size(self,split='train'):
        x=self.splits[split][0]
        return max(0,len(x)-self.context-1) if self.family=='text' else len(x)

    def batch(self,split,*,step,count,seed,device='cpu',dtype=torch.float32,max_tokens=None,augment=False,offset=None):
        if count<1:raise ValueError('Positive batch size required')
        X,Y=self.splits[split];n=self.size(split)
        if n<=0:raise DatasetUnavailable(f'Insufficient {split} data')
        generator=torch.Generator();generator.manual_seed(seed_for('BATCH',seed,split,step))
        if self.family=='text':
            starts=torch.randint(n,(count,),generator=generator)
            x=torch.stack([X[s:s+self.context] for s in starts])
            y=torch.stack([X[s+1:s+self.context+1] for s in starts]).clone()
            if max_tokens is not None:
                if max_tokens<=0 or max_tokens>y.numel():raise ValueError('Invalid final token count')
                y.flatten()[max_tokens:]=-100
            return x.to(device),y.to(device)
        if offset is None:
            ids=torch.randint(n,(count,),generator=generator)
        else:
            # Epoch permutation and cursor are stateless, making a resumed step bit-identical.
            ids=[];pos=offset;remaining=count
            while remaining:
                epoch=pos//n;start=pos%n;take=min(remaining,n-start)
                rng=torch.Generator();rng.manual_seed(seed_for('EPOCH',seed,split,epoch))
                ids.append(torch.randperm(n,generator=rng)[start:start+take]);pos+=take;remaining-=take
            ids=torch.cat(ids)
        x=X[ids].clone();y=Y[ids].clone()
        if self.family=='image':
            x=x.float()/255. if X.dtype==torch.uint8 else x.float()
            if augment:
                if split!='train':raise ValueError('Evaluation augmentation forbidden')
                # Sample-local, reproducible crop/flip. No BatchNorm state in admitted models.
                padded=torch.nn.functional.pad(x,(4,4,4,4),mode='reflect')
                for i in range(len(x)):
                    a=int(torch.randint(9,(),generator=generator));b=int(torch.randint(9,(),generator=generator))
                    x[i]=padded[i,:,a:a+x.shape[-2],b:b+x.shape[-1]]
                    if bool(torch.randint(2,(),generator=generator)):x[i]=x[i].flip(-1)
            mean=.1307 if self.channels==1 else .5;std=.3081 if self.channels==1 else .5
            x=(x-mean)/std
        return x.to(device=device,dtype=dtype),y.to(device=device,dtype=dtype if y.is_floating_point() else torch.long)


def _synthetic(run,cfg):
    rng=torch.Generator();rng.manual_seed(seed_for('DATA',run.seed))
    m=run.model;small=cfg['profile']=='smoke'
    N=32 if small else 4096;V=16 if small else 1024
    source={'dataset':run.dataset,'seed':run.seed,'license':'generated locally; no external material',
            'evidence_class':'SMOKE_SYNTHETIC_NOT_RESEARCH' if small else 'FRESH_SYNTHETIC_FIXED_TEACHER'}
    if run.dataset=='synthetic_text':
        values=(torch.arange(256)+torch.randint(m.vocab_size,(),generator=rng))%m.vocab_size
        splits={'train':(values[:160].long(),None),'validation':(values[160:208].long(),None),'test':(values[208:].long(),None)}
        family='text'
    elif run.dataset=='synthetic_dln':
        eig=torch.logspace(0,math.log10(m.covariance_condition),m.input_dim,dtype=torch.float64)
        eig=eig/eig.mean()
        rotation,_=torch.linalg.qr(torch.randn(m.input_dim,m.input_dim,generator=rng,dtype=torch.float64))
        teacher=torch.randn(m.output_dim,m.input_dim,generator=rng,dtype=torch.float64)/math.sqrt(m.input_dim)
        splits={}
        for name,n in [('train',N),('validation',V),('test',V)]:
            x=(torch.randn(n,m.input_dim,generator=rng,dtype=torch.float64)*eig.sqrt())@rotation.T
            y=x@teacher.T
            splits[name]=(x,y)
        source['teacher_sha']=tensor_dict_sha({'teacher':teacher});family='regression'
    elif run.dataset=='synthetic_image':
        splits={}
        for name,n in [('train',N),('validation',V),('test',V)]:
            x=torch.randn(n,m.channels,m.image_size,m.image_size,generator=rng)
            y=(torch.arange(n)+int(torch.randint(m.output_dim,(),generator=rng)))%m.output_dim
            splits[name]=(x,y.long())
        family='image'
    else:
        teacher=torch.randn(m.input_dim,m.output_dim,generator=rng)
        splits={name:(x,(x@teacher).argmax(-1)) for name,n in [('train',N),('validation',V),('test',V)]
                for x in [torch.randn(n,m.input_dim,generator=rng)]}
        family='classification'
    tensors={f'{k}_x':v[0] for k,v in splits.items()}
    tensors.update({f'{k}_y':v[1] for k,v in splits.items() if v[1] is not None})
    source['split_sha']=tensor_dict_sha(tensors);source['fingerprint']=object_sha(source)
    return DataBundle(splits,source,family,m.context,m.channels)


def data_root(cfg):
    return Path(cfg['storage_root'])/'datasets'/'genesis_v2'


def _write_dataset(root,name,tensors,source):
    path=root/name;path.mkdir(parents=True,exist_ok=True)
    target=path/'data.safetensors';temporary=path/'data.safetensors.tmp'
    save_file({k:v.contiguous().clone() for k,v in tensors.items()},str(temporary))
    temporary.replace(target)
    source={**source,'data_sha':sha256_file(target),'data_bytes':target.stat().st_size}
    source['fingerprint']=object_sha(source)
    atomic_json(path/'manifest.json',source)
    return source


def prepare_data(cfg,run_root,accept_licenses=False):
    if cfg['profile']=='smoke':
        result={'status':'SMOKE_SYNTHETIC_ONLY','sources':[]}
        atomic_json(Path(run_root)/'datasets'/'manifest.json',result);return result
    root=data_root(cfg);root.mkdir(parents=True,exist_ok=True)
    sources=[]
    for name in ('mnist','cifar10','shakespeare'):
        manifest=root/name/'manifest.json';data=root/name/'data.safetensors'
        if manifest.exists() and data.exists():
            source=read_json(manifest)
            if sha256_file(data)!=source['data_sha']:
                raise DatasetUnavailable(f'{name} SHA mismatch; no automatic destructive replacement')
            sources.append(source);continue
        if not accept_licenses:
            raise DatasetUnavailable('Public-data rights review is required; prepare-data --accept-public-data-licenses records acceptance')
        if name in ('mnist','cifar10'):
            try:from torchvision.datasets import MNIST,CIFAR10
            except Exception as exc:raise DatasetUnavailable(f'torchvision dataset adapter unavailable: {exc}') from exc
            cls=MNIST if name=='mnist' else CIFAR10
            train=cls(str(root/'downloads'),train=True,download=True)
            test=cls(str(root/'downloads'),train=False,download=True)
            if name=='mnist':
                x=train.data.unsqueeze(1);tx=test.data.unsqueeze(1)
                y=train.targets.long();ty=test.targets.long()
            else:
                x=torch.from_numpy(np.asarray(train.data)).permute(0,3,1,2).contiguous()
                tx=torch.from_numpy(np.asarray(test.data)).permute(0,3,1,2).contiguous()
                y=torch.tensor(train.targets,dtype=torch.long);ty=torch.tensor(test.targets,dtype=torch.long)
            rng=torch.Generator().manual_seed(20261102);ids=torch.randperm(len(x),generator=rng)
            train_ids,val_ids=ids[:-5000],ids[-5000:]
            tensors={'train_x':x[train_ids],'train_y':y[train_ids],'validation_x':x[val_ids],
                     'validation_y':y[val_ids],'test_x':tx,'test_y':ty,'train_ids':train_ids,'validation_ids':val_ids}
            source={'dataset':name,'source_uri':'torchvision.datasets.'+cls.__name__,
                    'license':'Original dataset terms acknowledged by operator; distribution not bundled',
                    'acceptance':'explicit CLI flag','download_verification':'torchvision source checksums plus prepared SHA256',
                    'split_seed':20261102,'split_sha':tensor_dict_sha({'train':train_ids,'validation':val_ids}),
                    'transform':'uint8 CHW; MNIST (x/255-.1307)/.3081, CIFAR (x/255-.5)/.5; curvature no augmentation'}
        else:
            url=cfg['data']['text_url'];parsed=urlparse(url)
            if parsed.scheme!='https' or parsed.hostname not in {'www.gutenberg.org','gutenberg.org'}:
                raise DatasetUnavailable('Text download restricted to declared HTTPS Gutenberg source')
            req=urllib.request.Request(url,headers={'User-Agent':'GENESIS-research/2.0'})
            with urllib.request.urlopen(req,timeout=cfg['data']['download_timeout_seconds']) as response:
                final=urlparse(response.url)
                if final.scheme!='https' or final.hostname not in {'www.gutenberg.org','gutenberg.org'}:
                    raise DatasetUnavailable('Unexpected download redirect')
                raw=response.read(25*1024*1024+1)
            if len(raw)>25*1024*1024:raise DatasetUnavailable('Text unexpectedly exceeds 25 MiB; requires review')
            raw_path=root/'downloads'/'shakespeare.txt';atomic_bytes(raw_path,raw)
            raw_sha=sha256_file(raw_path);expected=cfg['data']['text_expected_sha256']
            if expected is not None and raw_sha!=expected:raise DatasetUnavailable('Text source hash mismatch')
            text=raw.decode('utf-8-sig')
            if len(text)<100000 or 'Gutenberg' not in text:raise DatasetUnavailable('Unexpected text payload')
            # Contiguous splits before tokenization; vocabulary learned only from training section.
            cut1=int(.8*len(text));cut2=int(.9*len(text));parts={'train':text[:cut1],'validation':text[cut1:cut2],'test':text[cut2:]}
            vocabulary=sorted(set(parts['train']));mapping={c:i+1 for i,c in enumerate(vocabulary)}
            if len(vocabulary)+1>256:raise DatasetUnavailable('Vocabulary exceeds frozen 256 output classes')
            tensors={f'{k}_tokens':torch.tensor([mapping.get(c,0) for c in s],dtype=torch.long) for k,s in parts.items()}
            source={'dataset':name,'source_uri':url,'source_sha':raw_sha,'license':cfg['data']['text_license'],
                    'acceptance':'explicit CLI flag; original distribution notice retained','vocabulary':vocabulary,'unknown_token':0,
                    'split_offsets':[0,cut1,cut2,len(text)],'vocabulary_scope':'train only',
                    'split_sha':object_sha([cut1,cut2,raw_sha]),'transform':'character IDs, no cross-boundary windows; output vocab size fixed 256'}
        sources.append(_write_dataset(root,name,tensors,source))
    result={'status':'PUBLIC_DATA_PREPARED','root':str(root),'sources':sources}
    atomic_json(Path(run_root)/'datasets'/'manifest.json',result)
    return result


def load_bundle(run,cfg,run_root):
    if run.dataset.startswith('synthetic_'):
        if cfg['profile']=='full' and run.dataset!='synthetic_dln':
            raise DatasetUnavailable('Synthetic replacement for real model families forbidden')
        return _synthetic(run,cfg)
    path=data_root(cfg)/run.dataset;mp=path/'manifest.json';dp=path/'data.safetensors'
    if not mp.exists() or not dp.exists():
        raise DatasetUnavailable(f'{run.dataset} not prepared; run prepare-data, never substitute a synthetic task')
    source=read_json(mp)
    if sha256_file(dp)!=source['data_sha']:raise DatasetUnavailable('Prepared dataset tampered or corrupted')
    data=load_file(str(dp),device='cpu')
    if run.dataset=='shakespeare':
        splits={k:(data[k+'_tokens'],None) for k in ('train','validation','test')};family='text'
    else:
        splits={k:(data[k+'_x'],data[k+'_y']) for k in ('train','validation','test')};family='image'
    return DataBundle(splits,source,family,run.model.context,run.model.channels)
