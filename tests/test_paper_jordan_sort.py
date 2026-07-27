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
from paper_jordan_sort import paper_jordan_sort_valid  # noqa: E402


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
