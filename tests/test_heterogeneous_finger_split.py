"""Real split/adopt operation development checks; NOT full sorting acceptance.

Only the oracle stores lists. Every update uses production nodes and public
operations, including explicit staging of the Step 3(a) transfer frontier.
"""
import itertools
import random
import unittest
from unittest.mock import patch

from test_heterogeneous_finger_backend import Fixture
from heterogeneous_finger_backend import ExternalLeaf, InternalNode
from sibling_list_backend import LEFT, RIGHT, LOWER, UPPER
from paper_execution_policy import MINIMAL_POLICY, COUNTERS_ONLY_POLICY


def build(size, seed=0, *, order=None, family=UPPER, policy=MINIMAL_POLICY):
    f = Fixture(policy); b = f.backend
    pairs = [f.pair(100*i, 100*i+10, reverse=bool(i % 2), family=family) for i in range(size)]
    if order is None:
        rng = random.Random(seed)
        lo = hi = size//2
        order = [lo]
        while len(order) < size:
            if lo and (hi == size-1 or rng.randrange(2)):
                lo -= 1; order.append(lo)
            else:
                hi += 1; order.append(hi)
    lo = hi = order[0]
    lid = b.make_list(pairs[lo].pair_id, -1 if family == UPPER else -2)
    for i in order[1:]:
        side = LEFT if i < lo else RIGHT
        b.insert_boundary(pairs[i].pair_id, pairs[lo if side == LEFT else hi].pair_id, side)
        lo, hi = min(lo, i), max(hi, i)
    return f, lid, pairs


def stage_parent(f, lid, cut, side):
    """Make a REAL live pair in another group, explicitly awaiting transfer."""
    b = f.backend; header = b._lists[lid]
    low, high = header.left_finger.handle.low, header.right_finger.handle.high
    outer_low, outer_high = min(low, cut)-30, max(high, cut)+30
    if not header.owner.pair.is_dummy:
        outer_low = max(outer_low, (header.owner.low + min(low, cut))/2)
        outer_high = min(outer_high, (header.owner.high + max(high, cut))/2)
    other = [h for h in header.owner.child_slots if h is not header]
    if other:
        other_low, other_high = other[0].left_finger.handle.low, other[0].right_finger.handle.high
        if other_high < low:
            outer_low = max(outer_low, (other_high+low)/2)
        if high < other_low:
            outer_high = min(outer_high, (high+other_low)/2)
    family = header.owner.pair.family
    parent = f.pair(outer_low, cut, family=family) if side == LEFT else f.pair(cut, outer_high, family=family)
    if other:
        h = other[0]
        insertion_side = LEFT if b.pair_handle(parent.pair_id).low < h.left_finger.handle.low else RIGHT
        anchor = h.left_finger if insertion_side == LEFT else h.right_finger
        b.insert_boundary(parent.pair_id, anchor.handle.pair.pair_id, insertion_side, transfer_from=lid)
    else:
        b.make_list(parent.pair_id, header.owner.pair.pair_id, transfer_from=lid)
    return parent


class SplitAdoptTests(unittest.TestCase):
    def check(self, f, ids, expected, owners, stable):
        b = f.backend
        self.assertTrue(b.validate_invariants())
        groups = b.materialize_audit()
        for lid, pairs, owner in zip(ids, expected, owners):
            if not pairs:
                self.assertIsNone(lid)
                continue
            self.assertEqual(b.list_size(lid), len(pairs))
            self.assertEqual(b.list_owner(lid), owner)
            self.assertIn((owner, tuple(p.pair_id for p in pairs)), groups)
            self.assertEqual(b.boundary_list(pairs[0].pair_id, LEFT), lid)
            self.assertEqual(b.boundary_list(pairs[-1].pair_id, RIGHT), lid)
        for pair, handle, leaf, children in stable:
            self.assertIs(b.get_pair(pair.pair_id), pair)
            self.assertIs(b.pair_handle(pair.pair_id), handle)
            self.assertIs(handle.leaf, leaf)
            self.assertEqual(tuple(h.list_id for h in handle.child_slots), children)

    @staticmethod
    def stable(b, pairs):
        return [(p, b.pair_handle(p.pair_id), b.pair_handle(p.pair_id).leaf,
                 b.child_list_ids(p.pair_id)) for p in pairs]

    def split(self, f, lid, pairs, count, side):
        b = f.backend; old = b._lists[lid]; owner = old.owner.pair.pair_id
        if 0 < count < len(pairs):
            cut = (b.pair_handle(pairs[count-1].pair_id).high + b.pair_handle(pairs[count].pair_id).low)/2
        else:
            cut = b.pair_handle(pairs[0].pair_id).low-40 if count == 0 else b.pair_handle(pairs[-1].pair_id).high+40
        parent = stage_parent(f, lid, cut, side)
        stable = self.stable(b, pairs)
        leaves = {h.node_id: h for h in b._nodes.values() if isinstance(h, ExternalLeaf)}
        internal = sum(isinstance(n, InternalNode) for n in b._nodes.values())
        result = b.split_pairs_at_value(lid, cut, side, parent.pair_id)
        ids = (result.left_list_id, result.right_list_id)
        owners = (parent.pair_id, owner) if side == LEFT else (owner, parent.pair_id)
        self.assertFalse(old.live)
        self.assertNotIn(lid, b._lists)
        with self.assertRaises((KeyError, ValueError)):
            b.list_size(lid)
        self.check(f, ids, (pairs[:count], pairs[count:]), owners, stable)
        self.assertEqual(leaves, {h.node_id: h for h in b._nodes.values() if isinstance(h, ExternalLeaf)})
        self.assertEqual(sum(isinstance(n, InternalNode) for n in b._nodes.values()), internal-int(0 < count < len(pairs)))
        self.assertEqual(b.work.last_operation['work']['leaf_allocations'], 0)
        self.assertEqual(b.work.last_operation['work']['internal_allocations'], 0)
        return ids, parent, cut

    def test_singleton_empty_sides_and_retired_header(self):
        for count, side in itertools.product((0, 1), (LEFT, RIGHT)):
            with self.subTest(count=count, side=side):
                f, lid, pairs = build(1)
                self.split(f, lid, pairs, count, side)

    def test_lower_family_and_curve_endpoint_reversals(self):
        for side in (LEFT, RIGHT):
            f, lid, pairs = build(17, 3, family=LOWER)
            self.split(f, lid, pairs, 8, side)

    def test_counter_policy_reports_actual_observations_without_copying_claim(self):
        snapshots = []
        for policy in (MINIMAL_POLICY, COUNTERS_ONLY_POLICY):
            f, lid, pairs = build(17, 3, policy=policy); b = f.backend
            parent = stage_parent(f, lid, 760, LEFT)
            result = b.split_pairs_at_value(lid, 760, LEFT, parent.pair_id)
            if policy is MINIMAL_POLICY:
                self.assertIsNone(result.work)
            else:
                result.work.validate()
                self.assertEqual(result.work.split_items_copied, 0)
                self.assertEqual(result.work.split_items_transferred, 8)
                self.assertGreater(result.work.sibling_scan_checks, 0)
            snapshots.append((b.logical_snapshot(), b.audit_snapshot()))
        self.assertEqual(snapshots[0], snapshots[1])

    def test_bounded_all_cuts_and_three_tree_histories_both_acquired_sides(self):
        # 3,348 real split/adopt cases, not Jordan sorting inputs.
        for size in range(2, 33):
            for count, seed, side in itertools.product(range(size+1), range(3), (LEFT, RIGHT)):
                with self.subTest(size=size, count=count, seed=seed, side=side):
                    f, lid, pairs = build(size, seed)
                    self.split(f, lid, pairs, count, side)

    def test_join_repairs_right_red_red_even_when_left_child_is_red(self):
        f, lid, pairs = build(8, order=[4, 5, 6, 7, 3, 2, 1, 0])
        self.split(f, lid, pairs, 5, LEFT)
        self.assertGreater(f.backend.work.last_operation['work']['join_outer_repairs'], 0)

    def test_all_128_seven_insert_histories_then_all_nonempty_cuts(self):
        for sides in itertools.product((LEFT, RIGHT), repeat=7):
            order = [0]; lo = hi = 0
            for side in sides:
                if side == LEFT: lo -= 1; order.append(lo)
                else: hi += 1; order.append(hi)
            order = [i-lo for i in order]
            for count in range(1, 8):
                with self.subTest(sides=sides, count=count):
                    f, lid, pairs = build(8, order=order)
                    self.split(f, lid, pairs, count, LEFT if count%2 else RIGHT)

    def test_deletion_shortness_cases_and_mirrored_near_rotation(self):
        examples = {
            'deletion_propagations': (5, 0, 3),
            'deletion_far_rotations': (5, 1, 4),
            'deletion_red_sibling': (7, 2, 6),
        }
        for metric, (n, seed, count) in examples.items():
            f, lid, pairs = build(n, seed)
            self.split(f, lid, pairs, count, LEFT)
            self.assertGreater(f.backend.work.last_operation['work'][metric], 0)
        # Near-child rotations require shapes produced by previous splits.
        # Seed 39 reaches this branch on the third nested split. Mirror the
        # initial insertion order AND each cut/acquisition, not just the labels.
        for mirror in (False, True):
            rng = random.Random(39); lo = hi = 50; order = [50]
            while len(order) < 100:
                if lo and (hi == 99 or rng.randrange(2)):
                    lo -= 1; order.append(lo)
                else:
                    hi += 1; order.append(hi)
            if mirror: order = [99-i for i in order]
            f, lid, model = build(100, order=order); b = f.backend
            rng = random.Random(39); near = 0
            for step in range(3):
                count = rng.randrange(1, len(model)); side = rng.choice((LEFT, RIGHT))
                if mirror:
                    count = len(model)-count
                    side = RIGHT if side == LEFT else LEFT
                ids, _, _ = self.split(f, lid, model, count, side)
                near += b.work.last_operation['work']['deletion_near_rotations']
                lid = ids[0 if side == LEFT else 1]
                model = model[:count] if side == LEFT else model[count:]
            self.assertGreater(near, 0, mirror)

    def test_extremely_unequal_and_mirrored_splits(self):
        for count, side in itertools.product((1, 2, 3, 64, 129, 254, 256), (LEFT, RIGHT)):
            f, lid, pairs = build(257, 47)
            self.split(f, lid, pairs, count, side)

    def test_split_adopt_insert_both_sides_split_again_and_insert(self):
        for side in (LEFT, RIGHT):
            f, lid, pairs = build(32, 17); b = f.backend
            ids, _, _ = self.split(f, lid, pairs, 16, side)
            for out, model in zip(ids, (pairs[:16], pairs[16:])):
                for end in (LEFT, RIGHT, LEFT, RIGHT):
                    anchor = model[0 if end == LEFT else -1]
                    h = b.pair_handle(anchor.pair_id)
                    new = f.pair(h.low-8, h.low-6) if end == LEFT else f.pair(h.high+6, h.high+8)
                    self.assertEqual(b.insert_boundary(new.pair_id, anchor.pair_id, end), out)
                    model.insert(0, new) if end == LEFT else model.append(new)
                    self.check(f, (out,), (model,), (b.list_owner(out),), self.stable(b, model))
                # Retained group has an existing other child group. Stage using
                # real end insertion into that group, not an extra owner slot.
                fresh, _, _ = self.split(f, out, model, 10, side)
                for new_id, new_model in zip(fresh, (model[:10], model[10:])):
                    anchor = new_model[-1]; h = b.pair_handle(anchor.pair_id)
                    gap = min(1, (b._lists[new_id].owner.high-h.high)/3) if not b._lists[new_id].owner.pair.is_dummy else 1
                    new = f.pair(h.high+gap, h.high+2*gap)
                    b.insert_boundary(new.pair_id, anchor.pair_id, RIGHT)
                    new_model.append(new)
                    self.check(f, (new_id,), (new_model,), (b.list_owner(new_id),), self.stable(b, new_model))

    def test_existing_descendants_and_destination_child_group_are_preserved(self):
        for side in (LEFT, RIGHT):
            f, lid, pairs = build(12); b = f.backend
            for p in pairs:
                h = b.pair_handle(p.pair_id)
                child = f.pair(h.low+2, h.low+4)
                b.make_list(child.pair_id, p.pair_id)
                grandchild = f.pair(h.low+2.5, h.low+3)
                b.make_list(grandchild.pair_id, child.pair_id)
            stable = self.stable(b, pairs)
            cut = 560
            parent = stage_parent(f, lid, cut, side)
            child = f.pair(-20, -10) if side == LEFT else f.pair(1120, 1130)
            existing = b.make_list(child.pair_id, parent.pair_id)
            with self.assertRaisesRegex(RuntimeError, 'staged transfer'):
                b.validate_invariants()
            result = b.split_pairs_at_value(lid, cut, side, parent.pair_id)
            self.assertIn(existing, b.child_list_ids(parent.pair_id))
            owners = (parent.pair_id, -1) if side == LEFT else (-1, parent.pair_id)
            self.check(f, (result.left_list_id, result.right_list_id), (pairs[:6], pairs[6:]), owners, stable)

    def test_explicit_split_then_adopt_fences_incomplete_state(self):
        f, lid, pairs = build(10); b = f.backend
        parent = stage_parent(f, lid, 460, LEFT)
        ids = b.split_value(lid, 460)
        for call in (lambda: b.list_size(ids[0]), b.validate_invariants,
                     lambda: b.split_value(ids[0], 200), lambda: f.pair(-100,-90)):
            with self.assertRaisesRegex(RuntimeError, 'pending split'):
                call()
        b.adopt_split(-1, parent.pair_id, *ids, LEFT)
        self.check(f, ids, (pairs[:5], pairs[5:]), (parent.pair_id,-1), self.stable(b,pairs))
        with self.assertRaisesRegex(ValueError, 'no pending'):
            b.adopt_split(-1, parent.pair_id, *ids, LEFT)

    def test_repeated_random_nested_splits_and_updates(self):
        # Recurse into the acquired group, preserving every earlier sibling tree.
        for seed in range(6):
            f, lid, model = build(80, seed); b=f.backend; rng=random.Random(seed)
            for step in range(10):
                if len(model)<3: break
                side = rng.choice((LEFT,RIGHT)); count=rng.randrange(1,len(model))
                ids, parent, _ = self.split(f,lid,model,count,side)
                lid=ids[0 if side==LEFT else 1]
                model=model[:count] if side==LEFT else model[count:]
                anchor=model[-1]; h=b.pair_handle(anchor.pair_id)
                gap=min(0.1, (b._lists[lid].owner.high-h.high)/3)
                new=f.pair(h.high+gap,h.high+2*gap)
                b.insert_boundary(new.pair_id,anchor.pair_id,RIGHT);model.append(new)
                self.check(f,(lid,),(model,),(parent.pair_id,),self.stable(b,model))

    def test_normal_split_and_adopt_do_not_enumerate_registries_or_materialize(self):
        f,lid,pairs=build(129,2);b=f.backend;parent=stage_parent(f,lid,1260,LEFT)
        class NoEnumeration(dict):
            def __iter__(self): raise AssertionError('registry enumeration')
            def items(self): raise AssertionError('registry items')
            def values(self): raise AssertionError('registry values')
        b._pairs,b._lists,b._nodes=(NoEnumeration(b._pairs),NoEnumeration(b._lists),NoEnumeration(b._nodes))
        with patch.object(b,'_audit',side_effect=AssertionError('full audit')), \
             patch.object(b,'materialize_audit',side_effect=AssertionError('materialize')):
            result=b.split_pairs_at_value(lid,1260,LEFT,parent.pair_id)
        b._pairs,b._lists,b._nodes=(dict(b._pairs),dict(b._lists),dict(b._nodes))
        self.check(f,(result.left_list_id,result.right_list_id),(pairs[:13],pairs[13:]),(parent.pair_id,-1),self.stable(b,pairs))

    def test_cost_phases_partition_operation_and_audits_are_separate(self):
        f,lid,pairs=build(65);b=f.backend;parent=stage_parent(f,lid,3260,LEFT)
        b.split_pairs_at_value(lid,3260,LEFT,parent.pair_id)
        record=b.work.last_operation
        for key,total in record['work'].items():
            self.assertEqual(sum(p[key] for p in record['phases'].values()),total,key)
        for phase in ('search','detach','join','rebalance','ownership'):
            self.assertGreater(sum(record['phases'][phase].values()),0,phase)
        self.assertGreater(record['work']['size_writes'],0)
        self.assertGreater(record['work']['node_retirements'],0)
        self.assertEqual(record['work']['leaf_allocations'],0)
        self.assertEqual(record['work']['internal_allocations'],0)
        before=b.work.snapshot();b.validate_invariants();after=b.work.snapshot()
        self.assertEqual(before['operations'],after['operations'])
        self.assertGreater(after['audit']['node_visits'],before['audit']['node_visits'])

    def test_endpoint_adoption_work_does_not_grow_with_transferred_count(self):
        rows=[]
        for n in (8,32,128):
            f,lid,_=build(n);b=f.backend;parent=stage_parent(f,lid,100*n-40,LEFT)
            ids=b.split_value(lid,100*n-40)
            b.adopt_split(-1,parent.pair_id,*ids,LEFT)
            rows.append(b.work.last_operation['work'])
            b.validate_invariants()
        self.assertEqual(rows[0],rows[1]);self.assertEqual(rows[1],rows[2])


class SplitRejectionTests(unittest.TestCase):
    def test_straddling_or_touching_geometric_boundary_rejected(self):
        for cut in (400,405,410):
            f,lid,_=build(10);b=f.backend;parent=stage_parent(f,lid,460,LEFT)
            with self.subTest(cut=cut),self.assertRaisesRegex(ValueError,'straddles or touches'):
                b.split_pairs_at_value(lid,cut,LEFT,parent.pair_id)

    def test_mismatched_source_owner_outputs_parent_and_side(self):
        for kind in ('owner','outputs','parent','side'):
            f,lid,pairs=build(10);b=f.backend;parent=stage_parent(f,lid,460,LEFT)
            ids=b.split_value(lid,460)
            args=[-1,parent.pair_id,*ids,LEFT]
            if kind=='owner':args[0]=-2
            if kind=='outputs':args[2],args[3]=args[3],args[2]
            if kind=='parent':args[1]=pairs[0].pair_id
            if kind=='side':args[4]='middle'
            with self.subTest(kind=kind),self.assertRaises((ValueError,RuntimeError)):
                b.adopt_split(*args)

    def test_non_enclosing_parent_and_wrong_acquired_side_rejected(self):
        for side in (LEFT,RIGHT):
            f,lid,_=build(10);b=f.backend;parent=stage_parent(f,lid,460,side)
            ids=b.split_value(lid,460)
            with self.assertRaisesRegex(ValueError,'strictly enclose'):
                b.adopt_split(-1,parent.pair_id,*ids,RIGHT if side==LEFT else LEFT)

    def test_family_dummy_and_unowned_destination_rejected(self):
        for kind in ('family','dummy','unowned'):
            f,lid,_=build(10);b=f.backend
            if kind=='family':
                p=f.pair(-100,1000,family=LOWER);b.make_list(p.pair_id,-2)
                parent=p.pair_id
            elif kind=='unowned':parent=f.pair(-100,1000).pair_id
            else:parent=-2
            ids=b.split_value(lid,460)
            with self.subTest(kind=kind),self.assertRaises(ValueError):
                b.adopt_split(-1,parent,*ids,LEFT)

    def test_descendant_cannot_become_parent_and_empty_acquisition_cannot_target_source(self):
        for count in (0,5):
            f,lid,pairs=build(10);b=f.backend
            child=f.pair(2,4);b.make_list(child.pair_id,pairs[0].pair_id)
            ids=b.split_value(lid,100*count-40)
            target=child.pair_id if count else pairs[5].pair_id
            with self.assertRaises(ValueError):
                b.adopt_split(-1,target,*ids,LEFT)

    def test_stage_requires_correct_source_and_cannot_be_silently_abandoned(self):
        f,lid,_=build(10);b=f.backend;stage_parent(f,lid,460,LEFT)
        other=b.child_list_ids(-1)[0]
        with self.assertRaisesRegex(ValueError,'staged transfer source'):
            b.split_value(other,0)
        with self.assertRaisesRegex(RuntimeError,'staged transfer'):
            b.validate_invariants()

    def test_stale_boundary_injection_and_rank_size_corruption_after_split_rejected(self):
        for kind in ('boundary','rank','size','span'):
            f,lid,_=build(30);b=f.backend;old=b._lists[lid];parent=stage_parent(f,lid,1460,LEFT)
            result=b.split_pairs_at_value(lid,1460,LEFT,parent.pair_id);h=b._lists[result.left_list_id]
            if kind=='boundary':h.left_finger.handle.left_boundary=old
            elif kind=='rank':h.root.rank+=1
            elif kind=='size':h.size+=1
            else:h.left_top.span+=1
            with self.subTest(kind=kind),self.assertRaises((ValueError,KeyError,RuntimeError)):
                b.validate_invariants()


if __name__=='__main__':
    unittest.main(verbosity=2)
