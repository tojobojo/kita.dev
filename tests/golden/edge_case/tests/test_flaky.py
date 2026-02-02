"""Flaky tests - sometimes pass, sometimes fail."""
import unittest
import random
import time

class TestFlaky(unittest.TestCase):
    
    def test_random_failure(self):
        """This test randomly fails."""
        # Simulates flaky test
        value = random.random()
        self.assertGreater(value, 0.1)  # Fails ~10% of the time
    
    def test_timing_dependent(self):
        """This test depends on timing."""
        start = time.time()
        time.sleep(0.001)  # Tiny sleep
        elapsed = time.time() - start
        # May fail due to system load
        self.assertLess(elapsed, 0.1)
    
    def test_unclear_assertion(self):
        """What is this testing?"""
        x = 42
        self.assertTrue(x)  # ???
    
    def test_missing_setup(self):
        """Missing setup data."""
        # self.data is never defined
        # self.assertEqual(self.data, expected)
        pass

if __name__ == '__main__':
    unittest.main()
