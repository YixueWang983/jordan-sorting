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

Status: approved for Day 2 data-structure work after review fixes.

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
- [x] Specify atomic split ownership replacement and the two-child-list limit.
- [x] Separate generic `split_by_key` from Jordan `split_pairs_at_value`.
- [x] Correct Python-list front-insertion complexity.
- [x] Add an existing-sibling-list insertion trace.
- [x] Add increasing and decreasing split/ownership-transfer traces.

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

The 197 passing tests are regression evidence for the existing repository only.
They do not validate the new Step 3 interpretation because Day 1 intentionally
adds no algorithm code or executable Step 3 tests. Those tests are required
before the later algorithm gate can pass.

## Review Fixes

The Day 1 review correctly identified that the original worked example did not
exercise the dangerous Step 3 paths. The specification now includes:

```text
[1, 2, 3, 4]:
    insert P4 after P2 in an existing sibling list

[2, 3, 1, 4]:
    increasing split; transfer P2 from the upper dummy to P4

[3, 2, 4, 1]:
    decreasing split; mirrored transfer and output insertion
```

All three candidates were checked as valid by the external oracle.

The ownership contract now requires:

```text
at most two child sibling lists per parent
ordered and unique child-list IDs
pair.parent_pair_id == list.owner_parent_pair_id
atomic retirement and replacement of split input lists
explicit None handling for empty split sides
```

The generic backend exposes `split_by_key`; the algorithm adapter performs pair
endpoint validation and commits the parent/list ownership transaction.

Python-list complexity is now stated accurately: append at the back is
amortized `O(1)`, insertion at the front is `O(k)`, and split is `O(k)`.

## Interpretations Requiring Executable Tests

1. Increasing Step 3(b) transfers the left split output to the new pair.
2. Decreasing Step 3(b) transfers the right split output to the new pair.
3. Decreasing Step 3(c) inserts before the second curve-order endpoint of the
   leftmost child.
4. Empty split outputs are represented by `None`, not persistent empty lists.

The three new traces fix the intended interpretation. Direct executable tests
are still required before the complete Step 3 algorithm is declared correct.

## Next Step

Wait for Day 1 review. After approval, begin Day 2 with:

```text
src/partial_sorted_list.py
tests/test_partial_sorted_list.py
```

Do not implement sibling-list mutation or the full paper loop before the
partial sorted-order structure passes its focused tests.
