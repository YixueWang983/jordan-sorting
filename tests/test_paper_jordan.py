"""论文 Jordan 算法初始化与 Step 1/2 的聚焦测试。"""

import itertools
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from paper_jordan import (  # noqa: E402
    LOWER_DUMMY_PAIR_ID,
    UPPER_DUMMY_PAIR_ID,
    BoundarySelection,
    initialize_paper_jordan_state,
    pair_family_for_end_index,
    select_processed_same_family_pair,
    step1_select_predecessor_boundary,
    step2_select_successor_boundary,
)
from sibling_list_backend import LOWER, UPPER, PairRecord  # noqa: E402


class PaperJordanInitializationTests(unittest.TestCase):
    def test_pair_family_for_end_index_uses_paper_parity(self):
        self.assertEqual(pair_family_for_end_index(2), UPPER)
        self.assertEqual(pair_family_for_end_index(3), LOWER)
        self.assertEqual(pair_family_for_end_index(8), UPPER)

        with self.assertRaises(ValueError):
            pair_family_for_end_index(1)
        with self.assertRaises(TypeError):
            pair_family_for_end_index(True)

    def test_initialization_orders_all_six_three_point_permutations(self):
        for values in itertools.permutations([1, 2, 3]):
            with self.subTest(values=values):
                state = initialize_paper_jordan_state(values)

                self.assertEqual(state.processed_count, 3)
                self.assertEqual(state.partial_order.to_list(), [1, 2, 3])
                self.assertEqual(
                    set(state.partial_order.to_point_ids()),
                    {1, 2, 3},
                )
                self.assertTrue(state.partial_order.validate_links())
                self.assertTrue(state.sibling_backend.validate_invariants())

    def test_initialization_builds_pairs_dummies_and_ownership(self):
        state = initialize_paper_jordan_state([3, 1, 2, 9])
        pair_2 = state.pairs[2]
        pair_3 = state.pairs[3]
        upper_dummy = state.pairs[UPPER_DUMMY_PAIR_ID]
        lower_dummy = state.pairs[LOWER_DUMMY_PAIR_ID]

        self.assertEqual((pair_2.first_point_id, pair_2.second_point_id), (1, 2))
        self.assertEqual((pair_3.first_point_id, pair_3.second_point_id), (2, 3))
        self.assertEqual(pair_2.family, UPPER)
        self.assertEqual(pair_3.family, LOWER)
        self.assertEqual(pair_2.parent_pair_id, UPPER_DUMMY_PAIR_ID)
        self.assertEqual(pair_3.parent_pair_id, LOWER_DUMMY_PAIR_ID)
        self.assertEqual(state.pair_by_end_index, {2: 2, 3: 3})
        self.assertEqual(len(upper_dummy.child_sibling_list_ids), 1)
        self.assertEqual(len(lower_dummy.child_sibling_list_ids), 1)
        self.assertEqual(
            state.sibling_backend.get_list(pair_2.sibling_list_id).pair_ids,
            [2],
        )
        self.assertEqual(
            state.sibling_backend.get_list(pair_3.sibling_list_id).pair_ids,
            [3],
        )

    def test_initialization_records_stable_trace_and_metrics(self):
        state = initialize_paper_jordan_state([1, 3, 2])

        self.assertEqual(
            [event["step"] for event in state.trace],
            ["initialize_partial_order", "initialize_pair_families"],
        )
        self.assertEqual(state.metrics["trace_event_count"], 2)
        self.assertEqual(state.metrics["predecessor_accesses"], 0)
        self.assertEqual(state.metrics["successor_accesses"], 0)
        self.assertEqual(state.metrics["boundary_pair_checks"], 0)

    def test_initialization_rejects_short_or_duplicate_prefix(self):
        for values in ([], [1], [1, 2]):
            with self.subTest(values=values):
                with self.assertRaises(ValueError):
                    initialize_paper_jordan_state(values)

        with self.assertRaises(ValueError):
            initialize_paper_jordan_state([1, 1, 2])


class PaperJordanBoundarySelectionTests(unittest.TestCase):
    def test_same_family_selection_uses_original_incident_pairs(self):
        state = initialize_paper_jordan_state([1, 2, 3, 4, 5])

        self.assertEqual(select_processed_same_family_pair(state, 1, 4), 2)
        self.assertEqual(select_processed_same_family_pair(state, 2, 4), 2)

        self._add_processed_point_four(state, anchor_point_id=3, after=True)
        self.assertEqual(select_processed_same_family_pair(state, 2, 5), 3)
        self.assertEqual(select_processed_same_family_pair(state, 3, 5), 3)

    def test_same_family_selection_rejects_z1_for_lower_family(self):
        state = initialize_paper_jordan_state([1, 2, 3, 4, 5])
        self._add_processed_point_four(state, anchor_point_id=3, after=True)

        with self.assertRaises(ValueError):
            select_processed_same_family_pair(state, 1, 5)

    def test_step1_uses_upper_dummy_at_negative_infinity(self):
        state = initialize_paper_jordan_state([2, 3, 1, 4])

        result = step1_select_predecessor_boundary(state, 4)

        self.assertEqual(
            result,
            BoundarySelection(None, UPPER_DUMMY_PAIR_ID, True, False),
        )
        self.assertEqual(state.metrics["predecessor_accesses"], 1)
        self.assertEqual(state.metrics["boundary_pair_checks"], 0)

    def test_step2_uses_upper_dummy_at_positive_infinity(self):
        state = initialize_paper_jordan_state([1, 2, 3, 4])

        result = step2_select_successor_boundary(state, 4)

        self.assertEqual(
            result,
            BoundarySelection(None, UPPER_DUMMY_PAIR_ID, True, False),
        )
        self.assertEqual(state.metrics["successor_accesses"], 1)
        self.assertEqual(state.metrics["boundary_pair_checks"], 0)

    def test_even_step_selects_same_upper_pair_on_both_sides(self):
        state = initialize_paper_jordan_state([1, 4, 2, 3])

        left = step1_select_predecessor_boundary(state, 4)
        right = step2_select_successor_boundary(state, 4)

        self.assertEqual(left, BoundarySelection(1, 2, False, False))
        self.assertEqual(right, BoundarySelection(2, 2, False, False))
        self.assertEqual(state.metrics["boundary_pair_checks"], 2)

    def test_even_boundaries_cover_all_four_point_permutations(self):
        for values in itertools.permutations([1, 2, 3, 4]):
            with self.subTest(values=values):
                state = initialize_paper_jordan_state(values)
                left = step1_select_predecessor_boundary(state, 4)
                right = step2_select_successor_boundary(state, 4)

                self.assertIn(left.pair_id, {2, UPPER_DUMMY_PAIR_ID})
                self.assertIn(right.pair_id, {2, UPPER_DUMMY_PAIR_ID})
                self.assertFalse(left.adjusted_for_z1)
                self.assertFalse(right.adjusted_for_z1)

    def test_odd_step1_skips_z1_and_selects_lower_pair(self):
        state = initialize_paper_jordan_state([3, 2, 1, 4, 5])
        self._add_processed_point_four(state, anchor_point_id=1, after=True)

        result = step1_select_predecessor_boundary(state, 5)

        self.assertEqual(result, BoundarySelection(2, 3, False, True))
        self.assertEqual(state.metrics["predecessor_accesses"], 2)
        self.assertEqual(state.metrics["z1_anchor_adjustments"], 1)

    def test_odd_step2_skips_z1_and_selects_lower_pair(self):
        state = initialize_paper_jordan_state([2, 3, 4, 1, 5])
        self._add_processed_point_four(state, anchor_point_id=1, after=False)

        result = step2_select_successor_boundary(state, 5)

        self.assertEqual(result, BoundarySelection(2, 3, False, True))
        self.assertEqual(state.metrics["successor_accesses"], 2)
        self.assertEqual(state.metrics["z1_anchor_adjustments"], 1)

    def test_odd_step1_can_adjust_from_z1_to_lower_dummy(self):
        state = initialize_paper_jordan_state([1, 3, 4, 2, 5])
        self._add_processed_point_four(state, anchor_point_id=1, after=True)

        result = step1_select_predecessor_boundary(state, 5)

        self.assertEqual(
            result,
            BoundarySelection(None, LOWER_DUMMY_PAIR_ID, True, True),
        )

    def test_odd_step2_can_adjust_from_z1_to_lower_dummy(self):
        state = initialize_paper_jordan_state([4, 2, 1, 3, 5])
        self._add_processed_point_four(state, anchor_point_id=1, after=False)

        result = step2_select_successor_boundary(state, 5)

        self.assertEqual(
            result,
            BoundarySelection(None, LOWER_DUMMY_PAIR_ID, True, True),
        )

    def test_step1_and_step2_record_two_events_each(self):
        state = initialize_paper_jordan_state([1, 4, 2, 3])

        step1_select_predecessor_boundary(state, 4)
        step2_select_successor_boundary(state, 4)

        self.assertEqual(
            [event["step"] for event in state.trace[-4:]],
            [
                "step1_find_predecessor",
                "step1_select_boundary_pair",
                "step2_find_successor",
                "step2_select_boundary_pair",
            ],
        )
        self.assertEqual(state.metrics["trace_event_count"], len(state.trace))

    def test_boundary_selection_requires_the_next_iteration(self):
        state = initialize_paper_jordan_state([1, 2, 3, 4, 5])

        with self.assertRaises(ValueError):
            step1_select_predecessor_boundary(state, 5)
        with self.assertRaises(ValueError):
            step2_select_successor_boundary(state, 5)

    def _add_processed_point_four(self, state, anchor_point_id, after):
        point_4 = state.point(4)
        if after:
            state.partial_order.insert_after(anchor_point_id, point_4)
        else:
            state.partial_order.insert_before(anchor_point_id, point_4)

        pair_4 = PairRecord(4, 4, 3, 4, UPPER)
        state.sibling_backend.register_pair(pair_4)
        state.sibling_backend.make_list(pair_4.pair_id, state.upper_dummy_pair_id)
        state.pairs[pair_4.pair_id] = pair_4
        state.pair_by_end_index[pair_4.end_index] = pair_4.pair_id
        state.processed_count = 4

        self.assertTrue(state.partial_order.validate_links())
        self.assertTrue(state.sibling_backend.validate_invariants())


if __name__ == "__main__":
    unittest.main()
