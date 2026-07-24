"""Tests for generator coverage-audit output validation."""

import csv
import json
import tempfile
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "experiments"))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from audit_generator_coverage import (  # noqa: E402
    audit_generator_coverage,
    summarize_audit_rows,
    write_audit,
    write_audit_config,
    write_audit_manifest,
    write_audit_summary,
)
from generators import FLAT_VALID, INCREMENTAL_VALID  # noqa: E402
from validate_generator_audit_outputs import validate_audit_outputs  # noqa: E402


class ValidateGeneratorAuditOutputsTests(unittest.TestCase):
    def _write_clean_run(self, run_dir):
        root = Path(run_dir)
        families = [FLAT_VALID, INCREMENTAL_VALID]
        sizes = [8]
        rows = audit_generator_coverage(
            families=families,
            sizes=sizes,
            randomized_repetitions=1,
            seed=41,
        )
        summary_rows = summarize_audit_rows(rows)
        config_json = root / "audit_config.json"
        audit_csv = root / "coverage_audit.csv"
        summary_csv = root / "coverage_summary.csv"
        manifest_json = root / "audit_manifest.json"

        write_audit_config(
            config_json,
            run_id="audit_validator_test",
            families=families,
            sizes=sizes,
            randomized_repetitions=1,
            seed=41,
        )
        write_audit(rows, audit_csv)
        write_audit_summary(summary_rows, summary_csv)
        write_audit_manifest(
            manifest_json,
            run_id="audit_validator_test",
            config_json=config_json,
            output_csv=audit_csv,
            summary_csv=summary_csv,
            rows=rows,
            summary_rows=summary_rows,
        )
        return {
            "run_dir": root,
            "audit_csv": audit_csv,
            "summary_csv": summary_csv,
            "manifest_json": manifest_json,
        }

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
            paths = self._write_clean_run(Path(tmpdir) / "audit")
            mutator(paths)

            report = validate_audit_outputs(paths["run_dir"])

            self.assertFalse(report["valid"])
            self.assertTrue(report["errors"])

    def test_validate_audit_outputs_accepts_clean_run_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = self._write_clean_run(Path(tmpdir) / "audit")

            report = validate_audit_outputs(paths["run_dir"])

            self.assertTrue(report["valid"])
            self.assertEqual(report["errors"], [])
            self.assertEqual(report["row_counts"]["coverage_audit"], 2)
            self.assertEqual(report["row_counts"]["coverage_summary"], 2)

    def test_validate_audit_outputs_rejects_tampered_audit_csv(self):
        def mutate(paths):
            rows = self._read_rows(paths["audit_csv"])
            rows[0]["sequence_hash"] = "0" * 64
            self._write_rows(paths["audit_csv"], rows)

        self._assert_tamper_is_rejected(mutate)

    def test_validate_audit_outputs_rejects_tampered_summary_csv(self):
        def mutate(paths):
            rows = self._read_rows(paths["summary_csv"])
            rows[0]["duplicate_case_count"] = "999"
            self._write_rows(paths["summary_csv"], rows)

        self._assert_tamper_is_rejected(mutate)

    def test_validate_audit_outputs_rejects_wrong_manifest_hash(self):
        def mutate(paths):
            data = json.loads(paths["manifest_json"].read_text(encoding="utf-8"))
            data["files"]["coverage_audit_csv"]["sha256"] = "0" * 64
            paths["manifest_json"].write_text(
                json.dumps(data, indent=2) + "\n",
                encoding="utf-8",
            )

        self._assert_tamper_is_rejected(mutate)

    def test_validate_audit_outputs_rejects_malformed_density(self):
        def mutate(paths):
            rows = self._read_rows(paths["audit_csv"])
            rows[0]["containment_pair_density"] = "not-a-number"
            self._write_rows(paths["audit_csv"], rows)

        self._assert_tamper_is_rejected(mutate)


if __name__ == "__main__":
    unittest.main()
