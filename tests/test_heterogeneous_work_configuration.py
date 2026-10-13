"""Detailed-work off is a real execution path, independent of execution policy."""

from contextlib import ExitStack
import itertools
import unittest
from unittest.mock import patch

from heterogeneous_finger_backend import HeterogeneousFingerBackend as Tree, WorkLedger
from oracle import oracle
from paper_execution_policy import PAPER_EXECUTION_POLICIES, MINIMAL_POLICY, COUNTERS_ONLY_POLICY
import paper_jordan as core
from paper_jordan_sort import paper_jordan_sort_valid, paper_jordan_diagnostics_valid
from sibling_backend_contract import SiblingBackendSpec
from partial_sorted_list import SortedOrderList
from test_heterogeneous_finger_backend import Fixture


def choice(enabled):
    return SiblingBackendSpec(Tree, (("detailed_work", enabled),))


class DetailedWorkConfigurationTests(unittest.TestCase):
    values = [1, 2, 3, 4, 6, 7, 0, 5]

    def observations(self, state):
        return (state.partial_order.to_list(), state.sibling_backend.logical_snapshot(),
                state.sibling_backend.audit_snapshot(), state.stage_results,
                state.backend_work, state.metrics, state.trace)

    def test_all_policies_preserve_full_behavior_for_mirrored_real_splits(self):
        for values, policy in itertools.product((self.values, [-v for v in self.values], [3, 2, 1, 4, 5]),
                                                 PAPER_EXECUTION_POLICIES.values()):
            with self.subTest(values=values, mode=policy.name):
                states = [core._run_paper_jordan_state_values(
                    values, execution_policy=policy, backend=choice(enabled)) for enabled in (True, False)]
                for state in states:
                    self.assertEqual(state.partial_order.to_list(), sorted(values))
                    self.assertTrue(core.validate_paper_jordan_state(state))
                self.assertEqual(self.observations(states[0]), self.observations(states[1]))
                self.assertNotEqual(states[0].backend_identity, states[1].backend_identity)

    def test_off_never_enters_record_accounting_snapshot_or_report_builders(self):
        with ExitStack() as stack:
            for method in ("read", "write", "snapshot", "observe", "_observe", "_phase"):
                stack.enter_context(patch.object(WorkLedger, method, side_effect=AssertionError(method)))
            for policy in PAPER_EXECUTION_POLICIES.values():
                state = core._run_paper_jordan_state_values(
                    self.values, execution_policy=policy, backend=choice(False))
                self.assertEqual(state.partial_order.to_list(), sorted(self.values))
                self.assertTrue(core.validate_paper_jordan_state(state))
                ledger = state.sibling_backend.work
                self.assertIsNone(ledger.buckets)
                self.assertIsNone(ledger.phases)
                self.assertIsNone(ledger.last_operation)
                self.assertIsNone(ledger.active)
                self.assertIsNone(state.sibling_backend._split_observations)

    def test_minimal_off_has_no_lightweight_split_accumulator(self):
        split = Tree.split_value
        seen = []
        def inspect(backend, *args, **kwargs):
            seen.append(backend._split_observations)
            return split(backend, *args, **kwargs)
        with patch.object(Tree, "split_value", inspect):
            output = paper_jordan_sort_valid(self.values, "minimal", backend=choice(False))
        self.assertEqual(output, sorted(self.values))
        self.assertTrue(seen)
        self.assertTrue(all(value is None for value in seen))

    def test_counted_split_observations_still_match_enabled_ledger(self):
        split = Tree.split_pairs_at_value
        seen = []
        def inspect(backend, *args, **kwargs):
            result = split(backend, *args, **kwargs)
            work = backend.work.last_operation['work']
            self.assertEqual(result.work.sibling_scan_checks, work['comparisons'])
            self.assertEqual(result.work.split_items_scanned, work['leaf_checks'])
            seen.append(result)
            return result
        with patch.object(Tree, "split_pairs_at_value", inspect):
            core._run_paper_jordan_state_values(self.values, execution_policy=COUNTERS_ONLY_POLICY, backend=choice(True))
        self.assertTrue(seen)

    def test_replay_constructs_distinct_instances_with_the_same_off_option(self):
        original = Tree.__init__
        instances = []
        def construct(instance, *args, **kwargs):
            original(instance, *args, **kwargs)
            instances.append(instance)
        with patch.object(Tree, "__init__", construct):
            result = paper_jordan_diagnostics_valid(self.values, backend=choice(False))
        self.assertEqual(result['output'], sorted(self.values))
        self.assertEqual(len(instances), 1 + len(self.values) - 2)
        self.assertEqual(len({id(b) for b in instances}), len(instances))
        self.assertTrue(all(b.detailed_work is False for b in instances))
        self.assertTrue(all(b._nodes is not instances[0]._nodes for b in instances[1:]))

    def test_invalid_or_changed_configuration_is_rejected(self):
        for invalid in (0, 1, None, 'false', []):
            with self.subTest(invalid=invalid), self.assertRaisesRegex(TypeError, 'bool'):
                Tree(lambda i: i, detailed_work=invalid)
        b = Tree(lambda i: i, detailed_work=False)
        for target, field in ((b, 'detailed_work'), (b.work, 'enabled')):
            with self.assertRaises(AttributeError):
                setattr(target, field, True)
        state = core._run_paper_jordan_state_values(self.values, backend=choice(False))
        state.sibling_backend.work._enabled = True  # Deliberate private corruption.
        with self.assertRaisesRegex(RuntimeError, 'configuration'):
            core.validate_paper_jordan_state(state)

    def test_constructor_cannot_silently_ignore_work_configuration(self):
        original = Tree.__init__
        def wrong(instance, point_value, *, execution_policy, detailed_work):
            original(instance, point_value, execution_policy=execution_policy, detailed_work=not detailed_work)
        with patch.object(Tree, '__init__', wrong):
            with self.assertRaisesRegex(RuntimeError, 'configuration'):
                paper_jordan_sort_valid(self.values, backend=choice(False))

    def test_disabled_snapshot_does_not_report_false_zero_measurements(self):
        ledger = WorkLedger(False)
        ledger.add('comparisons', 100)
        self.assertIsNone(ledger.buckets)
        with self.assertRaisesRegex(RuntimeError, 'disabled'):
            ledger.snapshot()

    def test_bounded_all_legal_inputs_preserve_behavior_and_external_output(self):
        for n in range(3, 8):
            for values in itertools.permutations(range(n)):
                if not oracle(values)['valid']:
                    continue
                states = [core._run_paper_jordan_state_values(list(values), execution_policy=MINIMAL_POLICY,
                          backend=choice(enabled)) for enabled in (True, False)]
                for state in states:
                    self.assertEqual(state.partial_order.to_list(), list(range(n)))
                    self.assertTrue(core.validate_paper_jordan_state(state))
                self.assertEqual(self.observations(states[0]), self.observations(states[1]))

    def test_failed_adopt_has_same_exception_no_output_and_clears_observation_only(self):
        for enabled in (True, False):
            state = core.initialize_paper_jordan_state([3, 2, 1, 4], backend=choice(enabled))
            left = core.step1_select_predecessor_boundary(state, 4)
            right = core.step2_select_successor_boundary(state, 4)
            core.step3a_increasing(state, 4, left)
            failure = RuntimeError('injected adoption error')
            with patch.object(state.sibling_backend, 'adopt_split', side_effect=failure):
                with self.assertRaises(RuntimeError) as caught:
                    core.step3b_increasing(state, 4, 4, right)
            self.assertIs(caught.exception, failure)
            self.assertIsNone(state.sibling_backend._split_observations)
            self.assertIsNotNone(state.sibling_backend._pending_split)
            with self.assertRaisesRegex(RuntimeError, 'pending split'):
                state.sibling_backend.validate_iteration_complete()

    def test_skipped_adopt_never_allows_output_in_either_mode(self):
        for enabled in (True, False):
            with patch.object(Tree, 'adopt_split', return_value=None), patch.object(SortedOrderList, 'to_list') as recover:
                with self.assertRaisesRegex(RuntimeError, 'pending split'):
                    paper_jordan_sort_valid([3, 2, 1, 4], 'minimal', backend=choice(enabled))
                recover.assert_not_called()

    def test_local_boundary_and_completed_structure_errors_are_identical(self):
        for enabled in (True, False):
            f = Fixture()
            f.backend = Tree(f.values.__getitem__, execution_policy=MINIMAL_POLICY, detailed_work=enabled)
            from sibling_list_backend import PairRecord, UPPER, RIGHT
            f.backend.register_pair(PairRecord(-1, None, None, None, UPPER, is_dummy=True))
            b = f.backend
            first = f.pair(0, 1); lid = b.make_list(first.pair_id, -1)
            second = f.pair(3, 4); b.insert_boundary(second.pair_id, first.pair_id, RIGHT)
            new = f.pair(6, 7)
            with self.assertRaisesRegex(ValueError, 'boundary'):
                b.insert_boundary(new.pair_id, first.pair_id, RIGHT)
            b._lists[lid].root.rank += 1
            with self.assertRaises(RuntimeError):
                b.validate_invariants(require_all_owned=False)


if __name__ == '__main__':
    unittest.main()
