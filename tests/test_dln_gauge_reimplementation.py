"""Regression tests for the NEW_REIMPLEMENTATION in reimplementation/dln_gauge (numpy only, fast)."""
import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "reimplementation", "dln_gauge"))
from dln import (block_metrics, flat, gauge_basis, ggn, hessian, jac_M, loss_grad,  # noqa: E402
                 orth_init, proj, shapes, unflat)


class TestDLNGauge(unittest.TestCase):
    def test_derivatives_match_finite_differences(self):
        rng = np.random.default_rng(0)
        shp = shapes(3, [4, 5], 2)
        Ws = [rng.standard_normal(s) for s in shp]
        X, Y = rng.standard_normal((3, 7)), rng.standard_normal((2, 7))
        th, eps = flat(Ws), 1e-6
        H = hessian(Ws, X, Y)
        Hfd = np.array([(loss_grad(th + eps * e, shp, X, Y)[1] - loss_grad(th - eps * e, shp, X, Y)[1]) / (2 * eps)
                        for e in np.eye(th.size)])
        self.assertLess(np.abs(H - Hfd).max() / np.abs(H).max(), 1e-7)
        self.assertLess(np.abs(jac_M(Ws) @ gauge_basis(Ws)).max(), 1e-12)

    def test_closed_form_plateau_square_orthogonal(self):
        L, d, N = 5, 3, 12
        rng = np.random.default_rng(1)
        shp = shapes(d, [d] * (L - 1), d)
        Ws = orth_init(shp, 1.0, rng)
        X = rng.standard_normal((d, N))
        G, JM = ggn(Ws, X, d)
        P0 = np.eye(G.shape[0]) - proj(JM.T)[0]
        Pg, r = proj(gauge_basis(Ws))
        self.assertEqual(r, (L - 1) * d * d)
        self.assertLess(np.linalg.norm(P0 - Pg), 1e-10)
        R = np.linalg.inv(G + 1e-9 * np.eye(G.shape[0]))
        b = block_metrics(R, [d * d] * L)
        np.testing.assert_allclose(b["rms_ratio"][1:], 1.0 / (L - 1), rtol=1e-6)
        self.assertAlmostEqual(b["offdiag"], 1.0 / L, places=6)

    def test_gradient_orthogonal_to_gauge(self):
        rng = np.random.default_rng(2)
        shp = shapes(3, [4, 4], 3)
        Ws = [rng.standard_normal(s) for s in shp]
        X, Y = rng.standard_normal((3, 9)), rng.standard_normal((3, 9))
        _, g = loss_grad(flat(Ws), shp, X, Y)
        Pg, _ = proj(gauge_basis(unflat(flat(Ws), shp)))
        self.assertLess(np.linalg.norm(Pg @ g) / np.linalg.norm(g), 1e-12)


if __name__ == "__main__":
    unittest.main()
