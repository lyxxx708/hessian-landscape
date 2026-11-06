"""Unit tests for the analytic population oracle: python -B -m unittest oracle/test_oracle.py (from the v3 root)."""
import math
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
import torch
import pop_oracle as po

torch.set_default_dtype(torch.float64)


def task(seed, din=16, dout=16, width=16, depth=4, cond=100.0):
    g = torch.Generator().manual_seed(seed)
    eig = torch.logspace(0, math.log10(cond), din)
    eig = eig / eig.mean()
    rot, _ = torch.linalg.qr(torch.randn(din, din, generator=g))
    A = torch.randn(dout, din, generator=g) / math.sqrt(din)
    dims = [din] + [width] * (depth - 1) + [dout]
    W = [torch.randn(dims[i + 1], dims[i], generator=g) / math.sqrt(dims[i]) for i in range(depth)]
    E = [torch.randn_like(w) * 0.1 for w in W]
    return eig, rot, A, W, E, g


class OracleTests(unittest.TestCase):
    def test_matrix_poly_matches_product(self):
        eig, rot, A, W, E, _ = task(1, depth=8)
        C = po.matrix_poly(W, E)
        for a in (0.0, 0.37, 2.9):
            M = sum(a ** k * c for k, c in enumerate(C))
            self.assertLess(float((M - po.product(po.ray(W, E, a))).norm() / M.norm()), 1e-12)

    def test_population_paths_and_polynomial_agree(self):
        eig, rot, A, W, E, _ = task(2)
        pop = po.Population(eig, rot, A)
        self.assertLess(abs(pop.risk(W) - pop.risk_via_dln(W)) / pop.risk(W), 1e-13)
        p = np.polynomial.Polynomial(pop.poly(W, E))
        for a in (0.0, 0.1, 1.0, 3.0):
            self.assertLess(abs(p(a) - pop.risk(po.ray(W, E, a))) / pop.risk(po.ray(W, E, a)), 1e-10)

    def test_population_equals_large_monte_carlo(self):
        eig, rot, A, W, E, g = task(3)
        pop = po.Population(eig, rot, A)
        x = (torch.randn(200000, len(eig), generator=g) * eig.sqrt()) @ rot.T
        pool = po.Pool(x, x @ A.T)
        l = pool.per_sample(W)
        se = float(l.std() / math.sqrt(len(l)))
        self.assertLess(abs(float(l.mean()) - pop.risk(W)), 5 * se)

    def test_exact_minimiser_one_layer(self):
        # L = 1: R(a) is quadratic, so a* = r1-slope / curvature in closed form
        eig, rot, A, W, E, _ = task(4, depth=1)
        pop = po.Population(eig, rot, A)
        E = [-(W[0] - A) * 0.7]
        r = pop.poly(W, E)
        a_star = -r[1] / (2 * r[2])
        o = po.minimize_on_ray(pop, W, E)
        self.assertLess(abs(o['alpha_opt'] - a_star) / a_star, 1e-10)
        self.assertLess(abs(o['alpha_opt'] - 1 / 0.7), 1e-8)

    def test_ascent_direction_gives_zero_step(self):
        eig, rot, A, W, E, _ = task(5, depth=1)
        pop = po.Population(eig, rot, A)
        o = po.minimize_on_ray(pop, W, [(W[0] - A)])
        self.assertEqual(o['alpha_opt'], 0.0)

    def test_pool_polynomial_and_minimiser(self):
        eig, rot, A, W, E, g = task(6, depth=8)
        x = (torch.randn(512, len(eig), generator=g) * eig.sqrt()) @ rot.T
        pool = po.Pool(x, x @ A.T)
        o = po.minimize_on_ray(pool, W, E)
        f = lambda a: pool.risk(po.ray(W, E, a))
        grid = np.linspace(0, po.ALPHA_HI, 30001)
        self.assertLessEqual(o['R_opt'], min(f(a) for a in grid[::10]) + 1e-15)
        self.assertLess(o['poly_vs_direct_rel'], 1e-8)


if __name__ == '__main__':
    unittest.main()
