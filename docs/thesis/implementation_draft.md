# Implementation Draft

Last updated: 2026-08-06

Status: Week 13 implementation-chapter draft; awaiting review.

## Implementation Scope

This project contains two deliberately separate sorting paths. The first is an
oracle-backed reference pipeline. The second is an ordinary-list reconstruction
of the high-level control flow described for simplified Jordan sorting. The
distinction matters because the two paths obtain their output differently and
support different claims.

The reference function `simplified_jordan_sort` copies the input, runs the
project oracle, constructs structural data for valid inputs, records reference
trace and statistics fields, and returns the sorted list supplied by the
oracle. It is a reproducible baseline and structural observation pipeline; it
does not recover sorted order by executing the paper-facing sibling-list
algorithm. [I-01]

The paper-facing function `paper_jordan_sort_valid` instead maintains a partial
sorted order and returns `state.partial_order.to_list()`. For inputs of length
at least three, its core neither imports the oracle nor reads
`oracle_result["sorted"]`. It therefore recovers the sorted order from its own
maintained state, subject to the explicit precondition that the input has
already been certified as a valid Jordan sequence. [I-02, I-03]

## Input and Index Model

The implementation treats the input sequence as curve order:

```text
z_1, z_2, ..., z_n
```

Paper indices are one-based even though Python storage is zero-based. Each
input element is represented by an immutable `PointRef(paper_index, value)` so
that an algorithmic point identifier cannot be confused with the comparable
value stored at that point. Input values must be distinct and mutually
comparable. The caller owns these preconditions; the pure paper core does not
classify arbitrary inputs as valid or invalid. [I-02, I-03]

For every `i >= 2`, the finite pair `P_i` stores the curve-order endpoints
`z_(i-1)` and `z_i`. Even end indices form the upper family and odd end indices
form the lower family. Pair records preserve curve endpoint order separately
from geometric endpoint order. This distinction is necessary because the first
or second curve endpoint need not be the smaller or larger value. [I-04]

## Maintained State

For inputs of length at least three, the central `PaperJordanState` contains:

```text
immutable point records
number of processed points
partial sorted-order list
finite and dummy pair records
end-index to pair mapping
ordinary sibling-list backend
upper and lower dummy roots
fixed execution policy
optional trace and counters
mandatory per-iteration stage results
```

This state is shared by one Step 1/2/3 runner. The increasing and decreasing
branches are explicit mirrored operations, but diagnostics, production sorting,
and execution modes do not maintain separate algorithm loops. [I-04, I-06,
I-07]

### Partial Sorted Order

`SortedOrderList` is a doubly linked structure bounded by identity-based
negative- and positive-infinity sentinels. A point-ID mapping gives direct
access to nodes. Predecessor, successor, insertion before an anchor, and
insertion after an anchor therefore use local links rather than a global scan.
Before mutation, an insertion checks that the new value lies strictly between
its two adjacent values. The final output traversal excludes sentinels and
returns the original values in maintained order. [I-02, I-04]

### Pair Families and Sibling Lists

`PairRecord` stores pair identity, end index, curve-order endpoint IDs, family,
parent ownership, sibling-list ownership, and ordered child-list IDs. Each
family also has a dummy pair that acts as the root and never appears as a
finite list item. [I-04, I-05]

A `SiblingList` contains finite pair IDs in increasing order of each pair's
geometric left endpoint. Every live list has exactly one owner. Every owned
finite pair occurs in exactly one live sibling list, and its parent must equal
that list's owner. A finite parent must already be connected to its same-family
dummy root. Parent chains are acyclic, and one parent may own at most two
ordered child sibling lists. [I-05]

The concrete backend uses ordinary Python lists. Boundary insertion may append
after the last item or insert before the first item. Splitting scans the input
list and materializes new Python lists. These choices make ownership behavior
explicit and testable but do not reproduce the theoretical data structures or
their complexity bounds. [I-05, I-09]

## Initialization

Lengths zero, one, and two are handled by fixed comparison logic. For
`n >= 3`, initialization creates all point records and sorts only the first
three points into the partial-order list. It then creates:

```text
P_2 = {z_1, z_2} in the upper family
P_3 = {z_2, z_3} in the lower family
one dummy root for each family
one singleton sibling list for P_2 under the upper dummy
one singleton sibling list for P_3 under the lower dummy
```

After initialization, `processed_count` is three. Each subsequent iteration
adds exactly one finite pair and one output point. [I-04]

## Iterative Paper-Facing Control Flow

For each `i` from four through `n`, the shared runner executes Step 1, Step 2,
and one orientation of Step 3. The orientation is increasing when
`z_(i-1) < z_i` and decreasing when `z_i < z_(i-1)`. Equal values violate the
distinct-value precondition. [I-04]

### Step 1: Predecessor-Side Boundary

Step 1 finds the predecessor of `z_(i-1)` in the maintained partial order. On
an odd iteration, if that neighbor is `z_1`, the algorithm moves once more to
the predecessor of `z_1`. An infinity sentinel selects the current family's
dummy pair; otherwise, the boundary is the already processed same-family pair
that contains the neighbor point. [I-04]

### Step 2: Successor-Side Boundary

Step 2 is the reflected search on the successor side. The odd-index `z_1`
adjustment moves from an immediate `z_1` neighbor to the successor of `z_1`.
Positive infinity selects the family dummy; a finite neighbor selects its
processed same-family pair. Both boundary selections are stored as immutable
stage results even when trace collection is disabled. [I-04, I-07]

### Step 3(a): Insert the New Pair

Step 3(a) creates `P_i` and places it in the current family tree. In the
increasing branch, the predecessor-side boundary controls insertion. If that
boundary encloses `z_(i-1)`, `P_i` becomes a singleton child list of the
boundary pair; otherwise, it is inserted immediately after the boundary pair
in the boundary's existing sibling list and inherits its parent. [I-04, I-05]

The decreasing branch mirrors this rule with the successor-side boundary. A
new singleton is created when that boundary encloses `z_(i-1)`; otherwise,
`P_i` is inserted immediately before the boundary pair and inherits its
parent. Registration is rolled back if insertion fails, so an unowned partial
pair is not left in the backend. [I-04, I-05]

### Step 3(b): Split and Transfer Children

Step 3(b) may transfer a contiguous side of an existing sibling list to the
new pair. In the increasing branch, no split is required if the
successor-side boundary encloses `z_(i-1)`. Otherwise, its list is partitioned
at `value(z_i)` and the left side becomes a child list of `P_i`; the right side
remains with the previous owner. The decreasing branch mirrors the operation:
it uses the predecessor-side boundary and transfers the right split side to
`P_i`. [I-04, I-05]

The backend first creates an immutable `SplitPlan` without modifying live
state. Commit then retires the old list, creates only nonempty output lists,
updates list owners and pair ownership, orders affected child-list IDs, and
checks the touched state. A stale plan, straddling pair, ownership mismatch,
cycle, unowned parent, or third child list is rejected. If publication or a
postcondition fails, the old list registry, parent child lists, next list ID,
and pair ownership are restored. [I-05]

### Step 3(c): Insert the New Point

Step 3(c) inserts `z_i` into the partial sorted order. With no acquired child,
the base anchor is `z_(i-1)`. In the increasing branch with children, the base
anchor is the geometric right endpoint of the rightmost child pair; insertion
occurs after that anchor. In the decreasing branch, it is the geometric left
endpoint of the leftmost child pair; insertion occurs before that anchor.
[I-04]

An additional odd-index rule handles `z_1`. If `z_1` lies strictly between the
base anchor and `z_i`, `z_1` replaces the base anchor before insertion. The
boundary adjustment in Steps 1 and 2 and this output-anchor adjustment are
separate operations. After successful insertion, Step 3(c) advances
`processed_count`; no earlier stage marks the point as processed. [I-04]

The geometric endpoint rule and the odd-index output-anchor adjustment are an
executable interpretation of details that are not fully specified in the 1990
text. They were fixed through minimal counterexamples, the related 1986
description, mirrored cases, and exhaustive repository validation over
oracle-certified cases. The implementation should therefore be described as a
paper-facing reconstruction rather than a verbatim transcription of every
omitted detail. [I-04]

## Output and Certification Boundary

After the final iteration, `paper_jordan_sort_valid` traverses the maintained
partial order and returns its values. It does not delegate output recovery to
the oracle or reference pipeline. [I-02, I-03]

The safe wrapper `certified_paper_jordan_sort` establishes the public
precondition boundary. It first invokes the oracle and rejects an invalid
candidate; only a valid candidate is passed to `paper_jordan_sort_valid`.
Certification makes the precondition explicit but does not convert the pure
paper core into a recognition algorithm. The oracle call is outside the
minimal paper timing boundary. [I-08]

## Validation and Deterministic Replay

The production sorter and `paper_jordan_diagnostics_valid` call the same core
runner. Diagnostics select the fixed `checked` policy and invoke full state
validation after initialization and each completed iteration. The audit checks
point identity and values, partial-order links and order, exact pair membership,
sibling ownership, parent chains, stage-result types and fields, trace payloads,
metrics, and a canonical backend snapshot. [I-06]

The state validator also performs deterministic replay from the input points
and compares the replayed partial order, pair/list registry, stage results,
trace, and metrics with the supplied state. Expected results used by external
tests do not feed into production state. Full diagnostics are correctness
evidence outside the timed minimal call, not part of the reported paper sorting
runtime. [I-06]

## Execution Policies and Timing Boundary

Five immutable policies select whether the shared runner records trace, counts
selected operations, and performs complete backend validation after split
commits. The `checked` policy enables all three. The `minimal` policy used for
paper timing disables all three. Intermediate policies isolate trace and
counter costs for the Week 10 contamination study. [I-07]

Policy-controlled observations do not change the Step 1/2/3 sequence. Even in
`minimal`, mandatory stage results, local ordering checks, split-plan
validation, cycle prevention, touched-state postconditions, rollback, input
materialization, and final `to_list()` traversal remain. The timed result is
therefore the ordinary-list algorithm with optional diagnostics removed, not a
bare or unchecked surrogate. [I-07]

## Implementation and Complexity Boundary

The linked partial order supports adjacent access and insertion through local
links. The sibling backend, however, uses ordinary Python lists: front
insertion and list splitting may require work proportional to sibling-list
length, and split materialization rebinds all items in the input list. Complete
checked validation may also follow every finite pair's parent chain. [I-05,
I-09]

Consequently, this implementation does not instantiate level-linked search
trees, heterogeneous finger trees, or a theoretical linear-time split/update
engine. Its purpose is to make the paper-facing control flow, ownership
transitions, independent output recovery, and correctness checks executable.
No overall linear-time or asymptotic-complexity claim is made for the
ordinary-list backend. [I-09, L-01, L-09]

## Claim Coverage

This chapter covers all implementation claims `I-01` through `I-09` and the
required implementation limitations `L-01`, `L-04`, and `L-09`. Experimental
protocol, runtime results, and exploratory correlations are intentionally
reserved for later chapters.
