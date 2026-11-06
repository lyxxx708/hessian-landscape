"""The three fixed T32 directions (Full, Block best-ray, CG8 best-ray) plus their independent reference checks."""
from __future__ import annotations
import copy
import numpy as np
import torch
from .dln_kron import DLN, cg_lean, best_ray, quad_gain

DIRECTION_RTOL = 1e-7          # protocol B1 acceptance for every new Block direction vs dense
FB_REL_TOL, FB_ABS_TOL = 1e-8, 1e-14   # best-ray F_B agreement (relative to F*, absolute fallback)
OPERATOR_RTOL = 1e-10          # GGN operator equality on predeclared random vectors
OPERATOR_PROBE_SEED = 20261106


def rel(a, b):
    a = torch.as_tensor(a)
    b = torch.as_tensor(b)
    return float((a - b).norm() / b.norm().clamp_min(1e-300))


def dense_reference(op, with_hessian=False, limit_out=None):
    """Independent reverse-autograd dense G (v2 audit code path, not FrozenOperator.raw_ggn)."""
    from genesis_gpu.audit.independent_reference import dense_reference as dr
    return dr(op, with_hessian=with_hessian, parameter_limit=4096,
              output_limit=limit_out or op.prediction.numel())


def dense_from_dln(m: DLN):
    """Second dense path for large batches: explicit Jacobian columns from the closed-form output JVP."""
    m.build_cache()
    eye = torch.eye(m.n, dtype=m.X.dtype)
    J = torch.stack([m.output_jvp(eye[i]).reshape(-1) for i in range(m.n)], 1)
    return J.T @ J / m.N


def compute_directions(op, m: DLN, lam, groups, dense_G=None, dense_g=None, with_cg_v2=True):
    """Return directions + qualification record. groups: list of index tensors (coarse = per layer)."""
    g = op.gradient()
    rec = {'lambda_absolute': lam}
    m.build_cache()
    m.build_factors()
    Q = lambda v: m.ggn_vec(v) + lam * v
    G = dense_G.cpu().numpy() if isinstance(dense_G, torch.Tensor) else dense_G
    gd = dense_g.cpu().numpy() if isinstance(dense_g, torch.Tensor) else dense_g
    Qd = G + lam * np.eye(len(gd))
    xF = np.linalg.solve(Qd, -gd)
    full = torch.as_tensor(xF, dtype=torch.float64)
    rec['full_dense_relative_residual'] = float(np.linalg.norm(Qd @ xF + gd) / np.linalg.norm(gd))
    rec['gradient_dense_vs_operator'] = rel(torch.as_tensor(gd), g)
    if with_cg_v2:
        from genesis_next.solvers import cg as cg_v2
        xc, rc = cg_v2(lambda v: op.matvec(v, lam), -g, rtol=1e-10, max_iter=4000)
        rec['full_cg_v2_operator_direction_error'] = rel(xc, full)
        rec['full_cg_v2_converged'] = rc['converged']
        rec['full_cg_v2_matvecs'] = rc['matvecs']
    # Block: Kronecker direct and dense block references
    bK = m.block_direct(g, lam)
    bD = np.zeros_like(gd)
    for idx in groups:
        ii = idx.cpu().numpy()
        bD[ii] = -np.linalg.solve(Qd[np.ix_(ii, ii)], gd[ii])
    conds, kres = [], []
    for idx in groups:
        ii = idx.cpu().numpy()
        A = Qd[np.ix_(ii, ii)]
        e = np.linalg.eigvalsh(A)
        conds.append(float(e.max() / e.min()))
        kres.append(float(np.linalg.norm(A @ bK.numpy()[ii] + gd[ii]) / np.linalg.norm(gd[ii])))
    rec['block_condition_numbers'] = conds
    rec['block_kron_direct_relative_residual'] = kres
    bD = torch.as_tensor(bD)
    bL, local_iters = m.block_local_cg(g, lam, rtol=1e-13, max_iter=5000)
    rec['block_kron_direct_vs_dense'] = rel(bK, bD)
    rec['block_kron_localcg_vs_dense'] = rel(bL, bD)
    rec['block_kron_localcg_iterations'] = local_iters
    # Operators on predeclared random vectors
    gen = torch.Generator()
    gen.manual_seed(OPERATOR_PROBE_SEED)
    errs = []
    for _ in range(3):
        v = torch.randn(m.n, generator=gen, dtype=torch.float64)
        a = m.ggn_vec(v)
        errs.append({'dln_vs_v2_operator': rel(a, op.raw_ggn(v)),
                     'dln_vs_dense': rel(a, torch.as_tensor(G @ v.numpy()))})
    rec['operator_checks'] = errs
    # Quadratic quantities (dense = reference)
    gt = torch.as_tensor(gd)
    QdT = lambda v: torch.as_tensor(Qd @ v.numpy())
    Fstar = quad_gain(gt, full, QdT(full))
    aB, FB = best_ray(gt, bK, QdT(bK))
    aBd, FBd = best_ray(gt, bD, QdT(bD))
    rec.update(F_star=Fstar, F_block=FB, F_block_dense=FBd, delta=1 - FB / Fstar if Fstar > 0 else None,
               block_ray_scale=aB)
    rec['F_block_agreement'] = abs(FB - FBd) <= FB_REL_TOL * abs(Fstar) + FB_ABS_TOL
    # CG8 (explicit DLN GGNv, v3 lean CG), best-ray scaled with one charged Qd
    x8, r8 = cg_lean(Q, -g, 8)
    a8, F8 = best_ray(g, x8, Q(x8))
    rec['cg8'] = {**r8, 'best_ray_scale': a8, 'F_ray': F8, 'F_raw': quad_gain(g, x8, Q(x8)),
                  'gain_ratio_raw': quad_gain(g, x8, Q(x8)) / Fstar}
    if with_cg_v2:
        x8v, r8v = cg_v2(lambda v: op.matvec(v, lam), -g, rtol=1e-8, max_iter=8)
        rec['cg8']['vs_next_v2_cg8_direction'] = rel(x8, x8v)
    ok = (rec['block_kron_direct_vs_dense'] <= DIRECTION_RTOL and rec['F_block_agreement']
          and max(max(e.values()) for e in errs) <= OPERATOR_RTOL and rec['full_dense_relative_residual'] <= 1e-10
          and rec.get('full_cg_v2_operator_direction_error', 0) <= 1e-6)
    rec['status'] = 'QUALIFIED' if ok else 'NUMERIC_UNRESOLVED'
    dirs = {'Full': full, 'Block': aB * bK, 'CG8': a8 * x8, 'Block_raw': bK, 'CG8_raw': x8}
    return dirs, rec, g
