"""simplified_jordan_sort 的参考骨架测试。"""

import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from generators import (  # noqa: E402
    FLAT_VALID,
    INCREMENTAL_VALID,
    INVALID_LOWER_CROSSING,
    INVALID_UPPER_CROSSING,
    MUTATION_BASED_INVALID,
    NESTED_VALID,
    RANDOM_INVALID,
    generate_sequence,
)
from oracle import oracle  # noqa: E402
from simplified_jordan import simplified_jordan_sort  # noqa: E402


class SimplifiedJordanTests(unittest.TestCase):
    def test_reference_skeleton_return_contract_keys(self):
        result = simplified_jordan_sort([1, 6, 2, 5, 3, 4])

        self.assertEqual(
            set(result.keys()),
            {
                "valid",
                "sorted",
                "reason",
                "oracle",
                "families",
                "stats",
                "trace",
                "implementation",
                "implementation_stage",
                "backend",
            },
        )
        self.assertEqual(result["implementation"], "reference_skeleton")
        self.assertEqual(result["implementation_stage"], "week4_algorithm_facing_reference")
        self.assertEqual(
            result["backend"],
            {
                "name": "ordinary_list",
                "uses_oracle_sorted_output": True,
                "linear_time_claim": False,
            },
        )

    def test_reference_skeleton_backend_is_isolated_per_result(self):
        first = simplified_jordan_sort([1, 6, 2, 5, 3, 4])
        second = simplified_jordan_sort([1, 6, 2, 5, 3, 4])

        first["backend"]["linear_time_claim"] = True

        self.assertFalse(
            second["backend"]["linear_time_claim"],
            "backend dict should be copied per result",
        )

    def test_reference_skeleton_matches_oracle_sorted_output(self):
        cases = [
            [],
            [1],
            [1, 2, 3, 4, 5, 6],
            [1, 6, 2, 5, 3, 4],
            generate_sequence(INCREMENTAL_VALID, 16, seed=7),
        ]

        for seq in cases:
            with self.subTest(seq=seq):
                result = simplified_jordan_sort(seq)
                oracle_result = oracle(seq)

                self.assertTrue(result["valid"])
                self.assertEqual(result["sorted"], oracle_result["sorted"])
                self.assertEqual(result["sorted"], sorted(seq))
                self.assertEqual(result["implementation"], "reference_skeleton")

    def test_reference_skeleton_rejects_invalid_inputs(self):
        cases = [
            generate_sequence(INVALID_UPPER_CROSSING, 8),
            generate_sequence(INVALID_LOWER_CROSSING, 8),
            generate_sequence(RANDOM_INVALID, 8, seed=11),
            generate_sequence(MUTATION_BASED_INVALID, 8, seed=13),
            [1, 2, 2, 3],
        ]

        for seq in cases:
            with self.subTest(seq=seq):
                result = simplified_jordan_sort(seq)

                self.assertFalse(result["valid"])
                self.assertIsNotNone(result["reason"])
                self.assertIsNone(result["families"])
                self.assertEqual(result["sorted"], sorted(seq))
                self.assertEqual(result["stats"]["category"], "invalid")
                self.assertEqual(result["implementation"], "reference_skeleton")
                self.assertEqual(
                    result["implementation_stage"],
                    "week4_algorithm_facing_reference",
                )
                self.assertEqual(
                    result["backend"],
                    {
                        "name": "ordinary_list",
                        "uses_oracle_sorted_output": True,
                        "linear_time_claim": False,
                    },
                )

    def test_reference_skeleton_returns_family_structures(self):
        result = simplified_jordan_sort([1, 6, 2, 5, 3, 4])

        self.assertTrue(result["valid"])
        self.assertIn("upper", result["families"])
        self.assertIn("lower", result["families"])

        upper = result["families"]["upper"]
        lower = result["families"]["lower"]

        self.assertEqual(upper["pair_family"], "upper")
        self.assertEqual(lower["pair_family"], "lower")

        self.assertEqual(
            [node["interval"] for node in upper["nodes"]],
            [[1, 6], [2, 5], [3, 4]],
        )
        self.assertEqual(
            [node["interval"] for node in lower["nodes"]],
            [[2, 6], [3, 5]],
        )

    def test_reference_skeleton_returns_stats(self):
        result = simplified_jordan_sort([1, 6, 2, 5, 3, 4])
        stats = result["stats"]

        self.assertTrue(stats["valid"])
        self.assertEqual(stats["upper_interval_count"], 3)
        self.assertEqual(stats["lower_interval_count"], 2)
        self.assertEqual(stats["nesting_count"], 3)
        self.assertEqual(stats["max_depth"], 2)
        self.assertEqual(stats["category"], "medium_nesting_valid")

    def test_reference_skeleton_records_trace_for_valid_input(self):
        result = simplified_jordan_sort([1, 6, 2, 5, 3, 4])
        steps = [entry["step"] for entry in result["trace"]]

        self.assertEqual(
            steps,
            [
                "copy_input",
                "oracle",
                "build_rank_map",
                "extract_pair_families",
                "convert_pairs_to_rank_intervals",
                "build_family_trees",
                "structure_profile",
                "prepare_reference_backend",
                "extract_rank_order",
                "return_reference_sorted_output",
            ],
        )
        self.assertFalse(result["trace"][2]["skipped"])
        self.assertEqual(result["trace"][2]["distinct_values"], True)
        self.assertEqual(result["trace"][2]["n"], 6)
        self.assertEqual(result["trace"][3]["upper_pair_count"], 3)
        self.assertEqual(result["trace"][3]["lower_pair_count"], 2)
        self.assertEqual(result["trace"][4]["upper_interval_count"], 3)
        self.assertEqual(result["trace"][4]["lower_interval_count"], 2)
        self.assertEqual(result["trace"][7]["backend"], "ordinary_list")
        self.assertEqual(result["trace"][8]["backend"], "oracle_sorted")

    def test_reference_skeleton_records_trace_for_invalid_input(self):
        result = simplified_jordan_sort([1, 3, 2, 4])
        steps = [entry["step"] for entry in result["trace"]]

        self.assertEqual(
            steps,
            [
                "copy_input",
                "oracle",
                "structure_profile",
                "reject_invalid_input",
            ],
        )
        self.assertFalse(result["valid"])
        self.assertEqual(result["reason"], "upper crossing")

    def test_reference_skeleton_rejects_duplicate_values_with_reason(self):
        result = simplified_jordan_sort([1, 2, 2, 3])

        self.assertFalse(result["valid"])
        self.assertEqual(result["reason"], "duplicate values")
        self.assertIsNone(result["families"])
        self.assertEqual(result["stats"]["reason"], "duplicate values")
        self.assertEqual(result["oracle"]["reason"], "duplicate values")

    def test_reference_skeleton_handles_day2_day3_cases(self):
        cases = [
            ("flat", FLAT_VALID),
            ("nested", NESTED_VALID),
            ("incremental", INCREMENTAL_VALID),
        ]

        for label, family in cases:
            with self.subTest(label=label):
                seq = generate_sequence(family, 8, seed=2026 if label == "incremental" else None)
                result = simplified_jordan_sort(seq)

                self.assertEqual(result["implementation"], "reference_skeleton")
                self.assertTrue(result["valid"], seq)
                self.assertEqual(result["reason"], None, seq)
                self.assertEqual(result["sorted"], sorted(seq))


if __name__ == "__main__":
    unittest.main()
