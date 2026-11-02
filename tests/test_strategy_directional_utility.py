"""Sanity checks for the investment-review diagnostic, not a science replication."""
import unittest
import numpy as np
from scripts.strategy_directional_utility import make, jacobian, counterexample, block_solve


class TestStrategyDirectionalUtility(unittest.TestCase):
    def test_two_dimensional_exact_value(self):
        x=counterexample(.9)
        self.assertAlmostEqual(x['offdiag_energy_mass'],.81/1.81,places=12)
        self.assertAlmostEqual(x['gradient_eigenvector_eta'],1.,places=12)
        self.assertAlmostEqual(x['gradient_axis_eta'],.19,places=12)

    def test_jacobian_small_finite_difference(self):
        weights,X=make(9,L=3,d=2,n=4)
        J,pred=jacobian(weights,X)
        eps=1e-6
        wp=weights.copy();wm=weights.copy()
        wp[0,0,0]+=eps;wm[0,0,0]-=eps
        def forward(ws):
            y=X.copy()
            for w in ws:y=y@w.T
            return y
        finite=((forward(wp)-forward(wm))/(2*eps)).reshape(-1)
        np.testing.assert_allclose(J[:,0],finite,rtol=2e-8,atol=2e-10)

    def test_block_solve(self):
        rng=np.random.default_rng(21)
        J=rng.standard_normal((7,3*4))
        g=rng.standard_normal(12)
        got=block_solve(J,g,lam=.05,d=2)
        want=np.empty_like(g)
        for i in range(3):
            sl=slice(i*4,(i+1)*4)
            want[sl]=np.linalg.solve(J[:,sl].T@J[:,sl]/7+.05*np.eye(4),g[sl])
        np.testing.assert_allclose(got,want,rtol=1e-11,atol=1e-11)

if __name__=='__main__':
    unittest.main()
