"""Executable semantic model, NOT a finger-tree implementation or readiness proof.

Run directly, or use unittest discovery. An explicit --factory module:callable
runs the same public semantic contracts against a TEST ADAPTER. A missing
adapter is an error, never a skipped/passing tree-backend validation. The
adapter interface below is test-only; it is not a new production interface.
Use --strict for complete contract acceptance. Filtered development runs never
set contract_acceptance_passed, even when unittest reports success.
"""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
import importlib
import json
import random
import sys
import unittest

LEFT, RIGHT = "left", "right"


@dataclass(frozen=True)
class Item:
    item_id: int
    key: int


class OrderedListModel:
    """Deliberately slow specification for ordered items and opaque owner labels.

    Lists, full scans, and materialization here are allowed ONLY as a test
    reference. No geometric intervals, family cycles, red-black invariants,
    amortized bounds, or Jordan correctness are established by this model.
    """

    def __init__(self):
        self._lists = {}
        self._owners = {}
        self._items = {}
        self._next = 1
        self._pending = None

    def _ready(self):
        if self._pending is not None:
            raise ValueError("adopt the pending split before another operation")

    @staticmethod
    def _side(side):
        if side not in (LEFT, RIGHT):
            raise ValueError("side must be left or right")

    def _fresh(self, item):
        if not isinstance(item, Item) or item.item_id in self._items:
            raise ValueError("item must be fresh")

    def _new_handle(self, items, owner):
        if not items:
            return None
        handle = self._next
        self._next += 1
        self._lists[handle] = tuple(items)
        self._owners[handle] = owner
        return handle

    def _owner_count(self, owner):
        return sum(value == owner for value in self._owners.values())

    def make_list(self, item, owner):
        self._ready()
        self._fresh(item)
        if owner is None or self._owner_count(owner) >= 2:
            raise ValueError("owner must exist and have a free child-list slot")
        handle = self._new_handle((item,), owner)
        self._items[item.item_id] = item
        return handle

    def boundary_list(self, item_id, side):
        self._ready()
        self._side(side)
        for handle, items in self._lists.items():
            endpoint = items[0] if side == LEFT else items[-1]
            if endpoint.item_id == item_id:
                return handle
        raise ValueError("item is not the requested live boundary")

    def insert_boundary(self, item, anchor_id, side):
        self._ready()
        self._fresh(item)
        handle = self.boundary_list(anchor_id, side)
        items = self._lists[handle]
        if side == LEFT:
            if not item.key < items[0].key:
                raise ValueError("left insertion must preserve strict order")
            updated = (item,) + items
        else:
            if not items[-1].key < item.key:
                raise ValueError("right insertion must preserve strict order")
            updated = items + (item,)
        self._lists[handle] = updated
        self._items[item.item_id] = item
        return handle

    def split_value(self, handle, value):
        self._ready()
        items = self._lists[handle]
        old_owner = self._owners[handle]
        left = tuple(item for item in items if item.key <= value)
        right = tuple(item for item in items if item.key > value)
        del self._lists[handle]
        del self._owners[handle]
        left_handle = self._new_handle(left, None)
        right_handle = self._new_handle(right, None)
        self._pending = (old_owner, left_handle, right_handle)
        return left_handle, right_handle

    def adopt_split(self, old_owner, new_owner, left, right, acquired_side):
        self._side(acquired_side)
        if self._pending is None or self._pending != (old_owner, left, right):
            raise ValueError("split provenance or old owner does not match")
        if new_owner is None or new_owner == old_owner:
            raise ValueError("new owner must differ from old owner")
        acquired = left if acquired_side == LEFT else right
        if acquired is not None and self._owner_count(new_owner) >= 2:
            raise ValueError("new owner has no free child-list slot")
        for side, handle in ((LEFT, left), (RIGHT, right)):
            if handle is not None:
                self._owners[handle] = new_owner if side == acquired_side else old_owner
        self._pending = None

    def items(self, handle):
        """Audit-only materialization; retired handles raise KeyError."""
        return self._lists[handle]

    def get_item(self, item_id):
        return self._items[item_id]

    def owner_of_list(self, handle):
        self._ready()
        return self._owners[handle]

    def extreme_child(self, owner, side):
        self._ready()
        self._side(side)
        children = [item for handle, items in self._lists.items()
                    if self._owners[handle] == owner for item in items]
        if not children:
            return None
        return (min if side == LEFT else max)(children, key=lambda item: item.key)

    def materialize_audit(self):
        """Canonical logical snapshot: (owner, tuple(item IDs)) per live list."""
        self._ready()
        if self._lists.keys() != self._owners.keys():
            raise RuntimeError("header/owner mismatch")
        seen = set()
        snapshot = []
        for handle, items in self._lists.items():
            owner = self._owners[handle]
            if owner is None or not items or self._owner_count(owner) > 2:
                raise RuntimeError("invalid owner slots or empty live list")
            if any(a.key >= b.key for a, b in zip(items, items[1:])):
                raise RuntimeError("list is not strictly ordered")
            for item in items:
                if item.item_id in seen or self._items.get(item.item_id) is not item:
                    raise RuntimeError("duplicate membership or unstable item identity")
                seen.add(item.item_id)
            snapshot.append((owner, tuple(item.item_id for item in items)))
        if seen != set(self._items):
            raise RuntimeError("item conservation failed")
        return tuple(sorted(snapshot))


SUBJECT_FACTORY = OrderedListModel


class OperationContractTests(unittest.TestCase):
    """These tests can be reused with a real backend through a test adapter."""

    def setUp(self):
        self.backend = SUBJECT_FACTORY()

    def build(self, keys=(10, 20, 30), owner=100):
        items = tuple(Item(index + 1, key) for index, key in enumerate(keys))
        handle = self.backend.make_list(items[0], owner)
        for previous, item in zip(items, items[1:]):
            handle = self.backend.insert_boundary(item, previous.item_id, RIGHT)
        return handle, items

    def test_singleton_has_two_boundaries(self):
        handle, items = self.build((10,))
        self.assertEqual(self.backend.boundary_list(1, LEFT), handle)
        self.assertEqual(self.backend.boundary_list(1, RIGHT), handle)
        self.assertIs(self.backend.get_item(1), items[0])
        self.assertEqual(self.backend.materialize_audit(), ((100, (1,)),))

    def test_insert_both_ends(self):
        handle, _ = self.build((20,))
        self.backend.insert_boundary(Item(2, 10), 1, LEFT)
        self.backend.insert_boundary(Item(3, 30), 1, RIGHT)
        self.assertEqual(tuple(i.item_id for i in self.backend.items(handle)), (2, 1, 3))
        self.backend.materialize_audit()

    def test_equal_key_rejected(self):
        self.build((10,))
        with self.assertRaises(ValueError):
            self.backend.insert_boundary(Item(2, 10), 1, RIGHT)

    def test_duplicate_item_rejected(self):
        _, items = self.build((10,))
        with self.assertRaises(ValueError):
            self.backend.make_list(items[0], 200)

    def test_interior_anchor_rejected(self):
        self.build()
        with self.assertRaises(ValueError):
            self.backend.insert_boundary(Item(4, 25), 2, RIGHT)

    def test_wrong_side_rejected(self):
        self.build((10,))
        with self.assertRaises(ValueError):
            self.backend.insert_boundary(Item(2, 20), 1, LEFT)

    def test_interior_owner_query_is_not_boundary_query(self):
        self.build()
        with self.assertRaises(ValueError):
            self.backend.boundary_list(2, LEFT)

    def test_split_cuts_and_adoption_directions(self):
        for cut in (0, 10, 15, 20, 30, 40):
            for side in (LEFT, RIGHT):
                with self.subTest(cut=cut, side=side):
                    self.backend = SUBJECT_FACTORY()
                    handle, items = self.build()
                    left, right = self.backend.split_value(handle, cut)
                    self.backend.adopt_split(100, 200, left, right, side)
                    expected = (tuple(i for i in items if i.key <= cut),
                                tuple(i for i in items if i.key > cut))
                    for name, out, wanted in zip((LEFT, RIGHT), (left, right), expected):
                        if not wanted:
                            self.assertIsNone(out)
                        else:
                            self.assertEqual(self.backend.items(out), wanted)
                            self.assertEqual(self.backend.owner_of_list(out),
                                             200 if name == side else 100)
                            self.assertEqual(self.backend.boundary_list(wanted[0].item_id, LEFT), out)
                            self.assertEqual(self.backend.boundary_list(wanted[-1].item_id, RIGHT), out)
                    with self.assertRaises(KeyError):
                        self.backend.items(handle)
                    for item in items:
                        self.assertIs(self.backend.get_item(item.item_id), item)
                    self.backend.materialize_audit()

    def test_new_boundaries_after_insertion(self):
        handle, _ = self.build()
        self.backend.insert_boundary(Item(4, 5), 1, LEFT)
        self.assertEqual(self.backend.boundary_list(4, LEFT), handle)
        with self.assertRaises(ValueError):
            self.backend.boundary_list(1, LEFT)

    def test_old_owner_mismatch_rejected(self):
        handle, _ = self.build()
        left, right = self.backend.split_value(handle, 15)
        with self.assertRaises(ValueError):
            self.backend.adopt_split(999, 200, left, right, LEFT)

    def test_same_owner_adoption_rejected(self):
        handle, _ = self.build()
        left, right = self.backend.split_value(handle, 15)
        with self.assertRaises(ValueError):
            self.backend.adopt_split(100, 100, left, right, LEFT)

    def test_two_child_slots(self):
        self.backend.make_list(Item(1, 10), 100)
        self.backend.make_list(Item(2, 30), 100)
        with self.assertRaises(ValueError):
            self.backend.make_list(Item(3, 50), 100)

    def test_adoption_cannot_overfill_owner(self):
        handle, _ = self.build()
        self.backend.make_list(Item(4, 40), 200)
        self.backend.make_list(Item(5, 50), 200)
        left, right = self.backend.split_value(handle, 15)
        with self.assertRaises(ValueError):
            self.backend.adopt_split(100, 200, left, right, LEFT)

    def test_extreme_child_across_two_slots(self):
        a, b = Item(1, 30), Item(2, 10)
        self.backend.make_list(a, 100)
        self.backend.make_list(b, 100)
        self.assertIs(self.backend.extreme_child(100, LEFT), b)
        self.assertIs(self.backend.extreme_child(100, RIGHT), a)
        self.assertIsNone(self.backend.extreme_child(999, LEFT))

    def test_repeated_skewed_splits_and_stable_items(self):
        handle, items = self.build(tuple(range(12)))
        owner = 100
        for index in range(11):
            left, right = self.backend.split_value(handle, index)
            self.backend.adopt_split(owner, owner + 1, left, right, RIGHT)
            self.assertEqual(self.backend.items(left), (items[index],))
            owner += 1
            handle = right
            self.backend.materialize_audit()
        self.assertEqual(self.backend.items(handle), (items[-1],))
        for item in items:
            self.assertIs(self.backend.get_item(item.item_id), item)

    def test_generated_operation_sequences(self):
        # Fixed, small development cases, NOT a Jordan input benchmark.
        for seed in range(8):
            with self.subTest(seed=seed):
                rng = random.Random(seed)
                self.backend = SUBJECT_FACTORY()
                handle = self.backend.make_list(Item(1, 0), 100)
                expected = [(1, 0)]
                for item_id in range(2, 34):
                    if rng.randrange(2):
                        key, anchor, side = expected[-1][1] + 3, expected[-1][0], RIGHT
                        expected.append((item_id, key))
                    else:
                        key, anchor, side = expected[0][1] - 3, expected[0][0], LEFT
                        expected.insert(0, (item_id, key))
                    handle = self.backend.insert_boundary(Item(item_id, key), anchor, side)
                    self.assertEqual(tuple((i.item_id, i.key) for i in self.backend.items(handle)),
                                     tuple(expected))
                    self.backend.materialize_audit()
                cut = rng.randint(expected[0][1] - 1, expected[-1][1] + 1)
                side = (LEFT, RIGHT)[rng.randrange(2)]
                left, right = self.backend.split_value(handle, cut)
                self.backend.adopt_split(100, 200, left, right, side)
                wanted = []
                for name, values in ((LEFT, tuple(i for i, k in expected if k <= cut)),
                                     (RIGHT, tuple(i for i, k in expected if k > cut))):
                    if values:
                        wanted.append((200 if side == name else 100, values))
                self.assertEqual(self.backend.materialize_audit(), tuple(sorted(wanted)))

    def assert_live_lists(self, records):
        """Compare each live list with explicit items/owners, not another backend."""
        for handle, owner, items in records:
            self.assertEqual(self.backend.items(handle), items)
            self.assertEqual(self.backend.owner_of_list(handle), owner)
            self.assertEqual(self.backend.boundary_list(items[0].item_id, LEFT), handle)
            self.assertEqual(self.backend.boundary_list(items[-1].item_id, RIGHT), handle)
            for item in items:
                self.assertIs(self.backend.get_item(item.item_id), item)
        expected = tuple(sorted((owner, tuple(i.item_id for i in items))
                                for _, owner, items in records))
        self.assertEqual(self.backend.materialize_audit(), expected)
        for owner in {owner for _, owner, _ in records}:
            children = [item for _, candidate, items in records if candidate == owner
                        for item in items]
            self.assertIs(self.backend.extreme_child(owner, LEFT),
                          min(children, key=lambda item: item.key))
            self.assertIs(self.backend.extreme_child(owner, RIGHT),
                          max(children, key=lambda item: item.key))

    def exercise_interleaved_updates(self, cut, acquired_side, mirrored):
        self.backend = SUBJECT_FACTORY()
        sign = -1 if mirrored else 1
        insertion_side = LEFT if mirrored else RIGHT
        items = tuple(Item(i + 1, sign * key) for i, key in enumerate((10, 20, 30, 40)))
        handle = self.backend.make_list(items[0], 100)
        for previous, item in zip(items, items[1:]):
            handle = self.backend.insert_boundary(item, previous.item_id, insertion_side)
        ordered = tuple(sorted(items, key=lambda item: item.key))
        self.assert_live_lists([(handle, 100, ordered)])
        left, right = self.backend.split_value(handle, sign * cut)
        self.backend.adopt_split(100, 200, left, right, acquired_side)
        retired = [handle]
        records = []
        for side, out, wanted in (
            (LEFT, left, tuple(i for i in ordered if i.key <= sign * cut)),
            (RIGHT, right, tuple(i for i in ordered if i.key > sign * cut)),
        ):
            if wanted:
                records.append((out, 200 if side == acquired_side else 100, wanted))
            else:
                self.assertIsNone(out)
        self.assert_live_lists(records)

        next_id = 5
        # Insert at BOTH ends of BOTH retained/acquired outputs before resplitting.
        for index, (out, owner, wanted) in enumerate(records):
            for side in (LEFT, RIGHT):
                anchor = wanted[0] if side == LEFT else wanted[-1]
                item = Item(next_id, anchor.key + (-1 if side == LEFT else 1))
                next_id += 1
                updated = self.backend.insert_boundary(item, anchor.item_id, side)
                self.assertEqual(updated, out)
                wanted = (item,) + wanted if side == LEFT else wanted + (item,)
                records[index] = (out, owner, wanted)
                self.assert_live_lists(records)

        # Split every first-round output again, keeping the other lists live.
        for index, (out, owner, wanted) in enumerate(list(records)):
            cut_again = (wanted[0].key + wanted[-1].key) // 2
            left, right = self.backend.split_value(out, cut_again)
            new_owner = 300 + index
            acquired_again = RIGHT if acquired_side == LEFT else LEFT
            self.backend.adopt_split(owner, new_owner, left, right, acquired_again)
            retired.append(out)
            records = [record for record in records if record[0] != out]
            for side, new_handle, values in (
                (LEFT, left, tuple(i for i in wanted if i.key <= cut_again)),
                (RIGHT, right, tuple(i for i in wanted if i.key > cut_again)),
            ):
                self.assertTrue(values)  # Both sides are deliberately nonempty here.
                records.append((new_handle, new_owner if side == acquired_again else owner,
                                values))
            self.assert_live_lists(records)

        stale_boundaries = []
        # A second round of updates also exercises singleton split outputs.
        for index, (out, owner, wanted) in enumerate(records):
            for side in (LEFT, RIGHT):
                anchor = wanted[0] if side == LEFT else wanted[-1]
                stale_boundaries.append((anchor.item_id, side))
                item = Item(next_id, anchor.key + (-1 if side == LEFT else 1))
                next_id += 1
                self.assertEqual(self.backend.insert_boundary(item, anchor.item_id, side), out)
                wanted = (item,) + wanted if side == LEFT else wanted + (item,)
                records[index] = (out, owner, wanted)
                self.assert_live_lists(records)

        # Negative queries come after all valid updates; no recovery is assumed.
        for old_handle in retired:
            with self.assertRaises(KeyError):
                self.backend.items(old_handle)
        for item_id, side in stale_boundaries:
            with self.assertRaises(ValueError):
                self.backend.boundary_list(item_id, side)

    def test_split_adopt_insert_and_resplit_both_outputs(self):
        for acquired_side in (LEFT, RIGHT):
            for mirrored in (False, True):
                with self.subTest(acquired_side=acquired_side, mirrored=mirrored):
                    self.exercise_interleaved_updates(25, acquired_side, mirrored)

    def test_empty_side_split_then_insert_and_resplit(self):
        for cut in (0, 50):
            for acquired_side in (LEFT, RIGHT):
                for mirrored in (False, True):
                    with self.subTest(cut=cut, acquired_side=acquired_side, mirrored=mirrored):
                        self.exercise_interleaved_updates(cut, acquired_side, mirrored)


class ModelAuditSelfTests(unittest.TestCase):
    """Mutation checks of the MODEL auditor, not the real backend auditor."""

    def test_audit_rejects_lost_item(self):
        m = OrderedListModel()
        h = m.make_list(Item(1, 10), 100)
        m._lists[h] = ()
        with self.assertRaises(RuntimeError):
            m.materialize_audit()

    def test_audit_rejects_wrong_order(self):
        m = OrderedListModel()
        h = m.make_list(Item(1, 10), 100)
        m.insert_boundary(Item(2, 20), 1, RIGHT)
        m._lists[h] = tuple(reversed(m._lists[h]))
        with self.assertRaises(RuntimeError):
            m.materialize_audit()

    def test_audit_rejects_replaced_item_identity(self):
        m = OrderedListModel()
        h = m.make_list(Item(1, 10), 100)
        m._lists[h] = (Item(1, 10),)
        with self.assertRaises(RuntimeError):
            m.materialize_audit()

    def test_audit_rejects_pending_adoption(self):
        m = OrderedListModel()
        h = m.make_list(Item(1, 10), 100)
        m.split_value(h, 10)
        with self.assertRaises(ValueError):
            m.materialize_audit()


class ContractTestResult(unittest.TextTestResult):
    """Track actual method execution, including duplicates and subtest skips."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.started_ids = Counter()
        self.passed_ids = Counter()

    def startTest(self, test):
        self.started_ids[test.id()] += 1
        super().startTest(test)

    def addSuccess(self, test):
        self.passed_ids[test.id()] += 1
        super().addSuccess(test)

    def group_report(self, expected_ids):
        expected = Counter(expected_ids)
        started = Counter({key: self.started_ids[key] for key in expected if self.started_ids[key]})
        passed = Counter({key: self.passed_ids[key] for key in expected if self.passed_ids[key]})

        def belongs(test):
            # unittest reports a skipped/failed subtest separately from its parent.
            return getattr(test, "test_case", test).id() in expected

        return {
            "expected_methods": len(expected),
            "started_methods": sum(started.values()),
            "passed_methods": sum(passed.values()),
            "skips": sum(belongs(test) for test, _ in self.skipped),
            "failures": sum(belongs(test) for test, _ in self.failures),
            "errors": sum(belongs(test) for test, _ in self.errors),
            "expected_failures": sum(belongs(test) for test, _ in self.expectedFailures),
            "unexpected_successes": sum(belongs(test) for test in self.unexpectedSuccesses),
            "missing_passes": sorted(set(expected) - set(passed)),
            "duplicate_methods": sorted(key for key, count in started.items() if count > 1),
            "complete": started == expected and passed == expected,
        }


class ContractTestRunner(unittest.TextTestRunner):
    resultclass = ContractTestResult


def expected_test_ids(case):
    return [f"{case.__module__}.{case.__qualname__}.{name}"
            for name in unittest.TestLoader().getTestCaseNames(case)]


def main(argv=None):
    global SUBJECT_FACTORY
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--factory", help="test adapter factory, module:callable")
    parser.add_argument("--strict", action="store_true",
                        help="require every operation contract exactly once, with no skips")
    args, unittest_args = parser.parse_known_args(argv)
    expected_contracts = expected_test_ids(OperationContractTests)
    expected_model_tests = expected_test_ids(ModelAuditSelfTests)
    SUBJECT_FACTORY = OrderedListModel
    scope = "reference_model_only"
    if args.factory:
        try:
            module_name, attribute = args.factory.split(":", 1)
            SUBJECT_FACTORY = getattr(importlib.import_module(module_name), attribute)
            if not callable(SUBJECT_FACTORY) or SUBJECT_FACTORY is OrderedListModel:
                raise ValueError("factory must be a callable external adapter")
        except (ValueError, ImportError, AttributeError) as exc:
            print(json.dumps({"scope": "external_adapter", "status": "UNAVAILABLE",
                              "mode": "strict" if args.strict else "development",
                              "contract_acceptance_passed": False,
                              "factory": args.factory, "reason": str(exc)}))
            return 2
        scope = "external_adapter_semantic_contract_only"
    result = unittest.main(module=__name__, argv=[sys.argv[0], *unittest_args],
                           testRunner=ContractTestRunner, exit=False).result
    contracts = result.group_report(expected_contracts)
    model_tests = result.group_report(expected_model_tests)
    clean = (result.wasSuccessful() and not result.skipped and not result.expectedFailures)
    accepted = args.strict and contracts["complete"] and clean
    if args.strict:
        status = "ACCEPTED" if accepted else "REJECTED"
    else:
        status = "DEVELOPMENT_CHECK_COMPLETED" if result.wasSuccessful() else "FAILED"
    print(json.dumps({"scope": scope, "mode": "strict" if args.strict else "development",
                      "status": status, "contract_acceptance_passed": accepted,
                      "partial_check": not contracts["complete"],
                      "operation_contracts": {"subject": "external_adapter" if args.factory
                                              else "reference_model", **contracts},
                      "reference_model_self_tests": model_tests,
                      "tests_run": result.testsRun,
                      "failures": len(result.failures), "errors": len(result.errors),
                      "skipped": len(result.skipped),
                      "expected_failures": len(result.expectedFailures),
                      "unexpected_successes": len(result.unexpectedSuccesses),
                      "jordan_integration_validated": False,
                      "efficiency_bound_proved": False,
                      "backend_ready_for_timing": False}))
    return 0 if (accepted if args.strict else result.wasSuccessful()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
