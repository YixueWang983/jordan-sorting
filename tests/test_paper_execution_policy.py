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
from paper_jordan_sort import (  # noqa: E402
    _run_paper_jordan_valid,
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

    def test_unknown_mode_and_caller_defined_policy_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "unknown paper execution mode"):
            resolve_paper_execution_policy("unknown")
        with self.assertRaisesRegex(TypeError, "execution_mode must be a string"):
            resolve_paper_execution_policy(None)

        copied_policy = PaperExecutionPolicy(
            name=CHECKED_MODE,
            record_trace=True,
            count_operations=True,
            validate_backend_commits=True,
        )
        with self.assertRaisesRegex(ValueError, "fixed policy registry"):
            require_fixed_paper_execution_policy(copied_policy)

    def test_unknown_public_mode_is_rejected_before_small_input_shortcuts(self):
        with self.assertRaisesRegex(ValueError, "unknown paper execution mode"):
            paper_jordan_sort_valid([], execution_mode="unknown")

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

    def test_day2_modes_do_not_disable_trace_counters_or_commit_validation(self):
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
                self.assertIn(False, validation_flags)


if __name__ == "__main__":
    unittest.main()
