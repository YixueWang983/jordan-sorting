"""Week 10 paper execution-policy architecture tests."""

import itertools
import sys
import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path
from unittest.mock import patch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import paper_jordan_sort  # noqa: E402
from generators import (  # noqa: E402
    generate_flat,
    generate_incremental_valid,
    generate_nested,
)
from oracle import oracle  # noqa: E402
from paper_execution_policy import (  # noqa: E402
    CHECKED_MODE,
    CHECKED_POLICY,
    COUNTERS_ONLY_MODE,
    COUNTERS_ONLY_POLICY,
    INSTRUMENTED_MODE,
    INSTRUMENTED_POLICY,
    MINIMAL_MODE,
    MINIMAL_POLICY,
    PAPER_EXECUTION_MODE_NAMES,
    PAPER_EXECUTION_POLICIES,
    TRACE_ONLY_MODE,
    TRACE_ONLY_POLICY,
    PaperExecutionPolicy,
    require_fixed_paper_execution_policy,
    resolve_paper_execution_policy,
)
from paper_jordan import (  # noqa: E402
    _validate_initial_backend_postconditions,
    initialize_paper_jordan_state,
    validate_paper_jordan_state,
)
from paper_jordan_sort import (  # noqa: E402
    _run_paper_jordan_valid,
    paper_jordan_diagnostics_valid,
    paper_jordan_sort_valid,
)
from sibling_list_backend import OrdinarySiblingListBackend  # noqa: E402


EXPECTED_POLICIES = {
    CHECKED_MODE: (True, True, True),
    INSTRUMENTED_MODE: (True, True, False),
    TRACE_ONLY_MODE: (True, False, False),
    COUNTERS_ONLY_MODE: (False, True, False),
    MINIMAL_MODE: (False, False, False),
}


class PaperExecutionPolicyTests(unittest.TestCase):
    def test_fixed_registry_contains_the_five_designed_modes(self):
        self.assertEqual(tuple(EXPECTED_POLICIES), PAPER_EXECUTION_MODE_NAMES)
        self.assertEqual(set(PAPER_EXECUTION_POLICIES), set(EXPECTED_POLICIES))

        for mode, expected_flags in EXPECTED_POLICIES.items():
            with self.subTest(mode=mode):
                policy = PAPER_EXECUTION_POLICIES[mode]
                self.assertEqual(
                    (
                        policy.record_trace,
                        policy.count_operations,
                        policy.validate_backend_commits,
                    ),
                    expected_flags,
                )
                self.assertIs(resolve_paper_execution_policy(mode), policy)

    def test_named_policy_constants_are_the_registry_objects(self):
        expected = {
            CHECKED_MODE: CHECKED_POLICY,
            INSTRUMENTED_MODE: INSTRUMENTED_POLICY,
            TRACE_ONLY_MODE: TRACE_ONLY_POLICY,
            COUNTERS_ONLY_MODE: COUNTERS_ONLY_POLICY,
            MINIMAL_MODE: MINIMAL_POLICY,
        }
        for mode, policy in expected.items():
            with self.subTest(mode=mode):
                self.assertIs(PAPER_EXECUTION_POLICIES[mode], policy)
                self.assertIs(require_fixed_paper_execution_policy(policy), policy)

    def test_policies_and_registry_are_immutable(self):
        with self.assertRaises(FrozenInstanceError):
            CHECKED_POLICY.record_trace = False
        with self.assertRaises(TypeError):
            PAPER_EXECUTION_POLICIES["custom"] = CHECKED_POLICY

    def test_invalid_modes_and_caller_defined_policy_are_rejected(self):
        for invalid_mode in (None, True, False, 1, 0, object()):
            with self.subTest(invalid_mode=invalid_mode):
                with self.assertRaisesRegex(
                    TypeError,
                    "execution_mode must be a string",
                ):
                    resolve_paper_execution_policy(invalid_mode)

        for invalid_mode in ("", "unknown"):
            with self.subTest(invalid_mode=invalid_mode):
                with self.assertRaisesRegex(
                    ValueError,
                    "unknown paper execution mode",
                ):
                    resolve_paper_execution_policy(invalid_mode)

        copied_policy = PaperExecutionPolicy(
            name=CHECKED_MODE,
            record_trace=True,
            count_operations=True,
            validate_backend_commits=True,
        )
        with self.assertRaisesRegex(ValueError, "fixed policy registry"):
            require_fixed_paper_execution_policy(copied_policy)

    def test_invalid_public_modes_are_rejected_before_small_input_shortcuts(self):
        for invalid_mode in (None, True, False, 1, 0, object()):
            with self.subTest(invalid_mode=invalid_mode):
                with self.assertRaisesRegex(
                    TypeError,
                    "execution_mode must be a string",
                ):
                    paper_jordan_sort_valid([], execution_mode=invalid_mode)

        for invalid_mode in ("", "unknown"):
            with self.subTest(invalid_mode=invalid_mode):
                with self.assertRaisesRegex(
                    ValueError,
                    "unknown paper execution mode",
                ):
                    paper_jordan_sort_valid([], execution_mode=invalid_mode)

    def test_small_inputs_match_in_all_modes(self):
        cases = [
            ([], []),
            ([7], [7]),
            ([2, 1], [1, 2]),
        ]
        cases.extend(
            (list(values), [1, 2, 3])
            for values in itertools.permutations([1, 2, 3])
        )

        for mode in PAPER_EXECUTION_MODE_NAMES:
            for values, expected in cases:
                with self.subTest(mode=mode, values=values):
                    self.assertEqual(
                        paper_jordan_sort_valid(values, execution_mode=mode),
                        expected,
                    )

    def test_duplicate_small_inputs_are_rejected_in_all_modes(self):
        for mode in PAPER_EXECUTION_MODE_NAMES:
            for values in ([1, 1], [1, 1, 2], [1, 2, 2]):
                with self.subTest(mode=mode, values=values):
                    with self.assertRaises(ValueError):
                        paper_jordan_sort_valid(values, execution_mode=mode)

    def test_all_modes_use_the_same_public_runner(self):
        values = [2, 3, 1, 4]
        original_runner = paper_jordan_sort._run_paper_jordan_valid

        with patch.object(
            paper_jordan_sort,
            "_run_paper_jordan_valid",
            wraps=original_runner,
        ) as runner_mock:
            for mode in PAPER_EXECUTION_MODE_NAMES:
                self.assertEqual(
                    paper_jordan_sort_valid(values, execution_mode=mode),
                    [1, 2, 3, 4],
                )

        self.assertEqual(runner_mock.call_count, len(PAPER_EXECUTION_MODE_NAMES))
        observed_policies = [
            call.kwargs["execution_policy"] for call in runner_mock.call_args_list
        ]
        self.assertEqual(
            observed_policies,
            [PAPER_EXECUTION_POLICIES[mode] for mode in PAPER_EXECUTION_MODE_NAMES],
        )

    def test_representative_valid_inputs_match_across_all_modes(self):
        cases = [
            generate_flat(8),
            generate_nested(8),
            generate_incremental_valid(8, seed=10008),
            generate_incremental_valid(16, seed=10016),
        ]

        for values in cases:
            expected = sorted(values)
            default_result = paper_jordan_sort_valid(values)
            self.assertEqual(default_result, expected)

            for mode in PAPER_EXECUTION_MODE_NAMES:
                with self.subTest(mode=mode, values=values):
                    self.assertEqual(
                        paper_jordan_sort_valid(values, execution_mode=mode),
                        default_result,
                    )

    def test_all_valid_permutations_through_n7_match_in_every_mode(self):
        expected_counts = {
            0: 1,
            1: 1,
            2: 2,
            3: 6,
            4: 16,
            5: 50,
            6: 144,
            7: 462,
        }

        for n, expected_count in expected_counts.items():
            valid_count = 0
            expected = list(range(n))

            for values in itertools.permutations(expected):
                if not oracle(values)["valid"]:
                    continue

                valid_count += 1
                for mode in PAPER_EXECUTION_MODE_NAMES:
                    with self.subTest(n=n, values=values, mode=mode):
                        self.assertEqual(
                            paper_jordan_sort_valid(
                                values,
                                execution_mode=mode,
                            ),
                            expected,
                        )

            self.assertEqual(valid_count, expected_count)

    def test_policy_object_reaches_state_and_backend(self):
        values = [2, 3, 1, 4]

        for mode in PAPER_EXECUTION_MODE_NAMES:
            with self.subTest(mode=mode):
                policy = PAPER_EXECUTION_POLICIES[mode]
                state = _run_paper_jordan_valid(
                    list(values),
                    execution_policy=policy,
                )

                self.assertIs(state.execution_policy, policy)
                self.assertIs(state.sibling_backend.execution_policy, policy)
                self.assertEqual(state.partial_order.to_list(), [1, 2, 3, 4])

    def test_diagnostics_always_use_checked_policy(self):
        original_runner = paper_jordan_sort._run_paper_jordan_valid

        with patch.object(
            paper_jordan_sort,
            "_run_paper_jordan_valid",
            wraps=original_runner,
        ) as runner_mock:
            result = paper_jordan_diagnostics_valid([2, 3, 1, 4])

        self.assertEqual(result["output"], [1, 2, 3, 4])
        self.assertEqual(runner_mock.call_count, 1)
        self.assertIs(
            runner_mock.call_args.kwargs["execution_policy"],
            CHECKED_POLICY,
        )

    def test_state_audit_rejects_state_backend_policy_disagreement(self):
        state = _run_paper_jordan_valid(
            [2, 3, 1, 4],
            execution_policy=CHECKED_POLICY,
        )
        state.sibling_backend._execution_policy = MINIMAL_POLICY

        with self.assertRaisesRegex(
            RuntimeError,
            "state and backend execution policies differ",
        ):
            validate_paper_jordan_state(state)

    def test_state_audit_rejects_invalid_state_policy(self):
        invalid_policies = (
            PaperExecutionPolicy(
                name=CHECKED_MODE,
                record_trace=True,
                count_operations=True,
                validate_backend_commits=True,
            ),
            object(),
        )

        for invalid_policy in invalid_policies:
            with self.subTest(invalid_policy=invalid_policy):
                state = _run_paper_jordan_valid(
                    [2, 3, 1, 4],
                    execution_policy=CHECKED_POLICY,
                )
                state.execution_policy = invalid_policy

                with self.assertRaisesRegex(
                    RuntimeError,
                    "state execution policy is invalid",
                ):
                    validate_paper_jordan_state(state)

    def test_all_modes_preserve_input_and_consume_iterables_once(self):
        class SinglePassIterable:
            def __init__(self, values):
                self.values = tuple(values)
                self.iteration_count = 0

            def __iter__(self):
                self.iteration_count += 1
                if self.iteration_count > 1:
                    raise RuntimeError("iterable consumed more than once")
                return iter(self.values)

        for mode in PAPER_EXECUTION_MODE_NAMES:
            with self.subTest(mode=mode, input_kind="list"):
                values = [2, 3, 1, 4]
                original = list(values)
                self.assertEqual(
                    paper_jordan_sort_valid(values, execution_mode=mode),
                    [1, 2, 3, 4],
                )
                self.assertEqual(values, original)

            with self.subTest(mode=mode, input_kind="single_pass"):
                values = SinglePassIterable([2, 3, 1, 4])
                self.assertEqual(
                    paper_jordan_sort_valid(values, execution_mode=mode),
                    [1, 2, 3, 4],
                )
                self.assertEqual(values.iteration_count, 1)

    def test_checked_instrumented_and_minimal_backend_states_match(self):
        values = [1, 2, 3, 4, 6, 7, 0, 5]
        states = {
            mode: _run_paper_jordan_valid(
                list(values),
                execution_policy=PAPER_EXECUTION_POLICIES[mode],
            )
            for mode in (CHECKED_MODE, INSTRUMENTED_MODE, MINIMAL_MODE)
        }
        checked = states[CHECKED_MODE]

        for mode, state in states.items():
            with self.subTest(mode=mode):
                self.assertEqual(
                    state.partial_order.to_point_ids(),
                    checked.partial_order.to_point_ids(),
                )
                self.assertEqual(state.processed_count, checked.processed_count)
                self.assertEqual(
                    state.sibling_backend.audit_snapshot(),
                    checked.sibling_backend.audit_snapshot(),
                )

    def test_complete_state_audit_remains_checked_for_minimal_state(self):
        state = _run_paper_jordan_valid(
            [2, 3, 1, 4],
            execution_policy=MINIMAL_POLICY,
        )
        pair = state.sibling_backend.get_pair(2)
        pair.parent_pair_id = state.lower_dummy_pair_id

        with self.assertRaises(RuntimeError):
            validate_paper_jordan_state(state)

    def test_initial_local_postconditions_detect_ownership_corruption(self):
        state = initialize_paper_jordan_state(
            [2, 3, 1, 4],
            execution_mode=MINIMAL_MODE,
        )
        upper_dummy = state.sibling_backend.get_pair(
            state.upper_dummy_pair_id
        )
        lower_dummy = state.sibling_backend.get_pair(
            state.lower_dummy_pair_id
        )
        pair_2 = state.sibling_backend.get_pair(state.pair_by_end_index[2])
        pair_3 = state.sibling_backend.get_pair(state.pair_by_end_index[3])
        family_records = (
            (upper_dummy, pair_2, pair_2.sibling_list_id),
            (lower_dummy, pair_3, pair_3.sibling_list_id),
        )
        pair_2.parent_pair_id = state.lower_dummy_pair_id

        with self.assertRaisesRegex(
            RuntimeError,
            "initial finite-pair ownership is inconsistent",
        ):
            _validate_initial_backend_postconditions(state, family_records)

    def test_day3_policy_only_disables_complete_backend_validation(self):
        values = [1, 2, 3, 4, 6, 7, 0, 5]
        original_validate = OrdinarySiblingListBackend.validate_invariants

        for mode in PAPER_EXECUTION_MODE_NAMES:
            validation_flags = []

            def record_validation(backend, require_all_owned=True):
                validation_flags.append(require_all_owned)
                return original_validate(backend, require_all_owned)

            with self.subTest(mode=mode):
                with patch.object(
                    OrdinarySiblingListBackend,
                    "validate_invariants",
                    new=record_validation,
                ):
                    state = _run_paper_jordan_valid(
                        list(values),
                        execution_policy=PAPER_EXECUTION_POLICIES[mode],
                    )

                self.assertTrue(state.trace)
                self.assertEqual(
                    state.metrics["trace_event_count"],
                    len(state.trace),
                )
                self.assertGreater(state.metrics["output_insertions"], 0)
                if mode == CHECKED_MODE:
                    self.assertIn(True, validation_flags)
                    self.assertIn(False, validation_flags)
                else:
                    self.assertEqual(validation_flags, [])


if __name__ == "__main__":
    unittest.main()
