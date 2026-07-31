"""Versioned Week 11 v2 M4 experiment-gate tests."""

import hashlib
import json
import subprocess
import sys
import unittest
from dataclasses import FrozenInstanceError, replace
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "experiments"))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from week11_experiment_gate_v1 import (  # noqa: E402
    WEEK11_EXPERIMENT_GATE_V1,
    WEEK11_MACHINE_BASELINE_PATH_V1,
    WEEK11_OUTPUT_DIR_V1,
    WEEK11_RUN_ID_V1,
)
from week11_experiment_gate_v2 import (  # noqa: E402
    WEEK11_EXPERIMENT_GATE_V2,
    WEEK11_MACHINE_BASELINE_SHA256_V2,
    gate_to_dict_v2,
    validate_week11_experiment_gate_v2,
)


class Week11ExperimentGateV2Tests(unittest.TestCase):
    def test_v2_gate_binds_the_m4_machine_baseline(self):
        gate = validate_week11_experiment_gate_v2()

        self.assertEqual(gate.gate_version, "v2")
        self.assertEqual(gate.run_id, "week11_paper_sorting_pilot_v2_m4")
        self.assertEqual(
            gate.output_dir,
            "results/runs/week11_paper_sorting_pilot_v2_m4",
        )
        self.assertEqual(
            gate.machine_baseline_path,
            "docs/analysis/week11_machine_baseline_v2_m4.json",
        )
        self.assertEqual(
            gate.machine_baseline_sha256,
            WEEK11_MACHINE_BASELINE_SHA256_V2,
        )
        self.assertEqual(gate.machine_identity_id, "week11_v2_m4_mac16_13")
        self.assertEqual(gate.case_count, 35)
        self.assertEqual(gate.raw_row_count, 1050)
        self.assertEqual(gate.case_summary_row_count, 105)
        self.assertEqual(gate.group_summary_row_count, 45)

    def test_v1_and_v2_use_distinct_run_and_output_identifiers(self):
        self.assertIsNot(WEEK11_EXPERIMENT_GATE_V1, WEEK11_EXPERIMENT_GATE_V2)
        self.assertNotEqual(WEEK11_RUN_ID_V1, WEEK11_EXPERIMENT_GATE_V2.run_id)
        self.assertNotEqual(
            WEEK11_OUTPUT_DIR_V1,
            WEEK11_EXPERIMENT_GATE_V2.output_dir,
        )
        self.assertNotEqual(
            WEEK11_MACHINE_BASELINE_PATH_V1,
            WEEK11_EXPERIMENT_GATE_V2.machine_baseline_path,
        )

    def test_v2_gate_hash_matches_the_committed_baseline_bytes(self):
        baseline = PROJECT_ROOT / WEEK11_EXPERIMENT_GATE_V2.machine_baseline_path
        actual = hashlib.sha256(baseline.read_bytes()).hexdigest()

        self.assertEqual(actual, WEEK11_EXPERIMENT_GATE_V2.machine_baseline_sha256)

    def test_v2_gate_is_immutable(self):
        with self.assertRaises(FrozenInstanceError):
            WEEK11_EXPERIMENT_GATE_V2.gate_version = "v3"

    def test_v2_gate_rejects_configuration_or_binding_drift(self):
        changed_gates = (
            replace(WEEK11_EXPERIMENT_GATE_V2, measured_runs=11),
            replace(WEEK11_EXPERIMENT_GATE_V2, gate_version="v1"),
            replace(WEEK11_EXPERIMENT_GATE_V2, run_id="other"),
            replace(WEEK11_EXPERIMENT_GATE_V2, output_dir="results/other"),
            replace(WEEK11_EXPERIMENT_GATE_V2, machine_baseline_path="other.json"),
            replace(WEEK11_EXPERIMENT_GATE_V2, machine_baseline_sha256="0" * 64),
            replace(WEEK11_EXPERIMENT_GATE_V2, machine_identity_id="other"),
        )

        for changed in changed_gates:
            with self.subTest(changed=changed):
                with self.assertRaises(ValueError):
                    validate_week11_experiment_gate_v2(changed)

    def test_v2_gate_json_contains_versioned_machine_binding(self):
        completed = subprocess.run(
            [sys.executable, "experiments/week11_experiment_gate_v2.py"],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        result = json.loads(completed.stdout)

        self.assertEqual(result["status"], "frozen_not_executed")
        self.assertEqual(result["gate_version"], "v2")
        self.assertEqual(result["run_id"], WEEK11_EXPERIMENT_GATE_V2.run_id)
        self.assertEqual(
            result["machine_baseline_sha256"],
            WEEK11_EXPERIMENT_GATE_V2.machine_baseline_sha256,
        )

    def test_v2_gate_to_dict_returns_independent_lists(self):
        first = gate_to_dict_v2()
        first["sizes"].append(1024)
        second = gate_to_dict_v2()

        self.assertEqual(second["sizes"], [32, 64, 128, 256, 512])


if __name__ == "__main__":
    unittest.main()
