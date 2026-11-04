"""Versioned immutable scientific contracts. No disk or scheduler side effects."""
from __future__ import annotations
from dataclasses import dataclass, asdict, field
from typing import Literal, Any
import hashlib
import json
import torch
from torch import Tensor
import torch.nn.functional as F


def object_sha(value: Any) -> str:
    if hasattr(value, '__dataclass_fields__'):
        value = asdict(value)
    raw = json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
    return hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True)
class LossSpec:
    kind: Literal['mse', 'ce']
    ignore_index: int = -100
    reduction: str = 'mean'
    label_smoothing: float = 0.0
    class_weights: None = None

    def __post_init__(self):
        if self.kind not in ('mse', 'ce') or self.reduction != 'mean':
            raise ValueError('Only half-MSE mean and unweighted CE mean are qualified')
        if self.label_smoothing != 0 or self.class_weights is not None:
            raise ValueError('Class weights / label smoothing require a separately validated adapter')

    def count(self, prediction: Tensor, target: Tensor) -> int:
        if self.kind == 'mse':
            if prediction.shape != target.shape or prediction.numel() == 0:
                raise ValueError('MSE output and target must match, nonempty')
            return prediction.numel()
        if prediction.shape[:-1] != target.shape or prediction.shape[-1] < 2:
            raise ValueError('CE uses classes on the last axis and target shaped [...], not one-hot')
        if target.dtype != torch.long:
            raise ValueError('CE target must be int64')
        mask = target != self.ignore_index
        count = int(mask.sum().item())
        if count == 0:
            raise ValueError('No valid target elements')
        valid = target[mask]
        if (valid < 0).any() or (valid >= prediction.shape[-1]).any():
            raise ValueError('CE target outside vocabulary')
        return count

    def value(self, prediction: Tensor, target: Tensor, denominator: int | None = None) -> Tensor:
        count = self.count(prediction, target)
        n = count if denominator is None else denominator
        if n < count or n <= 0:
            raise ValueError('Global loss denominator cannot be smaller than this microbatch')
        if self.kind == 'mse':
            return (prediction - target).square().sum() / (2 * n)
        return F.cross_entropy(prediction.reshape(-1, prediction.shape[-1]), target.reshape(-1),
                               ignore_index=self.ignore_index, reduction='sum') / n

    def output_metric(self, prediction: Tensor, target: Tensor, vector: Tensor,
                      denominator: int | None = None) -> Tensor:
        """The true output-loss Hessian action, including global reduction and ignore mask."""
        count = self.count(prediction, target)
        n = count if denominator is None else denominator
        if vector.shape != prediction.shape or n < count:
            raise ValueError('Output metric shape or denominator mismatch')
        if self.kind == 'mse':
            return vector / n
        p = prediction.detach().softmax(-1)
        weighted = p * (vector - (p * vector).sum(-1, keepdim=True))
        return weighted * (target != self.ignore_index).unsqueeze(-1) / n


@dataclass(frozen=True)
class ModelSpec:
    family: str
    depth: int
    width: int = 16
    input_dim: int = 16
    output_dim: int = 16
    activation: str = 'relu'
    normalization: str = 'none'
    heads: int = 6
    context: int = 128
    vocab_size: int = 128
    tie_weights: bool = False
    dropout: float = 0.0
    balance: str = 'orthogonal_balanced'
    covariance_condition: float = 1.0
    image_size: int = 32
    channels: int = 3

    def __post_init__(self):
        if self.family not in {'dln', 'mlp', 'resnet', 'transformer'}:
            raise ValueError(f'Unknown model family {self.family}')
        if min(self.depth, self.width, self.input_dim, self.output_dim, self.context, self.vocab_size) < 1:
            raise ValueError('Model dimensions must be positive')
        if self.family == 'transformer' and (self.heads < 1 or self.width % self.heads):
            raise ValueError('Transformer width must be divisible by heads')
        if self.family == 'resnet' and (self.depth < 8 or (self.depth - 2) % 6):
            raise ValueError('CIFAR ResNet depth must be 6n+2, n>=1')
        if self.dropout != 0:
            raise ValueError('v2 freezes dropout=0: moving stochastic operators are not allowed')
        if self.covariance_condition < 1:
            raise ValueError('Covariance condition must be at least 1')

    @property
    def sha(self):
        return object_sha(self)


@dataclass(frozen=True)
class TrainSpec:
    optimizer: str = 'adam'
    budget_kind: str = 'steps'
    budget: int = 4000
    effective_batch: int = 256
    microbatch: int = 32
    learning_rate: float = .001
    weight_decay: float = 0.0
    momentum: float = .9
    checkpoint_fractions: tuple[float, ...] = (0., 1/3, 2/3, 1.)
    save_every_steps: int = 100
    schedule: str = 'cosine'
    augmentation: bool = False

    def __post_init__(self):
        if self.budget_kind not in {'steps', 'epochs', 'tokens'}:
            raise ValueError('Unknown training budget')
        if min(self.budget, self.effective_batch, self.microbatch, self.save_every_steps) <= 0:
            raise ValueError('Training counts must be positive')
        if self.learning_rate <= 0 or self.weight_decay < 0:
            raise ValueError('Invalid learning rate or weight decay')
        if tuple(sorted(set(self.checkpoint_fractions))) != self.checkpoint_fractions:
            raise ValueError('Checkpoint fractions must be unique and sorted')
        if self.checkpoint_fractions[0] != 0 or self.checkpoint_fractions[-1] != 1:
            raise ValueError('Checkpoint fractions must include 0 and 1')


@dataclass(frozen=True)
class RunSpec:
    run_id: str
    setting_id: str
    stage: str
    seed: int
    seed_index: int
    model: ModelSpec
    train: TrainSpec
    dataset: str
    deep: bool = False

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, value):
        v = dict(value)
        v['model'] = ModelSpec(**v['model'])
        t = dict(v['train'])
        t['checkpoint_fractions'] = tuple(t['checkpoint_fractions'])
        v['train'] = TrainSpec(**t)
        return cls(**v)


@dataclass(frozen=True)
class SnapshotSpec:
    run_id: str
    seed_cluster: str
    step: int
    checkpoint_sha256: str
    model_sha256: str
    batch_sha256: str
    loss_spec_sha: str
    params_sha256: str
    buffers_sha256: str
    precision: str


@dataclass
class SolveResult:
    direction: Tensor
    converged: bool
    true_residual: float
    iterations: int
    status: str
    absolute_residual: float = 0.
    wall_time: float = 0.
    matvecs: int = 0
    residual_history: list[float] = field(default_factory=list)

    def receipt(self):
        return {k: v for k, v in self.__dict__.items() if k != 'direction'}
