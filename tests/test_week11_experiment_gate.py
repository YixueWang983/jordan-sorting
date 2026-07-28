"""Week 11 frozen integration-pilot gate tests."""

import json
import subprocess
import sys
import unittest
from dataclasses import FrozenInstanceError, replace
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "experiments"))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from paper_execution_policy import (  # noqa: E402
    CHECKED_MODE,
    MINIMAL_MODE,
    PAPER_EXECUTION_POLICIES,
)
from week11_experiment_gate import (  # noqa: E402
    PAPER_ALGORITHM_NAME,
    WEEK11_EXPERIMENT_GATE,
    gate_to_dict,
    validate_week11_experiment_gate,
)


class Week11ExperimentGateTests(unittest.TestCase):
    def test_frozen_gate_has_expected_contract_and_row_counts(self):
        gate = validate_week11_experiment_gate()

        self.assertEqual(gate.paper_execution_mode, MINIMAL_MODE)
        self.assertEqual(gate.audit_execution_mode, CHECKED_MODE)
        self.assertEqual(gate.case_count, 35)
        self.assertEqual(gate.raw_row_count, 1050)
        self.assertEqual(gate.case_summary_row_count, 105)
        self.assertEqual(gate.group_summary_row_count, 45)
        self.assertIn(PAPER_ALGORITHM_NAME, gate.algorithms)
        self.assertTrue(gate.output_dir.endswith(gate.run_id))

    def test_selected_modes_preserve_timing_and_audit_boundaries(self):
        timing = PAPER_EXECUTION_POLICIES[
            WEEK11_EXPERIMENT_GATE.paper_execution_mode
        ]
        audit = PAPER_EXECUTION_POLICIES[
            WEEK11_EXPERIMENT_GATE.audit_execution_mode
        ]

        self.assertFalse(timing.record_trace)
        self.assertFalse(timing.count_operations)
        self.assertFalse(timing.validate_backend_commits)
        self.assertTrue(audit.record_trace)
        self.assertTrue(audit.count_operations)
        self.assertTrue(audit.validate_backend_commits)

    def test_gate_is_immutable(self):
        with self.assertRaises(FrozenInstanceError):
            WEEK11_EXPERIMENT_GATE.measured_runs = 20

    def test_gate_rejects_configuration_drift(self):
        changed = (
            replace(WEEK11_EXPERIMENT_GATE, paper_execution_mode=CHECKED_MODE),
            replace(WEEK11_EXPERIMENT_GATE, measured_runs=20),
            replace(WEEK11_EXPERIMENT_GATE, randomized_cases=3),
            replace(WEEK11_EXPERIMENT_GATE, valid_families=("flat_valid",)),
            replace(WEEK11_EXPERIMENT_GATE, output_dir="results/other"),
        )

        for gate in changed:
            with self.subTest(gate=gate):
                with self.assertRaises((ValueError, RuntimeError)):
                    validate_week11_experiment_gate(gate)

    def test_gate_json_is_machine_readable_and_not_an_experiment_run(self):
        completed = subprocess.run(
            [sys.executable, "experiments/week11_experiment_gate.py"],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        result = json.loads(completed.stdout)

        self.assertEqual(result["status"], "frozen_not_executed")
        self.assertEqual(result["paper_execution_mode"], MINIMAL_MODE)
        self.assertEqual(result["raw_row_count"], 1050)

    def test_gate_to_dict_returns_independent_mutable_containers(self):
        first = gate_to_dict()
        first["sizes"].append(1024)
        second = gate_to_dict()

        self.assertEqual(second["sizes"], [32, 64, 128, 256, 512])


if __name__ == "__main__":
    unittest.main()
