"""Week 11 machine-independent protocol and execution-context tests."""

import json
import subprocess
import sys
import unittest
from dataclasses import FrozenInstanceError, replace
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "experiments"))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from week11_execution_context import (  # noqa: E402
    Week11ExecutionContext,
    execution_context_to_dict,
    output_dir_for_execution,
    validate_execution_context,
    validate_execution_id,
)
from week11_experiment_gate import WEEK11_EXPERIMENT_GATE as HISTORICAL_V1  # noqa: E402
from week11_experiment_gate_v2 import WEEK11_EXPERIMENT_GATE_V2 as HISTORICAL_V2  # noqa: E402
from week11_experiment_protocol import (  # noqa: E402
    WEEK11_EXPERIMENT_PROTOCOL,
    protocol_to_dict,
    validate_week11_experiment_protocol,
)


class Week11ExperimentProtocolTests(unittest.TestCase):
    def _identity(self, model="Mac16,13"):
        return {
            "machine_model": model,
            "architecture": "arm64",
        }

    def test_protocol_contains_only_machine_independent_choices(self):
        record = protocol_to_dict()

        self.assertEqual(record["protocol_version"], "week11_pilot_v1")
        self.assertEqual(record["case_count"], 35)
        self.assertEqual(record["raw_row_count"], 1050)
        self.assertEqual(record["case_summary_row_count"], 105)
        self.assertEqual(record["group_summary_row_count"], 45)
        for forbidden in (
            "run_id",
            "execution_id",
            "output_dir",
            "machine_identity",
            "machine_baseline_path",
            "machine_baseline_sha256",
            "source_commit",
        ):
            self.assertNotIn(forbidden, record)

    def test_historical_gate_parameters_match_the_active_protocol(self):
        for historical in (HISTORICAL_V1, HISTORICAL_V2):
            with self.subTest(gate=historical.run_id):
                for field_name in (
                    "sizes",
                    "valid_families",
                    "randomized_cases",
                    "warmup_runs",
                    "measured_runs",
                    "algorithms",
                    "paper_execution_mode",
                    "audit_execution_mode",
                    "seed",
                    "algorithm_order_seed",
                    "case_order_seed",
                ):
                    self.assertEqual(
                        getattr(historical, field_name),
                        getattr(WEEK11_EXPERIMENT_PROTOCOL, field_name),
                    )

    def test_protocol_is_immutable_and_rejects_drift(self):
        with self.assertRaises(FrozenInstanceError):
            WEEK11_EXPERIMENT_PROTOCOL.measured_runs = 20
        with self.assertRaises(ValueError):
            validate_week11_experiment_protocol(
                replace(WEEK11_EXPERIMENT_PROTOCOL, measured_runs=20)
            )

    def test_protocol_cli_prints_the_frozen_record(self):
        completed = subprocess.run(
            [sys.executable, "experiments/week11_experiment_protocol.py"],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertEqual(json.loads(completed.stdout), protocol_to_dict())

    def test_execution_id_determines_only_the_run_directory(self):
        first = "week11_pilot_v1__m4__run1"
        second = "week11_pilot_v1__linux__run1"

        self.assertEqual(
            output_dir_for_execution(first),
            f"results/runs/{first}",
        )
        self.assertEqual(
            output_dir_for_execution(second),
            f"results/runs/{second}",
        )
        self.assertNotEqual(
            output_dir_for_execution(first),
            output_dir_for_execution(second),
        )

    def test_execution_id_rejects_path_traversal_and_empty_values(self):
        for value in ("", "../run", "run/name", "run name", True, None):
            with self.subTest(value=value):
                with self.assertRaises((TypeError, ValueError)):
                    validate_execution_id(value)

    def test_execution_context_accepts_different_machines(self):
        for execution_id, identity in (
            ("week11_pilot_v1__m4__run1", self._identity()),
            (
                "week11_pilot_v1__linux__run1",
                self._identity("Linux-5800U"),
            ),
        ):
            with self.subTest(execution_id=execution_id):
                context = Week11ExecutionContext(
                    execution_id=execution_id,
                    output_dir=output_dir_for_execution(execution_id),
                    machine_identity=identity,
                    source_commit="a" * 40,
                )
                self.assertIs(validate_execution_context(context), context)

    def test_execution_context_copies_machine_identity(self):
        identity = self._identity()
        context = Week11ExecutionContext(
            execution_id="week11_pilot_v1__m4__run1",
            output_dir="results/runs/week11_pilot_v1__m4__run1",
            machine_identity=identity,
            source_commit="a" * 40,
        )
        identity["machine_model"] = "changed"

        self.assertEqual(context.machine_identity["machine_model"], "Mac16,13")
        with self.assertRaises(TypeError):
            context.machine_identity["machine_model"] = "changed"

    def test_execution_context_rejects_wrong_output_or_source(self):
        wrong_output = Week11ExecutionContext(
            execution_id="week11_pilot_v1__m4__run1",
            output_dir="results/runs/another_run",
            machine_identity=self._identity(),
            source_commit="a" * 40,
        )
        wrong_source = Week11ExecutionContext(
            execution_id="week11_pilot_v1__m4__run1",
            output_dir="results/runs/week11_pilot_v1__m4__run1",
            machine_identity=self._identity(),
            source_commit="not-a-sha",
        )

        with self.assertRaises(ValueError):
            validate_execution_context(wrong_output)
        with self.assertRaises(ValueError):
            validate_execution_context(wrong_source)

    def test_execution_context_serialization_keeps_run_level_fields(self):
        context = Week11ExecutionContext(
            execution_id="week11_pilot_v1__m4__run1",
            output_dir="results/runs/week11_pilot_v1__m4__run1",
            machine_identity=self._identity(),
            source_commit="a" * 40,
        )

        self.assertEqual(
            execution_context_to_dict(context),
            {
                "execution_id": "week11_pilot_v1__m4__run1",
                "output_dir": "results/runs/week11_pilot_v1__m4__run1",
                "machine_identity": self._identity(),
                "source_commit": "a" * 40,
            },
        )


if __name__ == "__main__":
    unittest.main()
