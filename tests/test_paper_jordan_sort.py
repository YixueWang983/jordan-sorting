"""1990 paper Jordan-sorting ordinary-list 主循环测试。"""

import ast
import inspect
import itertools
import sys
import unittest
from dataclasses import replace
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import paper_jordan  # noqa: E402
import paper_jordan_sort  # noqa: E402
from generators import (  # noqa: E402
    generate_flat,
    generate_incremental_valid,
    generate_nested,
)
from oracle import oracle  # noqa: E402
from paper_jordan_sort import (  # noqa: E402
    _run_paper_jordan_valid,
    paper_jordan_diagnostics_valid,
    paper_jordan_sort_valid,
)


class PaperJordanSortValidTests(unittest.TestCase):
    def test_small_inputs_are_handled_without_main_loop(self):
        self.assertEqual(paper_jordan_sort_valid([]), [])
        self.assertEqual(paper_jordan_sort_valid([7]), [7])

        for values in itertools.permutations([1, 2]):
            with self.subTest(values=values):
                self.assertEqual(paper_jordan_sort_valid(values), [1, 2])

        for values in itertools.permutations([1, 2, 3]):
            with self.subTest(values=values):
                self.assertEqual(paper_jordan_sort_valid(values), [1, 2, 3])

    def test_duplicate_small_inputs_are_rejected(self):
        for values in ([1, 1], [1, 1, 2], [1, 2, 2]):
            with self.subTest(values=values):
                with self.assertRaises(ValueError):
                    paper_jordan_sort_valid(values)

    def test_representative_valid_generators_match_standard_order(self):
        generators = [
            ("flat", lambda n: generate_flat(n)),
            ("nested", lambda n: generate_nested(n)),
            (
                "incremental",
                lambda n: generate_incremental_valid(n, seed=9000 + n),
            ),
        ]

        for family, generator in generators:
            for n in (4, 5, 8, 16, 32):
                with self.subTest(family=family, n=n):
                    values = generator(n)
                    oracle_result = oracle(values)
                    self.assertTrue(oracle_result["valid"], values)
                    self.assertEqual(
                        paper_jordan_sort_valid(values),
                        oracle_result["sorted"],
                    )

    def test_odd_z1_adjustment_traces_sort_end_to_end(self):
        cases = [
            [1, 2, 3, 4, 6, 7, 0, 5],
            [6, 5, 4, 3, 1, 0, 7, 2],
        ]

        for values in cases:
            with self.subTest(values=values):
                self.assertTrue(oracle(values)["valid"])
                self.assertEqual(paper_jordan_sort_valid(values), sorted(values))

    def test_all_oracle_valid_permutations_through_n7(self):
        expected_counts = {
            4: 16,
            5: 50,
            6: 144,
            7: 462,
        }

        for n, expected_count in expected_counts.items():
            valid_count = 0
            expected_order = list(range(1, n + 1))
            for values in itertools.permutations(expected_order):
                if not oracle(values)["valid"]:
                    continue

                valid_count += 1
                with self.subTest(n=n, values=values):
                    self.assertEqual(
                        paper_jordan_sort_valid(values),
                        expected_order,
                    )

            self.assertEqual(valid_count, expected_count)

    def test_input_sequence_is_not_modified(self):
        values = [2, 3, 1, 4]

        result = paper_jordan_sort_valid(values)

        self.assertEqual(values, [2, 3, 1, 4])
        self.assertEqual(result, [1, 2, 3, 4])

    def test_materialized_main_path_does_not_copy_values_again(self):
        public_tree = ast.parse(
            inspect.getsource(paper_jordan_sort.paper_jordan_sort_valid)
        )
        runner_tree = ast.parse(
            inspect.getsource(paper_jordan_sort._run_paper_jordan_valid)
        )
        initializer_tree = ast.parse(
            inspect.getsource(paper_jordan._initialize_paper_jordan_state_values)
        )

        def count_list_calls(tree):
            return sum(
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "list"
                for node in ast.walk(tree)
            )

        self.assertEqual(count_list_calls(public_tree), 1)
        self.assertEqual(count_list_calls(runner_tree), 0)
        self.assertEqual(count_list_calls(initializer_tree), 0)

    def test_step_control_flow_exists_only_once_across_core_modules(self):
        step_calls = {
            "step1_select_predecessor_boundary",
            "step2_select_successor_boundary",
            "step3a_increasing",
            "step3a_decreasing",
            "step3b_increasing",
            "step3b_decreasing",
            "step3c_increasing",
            "step3c_decreasing",
        }
        call_counts = {name: 0 for name in step_calls}

        for module in (paper_jordan, paper_jordan_sort):
            tree = ast.parse(inspect.getsource(module))
            for node in ast.walk(tree):
                if (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name)
                    and node.func.id in call_counts
                ):
                    call_counts[node.func.id] += 1

        self.assertEqual(call_counts, {name: 1 for name in step_calls})

    def test_shared_runner_returns_complete_state(self):
        values = [2, 3, 1, 4]

        state = _run_paper_jordan_valid(list(values))

        self.assertEqual(state.processed_count, len(values))
        self.assertEqual(state.partial_order.to_list(), [1, 2, 3, 4])
        self.assertTrue(paper_jordan.validate_paper_jordan_state(state))

    def test_shared_runner_invokes_invariant_callback_for_each_prefix(self):
        values = [1, 6, 2, 5, 3, 4]
        checked_prefixes = []

        def check_state(state):
            paper_jordan.validate_paper_jordan_state(state)
            checked_prefixes.append(state.processed_count)

        state = _run_paper_jordan_valid(
            list(values),
            invariant_callback=check_state,
        )

        self.assertEqual(checked_prefixes, [3, 4, 5, 6])
        self.assertEqual(state.metrics["invariant_checks"], 4)

    def test_diagnostics_reuses_core_and_returns_independent_data(self):
        values = [1, 6, 2, 5, 3, 4]

        result = paper_jordan_diagnostics_valid(values)

        self.assertEqual(result["output"], sorted(values))
        self.assertEqual(result["processed_count"], len(values))
        self.assertTrue(result["invariants_valid"])
        self.assertEqual(result["metrics"]["invariant_checks"], len(values) - 2)
        self.assertEqual(
            result["metrics"]["trace_event_count"],
            len(result["trace"]),
        )
        self.assertEqual(result["metrics"]["output_insertions"], len(values) - 3)

        result["metrics"]["output_insertions"] = -1
        second = paper_jordan_diagnostics_valid(values)
        self.assertEqual(second["metrics"]["output_insertions"], len(values) - 3)

    def test_diagnostics_handles_small_inputs_without_core_loop(self):
        for values, expected in (([], []), ([2], [2]), ([2, 1], [1, 2])):
            with self.subTest(values=values):
                result = paper_jordan_diagnostics_valid(values)

                self.assertEqual(result["output"], expected)
                self.assertEqual(result["processed_count"], len(values))
                self.assertEqual(result["trace"], [])
                self.assertTrue(result["invariants_valid"])
                self.assertTrue(all(value == 0 for value in result["metrics"].values()))

    def test_invariant_audit_rejects_corrupted_trace_state(self):
        state = _run_paper_jordan_valid([2, 3, 1, 4])
        state.trace.pop()

        with self.assertRaises(RuntimeError):
            paper_jordan.validate_paper_jordan_state(state)

    def test_invariant_audit_rejects_forged_stage_result(self):
        state = _run_paper_jordan_valid([2, 3, 1, 4])
        state.stage_results[4]["step3a_insert_pair"] = object()

        with self.assertRaises(RuntimeError):
            paper_jordan.validate_paper_jordan_state(state)

    def test_invariant_audit_rejects_forged_trace_payload(self):
        state = _run_paper_jordan_valid([2, 3, 1, 4])
        step3c_event = next(
            event
            for event in state.trace
            if event["step"] == "step3c_insert_output_point"
        )
        step3c_event["pair_id"] = 999

        with self.assertRaises(RuntimeError):
            paper_jordan.validate_paper_jordan_state(state)

    def test_invariant_audit_rejects_extra_state_pair_alias(self):
        state = _run_paper_jordan_valid([2, 3, 1, 4])
        state.pairs[999] = state.pairs[2]

        with self.assertRaises(RuntimeError):
            paper_jordan.validate_paper_jordan_state(state)

    def test_invariant_audit_rejects_unknown_or_reordered_trace_events(self):
        state_with_unknown = _run_paper_jordan_valid([2, 3, 1, 4])
        state_with_unknown.trace[2]["unexpected"] = True

        with self.assertRaises(RuntimeError):
            paper_jordan.validate_paper_jordan_state(state_with_unknown)

        state_with_reordering = _run_paper_jordan_valid([2, 3, 1, 4])
        state_with_reordering.trace[2], state_with_reordering.trace[3] = (
            state_with_reordering.trace[3],
            state_with_reordering.trace[2],
        )

        with self.assertRaises(RuntimeError):
            paper_jordan.validate_paper_jordan_state(state_with_reordering)

    def test_invariant_audit_rejects_coordinated_step3a_forgery(self):
        state = _run_paper_jordan_valid([1, 2, 3, 4])
        original = state.stage_results[4]["step3a_insert_pair"]
        forged = replace(
            original,
            parent_pair_id=999,
            sibling_list_id=999,
        )
        state.stage_results[4]["step3a_insert_pair"] = forged
        event = next(
            event for event in state.trace if event["step"] == "step3a_insert_pair"
        )
        event["parent_pair_id"] = 999
        event["sibling_list_id"] = 999

        with self.assertRaisesRegex(RuntimeError, "deterministic replay"):
            paper_jordan.validate_paper_jordan_state(state)

    def test_invariant_audit_rejects_coordinated_step3b_forgery(self):
        state = _run_paper_jordan_valid([2, 3, 1, 4])
        original = state.stage_results[4]["step3b_split_sibling_list"]
        forged = replace(
            original,
            input_list_id=999,
            left_list_id=1000,
        )
        state.stage_results[4]["step3b_split_sibling_list"] = forged
        event = next(
            event
            for event in state.trace
            if event["step"] == "step3b_split_sibling_list"
        )
        event["input_list_id"] = 999
        event["left_list_id"] = 1000

        with self.assertRaisesRegex(RuntimeError, "deterministic replay"):
            paper_jordan.validate_paper_jordan_state(state)

    def test_invariant_audit_rejects_coordinated_step3c_forgery(self):
        state = _run_paper_jordan_valid([2, 3, 1, 4])
        original = state.stage_results[4]["step3c_insert_output_point"]
        forged = replace(original, child_pair_id=3)
        state.stage_results[4]["step3c_insert_output_point"] = forged
        event = next(
            event
            for event in state.trace
            if event["step"] == "step3c_insert_output_point"
        )
        event["child_pair_id"] = 3

        with self.assertRaisesRegex(RuntimeError, "deterministic replay"):
            paper_jordan.validate_paper_jordan_state(state)

    def test_invariant_audit_rejects_coordinated_split_metric_forgery(self):
        state = _run_paper_jordan_valid([2, 3, 1, 4])
        event = next(
            event
            for event in state.trace
            if event["step"] == "step3b_split_sibling_list"
        )
        event["input_size"] = 2
        event["left_size"] = 2
        for metric_name in (
            "sibling_scan_checks",
            "split_items_scanned",
            "split_items_copied",
            "split_items_transferred",
        ):
            state.metrics[metric_name] += 1

        with self.assertRaisesRegex(RuntimeError, "deterministic replay"):
            paper_jordan.validate_paper_jordan_state(state)

    def test_comparable_non_numeric_values_are_supported(self):
        values = ["b", "c", "a", "d"]

        self.assertTrue(oracle(values)["valid"])
        self.assertEqual(
            paper_jordan_sort_valid(values),
            ["a", "b", "c", "d"],
        )

    def test_core_modules_do_not_use_forbidden_shortcuts(self):
        forbidden_calls = {"sorted", "rank_map", "oracle", "simplified_jordan_sort"}

        for module in (paper_jordan, paper_jordan_sort):
            with self.subTest(module=module.__name__):
                tree = ast.parse(inspect.getsource(module))
                imported_modules = {
                    alias.name
                    for node in ast.walk(tree)
                    if isinstance(node, ast.Import)
                    for alias in node.names
                }
                imported_from = {
                    node.module
                    for node in ast.walk(tree)
                    if isinstance(node, ast.ImportFrom)
                }
                called_names = {
                    node.func.id
                    for node in ast.walk(tree)
                    if isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name)
                }

                self.assertNotIn("oracle", imported_modules)
                self.assertNotIn("oracle", imported_from)
                self.assertTrue(forbidden_calls.isdisjoint(called_names))


if __name__ == "__main__":
    unittest.main()
