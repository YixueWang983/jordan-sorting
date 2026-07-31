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
from week11_experiment_gate_v1 import (  # noqa: E402
    WEEK11_MACHINE_BASELINE_PATH_V1,
    WEEK11_MACHINE_BASELINE_SHA256_V1,
)
from week11_experiment_gate_v2 import (  # noqa: E402
    WEEK11_EXPERIMENT_GATE_V2 as WEEK11_EXPERIMENT_GATE,
)


class RunWeek11PilotTests(unittest.TestCase):
    def _tiny_execution_config(self, **changes):
        defaults = {
            "run_id": "week11_day3_test",
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

    def _matching_machine_identity(self):
        return {
            "machine_name": "MacBook Air",
            "machine_model": "Mac16,13",
            "chip": "Apple M4",
            "architecture": "arm64",
            "os_name": "macOS",
            "os_version": "26.5.2",
            "os_build": "25F84",
            "python_executable": "/opt/anaconda3/bin/python",
            "python_implementation": "CPython",
            "python_version": "3.12.4",
        }

    def _minimal_environment_record(self):
        return {
            "run_id": WEEK11_EXPERIMENT_GATE.run_id,
            "gate_version": WEEK11_EXPERIMENT_GATE.gate_version,
            "machine_identity_id": WEEK11_EXPERIMENT_GATE.machine_identity_id,
            "machine_baseline_path": (
                WEEK11_EXPERIMENT_GATE.machine_baseline_path
            ),
            "machine_baseline_sha256": (
                WEEK11_EXPERIMENT_GATE.machine_baseline_sha256
            ),
            "captured_before_timing": True,
        }

    def _temporary_project(self):
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name)
        machine_doc = root / runner.MACHINE_PREFLIGHT_DOCUMENT
        machine_doc.parent.mkdir(parents=True)
        machine_doc.write_text("# fixed machine\n", encoding="utf-8")
        baseline_doc = root / runner.MACHINE_BASELINE_DOCUMENT
        baseline_doc.write_bytes(
            (PROJECT_ROOT / runner.MACHINE_BASELINE_DOCUMENT).read_bytes()
        )
        return temporary, root

    def _run_git(self, repository, *args):
        return subprocess.run(
            ["git", *args],
            cwd=repository,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

    def test_runner_imports_the_exact_frozen_gate(self):
        self.assertIs(runner.WEEK11_EXPERIMENT_GATE, WEEK11_EXPERIMENT_GATE)
        self.assertEqual(
            WEEK11_EXPERIMENT_GATE.valid_families,
            ("flat_valid", "nested_valid", "incremental_valid"),
        )

    def test_execution_config_is_derived_from_frozen_gate(self):
        config = runner.build_execution_config()

        self.assertEqual(config.run_id, WEEK11_EXPERIMENT_GATE.run_id)
        self.assertEqual(config.gate_version, "v2")
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
            WEEK11_EXPERIMENT_GATE.algorithms,
            (
                "python_sort",
                "simplified_jordan_reference",
                "simplified_jordan_paper_ordinary_list",
            ),
        )

    def test_output_contract_uses_the_frozen_run_id(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = runner.build_pilot_paths(tmpdir)

        self.assertEqual(
            paths.run_dir,
            Path(tmpdir)
            / "results/runs/week11_paper_sorting_pilot_v2_m4",
        )
        self.assertEqual(
            tuple(path.name for path in paths.evidence_paths),
            runner.EVIDENCE_FILENAMES,
        )
        self.assertTrue(
            all(path.parent == paths.run_dir for path in paths.evidence_paths)
        )

    def test_modified_gate_is_rejected(self):
        changed = replace(WEEK11_EXPERIMENT_GATE, measured_runs=11)
        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaises(ValueError):
                runner.build_pilot_paths(tmpdir, gate=changed)

    def test_existing_run_directory_is_rejected_even_when_empty(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = runner.build_pilot_paths(tmpdir)
            paths.run_dir.mkdir(parents=True)

            with self.assertRaisesRegex(RuntimeError, "already in use"):
                runner.require_unused_output(paths)

    def test_existing_evidence_file_is_rejected(self):
        for filename in runner.EVIDENCE_FILENAMES:
            with self.subTest(filename=filename):
                temporary = tempfile.TemporaryDirectory()
                self.addCleanup(temporary.cleanup)
                tmpdir = temporary.name
                paths = runner.build_pilot_paths(tmpdir)
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

    def test_cli_exposes_only_preflight_operational_option(self):
        self.assertTrue(runner.parse_args(["--preflight-only"]).preflight_only)
        self.assertFalse(runner.parse_args([]).preflight_only)

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

    def test_formal_execution_is_disabled(self):
        with patch.object(runner, "run_preflight") as preflight:
            with self.assertRaisesRegex(RuntimeError, "Day 5 gate"):
                runner.main([])
        preflight.assert_not_called()

    def test_preflight_is_read_only_and_reports_frozen_counts(self):
        temporary, root = self._temporary_project()
        self.addCleanup(temporary.cleanup)
        with patch.object(
            runner,
            "git_snapshot",
            return_value=self._clean_git_state(),
        ), patch.object(
            runner,
            "capture_machine_identity",
            return_value=self._matching_machine_identity(),
        ):
            result = runner.run_preflight(root)

        self.assertEqual(result["status"], "ready_not_executed")
        self.assertTrue(result["gate_valid"])
        self.assertTrue(result["machine_preflight_document_present"])
        self.assertTrue(result["machine_baseline_present"])
        self.assertTrue(result["machine_identity_matches_baseline"])
        self.assertEqual(result["machine_identity_mismatches"], {})
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
        self.assertFalse(result["formal_execution_enabled"])
        self.assertFalse(
            (root / WEEK11_EXPERIMENT_GATE.output_dir).exists()
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
                "capture_machine_identity",
                return_value=self._matching_machine_identity(),
            ):
                with self.assertRaises(RuntimeError):
                    runner.run_preflight(root)

    def test_preflight_requires_machine_document(self):
        with tempfile.TemporaryDirectory() as tmpdir, patch.object(
            runner,
            "git_snapshot",
            return_value=self._clean_git_state(),
        ):
            with self.assertRaisesRegex(RuntimeError, "document is missing"):
                runner.run_preflight(tmpdir)

    def test_preflight_reports_machine_identity_mismatch(self):
        temporary, root = self._temporary_project()
        self.addCleanup(temporary.cleanup)
        changed = dict(self._matching_machine_identity())
        changed["machine_model"] = "MacBookAir10,1"
        changed["chip"] = "Apple M1"
        with patch.object(
            runner,
            "git_snapshot",
            return_value=self._clean_git_state(),
        ), patch.object(
            runner,
            "capture_machine_identity",
            return_value=changed,
        ):
            result = runner.run_preflight(root)

        self.assertEqual(result["status"], "blocked_machine_mismatch")
        self.assertFalse(result["machine_identity_matches_baseline"])
        self.assertIn("machine_model", result["machine_identity_mismatches"])
        self.assertIn("chip", result["machine_identity_mismatches"])
        self.assertFalse((root / WEEK11_EXPERIMENT_GATE.output_dir).exists())

    def test_config_contract_records_modes_counts_and_paths(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = runner.build_pilot_paths(tmpdir)
            config = runner.build_config_record(paths, project_root=tmpdir)

        self.assertEqual(config["status"], "ready_not_executed")
        self.assertEqual(config["paper_execution_mode"], "minimal")
        self.assertEqual(config["audit_execution_mode"], "checked")
        self.assertEqual(config["case_count"], 35)
        self.assertEqual(config["raw_row_count"], 1050)
        self.assertEqual(config["gate_version"], "v2")
        self.assertEqual(
            config["machine_baseline_path"],
            "docs/analysis/week11_machine_baseline_v2_m4.json",
        )
        self.assertEqual(
            config["machine_baseline_sha256"],
            WEEK11_EXPERIMENT_GATE.machine_baseline_sha256,
        )
        self.assertEqual(set(config["outputs"]), set(runner.EVIDENCE_FILENAMES))

    def test_tiny_execution_builds_all_four_row_products(self):
        config = self._tiny_execution_config()
        result = runner.run_pilot_in_memory(config)

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
            result = runner.run_pilot_in_memory(config)

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
            runner.run_pilot_in_memory(config)

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
                runner.run_pilot_in_memory(config)

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
                runner.build_cases_and_audits(config)

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
                runner.run_pilot_in_memory(config)

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
        ):
            environment = runner.build_environment_record(
                git_state,
                project_root=tmpdir,
                machine_identity=self._matching_machine_identity(),
            )

        self.assertTrue(environment["captured_before_timing"])
        self.assertFalse(environment["git_dirty"])
        self.assertTrue(environment["head_matches_origin_main"])
        self.assertEqual(environment["git_commit_sha"], "a" * 40)
        self.assertEqual(environment["paper_execution_mode"], "minimal")
        self.assertEqual(environment["audit_execution_mode"], "checked")
        self.assertEqual(environment["power_snapshot"], "captured")
        self.assertEqual(environment["load_snapshot"], "captured")
        self.assertTrue(environment["power_command_success"])
        self.assertTrue(environment["load_command_success"])
        self.assertGreaterEqual(environment["available_disk_bytes"], 0)
        self.assertEqual(environment["gate_version"], "v2")
        self.assertEqual(
            environment["machine_baseline_sha256"],
            WEEK11_EXPERIMENT_GATE.machine_baseline_sha256,
        )
        self.assertEqual(environment["machine_model"], "Mac16,13")
        self.assertEqual(environment["architecture"], "arm64")

    def test_active_baseline_hash_tampering_is_rejected(self):
        temporary, root = self._temporary_project()
        self.addCleanup(temporary.cleanup)
        baseline = root / runner.MACHINE_BASELINE_DOCUMENT
        baseline.write_bytes(baseline.read_bytes() + b"\n")

        with self.assertRaisesRegex(RuntimeError, "SHA-256"):
            runner.load_machine_baseline(root)

    def test_preserved_v1_m1_baseline_rejects_current_m4_identity(self):
        baseline = runner.load_verified_machine_baseline(
            PROJECT_ROOT,
            WEEK11_MACHINE_BASELINE_PATH_V1,
            WEEK11_MACHINE_BASELINE_SHA256_V1,
        )
        mismatches = runner.machine_identity_mismatches(
            baseline,
            self._matching_machine_identity(),
        )

        self.assertIn("machine_model", mismatches)
        self.assertIn("chip", mismatches)
        self.assertIn("os_version", mismatches)

    def test_initialize_evidence_directory_writes_and_verifies_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = runner.build_pilot_paths(tmpdir)
            config = runner.build_config_record(paths, project_root=tmpdir)
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

    def test_initialize_evidence_rejects_changed_gate_binding(self):
        for record_name in ("config", "environment"):
            with self.subTest(record=record_name):
                temporary, root = self._temporary_project()
                self.addCleanup(temporary.cleanup)
                paths = runner.build_pilot_paths(root)
                config = runner.build_config_record(paths, project_root=root)
                environment = self._minimal_environment_record()
                target = config if record_name == "config" else environment
                target["machine_baseline_sha256"] = "0" * 64

                with self.assertRaisesRegex(ValueError, "does not match"):
                    runner.initialize_evidence_directory(
                        paths,
                        config,
                        environment,
                    )

                self.assertFalse(paths.run_dir.exists())

    def test_environment_write_failure_preserves_partial_evidence(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = runner.build_pilot_paths(tmpdir)
            config = runner.build_config_record(paths, project_root=tmpdir)
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
            "capture_machine_identity",
            return_value=self._matching_machine_identity(),
        ):
            runner.initialize_formal_evidence(root)
        paths = runner.build_pilot_paths(root)

        def future_sorter():
            self.assertTrue(paths.config_json.is_file())
            self.assertTrue(paths.environment_json.is_file())

        sorter = Mock(side_effect=future_sorter)
        sorter()
        sorter.assert_called_once_with()

    def test_formal_evidence_rejects_machine_mismatch_before_writing(self):
        temporary, root = self._temporary_project()
        self.addCleanup(temporary.cleanup)
        changed = dict(self._matching_machine_identity())
        changed["machine_model"] = "another-machine"

        with patch.object(
            runner,
            "git_snapshot",
            return_value=self._clean_git_state(),
        ), patch.object(
            runner,
            "capture_machine_identity",
            return_value=changed,
        ):
            with self.assertRaisesRegex(RuntimeError, "does not match"):
                runner.initialize_formal_evidence(root)

        self.assertFalse((root / WEEK11_EXPERIMENT_GATE.output_dir).exists())

    def test_preflight_main_prints_json_without_writing_outputs(self):
        result = {
            "status": "ready_not_executed",
            "formal_execution_enabled": False,
        }
        with patch.object(
            runner,
            "run_preflight",
            return_value=result,
        ), patch("builtins.print") as print_mock:
            runner.main(["--preflight-only"])

        written = json.loads(print_mock.call_args.args[0])
        self.assertEqual(written, result)

    def test_day3_timing_path_is_not_reachable_from_cli(self):
        with patch.object(runner, "run_pilot_in_memory") as pilot:
            with self.assertRaisesRegex(RuntimeError, "Day 5 gate"):
                runner.main([])
        pilot.assert_not_called()


if __name__ == "__main__":
    unittest.main()
