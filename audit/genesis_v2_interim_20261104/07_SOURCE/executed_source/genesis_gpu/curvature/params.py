"""One layout shared by training snapshots, exact/block oracles and verifier."""
from collections import OrderedDict
from dataclasses import dataclass
import hashlib
import torch
from genesis_gpu.contracts import object_sha
from genesis_gpu.models.registry import parameter_groups


def tensor_sha(tensor):
    t=tensor.detach().contiguous().cpu()
    h=hashlib.sha256()
    h.update(str(t.dtype).encode());h.update(str(tuple(t.shape)).encode())
    h.update(t.reshape(-1).view(torch.uint8).numpy().tobytes())
    return h.hexdigest()


def tensor_dict_sha(tensors):
    return object_sha({k:tensor_sha(v) for k,v in sorted(tensors.items())})


@dataclass(frozen=True)
class Entry:
    name: str
    shape: tuple
    start: int
    stop: int


class ParamLayout:
    def __init__(self, model):
        unique=list(model.named_parameters(remove_duplicate=True))
        self.entries=[];offset=0
        by_id={id(p):name for name,p in unique}
        self.aliases={name:[] for name,_ in unique}
        for name,p in model.named_parameters(remove_duplicate=False):
            self.aliases[by_id[id(p)]].append(name)
        for name,p in unique:
            self.entries.append(Entry(name,tuple(p.shape),offset,offset+p.numel()));offset+=p.numel()
        self.numel=offset
        self.schemas={s:parameter_groups(model,s) for s in ('coarse','fine')}
        self.by_name={e.name:e for e in self.entries}
        self.sha=object_sha({'entries':[e.__dict__ for e in self.entries],'aliases':self.aliases,'schemas':self.schemas})
        for schema in self.schemas:
            ids=torch.cat(self.group_indices(schema))
            if len(ids)!=offset or len(torch.unique(ids))!=offset:
                raise ValueError('Parameter grouping does not partition logical degrees of freedom')

    def flatten(self,model):
        params=dict(model.named_parameters(remove_duplicate=True))
        return torch.cat([params[e.name].detach().reshape(-1) for e in self.entries]).clone()

    def unflatten(self,theta):
        if theta.ndim!=1 or theta.numel()!=self.numel:
            raise ValueError('Parameter vector/layout mismatch')
        return OrderedDict((e.name,theta[e.start:e.stop].view(e.shape)) for e in self.entries)

    def group_indices(self,schema='coarse',device=None):
        return [torch.cat([torch.arange(self.by_name[n].start,self.by_name[n].stop,device=device)
                           for n in names]) for names in self.schemas[schema].values()]

    def group_sizes(self,schema='coarse'):
        return [len(x) for x in self.group_indices(schema)]
