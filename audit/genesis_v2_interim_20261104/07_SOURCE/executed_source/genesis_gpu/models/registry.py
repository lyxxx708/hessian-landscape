from collections import OrderedDict
import torch
from genesis_gpu.contracts import ModelSpec
from .dln import DeepLinear
from .mlp import MLP
from .resnet_gn import ResNetGN
from .tiny_transformer import TinyTransformer


REGISTRY={'dln':DeepLinear,'mlp':MLP,'resnet':ResNetGN,'transformer':TinyTransformer}


def build_model(spec: ModelSpec, seed: int):
    # Isolate initialization from the caller's RNG. Seed is explicit and persisted.
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(seed)
        model=REGISTRY[spec.family](spec)
    return model


def parameter_groups(model, schema='coarse'):
    if schema not in ('coarse','fine'):
        raise ValueError('Unknown grouping schema')
    groups=OrderedDict()
    for name,_ in model.named_parameters(remove_duplicate=True):
        label=model.group_for(name,schema) if hasattr(model,'group_for') else name.rsplit('.',1)[0]
        groups.setdefault(label,[]).append(name)
    return groups
