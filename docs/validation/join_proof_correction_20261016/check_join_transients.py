"""Focused proof-example checks using unchanged production nodes and methods.

No sorting, qualification or timing campaign is run. Builders are existing
test fixtures; the observations below independently traverse downward fields.
"""
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

if sys.flags.optimize:
    raise RuntimeError('Run evidence checks without Python optimization')
ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / p) for p in ('src', 'tests', 'experiments')]
from probe_finger_cost_lemmas import Fixture, build_down as fixture_build_down
from heterogeneous_finger_backend import ExternalLeaf, InternalNode, INTERIOR
from heterogeneous_finger_split import TreeOperations

EVENTS = []
LEAF = (False, 0, None, None)


def build_down(form, fixture, offset=0):
    piece = fixture_build_down(form, fixture, offset)
    # The historical detached-shape builder does not populate this backlink.
    # Establish it as fixture setup, before observing any production operation.
    stack = [piece.root]
    while stack:
        node = stack.pop()
        if isinstance(node, ExternalLeaf):
            assert node.handle.leaf is None
            node.handle.leaf = node
        else:
            stack.extend((node.left, node.right))
    return piece


def shape(red, left, right):
    if left[1] != right[1]:
        raise ValueError('fixture black heights differ')
    return (red, left[1] + int(not red), left, right)


def inspect(root):
    """Return identities and red-red edges; validate all other downward fields."""
    seen, edges, leaves = set(), [], []
    def visit(node):
        if id(node) in seen:
            raise AssertionError('shared/cyclic downward node')
        seen.add(id(node))
        if isinstance(node, ExternalLeaf):
            assert not node.red and node.rank == 0 and node.span == 1
            assert node.handle.leaf is node
            leaves.append((node, node.handle, node.handle.pair))
            return [node.key], 0
        assert node.role == INTERIOR
        lv, lr = visit(node.left); rv, rr = visit(node.right)
        assert lr == rr and node.rank == lr + int(not node.red)
        assert node.span == len(lv) + len(rv)
        assert node.key == lv[-1] and lv[-1] < rv[0]
        for child in (node.left, node.right):
            if node.red and child.red:
                edges.append((node, child))
        return lv + rv, node.rank
    values, rank = visit(root)
    return dict(values=values, rank=rank, edges=edges, leaves=leaves)


class JoinTransientChecks(unittest.TestCase):
    def connector(self, f):
        b = f.backend
        node = InternalNode(b.work, b._node_id(), INTERIOR, True, 0, 0, 0)
        b._store(b._nodes, node.node_id, node)
        return node

    def joined(self, left_form, right_form, name, *, expected_side=None):
        f = Fixture(); b = f.backend
        left = build_down(left_form, f)
        right = build_down(right_form, f, left.size)
        original = inspect(left.root)['leaves'] + inspect(right.root)['leaves']
        before_ranks = [p.root.rank + int(p.root.red) for p in (left, right)]
        observations = []
        production_balance = TreeOperations.balance_down
        def observe(ops, node):
            was_red, rank = node.red, node.rank
            result = production_balance(ops, node)
            state = inspect(result)
            assert state['rank'] == rank
            if not was_red:
                assert not state['edges']
            elif state['edges']:
                assert len(state['edges']) == 1
                parent, child = state['edges'][0]
                assert parent is result and child in (result.left, result.right)
                assert not child.left.red and not child.right.red
                observations.append('left' if child is result.left else 'right')
            return result
        with patch.object(TreeOperations, 'balance_down', observe):
            result = TreeOperations(b).join_down(left, right, self.connector(f))
        final = inspect(result.root)
        self.assertFalse(result.root.red)
        self.assertFalse(final['edges'])
        self.assertEqual(final['leaves'], original)
        self.assertEqual(final['values'], list(range(0, 10 * result.size, 10)))
        self.assertEqual(result.size, len(original))
        self.assertEqual(result.maximum, final['values'][-1])
        self.assertLessEqual(max(before_ranks), final['rank'])
        self.assertLessEqual(final['rank'], max(before_ranks) + 1)
        if expected_side:
            self.assertEqual(observations, [expected_side])
        EVENTS.append(dict(case=name, transient_sides=observations,
                           values=final['values'], normalized_inputs=before_ranks,
                           result_rank=final['rank'], stable_leaf_handle_pair=True))

    def test_right_red_root_transmission(self):
        self.joined(shape(False, LEAF, shape(True, LEAF, LEAF)), LEAF,
                    'review_example_RR', expected_side='right')

    def test_left_red_root_transmission(self):
        self.joined(LEAF, shape(False, shape(True, LEAF, LEAF), LEAF),
                    'review_example_LL', expected_side='left')

    def test_all_four_black_root_repairs(self):
        red = shape(True, LEAF, LEAF)
        cases = {
            'LL': shape(False, shape(True, red, LEAF), LEAF),
            'LR': shape(False, shape(True, LEAF, red), LEAF),
            'RR': shape(False, LEAF, shape(True, LEAF, red)),
            'RL': shape(False, LEAF, shape(True, red, LEAF)),
        }
        for name, form in cases.items():
            with self.subTest(branch=name):
                f = Fixture(); piece = build_down(form, f)
                before = inspect(piece.root)
                self.assertEqual(len(before['edges']), 1)
                node = TreeOperations(f.backend).balance_down(piece.root)
                after = inspect(node)
                self.assertEqual(after['leaves'], before['leaves'])
                self.assertEqual(after['rank'], before['rank'])
                self.assertFalse(after['edges'])
                self.assertTrue(node.red)
                self.assertFalse(node.left.red or node.right.red)
                EVENTS.append(dict(case=name, internal_valid=True, rank=after['rank']))

    def test_black_root_no_repair(self):
        self.direct_no_repair(False)

    def test_red_root_no_conflict(self):
        self.direct_no_repair(True)

    def direct_no_repair(self, red):
        f = Fixture(); piece = build_down(shape(red, LEAF, LEAF), f)
        original = inspect(piece.root)
        result = TreeOperations(f.backend).balance_down(piece.root)
        self.assertIs(result, piece.root)
        self.assertEqual(inspect(result), original)
        EVENTS.append(dict(case='red_no_conflict' if red else 'black_no_repair',
                           internal_valid=True))

    def test_blackening_of_two_red_input_roots(self):
        self.joined(shape(True, LEAF, LEAF), shape(True, LEAF, LEAF), 'red_inputs')

    def test_empty_sides_retire_connector_without_blackening(self):
        for empty_left in (True, False):
            with self.subTest(empty_left=empty_left):
                f = Fixture(); piece = build_down(shape(True, LEAF, LEAF), f)
                before = inspect(piece.root); conn = self.connector(f)
                left, right = (None, piece) if empty_left else (piece, None)
                result = TreeOperations(f.backend).join_down(left, right, conn)
                self.assertIs(result, piece)
                self.assertEqual(inspect(result.root), before)
                self.assertNotIn(conn.node_id, f.backend._nodes)
                EVENTS.append(dict(case='empty_left' if empty_left else 'empty_right',
                                   red_root_preserved=True, connector_retired=True))


if __name__ == '__main__':
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(JoinTransientChecks))
    report = dict(scope='focused_production_join_transients_not_sorting_qualification',
                  tests_run=result.testsRun, failures=len(result.failures),
                  errors=len(result.errors), skipped=len(result.skipped), cases=EVENTS)
    Path(__file__).with_name('join_transient_results.json').write_text(
        json.dumps(report, indent=2) + '\n')
    sys.exit(0 if result.wasSuccessful() and not result.skipped else 1)
