"""Week 11 frozen pilot runner-framework tests."""

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

    def test_day2_framework_does_not_import_or_call_sorting_code(self):
        source = Path(runner.__file__).read_text(encoding="utf-8")
        self.assertNotIn("paper_jordan_sort_valid", source)
        self.assertNotIn("generate_sequence", source)
        self.assertNotIn("time.perf_counter_ns", source)


if __name__ == "__main__":
    unittest.main()
