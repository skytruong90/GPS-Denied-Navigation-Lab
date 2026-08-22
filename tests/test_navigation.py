import unittest
from navigation import simulate, metrics


class NavigationTests(unittest.TestCase):
    def test_repeatable_seed(self): self.assertEqual(simulate(2, .5, 1.5, 4), simulate(2, .5, 1.5, 4))
    def test_landmarks_used_in_outage(self):
        rows = simulate(20, 2, 18); self.assertGreaterEqual(metrics(rows)["landmark_updates"], 1)
    def test_error_nonnegative(self):
        self.assertTrue(all(float(r["position_error_m"]) >= 0 for r in simulate(2, 1, 1.5)))


if __name__ == "__main__": unittest.main()
