import unittest
from api.metrics import MetricsCollector
from config.release_gates import ReleaseGateKeeper


class TestReleaseFlow(unittest.TestCase):

    def test_gate_pass_healthy(self):
        collector = MetricsCollector()
        # 100 tasks, 70 success, 20 stops (20%), 50 retries (0.5)
        for _ in range(100):
            collector.record_start()
        for _ in range(70):
            collector.record_success()
        for _ in range(20):
            collector.record_stop("Test")
        for _ in range(50):
            collector.record_retry()

        keeper = ReleaseGateKeeper()
        result = keeper.check_gates(collector.get_summary())
        self.assertTrue(result.passed)

    def test_gate_fail_low_completion(self):
        collector = MetricsCollector()
        # 100 tasks, 20 success (20%)
        for _ in range(100):
            collector.record_start()
        for _ in range(20):
            collector.record_success()

        keeper = ReleaseGateKeeper()
        result = keeper.check_gates(collector.get_summary())
        self.assertFalse(result.passed)
        self.assertTrue(any("Completion rate" in r for r in result.reasons))

    def test_gate_fail_reckless_stops(self):
        collector = MetricsCollector()
        # 100 tasks, 0 stops (0%) -> Reckless
        for _ in range(100):
            collector.record_start()
        for _ in range(100):
            collector.record_success()

        keeper = ReleaseGateKeeper()
        result = keeper.check_gates(collector.get_summary())
        self.assertFalse(result.passed)
        self.assertTrue(any("STOP rate" in r for r in result.reasons))

    def test_gate_fail_high_retries(self):
        collector = MetricsCollector()
        # 10 tasks, 200 retries (20.0 rate) -> Flailing
        for _ in range(10):
            collector.record_start()
        for _ in range(200):
            collector.record_retry()

        keeper = ReleaseGateKeeper()
        result = keeper.check_gates(collector.get_summary())
        self.assertFalse(result.passed)
        self.assertTrue(any("Retry rate" in r for r in result.reasons))


if __name__ == "__main__":
    unittest.main()
