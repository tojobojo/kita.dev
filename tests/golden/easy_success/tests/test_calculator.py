"""Tests for the calculator module."""

import unittest
import sys

sys.path.insert(0, "..")

from src.calculator import add, subtract, divide


class TestCalculator(unittest.TestCase):

    def test_add_positive(self):
        self.assertEqual(add(2, 3), 5)

    def test_add_negative(self):
        self.assertEqual(add(-1, -1), -2)

    def test_add_zero(self):
        self.assertEqual(add(0, 5), 5)

    def test_divide_basic(self):
        self.assertEqual(divide(10, 2), 5.0)

    # TODO: Add test for zero division
    # TODO: Add tests for subtract function


if __name__ == "__main__":
    unittest.main()
