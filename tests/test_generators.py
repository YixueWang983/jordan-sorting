"""Unit tests for test instance generators."""

import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from generators import (  # noqa: E402
    generate_flat,
    generate_invalid_lower_crossing,
    generate_invalid_upper_crossing,
    generate_nested,
    generate_random_permutation,
    generate_small_handmade_valid_cases,
    mutate_by_swap,
)
from oracle import oracle  # noqa: E402


class GeneratorTests(unittest.TestCase):
    def test_generate_flat(self):
        seq = generate_flat(6)

        self.assertEqual(seq, [1, 2, 3, 4, 5, 6])
        self.assertTrue(oracle(seq)["valid"])

    def test_generate_nested_even_size(self):
        seq = generate_nested(6)

        self.assertEqual(seq, [1, 6, 2, 5, 3, 4])
        self.assertTrue(oracle(seq)["valid"])

    def test_generate_nested_odd_size(self):
        seq = generate_nested(5)

        self.assertEqual(seq, [1, 5, 2, 4, 3])
        self.assertTrue(oracle(seq)["valid"])

    def test_generate_invalid_upper_crossing(self):
        result = oracle(generate_invalid_upper_crossing())

        self.assertFalse(result["valid"])
        self.assertEqual(result["reason"], "upper crossing")

    def test_generate_invalid_lower_crossing(self):
        result = oracle(generate_invalid_lower_crossing())

        self.assertFalse(result["valid"])
        self.assertEqual(result["reason"], "lower crossing")

    def test_generate_random_permutation(self):
        seq = generate_random_permutation(8, seed=11)

        self.assertEqual(sorted(seq), list(range(1, 9)))
        self.assertEqual(len(set(seq)), 8)

    def test_mutate_by_swap(self):
        self.assertEqual(mutate_by_swap([1, 2, 3], i=0, j=2), [3, 2, 1])

    def test_small_handmade_valid_cases(self):
        for seq in generate_small_handmade_valid_cases():
            self.assertTrue(oracle(seq)["valid"], seq)


if __name__ == "__main__":
    unittest.main()
