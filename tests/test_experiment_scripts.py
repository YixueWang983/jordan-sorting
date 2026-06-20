"""Tests for experiment helper scripts."""

import sys
from pathlib import Path
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from experiments.profile_generated_cases import _normalize_family_category_row
from experiments.summarize_results import _median, summarize


class ExperimentScriptsTests(unittest.TestCase):
    def test_median(self):
        self.assertEqual(_median([1, 3, 2]), 2)
        self.assertEqual(_median([1, 2, 3, 4]), 2.5)

    def test_summarize_raw_results(self):
        raw_rows = [
            {"algorithm": "python_sort", "family": "flat_valid", "n": "8", "time_ns": "100", "sorted_correct": "True"},
            {"algorithm": "python_sort", "family": "flat_valid", "n": "8", "time_ns": "300", "sorted_correct": "True"},
            {"algorithm": "python_sort", "family": "flat_valid", "n": "8", "time_ns": "500", "sorted_correct": "True"},
        ]

        summary_rows = summarize(raw_rows)
        self.assertEqual(len(summary_rows), 1)
        self.assertEqual(summary_rows[0]["algorithm"], "python_sort")
        self.assertEqual(summary_rows[0]["family"], "flat_valid")
        self.assertEqual(summary_rows[0]["n"], 8)
        self.assertEqual(summary_rows[0]["run_count"], 3)
        self.assertEqual(summary_rows[0]["min_time_ns"], 100)
        self.assertEqual(summary_rows[0]["max_time_ns"], 500)
        self.assertEqual(summary_rows[0]["median_time_ns"], 300)
        self.assertEqual(summary_rows[0]["mean_time_ns"], 300.0)
        self.assertTrue(summary_rows[0]["all_correct"])

    def test_profile_distribution_normalization(self):
        rows = [
            {
                "family": "flat_valid",
                "n": 8,
                "oracle_valid": True,
                "oracle_reason": "",
                "category": "strict_flat",
                "nesting_density": 0.0,
                "nesting_count": 0,
                "max_depth": 0,
            },
            {
                "family": "flat_valid",
                "n": 8,
                "oracle_valid": False,
                "oracle_reason": "upper crossing",
                "category": "invalid",
                "nesting_density": None,
                "nesting_count": None,
                "max_depth": None,
            },
            {
                "family": "flat_valid",
                "n": 8,
                "oracle_valid": False,
                "oracle_reason": "duplicate values",
                "category": "invalid",
                "nesting_density": None,
                "nesting_count": None,
                "max_depth": None,
            },
        ]

        summary_rows = _normalize_family_category_row(rows)
        summary = summary_rows[0]

        self.assertEqual(summary["family"], "flat_valid")
        self.assertEqual(summary["n"], 8)
        self.assertEqual(summary["total_cases"], 3)
        self.assertEqual(summary["valid_cases"], 1)
        self.assertEqual(summary["invalid_cases"], 2)
        self.assertEqual(summary["strict_flat"], 1)
        self.assertEqual(summary["invalid"], 2)
        self.assertEqual(summary["invalid_reason_duplicate_values"], 1)
        self.assertEqual(summary["invalid_reason_upper_crossing"], 1)
        self.assertEqual(summary["avg_nesting_density"], 0.0)


if __name__ == "__main__":
    unittest.main()
