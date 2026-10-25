"""Tests for the GitHub-portable P0 runner (NumPy-only in CI)."""
import unittest
import numpy as np
from scripts.p0_repro import make_data, matrices, summarize


class TestP0Runner(unittest.TestCase):
    def test_zero_residual_rank_and_psd(self):
        w,x=make_data(3,L=4,d=3,n=8)
        pred=x.copy()
        for wi in w:pred=pred@wi.T
        J,G,S,H,res=matrices(w,x,pred)
        self.assertLess(np.linalg.norm(S),1e-12)
        self.assertLessEqual(np.linalg.matrix_rank(J,tol=1e-10),9)
        self.assertGreaterEqual(float(np.linalg.eigvalsh(H).min()),-1e-12)

    def test_energy_consistency_and_zero_offdiag(self):
        norms,rms,mass=summarize(np.eye(16),L=4,d=2)
        self.assertAlmostEqual(float(mass[0]),1.,places=12)
        self.assertAlmostEqual(float(rms[0]),1.,places=12)
        self.assertTrue(np.allclose(rms[1:],0))

    def test_hessian_against_torch_if_available(self):
        try:import torch
        except ImportError:self.skipTest('torch optional for independent autodiff')
        L,d,n=3,2,3
        w,x=make_data(13,L,d,n)
        target=x.copy()
        J,G,S,H,_=matrices(w,x,target)
        xt=torch.tensor(x,dtype=torch.float64)
        tt=torch.tensor(target,dtype=torch.float64)
        flat=torch.tensor(w.reshape(-1),dtype=torch.float64)
        def loss(theta):
            pred=xt
            for wi in theta.reshape(L,d,d):pred=pred@wi.T
            return .5*((pred-tt)**2).mean()
        expected=torch.autograd.functional.hessian(loss,flat).numpy()
        np.testing.assert_allclose(H,expected,atol=1e-11,rtol=1e-11)

if __name__=='__main__':unittest.main()
