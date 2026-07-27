# Week 9 Summary

Last updated: 2026-07-27

## Goal

Week 9 moved the project from an oracle-backed reference framework to an
ordinary-list implementation of the high-level 1990 Jordan-sorting control
flow for pre-certified valid inputs.

The week did not implement heterogeneous finger trees and does not claim
linear time.

## Implemented Algorithm

The new valid-input path is:

```text
paper_jordan_sort_valid(seq)
    -> initialize the first three points and pair families
    -> for i = 4..n:
         Step 1 predecessor boundary
         Step 2 successor boundary
         Step 3(a) pair insertion
         Step 3(b) sibling-list split/ownership transfer
         Step 3(c) output insertion
    -> state.partial_order.to_list()
```

The final output is recovered only from the maintained partial sorted order.
The core does not call the oracle, `rank_map`, Python `sorted()`, or the
reference skeleton.

## Ordinary Data Structures

Week 9 added:

```text
SortedOrderList
OrdinarySiblingListBackend
PaperJordanState
BoundarySelection
Step3AResult
Step3BResult
Step3CResult
```

The sibling backend supports singleton-list creation, legal boundary
insertion, ordinary-list split materialization, atomic ownership transfer,
rollback, dummy roots, parent-chain validation, and canonical audit snapshots.

## Correctness Evidence

Repository differential tests cover every oracle-accepted permutation through
`n=7`. The standalone validator extends exhaustive validation through `n=8`
and checks fixed-seed generated cases:

```text
exhaustive n=0..8:
    2,074 valid permutations

complete-loop n=4..8:
    2,064 valid permutations

generated validation:
    4 flat cases
    4 nested cases
    40 incremental cases
    sizes 16, 32, 64, 128
```

An additional external review enumerated all 4,536 valid `n=9` permutations.
That review is supporting evidence; the repository's default reproducible
validator remains bounded at `n=8`.

## State Audit

Diagnostics and production sorting share one Step 1/2/3 runner. Complete
diagnostics are untimed and validate:

```text
partial-order links and PointRef identity
all current and future point values against the backend data source
exact pair and sibling-list registries
dummy roots and parent ownership
typed stage records
strict trace order and payload
operation metrics
deterministic replay through the processed prefix
canonical backend state after replay
```

Regression tests reject isolated and coordinated corruption of stage records,
trace events, metrics, pair registries, sibling-list identifiers, child
selection, split sizes, the complete point tuple, and unprocessed future
points.

## Day 7 Integration Pilot

The experiment-facing algorithm name is:

```text
simplified_jordan_paper_ordinary_list
```

Two separate small pilots were run from clean commit `7d05901`:

### Sorting Pilot

```text
families:
    flat_valid
    nested_valid
    incremental_valid

algorithms:
    python_sort
    simplified_jordan_reference
    simplified_jordan_paper_ordinary_list

sizes: 8, 16, 32
randomized cases: 2
warm-up runs: 1
measured runs: 3

rows:
    raw = 108
    case summary = 36
    group summary = 27
```

### Recognition Pilot

```text
families:
    all seven existing valid/invalid generator families

algorithms:
    sort_plus_laminarity_check
    simplified_jordan_reference

sizes: 8, 16, 32
randomized cases: 2
warm-up runs: 1
measured runs: 3

rows:
    raw = 180
    case summary = 60
    group summary = 42
```

Both output validators returned:

```text
valid = true
errors = []
all raw errors empty
all overall_correct = true
```

Paper diagnostics were collected once per case outside the timed region and
were written only to paper-algorithm rows. Sorting and recognition outputs use
separate directories and manifests.

## Timing Boundary

The pilot demonstrates integration, correctness, schema stability, output
isolation, manifest generation, and rough executability only.

It is not final performance evidence because the timed ordinary-list paper path
still includes:

```text
trace recording
operation-counter updates
correctness-first sibling-backend commit validation
ordinary Python list split costs
```

Complete deterministic replay diagnostics are excluded from timing.

## Verification

```text
python -m unittest discover -s tests:
    Ran 322 tests
    OK

python -m compileall -q src experiments tests:
    passed

python experiments/validate_paper_algorithm.py --max-n 8:
    passed

sorting pilot output validator:
    valid = true

recognition pilot output validator:
    valid = true

git diff --check:
    passed
```

## Week 10 Handoff

Week 10 should not immediately run thesis-scale benchmarks. It should first:

1. define a timing mode that excludes complete backend commit validation;
2. preserve an equivalent untimed correctness audit for every case;
3. decide whether trace/counter recording remains in the measured paper path;
4. add a validated public wrapper that separates recognition from valid-input
   sorting without hiding oracle work inside paper timing;
5. freeze the paper-algorithm experiment configuration only after a timing
   contamination study.

