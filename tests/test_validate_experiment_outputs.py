"""Tests for benchmark output validation."""

import csv
import json
import tempfile
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "experiments"))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from generators import FLAT_VALID, INCREMENTAL_VALID  # noqa: E402
from run_week7_pilot import DEFAULT_ALGORITHM_NAMES, PilotConfig, run_pilot  # noqa: E402
from validate_experiment_outputs import validate_outputs  # noqa: E402


class ValidateExperimentOutputsTests(unittest.TestCase):
    def _config(self, run_dir):
        root = Path(run_dir)
        return PilotConfig(
            families=[FLAT_VALID, INCREMENTAL_VALID],
            sizes=[8],
            algorithms=list(DEFAULT_ALGORITHM_NAMES),
            randomized_cases=1,
            warmup_runs=0,
            measured_runs=1,
            seed=23,
            algorithm_order_seed=29,
            case_order_seed=31,
            run_id="validator_test",
            run_dir=root,
            raw_csv=root / "raw.csv",
            case_summary_csv=root / "case_summary.csv",
            group_summary_csv=root / "group_summary.csv",
            environment_json=root / "environment.json",
            auto_report_md=root / "auto_report.md",
            config_json=root / "config.json",
            manifest_json=root / "manifest.json",
        )

    def _read_rows(self, path):
        with Path(path).open(newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))

    def _write_rows(self, path, rows):
        with Path(path).open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)

    def _assert_tamper_is_rejected(self, mutator):
        with tempfile.TemporaryDirectory() as tmpdir:
            config = self._config(Path(tmpdir) / "run")
            run_pilot(config)
            mutator(config)

            report = validate_outputs(config.run_dir)

            self.assertFalse(report["valid"])
            self.assertTrue(report["errors"])

    def test_validate_outputs_accepts_clean_run_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config = self._config(Path(tmpdir) / "run")
            run_pilot(config)

            report = validate_outputs(config.run_dir)

            self.assertTrue(report["valid"])
            self.assertEqual(report["errors"], [])
            self.assertEqual(report["row_counts"]["raw"], 6)
            self.assertTrue((config.run_dir / "validation_report.json").exists())

    def test_validate_outputs_rejects_tampered_raw_correctness(self):
        def mutate(config):
            rows = self._read_rows(config.raw_csv)
            rows[0]["overall_correct"] = "False"
            self._write_rows(config.raw_csv, rows)

        self._assert_tamper_is_rejected(mutate)

    def test_validate_outputs_rejects_tampered_raw_timing(self):
        def mutate(config):
            rows = self._read_rows(config.raw_csv)
            rows[0]["time_ns"] = "999999999999"
            self._write_rows(config.raw_csv, rows)

        self._assert_tamper_is_rejected(mutate)

    def test_validate_outputs_rejects_tampered_case_summary(self):
        def mutate(config):
            rows = self._read_rows(config.case_summary_csv)
            rows[0]["median_time_ns"] = "999999999999"
            self._write_rows(config.case_summary_csv, rows)

        self._assert_tamper_is_rejected(mutate)

    def test_validate_outputs_rejects_tampered_group_summary(self):
        def mutate(config):
            rows = self._read_rows(config.group_summary_csv)
            rows[0]["median_case_time_ns"] = "999999999999"
            self._write_rows(config.group_summary_csv, rows)

        self._assert_tamper_is_rejected(mutate)

    def test_validate_outputs_rejects_tampered_environment(self):
        def mutate(config):
            data = json.loads(config.environment_json.read_text(encoding="utf-8"))
            data["run_id"] = "wrong"
            config.environment_json.write_text(
                json.dumps(data, indent=2) + "\n",
                encoding="utf-8",
            )

        self._assert_tamper_is_rejected(mutate)

    def test_validate_outputs_rejects_wrong_manifest_hash(self):
        def mutate(config):
            data = json.loads(config.manifest_json.read_text(encoding="utf-8"))
            data["files"]["raw_csv"]["sha256"] = "0" * 64
            config.manifest_json.write_text(
                json.dumps(data, indent=2) + "\n",
                encoding="utf-8",
            )

        self._assert_tamper_is_rejected(mutate)

    def test_validate_outputs_rejects_missing_raw_row(self):
        def mutate(config):
            rows = self._read_rows(config.raw_csv)
            self._write_rows(config.raw_csv, rows[:-1])

        self._assert_tamper_is_rejected(mutate)

    def test_validate_outputs_rejects_duplicate_raw_row(self):
        def mutate(config):
            rows = self._read_rows(config.raw_csv)
            self._write_rows(config.raw_csv, rows + [dict(rows[0])])

        self._assert_tamper_is_rejected(mutate)

    def test_validate_outputs_rejects_malformed_numeric_field(self):
        def mutate(config):
            rows = self._read_rows(config.raw_csv)
            rows[0]["containment_pair_density"] = "not-a-number"
            self._write_rows(config.raw_csv, rows)

        self._assert_tamper_is_rejected(mutate)


if __name__ == "__main__":
    unittest.main()
