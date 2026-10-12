"""PARTIAL operation validation of real make/insert, never full acceptance.

The list below is an independent semantic oracle used only by tests. The
production backend contains external/internal nodes and reversed end ribs.
"""

import itertools
from pathlib import Path
import random
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from heterogeneous_finger_backend import (  # noqa: E402
    ExternalLeaf, HeterogeneousFingerBackend, InternalNode, INTERIOR, ROOT,
)
from paper_execution_policy import MINIMAL_POLICY  # noqa: E402
from sibling_backend_contract import SiblingBackendSpec, resolve_sibling_backend  # noqa: E402
from sibling_list_backend import LEFT, RIGHT, UPPER, LOWER, PairRecord  # noqa: E402


class Fixture:
    def __init__(self, policy=MINIMAL_POLICY):
        self.values = {}
        self.backend = HeterogeneousFingerBackend(self.values.__getitem__, execution_policy=policy)
        self.backend.register_pair(PairRecord(-1, None, None, None, UPPER, is_dummy=True))
        self.backend.register_pair(PairRecord(-2, None, None, None, LOWER, is_dummy=True))
        self.next_pair = 2

    def pair(self, low, high, *, reverse=False, family=UPPER):
        pair_id = self.next_pair + (family == LOWER)
        self.next_pair += 2
        first, second = 4 * pair_id + 1, 4 * pair_id + 2
        self.values[first], self.values[second] = (high, low) if reverse else (low, high)
        pair = PairRecord(pair_id, pair_id, first, second, family)
        self.backend.register_pair(pair)
        return pair


class HeterogeneousMakeInsertTests(unittest.TestCase):
    def assert_model(self, fixture, list_id, pairs, owner=-1):
        backend = fixture.backend
        self.assertTrue(backend.validate_invariants())
        self.assertIn((owner, tuple(p.pair_id for p in pairs)), backend.materialize_audit())
        self.assertEqual(backend.list_size(list_id), len(pairs))
        self.assertEqual(backend.list_owner(list_id), owner)
        self.assertEqual(backend.boundary_list(pairs[0].pair_id, LEFT), list_id)
        self.assertEqual(backend.boundary_list(pairs[-1].pair_id, RIGHT), list_id)
        for index, pair in enumerate(pairs):
            self.assertIs(backend.get_pair(pair.pair_id), pair)
            self.assertIs(backend.validate_live_pair(pair.pair_id), pair)
            handle = backend.pair_handle(pair.pair_id)
            self.assertIs(handle.leaf.handle, handle)
            self.assertIs(handle.pair, pair)
            self.assertIsNone(pair.parent_pair_id)
            self.assertIsNone(pair.sibling_list_id)
            if index:
                self.assertIsNone(handle.left_boundary)
            if index < len(pairs)-1:
                self.assertIsNone(handle.right_boundary)

    def sequence(self, sides, *, family=UPPER, reverse=False):
        fixture = Fixture()
        b = fixture.backend
        owner = -1 if family == UPPER else -2
        first = fixture.pair(0, 1, reverse=reverse, family=family)
        pairs = [first]
        list_id = b.make_list(first.pair_id, owner)
        handles = {first.pair_id: b.pair_handle(first.pair_id)}
        leaves = {first.pair_id: handles[first.pair_id].leaf}
        self.assert_model(fixture, list_id, pairs, owner)
        low, high = 0, 1
        for index, side in enumerate(sides):
            if side == LEFT:
                low -= 3
                new = fixture.pair(low, low+1, reverse=reverse ^ bool(index % 2), family=family)
                anchor = pairs[0]
            else:
                high += 3
                new = fixture.pair(high-1, high, reverse=reverse ^ bool(index % 2), family=family)
                anchor = pairs[-1]
            self.assertEqual(b.insert_boundary(new.pair_id, anchor.pair_id, side), list_id)
            pairs.insert(0, new) if side == LEFT else pairs.append(new)
            handles[new.pair_id] = b.pair_handle(new.pair_id)
            leaves[new.pair_id] = handles[new.pair_id].leaf
            self.assert_model(fixture, list_id, pairs, owner)
            for pair in pairs:
                self.assertIs(b.pair_handle(pair.pair_id), handles[pair.pair_id])
                self.assertIs(handles[pair.pair_id].leaf, leaves[pair.pair_id])
        return fixture, list_id, pairs

    def test_singleton_is_real_external_leaf_with_two_boundary_references(self):
        f, list_id, pairs = self.sequence([])
        header = f.backend._lists[list_id]
        self.assertIsInstance(header.root, ExternalLeaf)
        self.assertEqual(header.root.role, ROOT)
        self.assertIs(header.left_finger, header.right_finger)
        h = f.backend.pair_handle(pairs[0].pair_id)
        self.assertIs(h.left_boundary, h.right_boundary)

    def test_continuous_left_insertion_model_and_identity_after_every_operation(self):
        self.sequence([LEFT] * 160)

    def test_continuous_right_insertion_model_and_identity_after_every_operation(self):
        self.sequence([RIGHT] * 160, reverse=True)

    def test_alternating_ends_in_both_families(self):
        for family in (UPPER, LOWER):
            with self.subTest(family=family):
                self.sequence([LEFT, RIGHT] * 64, family=family)

    def test_bounded_all_side_sequences(self):
        # 256 histories, each with singleton + 8 updates. Not 256 Jordan inputs.
        for sides in itertools.product((LEFT, RIGHT), repeat=8):
            with self.subTest(sides=sides):
                self.sequence(sides)

    def test_seeded_irregular_sequences(self):
        for seed in range(5):
            generator = random.Random(seed)
            sides = [generator.choice((LEFT, RIGHT)) for _ in range(120)]
            with self.subTest(seed=seed):
                self.sequence(sides, reverse=bool(seed % 2))

    def test_mirrors_have_same_structure_and_swap_rotation_directions(self):
        sides = [LEFT] * 19 + [RIGHT] * 31 + [LEFT, RIGHT] * 28
        left, lid, lp = self.sequence(sides)
        right, rid, rp = self.sequence([RIGHT if s == LEFT else LEFT for s in sides])
        a, b = left.backend, right.backend
        self.assertEqual([p.pair_id for p in lp], [p.pair_id for p in reversed(rp)])
        wa, wb = a.work.snapshot()["operations"], b.work.snapshot()["operations"]
        self.assertEqual(wa["left_rotations"], wb["right_rotations"])
        self.assertEqual(wa["right_rotations"], wb["left_rotations"])
        self.assertEqual(wa["recolorings"], wb["recolorings"])
        self.assertEqual(a._lists[lid].root.rank, b._lists[rid].root.rank)

    def test_rebalancing_exercises_root_and_nonroot_rotation_and_cascades(self):
        f = Fixture()
        b = f.backend
        seen = set()
        original = b._rotate_outward
        def record(header, grand, parent, child, side):
            seen.add((grand.role == ROOT, side))
            return original(header, grand, parent, child, side)
        with patch.object(b, "_rotate_outward", side_effect=record):
            p = f.pair(0, 1)
            list_id = b.make_list(p.pair_id, -1)
            low = high = p
            for i, side in enumerate([RIGHT]*80 + [LEFT]*160 + [RIGHT]*240, 1):
                pair = f.pair(3*i, 3*i+1) if side == RIGHT else f.pair(-3*i, -3*i+1)
                b.insert_boundary(pair.pair_id, (low if side == LEFT else high).pair_id, side)
                if side == LEFT:
                    low = pair
                else:
                    high = pair
                b.validate_invariants()
        self.assertEqual(seen, {(True, LEFT), (False, LEFT), (True, RIGHT), (False, RIGHT)})
        work = b.work.snapshot()["operations"]
        self.assertGreater(work["recolor_cascades"], 0)
        self.assertGreater(work["root_blackenings"], 1)
        self.assertEqual(b.list_size(list_id), 481)

    def test_owner_slots_order_and_extreme_child_are_constant_size(self):
        f = Fixture(); b = f.backend
        right = f.pair(20, 21); left = f.pair(0, 1)
        r = b.make_list(right.pair_id, -1); l = b.make_list(left.pair_id, -1)
        self.assertEqual(b.child_list_ids(-1), (l, r))
        self.assertIs(b.extreme_child(-1, LEFT), left)
        self.assertIs(b.extreme_child(-1, RIGHT), right)
        near = f.pair(3, 4); b.insert_boundary(near.pair_id, left.pair_id, RIGHT)
        self.assert_model(f, l, [left, near])
        self.assert_model(f, r, [right])

    def test_internal_pair_can_be_parent_without_owner_search(self):
        f = Fixture(); b = f.backend
        parent = f.pair(10, 30, reverse=True)
        l = b.make_list(parent.pair_id, -1)
        first = f.pair(0, 1); last = f.pair(40, 41)
        b.insert_boundary(first.pair_id, parent.pair_id, LEFT)
        b.insert_boundary(last.pair_id, parent.pair_id, RIGHT)
        child = f.pair(15, 16)
        with patch.object(b, "boundary_list", side_effect=AssertionError("arbitrary-owner lookup")):
            child_list = b.make_list(child.pair_id, parent.pair_id)
        self.assert_model(f, l, [first, parent, last])
        self.assert_model(f, child_list, [child], parent.pair_id)

    def test_normal_updates_and_queries_never_materialize_or_audit(self):
        f = Fixture(); b = f.backend
        class NoEnumeration(dict):
            def __iter__(self):
                raise AssertionError("registry enumeration on the normal path")
            def items(self):
                raise AssertionError("registry enumeration on the normal path")
            def values(self):
                raise AssertionError("registry enumeration on the normal path")
        b._pairs, b._lists, b._nodes = (NoEnumeration(b._pairs), NoEnumeration(b._lists), NoEnumeration(b._nodes))
        with patch.object(b, "_audit", side_effect=AssertionError("audit in update")), \
             patch.object(b, "materialize_audit", side_effect=AssertionError("materialization")), \
             patch.object(b, "registered_pair_ids", side_effect=AssertionError("enumeration")):
            p = f.pair(0, 1); list_id = b.make_list(p.pair_id, -1)
            for i in range(1, 96):
                new = f.pair(3*i, 3*i+1)
                b.insert_boundary(new.pair_id, p.pair_id, RIGHT)
                self.assertEqual(b.boundary_list(new.pair_id, RIGHT), list_id)
                self.assertIs(b.extreme_child(-1, RIGHT), new)
                self.assertEqual(b.list_owner(list_id), -1)
                p = new
        b._pairs, b._lists, b._nodes = (dict(b._pairs), dict(b._lists), dict(b._nodes))
        b.validate_invariants()

    def test_boundary_owner_and_extreme_queries_have_size_independent_work(self):
        f = Fixture(); b = f.backend
        p = f.pair(0, 1); lid = b.make_list(p.pair_id, -1)
        observations = []
        for size in range(2, 514):
            new = f.pair(3*size, 3*size+1)
            b.insert_boundary(new.pair_id, p.pair_id, RIGHT)
            p = new
            if size in (8, 64, 513):
                before = b.work.snapshot()["queries"]
                self.assertEqual(b.boundary_list(p.pair_id, RIGHT), lid)
                self.assertEqual(b.list_owner(lid), -1)
                self.assertIs(b.extreme_child(-1, RIGHT), p)
                after = b.work.snapshot()["queries"]
                observations.append({key: after[key]-before[key] for key in before})
        self.assertEqual(observations[0], observations[1])
        self.assertEqual(observations[1], observations[2])
        b.validate_invariants()

    def test_cost_ledger_includes_all_record_writes_and_keeps_audit_separate(self):
        f, _, _ = self.sequence([RIGHT]*24 + [LEFT]*24)
        b = f.backend
        before = b.work.snapshot()
        b.validate_invariants()
        after = b.work.snapshot()
        self.assertEqual(before["operations"], after["operations"])
        self.assertEqual(before["queries"], after["queries"])
        self.assertGreater(after["audit"]["node_visits"], before["audit"]["node_visits"])
        work = after["operations"]
        self.assertEqual(work["leaf_allocations"], 49)
        self.assertEqual(work["internal_allocations"], 48)
        self.assertEqual(work["header_allocations"], 1)
        self.assertEqual(work["handle_allocations"], 51)  # including two family dummies
        self.assertEqual(work["node_visits"], work["node_reads"] + work["node_writes"])
        self.assertGreater(work["metadata_writes"], work["node_writes"])
        self.assertGreater(work["node_reads"], work["rotations"])
        self.assertGreater(work["comparisons"], 0)

    def test_terminal_repair_cost_does_not_grow_with_full_ancestor_height(self):
        f = Fixture(); b = f.backend
        p = f.pair(0, 1); lid = b.make_list(p.pair_id, -1)
        plain = []
        for i in range(1, 300):
            new = f.pair(3*i, 3*i+1)
            b.insert_boundary(new.pair_id, p.pair_id, RIGHT)
            work = b.work.last_operation["work"]
            # With monotone endpoint insertion the newest internal parent is
            # red. Compare equal terminal repairs at different tree heights,
            # excluding the constant-size root/root-child special cases.
            if (work["rotations"] == 1 and not work["recolor_cascades"]
                    and b._lists[lid].root.rank >= 3):
                plain.append((b._lists[lid].root.rank, work["node_visits"], work["metadata_writes"]))
            p = new
        self.assertGreater(max(x[0] for x in plain), min(x[0] for x in plain))
        self.assertEqual(len({x[1:] for x in plain}), 1)
        b.validate_invariants()

    def test_snapshot_determinism_and_schema(self):
        a, _, _ = self.sequence([LEFT, RIGHT, RIGHT, LEFT]*9)
        b, _, _ = self.sequence([LEFT, RIGHT, RIGHT, LEFT]*9)
        self.assertEqual(a.backend.audit_snapshot(), b.backend.audit_snapshot())
        self.assertEqual(a.backend.logical_snapshot(), b.backend.logical_snapshot())
        self.assertEqual(a.backend.logical_snapshot()[0], "jordan-logical-v1")


class HeterogeneousRejectionTests(unittest.TestCase):
    def initial(self):
        f = Fixture(); p = f.pair(0, 1)
        lid = f.backend.make_list(p.pair_id, -1)
        return f, p, lid

    def test_nonboundary_and_outdated_anchor_rejected(self):
        for side in (LEFT, RIGHT):
            with self.subTest(side=side):
                f, first, lid = self.initial(); b = f.backend
                new = f.pair(-3, -2) if side == LEFT else f.pair(3, 4)
                b.insert_boundary(new.pair_id, first.pair_id, side)
                pending = f.pair(-6, -5) if side == LEFT else f.pair(6, 7)
                with self.assertRaises(ValueError):
                    b.insert_boundary(pending.pair_id, first.pair_id, side)
                self.assertFalse(b.sorting_ready)
                self.assertEqual(b.work.last_operation["status"], "failed")

    def test_forged_stale_boundary_reference_is_not_trusted(self):
        f, first, lid = self.initial(); b = f.backend
        new = f.pair(3, 4); b.insert_boundary(new.pair_id, first.pair_id, RIGHT)
        b.pair_handle(first.pair_id).right_boundary = b._lists[lid]
        with self.assertRaisesRegex(ValueError, "stale boundary finger"):
            b.boundary_list(first.pair_id, RIGHT)

    def test_retired_header_reference_rejected(self):
        f, first, lid = self.initial(); b = f.backend
        b._lists[lid].live = False  # fault injection; split is not implemented
        with self.assertRaisesRegex(ValueError, "retired"):
            b.boundary_list(first.pair_id, LEFT)

    def test_foreign_header_with_same_id_rejected(self):
        f, first, lid = self.initial(); other, _, _ = self.initial()
        f.backend.pair_handle(first.pair_id).left_boundary = other.backend._lists[lid]
        with self.assertRaisesRegex(ValueError, "stale boundary header"):
            f.backend.boundary_list(first.pair_id, LEFT)

    def test_owned_item_and_dummy_cannot_be_inserted_or_made_again(self):
        for action in ("make_owned", "insert_owned", "make_dummy", "insert_dummy"):
            f, first, _ = self.initial(); b = f.backend
            with self.subTest(action=action), self.assertRaises(ValueError):
                if action == "make_owned": b.make_list(first.pair_id, -1)
                elif action == "insert_owned": b.insert_boundary(first.pair_id, first.pair_id, LEFT)
                elif action == "make_dummy": b.make_list(-1, -1)
                else: b.insert_boundary(-1, first.pair_id, RIGHT)

    def test_wrong_family_rejected(self):
        f, first, _ = self.initial(); p = f.pair(3, 4, family=LOWER)
        with self.assertRaisesRegex(ValueError, "same family"):
            f.backend.insert_boundary(p.pair_id, first.pair_id, RIGHT)

    def test_reversed_overlapping_and_touching_intervals_rejected(self):
        for low, high in [(-3, -2), (0, 3), (1, 3)]:
            f, first, _ = self.initial(); p = f.pair(low, high)
            with self.subTest(interval=(low, high)), self.assertRaises(ValueError):
                f.backend.insert_boundary(p.pair_id, first.pair_id, RIGHT)

    def test_insertion_cannot_cross_other_child_slot(self):
        for side in (LEFT, RIGHT):
            f, first, _ = self.initial(); b = f.backend
            other = f.pair(9, 10); b.make_list(other.pair_id, -1)
            new = f.pair(12, 13) if side == RIGHT else f.pair(-3, -2)
            anchor = first if side == RIGHT else other
            with self.subTest(side=side), self.assertRaises(ValueError):
                b.insert_boundary(new.pair_id, anchor.pair_id, side)

    def test_make_rejects_overlapping_group_and_third_slot(self):
        for interval in [(0, 2), (6, 7)]:
            f, _, _ = self.initial(); b = f.backend
            if interval == (6, 7):
                second = f.pair(3, 4); b.make_list(second.pair_id, -1)
            new = f.pair(*interval)
            with self.subTest(interval=interval), self.assertRaises(ValueError):
                b.make_list(new.pair_id, -1)

    def test_make_rejects_unowned_parent_and_non_enclosed_child(self):
        for owned in (False, True):
            f = Fixture(); b = f.backend
            parent = f.pair(10, 20)
            if owned: b.make_list(parent.pair_id, -1)
            child = f.pair(19, 21)
            with self.subTest(owned=owned), self.assertRaises(ValueError):
                b.make_list(child.pair_id, parent.pair_id)

    def test_duplicate_registration_and_unordered_endpoints_rejected(self):
        f, first, _ = self.initial()
        with self.assertRaisesRegex(ValueError, "duplicate"):
            f.backend.register_pair(first)
        with self.assertRaises(ValueError):
            f.pair(3, 3)

    def test_invalid_side_and_unknown_anchor_rejected(self):
        for side, anchor in [("middle", 2), (RIGHT, 999)]:
            f, _, _ = self.initial(); p = f.pair(3, 4)
            with self.subTest(side=side), self.assertRaises((ValueError, KeyError)):
                f.backend.insert_boundary(p.pair_id, anchor, side)

    def test_split_explicitly_unimplemented_and_backend_unavailable_for_sorting(self):
        f, _, lid = self.initial(); b = f.backend
        for method in (b.split_value, b.adopt_split, b.split_pairs_at_value):
            with self.subTest(method=method.__name__), self.assertRaises(NotImplementedError):
                method(lid, 0)
        with self.assertRaisesRegex(TypeError, "partial backend"):
            SiblingBackendSpec(HeterogeneousFingerBackend)
        with self.assertRaises(ValueError):
            resolve_sibling_backend(b.backend_name)

    def test_auditor_rejects_structural_and_metadata_corruption(self):
        def corrupt(b, lid, kind):
            h = b._lists[lid]
            if kind == "rank": h.root.rank += 1
            elif kind == "red_root": h.root.red = True
            elif kind == "root_pointer": h.root.left = h.left_top
            elif kind == "root_cache": h.left_top = h.right_top
            elif kind == "size": h.size += 1
            elif kind == "key": h.root.key = 9999
            elif kind == "mass": h.left_top.span += 1
            elif kind == "rib_cycle": h.left_finger.left = h.left_finger
            elif kind == "role": h.left_finger.role = INTERIOR
            elif kind == "boundary": h.left_finger.handle.left_boundary = None
            elif kind == "identity": h.left_finger.handle.pair.end_index += 2
            elif kind == "owner_slot": h.owner.child_slots = ()
            elif kind == "stable_leaf": h.left_finger.handle.leaf = h.right_finger
            elif kind == "eager_owner": h.left_finger.handle.pair.parent_pair_id = -1
        for kind in ("rank", "red_root", "root_pointer", "root_cache", "size", "key", "mass",
                     "rib_cycle", "role", "boundary", "identity", "owner_slot", "stable_leaf", "eager_owner"):
            f, p, lid = self.initial(); b = f.backend
            for i in range(1, 24):
                new = f.pair(3*i, 3*i+1); b.insert_boundary(new.pair_id, p.pair_id, RIGHT); p = new
            corrupt(b, lid, kind)
            with self.subTest(kind=kind), self.assertRaises((RuntimeError, ValueError)):
                b.validate_invariants()

    def test_auditor_rejects_fixed_source_mutation(self):
        f, p, _ = self.initial()
        f.values[p.first_point_id] = -999
        with self.assertRaisesRegex(RuntimeError, "point source changed"):
            f.backend.validate_invariants()

    def test_pending_pair_is_only_allowed_in_explicit_partial_audit(self):
        f, _, _ = self.initial(); f.pair(3, 4)
        with self.assertRaisesRegex(RuntimeError, "unowned pair"):
            f.backend.validate_invariants()
        self.assertTrue(f.backend.validate_invariants(require_all_owned=False))


if __name__ == "__main__":
    unittest.main(verbosity=2)
