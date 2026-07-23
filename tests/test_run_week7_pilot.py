"""Tests for the Week 7 pilot benchmark runner."""

import tempfile
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "experiments"))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from generators import FLAT_VALID, INCREMENTAL_VALID, INVALID_UPPER_CROSSING  # noqa: E402
from run_week7_pilot import (  # noqa: E402
    ALGORITHMS,
    PilotConfig,
    build_cases,
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
            randomized_cases=1,
            warmup_runs=1,
            measured_runs=2,
            seed=17,
            raw_csv=root / "raw.csv",
            case_summary_csv=root / "case.csv",
            group_summary_csv=root / "group.csv",
            environment_json=root / "env.json",
            auto_report_md=root / "auto_report.md",
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

            expected = 3 * len(ALGORITHMS) * config.measured_runs
            self.assertEqual(len(rows), expected)
            self.assertEqual({row["run_index"] for row in rows}, {1, 2})
            self.assertIn("containment_pair_density", rows[0])
            self.assertIn("trace_event_count", rows[0])
            self.assertTrue(all(row["overall_correct"] for row in rows))

    def test_summaries_aggregate_by_case_then_group(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config = self._config(tmpdir)
            raw_rows = make_raw_rows(config)
            case_rows = summarize_by_case(raw_rows)
            group_rows = summarize_by_group(case_rows)

            self.assertEqual(len(case_rows), 3 * len(ALGORITHMS))
            self.assertEqual(len(group_rows), 3 * len(ALGORITHMS))
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


if __name__ == "__main__":
    unittest.main()
