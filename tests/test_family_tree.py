"""Family tree 结构单元测试。"""

import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from family_tree import (  # noqa: E402
    LOWER,
    UPPER,
    build_family_intervals,
    build_family_tree,
    build_family_trees,
    family_tree_to_dict,
    family_tree_to_debug_lines,
    interval_contains,
    proper_interval_contains,
)


class FamilyTreeTests(unittest.TestCase):
    def test_interval_contains_predicates(self):
        self.assertTrue(interval_contains((1, 6), (1, 6)))
        self.assertTrue(interval_contains((1, 6), (2, 5)))
        self.assertFalse(interval_contains((2, 5), (1, 6)))

        self.assertFalse(proper_interval_contains((1, 6), (1, 6)))
        self.assertTrue(proper_interval_contains((1, 6), (2, 5)))
        self.assertFalse(proper_interval_contains((1, 6), (1, 5)))
        self.assertFalse(proper_interval_contains((1, 6), (2, 6)))

    def test_build_upper_intervals(self):
        seq = [1, 6, 2, 5, 3, 4]

        self.assertEqual(
            build_family_intervals(seq, UPPER),
            [(1, 6), (2, 5), (3, 4)],
        )

    def test_build_lower_intervals(self):
        seq = [1, 6, 2, 5, 3, 4]

        self.assertEqual(
            build_family_intervals(seq, LOWER),
            [(2, 6), (3, 5)],
        )

    def test_build_family_intervals_rejects_invalid_pair_family(self):
        with self.assertRaises(ValueError):
            build_family_intervals([1, 2], "flat_valid")

    def test_flat_upper_family_tree_has_multiple_roots(self):
        tree = build_family_tree([(1, 2), (3, 4), (5, 6)], UPPER)

        self.assertEqual(tree.pair_family, UPPER)
        self.assertEqual(tree.roots, [0, 1, 2])
        self.assertEqual([node.parent for node in tree.nodes], [None, None, None])
        self.assertEqual([node.depth for node in tree.nodes], [0, 0, 0])
        self.assertEqual([node.children for node in tree.nodes], [[], [], []])

    def test_nested_upper_family_tree_parent_chain(self):
        seq = [1, 6, 2, 5, 3, 4]
        tree = build_family_tree(build_family_intervals(seq, UPPER), UPPER)

        self.assertEqual([node.interval for node in tree.nodes], [(1, 6), (2, 5), (3, 4)])
        self.assertEqual(tree.roots, [0])
        self.assertIsNone(tree.nodes[0].parent)
        self.assertEqual(tree.nodes[0].children, [1])
        self.assertEqual(tree.nodes[1].parent, 0)
        self.assertEqual(tree.nodes[1].children, [2])
        self.assertEqual(tree.nodes[2].parent, 1)
        self.assertEqual(tree.nodes[2].children, [])
        self.assertEqual([node.depth for node in tree.nodes], [0, 1, 2])

    def test_nested_lower_family_tree_parent_chain(self):
        seq = [1, 6, 2, 5, 3, 4]
        tree = build_family_tree(build_family_intervals(seq, LOWER), LOWER)

        self.assertEqual([node.interval for node in tree.nodes], [(2, 6), (3, 5)])
        self.assertEqual(tree.roots, [0])
        self.assertIsNone(tree.nodes[0].parent)
        self.assertEqual(tree.nodes[0].children, [1])
        self.assertEqual(tree.nodes[1].parent, 0)
        self.assertEqual(tree.nodes[1].children, [])
        self.assertEqual([node.depth for node in tree.nodes], [0, 1])

    def test_nodes_preserve_input_order_while_roots_are_sorted(self):
        tree = build_family_tree([(5, 6), (1, 2), (3, 4)], UPPER)

        self.assertEqual(
            [node.interval for node in tree.nodes],
            [(5, 6), (1, 2), (3, 4)],
        )
        self.assertEqual(tree.roots, [1, 2, 0])

    def test_build_family_trees_returns_upper_and_lower_trees(self):
        seq = [1, 6, 2, 5, 3, 4]
        trees = build_family_trees(seq)

        self.assertEqual(set(trees.keys()), {UPPER, LOWER})
        self.assertEqual(trees[UPPER].pair_family, UPPER)
        self.assertEqual(trees[LOWER].pair_family, LOWER)
        self.assertEqual(
            [node.interval for node in trees[UPPER].nodes],
            [(1, 6), (2, 5), (3, 4)],
        )
        self.assertEqual(
            [node.interval for node in trees[LOWER].nodes],
            [(2, 6), (3, 5)],
        )

    def test_build_family_trees_handles_empty_and_singleton(self):
        for seq in ([], [1]):
            trees = build_family_trees(seq)

            self.assertEqual(trees[UPPER].nodes, [])
            self.assertEqual(trees[UPPER].roots, [])
            self.assertEqual(trees[LOWER].nodes, [])
            self.assertEqual(trees[LOWER].roots, [])

    def test_build_family_trees_rejects_invalid_sequence(self):
        with self.assertRaises(ValueError):
            build_family_trees([1, 3, 2, 4])

    def test_build_family_tree_rejects_crossing_intervals(self):
        with self.assertRaises(ValueError):
            build_family_tree([(1, 3), (2, 4)], UPPER)

    def test_build_family_tree_rejects_duplicate_intervals(self):
        with self.assertRaises(ValueError):
            build_family_tree([(1, 4), (1, 4)], UPPER)

    def test_build_family_tree_rejects_shared_endpoint_intervals(self):
        with self.assertRaises(ValueError):
            build_family_tree([(1, 4), (1, 3)], UPPER)

    def test_build_family_tree_rejects_invalid_pair_family(self):
        with self.assertRaises(ValueError):
            build_family_tree([(1, 2)], "generator_family")

    def test_build_family_tree_rejects_malformed_intervals(self):
        bad_inputs = [
            [[1, 2]],
            [(1, 2, 3)],
            [(2, 1)],
            [(1, 1)],
            [(1, "2")],
        ]

        for intervals in bad_inputs:
            with self.subTest(intervals=intervals):
                with self.assertRaises(ValueError):
                    build_family_tree(intervals, UPPER)

    def test_family_tree_to_dict(self):
        tree = build_family_tree([(1, 6), (2, 5)], UPPER)
        result = family_tree_to_dict(tree)

        self.assertEqual(result["pair_family"], UPPER)
        self.assertEqual(result["roots"], [0])
        self.assertEqual(
            result["nodes"],
            [
                {
                    "id": 0,
                    "interval": [1, 6],
                    "pair_index": 0,
                    "parent": None,
                    "children": [1],
                    "depth": 0,
                },
                {
                    "id": 1,
                    "interval": [2, 5],
                    "pair_index": 1,
                    "parent": 0,
                    "children": [],
                    "depth": 1,
                },
            ],
        )

    def test_family_tree_to_debug_lines_nested_tree(self):
        tree = build_family_tree([(1, 6), (2, 5), (3, 4)], UPPER)

        self.assertEqual(
            family_tree_to_debug_lines(tree),
            [
                "[1, 6]",
                "  [2, 5]",
                "    [3, 4]",
            ],
        )

    def test_family_tree_to_debug_lines_multiple_roots(self):
        tree = build_family_tree([(1, 2), (3, 4), (5, 6)], UPPER)

        self.assertEqual(
            family_tree_to_debug_lines(tree),
            [
                "[1, 2]",
                "[3, 4]",
                "[5, 6]",
            ],
        )


if __name__ == "__main__":
    unittest.main()
