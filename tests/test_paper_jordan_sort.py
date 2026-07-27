"""1990 paper Jordan-sorting ordinary-list 主循环测试。"""

import ast
import inspect
import itertools
import sys
import unittest
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
