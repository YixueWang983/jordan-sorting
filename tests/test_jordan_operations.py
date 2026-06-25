"""Operation helpers for week 4 reference pipeline."""

import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from jordan_operations import (  # noqa: E402
    build_operation_state,
    build_rank_intervals,
    extract_pair_families,
    operation_state_to_trace_fields,
)
from oracle import oracle  # noqa: E402


class JordanOperationsTests(unittest.TestCase):
    def test_extract_pair_families(self):
        self.assertEqual(
            extract_pair_families([1, 6, 2, 5, 3, 4]),
            {
                "upper": [(1, 6), (2, 5), (3, 4)],
                "lower": [(6, 2), (5, 3)],
            },
        )

    def test_build_rank_intervals_for_valid_perm(self):
        self.assertEqual(
            build_rank_intervals([10, 60, 20, 50, 30, 40]),
            {
                "upper": [(1, 6), (2, 5), (3, 4)],
                "lower": [(2, 6), (3, 5)],
            },
        )

    def test_build_rank_intervals_rejects_duplicates(self):
        with self.assertRaises(ValueError):
            build_rank_intervals([1, 2, 2, 3])

    def test_build_operation_state_empty_and_singleton(self):
        for seq in ([], [1]):
            state = build_operation_state(seq)

            self.assertEqual(state["n"], len(seq))
            self.assertEqual(state["values"], seq)
            self.assertTrue(state["oracle"]["valid"])
            self.assertIsNotNone(state["rank_map"])
            self.assertEqual(state["upper_pairs"], [])
            self.assertEqual(state["lower_pairs"], [])
            self.assertEqual(state["upper_intervals"], [])
            self.assertEqual(state["lower_intervals"], [])
            self.assertEqual(state["oracle"]["reason"], None)

    def test_build_operation_state_odd_and_even_lengths(self):
        even = build_operation_state([1, 6, 2, 5, 3, 4])
        odd = build_operation_state([1, 6, 2, 5, 3])

        self.assertEqual(even["upper_pairs"], [(1, 6), (2, 5), (3, 4)])
        self.assertEqual(even["lower_pairs"], [(6, 2), (5, 3)])
        self.assertEqual(odd["upper_pairs"], [(1, 6), (2, 5)])
        self.assertEqual(odd["lower_pairs"], [(6, 2), (5, 3)])

    def test_build_operation_state_nested_and_flat_cases(self):
        flat = build_operation_state([1, 2, 3, 4])
        nested = build_operation_state([1, 6, 2, 5, 3, 4])

        self.assertEqual(flat["upper_intervals"], [(1, 2), (3, 4)])
        self.assertEqual(flat["lower_intervals"], [(2, 3)])
        self.assertEqual(nested["upper_intervals"], [(1, 6), (2, 5), (3, 4)])
        self.assertEqual(nested["lower_intervals"], [(2, 6), (3, 5)])

    def test_build_operation_state_duplicate_behavior(self):
        state = build_operation_state([1, 2, 2, 3], oracle_result=oracle([1, 2, 2, 3]))

        self.assertFalse(state["oracle"]["valid"])
        self.assertFalse(state["oracle"]["distinct_values"])
        self.assertIsNone(state["rank_map"])
        self.assertIsNone(state["upper_intervals"])
        self.assertIsNone(state["lower_intervals"])
        self.assertEqual(state["upper_pairs"], [(1, 2), (2, 3)])
        self.assertEqual(state["lower_pairs"], [(2, 2)])

    def test_operation_state_to_trace_fields(self):
        state = build_operation_state([1, 6, 2, 5, 3, 4], oracle([1, 6, 2, 5, 3, 4]))
        trace_fields = operation_state_to_trace_fields(state)

        self.assertEqual(
            trace_fields,
            [
                {
                    "step": "build_rank_map",
                    "n": 6,
                    "distinct_values": True,
                },
                {
                    "step": "extract_pair_families",
                    "upper_pair_count": 3,
                    "lower_pair_count": 2,
                },
                {
                    "step": "convert_pairs_to_rank_intervals",
                    "upper_interval_count": 3,
                    "lower_interval_count": 2,
                },
            ],
        )


if __name__ == "__main__":
    unittest.main()
