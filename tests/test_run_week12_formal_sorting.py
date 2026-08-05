"""Week 12 formal runner contract and timing-boundary tests."""

import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock, patch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "experiments"))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import run_week12_formal_sorting as runner  # noqa: E402
from week12_experiment_gate import (  # noqa: E402
    WEEK12_EXPERIMENT_GATE,
    gate_to_dict,
)


EXECUTION_ID = "week12_formal_sorting_v1__test_run001"


class RunWeek12FormalSortingTests(unittest.TestCase):
    def _tiny_config(self, **changes):
        defaults = {
            "sizes": (8,),
            "randomized_cases": 2,
            "warmup_runs": 1,
            "measured_runs": 2,
        }
        defaults.update(changes)
        return replace(runner.build_execution_config(), **defaults)

    def _environment(self):
        return {
            "execution_id": EXECUTION_ID,
            "output_dir": f"results/runs/{EXECUTION_ID}",
            "benchmark_environment": {
                "processor_class": "Test Processor",
                "architecture": "test-arch",
                "memory_gb": 16,
                "logical_cpu_count": 8,
                "os_name": "Test OS",
                "os_version": "1.0",
                "os_build": "build-1",
                "python_implementation": "CPython",
                "python_version": "3.12.4",
            },
            "source_commit": "a" * 40,
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
            "timing_readiness": {
                "ready": True,
                "execution_stage": "formal",
                "quality": "clean",
                "warnings": [],
                "power_ready": True,
                "load_low": True,
                "load_stable": True,
                "disk_ready": True,
                "minimum_disk_bytes": 1 << 30,
                "available_disk_bytes": 2 << 30,
                "load_status": {},
            },
        }

    def test_execution_config_is_derived_from_complete_gate(self):
        config = runner.validate_execution_config(
            runner.build_execution_config(),
            require_frozen=True,
        )

        self.assertEqual(config.case_count, 60)
        self.assertEqual(config.raw_row_count, 3600)
        self.assertEqual(config.case_summary_row_count, 180)
        self.assertEqual(config.group_summary_row_count, 45)
        self.assertTrue(WEEK12_EXPERIMENT_GATE.recognition_separate)
        self.assertEqual(config.paper_execution_mode, "minimal")
        self.assertEqual(config.audit_execution_mode, "checked")

    def test_invalid_numeric_config_types_are_rejected(self):
        for field, value in (
            ("randomized_cases", True),
            ("warmup_runs", False),
            ("measured_runs", 0),
            ("seed", True),
        ):
            with self.subTest(field=field, value=value):
                with self.assertRaises(ValueError):
                    runner.validate_execution_config(
                        replace(self._tiny_config(), **{field: value})
                    )

    def test_cli_has_no_protocol_override_flags(self):
        args = runner.parse_args(
            ["--execution-id", EXECUTION_ID, "--preflight-only"]
        )
        self.assertEqual(args.execution_id, EXECUTION_ID)
        self.assertTrue(args.preflight_only)
        with redirect_stderr(Mock()), self.assertRaises(SystemExit):
            runner.parse_args(["--execution-id", EXECUTION_ID, "--sizes", "8"])

    def test_public_formal_execution_is_hard_disabled(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaisesRegex(RuntimeError, "disabled"):
                runner.execute_week12_formal(tmpdir, execution_id=EXECUTION_ID)
            self.assertFalse(
                (Path(tmpdir) / "results" / "runs" / EXECUTION_ID).exists()
            )

    def test_case_seed_contract(self):
        self.assertIsNone(runner.seed_for_case("flat_valid", 32, 1, 20261201))
        self.assertIsNone(runner.seed_for_case("nested_valid", 32, 1, 20261201))
        self.assertEqual(
            runner.seed_for_case("incremental_valid", 32, 5, 20261201),
            20293206,
        )

    def test_checked_diagnostics_are_called_without_mode_argument(self):
        original = runner.paper_jordan_diagnostics_valid
        diagnostic = Mock(side_effect=original)
        with patch.object(runner, "paper_jordan_diagnostics_valid", diagnostic):
            cases, audits = runner.build_cases_and_audits(
                self._tiny_config(warmup_runs=0, measured_runs=1),
                EXECUTION_ID,
            )

        self.assertEqual(len(cases), 4)
        self.assertEqual(len(audits), 4)
        self.assertEqual(diagnostic.call_count, 4)
        self.assertTrue(all(not call.kwargs for call in diagnostic.call_args_list))

    def test_duplicate_case_is_rejected_before_timing(self):
        with patch.object(
            runner,
            "generate_sequence",
            return_value=[1, 2, 3, 4],
        ):
            with self.assertRaisesRegex(RuntimeError, "duplicate"):
                runner.build_cases_and_audits(
                    self._tiny_config(
                        sizes=(4,),
                        warmup_runs=0,
                        measured_runs=1,
                    ),
                    EXECUTION_ID,
                )

    def test_invalid_case_is_rejected_before_diagnostics(self):
        diagnostic = Mock()
        with patch.object(
            runner,
            "generate_sequence",
            return_value=[1, 3, 2, 4],
        ), patch.object(
            runner,
            "paper_jordan_diagnostics_valid",
            diagnostic,
        ):
            with self.assertRaisesRegex(RuntimeError, "oracle-certified"):
                runner.build_cases_and_audits(
                    self._tiny_config(
                        sizes=(4,),
                        warmup_runs=0,
                        measured_runs=1,
                    ),
                    EXECUTION_ID,
                )
        diagnostic.assert_not_called()

    def test_failed_checked_diagnostic_prevents_timing(self):
        failed = {
            "invariants_valid": False,
            "output": [],
            "processed_count": 0,
            "trace": [],
            "metrics": {name: 0 for name in runner.PAPER_METRIC_NAMES},
        }
        timed = Mock()
        with patch.object(
            runner,
            "paper_jordan_diagnostics_valid",
            return_value=failed,
        ), patch.object(runner, "run_timed_algorithm", timed):
            with self.assertRaisesRegex(RuntimeError, "diagnostics failed"):
                runner.run_formal_in_memory(
                    self._tiny_config(),
                    EXECUTION_ID,
                )
        timed.assert_not_called()

    def test_all_audits_finish_before_any_warmup(self):
        events = []
        original_diagnostic = runner.paper_jordan_diagnostics_valid

        def diagnostic(sequence):
            events.append("audit")
            return original_diagnostic(sequence)

        def timed(
            algorithm_name,
            sequence,
            oracle_result,
            paper_execution_mode,
            run_index,
            algorithm_position="",
        ):
            events.append("timing")
            return {
                "run_index": run_index,
                "measured_round": run_index,
                "algorithm_position": algorithm_position,
                "time_ns": 100,
                "output_correct": True,
                "error": "",
            }

        config = self._tiny_config(warmup_runs=1, measured_runs=1)
        with patch.object(
            runner,
            "paper_jordan_diagnostics_valid",
            side_effect=diagnostic,
        ), patch.object(runner, "run_timed_algorithm", side_effect=timed):
            products = runner.run_formal_in_memory(config, EXECUTION_ID)

        self.assertEqual(len(products["case_audit_rows"]), config.case_count)
        first_timing = events.index("timing")
        self.assertEqual(events[:first_timing], ["audit"] * config.case_count)

    def test_formal_initialization_archives_full_gate_before_work(self):
        environment = self._environment()
        with tempfile.TemporaryDirectory() as tmpdir, patch.object(
            runner,
            "build_formal_environment_record",
            return_value=environment,
        ), patch.object(
            runner,
            "validate_formal_environment_record",
            return_value=environment,
        ):
            paths, stored_environment, _, _ = runner.initialize_formal_evidence(
                tmpdir,
                EXECUTION_ID,
            )
            stored_config = json.loads(
                paths.config_json.read_text(encoding="utf-8")
            )

        self.assertEqual(stored_config, gate_to_dict())
        self.assertEqual(stored_environment, environment)
        self.assertIn("source_pilot_manifest_sha256", stored_config)
        self.assertIn("scope", stored_config)

    def test_formal_elapsed_clock_starts_before_directory_reservation(self):
        environment = self._environment()
        events = []

        def reserve(paths):
            events.append("reserve")
            paths.run_dir.mkdir(parents=True)

        def start_clock():
            events.append("start_clock")
            return 100

        with tempfile.TemporaryDirectory() as tmpdir, patch.object(
            runner,
            "build_formal_environment_record",
            return_value=environment,
        ), patch.object(
            runner,
            "validate_formal_environment_record",
            return_value=environment,
        ), patch.object(
            runner,
            "reserve_formal_run_directory",
            side_effect=reserve,
        ), patch.object(
            runner.time,
            "perf_counter_ns",
            side_effect=start_clock,
        ):
            runner.initialize_formal_evidence(tmpdir, EXECUTION_ID)

        self.assertEqual(events, ["start_clock", "reserve"])

    def test_manifest_separates_pipeline_and_measured_call_time(self):
        gate = WEEK12_EXPERIMENT_GATE

        def rows(fields, count):
            return [{field: "" for field in fields} for _ in range(count)]

        products = {
            "raw_rows": rows(runner.RAW_FIELDS, gate.raw_row_count),
            "case_summary_rows": rows(
                runner.CASE_SUMMARY_FIELDS, gate.case_summary_row_count
            ),
            "group_summary_rows": rows(
                runner.GROUP_SUMMARY_FIELDS, gate.group_summary_row_count
            ),
            "case_audit_rows": rows(
                runner.CASE_AUDIT_FIELDS, gate.case_audit_row_count
            ),
        }
        for row in products["raw_rows"]:
            row["time_ns"] = 7
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = runner.build_formal_run_paths(tmpdir, EXECUTION_ID)
            paths.run_dir.mkdir(parents=True)
            runner.write_json_exclusive(paths.config_json, gate_to_dict())
            runner.write_json_exclusive(paths.environment_json, self._environment())
            with patch.object(runner.time, "perf_counter_ns", return_value=40_100):
                manifest = runner.write_formal_products(
                    paths,
                    products,
                    self._environment(),
                    started_at=datetime(2026, 8, 4, tzinfo=timezone.utc),
                    started_ns=100,
                )

        self.assertEqual(manifest["experiment_elapsed_ns"], 40_000)
        self.assertEqual(
            manifest["measured_call_total_ns"], gate.raw_row_count * 7
        )
        self.assertEqual(
            manifest["experiment_elapsed_scope"],
            runner.EXPERIMENT_ELAPSED_SCOPE,
        )

    def test_preflight_is_read_only(self):
        environment = self._environment()
        with tempfile.TemporaryDirectory() as tmpdir, patch.object(
            runner,
            "build_formal_environment_record",
            return_value=environment,
        ):
            result = runner.run_preflight(tmpdir, execution_id=EXECUTION_ID)
            run_dir = Path(result["run_dir"])
            self.assertFalse(run_dir.exists())

        self.assertEqual(result["status"], "ready_not_executed")
        self.assertIs(
            result["formal_execution_enabled"],
            runner.FORMAL_EXECUTION_ENABLED,
        )


if __name__ == "__main__":
    unittest.main()
