# Week 9 Progress

Last updated: 2026-07-27

## Goal

Implement the high-level 1990 Simplified Jordan Sorting algorithm with an
ordinary-list sibling-list backend while keeping the existing reference
pipeline as a separate baseline.

Detailed plan:

```text
docs/plan/week9_plan.md
```

## Day 1: Freeze the Executable Specification

Status: completed and waiting for review.

- [x] Read and map paper Sections 2 and 3.
- [x] Fix one-based paper indexing versus zero-based Python storage.
- [x] Fix upper/lower pair-family parity.
- [x] Define same-family pair selection from original point indices.
- [x] Define family-specific dummy pairs and output sentinels.
- [x] Define `SortedOrderList`, pair records, sibling lists, and algorithm state.
- [x] Separate output-list insertion from sibling-list boundary insertion.
- [x] Define `make_list`, `insert_at_boundary`, and `split` contracts.
- [x] Define behavior for `n = 0, 1, 2, 3`.
- [x] Define Step 1, Step 2, Step 3(a-c), and the mirrored orientation.
- [x] Define the pure core and validating-wrapper boundary.
- [x] Define online invariants, trace fields, counters, and complexity limits.
- [x] Add a complete worked trace for `[1, 4, 2, 3]`.
- [x] Add a test matrix and paper-to-implementation ambiguity table.
- [x] Record unresolved Step 3 ownership interpretations explicitly.

Primary output:

```text
docs/design/paper_algorithm_ordinary_list.md
```

## Day 1 Verification

The worked example was checked with the current external oracle:

```text
sequence: [1, 4, 2, 3]
valid: true
upper_ok: true
lower_ok: true
ordinary sorted reference: [1, 2, 3, 4]
```

Repository checks:

```text
python -m unittest discover -s tests:
    Ran 197 tests
    OK

python -m compileall -q src experiments tests:
    passed

git diff --check: passed
main algorithm source files created: none
```

No implementation or performance experiment was started on Day 1.

## Open Interpretations for Later Focused Tests

1. Increasing Step 3(b) transfers the left split output to the new pair.
2. Decreasing Step 3(b) transfers the right split output to the new pair.
3. Decreasing Step 3(c) inserts before the second curve-order endpoint of the
   leftmost child.
4. Empty split outputs are represented by `None`, not persistent empty lists.

These do not block Day 2 standalone data-structure work. They block declaring
the complete Step 3 algorithm correct.

## Next Step

Wait for Day 1 review. After approval, begin Day 2 with:

```text
src/partial_sorted_list.py
tests/test_partial_sorted_list.py
```

Do not implement sibling-list mutation or the full paper loop before the
partial sorted-order structure passes its focused tests.
