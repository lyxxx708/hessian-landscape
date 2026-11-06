"""Gate 3: independent reference tests for the Kronecker Block solvers, DLN operators, alpha-grid evaluator and pools.
Synthetic tests use only torch autograd / dense linear algebra as references; real-state tests use one S1 state."""
import math
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from genesis_next_v3 import env
env.configure_torch()
import numpy as np
import torch
from genesis_next_v3.dln_kron import DLN, cg_lean, best_ray
from genesis_next_v3.alpha_grid import PoolEval, evaluate_direction, pool_gradient, ALPHA_GRID, select_alpha, sign_of

torch.manual_seed(0)


def random_dln(depth=4, din=5, width=6, dout=3, B=11, scale=0.7):
    W = [torch.randn(width if i < depth - 1 else dout, din if i == 0 else width, dtype=torch.float64) * scale
         for i in range(depth)]
    X = torch.randn(B, din, dtype=torch.float64)
    Y = torch.randn(B, dout, dtype=torch.float64)
    return W, X, Y


def autograd_dense(W, X, Y):
    shapes = [w.shape for w in W]
    sizes = [w.numel() for w in W]
    theta = torch.cat([w.reshape(-1) for w in W]).requires_grad_(True)

    def unflat(t):
        out, o = [], 0
        for s, n in zip(shapes, sizes):
            out.append(t[o:o + n].view(s))
            o += n
        return out

    def f(t):
        return DLN.forward_weights(unflat(t), X).reshape(-1)

    J = torch.autograd.functional.jacobian(f, theta)
    loss = lambda t: (f(t) - Y.reshape(-1)).square().sum() / (2 * Y.numel())
    g = torch.autograd.grad(loss(theta), theta)[0]
    H = torch.autograd.functional.hessian(loss, theta)
    return (J.T @ J / Y.numel()).detach(), g.detach(), H.detach(), sizes


class KroneckerExactness(unittest.TestCase):
    def test_gradient_and_ggnv_match_autograd(self):
        for depth in (1, 2, 4, 8):
            W, X, Y = random_dln(depth=depth)
            m = DLN(W, X, Y)
            G, g, _, _ = autograd_dense(W, X, Y)
            self.assertLess(float((m.gradient() - g).norm() / g.norm()), 1e-12)
            v = torch.randn(m.n, dtype=torch.float64)
            self.assertLess(float((m.ggn_vec(v) - G @ v).norm() / (G @ v).norm()), 1e-12)

    def test_block_direct_and_local_cg_equal_dense_block_solve(self):
        for depth, lam in ((2, 1e-3), (4, 1e-2), (8, 1e-4), (4, 10.0)):
            W, X, Y = random_dln(depth=depth)
            m = DLN(W, X, Y)
            G, g, _, sizes = autograd_dense(W, X, Y)
            d = m.block_direct(g, lam)
            dl, _ = m.block_local_cg(g, lam, rtol=1e-14, max_iter=10000)
            o = 0
            for n in sizes:
                sl = slice(o, o + n)
                A = G[sl, sl] + lam * torch.eye(n, dtype=torch.float64)
                ref = -torch.linalg.solve(A, g[sl])
                e = torch.linalg.eigvalsh(A)
                cond = float(e.max() / e.min())
                # backward stability, then forward error at the conditioning-implied level
                self.assertLess(float((A @ d[sl] + g[sl]).norm() / g[sl].norm()), 1e-13)
                self.assertLess(float((d[sl] - ref).norm() / ref.norm()), 100 * cond * 2.2e-16)
                self.assertLess(float((dl[sl] - ref).norm() / ref.norm()), max(1e-8, 1e3 * cond * 2.2e-16))
                o += n

    def test_block_kronecker_form_is_the_dense_diagonal_block(self):
        W, X, Y = random_dln(depth=3)
        m = DLN(W, X, Y)
        G, _, _, sizes = autograd_dense(W, X, Y)
        f = m.build_factors()
        o = 0
        for l, n in enumerate(sizes):
            K = torch.kron(f[l]['S'], f[l]['T'])  # row-major vec(E): (S E T)_ij = sum S_ia E_ab T_bj
            self.assertLess(float((K - G[o:o + n, o:o + n]).norm() / G[o:o + n, o:o + n].norm()), 1e-12)
            o += n

    def test_singular_factors_and_rank_deficient_inputs(self):
        # B < d_in makes T rank-deficient; lambda keeps the block SPD; still exact.
        W, X, Y = random_dln(depth=3, din=8, width=8, B=3)
        m = DLN(W, X, Y)
        G, g, _, sizes = autograd_dense(W, X, Y)
        lam = 1e-6
        d = m.block_direct(g, lam)
        o = 0
        for n in sizes:
            sl = slice(o, o + n)
            r = -torch.linalg.solve(G[sl, sl] + lam * torch.eye(n, dtype=torch.float64), g[sl])
            self.assertLess(float((d[sl] - r).norm() / r.norm()), 1e-7)
            o += n

    def test_cg_lean_matches_dense_and_counts_matvecs(self):
        W, X, Y = random_dln(depth=4)
        m = DLN(W, X, Y)
        G, g, _, _ = autograd_dense(W, X, Y)
        lam = 1e-2
        Qm = G + lam * torch.eye(m.n, dtype=torch.float64)
        calls = []
        Q = lambda v: (calls.append(1), m.ggn_vec(v) + lam * v)[1]
        x, r = cg_lean(Q, -m.gradient(), 5)
        self.assertEqual(r['matvecs'], 5)
        self.assertEqual(len(calls), 5)
        x, r = cg_lean(Q, -m.gradient(), 4000, rtol=1e-12)
        ref = -torch.linalg.solve(Qm, g)
        self.assertLess(float((x - ref).norm() / ref.norm()), 1e-8)
        a, F = best_ray(g, ref, Qm @ ref)
        self.assertAlmostEqual(a, 1.0, places=8)


class AlphaGridReferences(unittest.TestCase):
    def test_dL_slope_and_curvature_against_autograd_and_polynomial(self):
        W, X, Y = random_dln(depth=4, B=40)
        m = DLN(W, X, Y)
        G, g, H, _ = autograd_dense(W, X, Y)
        d = torch.randn(m.n, dtype=torch.float64) * 1e-2
        E = m.split(d)
        ev = evaluate_direction(W, E, {'P': (X, Y)}, {'P': [(0, 20), (20, 40)]})['P']
        self.assertAlmostEqual(ev['slope'], -float(g @ d), delta=1e-14 + 1e-10 * abs(float(g @ d)))
        self.assertAlmostEqual(ev['slope_gradient_formula'], -float(g @ d), delta=1e-14 + 1e-10 * abs(float(g @ d)))
        self.assertAlmostEqual(ev['curv_H'], float(d @ H @ d), delta=1e-12 * abs(float(d @ H @ d)) + 1e-18)
        self.assertAlmostEqual(ev['curv_GGN'], float(d @ G @ d), delta=1e-12 * abs(float(d @ G @ d)) + 1e-18)
        L0 = m.loss_at()
        for a, dl in zip(ALPHA_GRID, ev['dL']):
            ref = m.loss_at(m.theta() + a * d) - L0
            self.assertLess(abs(dl - ref), 1e-15 + 1e-9 * abs(ref))
        # group decomposition: whole-pool dL is the mean of equal-size group dLs
        for i in range(len(ALPHA_GRID)):
            self.assertAlmostEqual(ev['dL'][i], 0.5 * sum(gr['dL'][i] for gr in ev['groups']), delta=1e-16 + 1e-12 * abs(ev['dL'][i]))

    def test_small_alpha_gain_matches_taylor(self):
        W, X, Y = random_dln(depth=4, B=40)
        m = DLN(W, X, Y)
        d = -m.gradient()
        ev = evaluate_direction(W, m.split(d), {'P': (X, Y)}, {})['P']
        a = 1e-5
        gain = -ev['dL'][ALPHA_GRID.index(a)]
        pred2 = a * ev['slope'] - 0.5 * a * a * ev['curv_H']
        self.assertLess(abs(gain - pred2), 1e-6 * abs(gain))

    def test_sign_resolution_is_conservative(self):
        self.assertEqual(sign_of(1e-20, 1e-18), 0)
        self.assertEqual(sign_of(-2e-18, 1e-18), -1)
        self.assertEqual(sign_of(2e-18, 1e-18), 1)
        W, X, Y = random_dln(depth=4, B=40)
        m = DLN(W, X, Y)
        d = torch.randn(m.n, dtype=torch.float64)
        ev = evaluate_direction(W, m.split(d), {'P': (X, Y)}, {})['P']
        self.assertEqual(ev['sign_gain'][0], 0)
        self.assertTrue(all(b >= 0 for b in ev['bound']))

    def test_select_alpha_v2_rule(self):
        grid = [0.0, 0.1, 1.0]
        self.assertEqual(select_alpha([1.0, 0.5, 0.5], grid, grid), 0.1)
        self.assertEqual(select_alpha([1.0, 2.0, 3.0], grid, grid), 0.0)


class RealState(unittest.TestCase):
    """One real S1 state (read-only): pools are deterministic/disjoint; teacher reproduces; operators agree."""

    @classmethod
    def setUpClass(cls):
        from genesis_next_v3.source import next_v2_states, load_state, weights_of
        states, _ = next_v2_states()
        cls.state = [s for s in states if s['setting_id'] == 'dln_d4_w16_orthogonal_balanced_c1'][0]
        cls.op, cls.val, cls.pv, cls.bundle, cls.orig, cls.ids = load_state(cls.state)
        cls.m = DLN(weights_of(cls.op), cls.op.inputs, cls.op.targets)

    def test_pools_deterministic_and_disjoint(self):
        from genesis_next_v3.pools import build_pools
        p1, n1, gr, id1, t512 = build_pools(self.state['run'], self.bundle, self.ids)
        p2, n2, _, id2, _ = build_pools(self.state['run'], self.bundle, self.ids)
        self.assertEqual(id1, id2)
        self.assertEqual(id1['t512_overlap_with_t32'], 0)
        self.assertEqual(len(set(t512.tolist())), 512)
        self.assertTrue(torch.equal(p1['T32'][0], self.op.inputs))
        self.assertEqual(p1['E8192'][0].shape[0], 8192)
        # E pool is new data: no row coincides with any split row
        tr = set(map(tuple, self.bundle.splits['train'][0][:, :2].tolist()))
        self.assertFalse(any(tuple(r) in tr for r in n1['E8192'][0][:, :2].tolist()))
        # teacher relation holds on the generated pool
        _, _, teacher = __import__('genesis_next_v3.pools', fromlist=['x']).regenerate_teacher(self.state['run'], self.bundle)
        self.assertLess(float((n1['E8192'][0] @ teacher.T - n1['E8192'][1]).abs().max()), 1e-12)

    def test_real_operators_and_hvp(self):
        op, m = self.op, self.m
        v = torch.randn(m.n, dtype=torch.float64)
        self.assertLess(float((m.ggn_vec(v) - op.raw_ggn(v)).norm() / op.raw_ggn(v).norm()), 1e-12)
        ev = evaluate_direction(m.W, m.split(v * 1e-3), {'T': (op.inputs, op.targets)}, {})['T']
        dHd = float((v * 1e-3) @ op.hvp(v * 1e-3))
        self.assertLess(abs(ev['curv_H'] - dHd), 1e-10 * abs(dHd) + 1e-20)
        self.assertLess(abs(ev['slope'] + float(op.gradient() @ (v * 1e-3))), 1e-14)


if __name__ == '__main__':
    unittest.main(verbosity=2)
