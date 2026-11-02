"""Unit tests for strict same-metric historical plateau audit."""
import unittest
import numpy as np
from scripts.strict_plateau_audit import audit_norms, block_norms, claim_bounds


class TestStrictHistoricalAudit(unittest.TestCase):
    def test_conflicting_historical_claims(self):
        a = claim_bounds()
        self.assertFalse(a["reported_mass_compatible"])
        self.assertAlmostEqual(a["compatible_offdiag_min"], 0.08181066936002204)
        self.assertAlmostEqual(a["compatible_offdiag_max"], 0.13674033149171272)
        self.assertAlmostEqual(a["necessary_max_ratio_for_reported_mass"],
                               0.2410854737705888)
        self.assertAlmostEqual(a["necessary_adjacent_ratio_if_k_ge_2_at_most_max_ratio"],
                               0.5260544021098347)

    def test_norms_from_full_matrix(self):
        a=np.eye(8)
        n=block_norms(a,[2,2,2,2])
        r=audit_norms(n)
        self.assertAlmostEqual(r["offdiag_energy_mass"],0)
        self.assertEqual(r["normalized_rms_by_distance"],[1.,0.,0.,0.])

    def test_analytic_all_equal_blocks(self):
        a=np.ones((12,12),dtype=float)
        for i in range(12):a[i,i]=10
        r=audit_norms(a)
        expected=(11*.01)/(1+11*.01)
        self.assertAlmostEqual(r["offdiag_energy_mass"],expected)
        self.assertTrue(np.allclose(r["normalized_rms_by_distance"][1:],0.1))

    def test_invalid_negative_block_norm(self):
        a=np.eye(3);a[0,1]=-0.1
        with self.assertRaises(ValueError):audit_norms(a)


if __name__=="__main__":
    unittest.main()
