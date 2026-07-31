"""Week 11 frozen pilot runner-framework tests."""

import json
import io
import sys
import tempfile
import unittest
from contextlib import redirect_stderr
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "experiments"))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import run_week11_pilot as runner  # noqa: E402
from week11_experiment_gate import (  # noqa: E402
    WEEK11_EXPERIMENT_GATE,
)


class RunWeek11PilotTests(unittest.TestCase):
    def _clean_git_state(self):
        return {
            "head": "a" * 40,
            "origin_main": "a" * 40,
            "git_clean": True,
            "head_pushed": True,
        }

    def _temporary_project(self):
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name)
        machine_doc = root / runner.MACHINE_PREFLIGHT_DOCUMENT
        machine_doc.parent.mkdir(parents=True)
        machine_doc.write_text("# fixed machine\n", encoding="utf-8")
        return temporary, root

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
            / "results/runs/week11_paper_sorting_pilot_v1",
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
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = runner.build_pilot_paths(tmpdir)
            paths.run_dir.mkdir(parents=True)
            paths.raw_csv.write_text("existing\n", encoding="utf-8")

            with self.assertRaisesRegex(RuntimeError, "raw.csv"):
                runner.require_unused_output(paths)

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
        ):
            result = runner.run_preflight(root)

        self.assertEqual(result["status"], "ready_not_executed")
        self.assertTrue(result["gate_valid"])
        self.assertTrue(result["machine_fixed"])
        self.assertTrue(result["git_clean"])
        self.assertTrue(result["head_pushed"])
        self.assertTrue(result["output_directory_unused"])
        self.assertEqual(result["case_count"], 35)
        self.assertEqual(result["expected_raw_rows"], 1050)
        self.assertEqual(result["expected_case_summary_rows"], 105)
        self.assertEqual(result["expected_group_summary_rows"], 45)
        self.assertEqual(result["paper_execution_mode"], "minimal")
        self.assertEqual(result["audit_execution_mode"], "checked")
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

    def test_config_contract_records_modes_counts_and_paths(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = runner.build_pilot_paths(tmpdir)
            config = runner.build_config_record(paths)

        self.assertEqual(config["status"], "ready_not_executed")
        self.assertEqual(config["paper_execution_mode"], "minimal")
        self.assertEqual(config["audit_execution_mode"], "checked")
        self.assertEqual(config["case_count"], 35)
        self.assertEqual(config["raw_row_count"], 1050)
        self.assertEqual(set(config["outputs"]), set(runner.EVIDENCE_FILENAMES))

    def test_environment_contract_is_captured_before_timing(self):
        git_state = self._clean_git_state()
        with patch.object(
            runner,
            "_safe_command_output",
            return_value="captured",
        ):
            environment = runner.build_environment_record(git_state)

        self.assertTrue(environment["captured_before_timing"])
        self.assertFalse(environment["git_dirty"])
        self.assertTrue(environment["head_matches_origin_main"])
        self.assertEqual(environment["git_commit_sha"], "a" * 40)
        self.assertEqual(environment["paper_execution_mode"], "minimal")
        self.assertEqual(environment["audit_execution_mode"], "checked")
        self.assertEqual(environment["power_snapshot"], "captured")
        self.assertEqual(environment["load_snapshot"], "captured")

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
