"""
Easy Success Golden Repository - Calculator Module
A simple, deterministic calculator for testing.
"""


def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b


def subtract(a: int, b: int) -> int:
    """Subtract b from a."""
    return a - b


def divide(a: int, b: int) -> float:
    """Divide a by b.

    BUG: Does not handle zero division.
    TODO: Fix this bug.
    """
    return a / b  # Bug: no zero check


# TODO: Add multiply function
