"""Frozen inputs, sort entry points and untimed key comparisons for the supplement."""
from collections import Counter
from dataclasses import dataclass
from functools import partial
import json
import math
import operator
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from baselines import merge_sort, quick_sort
from input_suite_registry import canonical_cases, digest
from matched_backend_fixture import backend_spec
from paper_jordan_sort import paper_jordan_sort_valid

FROZEN = "bca4c1c6a5480e22c7121987de2c97bb00688264"
SUITE = "a8c2fe3aa2fe4b45bbe876db9e9dabe3b7f95fd666b3c3afab0776bef67234b7"
METHODS = ("ordinary_list", "heterogeneous_finger_uninstrumented", "merge_sort", "quick_sort", "sorted")
CANDIDATES = tuple(2 ** i for i in range(21))
TARGET_NS = 10_000_000


def require(condition, message):
    if not condition:
        raise ValueError(message)


def inputs():
    path = ROOT / "docs/validation/input_suite_registry_20261101/suite.json"
    suite = json.loads(path.read_bytes())
    require(suite.pop("suite_sha256") == SUITE == digest(suite), "input suite digest")
    cases = canonical_cases(suite)
    require(len(cases) == len({c["case_id"] for c in cases}) == 302, "case inventory")
    for c in cases:
        values = c["values"]
        require(len(values) == c["n"] and digest(values) == c["input_sha256"], "input identity")
    random.Random(20261120).shuffle(cases)
    return cases


def reference(values):
    expected = sorted(values)
    require(Counter(expected) == Counter(values) and
            all(a < b for a, b in zip(expected, expected[1:])), "invalid reference")
    return expected


def sort_methods():
    methods = {name: partial(paper_jordan_sort_valid, execution_mode="minimal", backend=backend_spec(name))
               for name in METHODS[:2]}
    methods.update(merge_sort=merge_sort, quick_sort=quick_sort, sorted=sorted)
    return methods


def rotation(case_index, round_index):
    start = (case_index + round_index) % len(METHODS)
    return METHODS[start:] + METHODS[:start]


@dataclass(frozen=True, eq=False, slots=True)
class CountedKey:
    value: int
    counts: Counter

    def _compare(self, other, relation):
        rhs = other.value if isinstance(other, CountedKey) else other
        if not isinstance(rhs, (float, int)):
            return NotImplemented
        result = relation(self.value, rhs)
        self.counts[relation.__name__] += 1
        if isinstance(rhs, float) and math.isinf(rhs):
            self.counts["sentinel"] += 1
        return result

    def __lt__(self, other):
        return self._compare(other, operator.lt)

    def __le__(self, other):
        return self._compare(other, operator.le)

    def __gt__(self, other):
        return self._compare(other, operator.gt)

    def __ge__(self, other):
        return self._compare(other, operator.ge)

    def __eq__(self, other):
        if isinstance(other, CountedKey):
            return self.value == other.value
        return self.value.__eq__(other)

    def __hash__(self):
        return hash(self.value)


def count_call(sort, values, expected):
    counts = Counter()
    keys = [CountedKey(value, counts) for value in values]
    result = sort(keys)
    snapshot = {op: counts[op] for op in ("lt", "le", "gt", "ge")}
    snapshot.update(total=sum(snapshot.values()), sentinel=counts["sentinel"])
    require([key.value for key in result] == expected, "counted output mismatch")
    require([key.value for key in keys] == values, "counted input mutation")
    return snapshot
