"""Adversarial tests for the Week 12 formal evidence validator."""

import csv
import hashlib
import json
import random
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "experiments"))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import run_week11_pilot as timing_support  # noqa: E402
import run_week12_formal_sorting as runner  # noqa: E402
import validate_week12_formal_sorting_outputs as validator  # noqa: E402
from week12_experiment_gate import (  # noqa: E402
    WEEK12_EXPERIMENT_GATE,
    gate_to_dict,
)


EXECUTION_ID = "week12_formal_sorting_v1__validator_test_run001"
SOURCE_COMMIT = "a" * 40


class ValidateWeek12FormalSortingOutputsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        gate = WEEK12_EXPERIMENT_GATE
        cases = []
        for family in gate.valid_families:
            for n in gate.sizes:
                for case_number in range(1, gate.repetitions_for_family(family) + 1):
                    case_id = runner.make_case_id(family, n, case_number)
                    seed = runner.seed_for_case(family, n, case_number, gate.seed)
                    profile = {
                        field: (
                            family
                            if field == "category"
                            else 0.5
                            if field.endswith("density") or field.endswith("ratio")
                            else n + case_number
                        )
                        for field in runner.STRUCTURAL_FIELDS
                    }
                    cases.append(
                        {
                            "case_id": case_id,
                            "case_index": len(cases) + 1,
                            "family": family,
                            "n": n,
                            "seed": seed,
                            "sequence_sha256": hashlib.sha256(
                                case_id.encode("ascii")
                            ).hexdigest(),
                            "profile": profile,
                            "audit": {
                                "audit_passed": True,
                                "diagnostic_output_sha256": hashlib.sha256(
                                    f"output:{case_id}".encode("ascii")
                                ).hexdigest(),
                                "diagnostic_processed_count": n,
                                "diagnostic_trace_event_count": n + 3,
                                **{
                                    f"paper_{name}": n + index
                                    for index, name in enumerate(
                                        validator.PAPER_METRIC_NAMES,
                                        start=1,
                                    )
                                },
                            },
                        }
                    )
        ordered = list(cases)
        random.Random(gate.case_order_seed).shuffle(ordered)
        positions = {
            case["case_id"]: position
            for position, case in enumerate(ordered, start=1)
        }
        cls.expected_cases = {
            case["case_id"]: {
                **case,
                "case_execution_position": positions[case["case_id"]],
            }
            for case in cases
        }

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

    def _environment(self):
        environment = {
            "execution_id": EXECUTION_ID,
            "output_dir": f"results/runs/{EXECUTION_ID}",
            "benchmark_environment": self._benchmark_environment(),
            "source_commit": SOURCE_COMMIT,
            "protocol_version": WEEK12_EXPERIMENT_GATE.protocol_version,
            "captured_before_timing": True,
            "timestamp_utc": "2026-08-04T10:00:00+00:00",
            "git_dirty": False,
            "head_matches_origin_main": True,
            "available_disk_bytes": 2 << 30,
            "perf_counter_resolution": 1e-9,
            "power_status": {
                "source": "test",
                "status": "not_applicable",
                "on_ac_power": None,
                "battery_state": "not_applicable",
                "battery_percent": None,
                "low_power_mode": None,
            },
            "paper_execution_mode": "minimal",
            "audit_execution_mode": "checked",
        }
        with patch.object(
            timing_support.os,
            "getloadavg",
            return_value=(0.40, 0.45, 0.50),
        ):
            load = timing_support.capture_load_status(8)
        environment["timing_readiness"] = (
            timing_support.require_timing_ready_environment(
                environment,
                load,
                execution_stage="formal",
            )
        )
        return environment

    def _raw_rows(self):
        gate = WEEK12_EXPERIMENT_GATE
        rows = []
        ordered_cases = sorted(
            self.expected_cases.values(),
            key=lambda case: case["case_execution_position"],
        )
        for case in ordered_cases:
            for run_index in range(1, gate.measured_runs + 1):
                algorithms = runner.algorithm_order_for_round(
                    gate.algorithms,
                    gate.algorithm_order_seed,
                    case["case_index"],
                    run_index,
                )
                for position, algorithm in enumerate(algorithms, start=1):
                    rows.append(
                        {
                            "protocol_version": gate.protocol_version,
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
                                for field in runner.STRUCTURAL_FIELDS
                            },
                            "algorithm": algorithm,
                            "paper_execution_mode": gate.paper_execution_mode,
                            "audit_execution_mode": gate.audit_execution_mode,
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
                    )
        return rows

    def _audit_rows(self):
        gate = WEEK12_EXPERIMENT_GATE
        rows = []
        for case in sorted(
            self.expected_cases.values(),
            key=lambda item: item["case_index"],
        ):
            rows.append(
                {
                    "protocol_version": gate.protocol_version,
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
                        for field in runner.STRUCTURAL_FIELDS
                    },
                    "audit_execution_mode": gate.audit_execution_mode,
                    **case["audit"],
                }
            )
        return rows

    def _write_csv(self, path, fields, rows):
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)

    def _read_csv(self, path):
        with path.open(newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))

    def _refresh_manifest(self, run_dir):
        manifest_path = run_dir / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for label, filename in validator.MANIFEST_FILES.items():
            manifest["files"][label]["sha256"] = runner.file_sha256(
                run_dir / filename
            )
        manifest_path.write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    def _build_evidence(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        run_dir = Path(temporary.name) / EXECUTION_ID
        run_dir.mkdir()
        raw_rows = self._raw_rows()
        case_rows = runner.summarize_by_case(raw_rows)
        group_rows = runner.summarize_by_group(case_rows)
        audit_rows = self._audit_rows()
        for filename, fields, rows in (
            ("raw.csv", runner.RAW_FIELDS, raw_rows),
            ("case_summary.csv", runner.CASE_SUMMARY_FIELDS, case_rows),
            ("group_summary.csv", runner.GROUP_SUMMARY_FIELDS, group_rows),
            ("case_audit.csv", runner.CASE_AUDIT_FIELDS, audit_rows),
        ):
            self._write_csv(run_dir / filename, fields, rows)
        (run_dir / "config.json").write_text(
            json.dumps(gate_to_dict(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        (run_dir / "environment.json").write_text(
            json.dumps(self._environment(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        manifest = {
            "protocol_version": WEEK12_EXPERIMENT_GATE.protocol_version,
            "execution_id": EXECUTION_ID,
            "source_commit": SOURCE_COMMIT,
            "row_counts": {
                "raw": len(raw_rows),
                "case_summary": len(case_rows),
                "group_summary": len(group_rows),
                "case_audit": len(audit_rows),
            },
            "experiment_started_at_utc": "2026-08-04T10:00:00+00:00",
            "experiment_completed_at_utc": "2026-08-04T10:10:00+00:00",
            "experiment_elapsed_ns": 600_000_000_000,
            "experiment_elapsed_scope": validator.EXPERIMENT_ELAPSED_SCOPE,
            "measured_call_total_ns": sum(
                int(row["time_ns"]) for row in raw_rows
            ),
            "files": {
                label: {
                    "path": filename,
                    "sha256": runner.file_sha256(run_dir / filename),
                }
                for label, filename in validator.MANIFEST_FILES.items()
            },
        }
        (run_dir / "manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return run_dir

    def _rewrite_csv(self, run_dir, filename, fields, mutate):
        rows = self._read_csv(run_dir / filename)
        mutate(rows)
        self._write_csv(run_dir / filename, fields, rows)

    def _validate(self, run_dir, report_json=None):
        with patch.object(
            validator,
            "rebuild_expected_cases",
            return_value=self.expected_cases,
        ):
            return validator.validate_outputs(run_dir, report_json)

    def test_valid_evidence_and_external_revalidation(self):
        run_dir = self._build_evidence()
        built_in = self._validate(run_dir)
        external_path = run_dir.parent / "week12_independent_validation.json"
        external = self._validate(run_dir, external_path)

        self.assertTrue(built_in["valid"], built_in["errors"])
        self.assertTrue(external["valid"], external["errors"])
        self.assertEqual(built_in["row_counts"]["raw"], 3600)
        self.assertGreater(built_in["validation_elapsed_ns"], 0)
        self.assertTrue((run_dir / "validation_report.json").is_file())
        self.assertTrue(external_path.is_file())

    def test_raw_product_and_schedule_corruption_fail_closed(self):
        mutations = {
            "missing row": lambda rows: rows.pop(),
            "duplicate row": lambda rows: rows.append(dict(rows[0])),
            "bad position": lambda rows: rows[0].__setitem__(
                "algorithm_position", "999"
            ),
            "bad run": lambda rows: rows[0].__setitem__("run_index", "999"),
            "incorrect output": lambda rows: rows[0].__setitem__(
                "output_correct", "False"
            ),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label):
                run_dir = self._build_evidence()
                self._rewrite_csv(
                    run_dir,
                    "raw.csv",
                    runner.RAW_FIELDS,
                    mutate,
                )
                self._refresh_manifest(run_dir)
                report = self._validate(run_dir)
                self.assertFalse(report["valid"])

    def test_rebuilt_case_and_audit_provenance_detects_coordinated_changes(self):
        run_dir = self._build_evidence()
        target = next(iter(self.expected_cases))

        def change_raw(rows):
            for row in rows:
                if row["case_id"] == target:
                    row["sequence_sha256"] = "0" * 64
                    row["seed"] = "999999"

        def change_audit(rows):
            for row in rows:
                if row["case_id"] == target:
                    row["sequence_sha256"] = "0" * 64
                    row["seed"] = "999999"
                    row["paper_output_insertions"] = str(
                        int(row["paper_output_insertions"]) + 1
                    )

        self._rewrite_csv(run_dir, "raw.csv", runner.RAW_FIELDS, change_raw)
        self._rewrite_csv(
            run_dir,
            "case_audit.csv",
            runner.CASE_AUDIT_FIELDS,
            change_audit,
        )
        self._refresh_manifest(run_dir)
        report = self._validate(run_dir)
        self.assertFalse(report["valid"])
        self.assertTrue(
            any("mismatch" in error for error in report["errors"]),
            report["errors"],
        )

    def test_timing_and_summary_corruption_fail_closed_after_hash_refresh(self):
        for filename, fields, field in (
            ("raw.csv", runner.RAW_FIELDS, "time_ns"),
            ("case_summary.csv", runner.CASE_SUMMARY_FIELDS, "median_time_ns"),
            ("group_summary.csv", runner.GROUP_SUMMARY_FIELDS, "median_case_time_ns"),
        ):
            with self.subTest(filename=filename):
                run_dir = self._build_evidence()

                def mutate(rows, changed_field=field):
                    rows[0][changed_field] = str(int(float(rows[0][changed_field])) + 1)

                self._rewrite_csv(run_dir, filename, fields, mutate)
                self._refresh_manifest(run_dir)
                report = self._validate(run_dir)
                self.assertFalse(report["valid"])

    def test_config_environment_manifest_and_missing_file_fail_closed(self):
        scenarios = ("config", "environment", "manifest", "missing")
        for scenario in scenarios:
            with self.subTest(scenario=scenario):
                run_dir = self._build_evidence()
                if scenario == "config":
                    path = run_dir / "config.json"
                    payload = json.loads(path.read_text(encoding="utf-8"))
                    payload["measured_runs"] = 21
                    path.write_text(json.dumps(payload), encoding="utf-8")
                    self._refresh_manifest(run_dir)
                elif scenario == "environment":
                    path = run_dir / "environment.json"
                    payload = json.loads(path.read_text(encoding="utf-8"))
                    payload["source_commit"] = "b" * 40
                    path.write_text(json.dumps(payload), encoding="utf-8")
                    self._refresh_manifest(run_dir)
                elif scenario == "manifest":
                    path = run_dir / "manifest.json"
                    payload = json.loads(path.read_text(encoding="utf-8"))
                    payload["files"]["raw"]["sha256"] = "0" * 64
                    path.write_text(json.dumps(payload), encoding="utf-8")
                else:
                    (run_dir / "case_audit.csv").unlink()
                report = self._validate(run_dir)
                self.assertFalse(report["valid"])

    def test_malformed_evidence_returns_report_instead_of_crashing(self):
        run_dir = self._build_evidence()
        (run_dir / "config.json").write_text("{broken", encoding="utf-8")
        report = self._validate(run_dir)
        self.assertFalse(report["valid"])
        self.assertTrue((run_dir / "validation_report.json").is_file())

    def test_unexpected_archive_file_and_non_utc_timestamp_are_rejected(self):
        for scenario in ("extra_file", "non_utc"):
            with self.subTest(scenario=scenario):
                run_dir = self._build_evidence()
                if scenario == "extra_file":
                    (run_dir / "notes.txt").write_text("unexpected\n", encoding="utf-8")
                else:
                    manifest_path = run_dir / "manifest.json"
                    manifest = json.loads(
                        manifest_path.read_text(encoding="utf-8")
                    )
                    manifest["experiment_started_at_utc"] = (
                        "2026-08-04T12:00:00+02:00"
                    )
                    manifest_path.write_text(
                        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8",
                    )
                report = self._validate(run_dir)
                self.assertFalse(report["valid"])

    def test_manifest_wall_clock_relationships_fail_closed(self):
        scenarios = {
            "elapsed below measured total": (
                lambda manifest: manifest.__setitem__(
                    "experiment_elapsed_ns",
                    manifest["measured_call_total_ns"] - 1,
                ),
                False,
            ),
            "elapsed inconsistent with UTC duration": (
                lambda manifest: manifest.__setitem__(
                    "experiment_elapsed_ns", 100_000_000_000
                ),
                False,
            ),
            "reversed UTC timestamps": (
                lambda manifest: manifest.__setitem__(
                    "experiment_completed_at_utc",
                    "2026-08-04T09:59:00+00:00",
                ),
                False,
            ),
            "small UTC and monotonic difference": (
                lambda manifest: manifest.__setitem__(
                    "experiment_elapsed_ns", 599_500_000_000
                ),
                True,
            ),
        }
        for label, (mutate, expected_valid) in scenarios.items():
            with self.subTest(label=label):
                run_dir = self._build_evidence()
                manifest_path = run_dir / "manifest.json"
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                mutate(manifest)
                manifest_path.write_text(
                    json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8",
                )

                report = self._validate(run_dir)

                self.assertIs(report["valid"], expected_valid, report["errors"])

    def test_external_report_must_be_outside_archive(self):
        run_dir = self._build_evidence()
        built_in = self._validate(run_dir)
        self.assertTrue(built_in["valid"], built_in["errors"])

        report = self._validate(run_dir, run_dir / "second_report.json")
        self.assertFalse(report["valid"])
        self.assertFalse((run_dir / "second_report.json").exists())


if __name__ == "__main__":
    unittest.main()
