# Week 9 Plan: Ordinary-List Implementation of the 1990 Jordan-Sorting Algorithm

Last updated: 2026-07-27

## Relationship to the Revised Thesis Direction

This plan implements the Week 9 portion of:

```text
docs/plan/refined_thesis_direction_after_week8.md
```

The existing reference framework remains available and unchanged. Week 9 adds a
separate implementation of the high-level algorithm in Section 2 of the 1990
paper, using ordinary lists for the Section 3 sibling-list operations.

The completed formal generator-coverage run remains usable evidence. The
interrupted reference-framework performance run is not a completed experiment
and must not be resumed as the final thesis experiment.

## Main Goal

Build the first correctness-oriented implementation of:

```text
paper algorithm control flow
+ incremental partial sorted order
+ dynamic sibling lists
+ make-list / boundary-insert / split semantics
+ independent sorted-order recovery
+ tests, trace, and operation counters
```

The implementation must not claim linear running time.

## Scope

### In Scope

- implementation-facing reconstruction of Section 2;
- behavior for `n < 3` and initialization with the first three points;
- incremental processing of `z_i` for `i = 4..n`;
- predecessor/successor access in the maintained partial order;
- upper/lower pair-family selection from paper indices;
- dynamic sibling-list creation, insertion, and splitting;
- Step 3(c) output insertion;
- both adjacent-point orientations;
- final output recovered from maintained algorithm state;
- focused unit tests and bounded correctness validation;
- trace events and operation counters.

### Out of Scope

- heterogeneous finger trees;
- level-linked search trees;
- a theoretical linear-time backend;
- polygon clipping;
- thesis-scale performance experiments;
- major new generator families;
- interactive visualization;
- any linear-time claim.

## Planned Files

### New

```text
docs/design/paper_algorithm_ordinary_list.md
src/partial_sorted_list.py
src/sibling_list_backend.py
src/paper_jordan_sort.py
tests/test_partial_sorted_list.py
tests/test_sibling_list_backend.py
tests/test_paper_jordan_sort.py
experiments/validate_paper_algorithm.py
docs/progress/week9_summary.md
```

### Updated Only After Interfaces Stabilize

```text
src/instrumentation.py
experiments/run_week7_pilot.py
docs/design/theory_to_implementation_mapping.md
docs/design/final_experiment_spec.md
docs/thesis/implementation_draft.md
README.md
```

The experiment schema is not changed until the paper algorithm passes its
correctness gate.

## Fixed Boundaries

### Indexing

```text
paper indices: 1-based
Python sequence storage: 0-based
```

Use a shared conversion helper instead of repeating `i - 1` throughout the
algorithm.

### Pair-Family Parity

For the pair ending at paper index `i`:

```text
i even -> upper family
i odd  -> lower family
```

### Algorithm Purity

The core interface:

```python
paper_jordan_sort_valid(seq)
```

must not call or read:

```text
oracle(seq)
rank_map(seq)
sorted(seq)
oracle_result["sorted"]
simplified_jordan_reference
```

A separate validation wrapper may call the oracle to reject invalid inputs. It
must pass only the original sequence into the core and must not be used for pure
sorting timings.

### Two Different Insert Operations

Keep these operations separate:

```text
SortedOrderList.insert_before / insert_after
OrdinarySiblingListBackend.insert_at_boundary
```

The sibling-list operation implements the paper's restricted `insert(x, y)`.
It is not arbitrary middle insertion.

## Day 1: Freeze the Executable Specification

### Objective

Translate Sections 2 and 3 into an implementation-facing specification before
writing the main algorithm.

### Required Work

- map paper symbols to Python state;
- fix the 1-based/0-based boundary;
- define pair identity and point-to-pair selection;
- separate curve-order pair endpoints from geometric left/right endpoints;
- define the upper/lower parity rule;
- define two family-specific dummy pairs;
- define partial-order sentinels;
- define sibling-list ownership and child-list ownership;
- write initialization and Step 1/2/3 pseudocode;
- write the decreasing-orientation mirror explicitly;
- define `n = 0, 1, 2, 3` behavior;
- define core and validation-wrapper contracts;
- provide one complete worked trace;
- record unresolved interpretations rather than hiding them.

### Deliverable

```text
docs/design/paper_algorithm_ordinary_list.md
```

### Gate

- every paper step has a planned state transition;
- no step relies on a global rank map;
- output is planned to come from `SortedOrderList`;
- sentinel and parity behavior are explicit;
- sibling-list and output-list insertion are not conflated;
- unresolved Step 3 ownership questions are visible;
- Step 3(c) is checked against all four parent/child orientation combinations;
- odd-index `z1` output-anchor adjustment is specified in both directions;
- at least one split trace has two nonempty outputs;
- no main algorithm code is written before this document is coherent.

## Day 2: Implement Core Data Structures

### Partial Sorted Order

Implement a doubly linked list with:

```text
point-id -> node mapping
negative/positive sentinel nodes
predecessor
successor
insert_before
insert_after
forward/backward validation
sentinel-free output extraction
```

### Point and Pair Records

Use stable paper indices and stable pair IDs. Pair records preserve curve order
and record:

```text
end_index
family
owning sibling-list id
child sibling-list ids
```

Geometric endpoint helpers select the smaller or larger endpoint by comparison;
they must not treat the curve-order second endpoint as the geometric right
endpoint.

Step 3(c) first selects this geometric base anchor. For odd paper indices, the
output anchor changes to `z1` when `z1` lies strictly between the base anchor
and the new point. This output adjustment is separate from the Step 1 and Step
2 boundary-pair adjustment.

### Ordinary Sibling-List Backend

Implement:

```text
make_list
insert_at_boundary
split
```

The backend must preserve order, reject illegal ownership, and never lose or
duplicate pair IDs.

### Tests

- all small partial-order shapes;
- all six three-point orders;
- predecessor/successor boundaries;
- duplicate insertion rejection;
- front/back sibling insertion;
- illegal middle insertion rejection;
- singleton, empty-side, and two-sided splits;
- ownership updates;
- optional counter increments.

### Gate

All focused and existing tests pass. No data-structure operation imports the
oracle or rank map.

## Day 3: Initialization, Step 1, and Step 2

### Initialization

For `n >= 3`, create:

```text
partial order containing z1, z2, z3
upper pair {z1, z2}
lower pair {z2, z3}
one singleton sibling list for each finite initial pair
upper and lower dummy pairs
point, pair, ownership, trace, and counter state
```

Use a fixed comparison procedure for two or three points. Do not call `sorted`.

### Step 1

- find the predecessor of `z_(i-1)`;
- apply the odd-`i` `z1` exception;
- select the processed same-family pair containing that point;
- use the correct family dummy pair at negative infinity.

### Step 2

- find the successor of `z_(i-1)`;
- apply the odd-`i` `z1` exception;
- select the processed same-family pair containing that point;
- use the correct family dummy pair at positive infinity.

### Gate

Direct unit tests cover odd/even parity, both sentinels, the `z1` exception, and
handcrafted boundary states. Step 1/2 are not tested only through the full loop.

## Day 4: Step 3(a) and Step 3(b)

This is the highest-risk implementation stage.

### Step 3(a)

- create the new pair;
- select its family;
- determine whether it starts a singleton sibling list or joins an existing
  sibling list;
- insert only at a legal sibling-list boundary;
- update ownership and trace.

### Step 3(b)

- determine whether the new pair acquires children;
- locate the child sibling-list region;
- partition it at `z_i`;
- preserve order and update all ownership maps;
- attach the acquired child list to the new pair;
- retain the non-acquired portion under its previous owner;
- handle empty, one-sided, and two-sided results.

### Raw Split Fields

```text
input size
left size
right size
items scanned
items moved
split boundary
```

Potential-function values are not required on Day 4.

### Fallback Rule

If Step 3(b) is ambiguous or incorrect:

1. stop adding features;
2. preserve the smallest failing processed prefix;
3. record the exact paper sentence and state interpretation;
4. inspect the first ownership invariant that fails;
5. do not use oracle-sorted output as a workaround.

## Day 5: Step 3(c), Symmetry, and End-to-End Output

### Step 3(c)

- if the new pair has no children, insert `z_i` adjacent to `z_(i-1)`;
- otherwise select the required extreme child;
- insert `z_i` at the paper-specified output anchor;
- update the linked partial order and trace.

### Symmetric Case

Use direction-aware helpers where they genuinely preserve the paper semantics.
Do not call a branch "symmetric" without separate increasing and decreasing
tests.

### Main Loop

```text
initialize
for i = 4..n:
    Step 1
    Step 2
    Step 3(a)
    Step 3(b)
    Step 3(c)
return partial_order.to_list()
```

### Hard Gate

Do not begin experiment integration unless:

- both orientations work;
- final output comes from the partial sorted-order list;
- the fixed basic valid set passes;
- no core path uses oracle sorting or a global rank map.

## Day 6: Correctness, Invariants, and Instrumentation

### Online Core Invariants

- each processed point occurs once;
- output links are consistent;
- adjacent output values are strictly increasing;
- every processed pair has the correct family;
- each finite pair has one sibling-list owner;
- no sibling list contains duplicates;
- split outputs preserve and partition their input;
- parent pairs are not in their own child lists;
- sentinels are used only for boundaries;
- every iteration has complete trace coverage.

### External Differential Checks

The test/validation layer may compare:

```text
partial output == sorted(processed prefix)
final output == sorted(input)
```

Those expected values must never feed back into core state.

### Exhaustive Validation

Required target:

```text
n <= 7
```

Preferred standalone target:

```text
n <= 8
```

Full enumeration belongs in `experiments/validate_paper_algorithm.py` or an
explicit slow test, not in the routine unit suite.

### Random Validation

Start with a bounded, reproducible set:

```text
families: flat_valid, nested_valid, incremental_valid
sizes: 16, 32, 64, 128
fixed seeds
10 cases per randomized family and size
```

Increase repetitions only after runtime is measured. Every failure records
family, size, seed, case ID, processed prefix, and first failed invariant.

### Independence Guards

Tests must protect against:

- importing or calling `rank_map` from the core module;
- using the existing reference skeleton as output;
- reading oracle-sorted metadata;
- aliasing wrapper output to oracle-sorted output.

## Day 7: Integration, Small Pilot, and Handoff

### Algorithmic Ladder

Keep:

```text
simplified_jordan_reference
```

Add:

```text
simplified_jordan_paper_ordinary_list
```

### Separate Configurations

Sorting pilot:

```text
valid families only
python_sort
simplified_jordan_reference
simplified_jordan_paper_ordinary_list
```

Recognition pilot:

```text
valid and invalid families
sort_plus_laminarity_check
simplified_jordan_reference
```

### Small Pilot Only

Suggested initial pilot:

```text
sizes: 8, 16, 32
randomized cases: 2
warm-up runs: 1
measured runs: 3
```

It validates integration, schemas, manifests, correctness, and rough runtime.
It is not final performance evidence.

### Documentation

Update implementation status only after the corresponding gate passes:

- theory-to-implementation mapping;
- implementation draft;
- experiment specification;
- README;
- `docs/progress/week9_summary.md`.

## Operation Counters

Initial counters:

```text
predecessor_accesses
successor_accesses
boundary_pair_checks
sibling_scan_checks
sibling_lists_created
sibling_list_insertions
sibling_list_splits
split_items_scanned
split_items_moved
output_insertions
invariant_checks
trace_event_count
```

When instrumentation changes runtime materially, time the plain algorithm and
collect detailed diagnostics in one separate execution per case.

## Final Definition of Done

Week 9 may be declared complete only when:

1. initialization and Step 1/2/3 are implemented;
2. both orientations are supported;
3. ordinary `make-list`, boundary insertion, and split semantics exist;
4. final output comes from the maintained partial sorted order;
5. the core does not use oracle-sorted output, rank map, or full sorting;
6. basic correctness and intermediate invariants pass;
7. bounded exhaustive and randomized validation pass;
8. the existing reference baseline remains available;
9. all routine tests pass;
10. a small integration pilot validates cleanly;
11. no thesis-scale performance experiment has run prematurely;
12. documentation distinguishes the paper algorithm from the theoretical
    linear-time backend.

## Risk Priority

If the week overruns, prioritize:

```text
1. executable specification
2. state and list structures
3. Step 1/2/3 correctness
4. independent output recovery
5. basic tests
6. exhaustive validation
7. invariants
8. instrumentation
9. pilot integration
10. optional analysis
```

The following may move into Week 10:

- potential-function replay;
- large randomized validation;
- final metric naming;
- pilot expansion;
- trace visualization.

The following cannot be postponed if Week 9 is declared complete:

- independent output recovery;
- Step 1/2/3 implementation;
- ordinary list-operation semantics;
- basic correctness tests;
- oracle-output independence.
