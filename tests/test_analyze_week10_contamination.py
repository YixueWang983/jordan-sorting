"""Tests for the Week 10 contamination-analysis helpers."""

import json
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "experiments"))

from analyze_week10_contamination import (  # noqa: E402
    EXECUTION_MODES,
    analyze_run,
    compute_case_overheads,
    require_validated_run,
    summarize_components,
    summarize_modes,
    summarize_ratios_by_family,
    summarize_ratios_by_family_and_size,
    summarize_ratios_by_size,
    write_observation_ratio_figure,
    write_ratio_figure,
)
import run_week10_timing_contamination as runner  # noqa: E402
from validate_week10_timing_outputs import validate_outputs  # noqa: E402


def make_case_rows(case_id, family, n, minimal):
    multipliers = {
        "checked": 2.0,
        "instrumented": 1.6,
        "trace_only": 1.4,
        "counters_only": 1.1,
        "minimal": 1.0,
    }
    return [
        {
            "case_id": case_id,
            "family": family,
            "n": str(n),
            "execution_mode": mode,
            "median_time_ns": str(minimal * multipliers[mode]),
        }
        for mode in EXECUTION_MODES
    ]


class AnalyzeWeek10ContaminationTests(unittest.TestCase):
    def test_compute_case_overheads_uses_minimal_as_case_baseline(self):
        records = compute_case_overheads(
            make_case_rows("flat_n8_001", "flat_valid", 8, 100)
        )

        self.assertEqual(len(records), 1)
        record = records[0]
        self.assertEqual(record["validation_overhead_ns"], 40)
        self.assertEqual(record["trace_overhead_ns"], 40)
        self.assertAlmostEqual(record["counter_overhead_ns"], 10)
        self.assertEqual(
            record["combined_instrumentation_overhead_ns"],
            60,
        )
        self.assertEqual(record["checked_ratio"], 2.0)
        self.assertEqual(record["minimal_ratio"], 1.0)

    def test_summaries_equal_weight_cases_and_group_by_size(self):
        rows = []
        rows.extend(make_case_rows("flat_n8_001", "flat_valid", 8, 100))
        rows.extend(make_case_rows("nested_n8_001", "nested_valid", 8, 200))
        records = compute_case_overheads(rows)

        mode_rows = summarize_modes(records)
        component_rows = summarize_components(records)
        size_rows = summarize_ratios_by_size(records)
        family_rows = summarize_ratios_by_family(records)
        family_size_rows = summarize_ratios_by_family_and_size(records)

        checked = next(
            row
            for row in mode_rows
            if row["execution_mode"] == "checked"
        )
        self.assertEqual(checked["case_count"], 2)
        self.assertEqual(checked["median_ratio"], 2.0)
        checked_size = next(
            row
            for row in size_rows
            if row["execution_mode"] == "checked"
        )
        self.assertEqual(checked_size["case_count"], 2)
        self.assertEqual(checked_size["median_ratio"], 2.0)
        validation = next(
            row
            for row in component_rows
            if row["component"] == "validation"
        )
        self.assertEqual(validation["median_ratio"], 1.25)
        checked_family = next(
            row
            for row in family_rows
            if row["family"] == "flat_valid"
            and row["execution_mode"] == "checked"
        )
        self.assertEqual(checked_family["case_count"], 1)
        checked_family_size = next(
            row
            for row in family_size_rows
            if row["family"] == "flat_valid"
            and row["n"] == 8
            and row["execution_mode"] == "checked"
        )
        self.assertEqual(checked_family_size["median_ratio"], 2.0)

    def test_ratio_figure_contains_modes_and_sizes(self):
        rows = []
        for n in (8, 16):
            rows.extend(
                make_case_rows(
                    f"flat_n{n}_001",
                    "flat_valid",
                    n,
                    100,
                )
            )
        size_rows = summarize_ratios_by_size(compute_case_overheads(rows))

        with tempfile.TemporaryDirectory() as tempdir:
            output = Path(tempdir) / "ratio.svg"
            observation_output = Path(tempdir) / "observation.svg"
            write_ratio_figure(size_rows, output)
            write_observation_ratio_figure(
                size_rows,
                observation_output,
            )
            content = output.read_text(encoding="utf-8")
            observation_content = observation_output.read_text(
                encoding="utf-8"
            )

        self.assertIn("<svg", content)
        self.assertIn("checked", content)
        self.assertIn(">8<", content)
        self.assertIn(">16<", content)
        self.assertNotIn(">checked<", observation_content)
        self.assertIn("instrumented", observation_content)

    def test_analysis_rejects_an_unvalidated_run(self):
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            (root / "validation_report.json").write_text(
                json.dumps({"valid": False, "errors": ["tampered"]}),
                encoding="utf-8",
            )

            with self.assertRaises(ValueError):
                require_validated_run(root)

    def test_analysis_rejects_tampering_after_a_successful_validation(self):
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            config = replace(
                runner.build_week10_config(
                    "stale_validation_report",
                    root,
                    smoke=True,
                ),
                sizes=[8],
                randomized_cases=1,
                warmup_runs=0,
                measured_runs=1,
            )
            runner.run_contamination_experiment(config)
            self.assertTrue(validate_outputs(root)["valid"])

            content = config.case_summary_csv.read_text(encoding="utf-8")
            config.case_summary_csv.write_text(
                content.replace(
                    "flat_valid_n8_001",
                    "forged_flat_n8_001",
                    1,
                ),
                encoding="utf-8",
            )

            with self.assertRaises(ValueError):
                analyze_run(
                    root,
                    root / "case_overheads.csv",
                    root / "mode_table.csv",
                    root / "component_table.csv",
                    root / "size_ratios.csv",
                    root / "family_ratios.csv",
                    root / "family_size_ratios.csv",
                    root / "ratios.svg",
                    root / "observation.svg",
                )


if __name__ == "__main__":
    unittest.main()
