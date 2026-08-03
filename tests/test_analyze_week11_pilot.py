"""Tests for the read-only Week 11 pilot analysis."""

import csv
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "experiments"))

import analyze_week11_pilot as analysis  # noqa: E402


MULTIPLIERS = {
    analysis.PYTHON_ALGORITHM: 1.0,
    analysis.REFERENCE_ALGORITHM: 2.0,
    analysis.PAPER_ALGORITHM_NAME: 4.0,
}


def synthetic_cases():
    cases = []
    index = 0
    for n in analysis.WEEK11_EXPERIMENT_PROTOCOL.sizes:
        for family, count in (
            ("flat_valid", 1),
            ("nested_valid", 1),
            ("incremental_valid", 5),
        ):
            for repetition in range(1, count + 1):
                index += 1
                cases.append(
                    {
                        "case_id": f"{family}_n{n}_{repetition:03d}",
                        "family": family,
                        "n": n,
                        "index": index,
                    }
                )
    return cases


def make_case_rows():
    rows = []
    for case in synthetic_cases():
        base = case["n"] * 100 + case["index"]
        for algorithm in analysis.ALGORITHMS:
            median = base * MULTIPLIERS[algorithm]
            q1 = median * 0.9
            q3 = median * 1.1
            rows.append(
                {
                    "case_id": case["case_id"],
                    "family": case["family"],
                    "n": str(case["n"]),
                    "algorithm": algorithm,
                    "measured_run_count": "10",
                    "median_time_ns": str(median),
                    "q1_time_ns": str(q1),
                    "q3_time_ns": str(q3),
                    "iqr_time_ns": str(q3 - q1),
                    "mean_time_ns": str(median),
                    "stdev_time_ns": str(median * 0.05),
                    "all_correct": "True",
                    "error_count": "0",
                }
            )
    return rows


def make_audit_rows():
    rows = []
    for case in synthetic_cases():
        index = case["index"]
        row = {
            "case_id": case["case_id"],
            "family": case["family"],
            "n": str(case["n"]),
            "audit_passed": "True",
            "nesting_density": str(index / 40),
            "max_depth": str(index),
            "containment_pair_density": str(index / 50),
        }
        for counter_index, field in enumerate(analysis.COUNTER_FIELDS, start=1):
            row[field] = str(index * counter_index)
        rows.append(row)
    return rows


def make_raw_rows():
    rows = []
    for case in synthetic_cases():
        for algorithm in analysis.ALGORITHMS:
            rows.append(
                {
                    "algorithm": algorithm,
                    "time_ns": str(
                        int(case["n"] * MULTIPLIERS[algorithm] + 1)
                    ),
                    "output_correct": "True",
                    "error": "",
                }
            )
    return rows


def write_csv(path, rows):
    with Path(path).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class AnalyzeWeek11PilotTests(unittest.TestCase):
    def test_case_records_and_ratios_are_case_weighted(self):
        records = analysis.load_case_runtime_records(make_case_rows())
        ratios = analysis.summarize_ratios(
            analysis.build_case_ratio_records(records)
        )

        self.assertEqual(len(records), 105)
        self.assertEqual(len(ratios), 72)
        overall = {
            row["comparison"]: row["median_ratio"]
            for row in ratios
            if row["scope"] == "overall"
        }
        self.assertEqual(overall["paper/reference"], 2.0)
        self.assertEqual(overall["paper/python"], 4.0)
        self.assertEqual(overall["reference/python"], 2.0)

    def test_runtime_and_relationship_tables_have_frozen_shapes(self):
        records = analysis.load_case_runtime_records(make_case_rows())
        audits = analysis.load_audit_records(make_audit_rows())

        self.assertEqual(len(analysis.summarize_runtime(records, ("n",))), 15)
        self.assertEqual(
            len(analysis.summarize_runtime(records, ("family",))),
            9,
        )
        self.assertEqual(
            len(analysis.summarize_runtime(records, ("family", "n"))),
            45,
        )
        self.assertEqual(
            len(analysis.summarize_structure_relationships(records, audits)),
            15,
        )
        self.assertEqual(
            len(analysis.summarize_counter_relationships(records, audits)),
            25,
        )

    def test_similar_runtime_quartiles_produce_relative_iqr(self):
        records = analysis.load_case_runtime_records(make_case_rows())
        first = records[0]

        self.assertAlmostEqual(first["relative_iqr"], 0.2)
        self.assertLess(
            first["relative_iqr"],
            analysis.HIGH_RELATIVE_IQR_THRESHOLD,
        )

    def test_require_validated_run_writes_report_outside_evidence(self):
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            report_path = root / "analysis" / "live_report.json"
            report_path.parent.mkdir()
            with patch.object(
                analysis,
                "validate_outputs",
                return_value={"valid": True, "row_counts": {}},
            ) as validator:
                result = analysis.require_validated_run(
                    root / "run",
                    report_path,
                )

        self.assertTrue(result["valid"])
        validator.assert_called_once_with(
            root / "run",
            report_json=report_path,
        )

    def test_require_validated_run_rejects_invalid_evidence(self):
        with tempfile.TemporaryDirectory() as tempdir, patch.object(
            analysis,
            "validate_outputs",
            return_value={"valid": False, "errors": ["tampered"]},
        ):
            with self.assertRaisesRegex(ValueError, "failed live validation"):
                analysis.require_validated_run(
                    Path(tempdir) / "run",
                    Path(tempdir) / "report.json",
                )

    def test_analysis_output_cannot_be_inside_archived_evidence(self):
        with tempfile.TemporaryDirectory() as tempdir:
            run_dir = Path(tempdir) / "run"
            run_dir.mkdir()

            with self.assertRaisesRegex(ValueError, "outside archived"):
                analysis.analyze_run(run_dir, run_dir / "analysis")

    def test_analyze_run_does_not_modify_source_evidence(self):
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            run_dir = root / "run"
            output_dir = root / "analysis"
            run_dir.mkdir()
            write_csv(run_dir / "case_summary.csv", make_case_rows())
            write_csv(run_dir / "case_audit.csv", make_audit_rows())
            write_csv(run_dir / "raw.csv", make_raw_rows())
            (run_dir / "manifest.json").write_text(
                json.dumps({"source_commit": "a" * 40}),
                encoding="utf-8",
            )
            source_hashes = {
                path.name: sha256(path)
                for path in run_dir.iterdir()
            }
            report = {
                "valid": True,
                "row_counts": {
                    "raw": 1050,
                    "case_summary": 105,
                    "group_summary": 45,
                    "case_audit": 35,
                },
            }

            with patch.object(
                analysis,
                "validate_outputs",
                return_value=report,
            ):
                summary, artifacts = analysis.analyze_run(run_dir, output_dir)
                runtime_figure = artifacts["runtime_figure"].read_text(
                    encoding="utf-8"
                )
                ratio_figure = artifacts["ratio_figure"].read_text(
                    encoding="utf-8"
                )

            final_hashes = {
                path.name: sha256(path)
                for path in run_dir.iterdir()
            }

        self.assertEqual(source_hashes, final_hashes)
        self.assertTrue(summary["validation_valid"])
        self.assertEqual(summary["case_runtime_rows"], 105)
        self.assertEqual(summary["runtime_by_size_rows"], 15)
        self.assertEqual(summary["runtime_by_family_size_rows"], 45)
        self.assertIn("<svg", runtime_figure)
        self.assertIn("rotate(-90", runtime_figure)
        self.assertIn("paper/reference", ratio_figure)
        self.assertIn("logarithmic ratio axis", ratio_figure)


if __name__ == "__main__":
    unittest.main()
