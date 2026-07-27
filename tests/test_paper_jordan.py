"""论文 Jordan 算法初始化与 Step 1/2/3 的聚焦测试。"""

import itertools
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from paper_jordan import (  # noqa: E402
    BOUNDARY_INSERTION,
    DECREASING,
    INCREASING,
    LOWER_DUMMY_PAIR_ID,
    SINGLETON_LIST,
    UPPER_DUMMY_PAIR_ID,
    BoundarySelection,
    Step3CResult,
    initialize_paper_jordan_state,
    pair_encloses_point,
    pair_family_for_end_index,
    select_processed_same_family_pair,
    step1_select_predecessor_boundary,
    step2_select_successor_boundary,
    step3a_decreasing,
    step3a_increasing,
    step3b_decreasing,
    step3b_increasing,
    step3c_decreasing,
    step3c_increasing,
)
from oracle import oracle  # noqa: E402
from sibling_list_backend import (  # noqa: E402
    AFTER,
    BEFORE,
    LEFT,
    LOWER,
    RIGHT,
    UPPER,
    PairRecord,
)


class _AppendOnlyTrace(list):
    """允许追加，但在阶段校验意外扫描 trace 时立即失败。"""

    def __iter__(self):
        raise AssertionError("stage validation must not scan the trace")


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
        self.assertEqual(state.metrics["split_items_copied"], 0)
        self.assertEqual(state.metrics["split_items_transferred"], 0)
        self.assertEqual(state.metrics["z1_boundary_adjustments"], 0)
        self.assertEqual(state.metrics["z1_output_anchor_adjustments"], 0)
        self.assertNotIn("split_items_moved", state.metrics)
        self.assertNotIn("z1_anchor_adjustments", state.metrics)
        self.assertEqual(state.stage_results, {})

    def test_initialization_rejects_short_or_duplicate_prefix(self):
        for values in ([], [1], [1, 2]):
            with self.subTest(values=values):
                with self.assertRaises(ValueError):
                    initialize_paper_jordan_state(values)

        with self.assertRaises(ValueError):
            initialize_paper_jordan_state([1, 1, 2])


class PaperJordanBoundarySelectionTests(unittest.TestCase):
    def test_boundary_stage_cannot_be_recorded_twice(self):
        state = initialize_paper_jordan_state([2, 3, 1, 4])
        first = step1_select_predecessor_boundary(state, 4)
        trace_size = len(state.trace)

        with self.assertRaises(RuntimeError):
            step1_select_predecessor_boundary(state, 4)

        self.assertEqual(len(state.trace), trace_size)
        self.assertIs(
            state.stage_results[4]["step1_select_boundary_pair"],
            first,
        )

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

                self.assertEqual(
                    left,
                    self._expected_boundary(values, iteration=4, direction=-1),
                )
                self.assertEqual(
                    right,
                    self._expected_boundary(values, iteration=4, direction=1),
                )

    def test_odd_boundaries_cover_all_five_point_permutations(self):
        for values in itertools.permutations([1, 2, 3, 4, 5]):
            with self.subTest(values=values):
                state = initialize_paper_jordan_state(values)
                self._add_processed_point_four_in_value_order(state)

                left = step1_select_predecessor_boundary(state, 5)
                right = step2_select_successor_boundary(state, 5)

                self.assertEqual(
                    left,
                    self._expected_boundary(values, iteration=5, direction=-1),
                )
                self.assertEqual(
                    right,
                    self._expected_boundary(values, iteration=5, direction=1),
                )

    def test_finite_boundary_rejects_inconsistent_live_ownership(self):
        def change_parent(state):
            state.pairs[2].parent_pair_id = LOWER_DUMMY_PAIR_ID

        def change_list_id(state):
            sibling_list = state.sibling_backend.get_list(
                state.pairs[2].sibling_list_id
            )
            sibling_list.list_id += 100

        for name, mutate in (
            ("parent mapping", change_parent),
            ("list id mapping", change_list_id),
        ):
            with self.subTest(name=name):
                state = initialize_paper_jordan_state([1, 4, 2, 3])
                mutate(state)

                with self.assertRaises(RuntimeError):
                    step1_select_predecessor_boundary(state, 4)

    def test_dummy_boundary_rejects_wrong_family_identity_or_ownership(self):
        def use_lower_dummy_id(state):
            state.upper_dummy_pair_id = LOWER_DUMMY_PAIR_ID

        def replace_state_dummy(state):
            state.pairs[UPPER_DUMMY_PAIR_ID] = PairRecord(
                UPPER_DUMMY_PAIR_ID,
                None,
                None,
                None,
                UPPER,
                is_dummy=True,
            )

        def add_ordinary_ownership(state):
            state.pairs[UPPER_DUMMY_PAIR_ID].parent_pair_id = LOWER_DUMMY_PAIR_ID

        for name, mutate in (
            ("wrong family", use_lower_dummy_id),
            ("backend identity", replace_state_dummy),
            ("ordinary ownership", add_ordinary_ownership),
        ):
            with self.subTest(name=name):
                state = initialize_paper_jordan_state([2, 3, 1, 4])
                mutate(state)

                with self.assertRaises(RuntimeError):
                    step1_select_predecessor_boundary(state, 4)

    def test_odd_step1_skips_z1_and_selects_lower_pair(self):
        state = initialize_paper_jordan_state([3, 2, 1, 4, 5])
        self._add_processed_point_four(state, anchor_point_id=1, after=True)

        result = step1_select_predecessor_boundary(state, 5)

        self.assertEqual(result, BoundarySelection(2, 3, False, True))
        self.assertEqual(state.metrics["predecessor_accesses"], 2)
        self.assertEqual(state.metrics["z1_boundary_adjustments"], 1)

    def test_odd_step2_skips_z1_and_selects_lower_pair(self):
        state = initialize_paper_jordan_state([2, 3, 4, 1, 5])
        self._add_processed_point_four(state, anchor_point_id=1, after=False)

        result = step2_select_successor_boundary(state, 5)

        self.assertEqual(result, BoundarySelection(2, 3, False, True))
        self.assertEqual(state.metrics["successor_accesses"], 2)
        self.assertEqual(state.metrics["z1_boundary_adjustments"], 1)

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

    def _add_processed_point_four_in_value_order(self, state):
        point_4 = state.point(4)
        ordered_ids = state.partial_order.to_point_ids()

        for anchor_point_id in ordered_ids:
            if point_4.value < state.point_value(anchor_point_id):
                state.partial_order.insert_before(anchor_point_id, point_4)
                break
        else:
            state.partial_order.insert_after(ordered_ids[-1], point_4)

        pair_4 = PairRecord(4, 4, 3, 4, UPPER)
        state.sibling_backend.register_pair(pair_4)
        state.sibling_backend.make_list(pair_4.pair_id, state.upper_dummy_pair_id)
        state.pairs[pair_4.pair_id] = pair_4
        state.pair_by_end_index[pair_4.end_index] = pair_4.pair_id
        state.processed_count = 4

        self.assertTrue(state.partial_order.validate_links())
        self.assertTrue(state.sibling_backend.validate_invariants())

    def _expected_boundary(self, values, iteration, direction):
        processed_ids = range(1, iteration)
        ordered_ids = sorted(processed_ids, key=lambda point_id: values[point_id - 1])
        previous_position = ordered_ids.index(iteration - 1)
        neighbor_position = previous_position + direction
        adjusted_for_z1 = False

        if 0 <= neighbor_position < len(ordered_ids):
            neighbor_point_id = ordered_ids[neighbor_position]
        else:
            neighbor_point_id = None

        if iteration % 2 == 1 and neighbor_point_id == 1:
            neighbor_position += direction
            adjusted_for_z1 = True
            if 0 <= neighbor_position < len(ordered_ids):
                neighbor_point_id = ordered_ids[neighbor_position]
            else:
                neighbor_point_id = None

        if neighbor_point_id is None:
            dummy_pair_id = (
                UPPER_DUMMY_PAIR_ID if iteration % 2 == 0 else LOWER_DUMMY_PAIR_ID
            )
            return BoundarySelection(
                None,
                dummy_pair_id,
                True,
                adjusted_for_z1,
            )

        if neighbor_point_id >= 2 and neighbor_point_id % 2 == iteration % 2:
            pair_id = neighbor_point_id
        else:
            pair_id = neighbor_point_id + 1

        return BoundarySelection(
            neighbor_point_id,
            pair_id,
            False,
            adjusted_for_z1,
        )


class PaperJordanStep3Tests(unittest.TestCase):
    def test_enclosure_uses_strict_geometry_and_dummy_fallback(self):
        state = initialize_paper_jordan_state([1, 4, 2, 3])

        self.assertTrue(pair_encloses_point(state, 2, 3))
        self.assertFalse(pair_encloses_point(state, 2, 1))
        self.assertTrue(
            pair_encloses_point(state, UPPER_DUMMY_PAIR_ID, 3)
        )

    def test_increasing_step3a_creates_singleton_list(self):
        state = initialize_paper_jordan_state([2, 3, 1, 4])
        left = step1_select_predecessor_boundary(state, 4)

        result = step3a_increasing(state, 4, left)
        pair = state.pairs[result.pair_id]

        self.assertEqual(result.orientation, INCREASING)
        self.assertEqual(result.insertion_mode, SINGLETON_LIST)
        self.assertEqual(result.parent_pair_id, UPPER_DUMMY_PAIR_ID)
        self.assertEqual((pair.first_point_id, pair.second_point_id), (3, 4))
        self.assertEqual(
            state.sibling_backend.get_list(result.sibling_list_id).pair_ids,
            [4],
        )
        self._assert_step3c_not_run(state, 4)

    def test_increasing_step3a_inserts_after_left_boundary(self):
        state = initialize_paper_jordan_state([1, 2, 3, 4])
        left = step1_select_predecessor_boundary(state, 4)
        pair_2_list_id = state.pairs[2].sibling_list_id

        result = step3a_increasing(state, 4, left)

        self.assertEqual(result.insertion_mode, BOUNDARY_INSERTION)
        self.assertEqual(result.sibling_list_id, pair_2_list_id)
        self.assertEqual(result.parent_pair_id, UPPER_DUMMY_PAIR_ID)
        self.assertEqual(
            state.sibling_backend.get_list(pair_2_list_id).pair_ids,
            [2, 4],
        )
        self._assert_step3c_not_run(state, 4)

    def test_decreasing_step3a_creates_singleton_list(self):
        state = initialize_paper_jordan_state([3, 2, 4, 1])
        right = step2_select_successor_boundary(state, 4)

        result = step3a_decreasing(state, 4, right)

        self.assertEqual(result.orientation, DECREASING)
        self.assertEqual(result.insertion_mode, SINGLETON_LIST)
        self.assertEqual(result.parent_pair_id, UPPER_DUMMY_PAIR_ID)
        self.assertEqual(
            state.sibling_backend.get_list(result.sibling_list_id).pair_ids,
            [4],
        )
        self._assert_step3c_not_run(state, 4)

    def test_decreasing_step3a_inserts_before_right_boundary(self):
        state = initialize_paper_jordan_state([4, 3, 2, 1])
        right = step2_select_successor_boundary(state, 4)
        pair_2_list_id = state.pairs[2].sibling_list_id

        result = step3a_decreasing(state, 4, right)

        self.assertEqual(result.insertion_mode, BOUNDARY_INSERTION)
        self.assertEqual(result.sibling_list_id, pair_2_list_id)
        self.assertEqual(
            state.sibling_backend.get_list(pair_2_list_id).pair_ids,
            [4, 2],
        )
        self._assert_step3c_not_run(state, 4)

    def test_step3a_wrong_orientation_does_not_register_pair(self):
        state = initialize_paper_jordan_state([1, 2, 3, 4])
        right = step2_select_successor_boundary(state, 4)

        with self.assertRaises(ValueError):
            step3a_decreasing(state, 4, right)

        self.assertNotIn(4, state.pairs)
        self.assertNotIn(4, state.pair_by_end_index)
        with self.assertRaises(KeyError):
            state.sibling_backend.get_pair(4)

    def test_step3a_rejects_boundary_from_wrong_side(self):
        state = initialize_paper_jordan_state([2, 3, 1, 4])
        step1_select_predecessor_boundary(state, 4)
        right = step2_select_successor_boundary(state, 4)

        with self.assertRaises(RuntimeError):
            step3a_increasing(state, 4, right)

        self.assertNotIn(4, state.pairs)
        with self.assertRaises(KeyError):
            state.sibling_backend.get_pair(4)

    def test_step3a_boundary_failure_rolls_back_pair_registration(self):
        state = initialize_paper_jordan_state([1, 2, 3, 4])
        left = step1_select_predecessor_boundary(state, 4)
        pair_2_list = state.sibling_backend.get_list(state.pairs[2].sibling_list_id)
        pair_2_list.pair_ids.append(999)

        with self.assertRaises(ValueError):
            step3a_increasing(state, 4, left)

        self.assertNotIn(4, state.pairs)
        self.assertNotIn(4, state.pair_by_end_index)
        with self.assertRaises(KeyError):
            state.sibling_backend.get_pair(4)

    def test_increasing_step3b_skips_when_right_boundary_encloses(self):
        state = initialize_paper_jordan_state([1, 2, 3, 4])
        left = step1_select_predecessor_boundary(state, 4)
        right = step2_select_successor_boundary(state, 4)
        new_pair = step3a_increasing(state, 4, left)

        result = step3b_increasing(state, 4, new_pair.pair_id, right)

        self.assertFalse(result.performed)
        self.assertIsNone(result.acquired_side)
        self.assertEqual(state.pairs[4].child_sibling_list_ids, [])
        self.assertEqual(state.metrics["sibling_list_splits"], 0)
        self.assertEqual(state.metrics["split_items_copied"], 0)
        self.assertEqual(state.metrics["split_items_transferred"], 0)
        self._assert_step3c_not_run(state, 4)

    def test_step3b_rejects_boundary_from_wrong_side(self):
        state = initialize_paper_jordan_state([2, 3, 1, 4])
        left = step1_select_predecessor_boundary(state, 4)
        step2_select_successor_boundary(state, 4)
        new_pair = step3a_increasing(state, 4, left)

        with self.assertRaises(RuntimeError):
            step3b_increasing(state, 4, new_pair.pair_id, left)

        self.assertEqual(state.pairs[4].child_sibling_list_ids, [])
        self.assertEqual(state.pairs[2].parent_pair_id, UPPER_DUMMY_PAIR_ID)

    def test_decreasing_step3b_skips_when_left_boundary_encloses(self):
        state = initialize_paper_jordan_state([4, 3, 2, 1])
        left = step1_select_predecessor_boundary(state, 4)
        right = step2_select_successor_boundary(state, 4)
        new_pair = step3a_decreasing(state, 4, right)

        result = step3b_decreasing(state, 4, new_pair.pair_id, left)

        self.assertFalse(result.performed)
        self.assertEqual(state.pairs[4].child_sibling_list_ids, [])
        self.assertEqual(state.metrics["split_items_copied"], 0)
        self.assertEqual(state.metrics["split_items_transferred"], 0)
        self._assert_step3c_not_run(state, 4)

    def test_increasing_step3b_acquires_left_one_sided_split(self):
        state = initialize_paper_jordan_state([2, 3, 1, 4])
        left = step1_select_predecessor_boundary(state, 4)
        right = step2_select_successor_boundary(state, 4)
        new_pair = step3a_increasing(state, 4, left)

        result = step3b_increasing(state, 4, new_pair.pair_id, right)

        self.assertTrue(result.performed)
        self.assertEqual(result.acquired_side, LEFT)
        self.assertEqual(
            state.sibling_backend.get_list(result.left_list_id).pair_ids,
            [2],
        )
        self.assertIsNone(result.right_list_id)
        self.assertEqual(state.pairs[2].parent_pair_id, 4)
        self.assertEqual(state.pairs[4].child_sibling_list_ids, [result.left_list_id])
        self.assertEqual(state.metrics["split_items_copied"], 1)
        self.assertEqual(state.metrics["split_items_transferred"], 1)
        self.assertTrue(state.sibling_backend.validate_invariants())
        self._assert_step3c_not_run(state, 4)

    def test_decreasing_step3b_acquires_right_one_sided_split(self):
        state = initialize_paper_jordan_state([3, 2, 4, 1])
        left = step1_select_predecessor_boundary(state, 4)
        right = step2_select_successor_boundary(state, 4)
        new_pair = step3a_decreasing(state, 4, right)

        result = step3b_decreasing(state, 4, new_pair.pair_id, left)

        self.assertTrue(result.performed)
        self.assertEqual(result.acquired_side, RIGHT)
        self.assertIsNone(result.left_list_id)
        self.assertEqual(
            state.sibling_backend.get_list(result.right_list_id).pair_ids,
            [2],
        )
        self.assertEqual(state.pairs[2].parent_pair_id, 4)
        self.assertTrue(state.sibling_backend.validate_invariants())
        self._assert_step3c_not_run(state, 4)

    def test_increasing_step3b_preserves_right_side_of_two_sided_split(self):
        state = self._prepare_seven_point_state([1, 2, 3, 4, 6, 7, 0, 5])
        left = step1_select_predecessor_boundary(state, 8)
        right = step2_select_successor_boundary(state, 8)
        new_pair = step3a_increasing(state, 8, left)

        result = step3b_increasing(state, 8, new_pair.pair_id, right)

        self.assertEqual(
            state.sibling_backend.get_list(result.left_list_id).pair_ids,
            [2, 4],
        )
        self.assertEqual(
            state.sibling_backend.get_list(result.right_list_id).pair_ids,
            [6],
        )
        self.assertEqual(state.pairs[2].parent_pair_id, 8)
        self.assertEqual(state.pairs[4].parent_pair_id, 8)
        self.assertEqual(state.pairs[6].parent_pair_id, UPPER_DUMMY_PAIR_ID)
        self.assertEqual(state.metrics["split_items_scanned"], 3)
        self.assertEqual(state.metrics["split_items_copied"], 3)
        self.assertEqual(state.metrics["split_items_transferred"], 2)
        self.assertTrue(state.sibling_backend.validate_invariants())
        self._assert_step3c_not_run(state, 8)

    def test_decreasing_step3b_preserves_left_side_of_two_sided_split(self):
        state = self._prepare_seven_point_state([6, 5, 4, 3, 1, 0, 7, 2])
        left = step1_select_predecessor_boundary(state, 8)
        right = step2_select_successor_boundary(state, 8)
        new_pair = step3a_decreasing(state, 8, right)

        result = step3b_decreasing(state, 8, new_pair.pair_id, left)

        self.assertEqual(
            state.sibling_backend.get_list(result.left_list_id).pair_ids,
            [6],
        )
        self.assertEqual(
            state.sibling_backend.get_list(result.right_list_id).pair_ids,
            [4, 2],
        )
        self.assertEqual(state.pairs[6].parent_pair_id, UPPER_DUMMY_PAIR_ID)
        self.assertEqual(state.pairs[4].parent_pair_id, 8)
        self.assertEqual(state.pairs[2].parent_pair_id, 8)
        self.assertEqual(result.acquired_side, RIGHT)
        self.assertEqual(state.metrics["split_items_scanned"], 3)
        self.assertEqual(state.metrics["split_items_copied"], 3)
        self.assertEqual(state.metrics["split_items_transferred"], 2)
        self.assertTrue(state.sibling_backend.validate_invariants())
        self._assert_step3c_not_run(state, 8)

    def test_repeated_step3_stages_leave_state_unchanged(self):
        state = initialize_paper_jordan_state([2, 3, 1, 4])
        left = step1_select_predecessor_boundary(state, 4)
        right = step2_select_successor_boundary(state, 4)
        new_pair = step3a_increasing(state, 4, left)
        after_step3a = self._state_snapshot(state)

        with self.assertRaises(RuntimeError):
            step3a_increasing(state, 4, left)

        self.assertEqual(self._state_snapshot(state), after_step3a)

        step3b_increasing(state, 4, new_pair.pair_id, right)
        after_step3b = self._state_snapshot(state)

        with self.assertRaises(RuntimeError):
            step3b_increasing(state, 4, new_pair.pair_id, right)

        self.assertEqual(self._state_snapshot(state), after_step3b)
        self.assertTrue(state.sibling_backend.validate_invariants())

    def test_step3_stage_validation_does_not_scan_trace(self):
        state = initialize_paper_jordan_state([2, 3, 1, 4])
        left = step1_select_predecessor_boundary(state, 4)
        right = step2_select_successor_boundary(state, 4)
        state.trace = _AppendOnlyTrace(state.trace)

        new_pair = step3a_increasing(state, 4, left)
        result = step3b_increasing(state, 4, new_pair.pair_id, right)
        output = step3c_increasing(state, 4, new_pair.pair_id)

        self.assertTrue(result.performed)
        self.assertIs(
            state.stage_results[4]["step3a_insert_pair"],
            new_pair,
        )
        self.assertIs(
            state.stage_results[4]["step3b_split_sibling_list"],
            result,
        )
        self.assertIs(
            state.stage_results[4]["step3c_insert_output_point"],
            output,
        )

    def test_step3c_no_child_uses_previous_point_in_both_directions(self):
        cases = [
            ([1, 4, 2, 3], INCREASING, AFTER),
            ([4, 3, 2, 1], DECREASING, BEFORE),
        ]

        for values, orientation, insertion_side in cases:
            with self.subTest(values=values):
                state = initialize_paper_jordan_state(values)
                left = step1_select_predecessor_boundary(state, 4)
                right = step2_select_successor_boundary(state, 4)
                if orientation == INCREASING:
                    new_pair = step3a_increasing(state, 4, left)
                    step3b_increasing(state, 4, new_pair.pair_id, right)
                    result = step3c_increasing(state, 4, new_pair.pair_id)
                else:
                    new_pair = step3a_decreasing(state, 4, right)
                    step3b_decreasing(state, 4, new_pair.pair_id, left)
                    result = step3c_decreasing(state, 4, new_pair.pair_id)

                self.assertEqual(result.child_pair_id, None)
                self.assertEqual(result.base_anchor_point_id, 3)
                self.assertEqual(result.output_anchor_point_id, 3)
                self.assertEqual(result.insertion_side, insertion_side)
                self.assertFalse(result.adjusted_for_z1)
                self.assertEqual(state.partial_order.to_list(), sorted(values))
                self.assertEqual(state.processed_count, 4)
                self.assertEqual(state.metrics["output_insertions"], 1)
                self.assertTrue(state.partial_order.validate_links())

    def test_step3c_uses_geometric_endpoint_for_all_orientation_combinations(self):
        cases = [
            ([2, 3, 1, 4], INCREASING, 2),
            ([3, 2, 1, 4], INCREASING, 1),
            ([2, 3, 4, 1], DECREASING, 1),
            ([3, 2, 4, 1], DECREASING, 2),
        ]

        for values, orientation, expected_anchor in cases:
            with self.subTest(values=values):
                state = initialize_paper_jordan_state(values)
                left = step1_select_predecessor_boundary(state, 4)
                right = step2_select_successor_boundary(state, 4)
                if orientation == INCREASING:
                    new_pair = step3a_increasing(state, 4, left)
                    step3b_increasing(state, 4, new_pair.pair_id, right)
                    result = step3c_increasing(state, 4, new_pair.pair_id)
                else:
                    new_pair = step3a_decreasing(state, 4, right)
                    step3b_decreasing(state, 4, new_pair.pair_id, left)
                    result = step3c_decreasing(state, 4, new_pair.pair_id)

                self.assertEqual(result.child_pair_id, 2)
                self.assertEqual(result.base_anchor_point_id, expected_anchor)
                self.assertEqual(result.output_anchor_point_id, expected_anchor)
                self.assertFalse(result.adjusted_for_z1)
                self.assertEqual(state.partial_order.to_list(), sorted(values))
                self.assertTrue(state.sibling_backend.validate_invariants())

    def test_step3c_applies_odd_z1_adjustment_in_both_directions(self):
        cases = [
            ([6, 5, 4, 3, 1, 0, 7], INCREASING, 2),
            ([1, 2, 3, 4, 6, 7, 0], DECREASING, 2),
        ]

        for values, orientation, expected_base_anchor in cases:
            with self.subTest(values=values):
                state = self._prepare_six_point_state(values)
                left = step1_select_predecessor_boundary(state, 7)
                right = step2_select_successor_boundary(state, 7)
                before_adjustments = state.metrics["z1_output_anchor_adjustments"]
                if orientation == INCREASING:
                    new_pair = step3a_increasing(state, 7, left)
                    step3b_increasing(state, 7, new_pair.pair_id, right)
                    result = step3c_increasing(state, 7, new_pair.pair_id)
                else:
                    new_pair = step3a_decreasing(state, 7, right)
                    step3b_decreasing(state, 7, new_pair.pair_id, left)
                    result = step3c_decreasing(state, 7, new_pair.pair_id)

                self.assertEqual(result.base_anchor_point_id, expected_base_anchor)
                self.assertEqual(result.output_anchor_point_id, 1)
                self.assertTrue(result.adjusted_for_z1)
                self.assertEqual(
                    state.metrics["z1_output_anchor_adjustments"],
                    before_adjustments + 1,
                )
                self.assertEqual(state.partial_order.to_list(), sorted(values))
                self.assertEqual(state.processed_count, 7)
                self.assertTrue(state.partial_order.validate_links())
                self.assertTrue(state.sibling_backend.validate_invariants())

    def test_step3c_does_not_adjust_for_odd_z1_outside_anchor_interval(self):
        cases = [
            [1, 2, 3, 4, 5],
            [5, 4, 3, 2, 1],
        ]

        for values in cases:
            with self.subTest(values=values):
                state = initialize_paper_jordan_state(values)
                self._complete_iteration(state, 4)
                before_adjustments = state.metrics["z1_output_anchor_adjustments"]

                result = self._complete_iteration(state, 5)

                self.assertFalse(result.adjusted_for_z1)
                self.assertNotEqual(result.output_anchor_point_id, 1)
                self.assertEqual(
                    state.metrics["z1_output_anchor_adjustments"],
                    before_adjustments,
                )
                self.assertEqual(state.partial_order.to_list(), sorted(values))
                self.assertEqual(state.processed_count, 5)

    def test_step3c_requires_step3b_without_changing_state(self):
        state = initialize_paper_jordan_state([1, 2, 3, 4])
        left = step1_select_predecessor_boundary(state, 4)
        step2_select_successor_boundary(state, 4)
        new_pair = step3a_increasing(state, 4, left)
        before = self._state_snapshot(state)

        with self.assertRaises(RuntimeError):
            step3c_increasing(state, 4, new_pair.pair_id)

        self.assertEqual(self._state_snapshot(state), before)

    def test_step3c_rejects_wrong_child_owner_without_changing_state(self):
        state = initialize_paper_jordan_state([2, 3, 1, 4])
        left = step1_select_predecessor_boundary(state, 4)
        right = step2_select_successor_boundary(state, 4)
        new_pair = step3a_increasing(state, 4, left)
        step3b_increasing(state, 4, new_pair.pair_id, right)
        child_list_id = state.pairs[4].child_sibling_list_ids[0]
        child_list = state.sibling_backend.get_list(child_list_id)
        child_list.owner_parent_pair_id = UPPER_DUMMY_PAIR_ID
        before = self._state_snapshot(state)

        with self.assertRaises(RuntimeError):
            step3c_increasing(state, 4, new_pair.pair_id)

        self.assertEqual(self._state_snapshot(state), before)

    def test_repeated_step3c_leaves_completed_state_unchanged(self):
        state = initialize_paper_jordan_state([2, 3, 1, 4])
        left = step1_select_predecessor_boundary(state, 4)
        right = step2_select_successor_boundary(state, 4)
        new_pair = step3a_increasing(state, 4, left)
        step3b_increasing(state, 4, new_pair.pair_id, right)
        first = step3c_increasing(state, 4, new_pair.pair_id)
        completed = self._state_snapshot(state)

        with self.assertRaises(RuntimeError):
            step3c_increasing(state, 4, new_pair.pair_id)

        self.assertEqual(self._state_snapshot(state), completed)
        self.assertIsInstance(first, Step3CResult)
        self.assertIs(
            state.stage_results[4]["step3c_insert_output_point"],
            first,
        )

    def test_step3c_records_stable_trace_fields(self):
        state = initialize_paper_jordan_state([3, 2, 1, 4])
        left = step1_select_predecessor_boundary(state, 4)
        right = step2_select_successor_boundary(state, 4)
        new_pair = step3a_increasing(state, 4, left)
        step3b_increasing(state, 4, new_pair.pair_id, right)

        result = step3c_increasing(state, 4, new_pair.pair_id)
        event = state.trace[-1]

        self.assertEqual(event["step"], "step3c_insert_output_point")
        self.assertEqual(event["iteration"], 4)
        self.assertEqual(event["orientation"], INCREASING)
        self.assertEqual(event["pair_id"], 4)
        self.assertEqual(event["child_pair_id"], 2)
        self.assertEqual(event["base_anchor_point_id"], 1)
        self.assertEqual(event["output_anchor_point_id"], 1)
        self.assertEqual(event["insertion_side"], AFTER)
        self.assertFalse(event["adjusted_for_z1"])
        self.assertEqual(event["processed_count"], 4)
        self.assertEqual(result.output_anchor_point_id, 1)

    def test_step3abc_completes_every_oracle_valid_four_point_permutation(self):
        valid_count = 0
        for values in itertools.permutations([1, 2, 3, 4]):
            if not oracle(values)["valid"]:
                continue

            valid_count += 1
            with self.subTest(values=values):
                state = initialize_paper_jordan_state(values)
                result = self._complete_iteration(state, 4)

                self.assertIsInstance(result, Step3CResult)
                self.assertEqual(state.partial_order.to_list(), sorted(values))
                self.assertEqual(state.processed_count, 4)
                self.assertEqual(state.metrics["output_insertions"], 1)
                self.assertTrue(state.partial_order.validate_links())
                self.assertTrue(state.sibling_backend.validate_invariants())

        self.assertEqual(valid_count, 16)

    def test_step3ab_trace_stops_before_output_insertion(self):
        state = initialize_paper_jordan_state([2, 3, 1, 4])
        left = step1_select_predecessor_boundary(state, 4)
        right = step2_select_successor_boundary(state, 4)
        new_pair = step3a_increasing(state, 4, left)
        step3b_increasing(state, 4, new_pair.pair_id, right)

        steps = [event["step"] for event in state.trace]
        self.assertIn("step3a_insert_pair", steps)
        self.assertIn("step3b_split_sibling_list", steps)
        self.assertNotIn("step3c_insert_output_point", steps)
        self.assertEqual(state.metrics["output_insertions"], 0)

    def test_step3ab_succeeds_for_every_oracle_valid_four_point_permutation(self):
        valid_count = 0
        for values in itertools.permutations([1, 2, 3, 4]):
            if not oracle(values)["valid"]:
                continue

            valid_count += 1
            with self.subTest(values=values):
                state = initialize_paper_jordan_state(values)
                left = step1_select_predecessor_boundary(state, 4)
                right = step2_select_successor_boundary(state, 4)

                if values[2] < values[3]:
                    new_pair = step3a_increasing(state, 4, left)
                    step3b_increasing(state, 4, new_pair.pair_id, right)
                else:
                    new_pair = step3a_decreasing(state, 4, right)
                    step3b_decreasing(state, 4, new_pair.pair_id, left)

                self.assertTrue(state.sibling_backend.validate_invariants())
                self._assert_step3c_not_run(state, 4)

        self.assertEqual(valid_count, 16)

    def _prepare_seven_point_state(self, values):
        state = self._prepare_six_point_state(values)
        self._insert_point_in_value_order(state, 7)

        pair_7 = PairRecord(7, 7, 6, 7, LOWER)
        state.sibling_backend.register_pair(pair_7)
        state.sibling_backend.make_list(pair_7.pair_id, state.lower_dummy_pair_id)
        state.pairs[pair_7.pair_id] = pair_7
        state.pair_by_end_index[7] = pair_7.pair_id
        state.processed_count = 7

        self.assertEqual(
            state.partial_order.to_list(),
            sorted(values[:7]),
        )
        self.assertTrue(state.sibling_backend.validate_invariants())
        return state

    def _complete_iteration(self, state, iteration):
        left = step1_select_predecessor_boundary(state, iteration)
        right = step2_select_successor_boundary(state, iteration)
        if state.point_value(iteration - 1) < state.point_value(iteration):
            new_pair = step3a_increasing(state, iteration, left)
            step3b_increasing(state, iteration, new_pair.pair_id, right)
            return step3c_increasing(state, iteration, new_pair.pair_id)

        new_pair = step3a_decreasing(state, iteration, right)
        step3b_decreasing(state, iteration, new_pair.pair_id, left)
        return step3c_decreasing(state, iteration, new_pair.pair_id)

    def _prepare_six_point_state(self, values):
        state = initialize_paper_jordan_state(values)

        for paper_index in range(4, 7):
            self._insert_point_in_value_order(state, paper_index)

        upper_list_id = state.pairs[2].sibling_list_id
        lower_list_id = state.pairs[3].sibling_list_id
        for end_index in (4, 5, 6):
            pair = PairRecord(
                end_index,
                end_index,
                end_index - 1,
                end_index,
                UPPER if end_index % 2 == 0 else LOWER,
            )
            state.sibling_backend.register_pair(pair)
            target_list_id = upper_list_id if pair.family == UPPER else lower_list_id
            self._insert_pair_at_ordered_boundary(state, pair, target_list_id)
            state.pairs[pair.pair_id] = pair
            state.pair_by_end_index[end_index] = pair.pair_id

        state.processed_count = 6

        self.assertEqual(
            state.partial_order.to_list(),
            sorted(values[:6]),
        )
        self.assertTrue(state.sibling_backend.validate_invariants())
        return state

    def _insert_point_in_value_order(self, state, paper_index):
        point = state.point(paper_index)
        ordered_ids = state.partial_order.to_point_ids()
        for anchor_id in ordered_ids:
            if point.value < state.point_value(anchor_id):
                state.partial_order.insert_before(anchor_id, point)
                return
        state.partial_order.insert_after(ordered_ids[-1], point)

    def _insert_pair_at_ordered_boundary(self, state, pair, list_id):
        sibling_list = state.sibling_backend.get_list(list_id)
        first_pair = state.sibling_backend.get_pair(sibling_list.pair_ids[0])
        last_pair = state.sibling_backend.get_pair(sibling_list.pair_ids[-1])
        pair_key = min(
            state.point_value(pair.first_point_id),
            state.point_value(pair.second_point_id),
        )
        first_key = min(
            state.point_value(first_pair.first_point_id),
            state.point_value(first_pair.second_point_id),
        )
        last_key = min(
            state.point_value(last_pair.first_point_id),
            state.point_value(last_pair.second_point_id),
        )

        if pair_key < first_key:
            state.sibling_backend.insert_at_boundary(
                pair.pair_id,
                first_pair.pair_id,
                BEFORE,
            )
        elif last_key < pair_key:
            state.sibling_backend.insert_at_boundary(
                pair.pair_id,
                last_pair.pair_id,
                AFTER,
            )
        else:
            self.fail("test fixture pair is not at a sibling-list boundary")

    def _assert_step3c_not_run(self, state, iteration):
        self.assertEqual(state.processed_count, iteration - 1)
        self.assertNotIn(iteration, state.partial_order)
        self.assertEqual(state.metrics["output_insertions"], 0)

    @staticmethod
    def _state_snapshot(state):
        list_ids = set()
        pair_state = {}
        for pair_id, pair in state.pairs.items():
            pair_state[pair_id] = (
                pair.parent_pair_id,
                pair.sibling_list_id,
                tuple(pair.child_sibling_list_ids),
            )
            if pair.sibling_list_id is not None:
                list_ids.add(pair.sibling_list_id)
            list_ids.update(pair.child_sibling_list_ids)

        list_state = {}
        for list_id in list_ids:
            sibling_list = state.sibling_backend.get_list(list_id)
            list_state[list_id] = (
                sibling_list.owner_parent_pair_id,
                tuple(sibling_list.pair_ids),
            )

        return {
            "processed_count": state.processed_count,
            "partial_order": tuple(state.partial_order.to_point_ids()),
            "pair_by_end_index": dict(state.pair_by_end_index),
            "pairs": pair_state,
            "lists": list_state,
            "trace": tuple(tuple(sorted(event.items())) for event in state.trace),
            "metrics": dict(state.metrics),
            "stage_results": {
                iteration: dict(stages)
                for iteration, stages in state.stage_results.items()
            },
        }


if __name__ == "__main__":
    unittest.main()
