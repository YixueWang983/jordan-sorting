"""OrdinarySiblingListBackend 的聚焦单元测试。"""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from paper_execution_policy import (  # noqa: E402
    CHECKED_POLICY,
    MINIMAL_POLICY,
)
from sibling_list_backend import (  # noqa: E402
    AFTER,
    BEFORE,
    LEFT,
    LOWER,
    RIGHT,
    UPPER,
    OrdinarySiblingListBackend,
    PairRecord,
    SplitPlan,
    left_endpoint_id,
    right_endpoint_id,
)


UPPER_DUMMY_ID = -1
LOWER_DUMMY_ID = -2


class SiblingListBackendTests(unittest.TestCase):
    def setUp(self):
        self.values = {}
        self.backend = self.make_backend()

    def make_backend(self, execution_policy=CHECKED_POLICY):
        backend = OrdinarySiblingListBackend(
            self.values.__getitem__,
            execution_policy=execution_policy,
        )
        backend.register_pair(
            PairRecord(UPPER_DUMMY_ID, None, None, None, UPPER, is_dummy=True)
        )
        backend.register_pair(
            PairRecord(LOWER_DUMMY_ID, None, None, None, LOWER, is_dummy=True)
        )
        return backend

    def register_finite_pair(self, end_index, first_value, second_value):
        first_point_id = end_index - 1
        second_point_id = end_index
        self.values[first_point_id] = first_value
        self.values[second_point_id] = second_value
        family = UPPER if end_index % 2 == 0 else LOWER
        pair = PairRecord(
            pair_id=end_index,
            end_index=end_index,
            first_point_id=first_point_id,
            second_point_id=second_point_id,
            family=family,
        )
        self.backend.register_pair(pair)
        return pair

    def test_geometric_endpoint_helpers_separate_curve_order(self):
        increasing = self.register_finite_pair(2, 1, 4)
        decreasing = self.register_finite_pair(4, 8, 3)

        self.assertEqual(left_endpoint_id(increasing, self.values.__getitem__), 1)
        self.assertEqual(right_endpoint_id(increasing, self.values.__getitem__), 2)
        self.assertEqual(left_endpoint_id(decreasing, self.values.__getitem__), 4)
        self.assertEqual(right_endpoint_id(decreasing, self.values.__getitem__), 3)

    def test_pair_record_rejects_wrong_family_parity(self):
        with self.assertRaises(ValueError):
            PairRecord(2, 2, 1, 2, LOWER)

    def test_register_pair_rejects_duplicate_id(self):
        self.register_finite_pair(2, 1, 2)

        with self.assertRaises(ValueError):
            self.backend.register_pair(PairRecord(2, 2, 1, 2, UPPER))

    def test_registered_pair_ids_returns_registry_snapshot(self):
        self.register_finite_pair(2, 1, 2)

        pair_ids = self.backend.registered_pair_ids()

        self.assertEqual(set(pair_ids), {UPPER_DUMMY_ID, LOWER_DUMMY_ID, 2})
        self.assertIsInstance(pair_ids, tuple)

    def test_audit_snapshot_changes_with_backend_ownership(self):
        pair = self.register_finite_pair(2, 1, 2)
        before = self.backend.audit_snapshot()

        self.backend.make_list(pair.pair_id, UPPER_DUMMY_ID)
        after = self.backend.audit_snapshot()

        self.assertNotEqual(before, after)
        self.assertIsInstance(after, tuple)

    def test_point_value_uses_backend_initialization_source(self):
        self.values[1] = 17

        self.assertEqual(self.backend.point_value(1), 17)

    def test_unregister_unowned_pair_supports_transaction_rollback(self):
        pair = self.register_finite_pair(2, 1, 2)

        removed = self.backend.unregister_unowned_pair(pair.pair_id)

        self.assertIs(removed, pair)
        with self.assertRaises(KeyError):
            self.backend.get_pair(pair.pair_id)

    def test_unregister_unowned_pair_rejects_live_owned_pair(self):
        pair = self.register_finite_pair(2, 1, 2)
        self.backend.make_list(pair.pair_id, UPPER_DUMMY_ID)

        with self.assertRaises(ValueError):
            self.backend.unregister_unowned_pair(pair.pair_id)

        self.assertIs(self.backend.get_pair(pair.pair_id), pair)
        self.assertTrue(self.backend.validate_invariants())

    def test_make_list_assigns_pair_and_parent_ownership(self):
        pair = self.register_finite_pair(2, 1, 2)

        list_id = self.backend.make_list(pair.pair_id, UPPER_DUMMY_ID)

        sibling_list = self.backend.get_list(list_id)
        self.assertEqual(sibling_list.pair_ids, [pair.pair_id])
        self.assertEqual(sibling_list.owner_parent_pair_id, UPPER_DUMMY_ID)
        self.assertEqual(pair.parent_pair_id, UPPER_DUMMY_ID)
        self.assertEqual(pair.sibling_list_id, list_id)
        self.assertEqual(
            self.backend.get_pair(UPPER_DUMMY_ID).child_sibling_list_ids,
            [list_id],
        )
        self.assertTrue(self.backend.validate_invariants())

    def test_make_list_rejects_unowned_finite_parent(self):
        parent = self.register_finite_pair(2, 0, 5)
        child = self.register_finite_pair(4, 1, 2)

        with self.assertRaises(ValueError):
            self.backend.make_list(child.pair_id, parent.pair_id)

        self.assertIsNone(parent.parent_pair_id)
        self.assertEqual(parent.child_sibling_list_ids, [])
        self.assertIsNone(child.parent_pair_id)
        self.assertIsNone(child.sibling_list_id)
        self.assertTrue(self.backend.validate_invariants(require_all_owned=False))

    def test_parent_child_lists_are_ordered_and_limited_to_two(self):
        right_pair = self.register_finite_pair(2, 5, 6)
        left_pair = self.register_finite_pair(4, 1, 2)
        third_pair = self.register_finite_pair(6, 8, 9)

        right_list = self.backend.make_list(right_pair.pair_id, UPPER_DUMMY_ID)
        left_list = self.backend.make_list(left_pair.pair_id, UPPER_DUMMY_ID)

        self.assertEqual(
            self.backend.get_pair(UPPER_DUMMY_ID).child_sibling_list_ids,
            [left_list, right_list],
        )

        with self.assertRaises(ValueError):
            self.backend.make_list(third_pair.pair_id, UPPER_DUMMY_ID)

        self.assertIsNone(third_pair.parent_pair_id)
        self.assertIsNone(third_pair.sibling_list_id)
        self.assertTrue(self.backend.validate_invariants(require_all_owned=False))

    def test_insert_at_both_boundaries_inherits_parent(self):
        middle = self.register_finite_pair(2, 3, 4)
        left = self.register_finite_pair(4, 1, 2)
        right = self.register_finite_pair(6, 5, 6)
        list_id = self.backend.make_list(middle.pair_id, UPPER_DUMMY_ID)

        self.backend.insert_at_boundary(left.pair_id, middle.pair_id, BEFORE)
        self.backend.insert_at_boundary(right.pair_id, middle.pair_id, AFTER)

        self.assertEqual(
            self.backend.get_list(list_id).pair_ids,
            [left.pair_id, middle.pair_id, right.pair_id],
        )
        self.assertEqual(left.parent_pair_id, UPPER_DUMMY_ID)
        self.assertEqual(right.parent_pair_id, UPPER_DUMMY_ID)
        self.assertEqual(left.sibling_list_id, list_id)
        self.assertEqual(right.sibling_list_id, list_id)
        self.assertTrue(self.backend.validate_invariants())

    def test_insert_rejects_nonboundary_anchor_without_mutation(self):
        first = self.register_finite_pair(2, 1, 2)
        second = self.register_finite_pair(4, 3, 4)
        new_pair = self.register_finite_pair(6, 5, 6)
        list_id = self.backend.make_list(first.pair_id, UPPER_DUMMY_ID)
        self.backend.insert_at_boundary(second.pair_id, first.pair_id, AFTER)

        with self.assertRaises(ValueError):
            self.backend.insert_at_boundary(new_pair.pair_id, first.pair_id, AFTER)

        self.assertEqual(self.backend.get_list(list_id).pair_ids, [2, 4])
        self.assertIsNone(new_pair.sibling_list_id)
        self.assertTrue(self.backend.validate_invariants(require_all_owned=False))

    def test_insert_rejects_pair_owned_by_another_list(self):
        first = self.register_finite_pair(2, 1, 2)
        second = self.register_finite_pair(4, 3, 4)
        self.backend.make_list(first.pair_id, UPPER_DUMMY_ID)
        self.backend.make_list(second.pair_id, UPPER_DUMMY_ID)

        with self.assertRaises(ValueError):
            self.backend.insert_at_boundary(second.pair_id, first.pair_id, AFTER)

        self.assertTrue(self.backend.validate_invariants())

    def test_split_by_key_is_non_destructive(self):
        pair_ids, list_id = self._make_three_upper_siblings()

        plan = self.backend.split_by_key(
            list_id,
            4,
            lambda pair: self.values[left_endpoint_id(pair, self.values.__getitem__)],
        )

        self.assertEqual(plan.left_pair_ids, tuple(pair_ids[:2]))
        self.assertEqual(plan.right_pair_ids, tuple(pair_ids[2:]))
        self.assertEqual(self.backend.get_list(list_id).pair_ids, pair_ids)
        self.assertTrue(self.backend.validate_invariants())

    def test_split_rejects_noncontiguous_key_partition(self):
        _, list_id = self._make_three_upper_siblings()
        keys = {2: 1, 4: 9, 6: 3}

        with self.assertRaises(ValueError):
            self.backend.split_by_key(
                list_id,
                5,
                lambda pair: keys[pair.pair_id],
            )

        self.assertTrue(self.backend.validate_invariants())

    def test_commit_split_with_two_nonempty_sides_updates_ownership(self):
        pair_ids, list_id = self._make_three_upper_siblings()
        new_parent = self.register_finite_pair(8, 0, 5)
        new_parent_list = self.backend.make_list(
            new_parent.pair_id,
            UPPER_DUMMY_ID,
        )

        result = self.backend.split_pairs_at_value(
            list_id,
            boundary_value=5,
            acquired_side=LEFT,
            new_parent_pair_id=new_parent.pair_id,
        )

        with self.assertRaises(KeyError):
            self.backend.get_list(list_id)
        self.assertEqual(
            self.backend.get_list(result.left_list_id).pair_ids,
            pair_ids[:2],
        )
        self.assertEqual(
            self.backend.get_list(result.right_list_id).pair_ids,
            pair_ids[2:],
        )
        self.assertEqual(new_parent.child_sibling_list_ids, [result.left_list_id])
        self.assertEqual(
            self.backend.get_pair(UPPER_DUMMY_ID).child_sibling_list_ids,
            [new_parent_list, result.right_list_id],
        )
        for pair_id in pair_ids[:2]:
            self.assertEqual(
                self.backend.get_pair(pair_id).parent_pair_id,
                new_parent.pair_id,
            )
        self.assertEqual(
            self.backend.get_pair(pair_ids[2]).parent_pair_id,
            UPPER_DUMMY_ID,
        )
        self.assertTrue(self.backend.validate_invariants())

    def test_commit_split_with_two_nonempty_sides_can_acquire_right(self):
        left = self.register_finite_pair(2, 1, 2)
        right = self.register_finite_pair(4, 6, 7)
        new_parent = self.register_finite_pair(6, 3, 8)
        list_id = self.backend.make_list(left.pair_id, UPPER_DUMMY_ID)
        self.backend.insert_at_boundary(right.pair_id, left.pair_id, AFTER)
        new_parent_list = self.backend.make_list(
            new_parent.pair_id,
            UPPER_DUMMY_ID,
        )

        result = self.backend.split_pairs_at_value(
            list_id,
            boundary_value=4,
            acquired_side=RIGHT,
            new_parent_pair_id=new_parent.pair_id,
        )

        self.assertEqual(
            self.backend.get_list(result.left_list_id).pair_ids,
            [left.pair_id],
        )
        self.assertEqual(
            self.backend.get_list(result.right_list_id).pair_ids,
            [right.pair_id],
        )
        self.assertEqual(left.parent_pair_id, UPPER_DUMMY_ID)
        self.assertEqual(right.parent_pair_id, new_parent.pair_id)
        self.assertEqual(new_parent.child_sibling_list_ids, [result.right_list_id])
        self.assertEqual(
            self.backend.get_pair(UPPER_DUMMY_ID).child_sibling_list_ids,
            [result.left_list_id, new_parent_list],
        )
        self.assertTrue(self.backend.validate_invariants())

    def test_commit_split_rejects_unowned_finite_new_parent(self):
        child = self.register_finite_pair(2, 1, 2)
        new_parent = self.register_finite_pair(4, 0, 5)
        list_id = self.backend.make_list(child.pair_id, UPPER_DUMMY_ID)

        with self.assertRaises(ValueError):
            self.backend.split_pairs_at_value(
                list_id,
                boundary_value=5,
                acquired_side=LEFT,
                new_parent_pair_id=new_parent.pair_id,
            )

        self.assertEqual(self.backend.get_list(list_id).pair_ids, [child.pair_id])
        self.assertEqual(child.parent_pair_id, UPPER_DUMMY_ID)
        self.assertIsNone(new_parent.parent_pair_id)
        self.assertEqual(new_parent.child_sibling_list_ids, [])
        self.assertTrue(self.backend.validate_invariants(require_all_owned=False))

    def test_commit_split_rejects_descendant_new_parent_without_mutation(self):
        old_owner = self.register_finite_pair(2, 0, 10)
        acquired = self.register_finite_pair(4, 2, 8)
        descendant = self.register_finite_pair(6, 3, 7)
        self.backend.make_list(old_owner.pair_id, UPPER_DUMMY_ID)
        acquired_list_id = self.backend.make_list(
            acquired.pair_id,
            old_owner.pair_id,
        )
        descendant_list_id = self.backend.make_list(
            descendant.pair_id,
            acquired.pair_id,
        )
        old_owner_children = list(old_owner.child_sibling_list_ids)
        acquired_children = list(acquired.child_sibling_list_ids)

        with self.assertRaises(ValueError):
            self.backend.split_pairs_at_value(
                acquired_list_id,
                boundary_value=9,
                acquired_side=LEFT,
                new_parent_pair_id=descendant.pair_id,
            )

        self.assertEqual(
            self.backend.get_list(acquired_list_id).pair_ids,
            [acquired.pair_id],
        )
        self.assertEqual(
            self.backend.get_list(descendant_list_id).pair_ids,
            [descendant.pair_id],
        )
        self.assertEqual(acquired.parent_pair_id, old_owner.pair_id)
        self.assertEqual(descendant.parent_pair_id, acquired.pair_id)
        self.assertEqual(old_owner.child_sibling_list_ids, old_owner_children)
        self.assertEqual(acquired.child_sibling_list_ids, acquired_children)
        self.assertTrue(self.backend.validate_invariants())

    def test_split_supports_empty_right_output(self):
        child = self.register_finite_pair(2, 1, 2)
        new_parent = self.register_finite_pair(4, 0, 5)
        list_id = self.backend.make_list(child.pair_id, UPPER_DUMMY_ID)
        self.backend.make_list(new_parent.pair_id, UPPER_DUMMY_ID)

        result = self.backend.split_pairs_at_value(
            list_id,
            boundary_value=5,
            acquired_side=LEFT,
            new_parent_pair_id=new_parent.pair_id,
        )

        self.assertIsNotNone(result.left_list_id)
        self.assertIsNone(result.right_list_id)
        self.assertEqual(child.parent_pair_id, new_parent.pair_id)
        self.assertEqual(new_parent.child_sibling_list_ids, [result.left_list_id])
        self.assertTrue(self.backend.validate_invariants())

    def test_split_supports_empty_left_output(self):
        child = self.register_finite_pair(2, 8, 9)
        new_parent = self.register_finite_pair(4, 5, 10)
        list_id = self.backend.make_list(child.pair_id, UPPER_DUMMY_ID)
        self.backend.make_list(new_parent.pair_id, UPPER_DUMMY_ID)

        result = self.backend.split_pairs_at_value(
            list_id,
            boundary_value=5,
            acquired_side=RIGHT,
            new_parent_pair_id=new_parent.pair_id,
        )

        self.assertIsNone(result.left_list_id)
        self.assertIsNotNone(result.right_list_id)
        self.assertEqual(child.parent_pair_id, new_parent.pair_id)
        self.assertEqual(new_parent.child_sibling_list_ids, [result.right_list_id])
        self.assertTrue(self.backend.validate_invariants())

    def test_split_supports_empty_acquired_side(self):
        child = self.register_finite_pair(2, 8, 9)
        new_parent = self.register_finite_pair(4, 0, 5)
        list_id = self.backend.make_list(child.pair_id, UPPER_DUMMY_ID)
        self.backend.make_list(new_parent.pair_id, UPPER_DUMMY_ID)

        result = self.backend.split_pairs_at_value(
            list_id,
            boundary_value=5,
            acquired_side=LEFT,
            new_parent_pair_id=new_parent.pair_id,
        )

        self.assertIsNone(result.left_list_id)
        self.assertIsNotNone(result.right_list_id)
        self.assertEqual(child.parent_pair_id, UPPER_DUMMY_ID)
        self.assertEqual(new_parent.child_sibling_list_ids, [])
        self.assertTrue(self.backend.validate_invariants())

    def test_split_rejects_straddling_pair_without_mutation(self):
        child = self.register_finite_pair(2, 1, 8)
        new_parent = self.register_finite_pair(4, 0, 10)
        list_id = self.backend.make_list(child.pair_id, UPPER_DUMMY_ID)
        self.backend.make_list(new_parent.pair_id, UPPER_DUMMY_ID)
        original_owner_lists = list(
            self.backend.get_pair(UPPER_DUMMY_ID).child_sibling_list_ids
        )

        with self.assertRaises(ValueError):
            self.backend.split_pairs_at_value(
                list_id,
                boundary_value=5,
                acquired_side=LEFT,
                new_parent_pair_id=new_parent.pair_id,
            )

        self.assertEqual(self.backend.get_list(list_id).pair_ids, [child.pair_id])
        self.assertEqual(child.parent_pair_id, UPPER_DUMMY_ID)
        self.assertEqual(
            self.backend.get_pair(UPPER_DUMMY_ID).child_sibling_list_ids,
            original_owner_lists,
        )
        self.assertTrue(self.backend.validate_invariants())

    def test_split_rejects_third_new_parent_child_list_without_mutation(self):
        split_child = self.register_finite_pair(2, 1, 2)
        existing_child_1 = self.register_finite_pair(4, 3, 4)
        existing_child_2 = self.register_finite_pair(6, 5, 6)
        new_parent = self.register_finite_pair(8, 0, 10)

        split_list = self.backend.make_list(split_child.pair_id, UPPER_DUMMY_ID)
        self.backend.make_list(new_parent.pair_id, UPPER_DUMMY_ID)
        first_child_list = self.backend.make_list(
            existing_child_1.pair_id,
            new_parent.pair_id,
        )
        second_child_list = self.backend.make_list(
            existing_child_2.pair_id,
            new_parent.pair_id,
        )

        with self.assertRaises(ValueError):
            self.backend.split_pairs_at_value(
                split_list,
                boundary_value=9,
                acquired_side=LEFT,
                new_parent_pair_id=new_parent.pair_id,
            )

        self.assertEqual(
            new_parent.child_sibling_list_ids,
            [first_child_list, second_child_list],
        )
        self.assertEqual(self.backend.get_list(split_list).pair_ids, [2])
        self.assertEqual(split_child.parent_pair_id, UPPER_DUMMY_ID)
        self.assertTrue(self.backend.validate_invariants())

    def test_commit_split_rolls_back_when_final_invariant_check_fails(self):
        child = self.register_finite_pair(2, 1, 2)
        new_parent = self.register_finite_pair(4, 0, 5)
        list_id = self.backend.make_list(child.pair_id, UPPER_DUMMY_ID)
        new_parent_list_id = self.backend.make_list(
            new_parent.pair_id,
            UPPER_DUMMY_ID,
        )
        dummy_children = list(
            self.backend.get_pair(UPPER_DUMMY_ID).child_sibling_list_ids
        )

        with patch.object(
            self.backend,
            "validate_invariants",
            side_effect=RuntimeError("forced final invariant failure"),
        ):
            with self.assertRaises(RuntimeError):
                self.backend.split_pairs_at_value(
                    list_id,
                    boundary_value=5,
                    acquired_side=LEFT,
                    new_parent_pair_id=new_parent.pair_id,
                )

        self.assertEqual(self.backend.get_list(list_id).pair_ids, [child.pair_id])
        self.assertEqual(
            self.backend.get_list(new_parent_list_id).pair_ids,
            [new_parent.pair_id],
        )
        self.assertEqual(child.parent_pair_id, UPPER_DUMMY_ID)
        self.assertEqual(child.sibling_list_id, list_id)
        self.assertEqual(new_parent.child_sibling_list_ids, [])
        self.assertEqual(
            self.backend.get_pair(UPPER_DUMMY_ID).child_sibling_list_ids,
            dummy_children,
        )
        self.assertTrue(self.backend.validate_invariants())

    def test_minimal_commit_skips_global_audit_and_runs_local_postconditions(self):
        self.backend = self.make_backend(MINIMAL_POLICY)
        child = self.register_finite_pair(2, 1, 2)
        new_parent = self.register_finite_pair(4, 0, 5)
        list_id = self.backend.make_list(child.pair_id, UPPER_DUMMY_ID)
        self.backend.make_list(new_parent.pair_id, UPPER_DUMMY_ID)
        local_postconditions = self.backend._validate_split_commit_postconditions

        with patch.object(
            self.backend,
            "_validate_split_commit_postconditions",
            wraps=local_postconditions,
        ) as local_mock:
            with patch.object(
                self.backend,
                "validate_invariants",
                side_effect=AssertionError("global audit must be skipped"),
            ):
                result = self.backend.split_pairs_at_value(
                    list_id,
                    boundary_value=5,
                    acquired_side=LEFT,
                    new_parent_pair_id=new_parent.pair_id,
                )

        self.assertIsNotNone(result.left_list_id)
        self.assertIsNone(result.right_list_id)
        self.assertEqual(local_mock.call_count, 1)
        self.assertTrue(self.backend.validate_invariants())

    def test_minimal_commit_rolls_back_when_local_postcondition_fails(self):
        self.backend = self.make_backend(MINIMAL_POLICY)
        child = self.register_finite_pair(2, 1, 2)
        new_parent = self.register_finite_pair(4, 0, 5)
        list_id = self.backend.make_list(child.pair_id, UPPER_DUMMY_ID)
        self.backend.make_list(new_parent.pair_id, UPPER_DUMMY_ID)
        before = self.backend.audit_snapshot()

        with patch.object(
            self.backend,
            "_validate_split_commit_postconditions",
            side_effect=RuntimeError("forced local postcondition failure"),
        ):
            with self.assertRaisesRegex(
                RuntimeError,
                "forced local postcondition failure",
            ):
                self.backend.split_pairs_at_value(
                    list_id,
                    boundary_value=5,
                    acquired_side=LEFT,
                    new_parent_pair_id=new_parent.pair_id,
                )

        self.assertEqual(self.backend.audit_snapshot(), before)
        self.assertTrue(self.backend.validate_invariants())

    def test_minimal_local_postconditions_detect_ownership_corruption(self):
        self.backend = self.make_backend(MINIMAL_POLICY)
        child = self.register_finite_pair(2, 1, 2)
        new_parent = self.register_finite_pair(4, 0, 5)
        list_id = self.backend.make_list(child.pair_id, UPPER_DUMMY_ID)
        self.backend.make_list(new_parent.pair_id, UPPER_DUMMY_ID)
        before = self.backend.audit_snapshot()
        local_postconditions = self.backend._validate_split_commit_postconditions

        def corrupt_then_validate(**kwargs):
            child.parent_pair_id = LOWER_DUMMY_ID
            return local_postconditions(**kwargs)

        with patch.object(
            self.backend,
            "_validate_split_commit_postconditions",
            side_effect=corrupt_then_validate,
        ):
            with self.assertRaisesRegex(RuntimeError, "wrong parent"):
                self.backend.split_pairs_at_value(
                    list_id,
                    boundary_value=5,
                    acquired_side=LEFT,
                    new_parent_pair_id=new_parent.pair_id,
                )

        self.assertEqual(self.backend.audit_snapshot(), before)
        self.assertTrue(self.backend.validate_invariants())

    def test_minimal_policy_keeps_invalid_side_and_stale_plan_guards(self):
        self.backend = self.make_backend(MINIMAL_POLICY)
        first = self.register_finite_pair(2, 1, 2)
        second = self.register_finite_pair(4, 3, 4)
        new_parent = self.register_finite_pair(6, 0, 5)
        list_id = self.backend.make_list(first.pair_id, UPPER_DUMMY_ID)
        plan = self.backend.split_by_key(list_id, 2, lambda pair: pair.pair_id)
        self.backend.make_list(new_parent.pair_id, UPPER_DUMMY_ID)
        before_invalid_side = self.backend.audit_snapshot()

        with self.assertRaisesRegex(ValueError, "acquired_side"):
            self.backend.commit_split(plan, "middle", new_parent.pair_id)
        self.assertEqual(self.backend.audit_snapshot(), before_invalid_side)

        self.backend.insert_at_boundary(second.pair_id, first.pair_id, AFTER)
        before_stale_plan = self.backend.audit_snapshot()
        with self.assertRaisesRegex(ValueError, "stale"):
            self.backend.commit_split(plan, LEFT, new_parent.pair_id)
        self.assertEqual(self.backend.audit_snapshot(), before_stale_plan)
        self.assertTrue(self.backend.validate_invariants())

    def test_split_guards_apply_with_and_without_global_audit(self):
        for policy in (CHECKED_POLICY, MINIMAL_POLICY):
            with self.subTest(policy=policy.name, guard="invalid_side"):
                self.values = {}
                self.backend = self.make_backend(policy)
                child = self.register_finite_pair(2, 1, 2)
                new_parent = self.register_finite_pair(4, 0, 5)
                list_id = self.backend.make_list(
                    child.pair_id,
                    UPPER_DUMMY_ID,
                )
                self.backend.make_list(
                    new_parent.pair_id,
                    UPPER_DUMMY_ID,
                )
                plan = self.backend.split_by_key(
                    list_id,
                    5,
                    lambda pair: pair.pair_id,
                )
                before = self.backend.audit_snapshot()

                with self.assertRaisesRegex(ValueError, "acquired_side"):
                    self.backend.commit_split(
                        plan,
                        "middle",
                        new_parent.pair_id,
                    )
                self.assertEqual(self.backend.audit_snapshot(), before)

            with self.subTest(policy=policy.name, guard="unowned_parent"):
                self.values = {}
                self.backend = self.make_backend(policy)
                child = self.register_finite_pair(2, 1, 2)
                new_parent = self.register_finite_pair(4, 0, 5)
                list_id = self.backend.make_list(
                    child.pair_id,
                    UPPER_DUMMY_ID,
                )
                plan = self.backend.split_by_key(
                    list_id,
                    5,
                    lambda pair: pair.pair_id,
                )
                before = self.backend.audit_snapshot()

                with self.assertRaisesRegex(ValueError, "finite parent"):
                    self.backend.commit_split(
                        plan,
                        LEFT,
                        new_parent.pair_id,
                    )
                self.assertEqual(self.backend.audit_snapshot(), before)
                self.assertTrue(
                    self.backend.validate_invariants(require_all_owned=False)
                )

            with self.subTest(policy=policy.name, guard="ownership_mismatch"):
                self.values = {}
                self.backend = self.make_backend(policy)
                child = self.register_finite_pair(2, 1, 2)
                new_parent = self.register_finite_pair(4, 0, 5)
                list_id = self.backend.make_list(
                    child.pair_id,
                    UPPER_DUMMY_ID,
                )
                self.backend.make_list(
                    new_parent.pair_id,
                    UPPER_DUMMY_ID,
                )
                plan = self.backend.split_by_key(
                    list_id,
                    5,
                    lambda pair: pair.pair_id,
                )
                child.parent_pair_id = new_parent.pair_id
                before = self.backend.audit_snapshot()

                with self.assertRaisesRegex(ValueError, "old parent"):
                    self.backend.commit_split(
                        plan,
                        LEFT,
                        new_parent.pair_id,
                    )
                self.assertEqual(self.backend.audit_snapshot(), before)

                child.parent_pair_id = UPPER_DUMMY_ID
                self.assertTrue(self.backend.validate_invariants())

    def test_validate_invariants_rejects_family_tree_cycle(self):
        parent = self.register_finite_pair(2, 0, 10)
        child = self.register_finite_pair(4, 2, 8)
        parent_list_id = self.backend.make_list(parent.pair_id, UPPER_DUMMY_ID)
        child_list_id = self.backend.make_list(child.pair_id, parent.pair_id)

        dummy = self.backend.get_pair(UPPER_DUMMY_ID)
        dummy.child_sibling_list_ids = []
        child.child_sibling_list_ids = [parent_list_id]
        parent.parent_pair_id = child.pair_id
        self.backend.get_list(parent_list_id).owner_parent_pair_id = child.pair_id

        self.assertEqual(parent.child_sibling_list_ids, [child_list_id])
        with self.assertRaises(RuntimeError):
            self.backend.validate_invariants()

    def test_stale_split_plan_is_rejected_without_retiring_live_list(self):
        first = self.register_finite_pair(2, 1, 2)
        second = self.register_finite_pair(4, 3, 4)
        new_parent = self.register_finite_pair(6, 0, 5)
        list_id = self.backend.make_list(first.pair_id, UPPER_DUMMY_ID)
        plan = self.backend.split_by_key(list_id, 2, lambda pair: pair.pair_id)
        self.backend.insert_at_boundary(second.pair_id, first.pair_id, AFTER)
        self.backend.make_list(new_parent.pair_id, UPPER_DUMMY_ID)

        with self.assertRaises(ValueError):
            self.backend.commit_split(plan, LEFT, new_parent.pair_id)

        self.assertEqual(self.backend.get_list(list_id).pair_ids, [2, 4])
        self.assertTrue(self.backend.validate_invariants())

    def test_forged_plan_with_foreign_pair_is_rejected(self):
        child = self.register_finite_pair(2, 1, 2)
        foreign = self.register_finite_pair(4, 4, 5)
        new_parent = self.register_finite_pair(6, 0, 3)
        list_id = self.backend.make_list(child.pair_id, UPPER_DUMMY_ID)
        self.backend.make_list(foreign.pair_id, UPPER_DUMMY_ID)
        forged = SplitPlan(
            retired_list_id=list_id,
            previous_owner_parent_pair_id=UPPER_DUMMY_ID,
            original_pair_ids=(child.pair_id, foreign.pair_id),
            left_pair_ids=(child.pair_id,),
            right_pair_ids=(foreign.pair_id,),
        )

        with self.assertRaises(ValueError):
            self.backend.commit_split(forged, LEFT, new_parent.pair_id)

        self.assertEqual(self.backend.get_list(list_id).pair_ids, [child.pair_id])

    def _make_three_upper_siblings(self):
        pairs = [
            self.register_finite_pair(2, 1, 2),
            self.register_finite_pair(4, 3, 4),
            self.register_finite_pair(6, 6, 7),
        ]
        list_id = self.backend.make_list(pairs[0].pair_id, UPPER_DUMMY_ID)
        self.backend.insert_at_boundary(pairs[1].pair_id, pairs[0].pair_id, AFTER)
        self.backend.insert_at_boundary(pairs[2].pair_id, pairs[1].pair_id, AFTER)
        return [pair.pair_id for pair in pairs], list_id


if __name__ == "__main__":
    unittest.main()
