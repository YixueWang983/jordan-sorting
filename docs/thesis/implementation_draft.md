# Implementation Draft

Last updated: 2026-07-27

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

## Ordinary-List Paper Algorithm

`paper_jordan_sort_valid(seq)` implements the high-level 1990 control flow for
pre-certified valid inputs. It maintains an incremental sorted-order linked
list and two parity-defined sibling-list families. Each iteration performs
predecessor/successor boundary selection, inserts the new pair, applies any
required sibling-list split and ownership transfer, and inserts the current
point into the partial output.

The output is:

```text
state.partial_order.to_list()
```

It is not taken from the oracle or the reference skeleton.

The implementation uses ordinary Python lists rather than heterogeneous finger
trees. Its correctness and operation semantics can therefore be evaluated,
but its runtime cannot be presented as an implementation of the theoretical
linear-time backend.

## Paper-State Validation

The diagnostics path shares the production Step 1/2/3 runner. It performs
prefix invariants and deterministic replay outside timed regions, comparing
stage records, traces, metrics, point data, partial output, and a canonical
sibling-backend snapshot.

## Experiment Runner

The pilot/formal benchmark runner generates cases outside timed regions, uses
fresh input copies, controls GC during timing, records correctness fields, writes
case/group summaries, writes environment metadata, and supports no-overwrite run
directories.

The Week 9 integration runner separates:

```text
valid-input sorting:
    python_sort
    simplified_jordan_reference
    simplified_jordan_paper_ordinary_list

recognition:
    sort_plus_laminarity_check
    simplified_jordan_reference
```

## Implementation Limitations

- No level-linked search trees.
- No heterogeneous finger trees.
- No specialized finger-tree split/update engine.
- No polygon clipping pipeline.
- No linear-time claim.
- The reference baseline still returns oracle-sorted output.
- The paper ordinary-list sorter requires pre-certified valid input.
- Current paper timing includes trace/counter and backend commit-validation
  overhead.
