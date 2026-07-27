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

Status: approved for Day 2 data-structure implementation.

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

An independent temporary state-machine check performed during Day 1 review
enumerated every oracle-valid permutation through length 7:

```text
n=4:  16 candidates
n=5:  50 candidates
n=6: 144 candidates
n=7: 462 candidates
```

For every iteration it checked:

```text
partial_order == sorted(processed_prefix)
```

This review evidence approved the executable specification. The enumeration
must later become a reproducible repository check in
`experiments/validate_paper_algorithm.py`.

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

## Day 2: Core Data Structures

Status: approved after ownership review fixes.

Completed first component:

```text
src/partial_sorted_list.py
tests/test_partial_sorted_list.py
```

Implemented:

- identity-based negative and positive infinity sentinels;
- immutable `PointRef` records with positive paper indices;
- a doubly linked `SortedOrderList`;
- O(1) predecessor and successor access through node links;
- O(1) insertion before or after a known anchor;
- point-id lookup and membership;
- sentinel-free value and point-id extraction;
- structural, mapping, size, and strict-order validation;
- local order checks that reject incorrect insertion anchors without scanning
  or sorting the whole list.

Focused tests cover:

- empty and singleton lists;
- both sentinel insertion paths;
- before/after insertion and neighbor recovery;
- all six three-point input orders;
- comparable nonnumeric values;
- duplicate point IDs and duplicate/out-of-position values;
- unknown point IDs;
- invalid sentinel operations;
- invalid `PointRef` paper indices.

Completed second component:

```text
src/sibling_list_backend.py
tests/test_sibling_list_backend.py
```

Implemented:

- parity-validated finite `PairRecord` and family-specific dummy pairs;
- geometric left/right endpoint helpers independent of curve-order endpoints;
- mandatory-owner `SiblingList` records;
- `make_list` with ordered parent child-list ownership;
- legal front/back `insert_at_boundary` with inherited parent ownership;
- non-destructive generic `split_by_key`;
- Jordan-specific straddle validation in `split_pairs_at_value`;
- immutable `SplitPlan` and `SplitCommitResult`;
- atomic split retirement, replacement, acquisition, and ownership transfer;
- `None` representation for empty outputs;
- stale/forged plan rejection;
- rollback if an unexpected final invariant check fails;
- global pair/list/parent ownership and order validation;
- rejection of unowned finite parents in list creation and split commits;
- descendant-parent rejection before split publication;
- global acyclic parent-chain validation to the same-family dummy root;
- enforcement of at most two child sibling lists per parent.

Backend tests cover:

- increasing and decreasing endpoint orientation;
- pair parity and duplicate registration;
- singleton creation and two-list parent ordering;
- front/back insertion and illegal middle insertion;
- rejection of pairs already owned elsewhere;
- non-destructive split planning;
- noncontiguous split-key rejection;
- empty-left, empty-right, empty-acquired-side, and two-nonempty-output commits;
- both `LEFT` and `RIGHT` acquisition for two-nonempty outputs;
- Trace F-style acquired/retained ownership;
- straddling-pair rejection without mutation;
- third-child-list rejection without mutation;
- stale and forged split plans;
- rejection of unowned finite owners and split parents;
- rejection of descendant split parents without mutation;
- direct detection of a deliberately corrupted family-tree cycle;
- complete rollback after a forced final invariant failure.

Day 2 verification:

```text
python -m unittest tests/test_partial_sorted_list.py:
    Ran 13 tests
    OK

python -m unittest tests/test_sibling_list_backend.py:
    Ran 24 tests
    OK

python -m unittest discover -s tests:
    Ran 234 tests
    OK

python -m compileall -q src experiments tests:
    passed

git diff --check:
    passed
```

Performance boundary recorded during Day 2 review:

- `validate_invariants()` follows each owned finite pair to its family dummy;
- a full validation is worst-case `O(p^2)` for `p` pairs;
- `commit_split()` currently retains this check because Day 2 prioritizes
  correctness and rollback safety;
- before timing the paper-algorithm implementation, full validation must be
  controlled by an explicit correctness/debug mode and executed separately
  outside the measured region.

## Day 3: Initialization, Step 1, and Step 2

Status: approved after finite-ownership and dummy-fallback review fixes.

Added:

```text
src/paper_jordan.py
tests/test_paper_jordan.py
```

Implemented:

- `PaperJordanState` with immutable input points, processed-prefix count,
  partial sorted order, pair mappings, sibling backend, family dummies, trace,
  and counters;
- fixed-comparison initialization of `z1`, `z2`, and `z3` without `sorted`;
- initial upper `P2` and lower `P3` with live singleton-list ownership;
- `BoundarySelection`;
- pair-family parity helper;
- processed same-family incident-pair selection using original paper indices;
- Step 1 predecessor-side boundary selection;
- Step 2 successor-side boundary selection;
- upper/lower dummy fallback at the matching infinity sentinel;
- odd-index `z1` adjustment on both predecessor and successor paths;
- bidirectional finite pair/list ownership validation;
- dummy family, state/backend identity, type, and ordinary-ownership checks;
- explicit trace events and local operation counters.

Focused tests cover all six initial three-point orders, exact boundary results
for all 24 four-point and all 120 five-point permutations, both infinity
dummies, both endpoints of `P2` and `P3`, the missing lower-family pair at
`z1`, odd predecessor/successor adjustments, adjusted finite and dummy
outcomes, corrupted pair/list ownership, corrupted dummy identity/family/
ownership, trace ordering, and iteration guards.

Day 3 checkpoint purity/scope check:

```text
the Day 3 source contained no oracle call
the Day 3 source contained no rank_map call
the Day 3 source contained no sorted() call
the Day 3 source contained no Step 3 implementation
the Day 3 source contained no complete paper loop
```

Day 3 verification:

```text
python -m unittest tests.test_paper_jordan:
    Ran 20 tests
    OK

python -m unittest discover -s tests:
    Ran 254 tests
    OK
```

## Day 4: Step 3(a) and Step 3(b)

Status: approved; ready for Day 5.

Implemented:

- `Step3AResult` and `Step3BResult`;
- increasing/decreasing orientation validation;
- strict finite-pair enclosure and dummy enclosure;
- Step 3(a) singleton-list creation;
- increasing insertion after the left boundary;
- decreasing insertion before the right boundary;
- Step 3(a) registration rollback through
  `unregister_unowned_pair`;
- Step 3(b) skip when the opposite boundary encloses the previous point;
- increasing acquisition of the left split side;
- decreasing acquisition of the right split side;
- one-sided and two-nonempty-side ownership transfers;
- O(1) Step 1/2 boundary-source stage validation;
- Step 3(a)-before-Step 3(b) stage validation;
- distinct split scan/copy/ownership-transfer counters and explicit trace
  output.

Focused tests reproduce Trace A, Trace B, Trace C, the decreasing boundary
insertion mirror, Trace F, and Trace F's value-reflected counterpart. They also
cover wrong orientation, wrong boundary side, failed-registration rollback,
both skip paths, and both acquisition directions. A differential gate executes
one structural iteration for all 16 oracle-valid four-point permutations and
checks sibling-backend invariants without passing oracle output into the core.

Independent ownership differential validation also compared every actual
finite-pair parent with the parent implied by strict same-family interval
containment:

```text
n=4:  16 oracle-valid permutations, all matched
n=5:  50 oracle-valid permutations, all matched
n=6: 144 oracle-valid permutations, all matched
n=7: 462 oracle-valid permutations, all matched
total: 672, all matched
```

The implementation now keeps per-iteration stage results in an O(1) mapping.
Diagnostic trace entries remain available, but Step 3 preconditions no longer
rescan the complete trace. Split metrics distinguish all input items copied by
the ordinary-list backend from acquired-side items transferred to the new
pair.

Follow-up coverage locks the copy/transfer counters for increasing and
decreasing two-sided splits, confirms both skip orientations leave the
counters unchanged, and verifies that repeated Step 3(a) or Step 3(b) calls
leave trace, metrics, stage state, partial order, and backend ownership
unchanged.

Scope boundary:

```text
z_i is not inserted into SortedOrderList
processed_count remains i - 1
output_insertions remains 0
no step3c function exists
no complete paper loop exists
```

Day 4 verification:

```text
python -m unittest tests.test_paper_jordan:
    Ran 40 tests
    OK

python -m unittest tests.test_sibling_list_backend:
    Ran 26 tests
    OK

python -m unittest discover -s tests:
    Ran 276 tests
    OK

python -m compileall -q src experiments tests:
    passed

git diff --check:
    passed
```

## Day 5: Independent Step 3(c) Output Insertion

Status: implementation complete; awaiting review before the end-to-end loop.

Implemented:

- immutable `Step3CResult`;
- increasing insertion after the selected output anchor;
- decreasing insertion before the selected output anchor;
- no-child fallback to `z_(i-1)`;
- geometric extreme-child anchor selection;
- odd-index `z1` output-anchor adjustment in both directions;
- O(1) Step 3(a)/(b)/(c) stage guards;
- successful advancement of `processed_count`;
- output insertion, adjustment, trace, and stage-result instrumentation;
- failure and repeat-call state atomicity tests.

Focused coverage includes all four parent/child orientation combinations,
inside/outside odd-index adjustment cases, both no-child directions, all 16
oracle-valid four-point permutations, and stable trace fields.

Scope boundary:

```text
Step 3(c) is callable only as an independent stage
no production end-to-end paper loop exists
no experiment runner calls the paper implementation
no oracle, rank_map, or global sorting is used by the core
```

Checkpoint verification:

```text
python -m unittest tests.test_paper_jordan:
    Ran 49 tests
    OK

python -m unittest discover -s tests:
    Ran 285 tests
    OK

python -m compileall -q src experiments tests:
    passed

git diff --check:
    passed
```

## Next Step

Review the independent Step 3(c) checkpoint. After approval:

```text
assemble the complete paper loop
handle n=0, n=1, n=2, and n=3 explicitly
return output only from SortedOrderList
add exhaustive valid-input differential tests
```
