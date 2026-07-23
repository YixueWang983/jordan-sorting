"""Instrumentation tests for Week 7 diagnostic counters."""

import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from family_tree import UPPER, build_family_tree  # noqa: E402
from instrumentation import OperationMetrics, instrumented_reference_run  # noqa: E402
from oracle import oracle  # noqa: E402
from simplified_jordan import simplified_jordan_sort  # noqa: E402


class InstrumentationTests(unittest.TestCase):
    def test_oracle_metrics_are_deterministic_for_nested_valid_case(self):
        metrics = OperationMetrics()
        result = oracle([1, 6, 2, 5, 3, 4], metrics=metrics)

        self.assertTrue(result["valid"])
        self.assertEqual(metrics.upper_pair_checks, 3)
        self.assertEqual(metrics.lower_pair_checks, 1)
        self.assertEqual(metrics.laminar_pair_checks, 4)
        self.assertEqual(metrics.crossings_found, 0)

    def test_family_tree_metrics_are_deterministic_for_nested_tree(self):
        metrics = OperationMetrics()
        tree = build_family_tree([(1, 6), (2, 5), (3, 4)], UPPER, metrics=metrics)

        self.assertEqual(len(tree.nodes), 3)
        self.assertEqual(metrics.nodes_created, 3)
        self.assertEqual(metrics.nodes_visited, 3)
        self.assertEqual(metrics.parent_candidate_checks, 6)
        self.assertEqual(metrics.containment_checks, 6)
        self.assertEqual(metrics.interval_validation_checks, 6)

    def test_instrumented_reference_run_matches_plain_reference_result(self):
        seq = [1, 6, 2, 5, 3, 4]
        plain = simplified_jordan_sort(seq)
        instrumented = instrumented_reference_run(seq)

        self.assertEqual(instrumented["result"]["valid"], plain["valid"])
        self.assertEqual(instrumented["result"]["sorted"], plain["sorted"])
        self.assertEqual(instrumented["result"]["reason"], plain["reason"])
        self.assertEqual(instrumented["result"]["trace"], plain["trace"])
        self.assertEqual(instrumented["metrics"]["trace_event_count"], len(plain["trace"]))

    def test_instrumented_reference_run_records_invalid_crossing_cost(self):
        instrumented = instrumented_reference_run([1, 3, 2, 4])

        self.assertFalse(instrumented["result"]["valid"])
        self.assertEqual(instrumented["result"]["reason"], "upper crossing")
        self.assertEqual(instrumented["metrics"]["upper_pair_checks"], 1)
        self.assertEqual(instrumented["metrics"]["crossings_found"], 1)
        self.assertEqual(instrumented["metrics"]["nodes_created"], 0)
        self.assertEqual(instrumented["metrics"]["trace_event_count"], 4)


if __name__ == "__main__":
    unittest.main()

