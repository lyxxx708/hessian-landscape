import unittest
import tempfile
import json
from pathlib import Path
import numpy as np

class NumericTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from genesis_next import numerics
        cls.n = numerics

    def test_block_utility_dense(self):
        G=np.array([[2.,.8],[.8,1.]])
        g=np.array([1.,-.4]); Q=G+.1*np.eye(2)
        d=-np.linalg.solve(Q,g); b=-g/np.diag(Q)
        r=self.n.ray_utility(Q,g,d,b)
        self.assertGreater(r['delta'],0)
        self.assertLess(r['delta'],1)
        self.assertAlmostEqual(r['F_star'],float(.5*g@np.linalg.solve(Q,g)))

    def test_zero_gradient_is_not_negative_result(self):
        r=self.n.ray_utility(np.eye(2),np.zeros(2),np.zeros(2),np.zeros(2))
        self.assertEqual(r['status'],'ZERO_GRADIENT_UNASSESSED')
        self.assertIsNone(r['delta'])

    def test_wrong_reference_rejected(self):
        with self.assertRaises(ValueError):
            self.n.ray_utility(np.eye(2),np.ones(2),-2*np.ones(2),-np.ones(2))

    def test_null_norm_uses_squares(self):
        G=np.diag([0.,0.,1.]); g=np.array([0.,0.,1.])
        r=self.n.dense_geometry(G,g,.001,[[0],[1],[2]],rank_rtol=1e-8)
        self.assertGreater(r['null_energy_fraction'],.999)
        self.assertLess(r['gradient_null_fraction'],1e-12)
        self.assertEqual(r['rank'],1)
        self.assertAlmostEqual(r['spectral_gain_weights_sum'],1)

    def test_hessian_negative_count_has_scale(self):
        G=np.diag([0.,1.]); H=np.diag([-1e-12,1.])
        r=self.n.hessian_diagnostics(G,H,1e-8)
        self.assertEqual(r['negative_certified_count'],0)
        self.assertEqual(r['ambiguous_count'],1)

    def test_covariant_gauge_recovery(self):
        G=np.array([[2.,.7],[.7,1.]])
        r=self.n.gauge_diagnostic(G,np.array([1.,-1.]),.1,[[0],[1]],np.array([10.,.1]))
        self.assertLess(r['covariant_direction_error'],1e-12)
        self.assertLess(r['covariant_delta_error'],1e-12)
        self.assertGreater(r['isotropic_direction_error'],.01)

    def test_duplicate_partition_rejected(self):
        with self.assertRaises(ValueError):
            self.n.dense_geometry(np.eye(3),np.ones(3),.1,[[0,1],[1,2]])

class IOTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from genesis_next import io_utils
        cls.io=io_utils

    def test_output_not_in_source(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)
            with self.assertRaises(ValueError): self.io.assert_separate(p/'x', [p])
            with self.assertRaises(ValueError): self.io.assert_separate(p, [p/'x'])
            self.io.assert_separate(p/'out',[p/'in'])

    def test_path_traversal(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError): self.io.safe_join(Path(d),'../evil')
            with self.assertRaises(ValueError): self.io.safe_join(Path(d),'/absolute')

    def test_atomic_json_no_nan(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'x.json'
            self.io.write_json(p,{'v':1})
            with self.assertRaises(ValueError):self.io.write_json(p,{'v':float('nan')})
            self.assertEqual(json.loads(p.read_text())['v'],1)

    def test_seed_preserved(self):
        from genesis_next.snapshot import aggregate_seeds
        seed='9223372036854775001'
        rows=[{'setting_id':'x','seed':seed,'gamma':'.01','checkpoint_index':str(i),
               'schema':'coarse','state':'COMPLETE','target_delta':str(i/10)} for i in [1,2,3]]
        r=aggregate_seeds(rows)
        self.assertEqual(r[0]['seed'],seed)
        self.assertEqual(r[0]['delta'],.2)

    def test_partial_seed_excluded(self):
        from genesis_next.snapshot import aggregate_seeds
        rows=[{'setting_id':'x','seed':'1','gamma':'.01','checkpoint_index':'1',
               'schema':'coarse','state':'COMPLETE','target_delta':'.2'}]
        self.assertEqual(aggregate_seeds(rows),[])

    def test_duplicate_checkpoint_fails(self):
        from genesis_next.snapshot import aggregate_seeds
        x={'setting_id':'x','seed':'1','gamma':'.01','checkpoint_index':'1',
           'schema':'coarse','state':'COMPLETE','target_delta':'.2'}
        with self.assertRaises(ValueError):aggregate_seeds([x,x])

    def test_s2_rejected(self):
        from genesis_next.snapshot import aggregate_seeds
        with self.assertRaises(ValueError):aggregate_seeds([{'stage':'s2'}])

class CGTests(unittest.TestCase):
    def test_dense_cpu_and_budget(self):
        import torch
        from genesis_next.solvers import cg
        A=torch.tensor([[2.,.3],[.3,1.]],dtype=torch.float64)
        b=torch.ones(2,dtype=torch.float64)
        x,r=cg(lambda x:A@x,b,rtol=1e-10,max_iter=10,max_matvecs=20)
        self.assertLess(float(torch.linalg.norm(A@x-b)),1e-10)
        self.assertTrue(r['converged'])
        self.assertLessEqual(r['matvecs'],20)
        x,r=cg(lambda x:A@x,b,rtol=1e-15,max_iter=10,max_matvecs=2)
        self.assertLessEqual(r['matvecs'],2)
        self.assertEqual(r['iterations'],1)

    def test_indefinite_operator_not_success(self):
        import torch
        from genesis_next.solvers import cg
        _,r=cg(lambda x:-x,torch.ones(3,dtype=torch.float64),max_iter=10)
        self.assertEqual(r['status'],'NONPOSITIVE_CURVATURE')

    def test_wrong_rhs_can_have_small_residual(self):
        import torch
        from genesis_next.solvers import cg
        b=torch.tensor([1.,2.],dtype=torch.float64)
        corrupt=b+torch.tensor([.2,-.2],dtype=torch.float64)
        x,r=cg(lambda x:x,corrupt,max_iter=10)
        self.assertTrue(r['converged'])
        self.assertGreater(float(torch.linalg.norm(x-b)/torch.linalg.norm(b)),.1)

if __name__=='__main__':unittest.main()
