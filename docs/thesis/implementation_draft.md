# Implementation Draft

Last updated: 2026-07-24

## Oracle

The oracle implements the project validity predicate for candidate Jordan
sequences. It checks:

```text
distinct values
upper family laminarity
lower family laminarity
```

The current laminarity check is pairwise and quadratic. Duplicate values are
rejected before rank intervals are interpreted.

## Generators

The generator module provides controlled valid and invalid families. Some
families are deterministic, while incremental, random-invalid, and
mutation-based families depend on seeds.

Generator family names are construction labels. Structural category is computed
after generation by `structure_profile`.

## Family-Tree Representation

Family trees represent static nesting structure within one pair family. Nodes
preserve input interval order. Root-level siblings are stored in `roots`, and
non-root siblings are stored in each node's ordered `children` list.

The current implementation uses ordinary Python lists and scans candidate
containers directly.

## Reference Pipeline

`simplified_jordan_sort(seq)` is a reference skeleton with a stable public return
contract. It:

1. copies input;
2. runs the oracle;
3. builds operation trace fields;
4. builds family trees for valid inputs;
5. computes structural stats;
6. returns `oracle_result["sorted"]`.

It does not recover sorted order through theoretical family-tree operations.

## Structural Metrics

`structure_profile(seq)` records interval counts, root counts, parented interval
ratio, containment pair counts, containment pair density, crossing severity for
invalid distinct candidates, max depth, and structural category.

`nesting_density` is retained as a legacy field and means:

```text
parented intervals / total intervals
```

## Instrumentation

`instrumented_reference_run(seq)` is an experiment-only wrapper. It returns the
same reference-style result plus selected operation counters. It does not change
the public return contract of `simplified_jordan_sort`.

Counters cover selected validation and family-tree construction operations, not
total computational cost.

## Experiment Runner

The pilot/formal benchmark runner generates cases outside timed regions, uses
fresh input copies, controls GC during timing, records correctness fields, writes
case/group summaries, writes environment metadata, and supports no-overwrite run
directories.

## Implementation Limitations

- No level-linked search trees.
- No heterogeneous finger trees.
- No dynamic split/update engine.
- No polygon clipping pipeline.
- No linear-time claim.
- Sorted output is still oracle-sorted output.

