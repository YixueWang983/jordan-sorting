"""Representation and locality refinement checks; bounded evidence, not timing."""
import itertools
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'tests'), str(ROOT/'experiments')]
from finger_refinement_model import check_records, check_run, decode_tree, next_plan
from heterogeneous_finger_backend import HeterogeneousFingerBackend as Tree, ExternalLeaf
from heterogeneous_finger_split import TreeOperations
from oracle import oracle
from paper_execution_policy import MINIMAL_POLICY, CHECKED_POLICY
from probe_finger_cost_lemmas import forms, build_down
from sibling_backend_contract import SiblingBackendSpec
from sibling_list_backend import LEFT, RIGHT
from test_heterogeneous_finger_backend import Fixture
from validate_finger_middle_splits import values_for

TREE_OFF = SiblingBackendSpec(Tree, (('detailed_work', False),))


def component(form, fixture):
    piece = build_down(form, fixture)
    # The cost-probe shape builder allocates leaves without a list/header.
    # Bind their handles once, just as make_list/insert do for production leaves.
    for node in fixture.backend._nodes.values():
        if isinstance(node, ExternalLeaf):
            node.handle.leaf = node
    return piece


class RepresentationRefinementTests(unittest.TestCase):
    def test_orientation_round_trip_all_colored_shapes_through_ten_leaves(self):
        count = 0
        for n in range(1, 11):
            for form in forms(n):
                f = Fixture()
                ops = TreeOperations(f.backend)
                down = component(form, f)
                ops.color_rank(down.root, False)  # fingers' documented normalization
                shape, leaves, nodes = decode_tree(down, downward=True)
                oriented = ops.fingers(down)
                self.assertEqual(decode_tree(oriented), (shape, leaves, nodes))
                restored = ops.rooted_component(oriented, LEFT, oriented.root, n, oriented.right_finger.key)
                self.assertEqual(decode_tree(restored, downward=True), (shape, leaves, nodes))
                count += 1
        self.assertGreater(count, 100)
        print(json.dumps({'check':'orientation_round_trip', 'colored_shapes':count, 'max_leaves':10}))

    def test_actual_finger_split_all_black_root_shapes_and_cuts_through_nine_leaves(self):
        counts = {}; cases = 0
        for n in range(1, 10):
            for form in forms(n):
                if form[0]:
                    continue
                for cut in range(n+1):
                    f = Fixture(); ops = TreeOperations(f.backend)
                    piece = ops.fingers(component(form, f))
                    _, old_leaves, _ = decode_tree(piece)
                    with f.backend.work.observe('operations', 'refinement_split'):
                        left, right = ops.split(piece, 10*cut-5)
                    result_leaves, result_nodes = [], set()
                    for output, expected in ((left, old_leaves[:cut]), (right, old_leaves[cut:])):
                        if output is None:
                            self.assertFalse(expected)
                            continue
                        _, leaves, nodes = decode_tree(output)
                        self.assertEqual(leaves, expected)
                        self.assertFalse(result_nodes.intersection(nodes))
                        result_nodes.update(nodes); result_leaves.extend(leaves)
                    self.assertEqual(tuple(result_leaves), old_leaves)
                    self.assertEqual(result_nodes, {id(node) for node in f.backend._nodes.values()})
                    for name, value in f.backend.work.buckets['operations'].items():
                        counts[name] = counts.get(name, 0) + value
                    cases += 1
        self.assertGreater(cases, 300)
        for name in ('deletion_red_sibling', 'deletion_near_rotations', 'deletion_far_rotations',
                     'deletion_propagations', 'left_rotations', 'right_rotations'):
            self.assertGreater(counts[name], 0, name)
        print(json.dumps({'check':'real_finger_split', 'shape_cut_cases':cases, 'max_leaves':9,
                          'repair_branch_counts':{k:counts[k] for k in
                          ('deletion_red_sibling','deletion_near_rotations','deletion_far_rotations',
                           'deletion_propagations','left_rotations','right_rotations')}}))

    def test_decoder_rejects_corrupted_reverse_pointer(self):
        f = Fixture(); ops = TreeOperations(f.backend)
        h = ops.fingers(component(forms(4)[0], f))
        h.left_finger.left = h.left_finger
        with self.assertRaisesRegex(AssertionError, 'broken reverse chain'):
            decode_tree(h)

    def test_decoder_rejects_rib_span_as_full_subtree_size(self):
        f = Fixture(); ops = TreeOperations(f.backend)
        h = ops.fingers(component(forms(8)[0], f))
        h.left_top.span += 1
        with self.assertRaisesRegex(AssertionError, 'role-sensitive span'):
            decode_tree(h)

    def test_decoder_rejects_wrong_root_child_cache(self):
        f = Fixture(); ops = TreeOperations(f.backend)
        h = ops.fingers(component(forms(4)[0], f))
        h.left_top = h.right_top
        with self.assertRaises(AssertionError):
            decode_tree(h)


class LocalityRefinementTests(unittest.TestCase):
    def test_every_legal_permutation_through_seven_both_backends(self):
        counts = {}
        for n in range(3, 8):
            counts[n] = 0
            for values in itertools.permutations(range(n)):
                if not oracle(values)['valid']:
                    continue
                counts[n] += 1
                for backend in ('ordinary_list', TREE_OFF):
                    with self.subTest(values=values, backend=str(backend)):
                        check_run(values, backend, MINIMAL_POLICY)
        self.assertEqual(counts, {3:6, 4:16, 5:50, 6:144, 7:462})

    def test_fixed_z1_cases_both_directions_and_checked_policy(self):
        counts = {'z1_boundary':0, 'z1_output':0, 'both_nonempty':0}
        for values in ([1,2,3,4,6,7,0,5], [3,2,1,4,5]):
            for mirror in (False, True):
                v = [-x for x in values] if mirror else values
                for backend in ('ordinary_list', TREE_OFF):
                    state, result = check_run(v, backend, CHECKED_POLICY)
                    for k in counts:
                        counts[k] += result.get(k,0)
        self.assertTrue(all(counts.values()))

    def test_middle_splits_parity_direction_and_finite_owners(self):
        for n, k, mirror in itertools.product((128,129), (3,7,19), (False,True)):
            values = values_for(n,k,mirror)
            self.assertTrue(oracle(values)['valid'])
            for backend in ('ordinary_list', TREE_OFF):
                _, counts = check_run(values, backend, MINIMAL_POLICY)
                self.assertGreater(counts['finite_owner'], 0)
                self.assertGreater(counts['both_nonempty'], 0)

    def test_exact_partition_rejects_merged_groups_even_with_same_members(self):
        values = [1,2,3,4,6,7,0,5]
        state, _ = check_run(values, TREE_OFF, MINIMAL_POLICY)
        records = list(state.sibling_backend.logical_snapshot()[1])
        index = next(i for i,r in enumerate(records) if len(r[7])==2)
        row = records[index]
        records[index] = (*row[:7], (tuple(c for g in row[7] for c in g),))
        with self.assertRaisesRegex(AssertionError, 'exact geometric forest/group mismatch'):
            check_records(values, len(values), records)


if __name__ == '__main__':
    unittest.main()
