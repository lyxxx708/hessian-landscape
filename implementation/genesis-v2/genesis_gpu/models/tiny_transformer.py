"""Reference causal attention built from ordinary matmuls for qualified JVP/HVP.

No FlashAttention/SDPA dispatch, dropout or mutable running-statistics buffers.
"""
import math
import torch
from torch import nn
import torch.nn.functional as F


class CausalBlock(nn.Module):
    def __init__(self,width,heads):
        super().__init__()
        self.heads=heads
        self.norm1=nn.LayerNorm(width)
        self.qkv=nn.Linear(width,3*width)
        self.projection=nn.Linear(width,width)
        self.norm2=nn.LayerNorm(width)
        self.ff1=nn.Linear(width,4*width)
        self.ff2=nn.Linear(4*width,width)

    def forward(self,x):
        b,t,d=x.shape
        z=self.norm1(x)
        q,k,v=self.qkv(z).reshape(b,t,3,self.heads,d//self.heads).unbind(2)
        q,k,v=(a.transpose(1,2) for a in (q,k,v))
        logits=q@k.transpose(-1,-2)/math.sqrt(d//self.heads)
        mask=torch.ones(t,t,device=x.device,dtype=torch.bool).triu(1)
        attn=logits.masked_fill(mask,float('-inf')).softmax(-1)
        y=(attn@v).transpose(1,2).reshape(b,t,d)
        x=x+self.projection(y)
        return x+self.ff2(F.gelu(self.ff1(self.norm2(x)),approximate='tanh'))


class TinyTransformer(nn.Module):
    def __init__(self,spec):
        super().__init__()
        self.position=nn.Parameter(torch.zeros(spec.context,spec.width))
        self.embedding=nn.Embedding(spec.vocab_size,spec.width)
        self.blocks=nn.ModuleList([CausalBlock(spec.width,spec.heads) for _ in range(spec.depth)])
        self.norm=nn.LayerNorm(spec.width)
        self.head=nn.Linear(spec.width,spec.vocab_size,bias=False)
        if spec.tie_weights:
            self.head.weight=self.embedding.weight
        nn.init.normal_(self.position,std=.02)
        self.genesis_spec=spec

    def forward(self,tokens):
        if tokens.ndim!=2 or tokens.shape[1]>self.position.shape[0]:
            raise ValueError('Token context exceeds fixed model context')
        x=self.embedding(tokens)+self.position[:tokens.shape[1]]
        for block in self.blocks:
            x=block(x)
        return self.head(self.norm(x))

    def group_for(self,name,schema):
        p=name.split('.')
        if p[0] in ('position','embedding'):
            return 'input_embedding'
        if p[0] in ('head','norm'):
            return 'output_head'
        if schema=='coarse':
            return f'block_{p[1]}'
        part='attention' if p[2] in ('norm1','qkv','projection') else 'feedforward'
        return f'block_{p[1]}_{part}'
