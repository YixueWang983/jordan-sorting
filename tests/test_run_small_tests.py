"""Week 1 baseline 实验 runner 的单元测试。"""

import csv
from unittest.mock import patch
import sys
import tempfile
import unittest
import io
from dataclasses import replace
from pathlib import Path
from contextlib import redirect_stdout

from experiments import run_small_tests


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from experiments.run_small_tests import (  # noqa: E402
    FLAT_VALID,
    CSV_FIELDS,
    FULL_CONFIG,
    _resolve_reference_output_csv,
    SMOKE_CONFIG,
    STRUCTURAL_FIELDS,
    expected_row_count,
    extract_sorted_output,
    run_algorithm_once,
    run_experiment,
    validate_coverage,
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

    def test_extract_sorted_output_handles_simplified_jordan_reference_result(self):
        result = {"sorted": [1, 2, 3], "valid": True}

        self.assertEqual(
            extract_sorted_output("simplified_jordan_reference", result),
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

    def test_validate_coverage_rejects_missing_family(self):
        config = replace(
            SMOKE_CONFIG,
            families=[FLAT_VALID, "missing_family"],
        )
        rows = [
            {
                "family": FLAT_VALID,
                "algorithm": "python_sort",
                "n": 8,
            }
        ]

        with self.assertRaises(RuntimeError):
            validate_coverage(rows, config)

    def test_validate_coverage_rejects_missing_algorithm(self):
        config = replace(
            SMOKE_CONFIG,
            algorithms=["python_sort", "missing_algorithm"],
        )
        rows = [
            {
                "family": FLAT_VALID,
                "algorithm": "python_sort",
                "n": 8,
            }
        ]

        with self.assertRaises(RuntimeError):
            validate_coverage(rows, config)

    def test_validate_coverage_rejects_missing_size(self):
        config = replace(
            SMOKE_CONFIG,
            sizes=[8, 16],
        )
        rows = [
            {
                "family": FLAT_VALID,
                "algorithm": "python_sort",
                "n": 8,
            }
        ]

        with self.assertRaises(RuntimeError):
            validate_coverage(rows, config)

    def test_default_configs_do_not_include_simplified_reference(self):
        self.assertNotIn("simplified_jordan_reference", SMOKE_CONFIG.algorithms)
        self.assertNotIn("simplified_jordan_reference", FULL_CONFIG.algorithms)

    def test_resolve_reference_output_csv_defaults_to_week4_results(self):
        self.assertEqual(
            _resolve_reference_output_csv(None, with_simplified=True),
            run_small_tests.PROJECT_ROOT / "results" / "week4_reference_results.csv",
        )
        self.assertIsNone(_resolve_reference_output_csv(None, with_simplified=False))

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

    def test_smoke_experiment_with_structure_fields(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            config = replace(
                SMOKE_CONFIG,
                cases_dir=temp_path / "cases",
                output_csv=temp_path / "week1_baseline_smoke_results.csv",
            )
            output_csv = temp_path / "week1_baseline_smoke_structural.csv"

            rows = run_experiment(
                config,
                include_structure=True,
                output_csv=output_csv,
            )

            self.assertEqual(len(rows), 1)
            self.assertTrue(output_csv.exists())

            with output_csv.open(newline="", encoding="utf-8") as file:
                csv_rows = list(csv.DictReader(file))

            self.assertEqual(csv_rows[0]["algorithm"], "python_sort")
            self.assertEqual(csv_rows[0]["error"], "")
            self.assertEqual(csv_rows[0]["category"], "strict_flat")
            self.assertEqual(csv_rows[0]["upper_root_count"], "4")

    def test_smoke_cli_structure_flag_controls_output_columns(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            output_csv = temp_path / "smoke_results.csv"
            structure_csv = temp_path / "smoke_results_structural.csv"
            structure_base_output = temp_path / "smoke_results_auto_structural.csv"
            config = replace(
                SMOKE_CONFIG,
                cases_dir=temp_path / "cases",
                output_csv=output_csv,
            )

            with patch.object(run_small_tests, "SMOKE_CONFIG", config):
                with patch("sys.argv", ["run_small_tests.py", "--smoke", "--output-csv", str(output_csv)]):
                    with redirect_stdout(io.StringIO()):
                        run_small_tests.main()

            with output_csv.open(newline="", encoding="utf-8") as file:
                base_reader = csv.DictReader(file)
                self.assertEqual(base_reader.fieldnames, CSV_FIELDS)

                base_row = next(base_reader)
                self.assertNotIn("upper_interval_count", base_row)

            with patch.object(run_small_tests, "SMOKE_CONFIG", config):
                with patch(
                    "sys.argv",
                    [
                        "run_small_tests.py",
                        "--smoke",
                        "--with-structure",
                        "--output-csv",
                        str(output_csv),
                        "--structural-output-csv",
                        str(structure_csv),
                    ],
                ):
                    with redirect_stdout(io.StringIO()):
                        run_small_tests.main()

            with structure_csv.open(newline="", encoding="utf-8") as file:
                structure_reader = csv.DictReader(file)
                for field in STRUCTURAL_FIELDS:
                    self.assertIn(field, structure_reader.fieldnames)

            self.assertFalse(structure_base_output.exists())

    def test_smoke_cli_with_simplified_reference(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            output_csv = temp_path / "smoke_results.csv"
            config = replace(
                SMOKE_CONFIG,
                cases_dir=temp_path / "cases",
                output_csv=output_csv,
                algorithms=["python_sort"],
            )

            with patch.object(run_small_tests, "SMOKE_CONFIG", config):
                with patch(
                    "sys.argv",
                    [
                        "run_small_tests.py",
                        "--smoke",
                        "--with-simplified",
                        "--output-csv",
                        str(output_csv),
                    ],
                ):
                    with redirect_stdout(io.StringIO()):
                        run_small_tests.main()

            with output_csv.open(newline="", encoding="utf-8") as file:
                rows = list(csv.DictReader(file))

            self.assertEqual(len(rows), 2)
            algorithms = {row["algorithm"] for row in rows}
            self.assertEqual(
                algorithms,
                {"python_sort", "simplified_jordan_reference"},
            )
            for row in rows:
                self.assertEqual(row["sorted_correct"], "True")
                self.assertEqual(row["error"], "")



if __name__ == "__main__":
    unittest.main()
