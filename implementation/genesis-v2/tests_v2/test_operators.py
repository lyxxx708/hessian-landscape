import importlib
import pytest
import torch
from genesis_gpu.contracts import ModelSpec, LossSpec


def mod(name):
    try:
        return importlib.import_module('genesis_gpu.' + name)
    except ModuleNotFoundError as exc:
        pytest.fail(f'Required v2 module missing: {name}: {exc}')


def make_op(kind='mse', micro=None):
    torch.manual_seed(21)
    spec = ModelSpec('dln', 3, 2, 2, 2) if kind == 'mse' else ModelSpec('mlp', 3, 4, 3, 3, activation='tanh')
    model = mod('models.registry').build_model(spec, 31).double()
    x = torch.randn(4, spec.input_dim, dtype=torch.float64)
    y = torch.randn(4, 2, dtype=torch.float64) if kind == 'mse' else torch.tensor([0, 1, -100, 2])
    op = mod('curvature.operators').FrozenOperator(model, x, y, LossSpec(kind), microbatch=micro)
    return model, x, y, op


@pytest.mark.parametrize('kind', ['mse', 'ce'])
def test_matrix_free_matches_independent_dense(kind):
    _, _, _, op = make_op(kind)
    ref = mod('audit.independent_reference').dense_reference(op)
    torch.manual_seed(8)
    v = torch.randn_like(op.theta)
    assert torch.allclose(op.raw_ggn(v), ref['G'] @ v, atol=2e-10, rtol=2e-10)
    assert torch.allclose(op.gradient(), ref['gradient'], atol=2e-11, rtol=2e-11)
    assert torch.allclose(op.hvp(v), ref['H'] @ v, atol=2e-9, rtol=2e-9)
    assert torch.linalg.eigvalsh(ref['G']).min() >= -1e-10
    assert torch.linalg.norm(ref['H'] - ref['G']) > 1e-5


@pytest.mark.parametrize('kind', ['mse', 'ce'])
def test_microbatch_sum_matches_whole_operator(kind):
    _, _, _, a = make_op(kind)
    _, _, _, b = make_op(kind, 2)
    v = torch.linspace(-.5, .5, len(a.theta), dtype=torch.float64)
    assert torch.allclose(a.raw_ggn(v), b.raw_ggn(v), atol=1e-11)
    assert torch.allclose(a.gradient(), b.gradient(), atol=1e-11)


def test_snapshot_isolated_from_model_batch_mutation():
    model, x, y, op = make_op()
    before = op.gradient().clone()
    for p in model.parameters():
        p.data.add_(100)
    x.add_(100)
    y.sub_(100)
    assert torch.equal(op.gradient(), before)


def test_same_snapshot_repeatability_and_adjoint():
    _, _, _, op = make_op('ce')
    v = torch.randn_like(op.theta)
    w = torch.randn_like(op.prediction)
    assert torch.allclose((op.jvp(v)*w).sum(), v @ op.vjp(w), atol=1e-11)
    assert torch.equal(op.raw_ggn(v), op.raw_ggn(v))
    assert op.identity['loss_sha']
    assert op.identity['batch_sha']


def test_block_matvec_and_shared_weight_layout():
    spec = ModelSpec('transformer', 2, 4, 4, 4, heads=1, context=4, vocab_size=7, tie_weights=True)
    model = mod('models.registry').build_model(spec, 3).double()
    x = torch.tensor([[0, 1, 2, 3]])
    y = torch.tensor([[1, 2, 3, 4]])
    op = mod('curvature.operators').FrozenOperator(model, x, y, LossSpec('ce'))
    assert op.layout.numel == sum(p.numel() for p in model.parameters())
    assert any('head.weight' in aliases for aliases in op.layout.aliases.values())
    all_indices = torch.cat(op.layout.group_indices('coarse'))
    assert torch.equal(torch.sort(all_indices).values, torch.arange(op.layout.numel))
    ids = op.layout.group_indices('coarse')[1]
    v = torch.randn(len(ids), dtype=torch.float64)
    full = torch.zeros_like(op.theta); full[ids] = v
    assert torch.allclose(op.block_matvec(1, v, .1), (op.raw_ggn(full)+.1*full)[ids])
    ref = mod('audit.independent_reference').dense_reference(op, with_hessian=False)
    u = torch.randn_like(op.theta)
    assert torch.allclose(op.raw_ggn(u), ref['G']@u, atol=1e-9, rtol=1e-9)


def test_resnet_has_all_parameters_in_both_schemas():
    spec = ModelSpec('resnet', 8, 2, 192, 3, image_size=8, normalization='groupnorm')
    model = mod('models.registry').build_model(spec, 8).double()
    op = mod('curvature.operators').FrozenOperator(model, torch.randn(2,3,8,8,dtype=torch.float64), torch.tensor([0,2]), LossSpec('ce'))
    for group in ['coarse','fine']:
        ids = torch.cat(op.layout.group_indices(group))
        assert len(ids) == op.layout.numel
        assert len(torch.unique(ids)) == len(ids)
    ref = mod('audit.independent_reference').dense_reference(op, with_hessian=False, parameter_limit=4000)
    v = torch.randn_like(op.theta)
    assert torch.allclose(op.raw_ggn(v), ref['G']@v, atol=1e-8, rtol=1e-8)


def test_reverse_mode_fallback_matches_forward():
    _, _, _, op = make_op('ce')
    other = mod('curvature.operators').FrozenOperator(op.model, op.inputs, op.targets, op.loss, jvp_mode='reverse')
    v = torch.randn_like(op.theta)
    assert torch.allclose(op.raw_ggn(v), other.raw_ggn(v), atol=1e-10)
