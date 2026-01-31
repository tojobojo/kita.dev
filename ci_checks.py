import sys
import unittest
from api.metrics import MetricsCollector
from config.release_gates import ReleaseGateKeeper

def run_ci_checks():
    """
    Simulates the CI pipeline defined in Bible VII.
    1. Unit Tests
    2. Integration/E2E
    3. Release Gates
    """
    print("Running CI Checks...")
    
    # 1. Tests (Mocking test runner invocation by importing and running suites or just simulating pass)
    # We will trust separate pytest commands for unit tests. This script is for the GATES.
    
    # 2. Release Gate Check (Simulation)
    # In a real CI, we'd pull metrics from the last N runs or a database.
    # Here we mock a "healthy" run to verify the gate logic.
    
    print("Verifying Release Gates...")
    collector = MetricsCollector()
    
    # Simulate data matching Appendix C targets
    # 80 tasks, 60 success, 15 stops, 5 active
    for _ in range(80):
        collector.record_start()
        
    for _ in range(60):
        collector.record_success()
        
    for _ in range(15):
        collector.record_stop("Safety check")
        
    # Retries: 40 retries total -> 0.5 rate
    for _ in range(40):
        collector.record_retry()
        
    metrics = collector.get_summary()
    print(f"Metrics: {metrics}")
    
    keeper = ReleaseGateKeeper()
    result = keeper.check_gates(metrics)
    
    if result.passed:
        print("Release Gates PASSED.")
        sys.exit(0)
    else:
        print(f"Release Gates FAILED: {result.reasons}")
        sys.exit(1)

if __name__ == "__main__":
    run_ci_checks()
