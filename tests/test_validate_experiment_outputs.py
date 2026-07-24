"""Tests for benchmark output validation."""

import csv
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
        with tempfile.TemporaryDirectory() as tmpdir:
            config = self._config(Path(tmpdir) / "run")
            run_pilot(config)

            with config.raw_csv.open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            rows[0]["overall_correct"] = "False"
            with config.raw_csv.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)

            report = validate_outputs(config.run_dir)

            self.assertFalse(report["valid"])
            self.assertTrue(report["errors"])


if __name__ == "__main__":
    unittest.main()
