"""Week 9 sorting/recognition integration pilot tests."""

import tempfile
import sys
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import Mock, patch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "experiments"))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import run_week7_pilot  # noqa: E402
from generators import INVALID_UPPER_CROSSING  # noqa: E402
from run_week7_pilot import (  # noqa: E402
    ALGORITHMS,
    PAPER_ALGORITHM_NAME,
    PAPER_METRIC_FIELDS,
    validate_config,
)
from run_week9_pilot import (  # noqa: E402
    RECOGNITION_ALGORITHMS,
    RECOGNITION_FAMILIES,
    SORTING_ALGORITHMS,
    SORTING_FAMILIES,
    WEEK9_MEASURED_RUNS,
    WEEK9_RANDOMIZED_CASES,
    WEEK9_SIZES,
    WEEK9_WARMUP_RUNS,
    build_week9_configs,
    run_week9_pilots,
)
from validate_experiment_outputs import validate_outputs  # noqa: E402


class RunWeek9PilotTests(unittest.TestCase):
    def test_frozen_configs_keep_sorting_and_recognition_separate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            configs = build_week9_configs("test_week9", tmpdir)

            sorting = configs["sorting"]
            recognition = configs["recognition"]
            self.assertEqual(sorting.sizes, WEEK9_SIZES)
            self.assertEqual(sorting.families, SORTING_FAMILIES)
            self.assertEqual(sorting.algorithms, SORTING_ALGORITHMS)
            self.assertEqual(recognition.families, RECOGNITION_FAMILIES)
            self.assertEqual(recognition.algorithms, RECOGNITION_ALGORITHMS)
            self.assertEqual(sorting.randomized_cases, WEEK9_RANDOMIZED_CASES)
            self.assertEqual(sorting.warmup_runs, WEEK9_WARMUP_RUNS)
            self.assertEqual(sorting.measured_runs, WEEK9_MEASURED_RUNS)
            self.assertNotIn(PAPER_ALGORITHM_NAME, recognition.algorithms)
            self.assertNotEqual(sorting.run_dir, recognition.run_dir)

    def test_paper_algorithm_rejects_invalid_family_configuration(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            sorting = build_week9_configs("test_week9", tmpdir, mode="sorting")[
                "sorting"
            ]
            invalid_config = replace(
                sorting,
                families=[*sorting.families, INVALID_UPPER_CROSSING],
            )

            with self.assertRaisesRegex(ValueError, "valid-only"):
                validate_config(invalid_config)

    def test_paper_diagnostics_run_once_per_case_outside_timing_loop(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            sorting = build_week9_configs("test_week9", tmpdir, mode="sorting")[
                "sorting"
            ]
            config = replace(
                sorting,
                sizes=[8],
                families=[SORTING_FAMILIES[0]],
                algorithms=[PAPER_ALGORITHM_NAME],
                warmup_runs=1,
                measured_runs=2,
            )
            real_diagnostics = run_week7_pilot.paper_jordan_diagnostics_valid
            real_algorithm = ALGORITHMS[PAPER_ALGORITHM_NAME]

            with patch.object(
                run_week7_pilot,
                "paper_jordan_diagnostics_valid",
                wraps=real_diagnostics,
            ) as diagnostics_mock:
                with patch.dict(
                    ALGORITHMS,
                    {PAPER_ALGORITHM_NAME: Mock(wraps=real_algorithm)},
                ):
                    algorithm_mock = ALGORITHMS[PAPER_ALGORITHM_NAME]
                    rows = run_week7_pilot.make_raw_rows(config)

            self.assertEqual(diagnostics_mock.call_count, 1)
            self.assertEqual(algorithm_mock.call_count, 3)
            self.assertEqual(len(rows), 2)

    def test_both_pilots_write_valid_isolated_outputs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            configs = build_week9_configs("test_week9", tmpdir)
            results = run_week9_pilots(configs)

            sorting = results["sorting"]
            recognition = results["recognition"]
            self.assertEqual(len(sorting["raw_rows"]), 108)
            self.assertEqual(len(sorting["case_rows"]), 36)
            self.assertEqual(len(sorting["group_rows"]), 27)
            self.assertEqual(len(recognition["raw_rows"]), 180)
            self.assertEqual(len(recognition["case_rows"]), 60)
            self.assertEqual(len(recognition["group_rows"]), 42)

            self.assertTrue(
                all(row["overall_correct"] for row in sorting["raw_rows"])
            )
            self.assertTrue(
                all(row["overall_correct"] for row in recognition["raw_rows"])
            )
            paper_rows = [
                row
                for row in sorting["raw_rows"]
                if row["algorithm"] == PAPER_ALGORITHM_NAME
            ]
            nonpaper_rows = [
                row
                for row in sorting["raw_rows"]
                if row["algorithm"] != PAPER_ALGORITHM_NAME
            ]
            self.assertTrue(paper_rows)
            self.assertTrue(
                all(
                    all(row[field] != "" for field in PAPER_METRIC_FIELDS)
                    for row in paper_rows
                )
            )
            self.assertTrue(
                all(
                    all(row[field] == "" for field in PAPER_METRIC_FIELDS)
                    for row in nonpaper_rows
                )
            )

            for config in configs.values():
                self.assertTrue(config.manifest_json.exists())
                report = validate_outputs(run_dir=config.run_dir)
                self.assertTrue(report["valid"], report["errors"])

            with self.assertRaises(ValueError):
                run_week9_pilots(configs)


if __name__ == "__main__":
    unittest.main()
