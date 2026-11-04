from torch import nn
import torch


class MLP(nn.Module):
    def __init__(self, spec):
        super().__init__()
        dims = [spec.input_dim]+[spec.width]*(spec.depth-1)+[spec.output_dim]
        self.layers = nn.ModuleList([nn.Linear(a,b) for a,b in zip(dims[:-1],dims[1:])])
        if spec.activation not in ('relu','tanh'):
            raise ValueError('Unqualified activation')
        self.activation = spec.activation
        self.genesis_spec = spec

    def forward(self,x):
        x = x.reshape(x.shape[0],-1)
        for layer in self.layers[:-1]:
            x = layer(x)
            x = torch.relu(x) if self.activation == 'relu' else torch.tanh(x)
        return self.layers[-1](x)

    def group_for(self,name,schema):
        return 'layer_' + name.split('.')[1]
