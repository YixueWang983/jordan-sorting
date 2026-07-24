"""Tests for the Week 7 pilot benchmark runner."""

import tempfile
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "experiments"))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from generators import FLAT_VALID, INCREMENTAL_VALID, INVALID_UPPER_CROSSING  # noqa: E402
from run_week7_pilot import (  # noqa: E402
    ALGORITHMS,
    DEFAULT_ALGORITHM_NAMES,
    PilotConfig,
    algorithm_order_for_round,
    build_cases,
    build_config_from_args,
    make_raw_rows,
    run_pilot,
    summarize_by_case,
    summarize_by_group,
)


class RunWeek7PilotTests(unittest.TestCase):
    def _config(self, tmpdir):
        root = Path(tmpdir)
        return PilotConfig(
            families=[FLAT_VALID, INCREMENTAL_VALID, INVALID_UPPER_CROSSING],
            sizes=[8],
            algorithms=list(DEFAULT_ALGORITHM_NAMES),
            randomized_cases=1,
            warmup_runs=1,
            measured_runs=2,
            seed=17,
            algorithm_order_seed=19,
            case_order_seed=31,
            run_id="test_run",
            run_dir=root,
            raw_csv=root / "raw.csv",
            case_summary_csv=root / "case.csv",
            group_summary_csv=root / "group.csv",
            environment_json=root / "env.json",
            auto_report_md=root / "auto_report.md",
            config_json=root / "config.json",
            manifest_json=root / "manifest.json",
        )

    def test_build_cases_uses_randomized_case_count_only_for_randomized_families(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cases = build_cases(self._config(tmpdir))

            self.assertEqual(len(cases), 3)
            self.assertEqual({case["n"] for case in cases}, {8})
            self.assertEqual(
                {case["family"] for case in cases},
                {FLAT_VALID, INCREMENTAL_VALID, INVALID_UPPER_CROSSING},
            )

    def test_make_raw_rows_records_only_measured_runs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config = self._config(tmpdir)
            rows = make_raw_rows(config)

            expected = 3 * len(config.algorithms) * config.measured_runs
            self.assertEqual(len(rows), expected)
            self.assertEqual({row["run_index"] for row in rows}, {1, 2})
            self.assertEqual({row["measured_round"] for row in rows}, {1, 2})
            self.assertEqual(
                {row["algorithm_position"] for row in rows},
                {1, 2, 3},
            )
            self.assertEqual(
                {row["case_execution_position"] for row in rows},
                {1, 2, 3},
            )
            self.assertIn("containment_pair_density", rows[0])
            self.assertIn("trace_event_count", rows[0])
            self.assertTrue(all(row["overall_correct"] for row in rows))

    def test_algorithm_order_rotates_by_measured_round(self):
        algorithms = ["a", "b", "c"]

        first = algorithm_order_for_round(algorithms, seed=11, case_index=0, measured_round=1)
        second = algorithm_order_for_round(algorithms, seed=11, case_index=0, measured_round=2)
        third = algorithm_order_for_round(algorithms, seed=11, case_index=0, measured_round=3)

        self.assertEqual(set(first), set(algorithms))
        self.assertEqual(second, first[1:] + first[:1])
        self.assertEqual(third, first[2:] + first[:2])

    def test_summaries_aggregate_by_case_then_group(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config = self._config(tmpdir)
            raw_rows = make_raw_rows(config)
            case_rows = summarize_by_case(raw_rows)
            group_rows = summarize_by_group(case_rows)

            self.assertEqual(len(case_rows), 3 * len(config.algorithms))
            self.assertEqual(len(group_rows), 3 * len(config.algorithms))
            self.assertTrue(all(row["measured_run_count"] == 2 for row in case_rows))
            self.assertTrue(all(row["case_count"] == 1 for row in group_rows))
            self.assertTrue(all(row["all_correct"] for row in case_rows))
            self.assertTrue(all(row["all_cases_correct"] for row in group_rows))

    def test_run_pilot_writes_all_outputs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config = self._config(tmpdir)
            raw_rows, case_rows, group_rows = run_pilot(config)

            self.assertTrue(config.raw_csv.exists())
            self.assertTrue(config.case_summary_csv.exists())
            self.assertTrue(config.group_summary_csv.exists())
            self.assertTrue(config.environment_json.exists())
            self.assertTrue(config.auto_report_md.exists())
            self.assertTrue(config.config_json.exists())
            self.assertTrue(config.manifest_json.exists())
            self.assertEqual(len(raw_rows), 18)
            self.assertEqual(len(case_rows), 9)
            self.assertEqual(len(group_rows), 9)

    def test_simplified_reference_timing_uses_plain_reference_with_external_counters(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config = self._config(tmpdir)
            rows = make_raw_rows(config)
            simplified_rows = [
                row for row in rows if row["algorithm"] == "simplified_jordan_reference"
            ]

            self.assertTrue(simplified_rows)
            self.assertTrue(all(row["trace_event_count"] != "" for row in simplified_rows))
            self.assertTrue(all(row["validity_correct"] is True for row in simplified_rows))
            self.assertTrue(all(row["reason_correct"] is True for row in simplified_rows))

    def test_group_summary_handles_algorithm_with_no_successful_timings(self):
        def always_fails(_seq):
            raise RuntimeError("intentional test failure")

        ALGORITHMS["always_fails"] = always_fails
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                config = self._config(tmpdir)
                config = PilotConfig(
                    families=config.families,
                    sizes=config.sizes,
                    algorithms=config.algorithms + ["always_fails"],
                    randomized_cases=config.randomized_cases,
                    warmup_runs=config.warmup_runs,
                    measured_runs=config.measured_runs,
                    seed=config.seed,
                    algorithm_order_seed=config.algorithm_order_seed,
                    case_order_seed=config.case_order_seed,
                    run_id=config.run_id,
                    run_dir=config.run_dir,
                    raw_csv=config.raw_csv,
                    case_summary_csv=config.case_summary_csv,
                    group_summary_csv=config.group_summary_csv,
                    environment_json=config.environment_json,
                    auto_report_md=config.auto_report_md,
                    config_json=config.config_json,
                    manifest_json=config.manifest_json,
                )
                rows = make_raw_rows(config)
                case_rows = summarize_by_case(rows)
                group_rows = summarize_by_group(case_rows)

                failing_case_rows = [
                    row for row in case_rows if row["algorithm"] == "always_fails"
                ]
                failing_group_rows = [
                    row for row in group_rows if row["algorithm"] == "always_fails"
                ]

                self.assertTrue(failing_case_rows)
                self.assertTrue(failing_group_rows)
                self.assertTrue(
                    all(row["median_time_ns"] == "" for row in failing_case_rows)
                )
                self.assertTrue(
                    all(row["median_case_time_ns"] == "" for row in failing_group_rows)
                )
                self.assertTrue(
                    all(row["all_cases_correct"] is False for row in failing_group_rows)
                )
                self.assertTrue(
                    all(int(row["total_error_count"]) > 0 for row in failing_group_rows)
                )
        finally:
            del ALGORITHMS["always_fails"]

    def test_build_config_from_args_uses_no_overwrite_run_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir) / "existing"
            run_dir.mkdir()
            (run_dir / "raw.csv").write_text("existing\n", encoding="utf-8")
            args = SimpleNamespace(
                families=[FLAT_VALID],
                sizes=[8],
                algorithms=["python_sort"],
                randomized_cases=1,
                warmup_runs=0,
                measured_runs=1,
                seed=17,
                algorithm_order_seed=None,
                case_order_seed=None,
                run_id="existing",
                run_dir=run_dir,
                overwrite=False,
                raw_csv=None,
                case_summary_csv=None,
                group_summary_csv=None,
                environment_json=None,
                auto_report_md=None,
            )

            with self.assertRaises(ValueError):
                build_config_from_args(args)

    def test_build_config_from_args_rejects_existing_explicit_output_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir) / "run"
            raw_csv = Path(tmpdir) / "existing_raw.csv"
            raw_csv.write_text("existing\n", encoding="utf-8")
            args = SimpleNamespace(
                families=[FLAT_VALID],
                sizes=[8],
                algorithms=["python_sort"],
                randomized_cases=1,
                warmup_runs=0,
                measured_runs=1,
                seed=17,
                algorithm_order_seed=None,
                case_order_seed=None,
                run_id="test",
                run_dir=run_dir,
                overwrite=False,
                raw_csv=raw_csv,
                case_summary_csv=None,
                group_summary_csv=None,
                environment_json=None,
                auto_report_md=None,
            )

            with self.assertRaises(ValueError):
                build_config_from_args(args)

    def test_build_config_from_args_rejects_invalid_algorithm(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            args = SimpleNamespace(
                families=[FLAT_VALID],
                sizes=[8],
                algorithms=["unknown"],
                randomized_cases=1,
                warmup_runs=0,
                measured_runs=1,
                seed=17,
                algorithm_order_seed=None,
                case_order_seed=None,
                run_id="test",
                run_dir=Path(tmpdir) / "run",
                overwrite=False,
                raw_csv=None,
                case_summary_csv=None,
                group_summary_csv=None,
                environment_json=None,
                auto_report_md=None,
            )

            with self.assertRaises(ValueError):
                build_config_from_args(args)


if __name__ == "__main__":
    unittest.main()
