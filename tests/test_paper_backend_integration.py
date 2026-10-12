"""Production routing/access regressions. Fixtures below are NOT tree backends."""

import itertools
import sys
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from certified_paper_jordan import certified_paper_jordan_sort
from oracle import oracle
from paper_execution_policy import PAPER_EXECUTION_POLICIES, MINIMAL_POLICY
from paper_jordan import (
    initialize_paper_jordan_state, validate_paper_jordan_state,
    step3c_increasing,
)
from paper_jordan_sort import (
    _run_paper_jordan_valid, paper_jordan_sort_valid,
    paper_jordan_diagnostics_valid,
)
from sibling_backend_contract import SiblingBackendSpec, SplitWork
from sibling_list_backend import OrdinarySiblingListBackend, PairRecord


class GeometryOnlyPair(PairRecord):
    """Reject core access to ordinary storage fields on the stable public pair."""

    def __getattribute__(self, name):
        if name in ("parent_pair_id", "sibling_list_id", "child_sibling_list_ids"):
            raise AssertionError(f"core read ordinary representation: {name}")
        return super().__getattribute__(name)


class RoutedOrdinaryFixture:
    """Hide ordinary storage behind the actual production interface.

    Owns separate internal ordinary PairRecords; public records carry geometry
    only. This tests representation independence and routing, not efficiency.
    """

    backend_name = "test_routed_ordinary"
    audit_schema = "test-routed-ordinary-v1"
    metrics_schema = OrdinarySiblingListBackend.metrics_schema
    instances = []

    def __init__(self, point_value, execution_policy, list_id_start=101):
        self.inner = OrdinarySiblingListBackend(point_value, execution_policy)
        self.inner._next_list_id = list_id_start
        self.execution_policy = execution_policy
        self.list_id_start = list_id_start
        self.public_pairs = {}
        self.split_calls = 0
        self.boundaries = []
        type(self).instances.append(self)

    def register_pair(self, pair):
        self.inner.register_pair(PairRecord(
            pair.pair_id, pair.end_index, pair.first_point_id,
            pair.second_point_id, pair.family, is_dummy=pair.is_dummy,
        ))
        self.public_pairs[pair.pair_id] = pair
        pair.__class__ = GeometryOnlyPair
        return pair.pair_id

    def get_pair(self, pair_id):
        return self.public_pairs[pair_id]

    def point_value(self, point_id):
        return self.inner.point_value(point_id)

    def registered_pair_ids(self):
        return tuple(self.public_pairs)

    def validate_live_pair(self, pair_id):
        self.inner.validate_live_pair(pair_id)
        return self.get_pair(pair_id)

    def validate_dummy_ownership(self, pair_id):
        return self.inner.validate_dummy_ownership(pair_id)

    def boundary_list(self, pair_id, side):
        list_id = self.inner.boundary_list(pair_id, side)
        self.boundaries.append((pair_id, side, list_id))
        return list_id

    def list_owner(self, list_id):
        return self.inner.list_owner(list_id)

    def list_size(self, list_id):
        return self.inner.list_size(list_id)

    def child_list_ids(self, pair_id):
        return self.inner.child_list_ids(pair_id)

    def extreme_child(self, pair_id, side):
        pair = self.inner.extreme_child(pair_id, side)
        return None if pair is None else self.get_pair(pair.pair_id)

    def make_list(self, pair_id, owner):
        return self.inner.make_list(pair_id, owner)

    def insert_boundary(self, pair_id, anchor, side):
        return self.inner.insert_boundary(pair_id, anchor, side)

    def split_pairs_at_value(self, *args, **kwargs):
        self.split_calls += 1
        return self.inner.split_pairs_at_value(*args, **kwargs)

    def validate_invariants(self):
        return self.inner.validate_invariants()

    def logical_snapshot(self):
        return self.inner.logical_snapshot()

    def audit_snapshot(self):
        return self.inner.audit_snapshot()


class SyntheticWorkFixture(RoutedOrdinaryFixture):
    metrics_schema = "test-synthetic-observations-not-cost-evidence-v1"

    def split_pairs_at_value(self, *args, **kwargs):
        result = super().split_pairs_at_value(*args, **kwargs)
        if self.execution_policy.count_operations:
            return replace(result, work=SplitWork(17, 19, 23, 29))
        return result


class PaperBackendIntegrationTests(unittest.TestCase):
    values = [1, 2, 3, 4, 6, 7, 0, 5]

    def setUp(self):
        RoutedOrdinaryFixture.instances = []
        self.spec = SiblingBackendSpec(
            RoutedOrdinaryFixture, (("list_id_start", 101),)
        )

    def test_all_modes_sort_with_hidden_representation_and_nonzero_splits(self):
        for mode, policy in PAPER_EXECUTION_POLICIES.items():
            for values in (self.values, [-x for x in self.values]):
                with self.subTest(mode=mode, values=values):
                    self.assertTrue(oracle(values)["valid"])
                    state = _run_paper_jordan_valid(
                        list(values), execution_policy=policy, backend=self.spec
                    )
                    self.assertEqual(state.partial_order.to_list(), sorted(values))
                    self.assertGreater(state.sibling_backend.split_calls, 0)
                    self.assertTrue(validate_paper_jordan_state(state))
                    self.assertEqual(state.initial_sibling_list_ids, (101, 102))
                    ordinary = _run_paper_jordan_valid(list(values), execution_policy=policy)
                    self.assertEqual(state.sibling_backend.logical_snapshot(),
                                     ordinary.sibling_backend.logical_snapshot())
                    self.assertEqual(state.metrics, {
                        **ordinary.metrics,
                        **({"invariant_checks": 1} if policy.count_operations else {}),
                    })

    def test_public_sort_diagnostics_and_certified_wrapper_forward_selection(self):
        for call in (paper_jordan_sort_valid, certified_paper_jordan_sort):
            RoutedOrdinaryFixture.instances.clear()
            self.assertEqual(call(self.values, backend=self.spec), sorted(self.values))
            self.assertEqual(len(RoutedOrdinaryFixture.instances), 1)
        RoutedOrdinaryFixture.instances.clear()
        result = paper_jordan_diagnostics_valid(self.values, backend=self.spec)
        self.assertEqual(result["output"], sorted(self.values))
        self.assertEqual(result["backend_identity"], self.spec.identity)
        instances = RoutedOrdinaryFixture.instances
        self.assertEqual(len(instances), 1 + len(self.values) - 2)
        self.assertEqual(len({id(instance) for instance in instances}), len(instances))
        self.assertTrue(all(type(instance) is RoutedOrdinaryFixture for instance in instances))
        self.assertTrue(all(instance.list_id_start == 101 for instance in instances))
        self.assertTrue(all(instance is not instances[0] for instance in instances[1:]))
        for replay in instances[1:]:
            self.assertIsNot(replay.inner._lists, instances[0].inner._lists)
            self.assertIsNot(replay.get_pair(2), instances[0].get_pair(2))

    def test_explicit_initialization_keeps_spec_and_fresh_replay(self):
        state = initialize_paper_jordan_state(self.values, backend=self.spec)
        self.assertIs(state.backend_spec, self.spec)
        self.assertTrue(validate_paper_jordan_state(state))
        self.assertEqual(len(RoutedOrdinaryFixture.instances), 2)

    def test_missing_backend_rejected_even_for_empty_or_small_inputs(self):
        for values in ([], [1], [2, 1], self.values):
            for call in (paper_jordan_sort_valid, paper_jordan_diagnostics_valid,
                         certified_paper_jordan_sort):
                with self.subTest(values=values, call=call):
                    with self.assertRaisesRegex(ValueError, "unavailable"):
                        call(values, backend="heterogeneous_finger")

    def test_small_diagnostics_identify_selection_without_constructing_state(self):
        result = paper_jordan_diagnostics_valid([2, 1], backend=self.spec)
        self.assertEqual(result["output"], [1, 2])
        self.assertEqual(result["backend_identity"], self.spec.identity)
        self.assertEqual(RoutedOrdinaryFixture.instances, [])

    def test_replay_constructor_failure_propagates_without_fallback(self):
        state = _run_paper_jordan_valid(self.values, backend=self.spec)
        with patch.object(RoutedOrdinaryFixture, "__init__",
                          side_effect=RuntimeError("replay unavailable")):
            with self.assertRaisesRegex(RuntimeError, "replay unavailable"):
                validate_paper_jordan_state(state)

    def test_replay_rejects_reusing_live_backend_instance(self):
        class CachedFixture(RoutedOrdinaryFixture):
            cached = None

            def __new__(cls, *args, **kwargs):
                if cls.cached is None:
                    cls.cached = super().__new__(cls)
                return cls.cached

            def __init__(self, *args, **kwargs):
                if not hasattr(self, "inner"):
                    super().__init__(*args, **kwargs)

        state = _run_paper_jordan_valid(
            self.values, backend=SiblingBackendSpec(CachedFixture)
        )
        before = state.sibling_backend.audit_snapshot()
        with self.assertRaisesRegex(RuntimeError, "fresh backend"):
            validate_paper_jordan_state(state)
        self.assertEqual(state.sibling_backend.audit_snapshot(), before)

    def test_constructor_rejects_different_type_instead_of_silent_fallback(self):
        class BadFactory(RoutedOrdinaryFixture):
            def __new__(cls, point_value, execution_policy):
                return OrdinarySiblingListBackend(point_value, execution_policy)

        with self.assertRaisesRegex(RuntimeError, "different backend type"):
            paper_jordan_sort_valid(self.values, backend=SiblingBackendSpec(BadFactory))

    def test_mutable_or_incomplete_backend_specs_are_rejected(self):
        with self.assertRaisesRegex(TypeError, "required operation"):
            SiblingBackendSpec(object)
        for options in ([('list_id_start', 1)], (("x", []),),
                        (("x", 1), ("x", 2)), (("execution_policy", "minimal"),)):
            with self.subTest(options=options):
                with self.assertRaises((TypeError, ValueError)):
                    SiblingBackendSpec(RoutedOrdinaryFixture, options)

    def test_state_rejects_changed_backend_config_or_schema(self):
        for mutation in ("config", "schema", "identity"):
            with self.subTest(mutation=mutation):
                state = _run_paper_jordan_valid(self.values, backend=self.spec)
                if mutation == "config":
                    state.backend_spec = SiblingBackendSpec(
                        RoutedOrdinaryFixture, (("list_id_start", 201),)
                    )
                elif mutation == "schema":
                    state.sibling_backend.audit_schema = "incompatible"
                else:
                    state.backend_identity = ("forged",)
                with self.assertRaisesRegex(RuntimeError, "identity|schema"):
                    validate_paper_jordan_state(state)

    def test_split_metrics_are_backend_reported_not_inferred_from_sizes(self):
        spec = SiblingBackendSpec(SyntheticWorkFixture)
        result = paper_jordan_diagnostics_valid(self.values, backend=spec)
        splits = result["metrics"]["sibling_list_splits"]
        self.assertGreater(splits, 0)
        for name, value in SplitWork(17, 19, 23, 29).items():
            self.assertEqual(result["metrics"][name], splits * value)
        self.assertIn(SyntheticWorkFixture.metrics_schema, result["backend_identity"])

    def test_invalid_or_missing_backend_work_is_rejected(self):
        for work in (None, SplitWork(-1, 1, 1, 1), SplitWork(True, 1, 1, 1)):
            class BadWork(RoutedOrdinaryFixture):
                def split_pairs_at_value(self, *args, **kwargs):
                    return replace(super().split_pairs_at_value(*args, **kwargs), work=work)

            with self.subTest(work=work):
                with self.assertRaisesRegex(RuntimeError, "observations|observation"):
                    paper_jordan_sort_valid(self.values, backend=SiblingBackendSpec(BadWork))

    def test_minimal_path_never_materializes_audit_or_discards_stage_guards(self):
        with patch.object(RoutedOrdinaryFixture, "logical_snapshot",
                          side_effect=AssertionError("logical materialization")), patch.object(
                              RoutedOrdinaryFixture, "audit_snapshot",
                              side_effect=AssertionError("physical materialization")), patch.object(
                                  RoutedOrdinaryFixture, "validate_invariants",
                                  side_effect=AssertionError("complete audit")):
            state = _run_paper_jordan_valid(
                self.values, execution_policy=MINIMAL_POLICY, backend=self.spec
            )
            self.assertEqual(state.partial_order.to_list(), sorted(self.values))
            self.assertEqual(state.backend_work, {})
            self.assertEqual(state.trace, [])
            self.assertEqual(len(state.stage_results), len(self.values) - 3)
            initial = initialize_paper_jordan_state(
                self.values, execution_mode="minimal", backend=self.spec
            )
            with self.assertRaisesRegex(RuntimeError, "Step 3\\(a\\)"):
                step3c_increasing(initial, 4, 4)

    def test_backend_work_forgery_rejected_even_without_trace(self):
        state = _run_paper_jordan_valid(
            self.values, execution_policy=PAPER_EXECUTION_POLICIES["counters_only"],
            backend=self.spec,
        )
        iteration = next(iter(state.backend_work))
        old = state.backend_work[iteration]
        state.backend_work[iteration] = replace(old, split_items_copied=old.split_items_copied + 1)
        state.metrics["split_items_copied"] += 1
        with self.assertRaisesRegex(RuntimeError, "deterministic replay"):
            validate_paper_jordan_state(state)

    def test_bounded_valid_permutations_through_geometry_only_interface(self):
        checked = 0
        for size in range(3, 7):
            for values in itertools.permutations(range(size)):
                if not oracle(values)["valid"]:
                    continue
                result = paper_jordan_diagnostics_valid(values, backend=self.spec)
                self.assertEqual(result["output"], sorted(values))
                checked += 1
                # Do not retain all per-prefix replay objects in this test.
                RoutedOrdinaryFixture.instances.clear()
        self.assertGreater(checked, 100)


if __name__ == "__main__":
    unittest.main()
