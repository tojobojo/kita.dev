"""
Golden Repositories pytest configuration.
Excludes the internal test files from repos (they're fixtures, not actual tests).
"""

import pytest

# Tell pytest to ignore the internal test files in golden repos
# These are fixtures for the agent to work with, not actual tests
collect_ignore = [
    "easy_success/tests",
    "realistic_production/tests",
    "edge_case/tests",
    "malicious/tests",
]


def pytest_ignore_collect(collection_path, config):
    """Ignore golden repo internal test files."""
    path_str = str(collection_path)

    # Ignore test files inside golden repo subdirectories
    if "golden" in path_str and any(
        sub in path_str
        for sub in [
            "easy_success/tests",
            "realistic_production/tests",
            "edge_case/tests",
            "malicious/tests",
        ]
    ):
        return True
    return False
