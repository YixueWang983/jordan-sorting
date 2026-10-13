"""Real-tree Jordan integration, prefix oracles and stage-failure regressions.

These are correctness/development checks, not performance qualification.
"""

import itertools
import unittest
from dataclasses import replace
from unittest.mock import patch

import paper_jordan as core
from certified_paper_jordan import certified_paper_jordan_sort
from heterogeneous_finger_backend import HeterogeneousFingerBackend as Tree
from oracle import oracle
from paper_execution_policy import PAPER_EXECUTION_POLICIES, MINIMAL_POLICY
from paper_jordan_sort import (
    paper_jordan_sort_valid, paper_jordan_diagnostics_valid,
)
from partial_sorted_list import SortedOrderList
from sibling_list_backend import OrdinarySiblingListBackend, SplitCommitResult


class HeterogeneousSortIntegrationTests(unittest.TestCase):
    values = [1, 2, 3, 4, 6, 7, 0, 5]

    def staged(self, values=(3, 2, 1, 4), mode="minimal", backend="heterogeneous_finger"):
        state = core.initialize_paper_jordan_state(values, mode, backend=backend)
        left = core.step1_select_predecessor_boundary(state, 4)
        right = core.step2_select_successor_boundary(state, 4)
        result = core.step3a_increasing(state, 4, left)
        return state, result, right

    def test_all_policies_execute_real_split_and_z1_output_adjustment(self):
        for values in (self.values, [-x for x in self.values]):
            self.assertTrue(oracle(values)["valid"])
            observed = []
            for policy in PAPER_EXECUTION_POLICIES.values():
                with self.subTest(values=values, policy=policy.name):
                    real_split = Tree.split_value
                    calls = []
                    def split(backend, *args, **kwargs):
                        ids = real_split(backend, *args, **kwargs)
                        calls.append(ids)
                        return ids
                    with patch.object(Tree, "split_value", split):
                        state = core._run_paper_jordan_state_values(
                            values, execution_policy=policy, backend="heterogeneous_finger"
                        )
                    self.assertIs(type(state.sibling_backend), Tree)
                    self.assertEqual(state.partial_order.to_list(), sorted(values))
                    self.assertGreater(len(calls), 0)
                    self.assertTrue(any(all(x is not None for x in ids) for ids in calls))
                    self.assertTrue(core.validate_paper_jordan_state(state))
                    self.assertIsNone(state.sibling_backend._pending_transfer)
                    self.assertIsNone(state.sibling_backend._pending_split)
                    if policy.count_operations:
                        self.assertEqual(len(calls), state.metrics["sibling_list_splits"])
                        self.assertGreater(state.metrics["z1_output_anchor_adjustments"], 0)
                    observed.append((state.sibling_backend.logical_snapshot(),
                                     state.sibling_backend.audit_snapshot(), state.stage_results))
            self.assertTrue(all(result == observed[0] for result in observed))

    def test_z1_boundary_adjustment_runs_on_both_sides_in_every_policy(self):
        for values in ([3, 2, 1, 4, 5], [-3, -2, -1, -4, -5]):
            self.assertTrue(oracle(values)["valid"])
            for policy in PAPER_EXECUTION_POLICIES.values():
                state = core._run_paper_jordan_state_values(
                    values, execution_policy=policy, backend="heterogeneous_finger"
                )
                self.assertEqual(state.partial_order.to_list(), sorted(values))
                selections = state.stage_results[5]
                self.assertTrue(any(selections[name].adjusted_for_z1 for name in
                                    ("step1_select_boundary_pair", "step2_select_boundary_pair")))
                self.assertTrue(core.validate_paper_jordan_state(state))

    def test_each_prefix_checks_output_structure_stable_handles_and_fresh_tree_replay(self):
        instances = []
        original_init = Tree.__init__
        def initialize(instance, *args, **kwargs):
            original_init(instance, *args, **kwargs)
            instances.append(instance)
        saved = {}
        prefixes = []
        def validate(state):
            backend = state.sibling_backend
            self.assertIs(type(backend), Tree)
            self.assertIsNone(backend._pending_transfer)
            self.assertIsNone(backend._pending_split)
            self.assertEqual(state.partial_order.to_list(), sorted(self.values[:state.processed_count]))
            for pair_id, pair in state.pairs.items():
                if pair.is_dummy:
                    continue
                handle = backend.pair_handle(pair_id)
                identity = (pair, handle, handle.leaf)
                if pair_id in saved:
                    self.assertTrue(all(a is b for a, b in zip(saved[pair_id], identity)))
                saved[pair_id] = identity
            self.assertTrue(core.validate_paper_jordan_state(state))
            prefixes.append(state.processed_count)
        with patch.object(Tree, "__init__", initialize):
            state = core._run_paper_jordan_state_values(
                self.values, backend="heterogeneous_finger", invariant_callback=validate
            )
        self.assertEqual(prefixes, list(range(3, len(self.values) + 1)))
        self.assertEqual(len(instances), 1 + len(prefixes))
        self.assertEqual(len({id(b) for b in instances}), len(instances))
        for replay in instances[1:]:
            self.assertIs(type(replay), Tree)
            self.assertIs(replay.execution_policy, state.execution_policy)
            self.assertIsNot(replay._nodes, instances[0]._nodes)
            self.assertIsNot(replay._lists, instances[0]._lists)
            self.assertIsNot(replay.pair_handle(2), instances[0].pair_handle(2))

    def test_public_routes_do_not_construct_ordinary_backend(self):
        with patch.object(OrdinarySiblingListBackend, "__init__", side_effect=AssertionError("fallback")):
            for values in ([], [1], [2, 1], [3, 1, 2], self.values):
                for call in (paper_jordan_sort_valid, certified_paper_jordan_sort):
                    self.assertEqual(call(values, backend="heterogeneous_finger"), sorted(values))
                result = paper_jordan_diagnostics_valid(values, backend="heterogeneous_finger")
                self.assertEqual(result["output"], sorted(values))
                self.assertTrue(result["invariants_valid"])
                self.assertEqual(result["backend_identity"][2], Tree.backend_name)

    def test_both_boundaries_are_required_before_registration_in_either_backend(self):
        for backend, increasing in itertools.product(("ordinary_list", "heterogeneous_finger"), (True, False)):
            values = [3, 2, 1, 4] if increasing else [-3, -2, -1, -4]
            state = core.initialize_paper_jordan_state(values, backend=backend)
            selection = (core.step1_select_predecessor_boundary if increasing else core.step2_select_successor_boundary)(state, 4)
            before = state.sibling_backend.audit_snapshot()
            call = core.step3a_increasing if increasing else core.step3a_decreasing
            with self.assertRaisesRegex(RuntimeError, "both Step 1/2"):
                call(state, 4, selection)
            self.assertEqual(state.sibling_backend.audit_snapshot(), before)
            self.assertNotIn(4, state.pairs)

    def test_pending_stage_queries_and_matching_adopt_restore_full_forest(self):
        state, insertion, boundary = self.staged()
        backend = state.sibling_backend
        source = insertion.transfer_source_list_id
        self.assertEqual(backend.boundary_list(boundary.pair_id, core.LEFT), source)
        self.assertEqual(backend.list_owner(source), insertion.parent_pair_id)
        self.assertIs(backend._pending_transfer[0], backend.pair_handle(4))
        for audit in (backend.validate_invariants, backend.audit_snapshot, backend.logical_snapshot,
                      backend.validate_iteration_complete):
            with self.assertRaisesRegex(RuntimeError, "staged transfer"):
                audit()
        real_adopt = backend.adopt_split
        def adopt(*args):
            self.assertIsNotNone(backend._pending_split)
            for action in (backend.validate_invariants, backend.validate_iteration_complete,
                           lambda: backend.list_size(source), lambda: backend.split_value(source, 3)):
                with self.assertRaisesRegex(RuntimeError, "pending split"):
                    action()
            return real_adopt(*args)
        with patch.object(backend, "adopt_split", adopt):
            result = core.step3b_increasing(state, 4, 4, boundary)
        self.assertTrue(result.performed)
        self.assertIsNone(backend._pending_transfer)
        self.assertIsNone(backend._pending_split)
        self.assertTrue(backend.validate_invariants())
        core.step3c_increasing(state, 4, 4)
        self.assertTrue(core.validate_paper_jordan_state(state))
        self.assertEqual(state.partial_order.to_list(), [1, 2, 3, 4])

    def test_wrong_owner_is_rejected_before_pair_registration(self):
        for backend in ("ordinary_list", "heterogeneous_finger"):
            state = core.initialize_paper_jordan_state([3, 2, 1, 4], backend=backend)
            left = core.step1_select_predecessor_boundary(state, 4)
            core.step2_select_successor_boundary(state, 4)
            before = state.sibling_backend.audit_snapshot()
            with patch.object(state.sibling_backend, "list_owner", return_value=-2):
                with self.assertRaisesRegex(RuntimeError, "another group"):
                    core.step3a_increasing(state, 4, left)
            self.assertEqual(state.sibling_backend.audit_snapshot(), before)

    def test_source_replacement_after_insertion_rejected_before_split(self):
        for backend in ("ordinary_list", "heterogeneous_finger"):
            state, insertion, boundary = self.staged(backend=backend)
            b = state.sibling_backend
            with patch.object(b, "boundary_list", return_value=insertion.sibling_list_id), patch.object(b, "split_pairs_at_value") as split:
                with self.assertRaisesRegex(RuntimeError, "transfer intent"):
                    core.step3b_increasing(state, 4, 4, boundary)
                split.assert_not_called()

    def test_source_owner_change_after_insertion_rejected_before_split(self):
        state, insertion, boundary = self.staged()
        b = state.sibling_backend
        with patch.object(b, "list_owner", return_value=-2), patch.object(b, "split_pairs_at_value") as split:
            with self.assertRaisesRegex(RuntimeError, "transfer intent"):
                core.step3b_increasing(state, 4, 4, boundary)
            split.assert_not_called()

    def test_forged_split_success_cannot_recover_output_with_pending_transfer(self):
        with patch.object(Tree, "split_pairs_at_value", return_value=SplitCommitResult(None, None, None)), patch.object(SortedOrderList, "to_list") as recover:
            with self.assertRaisesRegex(RuntimeError, "staged transfer"):
                paper_jordan_sort_valid([3, 2, 1, 4], execution_mode="minimal", backend="heterogeneous_finger")
            recover.assert_not_called()

    def test_adopt_failure_propagates_without_output_or_ordinary_retry(self):
        failure = RuntimeError("injected adopt failure")
        with patch.object(Tree, "adopt_split", side_effect=failure) as adopt, patch.object(SortedOrderList, "to_list") as recover, patch.object(OrdinarySiblingListBackend, "__init__") as ordinary:
            with self.assertRaises(RuntimeError) as caught:
                paper_jordan_sort_valid([3, 2, 1, 4], execution_mode="minimal", backend="heterogeneous_finger")
            self.assertIs(caught.exception, failure)
            adopt.assert_called_once()
            recover.assert_not_called()
            ordinary.assert_not_called()

    def test_replay_constructor_failure_has_no_fallback(self):
        state = core._run_paper_jordan_state_values(self.values, backend="heterogeneous_finger")
        with patch.object(Tree, "__init__", side_effect=RuntimeError("tree replay unavailable")), patch.object(OrdinarySiblingListBackend, "__init__") as ordinary:
            with self.assertRaisesRegex(RuntimeError, "tree replay unavailable"):
                core.validate_paper_jordan_state(state)
            ordinary.assert_not_called()

    def test_transfer_record_is_audited_even_without_trace(self):
        state = core._run_paper_jordan_state_values([3, 2, 1, 4], execution_policy=MINIMAL_POLICY, backend="heterogeneous_finger")
        stages = state.stage_results[4]
        stages["step3a_insert_pair"] = replace(stages["step3a_insert_pair"], transfer_source_list_id=None)
        with self.assertRaisesRegex(RuntimeError, "transfer intent"):
            core.validate_paper_jordan_state(state)

    def test_minimal_loop_does_not_materialize_or_enumerate_tree_registries(self):
        class NoEnumeration(dict):
            def reject(self, *args, **kwargs):
                raise AssertionError("normal path enumerated a tree registry")
            __iter__ = keys = values = items = reject
        initialize = core._initialize_paper_jordan_state_values
        def guarded(*args, **kwargs):
            state = initialize(*args, **kwargs)
            b = state.sibling_backend
            b._pairs = NoEnumeration(b._pairs)
            b._lists = NoEnumeration(b._lists)
            b._nodes = NoEnumeration(b._nodes)
            return state
        with patch.object(core, "_initialize_paper_jordan_state_values", guarded), patch.object(Tree, "validate_invariants", side_effect=AssertionError("full audit")), patch.object(Tree, "materialize_audit", side_effect=AssertionError("materialization")), patch.object(Tree, "audit_snapshot", side_effect=AssertionError("snapshot")):
            self.assertEqual(paper_jordan_sort_valid(self.values, execution_mode="minimal", backend="heterogeneous_finger"), sorted(self.values))

    def test_bounded_legal_permutations_each_backend_against_external_order(self):
        counts = {}
        for n in range(3, 7):
            counts[n] = 0
            for values in itertools.permutations(range(n)):
                if not oracle(values)["valid"]:
                    continue
                counts[n] += 1
                for backend in ("ordinary_list", "heterogeneous_finger"):
                    with self.subTest(values=values, backend=backend):
                        result = paper_jordan_diagnostics_valid(values, backend=backend)
                        self.assertEqual(result["output"], list(range(n)))
                        self.assertTrue(result["invariants_valid"])
        self.assertEqual(counts, {3: 6, 4: 16, 5: 50, 6: 144})


if __name__ == "__main__":
    unittest.main()
