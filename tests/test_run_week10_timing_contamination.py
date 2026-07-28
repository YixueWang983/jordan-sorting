"""Week 10 timing-contamination runner tests."""

import tempfile
import sys
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "experiments"))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import run_week10_timing_contamination as runner  # noqa: E402
from paper_execution_policy import PAPER_EXECUTION_POLICIES  # noqa: E402
from validate_week10_timing_outputs import validate_outputs  # noqa: E402


class RunWeek10TimingContaminationTests(unittest.TestCase):
    def _tiny_config(self, root, measured_runs=2):
        return replace(
            runner.build_week10_config(
                "test_week10",
                root,
                smoke=True,
            ),
            sizes=[8],
            randomized_cases=1,
            warmup_runs=0,
            measured_runs=measured_runs,
        )

    def test_frozen_full_and_smoke_row_counts(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            full = runner.build_week10_config(
                "full",
                Path(tmpdir) / "full",
                smoke=False,
            )
            smoke = runner.build_week10_config(
                "smoke",
                Path(tmpdir) / "smoke",
                smoke=True,
            )

        self.assertEqual(runner.expected_case_count(full), 20)
        self.assertEqual(
            runner.expected_case_count(full)
            * len(full.execution_modes)
            * full.measured_runs,
            1500,
        )
        self.assertEqual(
            runner.expected_case_count(full) * len(full.execution_modes),
            100,
        )
        self.assertEqual(
            len(full.families) * len(full.sizes) * len(full.execution_modes),
            60,
        )
        self.assertEqual(runner.expected_case_count(smoke), 9)

    def test_case_certification_and_diagnostics_run_once_before_timing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config = self._tiny_config(tmpdir)
            real_oracle = runner.oracle
            real_diagnostics = runner.paper_jordan_diagnostics_valid

            with patch.object(
                runner,
                "oracle",
                wraps=real_oracle,
            ) as oracle_mock, patch.object(
                runner,
                "paper_jordan_diagnostics_valid",
                wraps=real_diagnostics,
            ) as diagnostics_mock:
                cases = runner.build_cases(config)

        self.assertEqual(len(cases), 3)
        self.assertEqual(oracle_mock.call_count, len(cases))
        self.assertEqual(diagnostics_mock.call_count, len(cases))
        self.assertTrue(all(case["audit_passed"] for case in cases))

    def test_invalid_generated_case_is_rejected_before_diagnostics(self):
        invalid = [2, 7, 3, 4, 5, 6, 1, 8]
        with tempfile.TemporaryDirectory() as tmpdir:
            config = self._tiny_config(tmpdir)
            with patch.object(
                runner,
                "generate_sequence",
                return_value=invalid,
            ), patch.object(
                runner,
                "paper_jordan_diagnostics_valid",
            ) as diagnostics_mock:
                with self.assertRaisesRegex(
                    RuntimeError,
                    "oracle-certified valid input",
                ):
                    runner.build_cases(config)

        diagnostics_mock.assert_not_called()

    def test_timed_mode_does_not_call_oracle_or_diagnostics(self):
        sequence = [2, 3, 1, 4]
        oracle_result = runner.oracle(sequence)

        with patch.object(
            runner,
            "oracle",
            side_effect=AssertionError("oracle entered timed call"),
        ), patch.object(
            runner,
            "paper_jordan_diagnostics_valid",
            side_effect=AssertionError("diagnostics entered timed call"),
        ):
            result = runner.run_timed_mode(
                "minimal",
                sequence,
                oracle_result,
                run_index=1,
                mode_position=1,
            )

        self.assertEqual(result["error"], "")
        self.assertTrue(result["output_correct"])
        self.assertGreaterEqual(result["time_ns"], 0)

    def test_mode_order_is_cyclically_balanced(self):
        modes = list(PAPER_EXECUTION_POLICIES)
        positions = {mode: [] for mode in modes}
        for measured_round in range(1, len(modes) + 1):
            order = runner.mode_order_for_round(
                modes,
                seed=17,
                case_index=3,
                measured_round=measured_round,
            )
            for position, mode in enumerate(order, start=1):
                positions[mode].append(position)

        expected = list(range(1, len(modes) + 1))
        self.assertTrue(
            all(sorted(observed) == expected for observed in positions.values())
        )

    def test_tiny_run_writes_outputs_that_pass_specialized_validator(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config = self._tiny_config(tmpdir)
            raw_rows, case_rows, group_rows = (
                runner.run_contamination_experiment(config)
            )
            report = validate_outputs(config.run_dir)

            self.assertEqual(len(raw_rows), 30)
            self.assertEqual(len(case_rows), 15)
            self.assertEqual(len(group_rows), 15)
            self.assertTrue(report["valid"], report["errors"])
            self.assertTrue(
                all(row["oracle_valid"] for row in raw_rows)
            )
            self.assertTrue(
                all(row["audit_passed"] for row in raw_rows)
            )
            self.assertTrue(
                all(row["output_correct"] for row in raw_rows)
            )

            with self.assertRaisesRegex(ValueError, "already exist"):
                runner.run_contamination_experiment(config)


if __name__ == "__main__":
    unittest.main()
