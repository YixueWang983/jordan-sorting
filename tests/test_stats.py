"""Structural statistics tests."""

import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from stats import (  # noqa: E402
    classify_valid_profile,
    crossing_pair_count,
    INVALID_CATEGORY,
    LOW_NESTING_VALID,
    MEDIUM_NESTING_VALID,
    NESTED_HEAVY_VALID,
    STRICT_FLAT,
    structure_profile,
)
from family_tree import build_family_trees  # noqa: E402


class StatsTests(unittest.TestCase):
    def test_structure_profile_marks_invalid_candidate(self):
        profile = structure_profile([1, 3, 2, 4])

        self.assertEqual(
            profile,
            {
                "valid": False,
                "reason": "upper crossing",
                "upper_interval_count": None,
                "lower_interval_count": None,
                "total_interval_count": None,
                "upper_root_count": None,
                "lower_root_count": None,
                "upper_nesting_count": None,
                "lower_nesting_count": None,
                "nesting_count": None,
                "nesting_density": None,
                "parented_interval_ratio": None,
                "upper_max_depth": None,
                "lower_max_depth": None,
                "max_depth": None,
                "upper_containment_pair_count": None,
                "lower_containment_pair_count": None,
                "containment_pair_count": None,
                "containment_pair_density": None,
                "upper_crossing_pair_count": 1,
                "lower_crossing_pair_count": 0,
                "total_crossing_pair_count": 1,
                "category": INVALID_CATEGORY,
            },
        )

    def test_structure_profile_marks_duplicate_candidate_invalid(self):
        profile = structure_profile([1, 2, 2, 3])

        self.assertFalse(profile["valid"])
        self.assertEqual(profile["reason"], "duplicate values")
        self.assertEqual(profile["category"], INVALID_CATEGORY)
        self.assertIsNone(profile["total_interval_count"])
        self.assertIsNone(profile["total_crossing_pair_count"])

    def test_structure_profile_handles_empty_and_singleton(self):
        for seq in ([], [1]):
            profile = structure_profile(seq)

            self.assertTrue(profile["valid"])
            self.assertIsNone(profile["reason"])
            self.assertEqual(profile["upper_interval_count"], 0)
            self.assertEqual(profile["lower_interval_count"], 0)
            self.assertEqual(profile["total_interval_count"], 0)
            self.assertEqual(profile["upper_root_count"], 0)
            self.assertEqual(profile["lower_root_count"], 0)
            self.assertEqual(profile["upper_nesting_count"], 0)
            self.assertEqual(profile["lower_nesting_count"], 0)
            self.assertEqual(profile["nesting_count"], 0)
            self.assertEqual(profile["nesting_density"], 0.0)
            self.assertEqual(profile["parented_interval_ratio"], 0.0)
            self.assertEqual(profile["upper_max_depth"], 0)
            self.assertEqual(profile["lower_max_depth"], 0)
            self.assertEqual(profile["max_depth"], 0)
            self.assertEqual(profile["containment_pair_count"], 0)
            self.assertEqual(profile["containment_pair_density"], 0.0)
            self.assertEqual(profile["total_crossing_pair_count"], 0)
            self.assertEqual(profile["category"], STRICT_FLAT)

    def test_structure_profile_strict_flat_valid(self):
        profile = structure_profile([1, 2, 3, 4, 5, 6])

        self.assertTrue(profile["valid"])
        self.assertIsNone(profile["reason"])
        self.assertEqual(profile["upper_interval_count"], 3)
        self.assertEqual(profile["lower_interval_count"], 2)
        self.assertEqual(profile["total_interval_count"], 5)
        self.assertEqual(profile["upper_root_count"], 3)
        self.assertEqual(profile["lower_root_count"], 2)
        self.assertEqual(profile["upper_nesting_count"], 0)
        self.assertEqual(profile["lower_nesting_count"], 0)
        self.assertEqual(profile["nesting_count"], 0)
        self.assertEqual(profile["nesting_density"], 0.0)
        self.assertEqual(profile["parented_interval_ratio"], 0.0)
        self.assertEqual(profile["upper_containment_pair_count"], 0)
        self.assertEqual(profile["lower_containment_pair_count"], 0)
        self.assertEqual(profile["containment_pair_count"], 0)
        self.assertEqual(profile["containment_pair_density"], 0.0)
        self.assertEqual(profile["max_depth"], 0)
        self.assertEqual(profile["total_crossing_pair_count"], 0)
        self.assertEqual(profile["category"], STRICT_FLAT)

    def test_structure_profile_nested_valid(self):
        profile = structure_profile([1, 6, 2, 5, 3, 4])

        self.assertTrue(profile["valid"])
        self.assertEqual(profile["upper_interval_count"], 3)
        self.assertEqual(profile["lower_interval_count"], 2)
        self.assertEqual(profile["total_interval_count"], 5)
        self.assertEqual(profile["upper_root_count"], 1)
        self.assertEqual(profile["lower_root_count"], 1)
        self.assertEqual(profile["upper_nesting_count"], 2)
        self.assertEqual(profile["lower_nesting_count"], 1)
        self.assertEqual(profile["nesting_count"], 3)
        self.assertAlmostEqual(profile["nesting_density"], 3 / 5)
        self.assertAlmostEqual(profile["parented_interval_ratio"], 3 / 5)
        self.assertEqual(profile["upper_max_depth"], 2)
        self.assertEqual(profile["lower_max_depth"], 1)
        self.assertEqual(profile["max_depth"], 2)
        self.assertEqual(profile["upper_containment_pair_count"], 3)
        self.assertEqual(profile["lower_containment_pair_count"], 1)
        self.assertEqual(profile["containment_pair_count"], 4)
        self.assertAlmostEqual(profile["containment_pair_density"], 1.0)
        self.assertEqual(profile["total_crossing_pair_count"], 0)
        self.assertEqual(profile["category"], MEDIUM_NESTING_VALID)

    def test_structure_profile_mixed_containment_density(self):
        profile = structure_profile([1, 4, 2, 3])

        self.assertTrue(profile["valid"])
        self.assertEqual(profile["upper_interval_count"], 2)
        self.assertEqual(profile["lower_interval_count"], 1)
        self.assertEqual(profile["upper_containment_pair_count"], 1)
        self.assertEqual(profile["lower_containment_pair_count"], 0)
        self.assertEqual(profile["containment_pair_count"], 1)
        self.assertAlmostEqual(profile["containment_pair_density"], 1.0)
        self.assertAlmostEqual(profile["parented_interval_ratio"], 1 / 3)

    def test_structure_profile_accepts_prebuilt_family_trees(self):
        seq = [1, 6, 2, 5, 3, 4]
        trees = build_family_trees(seq)
        profile = structure_profile(seq, family_trees=trees)

        self.assertTrue(profile["valid"])
        self.assertEqual(profile["upper_interval_count"], 3)
        self.assertEqual(profile["lower_interval_count"], 2)
        self.assertEqual(profile["max_depth"], 2)
        self.assertEqual(profile["category"], MEDIUM_NESTING_VALID)

    def test_structure_profile_rejects_invalid_family_trees(self):
        with self.assertRaises(ValueError):
            structure_profile([1, 6, 2, 5, 3, 4], family_trees={})

    def test_structure_profile_rejects_missing_upper_or_lower_tree(self):
        with self.assertRaises(ValueError):
            structure_profile([1, 2, 3, 4], family_trees={"upper": object()})

    def test_structure_profile_ignores_family_trees_for_invalid_input(self):
        profile = structure_profile([1, 3, 2, 4], family_trees={})

        self.assertFalse(profile["valid"])
        self.assertEqual(profile["category"], "invalid")

    def test_low_nesting_is_not_called_flat_when_nesting_exists(self):
        profile = structure_profile([1, 4, 2, 3])

        self.assertTrue(profile["valid"])
        self.assertGreater(profile["nesting_count"], 0)
        self.assertEqual(profile["upper_interval_count"], 2)
        self.assertEqual(profile["lower_interval_count"], 1)
        self.assertEqual(profile["category"], LOW_NESTING_VALID)

    def test_crossing_pair_counts_for_invalid_families(self):
        upper_profile = structure_profile([1, 3, 2, 4])
        lower_profile = structure_profile([1, 2, 4, 3, 5])
        both_profile = structure_profile([1, 4, 2, 5, 3, 6])

        self.assertEqual(upper_profile["upper_crossing_pair_count"], 1)
        self.assertEqual(upper_profile["lower_crossing_pair_count"], 0)
        self.assertEqual(upper_profile["total_crossing_pair_count"], 1)

        self.assertEqual(lower_profile["upper_crossing_pair_count"], 0)
        self.assertEqual(lower_profile["lower_crossing_pair_count"], 1)
        self.assertEqual(lower_profile["total_crossing_pair_count"], 1)

        self.assertGreaterEqual(both_profile["upper_crossing_pair_count"], 1)
        self.assertGreaterEqual(both_profile["lower_crossing_pair_count"], 1)
        self.assertEqual(
            both_profile["total_crossing_pair_count"],
            both_profile["upper_crossing_pair_count"]
            + both_profile["lower_crossing_pair_count"],
        )

    def test_crossing_pair_count_rejects_duplicate_rank_interpretation(self):
        self.assertIsNone(crossing_pair_count([1, 2, 2, 3], "upper"))

    def test_crossing_pair_count_rejects_invalid_pair_family(self):
        with self.assertRaises(ValueError):
            crossing_pair_count([1, 3, 2, 4], "random_invalid")

    def test_classify_nested_heavy_valid(self):
        self.assertEqual(
            classify_valid_profile(
                nesting_count=10,
                total_interval_count=10,
                max_depth=5,
            ),
            NESTED_HEAVY_VALID,
        )


if __name__ == "__main__":
    unittest.main()
