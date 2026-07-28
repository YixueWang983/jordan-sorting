"""Adversarial tests for the Week 10 timing-output validator."""

import csv
import json
import tempfile
import sys
import unittest
from dataclasses import replace
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "experiments"))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import run_week10_timing_contamination as runner  # noqa: E402
from validate_week10_timing_outputs import validate_outputs  # noqa: E402


class ValidateWeek10TimingOutputsTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.config = replace(
            runner.build_week10_config(
                "tamper_week10",
                self.root,
                smoke=True,
            ),
            sizes=[8],
            randomized_cases=1,
            warmup_runs=0,
            measured_runs=2,
        )
        runner.run_contamination_experiment(self.config)

    def tearDown(self):
        self.tempdir.cleanup()

    def _read_rows(self, path):
        with path.open(newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))

    def _write_rows(self, path, rows, fields):
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)

    def _refresh_manifest_entry(self, label, update_row_count=False):
        manifest = json.loads(
            self.config.manifest_json.read_text(encoding="utf-8")
        )
        path = Path(manifest["files"][label]["path"])
        manifest["files"][label]["sha256"] = runner.file_sha256(path)
        if update_row_count:
            rows = self._read_rows(path)
            manifest["row_counts"][label.removesuffix("_csv")] = len(rows)
        self.config.manifest_json.write_text(
            json.dumps(manifest, indent=2) + "\n",
            encoding="utf-8",
        )

    def test_validator_rejects_semantic_raw_tampering_with_fresh_hash(self):
        tamper_cases = [
            (
                "oracle_valid",
                "False",
                "not oracle-valid",
            ),
            (
                "record_trace",
                "False",
                "does not match mode",
            ),
            (
                "output_correct",
                "False",
                "wrong output",
            ),
            (
                "audit_passed",
                "False",
                "failed checked audit",
            ),
            (
                "mode_position",
                "99",
                "mode_position out of range",
            ),
            (
                "time_ns",
                "-1",
                "time_ns must be non-negative",
            ),
            (
                "category",
                "forged_category",
                "fields changed between modes",
            ),
            (
                "sequence_sha256",
                "not-a-hash",
                "invalid sequence SHA-256",
            ),
        ]

        original_raw = self.config.raw_csv.read_text(encoding="utf-8")
        original_manifest = self.config.manifest_json.read_text(encoding="utf-8")
        for field, value, expected_error in tamper_cases:
            with self.subTest(field=field):
                self.config.raw_csv.write_text(
                    original_raw,
                    encoding="utf-8",
                )
                self.config.manifest_json.write_text(
                    original_manifest,
                    encoding="utf-8",
                )
                rows = self._read_rows(self.config.raw_csv)
                rows[0][field] = value
                self._write_rows(
                    self.config.raw_csv,
                    rows,
                    runner.RAW_FIELDS,
                )
                self._refresh_manifest_entry("raw_csv")

                report = validate_outputs(self.root)

                self.assertFalse(report["valid"])
                self.assertTrue(
                    any(expected_error in error for error in report["errors"]),
                    report["errors"],
                )

    def test_validator_rejects_seed_inconsistent_mode_order(self):
        rows = self._read_rows(self.config.raw_csv)
        first_case = rows[0]["case_id"]
        first_round = [
            row
            for row in rows
            if row["case_id"] == first_case and row["run_index"] == "1"
        ]
        first_round[0]["mode_position"], first_round[1]["mode_position"] = (
            first_round[1]["mode_position"],
            first_round[0]["mode_position"],
        )
        self._write_rows(self.config.raw_csv, rows, runner.RAW_FIELDS)
        self._refresh_manifest_entry("raw_csv")

        report = validate_outputs(self.root)

        self.assertFalse(report["valid"])
        self.assertTrue(
            any(
                "mode order does not match seed" in error
                for error in report["errors"]
            ),
            report["errors"],
        )

    def test_validator_rejects_missing_mode_row(self):
        rows = self._read_rows(self.config.raw_csv)
        rows.pop()
        self._write_rows(self.config.raw_csv, rows, runner.RAW_FIELDS)
        self._refresh_manifest_entry("raw_csv", update_row_count=True)

        report = validate_outputs(self.root)

        self.assertFalse(report["valid"])
        self.assertTrue(
            any("raw row count" in error for error in report["errors"]),
            report["errors"],
        )

    def test_validator_rejects_summary_tampering_with_fresh_hash(self):
        rows = self._read_rows(self.config.case_summary_csv)
        rows[0]["median_time_ns"] = str(
            int(float(rows[0]["median_time_ns"])) + 1
        )
        self._write_rows(
            self.config.case_summary_csv,
            rows,
            runner.CASE_SUMMARY_FIELDS,
        )
        self._refresh_manifest_entry("case_summary_csv")

        report = validate_outputs(self.root)

        self.assertFalse(report["valid"])
        self.assertIn(
            "case summary does not match recomputed raw summary",
            report["errors"],
        )

    def test_validator_rejects_manifest_hash_mismatch(self):
        with self.config.raw_csv.open("a", encoding="utf-8") as handle:
            handle.write("\n")

        report = validate_outputs(self.root)

        self.assertFalse(report["valid"])
        self.assertIn(
            "manifest hash mismatch for raw_csv",
            report["errors"],
        )


if __name__ == "__main__":
    unittest.main()
