import unittest
import numpy as np

from scripts.reference_block_metrics import (
    relative_inverse_residual,
    summarize_blocks,
    uniform_offdiag_upper_bound,
)


class TestMetrics(unittest.TestCase):
    def test_identity(self):
        r = summarize_blocks(np.eye(6), [2, 2, 2])
        self.assertAlmostEqual(r["offdiag_mass"], 0.0)
        self.assertEqual(r["mass_by_distance"][0], 1.0)
        np.testing.assert_allclose(r["normalized_rms"], [1, 0, 0])

    def test_all_ones(self):
        r = summarize_blocks(np.ones((4, 4)), [1, 1, 1, 1])
        self.assertAlmostEqual(r["offdiag_mass"], 0.75)
        np.testing.assert_allclose(r["normalized_rms"], [1, 1, 1, 1])
        self.assertAlmostEqual(r["energy_consistency_error"], 0.0)

    def test_plateau_mass_bound(self):
        self.assertLess(uniform_offdiag_upper_bound(12, 0.12), 0.14)

    def test_solve_residual(self):
        a = np.array([[2.0, 1.0], [1.0, 3.0]])
        x = np.linalg.solve(a, np.eye(2))
        self.assertLess(relative_inverse_residual(a, x), 1e-12)


if __name__ == "__main__":
    unittest.main()
