"""No historical files; fast, deterministic numerical G0 regression tests."""
import unittest
import numpy as np
from scripts.fresh_revalidation_g0 import cg_spd, dense_utility, sketch_inverse_blocks


class TestFreshG0(unittest.TestCase):
    def test_gradients_change_value_without_changing_Q(self):
        G = np.array([[.95,.9],[.9,.95]])
        a = dense_utility(G,np.array([1.,1.]),[1,1],.05)
        b = dense_utility(G,np.array([1.,0.]),[1,1],.05)
        self.assertAlmostEqual(a["eta"],1.,places=12)
        self.assertAlmostEqual(b["eta"],.19,places=12)
        self.assertAlmostEqual(b["delta"],.81,places=12)

    def test_psd_rank_deficiency_and_g_zero(self):
        G = np.ones((4,4))
        self.assertEqual(dense_utility(G,np.zeros(4),[2,2],.1)["status"],
                         "INELIGIBLE_ZERO_GRADIENT")
        a = dense_utility(G,np.ones(4),[2,2],.1,np.ones((1,4)))
        self.assertAlmostEqual(a["eta"],1.,places=12)
        self.assertAlmostEqual(a["E_task"],0.,places=12)

    def test_reject_indefinite_h_and_bad_damping(self):
        with self.assertRaises(ValueError):
            dense_utility(np.diag([-1.,2.]),np.ones(2),[1,1],.1)
        with self.assertRaises(ValueError):
            dense_utility(np.eye(2),np.ones(2),[1,1],0.)

    def test_cg_matches_dense(self):
        rng = np.random.default_rng(123)
        B = rng.normal(size=(7,7))
        Q = B.T@B+np.eye(7)
        v = rng.normal(size=7)
        x,err,success,_ = cg_spd(lambda y: Q@y,v)
        self.assertTrue(success)
        self.assertLess(err,1e-10)
        np.testing.assert_allclose(x,np.linalg.solve(Q,v),atol=1e-10,rtol=1e-10)

    def test_sketch_identity_exact_and_unequal_groups(self):
        a = sketch_inverse_blocks(lambda z:z,[1,2,3],16,seed=123)
        self.assertAlmostEqual(a["offdiag_mass_estimate"],0.,places=12)
        np.testing.assert_allclose(a["normalized_element_rms_by_distance"],[1.,0.,0.],atol=1e-12)

    def test_sketch_agrees_with_small_dense_inverse(self):
        Q = np.eye(8)+.2*np.ones((8,8))
        R = np.linalg.inv(Q)
        x = sketch_inverse_blocks(lambda z:np.linalg.solve(Q,z),[2,2,2,2],512,seed=20261102)
        exact = np.array([[np.linalg.norm(R[i*2:(i+1)*2,j*2:(j+1)*2])**2
                           for j in range(4)] for i in range(4)])
        np.testing.assert_allclose(np.asarray(x["energy_by_target_source"]),
                                   exact,atol=.015,rtol=.15)


if __name__ == "__main__":
    unittest.main()
