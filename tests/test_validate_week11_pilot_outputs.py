"""Adversarial tests for the Week 11 pilot evidence validator."""

import csv
import hashlib
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "experiments"))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import run_week11_pilot as runner  # noqa: E402
import validate_week11_pilot_outputs as validator  # noqa: E402
from week11_execution_context import output_dir_for_execution  # noqa: E402
from week11_experiment_protocol import (  # noqa: E402
    WEEK11_EXPERIMENT_PROTOCOL,
    protocol_to_dict,
)


EXECUTION_ID = "week11_pilot_v1__validator_test_run001"
SOURCE_COMMIT = "a" * 40


class ValidateWeek11PilotOutputsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        def diagnostics_for(sequence):
            n = len(sequence)
            return {
                "invariants_valid": True,
                "output": sorted(sequence),
                "processed_count": n,
                "trace": [{} for _ in range(n + 3)],
                "metrics": {
                    name: n + index
                    for index, name in enumerate(
                        validator.PAPER_METRIC_NAMES,
                        start=1,
                    )
                },
            }

        validator.rebuild_expected_cases.cache_clear()
        diagnostics = Mock(side_effect=diagnostics_for)
        with patch.object(
            validator,
            "paper_jordan_diagnostics_valid",
            diagnostics,
        ):
            cls.expected_cases = validator.rebuild_expected_cases()
        if diagnostics.call_count != WEEK11_EXPERIMENT_PROTOCOL.case_count:
            raise AssertionError(
                "validator did not rebuild one checked diagnostic per case"
            )

    def _benchmark_environment(self):
        return {
            "processor_class": "Test Processor",
            "architecture": "test-arch",
            "memory_gb": 16,
            "logical_cpu_count": 8,
            "os_name": "Test OS",
            "os_version": "1.0",
            "os_build": "build-1",
            "python_implementation": "CPython",
            "python_version": "3.12.4",
        }

    def _environment(self, power_status=None):
        protocol = WEEK11_EXPERIMENT_PROTOCOL
        return {
            "execution_id": EXECUTION_ID,
            "output_dir": output_dir_for_execution(EXECUTION_ID),
            "benchmark_environment": self._benchmark_environment(),
            "source_commit": SOURCE_COMMIT,
            "protocol_version": protocol.protocol_version,
            "captured_before_timing": True,
            "timestamp_utc": "2026-07-31T12:00:00+00:00",
            "git_dirty": False,
            "head_matches_origin_main": True,
            "available_disk_bytes": 1_000_000,
            "perf_counter_resolution": 1e-9,
            "power_status": power_status
            or {
                "source": "test_power",
                "status": "available",
                "on_ac_power": True,
                "battery_state": "charging",
            },
            "load_command_success": True,
            "load_snapshot": "load averages: 0.10 0.10 0.10",
            "paper_execution_mode": protocol.paper_execution_mode,
            "audit_execution_mode": protocol.audit_execution_mode,
        }

    def _raw_rows(self):
        protocol = WEEK11_EXPERIMENT_PROTOCOL
        rows = []
        ordered_cases = sorted(
            self.expected_cases.values(),
            key=lambda case: case["case_execution_position"],
        )
        for case in ordered_cases:
            for run_index in range(1, protocol.measured_runs + 1):
                algorithms = runner.algorithm_order_for_round(
                    protocol.algorithms,
                    protocol.algorithm_order_seed,
                    case["case_index"],
                    run_index,
                )
                for position, algorithm in enumerate(algorithms, start=1):
                    row = {
                        "protocol_version": protocol.protocol_version,
                        "execution_id": EXECUTION_ID,
                        "case_id": case["case_id"],
                        "case_index": case["case_index"],
                        "family": case["family"],
                        "n": case["n"],
                        "seed": "" if case["seed"] is None else case["seed"],
                        "sequence_sha256": case["sequence_sha256"],
                        "case_execution_position": case[
                            "case_execution_position"
                        ],
                        **{
                            field: case["profile"][field]
                            for field in validator.STRUCTURAL_FIELDS
                        },
                        "algorithm": algorithm,
                        "paper_execution_mode": protocol.paper_execution_mode,
                        "audit_execution_mode": protocol.audit_execution_mode,
                        "run_index": run_index,
                        "measured_round": run_index,
                        "algorithm_position": position,
                        "time_ns": (
                            case["case_index"] * 100_000
                            + run_index * 100
                            + position
                        ),
                        "oracle_valid": True,
                        "oracle_reason": "",
                        "output_correct": True,
                        "audit_passed": True,
                        "error": "",
                    }
                    rows.append(row)
        return rows

    def _audit_rows(self):
        protocol = WEEK11_EXPERIMENT_PROTOCOL
        rows = []
        for case in sorted(
            self.expected_cases.values(),
            key=lambda item: item["case_index"],
        ):
            row = {
                "protocol_version": protocol.protocol_version,
                "execution_id": EXECUTION_ID,
                "case_id": case["case_id"],
                "case_index": case["case_index"],
                "family": case["family"],
                "n": case["n"],
                "seed": "" if case["seed"] is None else case["seed"],
                "sequence_sha256": case["sequence_sha256"],
                "oracle_valid": True,
                "oracle_reason": "",
                **{
                    field: case["profile"][field]
                    for field in validator.STRUCTURAL_FIELDS
                },
                "audit_execution_mode": protocol.audit_execution_mode,
                **case["audit"],
            }
            rows.append(row)
        return rows

    def _write_csv(self, path, fields, rows):
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)

    def _read_csv(self, path):
        with path.open(newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))

    def _sha256(self, path):
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def _refresh_manifest(self, run_dir):
        manifest_path = run_dir / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for label, filename in validator.MANIFEST_FILE_LABELS.items():
            manifest["files"][label]["sha256"] = self._sha256(
                run_dir / filename
            )
        manifest_path.write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    def _build_evidence(self, environment=None):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        run_dir = Path(temporary.name) / EXECUTION_ID
        run_dir.mkdir()

        raw_rows = self._raw_rows()
        case_rows = runner.summarize_by_case(raw_rows)
        group_rows = runner.summarize_by_group(case_rows)
        audit_rows = self._audit_rows()
        payloads = {
            "raw.csv": (validator.RAW_FIELDS, raw_rows),
            "case_summary.csv": (validator.CASE_SUMMARY_FIELDS, case_rows),
            "group_summary.csv": (
                validator.GROUP_SUMMARY_FIELDS,
                group_rows,
            ),
            "case_audit.csv": (validator.CASE_AUDIT_FIELDS, audit_rows),
        }
        for filename, (fields, rows) in payloads.items():
            self._write_csv(run_dir / filename, fields, rows)

        (run_dir / "config.json").write_text(
            json.dumps(protocol_to_dict(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        (run_dir / "environment.json").write_text(
            json.dumps(
                environment or self._environment(),
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        manifest = {
            "protocol_version": WEEK11_EXPERIMENT_PROTOCOL.protocol_version,
            "execution_id": EXECUTION_ID,
            "source_commit": SOURCE_COMMIT,
            "row_counts": {
                "raw": len(raw_rows),
                "case_summary": len(case_rows),
                "group_summary": len(group_rows),
                "case_audit": len(audit_rows),
            },
            "files": {
                label: {
                    "path": filename,
                    "sha256": self._sha256(run_dir / filename),
                }
                for label, filename in validator.MANIFEST_FILE_LABELS.items()
            },
        }
        (run_dir / "manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return run_dir

    def _rewrite_raw(self, run_dir, mutate):
        rows = self._read_csv(run_dir / "raw.csv")
        mutate(rows)
        self._write_csv(run_dir / "raw.csv", validator.RAW_FIELDS, rows)
        self._refresh_manifest(run_dir)

    def _rewrite_audit(self, run_dir, mutate):
        rows = self._read_csv(run_dir / "case_audit.csv")
        mutate(rows)
        self._write_csv(
            run_dir / "case_audit.csv",
            validator.CASE_AUDIT_FIELDS,
            rows,
        )
        self._refresh_manifest(run_dir)

    def test_runner_and_validator_schemas_match_without_shared_definitions(self):
        self.assertEqual(validator.RAW_FIELDS, runner.RAW_FIELDS)
        self.assertEqual(
            validator.CASE_SUMMARY_FIELDS,
            runner.CASE_SUMMARY_FIELDS,
        )
        self.assertEqual(
            validator.GROUP_SUMMARY_FIELDS,
            runner.GROUP_SUMMARY_FIELDS,
        )
        self.assertEqual(
            validator.CASE_AUDIT_FIELDS,
            runner.CASE_AUDIT_FIELDS,
        )

    def test_valid_full_evidence_is_accepted(self):
        report = validator.validate_outputs(self._build_evidence())

        self.assertTrue(report["valid"], report["errors"])
        self.assertEqual(
            report["row_counts"],
            {
                "raw": 1050,
                "case_summary": 105,
                "group_summary": 45,
                "case_audit": 35,
            },
        )

    def test_coordinated_case_metadata_tampering_is_rejected(self):
        mutations = {
            "family": "forged_family",
            "n": "999",
            "seed": "999999",
            "sequence_sha256": "0" * 64,
            "max_depth": "-999",
        }
        for field, value in mutations.items():
            with self.subTest(field=field):
                run_dir = self._build_evidence()
                case_id = next(iter(self.expected_cases))

                def mutate(rows):
                    for row in rows:
                        if row["case_id"] == case_id:
                            row[field] = value

                self._rewrite_raw(run_dir, mutate)
                self._rewrite_audit(run_dir, mutate)
                report = validator.validate_outputs(run_dir)
                self.assertFalse(report["valid"])

    def test_scheduling_and_mode_tampering_is_rejected(self):
        mutations = (
            ("case_execution_position", "999"),
            ("algorithm_position", "3"),
            ("algorithm_position", "4"),
            ("algorithm_position", "999"),
            ("run_index", "999"),
            ("measured_round", "9"),
            ("paper_execution_mode", "checked"),
            ("audit_execution_mode", "minimal"),
        )
        for field, value in mutations:
            with self.subTest(field=field, value=value):
                run_dir = self._build_evidence()

                def mutate(rows):
                    rows[0][field] = value

                self._rewrite_raw(run_dir, mutate)
                report = validator.validate_outputs(run_dir)
                self.assertFalse(report["valid"])

    def test_unexpected_validator_error_fails_closed(self):
        run_dir = self._build_evidence()
        with patch.object(
            validator,
            "_validate_raw_rows",
            side_effect=IndexError("simulated internal failure"),
        ):
            report = validator.validate_outputs(run_dir)

        self.assertFalse(report["valid"])
        self.assertIn("IndexError", report["errors"][0])

    def test_missing_duplicate_and_extra_raw_rows_are_rejected(self):
        for mutation in ("missing", "duplicate", "extra"):
            with self.subTest(mutation=mutation):
                run_dir = self._build_evidence()
                rows = self._read_csv(run_dir / "raw.csv")
                if mutation == "missing":
                    rows.pop()
                elif mutation == "duplicate":
                    rows[-1] = dict(rows[0])
                else:
                    rows.append(dict(rows[0]))
                self._write_csv(
                    run_dir / "raw.csv",
                    validator.RAW_FIELDS,
                    rows,
                )
                self._refresh_manifest(run_dir)

                report = validator.validate_outputs(run_dir)
                self.assertFalse(report["valid"])

    def test_coordinated_summary_tampering_is_rejected(self):
        run_dir = self._build_evidence()
        rows = self._read_csv(run_dir / "case_summary.csv")
        rows[0]["median_time_ns"] = "123"
        self._write_csv(
            run_dir / "case_summary.csv",
            validator.CASE_SUMMARY_FIELDS,
            rows,
        )
        self._refresh_manifest(run_dir)

        report = validator.validate_outputs(run_dir)
        self.assertFalse(report["valid"])

    def test_missing_and_unknown_csv_fields_fail_closed(self):
        for mutation in ("missing", "unknown", "duplicate"):
            with self.subTest(mutation=mutation):
                run_dir = self._build_evidence()
                rows = self._read_csv(run_dir / "raw.csv")
                fields = list(validator.RAW_FIELDS)
                if mutation == "missing":
                    fields.remove("paper_execution_mode")
                    for row in rows:
                        row.pop("paper_execution_mode")
                elif mutation == "unknown":
                    fields.append("unknown_field")
                    for row in rows:
                        row["unknown_field"] = "unexpected"
                if mutation == "duplicate":
                    path = run_dir / "raw.csv"
                    lines = path.read_text(encoding="utf-8").splitlines()
                    header = lines[0].replace(
                        "protocol_version",
                        "execution_id",
                        1,
                    )
                    path.write_text(
                        "\n".join([header, *lines[1:]]) + "\n",
                        encoding="utf-8",
                    )
                else:
                    self._write_csv(run_dir / "raw.csv", fields, rows)
                self._refresh_manifest(run_dir)

                report = validator.validate_outputs(run_dir)
                self.assertFalse(report["valid"])

    def test_invalid_summary_numbers_are_rejected(self):
        for field, value in (
            ("mean_time_ns", "not-a-number"),
            ("stdev_time_ns", "nan"),
            ("median_time_ns", "inf"),
            ("iqr_time_ns", "-1"),
        ):
            with self.subTest(field=field):
                run_dir = self._build_evidence()
                rows = self._read_csv(run_dir / "case_summary.csv")
                rows[0][field] = value
                self._write_csv(
                    run_dir / "case_summary.csv",
                    validator.CASE_SUMMARY_FIELDS,
                    rows,
                )
                self._refresh_manifest(run_dir)

                report = validator.validate_outputs(run_dir)
                self.assertFalse(report["valid"])

    def test_invalid_numbers_and_certification_fields_are_rejected(self):
        mutations = {
            "run_index": "not-an-integer",
            "time_ns": "-1",
            "nesting_density": "nan",
            "oracle_valid": "False",
            "output_correct": "False",
            "audit_passed": "False",
            "error": "RuntimeError: failed",
        }
        for field, value in mutations.items():
            with self.subTest(field=field):
                run_dir = self._build_evidence()

                def mutate(rows):
                    rows[0][field] = value

                self._rewrite_raw(run_dir, mutate)
                report = validator.validate_outputs(run_dir)
                self.assertFalse(report["valid"])

    def test_invalid_audit_fields_are_rejected(self):
        metric_field = validator.PAPER_AUDIT_FIELDS[0]
        mutations = {
            "audit_passed": "False",
            "diagnostic_output_sha256": "0" * 64,
            "diagnostic_processed_count": "-1",
            "diagnostic_trace_event_count": "nan",
            metric_field: "-1",
            f"{metric_field}_nonnegative_forgery": None,
        }
        for field, value in mutations.items():
            with self.subTest(field=field):
                run_dir = self._build_evidence()

                def mutate(rows):
                    if field.endswith("_nonnegative_forgery"):
                        rows[0][metric_field] = str(
                            int(rows[0][metric_field]) + 1
                        )
                    else:
                        rows[0][field] = value

                self._rewrite_audit(run_dir, mutate)
                report = validator.validate_outputs(run_dir)
                self.assertFalse(report["valid"])

    def test_damaged_json_and_wrong_container_fail_closed(self):
        cases = {
            "damaged": "{not-json",
            "wrong-container": "[]",
        }
        for label, content in cases.items():
            with self.subTest(label=label):
                run_dir = self._build_evidence()
                (run_dir / "config.json").write_text(
                    content,
                    encoding="utf-8",
                )
                self._refresh_manifest(run_dir)

                report = validator.validate_outputs(run_dir)
                self.assertFalse(report["valid"])

    def test_environment_contract_drift_is_rejected(self):
        run_dir = self._build_evidence()
        path = run_dir / "environment.json"
        environment = json.loads(path.read_text(encoding="utf-8"))
        environment["processor_class"] = "duplicated top-level value"
        environment["paper_execution_mode"] = "checked"
        path.write_text(
            json.dumps(environment, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        self._refresh_manifest(run_dir)

        report = validator.validate_outputs(run_dir)
        self.assertFalse(report["valid"])

    def test_linux_desktop_power_status_is_accepted(self):
        environment = self._environment(
            power_status={
                "source": "linux_sysfs",
                "status": "not_applicable",
                "on_ac_power": None,
                "battery_state": "not_applicable",
            }
        )
        report = validator.validate_outputs(
            self._build_evidence(environment=environment)
        )

        self.assertTrue(report["valid"], report["errors"])

    def test_inconsistent_available_power_status_is_rejected(self):
        environment = self._environment(
            power_status={
                "source": "linux_sysfs",
                "status": "available",
                "on_ac_power": True,
                "battery_state": "not_applicable",
            }
        )

        report = validator.validate_outputs(
            self._build_evidence(environment=environment)
        )

        self.assertFalse(report["valid"])

    def test_stale_valid_report_cannot_authorize_tampered_evidence(self):
        run_dir = self._build_evidence()
        first = validator.validate_outputs(run_dir)
        self.assertTrue(first["valid"])

        rows = self._read_csv(run_dir / "raw.csv")
        rows[0]["time_ns"] = "-1"
        self._write_csv(run_dir / "raw.csv", validator.RAW_FIELDS, rows)

        second = validator.validate_outputs(run_dir)
        self.assertFalse(second["valid"])

    def test_missing_evidence_returns_a_report_instead_of_raising(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        run_dir = Path(temporary.name) / EXECUTION_ID
        run_dir.mkdir()

        report = validator.validate_outputs(run_dir)

        self.assertFalse(report["valid"])
        self.assertTrue((run_dir / "validation_report.json").is_file())

    def test_manifest_hash_mismatch_is_rejected(self):
        run_dir = self._build_evidence()
        shutil.copyfile(
            run_dir / "raw.csv",
            run_dir / "raw-copy.csv",
        )
        with (run_dir / "raw.csv").open("a", encoding="utf-8") as handle:
            handle.write("\n")

        report = validator.validate_outputs(run_dir)
        self.assertFalse(report["valid"])


if __name__ == "__main__":
    unittest.main()
