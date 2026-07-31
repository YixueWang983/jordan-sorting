# Refined Thesis Direction After Week 8

Last updated: 2026-07-27

## Status and Scope Revision

Weeks 1-8 established a correctness-oriented and experiment-oriented
Jordan-sorting reference framework. The official thesis direction is to
implement and evaluate the 1990 Simplified Jordan Sorting algorithm, so the
reference framework is now treated as infrastructure and as an experimental
baseline rather than as the final algorithmic deliverable.

This document revises the post-Week-8 implementation plan. It expands the
previous minimum reference-framework boundary by adding:

- the incremental control flow from Section 2 of the 1990 paper;
- dynamic sibling-list maintenance;
- ordinary-list `make-list`, boundary insertion, and split operations;
- sorted-order recovery from the maintained algorithm state.

The supervisor decision recorded after Week 8 remains a valid record of the
accepted minimum scope. This expanded algorithmic deliverable should be recorded
as a scope amendment before the thesis claims are frozen. Until then, it is the
project's working implementation target, not a claim that the expanded scope has
already been approved.

The completed `week9_formal_coverage` run remains useful generator evidence. It
does not need to be repeated unless the generators, metrics, or coverage
configuration change. The interrupted formal performance run is not thesis
evidence and must not be resumed until the paper algorithm passes its
correctness gates.

## Core Deliverable

The revised main deliverable is:

```text
An executable, testable, and instrumented reconstruction of the 1990
Simplified Jordan Sorting algorithm using an ordinary-list sibling-list
backend, together with an empirical explanation of the gap between the
high-level algorithm and its theoretical linear-time data structures.
```

The implementation must preserve:

- incremental processing of `z_1, ..., z_n`;
- predecessor and successor access in the partial sorted order;
- upper/lower pair-family selection;
- dynamic sibling-list maintenance;
- the paper's Step 1, Step 2, and Step 3(a-c);
- `make-list`, boundary insertion, and split semantics;
- independent recovery of the sorted order from algorithm state.

The implementation does not include:

- heterogeneous finger trees;
- level-linked search trees;
- a theoretical linear-time backend;
- polygon clipping;
- a proof or claim of linear running time.

Linear scans and Python list slicing are permitted in the sibling-list backend.
The backend exists for correctness, observability, and experimental analysis.

## Refined Research Questions

The thesis uses three main research questions. Locality, split behavior, and
cost decomposition are subquestions of RQ3 rather than separate top-level
research questions.

### RQ1: Algorithmic Correctness

Can an ordinary-list reconstruction of the 1990 Simplified Jordan Sorting
algorithm independently recover the sorted order of oracle-accepted candidate
Jordan sequences?

Correctness requires:

- every processed point appears exactly once;
- the partial output remains ordered after every iteration;
- pair-family and sibling-list invariants remain valid;
- the final output agrees with the independent test oracle.

The paper-algorithm core must not obtain its output from:

```text
oracle_result["sorted"]
global rank_map(seq)
full-input sorted(seq)
```

The project must document why distinct values plus upper/lower laminarity are
the validity model used for the tested Jordan sequences. Until that equivalence
is stated explicitly, documentation should use the conservative term
`oracle-accepted candidate Jordan sequences`.

### RQ2: Structural Coverage

What structures are actually produced by the generator families?

Primary metrics:

```text
structural_category
max_depth
parented_interval_ratio
containment_pair_density
crossing_pair_density
invalid_reason
duplicate_case_rate
```

Generator names are labels, not evidence of structure. Structural claims must
come from measured outputs. Existing validated coverage evidence may be reused
when its generators and configuration remain unchanged.

### RQ3: Structure, Locality, and Ordinary-Backend Cost

How do input structure, locality, and sibling-list shape affect the operation
cost of the ordinary-list implementation, and which costs would the theoretical
data structures be expected to reduce?

Primary explanatory variables:

```text
n
max_depth
containment_pair_density
sibling_list_size
split_count
split_balance
items_moved
sibling_scan_checks
global_candidate_count
local_candidate_count
locality_reduction_ratio
```

The analysis may compare these implementation levels:

```text
python_sort
sort_plus_laminarity_check
simplified_jordan_reference
simplified_jordan_paper_ordinary_list
```

Recognition and sorting timings must remain separate so that invalid-input
recognition cost is not reported as paper-algorithm sorting cost.

## Implementation Architecture

The existing `simplified_jordan_reference` remains unchanged as a baseline.
The paper implementation is introduced under separate modules and names.

Recommended modules:

```text
src/paper_jordan_sort.py
src/sibling_list_backend.py
tests/test_paper_jordan_sort.py
tests/test_sibling_list_backend.py
```

The implementation requires four explicit state layers.

### Partial Sorted Order

Use a doubly linked sorted-order structure with a point-to-node map:

```python
class SortedOrderList:
    def predecessor(self, point): ...
    def successor(self, point): ...
    def insert_after(self, anchor, point): ...
    def insert_before(self, anchor, point): ...
    def to_list(self): ...
```

This prevents `list.index()` scans from being mistaken for the predecessor and
successor behavior assumed by the paper. It also keeps output insertion
separate from sibling-list insertion.

Boundary sentinels must have explicit identities and behavior. They must not be
represented by numeric values that can collide with input data.

### Pair Records

Each algorithm pair needs a stable identity and explicit ownership metadata:

```text
PairId
original endpoint indices
endpoint values
upper or lower family
parent relation when known
owning sibling-list id
```

The specification must explain how a point maps to the parity-compatible pair
selected in Step 1 or Step 2. Pair selection must use original sequence indices
and maintained algorithm state, not a global rank map.

### Sibling Lists

Sibling lists use stable list identifiers. Each finite pair must be owned by
exactly one sibling list at a time.

The ordinary backend exposes:

```python
class SiblingListBackend:
    def make_list(self, item): ...
    def insert_at_boundary(self, item, anchor): ...
    def split(self, boundary, list_id): ...
```

`insert_at_boundary` implements the paper's Section 3 `insert(x, y)` semantics:
the anchor must be at the appropriate front or back boundary of its list.
Arbitrary middle insertion is not part of this operation.

`split(boundary, list_id)` returns one list containing items whose represented
points are at most the boundary and another containing the remaining items.
The exact comparison key for a pair must be fixed in the implementation-facing
specification.

### Algorithm State

The algorithm state owns:

- processed sequence indices;
- the partial sorted-order list;
- pair records and point-to-pair mappings;
- upper/lower sibling-list collections;
- pair ownership maps;
- trace events and optional counters.

## Public Interfaces and Purity Boundary

The pure core interface is:

```python
paper_jordan_sort_valid(seq)
```

It assumes a valid input and must not:

- call the oracle;
- call `rank_map`;
- read `oracle_result["sorted"]`;
- call `sorted(seq)` on the complete input.

A separate composition wrapper may be provided:

```python
validated_paper_jordan_sort(seq)
```

The wrapper may call the oracle to reject invalid input. It must not pass the
oracle's sorted result into the core. Because oracle validation itself performs
ordinary sorting, this wrapper must be excluded from pure paper-algorithm
sorting timings.

## Paper-Algorithm Trace

Each processed point records events corresponding to the paper:

```text
initialize
step1_find_predecessor
step1_select_boundary_pair
step2_find_successor
step2_select_boundary_pair
step3a_insert_pair
step3b_split_sibling_list
step3c_insert_output_point
check_invariants
```

Skipped or empty operations still receive a trace event with
`performed = false` and a reason. This keeps one complete trace contract per
iteration.

Relevant fields include:

```text
iteration
previous_point
current_point
selected_pair
pair_family
sibling_list_id
sibling_list_size
split_left_size
split_right_size
output_anchor
output_insertion_side
```

At least one worked trace must be converted into a thesis table or figure.

## Executable Invariants

Core online checks may verify:

1. every processed point appears exactly once;
2. adjacent points in the partial output are ordered;
3. each pair belongs to the family dictated by its original parity;
4. a parent pair is not contained in its own sibling list;
5. each pair is owned by exactly one sibling list;
6. items in each sibling list follow the specified order;
7. split outputs satisfy the selected boundary;
8. every transferred child appears in exactly one split result;
9. Step 3(c) inserts the new point at the required anchor;
10. sentinel links and endpoint behavior remain consistent.

The stronger differential assertion:

```text
partial output == sorted(processed prefix)
```

belongs in external tests or validation scripts. It may inspect trace snapshots,
but it must not influence core algorithm decisions or timed execution.

## Operation Instrumentation

The paper implementation records:

```text
predecessor_accesses
successor_accesses
sibling_scan_checks
boundary_pair_checks
sibling_lists_created
sibling_list_insertions
sibling_list_splits
split_items_copied
split_items_transferred
output_insertions
trace_event_count
invariant_check_count
```

When diagnostics materially affect runtime, collect them in a separate untimed
execution of the same case.

Locality metrics use fixed definitions:

```text
global_candidate_count:
    all candidate pairs in the relevant family before the step

local_candidate_count:
    candidate pairs in the sibling-list region selected by locality

sibling_items_inspected:
    items actually examined by the ordinary backend

locality_reduction_ratio:
    1 - local_candidate_count / global_candidate_count
```

When `global_candidate_count == 0`, the reduction ratio is recorded as empty
rather than inventing a numeric value.

## Optional Potential-Function Replay

Potential-function replay is an optional explanatory analysis, not a Week 10
correctness gate.

If implemented, it must state:

- logarithms use base 2, following the paper;
- the potential for an absent or empty list is defined explicitly;
- `log(0)` is never evaluated;
- splits with an empty side are treated separately from the paper's
  two-nonempty-side calculation;
- the constant `c` is illustrative and is not fitted as proof of ordinary-list
  complexity.

For eligible splits, an offline analysis may compare:

```text
input size
left and right output sizes
minimum and maximum side sizes
split balance
potential change
actual items scanned
actual items copied
actual items transferred
```

This analysis explains the theoretical amortization argument. It does not show
that the ordinary-list backend has the same asymptotic behavior.

## Experiment Separation

### Recognition

Recognition accepts valid and invalid candidate sequences and evaluates:

```text
oracle validation
sort_plus_laminarity_check
simplified_jordan_reference
```

### Sorting

Paper-algorithm sorting accepts pre-certified valid inputs only and evaluates:

```text
python_sort
simplified_jordan_reference
simplified_jordan_paper_ordinary_list
```

The timed region must state whether validation is included. Pure
`paper_jordan_sort_valid` timing excludes validation. If a validated end-to-end
variant is measured, it is reported as a separate algorithm.

## Revised Schedule

### Week 9: Executable Specification and Core Prototype

Required:

- write `docs/design/paper_algorithm_ordinary_list.md`;
- define the state model, pair mapping, sentinels, and invariants;
- provide implementation-facing Step 1/2/3 pseudocode;
- work through at least one complete example by hand;
- implement `SortedOrderList`;
- implement the ordinary sibling-list backend;
- implement initialization and Step 1/2;
- keep all existing tests green.

Target if debugging permits:

- implement Step 3(a-c) and the symmetric case;
- recover final output from the maintained sorted-order list.

Week 9 is not considered failed if Step 3 debugging continues into Week 10.
No formal performance experiment is allowed during this stage.

### Week 10: Complete Algorithm and Correctness Validation

- finish Step 3(a-c) and the symmetric case;
- add executable core invariants;
- test each paper step independently;
- exhaustively test oracle-accepted permutations for small `n`;
- run randomized valid-case differential validation;
- add trace and stable operation counters;
- fix all correctness mismatches.

The routine unit suite should contain a bounded representative subset.
Full `n <= 8` enumeration belongs in a dedicated validation script or explicitly
marked slow test so normal development remains usable.

### Week 11: Experiment Integration and Pilot

- register `simplified_jordan_paper_ordinary_list` separately;
- separate recognition and sorting configurations;
- update CSV schemas, manifests, expected row counts, and validators;
- reuse existing coverage evidence when its inputs remain unchanged;
- run a small pilot only;
- estimate formal runtime and inspect split/locality distributions;
- freeze the final experiment specification.

### Week 12: Formal Experiments

- freeze machine and environment;
- run formal valid-input sorting experiments;
- run recognition experiments separately;
- validate all outputs;
- preserve configs, manifests, hashes, summaries, and reports;
- use new run IDs for reruns instead of overwriting evidence.

### Week 13: Analysis and Figures

- runtime and operations by algorithm and size;
- structure-sensitive costs;
- locality reduction;
- split count, balance, items copied, and items transferred;
- generator family versus measured structural category;
- optional potential-function replay.

### Weeks 14-15: Thesis Chapters

- algorithm reconstruction and locality lemma;
- ordinary-list implementation and invariants;
- experimental methodology and coverage;
- correctness, performance, and structure-sensitive results;
- threats to validity, limitations, and future work.

### Week 16: Integration and Finalization

- integrate chapters;
- verify terminology, citations, figures, and code mappings;
- rerun tests and reproduction commands;
- incorporate supervisor feedback;
- prepare the final PDF and defense slides.

## Gates

### Algorithm Gate

- initialization and Step 1/2/3 have explicit code mappings;
- final output comes from the maintained sorted-order state;
- no core decision uses oracle-sorted output, global rank map, or full sorting;
- basic, exhaustive, and randomized correctness checks pass;
- sibling-list ownership and split invariants pass;
- ordinary-list and no-linear-time boundaries are explicit.

### Experiment Gate

- recognition and sorting are configured separately;
- correctness is established before performance;
- counters and trace semantics are stable;
- pilot outputs validate cleanly;
- runtime is feasible;
- no schema redesign is expected after the gate.

### Thesis Gate

- theory, implementation, experiments, and limitations are separated;
- every major claim has code, tests, generated evidence, or a citation;
- no text implies implementation of heterogeneous finger trees,
  level-linked trees, polygon clipping, or a linear-time backend.

## Explicit Non-Goals

The following must not block completion:

- heterogeneous finger trees;
- level-linked search trees;
- polygon clipping;
- a new asymptotic-complexity proof;
- every data structure from the 1986 algorithm;
- an interactive visualization system;
- unrelated sorting baselines;
- machine-learning-based structure classification;
- a claim that generated inputs represent all Jordan sequences.

## Immediate Next Step

Week 9 and Week 10 are complete. The next implementation gate is the frozen
Week 11 paper-sorting integration protocol:

```text
experiments/week11_experiment_protocol.py
```

Week 11 must:

```text
implement a dedicated runner and validator
pass execution_mode="minimal" explicitly for paper timing
run one checked diagnostic per case outside timing
keep oracle certification outside timing
keep valid-input sorting separate from recognition
produce exactly 1050 raw rows under the frozen protocol
```

The protocol is machine-independent. Each execution uses a unique execution
ID, output directory, machine environment record, and source commit. Different
machines must not pool absolute runtimes, but may compare within-run ratios and
cross-machine trend consistency.

The Week 11 pilot is not the Week 12 formal experiment and does not support a
linear-time claim.
