"""CLI acceptance regressions with deliberate test doubles, never a real backend."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import test_finger_backend_contract_model as contracts


ADAPTER_FIXTURE = '''
import __main__ as contract
import unittest

# This fixture runs only through the contract script's CLI. All classes below
# deliberately wrap/subclass the reference model; none is a production adapter.
class ModelDouble(contract.OrderedListModel):
    pass

def skip():
    raise unittest.SkipTest("synthetic adapter skips construction")

def error():
    raise RuntimeError("synthetic construction error")

class SkipSplit(ModelDouble):
    def split_value(self, handle, cut):
        raise unittest.SkipTest("synthetic split subtest skip")

class BrokenAfterSplit(ModelDouble):
    has_split = False
    def split_value(self, handle, value):
        result = super().split_value(handle, value)
        self.has_split = True
        return result
    def insert_boundary(self, item, anchor_id, side):
        if self.has_split:
            raise RuntimeError("synthetic defect: insertion disabled after split")
        return super().insert_boundary(item, anchor_id, side)
'''


class ContractRunnerTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.fixture_dir = Path(temporary.name)
        (self.fixture_dir / "contract_test_adapters.py").write_text(ADAPTER_FIXTURE)
        (self.fixture_dir / "expected_failure_adapter.py").write_text('''
import __main__ as contract
import unittest
from contract_test_adapters import ModelDouble

@unittest.expectedFailure
def fail(self):
    self.fail("synthetic expected failure")
contract.OperationContractTests.test_singleton_has_two_boundaries = fail
''')
        self.script = Path(contracts.__file__).resolve()
        self.expected = len(unittest.TestLoader().getTestCaseNames(contracts.OperationContractTests))

    def run_cli(self, *args, exit_code=0):
        result = subprocess.run(
            [sys.executable, str(self.script), *args],
            cwd=self.fixture_dir,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1",
                 "PYTHONPATH": str(self.fixture_dir)},
            text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=15,
        )
        self.assertEqual(result.returncode, exit_code, result.stdout + result.stderr)
        report = json.loads(result.stdout.splitlines()[-1])
        return report

    def run_adapter(self, name="ModelDouble", *args, exit_code=0):
        return self.run_cli("--factory", f"contract_test_adapters:{name}",
                            *args, exit_code=exit_code)

    def assert_rejected(self, report):
        self.assertEqual(report["status"], "REJECTED")
        self.assertFalse(report["contract_acceptance_passed"])
        self.assertFalse(report["backend_ready_for_timing"])

    def test_strict_reference_model_counts_are_separate(self):
        report = self.run_cli("--strict")
        self.assertEqual(report["scope"], "reference_model_only")
        self.assertTrue(report["contract_acceptance_passed"])
        self.assertEqual(report["operation_contracts"]["passed_methods"], self.expected)
        self.assertEqual(report["reference_model_self_tests"]["passed_methods"], 4)
        self.assertFalse(report["backend_ready_for_timing"])

    def test_strict_complete_external_double_has_only_semantic_acceptance(self):
        report = self.run_adapter("ModelDouble", "--strict")
        self.assertTrue(report["contract_acceptance_passed"])
        self.assertEqual(report["operation_contracts"]["subject"], "external_adapter")
        self.assertEqual(report["operation_contracts"]["passed_methods"], self.expected)
        self.assertEqual(report["reference_model_self_tests"]["passed_methods"], 4)
        self.assertFalse(report["jordan_integration_validated"])
        self.assertFalse(report["efficiency_bound_proved"])
        self.assertFalse(report["backend_ready_for_timing"])

    def test_strict_operation_suite_can_run_without_model_self_tests(self):
        report = self.run_adapter("ModelDouble", "--strict", "OperationContractTests")
        self.assertTrue(report["contract_acceptance_passed"])
        self.assertEqual(report["reference_model_self_tests"]["started_methods"], 0)

    def test_strict_rejects_adapter_that_skips_every_contract(self):
        report = self.run_adapter("skip", "--strict", exit_code=1)
        self.assert_rejected(report)
        self.assertEqual(report["operation_contracts"]["skips"], self.expected)
        self.assertEqual(report["operation_contracts"]["passed_methods"], 0)
        self.assertEqual(report["reference_model_self_tests"]["passed_methods"], 4)

    def test_strict_rejects_only_model_self_tests(self):
        report = self.run_adapter("skip", "--strict", "ModelAuditSelfTests", exit_code=1)
        self.assert_rejected(report)
        self.assertEqual(report["operation_contracts"]["started_methods"], 0)
        self.assertEqual(report["reference_model_self_tests"]["passed_methods"], 4)

    def test_strict_rejects_zero_selected_tests(self):
        report = self.run_adapter("ModelDouble", "--strict", "-k", "no_matching_test", exit_code=1)
        self.assert_rejected(report)
        self.assertEqual(report["tests_run"], 0)

    def test_strict_rejects_partial_operation_selection(self):
        report = self.run_adapter("ModelDouble", "--strict", "-k", "singleton", exit_code=1)
        self.assert_rejected(report)
        self.assertTrue(report["partial_check"])
        self.assertEqual(report["operation_contracts"]["passed_methods"], 1)

    def test_strict_rejects_duplicate_contract_execution(self):
        report = self.run_adapter("ModelDouble", "--strict", "OperationContractTests",
                                  "OperationContractTests", exit_code=1)
        self.assert_rejected(report)
        self.assertEqual(report["operation_contracts"]["started_methods"], self.expected * 2)
        self.assertEqual(len(report["operation_contracts"]["duplicate_methods"]), self.expected)

    def test_strict_rejects_subtest_skips(self):
        report = self.run_adapter("SkipSplit", "--strict", exit_code=1)
        self.assert_rejected(report)
        self.assertGreater(report["operation_contracts"]["skips"], 0)

    def test_strict_rejects_expected_failure(self):
        report = self.run_cli("--strict", "--factory", "expected_failure_adapter:ModelDouble",
                              exit_code=1)
        self.assert_rejected(report)
        self.assertEqual(report["operation_contracts"]["expected_failures"], 1)

    def test_strict_rejects_adapter_errors(self):
        report = self.run_adapter("error", "--strict", exit_code=1)
        self.assert_rejected(report)
        self.assertEqual(report["operation_contracts"]["errors"], self.expected)

    def test_development_subset_never_claims_acceptance(self):
        report = self.run_adapter("skip", "ModelAuditSelfTests")
        self.assertEqual(report["mode"], "development")
        self.assertTrue(report["partial_check"])
        self.assertFalse(report["contract_acceptance_passed"])

    def test_development_full_run_never_claims_strict_acceptance(self):
        report = self.run_adapter()
        self.assertFalse(report["partial_check"])
        self.assertFalse(report["contract_acceptance_passed"])

    def test_missing_adapter_is_unavailable_not_skipped(self):
        report = self.run_cli("--strict", "--factory", "nonexistent_contract_adapter:factory",
                              exit_code=2)
        self.assertEqual(report["status"], "UNAVAILABLE")
        self.assertFalse(report["contract_acceptance_passed"])

    def test_interleaving_exposes_post_split_insertion_defect(self):
        new_methods = {"test_split_adopt_insert_and_resplit_both_outputs",
                       "test_empty_side_split_then_insert_and_resplit"}
        old_methods = ["OperationContractTests." + name for name in
                       unittest.TestLoader().getTestCaseNames(contracts.OperationContractTests)
                       if name not in new_methods]
        # Reproduce the old blind spot, then require the full suite to reject it.
        partial = self.run_adapter("BrokenAfterSplit", *old_methods)
        self.assertEqual(partial["operation_contracts"]["passed_methods"], self.expected - 2)
        self.assertFalse(partial["contract_acceptance_passed"])
        full = self.run_adapter("BrokenAfterSplit", "--strict", exit_code=1)
        self.assert_rejected(full)
        self.assertEqual(full["operation_contracts"]["passed_methods"], self.expected - 2)
        self.assertGreater(full["operation_contracts"]["errors"], 0)
        for name in new_methods:
            self.assertTrue(any(test.endswith("." + name)
                                for test in full["operation_contracts"]["missing_passes"]))


if __name__ == "__main__":
    unittest.main()
