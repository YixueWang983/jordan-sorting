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
    def _environment(self, processor="Apple M4"):
        return {
            "processor_class": processor,
            "architecture": "arm64",
            "memory_gb": 16,
            "logical_cpu_count": 10,
            "os_name": "macOS",
            "os_version": "26.5.2",
            "os_build": "25F84",
            "python_implementation": "CPython",
            "python_version": "3.12.4",
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
            "benchmark_environment",
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
        first = "week11_pilot_v1__run001"
        second = "week11_pilot_v1__run002"

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
        for execution_id, environment in (
            ("week11_pilot_v1__run001", self._environment()),
            (
                "week11_pilot_v1__run002",
                self._environment("AMD Ryzen 7 5800U"),
            ),
        ):
            with self.subTest(execution_id=execution_id):
                context = Week11ExecutionContext(
                    execution_id=execution_id,
                    output_dir=output_dir_for_execution(execution_id),
                    benchmark_environment=environment,
                    source_commit="a" * 40,
                )
                self.assertIs(validate_execution_context(context), context)

    def test_execution_context_copies_benchmark_environment(self):
        environment = self._environment()
        context = Week11ExecutionContext(
            execution_id="week11_pilot_v1__run001",
            output_dir="results/runs/week11_pilot_v1__run001",
            benchmark_environment=environment,
            source_commit="a" * 40,
        )
        environment["processor_class"] = "changed"

        self.assertEqual(
            context.benchmark_environment["processor_class"],
            "Apple M4",
        )
        with self.assertRaises(TypeError):
            context.benchmark_environment["processor_class"] = "changed"

    def test_execution_context_rejects_wrong_output_or_source(self):
        wrong_output = Week11ExecutionContext(
            execution_id="week11_pilot_v1__run001",
            output_dir="results/runs/another_run",
            benchmark_environment=self._environment(),
            source_commit="a" * 40,
        )
        wrong_source = Week11ExecutionContext(
            execution_id="week11_pilot_v1__run001",
            output_dir="results/runs/week11_pilot_v1__run001",
            benchmark_environment=self._environment(),
            source_commit="not-a-sha",
        )

        with self.assertRaises(ValueError):
            validate_execution_context(wrong_output)
        with self.assertRaises(ValueError):
            validate_execution_context(wrong_source)

    def test_execution_context_serialization_keeps_run_level_fields(self):
        context = Week11ExecutionContext(
            execution_id="week11_pilot_v1__run001",
            output_dir="results/runs/week11_pilot_v1__run001",
            benchmark_environment=self._environment(),
            source_commit="a" * 40,
        )

        self.assertEqual(
            execution_context_to_dict(context),
            {
                "execution_id": "week11_pilot_v1__run001",
                "output_dir": "results/runs/week11_pilot_v1__run001",
                "benchmark_environment": self._environment(),
                "source_commit": "a" * 40,
            },
        )


if __name__ == "__main__":
    unittest.main()
