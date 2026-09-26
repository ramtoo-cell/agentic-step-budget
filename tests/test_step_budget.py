'''Tests for the step budget limiter.'''

import unittest

from src.step_budget import StepBudget


class StepBudgetTests(unittest.TestCase):
    def test_total_cap(self):
        b = StepBudget(3)
        self.assertFalse(b.tick())
        self.assertFalse(b.tick())
        self.assertTrue(b.tick())
        self.assertTrue(b.exhausted())

    def test_phase_quota(self):
        b = StepBudget(100, phase_quotas={"plan": 2})
        b.tick("plan")
        self.assertTrue(b.tick("plan"))
        self.assertFalse(b.exhausted("act"))

    def test_overrun_callback(self):
        calls = []
        b = StepBudget(1, on_overrun=lambda phase, n: calls.append((phase, n)))
        b.tick("act")
        self.assertEqual(calls, [("act", 1)])

    def test_wind_down(self):
        b = StepBudget(10, reserve=3)
        for _ in range(7):
            b.tick()
        self.assertTrue(b.should_wind_down())
        self.assertFalse(b.exhausted())

    def test_remaining(self):
        b = StepBudget(5)
        b.tick()
        b.tick()
        self.assertEqual(b.remaining(), 3)





from src.step_budget import StepBudget


class StepBudgetExtraTests(unittest.TestCase):
    def test_extend(self):
        b = StepBudget(3)
        for _ in range(3):
            b.tick()
        self.assertTrue(b.exhausted())
        self.assertEqual(b.extend(2), 5)
        self.assertFalse(b.exhausted())
        self.assertEqual(b.remaining(), 2)





if __name__ == "__main__":
    unittest.main()
