import torch
from torch import nn


class DeepLinear(nn.Module):
    def __init__(self, spec):
        super().__init__()
        dims = [spec.input_dim] + [spec.width]*(spec.depth-1) + [spec.output_dim]
        self.layers = nn.ModuleList([nn.Linear(a,b,bias=False) for a,b in zip(dims[:-1],dims[1:])])
        with torch.no_grad():
            for i, layer in enumerate(self.layers):
                if spec.balance == 'orthogonal_balanced':
                    nn.init.orthogonal_(layer.weight, gain=.95)
                elif spec.balance == 'random_unbalanced':
                    nn.init.normal_(layer.weight, std=layer.in_features**-.5)
                    # Product of reciprocal scale pairs remains one; non-orthogonal weights remain explicit.
                    layer.weight.mul_(2. if i%2 == 0 else .5)
                else:
                    raise ValueError(f'Unknown DLN initialization {spec.balance}')
        self.genesis_spec = spec

    def forward(self, x):
        for layer in self.layers:
            x = layer(x)
        return x

    def group_for(self, name, schema):
        return 'layer_' + name.split('.')[1]
