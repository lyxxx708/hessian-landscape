import importlib
import pytest
import torch
import numpy as np
from genesis_gpu.contracts import ModelSpec, LossSpec
from genesis_gpu.models.registry import build_model
from genesis_gpu.curvature.operators import FrozenOperator
from genesis_gpu.audit.independent_reference import dense_reference


def mod(name):
    try:
        return importlib.import_module('genesis_gpu.'+name)
    except ModuleNotFoundError as exc:
        pytest.fail(f'Required module not implemented: {name}: {exc}')


def op_tiny(kind='mse'):
    torch.manual_seed(32)
    spec=ModelSpec('dln',3,2,2,2) if kind=='mse' else ModelSpec('mlp',2,3,2,3,activation='tanh')
    m=build_model(spec,23).double()
    x=torch.randn(3,2,dtype=torch.float64)
    y=torch.randn(3,2,dtype=torch.float64) if kind=='mse' else torch.tensor([0,2,1])
    return FrozenOperator(m,x,y,LossSpec(kind))


def test_cg_true_residual_and_indefinite_detection():
    cg=mod('solvers.cg').cg
    torch.manual_seed(5)
    A=torch.randn(8,8,dtype=torch.float64);Q=A.T@A+.1*torch.eye(8,dtype=A.dtype)
    b=torch.randn(8,dtype=A.dtype)
    r=cg(lambda x:Q@x,b,rtol=1e-10,max_iter=100)
    assert r.converged
    assert r.true_residual==pytest.approx(float((Q@r.direction-b).norm()/b.norm()))
    assert torch.allclose(r.direction,torch.linalg.solve(Q,b),rtol=1e-9,atol=1e-10)
    bad=cg(lambda x:-x,b,rtol=1e-10,max_iter=10)
    assert not bad.converged and bad.status=='NON_SPD'
    zero=cg(lambda x:Q@x,torch.zeros_like(b))
    assert zero.converged and zero.iterations==0


def test_block_and_dual_match_dense():
    cg=mod('solvers.cg');dual=mod('curvature.dual_solve')
    op=op_tiny('ce');r=dense_reference(op,with_hessian=False)
    lam=.2;g=op.gradient();Q=r['G']+lam*torch.eye(len(g),dtype=g.dtype)
    got,receipts=cg.block_solve(op,-g,lam,'coarse',rtol=1e-11,max_iter=100)
    for ids in op.layout.group_indices('coarse'):
        assert torch.allclose(got[ids],torch.linalg.solve(Q[ids][:,ids],-g[ids]),atol=1e-10)
    assert all(s.converged for s in receipts)
    x=dual.dual_solve(r['J'],r['W'],-g,lam)
    assert torch.allclose(x,torch.linalg.solve(Q,-g),atol=1e-10)


def test_same_matrix_different_gradient_utility():
    utility=mod('science.utility').quadratic_utility
    Q=torch.tensor([[1.,.9],[.9,1.]],dtype=torch.float64)
    for g,want in [(torch.ones(2,dtype=Q.dtype),1.),(torch.tensor([1.,0.],dtype=Q.dtype),.19)]:
        full=-torch.linalg.solve(Q,g);block=-g
        result=utility(g,full,block,Q@block)
        assert result['eta']==pytest.approx(want,abs=1e-12)
    invalid=utility(torch.zeros(2),torch.zeros(2),torch.zeros(2),torch.zeros(2))
    assert invalid['status']=='INELIGIBLE_ZERO_GRADIENT' and invalid['delta'] is None


def test_distinct_task_alpha_and_validation_not_refit():
    metric=mod('science.utility').task_response_metrics
    op=op_tiny('ce')
    r=dense_reference(op,with_hessian=False);g=op.gradient();lam=.03
    Q=r['G']+lam*torch.eye(len(g),dtype=g.dtype)
    full=-torch.linalg.solve(Q,g)
    block=-g
    val=op.validation_operator(op.inputs*.7,torch.tensor([2,1,0]))
    result=metric(op,full,block,val)
    u=op.jvp(full);v=op.jvp(block);W=r['W']
    expected=float((u.flatten()@W@v.flatten())/(v.flatten()@W@v.flatten()))
    assert result['alpha_task']==pytest.approx(max(0,expected),abs=1e-12)
    uv=val.jvp(full);vv=val.jvp(block)
    e=uv-result['alpha_task']*vv
    want=torch.sqrt((e*val.metric_action(e)).sum()/(uv*val.metric_action(uv)).sum()).item()
    assert result['E_val']==pytest.approx(want,abs=1e-10)


def test_full_utility_qualified_and_immutable():
    evaluate=mod('science.utility').evaluate_utility
    op=op_tiny('mse')
    old=op.theta.clone()
    result,vectors=evaluate(op,.1,rtol=1e-9,max_iter=120,validation=op.validation_operator(op.inputs*.9,op.targets),line_search=[0.,.1,1.])
    assert result['status']=='NUMERIC_VALID'
    assert 0<=result['delta']<=1
    assert result['delta_stability']<=.005
    assert result['alpha_task'] is not None
    assert torch.equal(old,op.theta)
    assert vectors['full'].shape==old.shape


def test_structure_nonuniform_block_normalization():
    profile=mod('science.structure').profile
    E=np.array([[2.,.02],[.02,8.]])
    got=profile(E,[2,4])
    expected=np.sqrt(.04/(2*2*4))/np.sqrt(10/(4+16))
    assert got['normalized_element_rms'][1]==pytest.approx(expected)
    assert got['offdiag_mass']==pytest.approx(.04/10.04)
    assert got['tail_status']=='SHORT_DEPTH'


def test_block_probe_matches_dense_and_identity_correction():
    sketch=mod('sketches.block_probe').estimate_blocks
    from genesis_gpu.solvers.cg import cg
    n=6;dtype=torch.float64
    G=.2*torch.ones(n,n,dtype=dtype);lam=.5;Q=G+lam*torch.eye(n,dtype=dtype)
    ids=[torch.arange(0,2),torch.arange(2,4),torch.arange(4,6)]
    result=sketch(lambda x:cg(lambda z:Q@z,x,rtol=1e-12,max_iter=40),lambda x:G@x,ids,lam,
                  dtype=dtype,device='cpu',seed=41,schedule=[128],relative_halfwidth=1.,bootstrap=100,independent_final=True)
    R=torch.linalg.inv(Q);C=R-torch.eye(n,dtype=dtype)/lam
    exact=np.array([[float((R[i][:,j]**2).sum()) for j in ids] for i in ids])
    np.testing.assert_allclose(result['energy_mean'],exact,rtol=.4,atol=.03)
    exact_c=np.array([[float((C[i][:,j]**2).sum()) for j in ids] for i in ids])
    np.testing.assert_allclose(result['correction_energy_mean'],exact_c,rtol=.4,atol=.03)
    exact_g=np.array([[float((G[i][:,j]**2).sum()) for j in ids] for i in ids])
    np.testing.assert_allclose(result['GGN_energy_mean'],exact_g,rtol=.4,atol=.03)
    assert result['GGN_profile']['normalized_element_rms'] is not None
    assert result['independent_final'] is True
    assert len(result['probe_records'])==3*128
    assert max(r['true_residual'] for r in result['probe_records'])<1e-10


def test_mechanism_matches_dln_rank_and_gauge_output():
    mechanism=mod('science.mechanism')
    op=op_tiny('mse')
    result=mechanism.dense_mechanism(op,[.01,.1],parameter_limit=100)
    assert result['rank_G']<=4
    assert result['null_gradient_relative']<1e-8
    assert result['finite_lambda_horizontal_nonzero'] is True
    gauge=mechanism.dln_gauge_controls(op,scales=(.5,2.))
    assert max(r['relative_output_drift'] for r in gauge)<1e-12
    assert any(r['parameter_norm_ratio']>1 for r in gauge)


def test_global_flat_matrix_is_not_architecture_order_evidence():
    controls=mod('science.controls')
    E=np.ones((10,10));np.fill_diagonal(E,100.)
    result=controls.order_null(E,[2]*10,permutations=40,seed=9)
    assert result['p_flatness']==1.


def test_cheap_block_energy_baseline_counts_work_and_does_not_use_inverse():
    from genesis_gpu.science.utility import cheap_block_energy
    op=op_tiny('mse');before=op.matvec_count
    r=cheap_block_energy(op,probes=3)
    assert r['matvecs']==op.matvec_count-before and r['matvecs']>0
    assert len(r['raw_total_energy'])==3 and r['uses_full_inverse'] is False
    assert np.isfinite(r['offdiag_fraction_proxy'])


def test_predictor_includes_matched_cost_and_block_energy_competitors():
    from genesis_gpu.science.predictor import FEATURES,BASELINES
    assert 'matched_gain_per_gradient_sq' in FEATURES
    assert 'block_energy_proxy' in FEATURES
    assert 'matched_cg' in BASELINES and 'block_energy' in BASELINES
