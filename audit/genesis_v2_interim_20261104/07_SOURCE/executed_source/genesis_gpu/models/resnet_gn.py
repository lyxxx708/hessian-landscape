import math
from torch import nn
import torch


def norm(c):
    return nn.GroupNorm(math.gcd(c,8), c)


class BasicBlock(nn.Module):
    def __init__(self,cin,cout,stride):
        super().__init__()
        self.conv1=nn.Conv2d(cin,cout,3,stride=stride,padding=1,bias=False)
        self.norm1=norm(cout)
        self.conv2=nn.Conv2d(cout,cout,3,padding=1,bias=False)
        self.norm2=norm(cout)
        self.skip=nn.Identity() if stride==1 and cin==cout else nn.Conv2d(cin,cout,1,stride=stride,bias=False)

    def forward(self,x):
        y=torch.relu(self.norm1(self.conv1(x)))
        y=self.norm2(self.conv2(y))
        return torch.relu(y+self.skip(x))


class ResNetGN(nn.Module):
    def __init__(self,spec):
        super().__init__()
        self.stem=nn.Sequential(nn.Conv2d(spec.channels,spec.width,3,padding=1,bias=False),norm(spec.width))
        n=(spec.depth-2)//6
        blocks=[]; cin=spec.width
        for stage in range(3):
            cout=spec.width*(2**stage)
            for i in range(n):
                stride=2 if stage>0 and i==0 else 1
                blocks.append(BasicBlock(cin,cout,stride));cin=cout
        self.blocks=nn.ModuleList(blocks)
        self.head=nn.Linear(cin,spec.output_dim)
        self.genesis_spec=spec

    def forward(self,x):
        x=torch.relu(self.stem(x))
        for block in self.blocks:
            x=block(x)
        return self.head(x.mean(dim=(-2,-1)))

    def group_for(self,name,schema):
        parts=name.split('.')
        if parts[0]!='blocks':
            return parts[0]
        if schema=='coarse':
            return f'block_{parts[1]}'
        half='a' if parts[2] in ('conv1','norm1') else 'b'
        return f'block_{parts[1]}_{half}'
