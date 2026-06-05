"""Unit tests for the Jordan-sorting oracle."""

import random
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from oracle import (  # noqa: E402
    crosses,
    lower_pairs,
    oracle,
    pair_to_interval,
    rank_map,
    upper_pairs,
)


class OracleTests(unittest.TestCase):
    def test_upper_and_lower_pairs(self):
        seq = [4, 1, 3, 2, 5]

        self.assertEqual(upper_pairs(seq), [(4, 1), (3, 2)])
        self.assertEqual(lower_pairs(seq), [(1, 3), (2, 5)])

    def test_rank_interval_conversion(self):
        seq = [4, 1, 3, 2]
        rank = rank_map(seq)

        self.assertEqual(rank, {1: 1, 2: 2, 3: 3, 4: 4})
        self.assertEqual(pair_to_interval((4, 1), rank), (1, 4))
        self.assertEqual(pair_to_interval((3, 2), rank), (2, 3))

    def test_crossing_detection(self):
        self.assertTrue(crosses((1, 3), (2, 4)))
        self.assertTrue(crosses((2, 4), (1, 3)))
        self.assertFalse(crosses((1, 2), (3, 4)))
        self.assertFalse(crosses((1, 4), (2, 3)))

    def test_empty_and_singleton_are_valid(self):
        self.assertTrue(oracle([])["valid"])
        self.assertTrue(oracle([1])["valid"])

    def test_flat_valid_case(self):
        result = oracle([1, 2, 3, 4, 5, 6])

        self.assertTrue(result["valid"])
        self.assertEqual(result["sorted"], [1, 2, 3, 4, 5, 6])
        self.assertTrue(result["upper_ok"])
        self.assertTrue(result["lower_ok"])
        self.assertIsNone(result["reason"])

    def test_nested_valid_case(self):
        result = oracle([1, 6, 2, 5, 3, 4])

        self.assertTrue(result["valid"])
        self.assertEqual(result["sorted"], [1, 2, 3, 4, 5, 6])
        self.assertTrue(result["upper_ok"])
        self.assertTrue(result["lower_ok"])
        self.assertIsNone(result["reason"])

    def test_invalid_upper_crossing(self):
        result = oracle([1, 3, 2, 4])

        self.assertFalse(result["valid"])
        self.assertFalse(result["upper_ok"])
        self.assertTrue(result["lower_ok"])
        self.assertEqual(result["reason"], "upper crossing")

    def test_invalid_lower_crossing(self):
        result = oracle([5, 1, 3, 2, 4])

        self.assertFalse(result["valid"])
        self.assertTrue(result["upper_ok"])
        self.assertFalse(result["lower_ok"])
        self.assertEqual(result["reason"], "lower crossing")

    def test_duplicate_values_rejected(self):
        result = oracle([1, 2, 2, 3])

        self.assertFalse(result["valid"])
        self.assertEqual(result["reason"], "duplicate values")

    def test_random_permutation_sanity_check(self):
        seq = list(range(1, 9))
        random.Random(7).shuffle(seq)
        result = oracle(seq)

        self.assertEqual(result["sorted"], list(range(1, 9)))
        self.assertIn(result["valid"], [True, False])
        self.assertIsInstance(result["upper_ok"], bool)
        self.assertIsInstance(result["lower_ok"], bool)


if __name__ == "__main__":
    unittest.main()
