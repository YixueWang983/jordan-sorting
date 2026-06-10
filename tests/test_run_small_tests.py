"""Week 1 baseline 实验 runner 的单元测试。"""

import csv
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from experiments.run_small_tests import (  # noqa: E402
    FLAT_VALID,
    SMOKE_CONFIG,
    expected_row_count,
    extract_sorted_output,
    run_algorithm_once,
    run_experiment,
    validate_rows,
)


class RunSmallTestsRunnerTests(unittest.TestCase):
    def test_extract_sorted_output_handles_list_result(self):
        self.assertEqual(
            extract_sorted_output("python_sort", [1, 2, 3]),
            [1, 2, 3],
        )

    def test_extract_sorted_output_handles_laminarity_check_result(self):
        result = {"sorted": [1, 2, 3], "valid": True}

        self.assertEqual(
            extract_sorted_output("sort_plus_laminarity_check", result),
            [1, 2, 3],
        )

    def test_expected_row_count(self):
        config = replace(
            SMOKE_CONFIG,
            sizes=[8, 16],
            families=[FLAT_VALID],
            algorithms=["python_sort", "merge_sort"],
            cases_per_size=2,
            timing_runs=3,
        )

        self.assertEqual(expected_row_count(config), 24)

    def test_run_algorithm_once_records_exceptions(self):
        result = run_algorithm_once(
            algorithm_name="missing_algorithm",
            sequence=[3, 1, 2],
            oracle_sorted=[1, 2, 3],
        )

        self.assertEqual(result["time_ns"], "")
        self.assertFalse(result["sorted_correct"])
        self.assertTrue(result["error"].startswith("KeyError:"))

    def test_validate_rows_rejects_failed_rows(self):
        rows = [
            {
                "family": FLAT_VALID,
                "oracle_valid": True,
                "sorted_correct": False,
                "error": "",
            }
        ]

        with self.assertRaises(RuntimeError):
            validate_rows(rows)

    def test_smoke_experiment_writes_csv(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            config = replace(
                SMOKE_CONFIG,
                cases_dir=temp_path / "cases",
                output_csv=temp_path / "week1_baseline_smoke_results.csv",
            )

            rows = run_experiment(config)

            self.assertEqual(len(rows), 1)
            self.assertTrue(config.output_csv.exists())

            with config.output_csv.open(newline="", encoding="utf-8") as file:
                csv_rows = list(csv.DictReader(file))

            self.assertEqual(len(csv_rows), 1)
            self.assertEqual(csv_rows[0]["family"], FLAT_VALID)
            self.assertEqual(csv_rows[0]["algorithm"], "python_sort")
            self.assertEqual(csv_rows[0]["sorted_correct"], "True")
            self.assertEqual(csv_rows[0]["error"], "")


if __name__ == "__main__":
    unittest.main()
