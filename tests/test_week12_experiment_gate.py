"""Tests for the frozen, unexecuted Week 12 experiment gate."""

import json
import hashlib
import subprocess
import sys
import unittest
from dataclasses import replace
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "experiments"))

from week12_experiment_gate import (  # noqa: E402
    WEEK12_EXPERIMENT_GATE,
    gate_to_dict,
    validate_week12_experiment_gate,
)


class Week12ExperimentGateTests(unittest.TestCase):
    def test_gate_is_frozen_and_unexecuted(self):
        gate = validate_week12_experiment_gate()

        self.assertEqual(gate.status, "frozen_not_executed")
        self.assertEqual(gate.protocol_version, "week12_formal_sorting_v1")
        self.assertEqual(gate.scope, "oracle_certified_valid_input_sorting")
        self.assertTrue(gate.recognition_separate)

    def test_gate_uses_week11_evidence_without_reusing_protocol_version(self):
        gate = WEEK12_EXPERIMENT_GATE

        self.assertEqual(
            gate.source_pilot_execution_id,
            "week11_pilot_v1__run003",
        )
        self.assertEqual(
            gate.source_pilot_commit,
            "01f6480fe179dcbe0f99486be86384b61dd4121f",
        )
        self.assertNotEqual(gate.protocol_version, "week11_pilot_v1")
        manifest_path = PROJECT_ROOT / gate.source_pilot_manifest_path
        self.assertEqual(
            hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
            gate.source_pilot_manifest_sha256,
        )

    def test_gate_freezes_formal_scale_and_row_counts(self):
        gate = WEEK12_EXPERIMENT_GATE

        self.assertEqual(gate.sizes, (32, 64, 128, 256, 512))
        self.assertEqual(gate.randomized_cases, 10)
        self.assertEqual(gate.warmup_runs, 5)
        self.assertEqual(gate.measured_runs, 20)
        self.assertEqual(gate.case_count, 60)
        self.assertEqual(gate.raw_row_count, 3600)
        self.assertEqual(gate.case_summary_row_count, 180)
        self.assertEqual(gate.group_summary_row_count, 45)
        self.assertEqual(gate.case_audit_row_count, 60)

    def test_gate_retains_minimal_timing_and_checked_audit(self):
        gate = WEEK12_EXPERIMENT_GATE

        self.assertEqual(gate.paper_execution_mode, "minimal")
        self.assertEqual(gate.audit_execution_mode, "checked")
        self.assertEqual(len(gate.algorithms), 3)

    def test_gate_rejects_any_configuration_drift(self):
        drifted = replace(WEEK12_EXPERIMENT_GATE, measured_runs=21)

        with self.assertRaisesRegex(ValueError, "frozen contract"):
            validate_week12_experiment_gate(drifted)

    def test_gate_json_contains_derived_counts_and_no_execution_context(self):
        record = gate_to_dict()

        self.assertEqual(record["status"], "frozen_not_executed")
        self.assertEqual(record["raw_row_count"], 3600)
        self.assertNotIn("execution_id", record)
        self.assertNotIn("output_dir", record)
        self.assertNotIn("benchmark_environment", record)

    def test_gate_rejects_changed_source_manifest(self):
        drifted = replace(
            WEEK12_EXPERIMENT_GATE,
            source_pilot_manifest_sha256="0" * 64,
        )

        with self.assertRaisesRegex(ValueError, "frozen contract"):
            validate_week12_experiment_gate(drifted)

    def test_gate_cli_is_read_only_json(self):
        result = subprocess.run(
            [sys.executable, "experiments/week12_experiment_gate.py"],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        record = json.loads(result.stdout)

        self.assertEqual(record["status"], "frozen_not_executed")
        self.assertEqual(record["case_count"], 60)


if __name__ == "__main__":
    unittest.main()
