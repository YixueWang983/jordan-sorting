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

Status: revised after Step 3(c) endpoint and odd-index counterexamples;
awaiting review before Day 2.

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
- [x] Separate curve-order `first/second` endpoints from geometric `left/right`
  endpoints.
- [x] Resolve the Step 3(c) anchor against minimal orientation counterexamples.
- [x] Add all four parent/child orientation combinations.
- [x] Add a split trace whose left and right outputs are both nonempty.
- [x] Add the odd-index `z1` output-anchor adjustment in both orientations.
- [x] Repair Trace F by deriving its `i=7` precondition instead of assuming it.
- [x] Restore mandatory ownership for every live sibling list.

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
3. Increasing Step 3(c) inserts after the geometric right endpoint of the
   rightmost child.
4. Decreasing Step 3(c) inserts before the geometric left endpoint of the
   leftmost child.
5. Empty split outputs are represented by `None`, not persistent empty lists.
6. A two-nonempty-side split preserves the retained side's parent and transfers
   every acquired pair to the new parent atomically.
7. Odd-index processing changes the output anchor to `z1` when `z1` lies
   strictly between the geometric base anchor and the new point.

The design traces fix the intended interpretation. Direct executable tests are
still required before the complete Step 3 algorithm is declared correct.

## Second Review: Step 3(c) Counterexamples

The second review found that interpreting the paper's `z_m` as
`PairRecord.second` is incorrect. Two oracle-valid minimal counterexamples are:

```text
[3,2,1,4]:
    increasing P4 acquires decreasing child P2={3,2}
    inserting 4 after P2.second=2 gives [1,2,4,3]

[2,3,4,1]:
    decreasing P4 acquires increasing child P2={2,3}
    inserting 1 before P2.second=3 gives [2,1,3,4]
```

The first candidate also has a direct simple-curve realization using a nested
inner upper arc from `3` to `2`, a lower arc from `2` to `1`, and an outer
upper arc from `1` to `4`. The failure is therefore not dismissed as an oracle
domain artifact.

The corrected executable rule is:

```text
increasing:
    insert after the geometric right endpoint of the rightmost child

decreasing:
    insert before the geometric left endpoint of the leftmost child
```

This agrees with the earlier 1986 algorithm's boundary item `u_q`, which is
stored in a sorted family list. The 1990 text compresses a child to a pair and
uses `z_m`; the ordinary-list reconstruction records that a literal
curve-index interpretation is insufficient.

The design now covers all four orientation combinations:

```text
increasing parent + increasing child: [2,3,1,4]
increasing parent + decreasing child: [3,2,1,4]
decreasing parent + increasing child: [2,3,4,1]
decreasing parent + decreasing child: [3,2,4,1]
```

The candidate `[1,2,3,4,6,7,0,5]` provides a two-nonempty-output split:
`[P2,P4]` is acquired by `P8`, while `[P6]` remains with the upper dummy.

`SiblingList.owner_parent_pair_id` is mandatory for every live list. Temporary
unowned partitions exist only inside `SplitPlan`.

## Third Review: Odd-Index `z1` Output Anchor

The third review showed that Step 1 and Step 2's `z1` boundary adjustment does
not eliminate the separate output-anchor anomaly described by the 1986
algorithm.

For:

```text
[1,2,3,4,6,7,0]
```

the decreasing `i=7` step has geometric base anchor `2`. Inserting `0` before
`2` gives `[1,0,2,3,4,6,7]`. Because `z1=1` lies between `0` and `2`, the
output anchor must change to `z1`, producing the correct partial order.

The reflected increasing case is:

```text
[6,5,4,3,1,0,7]
```

Its base anchor is `5`, but `z1=6` lies between `5` and `7`; insertion after
`z1` produces the correct order.

Step 3(c) now has two stages:

```text
1. choose the geometric base anchor;
2. when i is odd and z1 lies between that anchor and z_i, replace the output
   anchor by z1.
```

Trace F now derives the correct sorted state after `i=7` before demonstrating
the two-nonempty-output split at `i=8`.

## Next Step

Wait for review of the corrected Step 3(c) rule and new traces. After approval,
begin Day 2 with:

```text
src/partial_sorted_list.py
tests/test_partial_sorted_list.py
```

Do not implement sibling-list mutation or the full paper loop before the
partial sorted-order structure passes its focused tests.
