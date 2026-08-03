"""Week 11 frozen pilot runner and timing-control tests."""

import gc
import json
import io
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr
from dataclasses import replace
from pathlib import Path
from unittest.mock import Mock, patch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "experiments"))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import run_week11_pilot as runner  # noqa: E402
from week11_execution_context import (  # noqa: E402
    Week11ExecutionContext,
    output_dir_for_execution,
    validate_execution_context,
)
from week11_experiment_protocol import (  # noqa: E402
    WEEK11_EXPERIMENT_PROTOCOL,
    protocol_to_dict,
)


TEST_EXECUTION_ID = "week11_pilot_v1__test_run001"


class RunWeek11PilotTests(unittest.TestCase):
    def _tiny_execution_config(self, **changes):
        defaults = {
            "sizes": (8,),
            "randomized_cases": 2,
            "warmup_runs": 1,
            "measured_runs": 2,
        }
        defaults.update(changes)
        return replace(runner.build_execution_config(), **defaults)

    def _clean_git_state(self):
        return {
            "head": "a" * 40,
            "origin_main": "a" * 40,
            "origin_main_source": "git_ls_remote",
            "git_clean": True,
            "head_pushed": True,
        }

    def _benchmark_environment(self, processor_class="Apple M4"):
        return {
            "processor_class": processor_class,
            "architecture": "arm64",
            "memory_gb": 16,
            "logical_cpu_count": 10,
            "os_name": "macOS",
            "os_version": "26.5.2",
            "os_build": "25F84",
            "python_implementation": "CPython",
            "python_version": "3.12.4",
        }

    def _power_status(self):
        return {
            "source": "test_power",
            "status": "available",
            "on_ac_power": True,
            "battery_state": "charging",
            "battery_percent": 80,
            "low_power_mode": False,
        }

    def _load_status(self, loads=(0.50, 0.60, 0.70), cpu_count=10):
        with patch.object(runner.os, "getloadavg", return_value=loads):
            return runner.capture_load_status(cpu_count)

    def _minimal_environment_record(self):
        environment = {
            "execution_id": TEST_EXECUTION_ID,
            "output_dir": output_dir_for_execution(TEST_EXECUTION_ID),
            "benchmark_environment": self._benchmark_environment(),
            "source_commit": "a" * 40,
            "protocol_version": WEEK11_EXPERIMENT_PROTOCOL.protocol_version,
            "captured_before_timing": True,
            "available_disk_bytes": runner.MIN_TIMING_DISK_BYTES,
            "power_status": self._power_status(),
            "paper_execution_mode": "minimal",
            "audit_execution_mode": "checked",
        }
        environment["timing_readiness"] = (
            runner.require_timing_ready_environment(
                environment,
                self._load_status(),
                execution_stage="pilot",
            )
        )
        return environment

    def _temporary_project(self):
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name)
        return temporary, root

    def _frozen_stub_products(self):
        def rows(fieldnames, count):
            return [
                {field_name: "" for field_name in fieldnames}
                for _ in range(count)
            ]

        protocol = WEEK11_EXPERIMENT_PROTOCOL
        return {
            "raw_rows": rows(runner.RAW_FIELDS, protocol.raw_row_count),
            "case_summary_rows": rows(
                runner.CASE_SUMMARY_FIELDS,
                protocol.case_summary_row_count,
            ),
            "group_summary_rows": rows(
                runner.GROUP_SUMMARY_FIELDS,
                protocol.group_summary_row_count,
            ),
            "case_audit_rows": rows(
                runner.CASE_AUDIT_FIELDS,
                protocol.case_count,
            ),
        }

    def _run_git(self, repository, *args):
        return subprocess.run(
            ["git", *args],
            cwd=repository,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

    def test_runner_imports_the_machine_independent_protocol(self):
        self.assertIs(
            runner.WEEK11_EXPERIMENT_PROTOCOL,
            WEEK11_EXPERIMENT_PROTOCOL,
        )
        self.assertEqual(
            WEEK11_EXPERIMENT_PROTOCOL.valid_families,
            ("flat_valid", "nested_valid", "incremental_valid"),
        )
        protocol_fields = set(protocol_to_dict())
        self.assertNotIn("run_id", protocol_fields)
        self.assertNotIn("output_dir", protocol_fields)
        self.assertNotIn("processor_class", protocol_fields)
        self.assertNotIn("machine_baseline_path", protocol_fields)

    def test_execution_config_is_derived_from_frozen_protocol(self):
        config = runner.build_execution_config()

        self.assertEqual(config.protocol_version, "week11_pilot_v1")
        self.assertEqual(config.case_count, 35)
        self.assertEqual(config.raw_row_count, 1050)
        self.assertEqual(config.case_summary_row_count, 105)
        self.assertEqual(config.group_summary_row_count, 45)
        self.assertEqual(config.paper_execution_mode, "minimal")
        self.assertEqual(config.audit_execution_mode, "checked")

    def test_case_seed_rule_matches_existing_generator_contract(self):
        self.assertIsNone(
            runner.seed_for_case("flat_valid", 32, 1, 20260723)
        )
        self.assertIsNone(
            runner.seed_for_case("nested_valid", 32, 1, 20260723)
        )
        self.assertEqual(
            runner.seed_for_case(
                "incremental_valid",
                32,
                5,
                20260723,
            ),
            20292728,
        )
        self.assertEqual(
            WEEK11_EXPERIMENT_PROTOCOL.algorithms,
            (
                "python_sort",
                "simplified_jordan_reference",
                "simplified_jordan_paper_ordinary_list",
            ),
        )

    def test_output_contract_is_derived_from_execution_id(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = runner.build_pilot_paths(
                tmpdir,
                execution_id=TEST_EXECUTION_ID,
            )

        self.assertEqual(
            paths.run_dir,
            Path(tmpdir)
            / f"results/runs/{TEST_EXECUTION_ID}",
        )
        self.assertEqual(
            tuple(path.name for path in paths.evidence_paths),
            runner.EVIDENCE_FILENAMES,
        )
        self.assertTrue(
            all(path.parent == paths.run_dir for path in paths.evidence_paths)
        )

    def test_modified_protocol_is_rejected(self):
        changed = replace(WEEK11_EXPERIMENT_PROTOCOL, measured_runs=11)
        with self.assertRaises(ValueError):
            runner.build_execution_config(changed)

    def test_different_execution_ids_share_the_same_protocol(self):
        first = Week11ExecutionContext(
            execution_id="week11_pilot_v1__run001",
            output_dir="results/runs/week11_pilot_v1__run001",
            benchmark_environment=self._benchmark_environment(),
            source_commit="a" * 40,
        )
        second_environment = self._benchmark_environment("AMD Ryzen 7 5800U")
        second = Week11ExecutionContext(
            execution_id="week11_pilot_v1__run002",
            output_dir="results/runs/week11_pilot_v1__run002",
            benchmark_environment=second_environment,
            source_commit="b" * 40,
        )

        self.assertIs(validate_execution_context(first), first)
        self.assertIs(validate_execution_context(second), second)
        self.assertEqual(
            runner.build_execution_config(),
            runner.build_execution_config(),
        )

    def test_existing_run_directory_is_rejected_even_when_empty(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = runner.build_pilot_paths(
                tmpdir,
                execution_id=TEST_EXECUTION_ID,
            )
            paths.run_dir.mkdir(parents=True)

            with self.assertRaisesRegex(RuntimeError, "already in use"):
                runner.require_unused_output(paths)

    def test_existing_evidence_file_is_rejected(self):
        for filename in runner.EVIDENCE_FILENAMES:
            with self.subTest(filename=filename):
                temporary = tempfile.TemporaryDirectory()
                self.addCleanup(temporary.cleanup)
                tmpdir = temporary.name
                paths = runner.build_pilot_paths(
                    tmpdir,
                    execution_id=TEST_EXECUTION_ID,
                )
                paths.run_dir.mkdir(parents=True)
                evidence = paths.run_dir / filename
                evidence.write_text("existing\n", encoding="utf-8")

                with self.assertRaisesRegex(RuntimeError, filename):
                    runner.require_unused_output(paths)

    def test_git_snapshot_queries_remote_instead_of_stale_tracking_ref(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            remote = root / "remote.git"
            clone_a = root / "clone-a"
            clone_b = root / "clone-b"
            self._run_git(root, "init", "--bare", "--initial-branch=main", str(remote))
            self._run_git(root, "init", "--initial-branch=main", str(clone_a))
            self._run_git(clone_a, "config", "user.name", "Week 11 Test")
            self._run_git(clone_a, "config", "user.email", "week11@example.com")
            (clone_a / "baseline.txt").write_text("old\n", encoding="utf-8")
            self._run_git(clone_a, "add", "baseline.txt")
            self._run_git(clone_a, "commit", "-m", "baseline")
            self._run_git(clone_a, "remote", "add", "origin", str(remote))
            self._run_git(clone_a, "push", "-u", "origin", "main")
            old_head = self._run_git(clone_a, "rev-parse", "HEAD")

            self._run_git(root, "clone", str(remote), str(clone_b))
            self._run_git(clone_b, "config", "user.name", "Week 11 Test")
            self._run_git(clone_b, "config", "user.email", "week11@example.com")
            (clone_b / "remote-change.txt").write_text("new\n", encoding="utf-8")
            self._run_git(clone_b, "add", "remote-change.txt")
            self._run_git(clone_b, "commit", "-m", "advance remote")
            self._run_git(clone_b, "push", "origin", "main")
            new_head = self._run_git(clone_b, "rev-parse", "HEAD")

            self.assertEqual(
                self._run_git(clone_a, "rev-parse", "origin/main"),
                old_head,
            )
            snapshot = runner.git_snapshot(clone_a)

        self.assertEqual(snapshot["head"], old_head)
        self.assertEqual(snapshot["origin_main"], new_head)
        self.assertEqual(snapshot["origin_main_source"], "git_ls_remote")
        self.assertFalse(snapshot["head_pushed"])

    def test_git_snapshot_includes_untracked_files_despite_local_config(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            remote = root / "remote.git"
            clone = root / "clone"
            self._run_git(
                root,
                "init",
                "--bare",
                "--initial-branch=main",
                str(remote),
            )
            self._run_git(root, "init", "--initial-branch=main", str(clone))
            self._run_git(clone, "config", "user.name", "Week 11 Test")
            self._run_git(clone, "config", "user.email", "week11@example.com")
            (clone / "tracked.txt").write_text("tracked\n", encoding="utf-8")
            self._run_git(clone, "add", "tracked.txt")
            self._run_git(clone, "commit", "-m", "baseline")
            self._run_git(clone, "remote", "add", "origin", str(remote))
            self._run_git(clone, "push", "-u", "origin", "main")
            self._run_git(
                clone,
                "config",
                "status.showUntrackedFiles",
                "no",
            )
            (clone / "hidden-by-config.txt").write_text(
                "untracked\n",
                encoding="utf-8",
            )

            snapshot = runner.git_snapshot(clone)

        self.assertFalse(snapshot["git_clean"])
        self.assertTrue(snapshot["head_pushed"])

    def test_cli_exposes_preflight_and_run_identity_only(self):
        args = runner.parse_args(
            ["--preflight-only", "--execution-id", "week11_test_run"]
        )
        self.assertTrue(args.preflight_only)
        self.assertEqual(args.execution_id, "week11_test_run")
        with redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                runner.parse_args(["--preflight-only"])

        for forbidden in (
            "--overwrite",
            "--sizes",
            "--families",
            "--measured-runs",
            "--warmup-runs",
            "--seed",
            "--execution-mode",
            "--algorithms",
        ):
            with self.subTest(option=forbidden):
                with redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit):
                        runner.parse_args([forbidden])

    def test_cli_delegates_formal_execution_to_the_sealed_entrypoint(self):
        result = {
            "status": "validated_pilot_complete",
            "execution_id": TEST_EXECUTION_ID,
        }
        with patch.object(
            runner,
            "execute_week11_pilot",
            return_value=result,
        ) as execute, patch("builtins.print") as print_mock:
            runner.main(["--execution-id", TEST_EXECUTION_ID])

        execute.assert_called_once_with(execution_id=TEST_EXECUTION_ID)
        self.assertEqual(json.loads(print_mock.call_args.args[0]), result)

    def test_preflight_cli_requires_explicit_execution_id_on_any_machine(self):
        other_environment = self._benchmark_environment("AMD Ryzen 7 5800U")
        with patch.object(
            runner,
            "capture_benchmark_environment",
            return_value=other_environment,
        ) as capture:
            with redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit):
                    runner.main(["--preflight-only"])
        capture.assert_not_called()

    def test_preflight_is_read_only_and_reports_frozen_counts(self):
        temporary, root = self._temporary_project()
        self.addCleanup(temporary.cleanup)
        with patch.object(
            runner,
            "git_snapshot",
            return_value=self._clean_git_state(),
        ), patch.object(
            runner,
            "capture_benchmark_environment",
            return_value=self._benchmark_environment(),
        ), patch.object(
            runner,
            "capture_power_status",
            return_value=self._power_status(),
        ), patch.object(
            runner,
            "capture_load_status",
            return_value=self._load_status(),
        ):
            result = runner.run_preflight(
                root,
                execution_id=TEST_EXECUTION_ID,
            )

        self.assertEqual(result["status"], "ready_not_executed")
        self.assertTrue(result["protocol_valid"])
        self.assertEqual(result["protocol_version"], "week11_pilot_v1")
        self.assertTrue(result["execution_context_valid"])
        self.assertEqual(result["execution_id"], TEST_EXECUTION_ID)
        self.assertTrue(result["benchmark_environment_recorded"])
        self.assertTrue(result["git_clean"])
        self.assertTrue(result["head_pushed"])
        self.assertTrue(result["output_directory_unused"])
        self.assertEqual(result["case_count"], 35)
        self.assertEqual(result["expected_raw_rows"], 1050)
        self.assertEqual(result["expected_case_summary_rows"], 105)
        self.assertEqual(result["expected_group_summary_rows"], 45)
        self.assertEqual(result["paper_execution_mode"], "minimal")
        self.assertEqual(result["audit_execution_mode"], "checked")
        self.assertTrue(result["environment_contract_ready"])
        self.assertTrue(result["timing_readiness"]["ready"])
        self.assertEqual(
            result["timing_readiness"]["execution_stage"],
            "pilot",
        )
        self.assertEqual(result["timing_readiness"]["quality"], "clean")
        self.assertEqual(result["timing_readiness"]["warnings"], [])
        self.assertTrue(result["timing_readiness"]["power_ready"])
        self.assertTrue(result["timing_readiness"]["load_low"])
        self.assertTrue(result["timing_readiness"]["load_stable"])
        self.assertTrue(result["timing_readiness"]["disk_ready"])
        self.assertFalse(result["formal_execution_enabled"])
        self.assertFalse(
            (root / output_dir_for_execution(TEST_EXECUTION_ID)).exists()
        )

    def test_preflight_reports_load_warnings_without_writing_outputs(self):
        temporary, root = self._temporary_project()
        self.addCleanup(temporary.cleanup)
        elevated_load = self._load_status(
            loads=(7.0, 11.0, 6.0),
            cpu_count=10,
        )
        with patch.object(
            runner,
            "git_snapshot",
            return_value=self._clean_git_state(),
        ), patch.object(
            runner,
            "capture_benchmark_environment",
            return_value=self._benchmark_environment(),
        ), patch.object(
            runner,
            "capture_power_status",
            return_value=self._power_status(),
        ), patch.object(
            runner,
            "capture_load_status",
            return_value=elevated_load,
        ):
            result = runner.run_preflight(
                root,
                execution_id=TEST_EXECUTION_ID,
            )

        readiness = result["timing_readiness"]
        self.assertTrue(readiness["ready"])
        self.assertEqual(readiness["quality"], "warning")
        self.assertFalse(readiness["load_low"])
        self.assertFalse(readiness["load_stable"])
        self.assertEqual(
            readiness["warnings"],
            [
                "load above recommended pilot threshold",
                "recent load history is still elevated",
            ],
        )
        self.assertFalse(
            (root / output_dir_for_execution(TEST_EXECUTION_ID)).exists()
        )

    def test_preflight_rejects_dirty_or_unpushed_source(self):
        temporary, root = self._temporary_project()
        self.addCleanup(temporary.cleanup)
        for field_name in ("git_clean", "head_pushed"):
            state = self._clean_git_state()
            state[field_name] = False
            with self.subTest(field=field_name), patch.object(
                runner,
                "git_snapshot",
                return_value=state,
            ), patch.object(
                runner,
                "capture_benchmark_environment",
                return_value=self._benchmark_environment(),
            ):
                with self.assertRaises(RuntimeError):
                    runner.run_preflight(
                        root,
                        execution_id=TEST_EXECUTION_ID,
                    )

    def test_preflight_accepts_an_unseen_machine_as_a_new_execution(self):
        with tempfile.TemporaryDirectory() as tmpdir, patch.object(
            runner,
            "git_snapshot",
            return_value=self._clean_git_state(),
        ), patch.object(
            runner,
            "_capture_command",
            return_value={"success": True, "output": "captured"},
        ), patch.object(
            runner,
            "capture_benchmark_environment",
        ) as environment_mock:
            environment_mock.return_value = self._benchmark_environment(
                "AMD Ryzen 7 5800U"
            )
            with patch.object(
                runner,
                "capture_power_status",
                return_value=self._power_status(),
            ), patch.object(
                runner,
                "capture_load_status",
                return_value=self._load_status(),
            ):
                result = runner.run_preflight(
                    tmpdir,
                    execution_id="week11_pilot_v1__run002",
                )

        self.assertEqual(result["status"], "ready_not_executed")
        self.assertTrue(result["benchmark_environment_recorded"])
        self.assertEqual(
            result["execution_id"],
            "week11_pilot_v1__run002",
        )

    def test_distinct_execution_ids_use_distinct_output_directories(self):
        temporary, root = self._temporary_project()
        self.addCleanup(temporary.cleanup)
        changed = self._benchmark_environment("Apple M1")
        with patch.object(
            runner,
            "git_snapshot",
            return_value=self._clean_git_state(),
        ), patch.object(
            runner,
            "capture_benchmark_environment",
            return_value=changed,
        ), patch.object(
            runner,
            "capture_power_status",
            return_value=self._power_status(),
        ), patch.object(
            runner,
            "capture_load_status",
            return_value=self._load_status(),
        ):
            first = runner.run_preflight(
                root,
                execution_id="week11_pilot_v1__run001",
            )
            second = runner.run_preflight(
                root,
                execution_id="week11_pilot_v1__run002",
            )

        self.assertNotEqual(first["output_dir"], second["output_dir"])
        self.assertEqual(first["protocol_version"], second["protocol_version"])

    def test_config_contract_contains_only_the_frozen_protocol(self):
        config = runner.build_config_record()

        self.assertEqual(config["status"], "frozen")
        self.assertEqual(config["protocol_version"], "week11_pilot_v1")
        self.assertEqual(config["paper_execution_mode"], "minimal")
        self.assertEqual(config["audit_execution_mode"], "checked")
        self.assertEqual(config["case_count"], 35)
        self.assertEqual(config["raw_row_count"], 1050)
        self.assertNotIn("execution_id", config)
        self.assertNotIn("output_dir", config)
        self.assertNotIn("benchmark_environment", config)
        self.assertNotIn("machine_baseline_sha256", config)

    def test_tiny_execution_builds_all_four_row_products(self):
        config = self._tiny_execution_config()
        result = runner.run_pilot_in_memory(config, TEST_EXECUTION_ID)

        self.assertEqual(config.case_count, 4)
        self.assertEqual(len(result["raw_rows"]), 24)
        self.assertEqual(len(result["case_summary_rows"]), 12)
        self.assertEqual(len(result["group_summary_rows"]), 9)
        self.assertEqual(len(result["case_audit_rows"]), 4)
        self.assertTrue(
            all(set(row) == set(runner.RAW_FIELDS) for row in result["raw_rows"])
        )
        self.assertTrue(
            all(
                set(row) == set(runner.CASE_AUDIT_FIELDS)
                for row in result["case_audit_rows"]
            )
        )
        self.assertTrue(
            all(row["output_correct"] for row in result["raw_rows"])
        )
        self.assertTrue(all(not row["error"] for row in result["raw_rows"]))
        self.assertTrue(
            all(row["all_correct"] for row in result["case_summary_rows"])
        )
        self.assertTrue(
            all(
                row["all_cases_correct"]
                for row in result["group_summary_rows"]
            )
        )
        self.assertTrue(
            all(row["audit_passed"] for row in result["case_audit_rows"])
        )

    def test_frozen_execution_builds_exact_row_counts_with_stubbed_work(self):
        config = runner.build_execution_config()

        def generate(family, n, seed=None):
            del family
            values = list(range(n))
            if seed is not None:
                values[0] = seed
            return values

        def certify(sequence):
            return {
                "valid": True,
                "reason": None,
                "sorted": list(sequence),
                "distinct_values": True,
            }

        def profile(sequence, oracle_result=None):
            del sequence, oracle_result
            return {
                field: "strict_flat" if field == "category" else 0
                for field in runner.STRUCTURAL_FIELDS
            }

        def diagnose(sequence):
            return {
                "output": list(sequence),
                "processed_count": len(sequence),
                "metrics": {
                    name: 0 for name in runner.PAPER_METRIC_NAMES
                },
                "trace": [],
                "invariants_valid": True,
            }

        def time_once(algorithm_name, sequence, paper_execution_mode):
            del paper_execution_mode
            output = list(sequence)
            if algorithm_name == "simplified_jordan_reference":
                output = {"sorted": output}
            return output, 100

        with patch.object(
            runner,
            "generate_sequence",
            side_effect=generate,
        ) as generator, patch.object(
            runner,
            "oracle",
            side_effect=certify,
        ) as oracle_mock, patch.object(
            runner,
            "structure_profile",
            side_effect=profile,
        ), patch.object(
            runner,
            "paper_jordan_diagnostics_valid",
            side_effect=diagnose,
        ) as diagnostic, patch.object(
            runner,
            "_time_once_algorithm",
            side_effect=time_once,
        ):
            result = runner.run_pilot_in_memory(config, TEST_EXECUTION_ID)

        self.assertEqual(generator.call_count, 35)
        self.assertEqual(oracle_mock.call_count, 35)
        self.assertEqual(diagnostic.call_count, 35)
        self.assertEqual(len(result["raw_rows"]), 1050)
        self.assertEqual(len(result["case_summary_rows"]), 105)
        self.assertEqual(len(result["group_summary_rows"]), 45)
        self.assertEqual(len(result["case_audit_rows"]), 35)
        self.assertEqual(
            len({row["case_id"] for row in result["case_audit_rows"]}),
            35,
        )

    def test_all_cases_are_certified_and_audited_before_timing(self):
        config = self._tiny_execution_config(warmup_runs=0, measured_runs=1)
        events = []
        real_oracle = runner.oracle
        real_diagnostics = runner.paper_jordan_diagnostics_valid

        def oracle_spy(sequence):
            events.append("oracle")
            return real_oracle(sequence)

        def diagnostics_spy(sequence):
            events.append("diagnostic")
            return real_diagnostics(sequence)

        def fake_timer(algorithm_name, sequence, paper_execution_mode):
            events.append("timing")
            result = runner.ALGORITHMS[algorithm_name](
                list(sequence),
                paper_execution_mode,
            )
            return result, 100

        with patch.object(runner, "oracle", side_effect=oracle_spy), patch.object(
            runner,
            "paper_jordan_diagnostics_valid",
            side_effect=diagnostics_spy,
        ), patch.object(
            runner,
            "_time_once_algorithm",
            side_effect=fake_timer,
        ):
            runner.run_pilot_in_memory(config, TEST_EXECUTION_ID)

        first_timing = events.index("timing")
        self.assertEqual(events.count("oracle"), config.case_count)
        self.assertEqual(events.count("diagnostic"), config.case_count)
        self.assertNotIn("timing", events[: config.case_count * 2])
        self.assertTrue(
            all(
                event in {"oracle", "diagnostic"}
                for event in events[:first_timing]
            )
        )

    def test_invalid_generated_case_is_rejected_before_audit_or_timing(self):
        config = self._tiny_execution_config(
            sizes=(4,),
            valid_families=("flat_valid",),
            randomized_cases=1,
        )
        with patch.object(
            runner,
            "generate_sequence",
            return_value=[1, 3, 2, 4],
        ), patch.object(
            runner,
            "paper_jordan_diagnostics_valid",
        ) as diagnostic, patch.object(
            runner,
            "_time_once_algorithm",
        ) as timer:
            with self.assertRaisesRegex(RuntimeError, "oracle-certified"):
                runner.run_pilot_in_memory(config, TEST_EXECUTION_ID)

        diagnostic.assert_not_called()
        timer.assert_not_called()

    def test_wrong_length_generated_case_is_rejected_before_oracle(self):
        config = self._tiny_execution_config(
            sizes=(8,),
            valid_families=("flat_valid",),
            randomized_cases=1,
        )
        with patch.object(
            runner,
            "generate_sequence",
            return_value=[1, 2, 3, 4],
        ), patch.object(runner, "oracle") as oracle_mock:
            with self.assertRaisesRegex(RuntimeError, "wrong length"):
                runner.build_cases_and_audits(config, TEST_EXECUTION_ID)

        oracle_mock.assert_not_called()

    def test_duplicate_randomized_case_is_rejected_before_timing(self):
        config = self._tiny_execution_config(
            sizes=(4,),
            valid_families=("incremental_valid",),
            randomized_cases=2,
        )
        with patch.object(
            runner,
            "generate_sequence",
            return_value=[1, 2, 3, 4],
        ), patch.object(
            runner,
            "paper_jordan_diagnostics_valid",
            wraps=runner.paper_jordan_diagnostics_valid,
        ) as diagnostic, patch.object(
            runner,
            "_time_once_algorithm",
        ) as timer:
            with self.assertRaisesRegex(RuntimeError, "duplicate case"):
                runner.run_pilot_in_memory(config, TEST_EXECUTION_ID)

        diagnostic.assert_called_once()
        timer.assert_not_called()

    def test_paper_timing_passes_minimal_mode_explicitly(self):
        with patch.object(
            runner,
            "paper_jordan_sort_valid",
            return_value=[1, 2, 3, 4],
        ) as sorter:
            result, elapsed = runner._time_once_algorithm(
                runner.PAPER_ALGORITHM_NAME,
                [1, 2, 3, 4],
                "minimal",
            )

        self.assertEqual(result, [1, 2, 3, 4])
        self.assertGreaterEqual(elapsed, 0)
        sorter.assert_called_once_with(
            [1, 2, 3, 4],
            execution_mode="minimal",
        )

    def test_timed_exception_restores_original_gc_state(self):
        def fail_algorithm(values, paper_execution_mode):
            del values, paper_execution_mode
            raise RuntimeError("timed failure")

        original_state = gc.isenabled()
        try:
            for initially_enabled in (True, False):
                with self.subTest(initially_enabled=initially_enabled):
                    if initially_enabled:
                        gc.enable()
                    else:
                        gc.disable()
                    with patch.dict(
                        runner.ALGORITHMS,
                        {"python_sort": fail_algorithm},
                    ):
                        with self.assertRaisesRegex(RuntimeError, "timed failure"):
                            runner._time_once_algorithm(
                                "python_sort",
                                [2, 1],
                                "minimal",
                            )
                    self.assertEqual(gc.isenabled(), initially_enabled)
        finally:
            if original_state:
                gc.enable()
            else:
                gc.disable()

    def test_timed_call_restores_gc_after_algorithm_changes_it(self):
        def enable_gc(values, paper_execution_mode):
            del paper_execution_mode
            gc.enable()
            return sorted(values)

        original_state = gc.isenabled()
        try:
            for initially_enabled in (True, False):
                with self.subTest(initially_enabled=initially_enabled):
                    if initially_enabled:
                        gc.enable()
                    else:
                        gc.disable()
                    with patch.dict(
                        runner.ALGORITHMS,
                        {"python_sort": enable_gc},
                    ):
                        result, elapsed = runner._time_once_algorithm(
                            "python_sort",
                            [2, 1],
                            "minimal",
                        )
                    self.assertEqual(result, [1, 2])
                    self.assertGreaterEqual(elapsed, 0)
                    self.assertEqual(gc.isenabled(), initially_enabled)
        finally:
            if original_state:
                gc.enable()
            else:
                gc.disable()

    def test_case_and_algorithm_orders_are_reproducible_and_balanced(self):
        config = runner.build_execution_config()
        cases = [
            {"case_index": index, "case_id": f"case-{index}"}
            for index in range(1, 8)
        ]
        first = runner.order_cases(cases, config.case_order_seed)
        second = runner.order_cases(cases, config.case_order_seed)

        self.assertEqual(first, second)
        self.assertNotEqual(
            [case["case_id"] for case in first],
            [case["case_id"] for case in cases],
        )
        self.assertNotIn("case_execution_position", cases[0])

        positions = {name: [] for name in config.algorithms}
        for measured_round in range(1, config.measured_runs + 1):
            order = runner.algorithm_order_for_round(
                config.algorithms,
                config.algorithm_order_seed,
                case_index=1,
                measured_round=measured_round,
            )
            self.assertEqual(set(order), set(config.algorithms))
            for position, algorithm_name in enumerate(order, start=1):
                positions[algorithm_name].append(position)

        for algorithm_positions in positions.values():
            counts = [algorithm_positions.count(position) for position in (1, 2, 3)]
            self.assertLessEqual(max(counts) - min(counts), 1)

    def test_summaries_preserve_an_all_error_algorithm_group(self):
        raw_rows = [
            {
                "case_id": "flat_valid_n8_001",
                "family": "flat_valid",
                "n": 8,
                "algorithm": "python_sort",
                "time_ns": "",
                "oracle_valid": True,
                "output_correct": False,
                "audit_passed": True,
                "error": "RuntimeError: failed",
            }
            for _ in range(2)
        ]

        case_rows = runner.summarize_by_case(raw_rows)
        group_rows = runner.summarize_by_group(case_rows)

        self.assertEqual(case_rows[0]["median_time_ns"], "")
        self.assertFalse(case_rows[0]["all_correct"])
        self.assertEqual(case_rows[0]["error_count"], 2)
        self.assertEqual(group_rows[0]["median_case_time_ns"], "")
        self.assertFalse(group_rows[0]["all_cases_correct"])
        self.assertEqual(group_rows[0]["total_error_count"], 2)

    def test_environment_contract_is_captured_before_timing(self):
        git_state = self._clean_git_state()
        with tempfile.TemporaryDirectory() as tmpdir, patch.object(
            runner,
            "_capture_command",
            return_value={"success": True, "output": "captured"},
        ), patch.object(
            runner,
            "capture_power_status",
            return_value=self._power_status(),
        ):
            environment = runner.build_environment_record(
                git_state,
                execution_id=TEST_EXECUTION_ID,
                project_root=tmpdir,
                benchmark_environment=self._benchmark_environment(),
            )

        self.assertTrue(environment["captured_before_timing"])
        self.assertFalse(environment["git_dirty"])
        self.assertTrue(environment["head_matches_origin_main"])
        self.assertEqual(environment["source_commit"], "a" * 40)
        self.assertEqual(environment["execution_id"], TEST_EXECUTION_ID)
        self.assertEqual(
            environment["output_dir"],
            output_dir_for_execution(TEST_EXECUTION_ID),
        )
        self.assertEqual(environment["protocol_version"], "week11_pilot_v1")
        self.assertEqual(environment["paper_execution_mode"], "minimal")
        self.assertEqual(environment["audit_execution_mode"], "checked")
        self.assertEqual(environment["power_status"], self._power_status())
        self.assertEqual(environment["load_snapshot"], "captured")
        self.assertTrue(environment["load_command_success"])
        self.assertGreaterEqual(environment["available_disk_bytes"], 0)
        self.assertEqual(
            environment["timing_readiness"]["execution_stage"],
            "pilot",
        )
        self.assertTrue(environment["timing_readiness"]["ready"])
        self.assertNotIn("processor_class", environment)
        self.assertNotIn("architecture", environment)
        self.assertEqual(
            environment["benchmark_environment"],
            self._benchmark_environment(),
        )

    def test_initialize_evidence_directory_writes_and_verifies_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = runner.build_pilot_paths(
                tmpdir,
                execution_id=TEST_EXECUTION_ID,
            )
            config = runner.build_config_record()
            environment = self._minimal_environment_record()
            result = runner.initialize_evidence_directory(
                paths,
                config,
                environment,
            )

            self.assertEqual(
                result["status"],
                "evidence_initialized_before_timing",
            )
            self.assertEqual(
                json.loads(paths.config_json.read_text(encoding="utf-8")),
                config,
            )
            self.assertEqual(
                json.loads(paths.environment_json.read_text(encoding="utf-8")),
                environment,
            )

            with self.assertRaisesRegex(RuntimeError, "already in use"):
                runner.initialize_evidence_directory(
                    paths,
                    config,
                    environment,
                )

    def test_initialize_evidence_rejects_protocol_or_execution_drift(self):
        for record_name in ("config", "environment"):
            with self.subTest(record=record_name):
                temporary, root = self._temporary_project()
                self.addCleanup(temporary.cleanup)
                paths = runner.build_pilot_paths(
                    root,
                    execution_id=TEST_EXECUTION_ID,
                )
                config = runner.build_config_record()
                environment = self._minimal_environment_record()
                if record_name == "config":
                    config["measured_runs"] = 11
                else:
                    environment["execution_id"] = "week11_other_run"
                    environment["output_dir"] = (
                        "results/runs/week11_other_run"
                    )

                with self.assertRaisesRegex(ValueError, "does not match"):
                    runner.initialize_evidence_directory(
                        paths,
                        config,
                        environment,
                    )

                self.assertFalse(paths.run_dir.exists())

    def test_initialize_evidence_rejects_duplicate_environment_fields(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = runner.build_pilot_paths(
                tmpdir,
                execution_id=TEST_EXECUTION_ID,
            )
            environment = self._minimal_environment_record()
            environment["processor_class"] = "contradictory-processor"

            with self.assertRaisesRegex(
                ValueError,
                "only in benchmark_environment",
            ):
                runner.initialize_evidence_directory(
                    paths,
                    runner.build_config_record(),
                    environment,
                )

            self.assertFalse(paths.run_dir.exists())

    def test_initialize_evidence_rejects_execution_mode_drift(self):
        for field_name, changed_value in (
            ("paper_execution_mode", "checked"),
            ("audit_execution_mode", "minimal"),
        ):
            with self.subTest(field=field_name):
                temporary, root = self._temporary_project()
                self.addCleanup(temporary.cleanup)
                paths = runner.build_pilot_paths(
                    root,
                    execution_id=TEST_EXECUTION_ID,
                )
                environment = self._minimal_environment_record()
                environment[field_name] = changed_value

                with self.assertRaisesRegex(ValueError, "mode does not match"):
                    runner.initialize_evidence_directory(
                        paths,
                        runner.build_config_record(),
                        environment,
                    )

                self.assertFalse(paths.run_dir.exists())

    def test_initialize_evidence_rejects_timing_readiness_drift(self):
        temporary, root = self._temporary_project()
        self.addCleanup(temporary.cleanup)
        paths = runner.build_pilot_paths(
            root,
            execution_id=TEST_EXECUTION_ID,
        )
        environment = self._minimal_environment_record()
        environment["timing_readiness"]["warnings"] = ["forged warning"]

        with self.assertRaisesRegex(ValueError, "measurements"):
            runner.initialize_evidence_directory(
                paths,
                runner.build_config_record(),
                environment,
            )

        self.assertFalse(paths.run_dir.exists())

    def test_pilot_products_are_written_exclusively_with_manifest(self):
        temporary, root = self._temporary_project()
        self.addCleanup(temporary.cleanup)
        paths = runner.build_pilot_paths(
            root,
            execution_id=TEST_EXECUTION_ID,
        )
        config = runner.build_config_record()
        environment = self._minimal_environment_record()
        runner.initialize_evidence_directory(paths, config, environment)

        result = runner.write_pilot_evidence_products(
            paths,
            self._frozen_stub_products(),
            environment,
        )

        self.assertEqual(
            result["row_counts"],
            {
                "raw": 1050,
                "case_summary": 105,
                "group_summary": 45,
                "case_audit": 35,
            },
        )
        manifest = json.loads(
            paths.manifest_json.read_text(encoding="utf-8")
        )
        self.assertEqual(
            set(manifest["files"]),
            set(runner.MANIFEST_FILE_ATTRIBUTES),
        )
        for label, attribute in runner.MANIFEST_FILE_ATTRIBUTES.items():
            path = getattr(paths, attribute)
            self.assertTrue(path.is_file())
            self.assertEqual(manifest["files"][label]["path"], path.name)
            self.assertEqual(
                manifest["files"][label]["sha256"],
                runner._file_sha256(path),
            )
        with self.assertRaises(FileExistsError):
            runner.write_pilot_evidence_products(
                paths,
                self._frozen_stub_products(),
                environment,
            )

    def test_execute_pilot_rechecks_environment_before_stubbed_timing(self):
        temporary, root = self._temporary_project()
        self.addCleanup(temporary.cleanup)
        events = []
        elevated_load = self._load_status(
            loads=(7.0, 11.0, 6.0),
            cpu_count=10,
        )

        def run_in_memory(config, execution_id):
            paths = runner.build_pilot_paths(
                root,
                execution_id=execution_id,
            )
            self.assertTrue(paths.config_json.is_file())
            self.assertTrue(paths.environment_json.is_file())
            events.append("timing")
            self.assertEqual(config, runner.build_execution_config())
            return self._frozen_stub_products()

        with patch.object(
            runner,
            "git_snapshot",
            return_value=self._clean_git_state(),
        ), patch.object(
            runner,
            "capture_benchmark_environment",
            return_value=self._benchmark_environment(),
        ), patch.object(
            runner,
            "capture_power_status",
            return_value=self._power_status(),
        ), patch.object(
            runner,
            "capture_load_status",
            return_value=elevated_load,
        ), patch.object(
            runner,
            "_capture_command",
            return_value={"success": True, "output": "captured"},
        ), patch.object(
            runner,
            "run_pilot_in_memory",
            side_effect=run_in_memory,
        ) as pilot, patch.object(
            runner,
            "_validate_written_outputs",
            return_value={"valid": True, "errors": []},
        ) as validate:
            result = runner.execute_week11_pilot(
                root,
                execution_id=TEST_EXECUTION_ID,
            )

        self.assertEqual(events, ["timing"])
        pilot.assert_called_once()
        validate.assert_called_once()
        self.assertEqual(result["status"], "validated_pilot_complete")
        self.assertEqual(result["timing_readiness"]["quality"], "warning")
        self.assertFalse(result["timing_readiness"]["load_low"])

    def test_execute_pilot_rejects_source_before_evidence_or_timing(self):
        temporary, root = self._temporary_project()
        self.addCleanup(temporary.cleanup)
        dirty = self._clean_git_state()
        dirty["git_clean"] = False
        with patch.object(
            runner,
            "git_snapshot",
            return_value=dirty,
        ), patch.object(
            runner,
            "capture_benchmark_environment",
            return_value=self._benchmark_environment(),
        ), patch.object(runner, "run_pilot_in_memory") as pilot:
            with self.assertRaisesRegex(RuntimeError, "clean"):
                runner.execute_week11_pilot(
                    root,
                    execution_id=TEST_EXECUTION_ID,
                )

        pilot.assert_not_called()
        self.assertFalse(
            runner.build_pilot_paths(
                root,
                execution_id=TEST_EXECUTION_ID,
            ).run_dir.exists()
        )

    def test_execute_pilot_preserves_evidence_after_validation_failure(self):
        temporary, root = self._temporary_project()
        self.addCleanup(temporary.cleanup)
        with patch.object(
            runner,
            "git_snapshot",
            return_value=self._clean_git_state(),
        ), patch.object(
            runner,
            "capture_benchmark_environment",
            return_value=self._benchmark_environment(),
        ), patch.object(
            runner,
            "capture_power_status",
            return_value=self._power_status(),
        ), patch.object(
            runner,
            "capture_load_status",
            return_value=self._load_status(),
        ), patch.object(
            runner,
            "_capture_command",
            return_value={"success": True, "output": "captured"},
        ), patch.object(
            runner,
            "run_pilot_in_memory",
            return_value=self._frozen_stub_products(),
        ), patch.object(
            runner,
            "_validate_written_outputs",
            return_value={"valid": False, "errors": ["simulated failure"]},
        ):
            with self.assertRaisesRegex(RuntimeError, "simulated failure"):
                runner.execute_week11_pilot(
                    root,
                    execution_id=TEST_EXECUTION_ID,
                )

        paths = runner.build_pilot_paths(
            root,
            execution_id=TEST_EXECUTION_ID,
        )
        self.assertTrue(paths.run_dir.is_dir())
        self.assertTrue(paths.config_json.is_file())
        self.assertTrue(paths.environment_json.is_file())
        self.assertTrue(paths.raw_csv.is_file())
        self.assertTrue(paths.manifest_json.is_file())
        with self.assertRaisesRegex(RuntimeError, "already in use"):
            runner.require_unused_output(paths)

    def test_initialize_evidence_rejects_unavailable_power_status(self):
        temporary, root = self._temporary_project()
        self.addCleanup(temporary.cleanup)
        paths = runner.build_pilot_paths(
            root,
            execution_id=TEST_EXECUTION_ID,
        )
        environment = self._minimal_environment_record()
        environment["power_status"] = {
            "source": "unknown",
            "status": "unavailable",
            "on_ac_power": None,
            "battery_state": "unknown",
            "battery_percent": None,
            "low_power_mode": None,
        }

        with self.assertRaisesRegex(ValueError, "available"):
            runner.initialize_evidence_directory(
                paths,
                runner.build_config_record(),
                environment,
            )

        self.assertFalse(paths.run_dir.exists())

    def test_environment_write_failure_preserves_partial_evidence(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = runner.build_pilot_paths(
                tmpdir,
                execution_id=TEST_EXECUTION_ID,
            )
            config = runner.build_config_record()
            environment = self._minimal_environment_record()
            original_write = runner._write_json_exclusive

            def fail_environment(path, payload):
                if path == paths.environment_json:
                    raise OSError("simulated environment write failure")
                return original_write(path, payload)

            with patch.object(
                runner,
                "_write_json_exclusive",
                side_effect=fail_environment,
            ):
                with self.assertRaisesRegex(OSError, "simulated"):
                    runner.initialize_evidence_directory(
                        paths,
                        config,
                        environment,
                    )

            self.assertTrue(paths.run_dir.is_dir())
            self.assertTrue(paths.config_json.is_file())
            self.assertFalse(paths.environment_json.exists())
            self.assertEqual(
                json.loads(paths.config_json.read_text(encoding="utf-8")),
                config,
            )

    def test_formal_evidence_is_initialized_before_future_sorter_call(self):
        temporary, root = self._temporary_project()
        self.addCleanup(temporary.cleanup)
        with patch.object(
            runner,
            "_capture_command",
            return_value={"success": True, "output": "captured"},
        ), patch.object(
            runner,
            "git_snapshot",
            return_value=self._clean_git_state(),
        ), patch.object(
            runner,
            "capture_benchmark_environment",
            return_value=self._benchmark_environment(),
        ), patch.object(
            runner,
            "capture_power_status",
            return_value=self._power_status(),
        ):
            runner.initialize_formal_evidence(
                root,
                execution_id=TEST_EXECUTION_ID,
            )
        paths = runner.build_pilot_paths(
            root,
            execution_id=TEST_EXECUTION_ID,
        )

        def future_sorter():
            self.assertTrue(paths.config_json.is_file())
            self.assertTrue(paths.environment_json.is_file())

        sorter = Mock(side_effect=future_sorter)
        sorter()
        sorter.assert_called_once_with()

    def test_formal_evidence_accepts_a_new_machine_with_a_new_execution_id(self):
        temporary, root = self._temporary_project()
        self.addCleanup(temporary.cleanup)
        changed = self._benchmark_environment("AMD Ryzen 7 5800U")

        with patch.object(
            runner,
            "git_snapshot",
            return_value=self._clean_git_state(),
        ), patch.object(
            runner,
            "capture_benchmark_environment",
            return_value=changed,
        ), patch.object(
            runner,
            "capture_power_status",
            return_value=self._power_status(),
        ):
            result = runner.initialize_formal_evidence(
                root,
                execution_id="week11_pilot_v1__run002",
            )

        self.assertEqual(result["status"], "evidence_initialized_before_timing")
        paths = runner.build_pilot_paths(
            root,
            execution_id="week11_pilot_v1__run002",
        )
        config = json.loads(paths.config_json.read_text(encoding="utf-8"))
        environment = json.loads(
            paths.environment_json.read_text(encoding="utf-8")
        )
        self.assertEqual(config, protocol_to_dict())
        self.assertEqual(
            environment["benchmark_environment"]["processor_class"],
            "AMD Ryzen 7 5800U",
        )
        self.assertEqual(
            environment["execution_id"],
            "week11_pilot_v1__run002",
        )

    def test_linux_processor_class_prefers_anonymous_cpu_model(self):
        cpuinfo = (
            "processor : 0\n"
            "model name : AMD Ryzen 7 5800U with Radeon Graphics\n"
        )
        with patch.object(runner.platform, "system", return_value="Linux"), patch(
            "run_week11_pilot.Path.read_text",
            return_value=cpuinfo,
        ):
            result = runner._processor_class()

        self.assertEqual(
            result,
            "AMD Ryzen 7 5800U with Radeon Graphics",
        )

    def test_linux_desktop_power_status_is_not_applicable(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = runner._linux_power_status(Path(tmpdir))

        self.assertEqual(
            result,
            {
                "source": "linux_sysfs",
                "status": "not_applicable",
                "on_ac_power": None,
                "battery_state": "not_applicable",
                "battery_percent": None,
                "low_power_mode": None,
            },
        )
        self.assertIs(runner.validate_power_status(result), result)

    def test_linux_power_status_is_unavailable_when_sysfs_scan_fails(self):
        with tempfile.TemporaryDirectory() as tmpdir, patch.object(
            Path,
            "iterdir",
            side_effect=PermissionError("sysfs denied"),
        ):
            result = runner._linux_power_status(Path(tmpdir))

        self.assertEqual(
            result,
            {
                "source": "linux_sysfs",
                "status": "unavailable",
                "on_ac_power": None,
                "battery_state": "unknown",
                "battery_percent": None,
                "low_power_mode": None,
            },
        )

    def test_linux_power_status_is_unavailable_when_type_read_fails(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            unreadable_supply = Path(tmpdir) / "BAT0"
            unreadable_supply.mkdir()

            result = runner._linux_power_status(Path(tmpdir))

        self.assertEqual(
            result,
            {
                "source": "linux_sysfs",
                "status": "unavailable",
                "on_ac_power": None,
                "battery_state": "unknown",
                "battery_percent": None,
                "low_power_mode": None,
            },
        )

    def test_power_status_rejects_inconsistent_available_state(self):
        with self.assertRaisesRegex(ValueError, "available.*inconsistent"):
            runner.validate_power_status(
                {
                    "source": "linux_sysfs",
                    "status": "available",
                    "on_ac_power": True,
                    "battery_state": "not_applicable",
                    "battery_percent": 80,
                    "low_power_mode": False,
                }
            )

    def test_power_status_rejects_inconsistent_unavailable_state(self):
        with self.assertRaisesRegex(ValueError, "unavailable.*inconsistent"):
            runner.validate_power_status(
                {
                    "source": "linux_sysfs",
                    "status": "unavailable",
                    "on_ac_power": True,
                    "battery_state": "full",
                    "battery_percent": None,
                    "low_power_mode": None,
                }
            )

    def test_load_status_normalizes_by_logical_cpu_count(self):
        result = self._load_status(loads=(1.0, 1.5, 2.0), cpu_count=10)

        self.assertEqual(result["one_minute_load_per_cpu"], 0.1)
        self.assertEqual(result["five_minute_load_per_cpu"], 0.15)
        self.assertEqual(result["one_five_delta_per_cpu"], 0.05)
        self.assertTrue(result["low"])
        self.assertTrue(result["stable"])
        self.assertIs(runner.validate_load_status(result), result)

    def test_timing_readiness_rejects_discharging_power(self):
        environment = self._minimal_environment_record()
        environment["available_disk_bytes"] = runner.MIN_TIMING_DISK_BYTES
        environment["power_status"] = {
            "source": "test_power",
            "status": "available",
            "on_ac_power": False,
            "battery_state": "discharging",
            "battery_percent": 80,
            "low_power_mode": False,
        }

        with self.assertRaisesRegex(RuntimeError, "power must"):
            runner.require_timing_ready_environment(
                environment,
                self._load_status(),
            )

    def test_timing_readiness_accepts_high_charge_discharging_on_ac(self):
        environment = self._minimal_environment_record()
        environment["available_disk_bytes"] = runner.MIN_TIMING_DISK_BYTES
        environment["power_status"] = {
            "source": "pmset",
            "status": "available",
            "on_ac_power": True,
            "battery_state": "discharging",
            "battery_percent": 91,
            "low_power_mode": False,
        }

        result = runner.require_timing_ready_environment(
            environment,
            self._load_status(),
        )

        self.assertTrue(result["ready"])
        self.assertTrue(result["power_ready"])
        self.assertEqual(result["quality"], "warning")
        self.assertIn("battery is discharging", result["warnings"][0])

    def test_timing_readiness_rejects_low_power_mode_while_charging(self):
        environment = self._minimal_environment_record()
        environment["available_disk_bytes"] = runner.MIN_TIMING_DISK_BYTES
        environment["power_status"] = {
            "source": "pmset",
            "status": "available",
            "on_ac_power": True,
            "battery_state": "charging",
            "battery_percent": 80,
            "low_power_mode": True,
        }

        with self.assertRaisesRegex(RuntimeError, "low-power mode disabled"):
            runner.require_timing_ready_environment(
                environment,
                self._load_status(),
            )

    def test_timing_readiness_rejects_low_charge_discharging(self):
        environment = self._minimal_environment_record()
        environment["available_disk_bytes"] = runner.MIN_TIMING_DISK_BYTES
        environment["power_status"] = {
            "source": "pmset",
            "status": "available",
            "on_ac_power": True,
            "battery_state": "discharging",
            "battery_percent": 49,
            "low_power_mode": False,
        }

        with self.assertRaisesRegex(RuntimeError, "power must"):
            runner.require_timing_ready_environment(
                environment,
                self._load_status(),
            )

    def test_timing_readiness_rejects_discharging_in_low_power_mode(self):
        environment = self._minimal_environment_record()
        environment["available_disk_bytes"] = runner.MIN_TIMING_DISK_BYTES
        environment["power_status"] = {
            "source": "pmset",
            "status": "available",
            "on_ac_power": True,
            "battery_state": "discharging",
            "battery_percent": 91,
            "low_power_mode": True,
        }

        with self.assertRaisesRegex(RuntimeError, "power must"):
            runner.require_timing_ready_environment(
                environment,
                self._load_status(),
            )

    def test_timing_readiness_accepts_battery_free_environment(self):
        environment = self._minimal_environment_record()
        environment["available_disk_bytes"] = runner.MIN_TIMING_DISK_BYTES
        environment["power_status"] = {
            "source": "linux_sysfs",
            "status": "not_applicable",
            "on_ac_power": None,
            "battery_state": "not_applicable",
            "battery_percent": None,
            "low_power_mode": None,
        }

        result = runner.require_timing_ready_environment(
            environment,
            self._load_status(),
        )

        self.assertTrue(result["ready"])
        self.assertTrue(result["power_ready"])

    def test_pilot_timing_readiness_warns_on_high_or_unstable_load(self):
        environment = self._minimal_environment_record()
        environment["available_disk_bytes"] = runner.MIN_TIMING_DISK_BYTES
        cases = {
            "high": self._load_status(loads=(3.0, 3.0, 3.0), cpu_count=10),
            "unstable": self._load_status(
                loads=(2.4, 0.5, 0.5),
                cpu_count=10,
            ),
        }

        for label, load_status in cases.items():
            with self.subTest(label=label):
                result = runner.require_timing_ready_environment(
                    environment,
                    load_status,
                    execution_stage="pilot",
                )

            self.assertTrue(result["ready"])
            self.assertEqual(result["quality"], "warning")
            self.assertTrue(result["warnings"])

    def test_formal_timing_readiness_rejects_high_or_unstable_load(self):
        environment = self._minimal_environment_record()
        environment["available_disk_bytes"] = runner.MIN_TIMING_DISK_BYTES
        cases = {
            "high": self._load_status(loads=(3.0, 3.0, 3.0), cpu_count=10),
            "unstable": self._load_status(
                loads=(2.4, 0.5, 0.5),
                cpu_count=10,
            ),
        }

        for label, load_status in cases.items():
            with self.subTest(label=label), self.assertRaisesRegex(
                RuntimeError,
                "load",
            ):
                runner.require_timing_ready_environment(
                    environment,
                    load_status,
                    execution_stage="formal",
                )

    def test_timing_readiness_rejects_invalid_execution_stage(self):
        environment = self._minimal_environment_record()
        with self.assertRaises(TypeError):
            runner.require_timing_ready_environment(
                environment,
                self._load_status(),
                execution_stage=None,
            )
        with self.assertRaises(ValueError):
            runner.require_timing_ready_environment(
                environment,
                self._load_status(),
                execution_stage="smoke",
            )

    def test_timing_readiness_rejects_insufficient_disk(self):
        environment = self._minimal_environment_record()
        environment["available_disk_bytes"] = (
            runner.MIN_TIMING_DISK_BYTES - 1
        )

        with self.assertRaisesRegex(RuntimeError, "1 GiB"):
            runner.require_timing_ready_environment(
                environment,
                self._load_status(),
            )

    def test_linux_laptop_power_status_reads_battery_and_ac(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            battery = root / "BAT0"
            mains = root / "AC0"
            battery.mkdir()
            mains.mkdir()
            (battery / "type").write_text("Battery\n", encoding="utf-8")
            (battery / "status").write_text(
                "Discharging\n",
                encoding="utf-8",
            )
            (battery / "capacity").write_text("80\n", encoding="utf-8")
            (mains / "type").write_text("Mains\n", encoding="utf-8")
            (mains / "online").write_text("0\n", encoding="utf-8")

            result = runner._linux_power_status(root)

        self.assertEqual(result["status"], "available")
        self.assertFalse(result["on_ac_power"])
        self.assertEqual(result["battery_state"], "discharging")
        self.assertEqual(result["battery_percent"], 80)
        self.assertIsNone(result["low_power_mode"])

    def test_macos_power_status_uses_pmset(self):
        snapshot = (
            "Now drawing from 'AC Power'\n"
            " -InternalBattery-0\t80%; charging; 1:20 remaining"
        )
        settings = "AC Power:\n lowpowermode 0\n"

        def capture(command):
            if command[-1] == "batt":
                return {"success": True, "output": snapshot}
            return {"success": True, "output": settings}

        with patch.object(
            runner.platform,
            "system",
            return_value="Darwin",
        ), patch.object(
            runner,
            "_capture_command",
            side_effect=capture,
        ):
            result = runner.capture_power_status()

        self.assertEqual(result["source"], "pmset")
        self.assertEqual(result["status"], "available")
        self.assertTrue(result["on_ac_power"])
        self.assertEqual(result["battery_state"], "charging")
        self.assertEqual(result["battery_percent"], 80)
        self.assertFalse(result["low_power_mode"])

    def test_macos_power_status_uses_only_active_profile_settings(self):
        snapshot = (
            "Now drawing from 'AC Power'\n"
            " -InternalBattery-0\t80%; discharging; 2:00 remaining"
        )
        cases = [
            (
                "Battery Power:\n lowpowermode 0\n"
                "AC Power:\n lowpowermode 1\n",
                True,
            ),
            (
                "Battery Power:\n lowpowermode 1\n"
                "AC Power:\n lowpowermode 0\n",
                False,
            ),
        ]

        for settings, expected in cases:
            with self.subTest(expected=expected):
                def capture(command):
                    if command[-1] == "batt":
                        return {"success": True, "output": snapshot}
                    return {"success": True, "output": settings}

                with patch.object(
                    runner.platform,
                    "system",
                    return_value="Darwin",
                ), patch.object(
                    runner,
                    "_capture_command",
                    side_effect=capture,
                ):
                    result = runner.capture_power_status()

                self.assertIs(result["low_power_mode"], expected)

    def test_macos_power_status_supports_powermode(self):
        snapshot = (
            "Now drawing from 'AC Power'\n"
            " -InternalBattery-0\t80%; discharging; 2:00 remaining"
        )
        for value, expected in ((0, False), (1, True), (2, False)):
            with self.subTest(value=value):
                settings = f"AC Power:\n powermode {value}\n"

                def capture(command):
                    if command[-1] == "batt":
                        return {"success": True, "output": snapshot}
                    return {"success": True, "output": settings}

                with patch.object(
                    runner.platform,
                    "system",
                    return_value="Darwin",
                ), patch.object(
                    runner,
                    "_capture_command",
                    side_effect=capture,
                ):
                    result = runner.capture_power_status()

                self.assertIs(result["low_power_mode"], expected)

    def test_macos_not_charging_state_is_unknown(self):
        snapshot = (
            "Now drawing from 'AC Power'\n"
            " -InternalBattery-0\t80%; not charging; 0:00 remaining"
        )

        def capture(command):
            if command[-1] == "batt":
                return {"success": True, "output": snapshot}
            return {
                "success": True,
                "output": "AC Power:\n lowpowermode 0\n",
            }

        with patch.object(
            runner.platform,
            "system",
            return_value="Darwin",
        ), patch.object(
            runner,
            "_capture_command",
            side_effect=capture,
        ):
            result = runner.capture_power_status()

        self.assertEqual(result["battery_state"], "unknown")

    def test_preflight_main_prints_json_without_writing_outputs(self):
        result = {
            "status": "ready_not_executed",
            "formal_execution_enabled": False,
        }
        with patch.object(
            runner,
            "run_preflight",
            return_value=result,
        ) as preflight, patch("builtins.print") as print_mock:
            runner.main(
                ["--preflight-only", "--execution-id", TEST_EXECUTION_ID]
            )

        written = json.loads(print_mock.call_args.args[0])
        self.assertEqual(written, result)
        preflight.assert_called_once_with(execution_id=TEST_EXECUTION_ID)

if __name__ == "__main__":
    unittest.main()
