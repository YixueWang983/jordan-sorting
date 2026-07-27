"""SortedOrderList 的聚焦单元测试。"""

import itertools
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from partial_sorted_list import (  # noqa: E402
    NEGATIVE_INFINITY,
    POSITIVE_INFINITY,
    PointRef,
    SortedOrderList,
)


class SortedOrderListTests(unittest.TestCase):
    def test_empty_list_connects_the_two_sentinels(self):
        order = SortedOrderList()

        self.assertEqual(len(order), 0)
        self.assertEqual(order.to_list(), [])
        self.assertEqual(order.to_point_ids(), [])
        self.assertIs(order.successor(NEGATIVE_INFINITY), POSITIVE_INFINITY)
        self.assertIs(order.predecessor(POSITIVE_INFINITY), NEGATIVE_INFINITY)
        self.assertTrue(order.validate_links())

    def test_single_point_can_be_inserted_from_either_sentinel(self):
        after_negative = SortedOrderList()
        before_positive = SortedOrderList()

        after_negative.insert_after(NEGATIVE_INFINITY, PointRef(1, 4))
        before_positive.insert_before(POSITIVE_INFINITY, PointRef(1, 4))

        for order in (after_negative, before_positive):
            self.assertEqual(order.to_list(), [4])
            self.assertIs(order.predecessor(1), NEGATIVE_INFINITY)
            self.assertIs(order.successor(1), POSITIVE_INFINITY)
            self.assertTrue(order.validate_links())

    def test_before_and_after_insertions_preserve_neighbors(self):
        order = SortedOrderList()
        order.insert_after(NEGATIVE_INFINITY, PointRef(2, 20))
        order.insert_before(2, PointRef(1, 10))
        order.insert_after(2, PointRef(4, 40))
        order.insert_before(4, PointRef(3, 30))

        self.assertEqual(order.to_point_ids(), [1, 2, 3, 4])
        self.assertEqual(order.to_list(), [10, 20, 30, 40])
        self.assertEqual(order.predecessor(3), 2)
        self.assertEqual(order.successor(3), 4)
        self.assertTrue(order.validate_links())

    def test_all_six_three_point_input_orders_reach_sorted_state(self):
        for values in itertools.permutations([1, 2, 3]):
            with self.subTest(values=values):
                order = SortedOrderList()
                inserted = []

                for paper_index, value in enumerate(values, start=1):
                    lower_ids = [
                        point_id
                        for point_id, previous_value in inserted
                        if previous_value < value
                    ]
                    anchor = lower_ids[-1] if lower_ids else NEGATIVE_INFINITY
                    order.insert_after(anchor, PointRef(paper_index, value))
                    inserted = [
                        (point_id, point_value)
                        for point_id, point_value in zip(
                            order.to_point_ids(),
                            order.to_list(),
                        )
                    ]

                self.assertEqual(order.to_list(), [1, 2, 3])
                self.assertTrue(order.validate_links())

    def test_string_values_are_supported_when_mutually_comparable(self):
        order = SortedOrderList()
        order.insert_after(NEGATIVE_INFINITY, PointRef(1, "b"))
        order.insert_before(1, PointRef(2, "a"))
        order.insert_after(1, PointRef(3, "c"))

        self.assertEqual(order.to_list(), ["a", "b", "c"])
        self.assertTrue(order.validate_links())

    def test_get_point_returns_the_original_point_reference(self):
        order = SortedOrderList()
        point = PointRef(7, 12.5)
        order.insert_after(NEGATIVE_INFINITY, point)

        self.assertIs(order.get_point(7), point)
        self.assertIn(7, order)
        self.assertNotIn(8, order)

    def test_duplicate_point_id_is_rejected_without_mutation(self):
        order = SortedOrderList()
        order.insert_after(NEGATIVE_INFINITY, PointRef(1, 10))

        with self.assertRaises(ValueError):
            order.insert_after(1, PointRef(1, 20))

        self.assertEqual(order.to_list(), [10])
        self.assertTrue(order.validate_links())

    def test_duplicate_or_out_of_position_value_is_rejected(self):
        order = SortedOrderList()
        order.insert_after(NEGATIVE_INFINITY, PointRef(1, 10))
        order.insert_after(1, PointRef(2, 30))

        invalid_points = [
            PointRef(3, 10),
            PointRef(4, 5),
            PointRef(5, 40),
        ]
        actions = [
            lambda: order.insert_before(2, invalid_points[0]),
            lambda: order.insert_after(1, invalid_points[1]),
            lambda: order.insert_before(2, invalid_points[2]),
        ]

        for action in actions:
            with self.subTest(action=action):
                with self.assertRaises(ValueError):
                    action()

        self.assertEqual(order.to_list(), [10, 30])
        self.assertTrue(order.validate_links())

    def test_unknown_point_ids_are_rejected(self):
        order = SortedOrderList()

        for operation in (
            lambda: order.predecessor(99),
            lambda: order.successor(99),
            lambda: order.insert_before(99, PointRef(1, 1)),
            lambda: order.insert_after(99, PointRef(1, 1)),
            lambda: order.get_point(99),
        ):
            with self.subTest(operation=operation):
                with self.assertRaises(KeyError):
                    operation()

    def test_invalid_sentinel_operations_are_rejected(self):
        order = SortedOrderList()

        with self.assertRaises(IndexError):
            order.predecessor(NEGATIVE_INFINITY)
        with self.assertRaises(IndexError):
            order.successor(POSITIVE_INFINITY)
        with self.assertRaises(IndexError):
            order.insert_before(NEGATIVE_INFINITY, PointRef(1, 1))
        with self.assertRaises(IndexError):
            order.insert_after(POSITIVE_INFINITY, PointRef(1, 1))

        self.assertTrue(order.validate_links())

    def test_insert_requires_point_ref(self):
        order = SortedOrderList()

        with self.assertRaises(TypeError):
            order.insert_after(NEGATIVE_INFINITY, (1, 10))

    def test_incomparable_value_failure_does_not_modify_list(self):
        order = SortedOrderList()
        order.insert_after(NEGATIVE_INFINITY, PointRef(1, 10))

        with self.assertRaises(TypeError):
            order.insert_after(1, PointRef(2, "20"))

        self.assertEqual(order.to_list(), [10])
        self.assertTrue(order.validate_links())

    def test_point_ref_rejects_invalid_paper_indices(self):
        for bad_index in (0, -1):
            with self.subTest(bad_index=bad_index):
                with self.assertRaises(ValueError):
                    PointRef(bad_index, 10)

        for bad_index in (True, 1.5, "1"):
            with self.subTest(bad_index=bad_index):
                with self.assertRaises(TypeError):
                    PointRef(bad_index, 10)


if __name__ == "__main__":
    unittest.main()
