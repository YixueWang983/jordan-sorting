# Ordinary-List Reconstruction of the 1990 Jordan-Sorting Algorithm

Last updated: 2026-07-27

Status: Week 9 ordinary-list implementation, validation, and integration contract complete.

## Purpose

This document translates Sections 2 and 3 of:

```text
Fung, Nicholl, Tarjan, and Van Wyk
Simplified Linear-Time Jordan Sorting and Polygon Clipping
Information Processing Letters 35 (1990), pages 85-92
```

into an executable design for this repository.

The implementation preserves the high-level incremental Jordan-sorting
algorithm and the semantics of `make-list`, boundary insertion, and split. It
uses ordinary Python data structures instead of heterogeneous finger trees.

The implementation is intended to be:

- independently correct on tested valid inputs;
- traceable back to the paper's Step 1/2/3;
- observable through invariants and operation counters;
- explicit about its non-linear-time backend.

It does not claim the paper's linear running time.

## Relationship to Existing Code

The existing modules retain their current responsibilities:

```text
oracle.py:
    external validity and differential-test oracle

simplified_jordan.py:
    existing reference pipeline using oracle-sorted output

family_tree.py:
    static family-tree construction for diagnostics

paper_jordan_sort.py:
    new incremental paper-algorithm implementation

partial_sorted_list.py:
    maintained partial sorted order

sibling_list_backend.py:
    ordinary-list implementation of sibling-list operations
```

The new core must not call the existing reference pipeline or use its output.

## Source Boundary

The main algorithm appears on paper pages 88-89:

1. initialize a sorted list containing the first three points and two initial
   singleton sibling lists;
2. for each `i = 4..n`, select predecessor-side and successor-side boundary
   pairs;
3. insert the new curve pair, split off its children, and insert `z_i` into the
   maintained sorted order.

Section 3, beginning on paper page 90, abstracts the required sibling-list
operations as:

```text
make-list(x)
insert(x, y)
split(x, L)
```

The heterogeneous finger tree is a backend for achieving the theoretical
amortized bound. It is not required to preserve the algorithm's control flow.

The 1986 predecessor algorithm is used only to resolve compressed notation
where the 1990 description is not executable under a literal reading. In
particular, the 1986 algorithm stores both endpoints in sorted family lists and
inserts the new point next to the geometric boundary item `u_q`. This provides
the comparison point for the Step 3(c) anchor correction documented below.

## Input Model

The pure core accepts:

```python
paper_jordan_sort_valid(seq)
```

Preconditions:

- values are distinct;
- values are mutually comparable;
- the sequence is valid under the project's Jordan-sequence model.

The project's current model accepts a candidate when:

```text
values are distinct
and upper pair intervals are laminar
and lower pair intervals are laminar
```

The oracle remains the executable decision procedure for this predicate. A
short thesis-facing justification is still required for why the two laminar
half-plane chord families form the validity model used by the implementation.
Until that argument is written, use:

```text
oracle-accepted candidate Jordan sequence
```

rather than claiming a stronger recognition theorem.

## Core Purity Contract

The pure algorithm core must not:

- call `oracle(seq)`;
- call or import `rank_map`;
- call `sorted(seq)` on the complete input;
- read `oracle_result["sorted"]`;
- call `simplified_jordan_sort`;
- prebuild static rank intervals or static family trees to make algorithm
  decisions.

Its returned order must come from:

```text
state.partial_order.to_list()
```

A separate wrapper may be added:

```python
validated_paper_jordan_sort(seq)
```

The wrapper may call the oracle to reject invalid input. It passes only the
original sequence to the pure core. Because the oracle performs ordinary
sorting internally, the wrapper is not used for pure paper-algorithm timing.

## Public Return Contracts

The pure core returns a new list:

```python
paper_jordan_sort_valid(seq) -> list
```

Postconditions:

- the returned list contains every input point exactly once;
- the returned list is strictly increasing;
- the caller's input is not mutated;
- the returned object does not alias the caller's list;
- for `n >= 4`, the list comes from `state.partial_order.to_list()`.

Invalid-input behavior is deliberately outside the pure core contract. Passing
an invalid candidate violates its precondition.

The proposed validated wrapper returns:

```python
{
    "valid": bool,
    "sorted": list | None,
    "reason": str | None,
    "oracle": dict,
    "oracle_sorted_reference": list,
    "implementation": "paper_ordinary_list",
    "backend": {
        "name": "ordinary_sibling_lists",
        "uses_oracle_sorted_output": False,
        "linear_time_claim": False,
    },
}
```

For a valid input, `sorted` is the core result. For an invalid input, `sorted`
is `None`. `oracle_sorted_reference` is retained under a deliberately different
field name for testing and diagnostics; it must never be substituted for
`sorted`.

This wrapper shape is provisional until experiment integration, but the meaning
of `sorted` is fixed now: it can only contain paper-algorithm output.

## Indexing Convention

The paper is one-based:

```text
z_1, z_2, ..., z_n
```

Python sequences are zero-based. The implementation should make conversions
visible:

```python
def paper_point(values, paper_index):
    return values[paper_index - 1]
```

Algorithm records use `paper_index`, not a raw Python offset. Stable identity is
the paper index; the value is used only for order comparisons.

This avoids using the input value as a dictionary key and avoids repeated
off-by-one conversions.

## Pair Definition and Parity

For every processed end index `i >= 2`, define:

```text
P_i = {z_(i-1), z_i}
```

The endpoints remain stored in curve order:

```text
first = z_(i-1)
second = z_i
```

They are not reordered by numeric value inside the pair record.

Family mapping:

```text
i even -> P_i is upper
i odd  -> P_i is lower
```

This matches the existing project definitions:

```text
upper: P_2, P_4, P_6, ...
lower: P_3, P_5, P_7, ...
```

Recommended helper:

```python
def pair_family_for_end_index(i):
    if i < 2:
        raise ValueError("a finite pair requires end index >= 2")
    return "upper" if i % 2 == 0 else "lower"
```

## Selecting the Same-Family Pair Containing a Point

A processed point `z_k` can be incident to:

```text
P_k     if k >= 2
P_(k+1) if k + 1 has already been processed
```

For the family required while processing `P_i`, select the incident pair whose
end index has the same parity as `i`.

Implementation rule:

```text
if k >= 2 and parity(k) == parity(i):
    select P_k
else if k + 1 <= processed_count and parity(k + 1) == parity(i):
    select P_(k+1)
else:
    no finite same-family pair exists
```

The important exceptional case is `z_1` in the lower family. It has no lower
pair. This is why the paper changes the predecessor or successor when `i` is odd
and the immediate neighbor is `z_1`.

This selection uses original sequence indices. It does not use sorted ranks.

## Point and Pair Records

Recommended conceptual records:

```python
@dataclass(frozen=True)
class PointRef:
    paper_index: int
    value: object


@dataclass
class PairRecord:
    pair_id: int
    end_index: int | None
    first_point_id: int | None
    second_point_id: int | None
    family: str
    parent_pair_id: int | None
    sibling_list_id: int | None
    child_sibling_list_ids: list[int]
    is_dummy: bool
```

Required meanings:

- `pair_id` is stable and unique;
- finite `pair_id` may equal its end index, but callers must not depend on that;
- `parent_pair_id` is the pair whose child collection contains this pair;
- `sibling_list_id` is the one list that owns this finite pair as an item;
- `child_sibling_list_ids` are ordered from left to right;
- dummy pairs have no ordinary sibling-list owner.

Every finite processed pair must be owned by exactly one sibling list.

`first_point_id` and `second_point_id` preserve curve order. They must not be
used as synonyms for the geometric left and right endpoints. The implementation
also exposes:

```python
def left_endpoint_id(pair, points):
    ...


def right_endpoint_id(pair, points):
    ...
```

These helpers compare the two endpoint values already present in the partial
order:

```text
left_endpoint_id(P_i):
    endpoint with smaller x-coordinate

right_endpoint_id(P_i):
    endpoint with larger x-coordinate
```

They perform one endpoint comparison and do not require a global rank map.
This distinction is required when a pair runs from right to left along the
curve.

## Sentinels and Dummy Pairs

The partial sorted order has two sentinel node identities:

```text
NEGATIVE_INFINITY
POSITIVE_INFINITY
```

They are objects, not numeric values. They cannot collide with user input and
are removed by `to_list()`.

Each family has its own dummy root pair:

```text
UPPER_DUMMY_PAIR
LOWER_DUMMY_PAIR
```

Both conceptually represent `{-infinity, +infinity}`, but they have distinct pair
IDs and family ownership. A dummy pair:

- encloses every finite point and finite pair;
- has no parent;
- is never an item in a sibling list;
- may own one or two child sibling lists.

Step 1 and Step 2 return the dummy pair of the currently processed family when
the selected neighbor is the corresponding infinity sentinel.

## Partial Sorted Order

The partial order contains exactly:

```text
z_1, ..., z_i
```

after iteration `i`, in increasing value order.

Use a doubly linked structure:

```python
class SortedOrderList:
    def predecessor(self, point_id): ...
    def successor(self, point_id): ...
    def insert_before(self, anchor_point_id, point): ...
    def insert_after(self, anchor_point_id, point): ...
    def to_list(self): ...
    def validate_links(self): ...
```

The Day 2 implementation fixes the concrete contract:

```text
point:
    immutable PointRef(paper_index, value)

predecessor / successor:
    return a paper point id or an identity-based infinity sentinel

insert_before / insert_after:
    accept a point id or legal sentinel anchor and a PointRef
    return the inserted paper point id

to_point_ids:
    return real point ids in maintained x-order

to_list:
    return real values in maintained x-order
```

Insertion checks only the two adjacent values. An anchor that would violate
strictly increasing order is rejected before links or mappings are changed.
This is an O(1) invariant check, not a scan, global sort, oracle call, or rank
map.

Internal state includes:

```text
negative sentinel node
positive sentinel node
point-id -> node mapping
size excluding sentinels
```

Predecessor/successor access must use node links, not a scan or
`list.index()`.

Output insertion and sibling-list insertion are different operations and use
different APIs.

## Sibling-List Representation

A sibling list contains finite pair IDs ordered by the paper's sibling order.
For siblings `P_a` and `P_b`, order them by:

```text
left(P_a) < left(P_b)
```

where:

```text
left(P_i) = min(value(z_(i-1)), value(z_i))
```

Conceptual structure:

```python
@dataclass
class SiblingList:
    list_id: int
    owner_parent_pair_id: int
    pair_ids: list[int]
```

A parent pair may temporarily own one or two sibling lists. Its
`child_sibling_list_ids` are kept in left-to-right order.

Persistent empty sibling lists are not required. When a split side is empty,
the backend returns `None` for that side.

Every live sibling list has an owner. Temporary split output without a live
owner exists only inside `SplitPlan`; it is not represented by a
`SiblingList` whose owner is `None`.

Ownership invariants:

```text
len(parent.child_sibling_list_ids) <= 2
child sibling-list IDs are unique
child sibling-list IDs are ordered from left to right
pair.parent_pair_id == sibling_list.owner_parent_pair_id
pair.sibling_list_id identifies the unique list containing the pair
every live owned list appears in exactly one parent's child-list collection
every finite parent already belongs to a live sibling list
every owned finite pair's parent chain reaches its same-family dummy root
pair parent chains are acyclic
```

Attempting to attach a third child sibling list to one parent is an invariant
error. An unowned finite pair cannot act as a parent, and a split cannot attach
an acquired pair below one of its own descendants. The implementation must not
silently truncate, reorder, detach, or cycle ownership.

## Ordinary Sibling-List Operations

### `make_list`

Conceptual API:

```python
make_list(pair_id, owner_parent_pair_id) -> list_id
```

Postconditions:

- a singleton list is created;
- the pair receives that list as its unique owner;
- the owner parent records the new child list;
- no existing list already owns the pair.
- the owner is either the registered family dummy or a finite pair already
  connected to that dummy through live ownership links.

When an owner already has one child list, the new list is inserted into
`child_sibling_list_ids` according to its first pair's left-endpoint key. The
result must contain no more than two list IDs.

### `insert_at_boundary`

Conceptual API:

```python
insert_at_boundary(pair_id, anchor_pair_id, side) -> list_id
```

Allowed `side` values:

```text
before
after
```

Preconditions:

- the anchor belongs to a live sibling list;
- `before` requires the anchor to be first;
- `after` requires the anchor to be last;
- the new pair and anchor belong to the same family;
- the new pair currently has no sibling-list owner;
- the resulting order agrees with pair-left-endpoint order.

This is the ordinary-backend interpretation of the restricted Section 3
`insert(x, y)`. It is not arbitrary middle insertion.

Additional postconditions:

- `parent(new_pair) = parent(anchor_pair)`;
- `new_pair.sibling_list_id = anchor_pair.sibling_list_id`;
- the owner parent's child-list IDs do not change;
- all pre-existing items retain their order and ownership.

### Backend `split_by_key`

The generic backend operation is:

```python
split_by_key(list_id, boundary_key, key_function) -> SplitPlan
```

It implements the Section 3 shape:

```text
left items:  key(item) <= boundary_key
right items: key(item) > boundary_key
```

`SplitPlan` contains:

```text
retired list ID
previous owner parent pair ID
original pair IDs
left pair IDs in original order
right pair IDs in original order
```

It is a partition plan, not a complete Jordan ownership transition. The plan
does not become visible as live state until the algorithm adapter commits it.

The ordinary backend exposes the atomic commit separately:

```python
commit_split(
    plan,
    acquired_side,
    new_parent_pair_id,
) -> SplitCommitResult
```

`SplitCommitResult` contains `left_list_id` and `right_list_id`; an empty side
is represented by `None`. A stale or forged plan, a third child list, an
unowned finite new parent, a descendant new parent, or any ownership mismatch
is rejected before publication. If the final invariant check raises
unexpectedly, all affected pair/list/parent fields are rolled back.

### Algorithm `split_pairs_at_value`

Conceptual API:

```python
split_pairs_at_value(
    list_id,
    boundary_value,
    acquired_side,
    new_parent_pair_id,
) -> SplitCommitResult
```

Before calling `split_by_key`, this adapter checks every pair in the input list:

```text
left classification:
    both finite endpoint values are less than boundary_value

right classification:
    both finite endpoint values are greater than boundary_value
```

An existing processed pair cannot have an endpoint equal to the new unprocessed
point `z_i`, because input values are distinct.

If a pair straddles the boundary, the backend raises an invariant error. The
paper's locality argument requires the selected list to partition cleanly.

After validation, `pair_left_endpoint` is a valid key for the generic split:
every pair with a left key below the boundary has both endpoints below it, and
every remaining pair has both endpoints above it.

The adapter commits one atomic ownership transaction:

1. verify that the retired list occurs exactly once in the old parent's
   `child_sibling_list_ids`;
2. create live list IDs only for nonempty outputs;
3. replace the retired list in the old parent with the nonempty retained side,
   or remove it when the retained side is empty;
4. attach the nonempty acquired side to the new parent at its left-to-right
   position;
5. update every output list's `owner_parent_pair_id`;
6. update every output pair's `sibling_list_id`;
7. update every acquired pair's `parent_pair_id` to the new parent;
8. preserve the retained pairs' old `parent_pair_id`;
9. retire the input list ID;
10. verify uniqueness, ordering, and the two-list maximum for both parents;
11. verify that every owned finite pair reaches its same-family dummy root
    without repeating a pair ID.

No public invariant check observes a half-applied transaction. If any
precondition or final invariant fails, the operation raises before publishing
the new state.

Empty-side behavior:

- an empty output has list ID `None`;
- it is not inserted into a parent's child-list collection;
- no pair mapping points to it;
- if the retained side is empty, the retired list is removed from the old
  parent without replacement;
- if the acquired side is empty, the new parent receives no child list.

## Algorithm State

Recommended conceptual state:

```python
PaperJordanState(
    points,
    processed_count,
    partial_order,
    pairs,
    pair_by_end_index,
    sibling_backend,
    upper_dummy_pair_id,
    lower_dummy_pair_id,
    trace,
    metrics,
)
```

The state owns:

- immutable input point records;
- the processed-prefix length;
- the partial sorted-order list;
- pair records indexed by stable ID and end index;
- point-to-incident-pair selection through original indices;
- sibling lists and ownership mappings;
- family-specific dummy pairs;
- trace and optional counters.

No rank map is part of this state.

## Small-Input Behavior

The paper loop assumes at least three initial points. The implementation defines:

```text
n = 0:
    return []

n = 1:
    return [z1]

n = 2:
    order z1 and z2 with one comparison

n = 3:
    order z1, z2, z3 with a fixed comparison/insertion procedure

n >= 4:
    initialize the paper state with z1, z2, z3 and run i = 4..n
```

No branch calls `sorted`.

For `n < 3`, no complete upper/lower initialization state is needed.

## Initialization for `n >= 3`

Create:

1. point records for all input positions;
2. a partial sorted order containing `z_1`, `z_2`, and `z_3`;
3. upper finite pair `P_2 = {z_1, z_2}`;
4. lower finite pair `P_3 = {z_2, z_3}`;
5. the two family-specific dummy pairs;
6. one upper sibling list containing `P_2`, owned by the upper dummy;
7. one lower sibling list containing `P_3`, owned by the lower dummy;
8. initial trace and zeroed optional metrics.

Initialization invariants:

- exactly three real output nodes exist;
- the three nodes are in increasing order;
- `P_2` and `P_3` preserve curve endpoint order;
- their family parity is correct;
- each finite pair has one sibling-list owner;
- neither dummy is an item in a sibling list.

## Boundary Selection Result

Step 1 and Step 2 return:

```python
@dataclass(frozen=True)
class BoundarySelection:
    neighbor_point_id: int | None
    pair_id: int
    used_dummy_pair: bool
    adjusted_for_z1: bool
```

`neighbor_point_id` is `None` when the selected neighbor is an infinity
sentinel.

## Step 1: Predecessor-Side Boundary

For iteration `i`:

```text
previous = z_(i-1)
family = family(P_i)
v = predecessor(previous) in the partial sorted order

if i is odd and v == z_1:
    v = predecessor(z_1)

if v is NEGATIVE_INFINITY:
    left_pair = dummy pair for family
else:
    left_pair = processed same-family pair containing v
```

Trace events:

```text
step1_find_predecessor
step1_select_boundary_pair
```

The finite pair must already have been processed.

## Step 2: Successor-Side Boundary

For iteration `i`:

```text
previous = z_(i-1)
family = family(P_i)
w = successor(previous) in the partial sorted order

if i is odd and w == z_1:
    w = successor(z_1)

if w is POSITIVE_INFINITY:
    right_pair = dummy pair for family
else:
    right_pair = processed same-family pair containing w
```

Trace events:

```text
step2_find_successor
step2_select_boundary_pair
```

## Shared Enclosure Predicate

For finite pair `P` and finite point `z`:

```text
P encloses z
iff
min(P.first.value, P.second.value) < z.value
and
z.value < max(P.first.value, P.second.value)
```

The family dummy pair encloses every finite point.

## Step 3: Increasing Orientation

This branch applies when:

```text
z_(i-1) < z_i
```

Let:

```text
A = left boundary pair from Step 1
B = right boundary pair from Step 2
N = new pair P_i
```

### Step 3(a): Insert the New Pair

If `A` encloses `z_(i-1)`:

```text
parent(N) = A
create a new singleton sibling list [N] owned by A
```

Otherwise:

```text
A is last in its current sibling list
parent(N) = parent(A)
insert N immediately after A in A's sibling list
```

This updates the new pair's unique sibling-list ownership.

### Step 3(b): Split Off Children

If `B` encloses `z_(i-1)`:

```text
N has no acquired child list
record a skipped split
```

Otherwise:

```text
B is first in its current sibling list L
(left, right) = split(L, value(z_i))
```

Proposed ownership transition:

```text
left:
    contains pairs enclosed by N
    becomes a child sibling list owned by N

right:
    remains a child sibling list of L's previous owner
```

The retired input list is replaced in its previous owner's ordered child-list
collection by the nonempty retained side. The acquired side is removed from the
old owner and attached to `N`.

This ownership transition must receive direct tests before full-loop use.

### Step 3(c): Insert `z_i` into the Partial Order

If `N` has no children:

```text
base_anchor = z_(i-1)
```

Otherwise:

```text
C = rightmost child pair of N
base_anchor = right_endpoint_id(C)
```

Then apply the odd-index `z1` adjustment:

```text
output_anchor = base_anchor

if i is odd and base_anchor < z1 < z_i:
    output_anchor = z1

insert z_i immediately after output_anchor
```

When children exist, the base anchor is the geometric right endpoint of the
rightmost child. It is not necessarily `C.second`, because `C.second` is
defined by curve order.

This is the executable interpretation of the paper's `z_m`. A literal reading
of `z_m` as the second curve-order endpoint fails for the oracle-valid and
geometrically realizable sequence `[3, 2, 1, 4]`: the only acquired child is
`P2={z1=3,z2=2}`, so inserting `z4=4` after `z2=2` would produce
`[1,2,4,3]`. Inserting after the child's geometric right endpoint `z1=3`
produces the correct order.

The earlier 1986 algorithm supports this interpretation. It stores both
endpoints in sorted family lists and inserts the new point after the boundary
item `u_q`. In the ordinary pair-list reconstruction,
`right_endpoint_id(C)` is that base boundary item for the rightmost acquired
child.

The same 1986 description records a special case: when `i` is odd and `z1`
lies between the ordinary boundary anchor and `z_i`, the new point belongs next
to `z1`. The 1990 Step 1 and Step 2 adjustments repair boundary-pair selection,
but they do not by themselves repair this final output anchor.

## Step 3: Decreasing Orientation

This branch applies when:

```text
z_(i-1) > z_i
```

It is the reflection of the increasing branch under reversal of the output
order. Step 1 and Step 2 still compute the predecessor-side and successor-side
boundary pairs.

Let:

```text
A = left boundary pair
B = right boundary pair
N = new pair P_i
```

### Mirrored Step 3(a)

If `B` encloses `z_(i-1)`:

```text
parent(N) = B
create a new singleton sibling list [N] owned by B
```

Otherwise:

```text
B is first in its current sibling list
parent(N) = parent(B)
insert N immediately before B
```

### Mirrored Step 3(b)

If `A` encloses `z_(i-1)`:

```text
N has no acquired child list
record a skipped split
```

Otherwise:

```text
A is last in its current sibling list L
(left, right) = split(L, value(z_i))

right:
    contains pairs enclosed by N
    becomes a child sibling list owned by N

left:
    remains with L's previous owner
```

### Mirrored Step 3(c)

If `N` has no children:

```text
base_anchor = z_(i-1)
```

Otherwise:

```text
C = leftmost child pair of N
base_anchor = left_endpoint_id(C)
```

Apply the reflected odd-index adjustment:

```text
output_anchor = base_anchor

if i is odd and z_i < z1 < base_anchor:
    output_anchor = z1

insert z_i immediately before output_anchor
```

When children exist, the base anchor is the geometric left endpoint of the
leftmost child, not necessarily its second curve-order endpoint. The sequence
`[2,3,4,1]` is the minimal endpoint-orientation counterexample: inserting
`z4=1` before `z2=3` is wrong, while inserting it before the child's geometric
left endpoint `z1=2` is correct.

The sequence `[1,2,3,4,6,7,0]` independently shows why the second anchor stage
is necessary. At `i=7`, the geometric base anchor is `2`, but the original
point `z1=1` lies between the new point `0` and `2`; insertion before `z1`
produces the correct order.

## End-to-End Pseudocode

```text
paper_jordan_sort_valid(seq):
    values = list(seq)

    if n == 0:
        return []
    if n == 1:
        return [z1]
    if n == 2:
        return compare_and_order_two(z1, z2)
    if n == 3:
        return compare_and_order_three(z1, z2, z3)

    state = initialize(z1, z2, z3)

    for i from 4 through n:
        left_boundary = step1(state, i)
        right_boundary = step2(state, i)

        if z_(i-1) < z_i:
            new_pair = step3a_increasing(state, i, left_boundary)
            step3b_increasing(state, i, new_pair, right_boundary)
            step3c_increasing(state, i, new_pair)
        else:
            new_pair = step3a_decreasing(state, i, right_boundary)
            step3b_decreasing(state, i, new_pair, left_boundary)
            step3c_decreasing(state, i, new_pair)

        state.processed_count = i
        run_online_invariants_if_enabled(state)

    return state.partial_order.to_list()
```

## Trace Contract

Every `i >= 4` records:

```text
step1_find_predecessor
step1_select_boundary_pair
step2_find_successor
step2_select_boundary_pair
step3a_insert_pair
step3b_split_sibling_list
step3c_insert_output_point
check_invariants
```

Skipped work still emits an event:

```python
{
    "step": "step3b_split_sibling_list",
    "iteration": i,
    "performed": False,
    "reason": "right boundary encloses previous point",
}
```

Common fields:

```text
iteration
family
previous_point_id
current_point_id
orientation
selected_pair_id
sibling_list_id
sibling_list_size
split_left_size
split_right_size
base_output_anchor_point_id
output_anchor_point_id
z1_anchor_adjusted
output_insertion_side
```

## Online Invariants

The core may check without ordinary sorting:

1. processed output size equals `processed_count`;
2. every processed point ID occurs exactly once;
3. forward and backward links agree;
4. adjacent real output values are strictly increasing;
5. every processed finite pair exists exactly once;
6. every finite pair has the family dictated by its end-index parity;
7. every finite pair belongs to exactly one sibling list;
8. no sibling list contains duplicate pair IDs;
9. every sibling list contains pairs from one family;
10. sibling pair-left endpoints are increasing;
11. every live list appears in exactly one parent's child-list collection;
12. no parent pair appears in its own child list;
13. split outputs are disjoint and preserve the input union;
14. sentinels and dummy pairs never appear as ordinary output/list items;
15. every completed iteration has the required trace events.

External tests may additionally assert:

```text
partial output snapshot == sorted(processed prefix)
final output == sorted(input)
```

Those expected values must not feed back into algorithm state.

## Initial Operation Counters

```text
predecessor_accesses
successor_accesses
boundary_pair_checks
sibling_scan_checks
sibling_lists_created
sibling_list_insertions
sibling_list_splits
split_items_scanned
split_items_copied
split_items_transferred
output_insertions
z1_boundary_adjustments
z1_output_anchor_adjustments
invariant_checks
trace_event_count
```

The two `z1` counters remain separate:

```text
z1_boundary_adjustments:
    Step 1/2 skips an immediate z1 predecessor/successor while selecting a
    same-family boundary pair

z1_output_anchor_adjustments:
    Step 3(c) replaces the geometric base anchor with z1 before output
    insertion
```

The three split counters have distinct meanings:

```text
split_items_scanned:
    pairs inspected while classifying the input sibling list

split_items_copied:
    input pairs copied/rebound while materializing ordinary Python-list
    split outputs; this increases by the full input-list size

split_items_transferred:
    acquired-side pairs whose ownership moves to the new P_i
```

`split_items_copied` is an ordinary-list backend cost model, not a claim about
exact physical memory writes. The old ambiguous name `split_items_moved` is
not used.

`paper_jordan_sort_valid(seq)` and the diagnostic API share one internal main
loop. The diagnostic API adds complete state audits through a callback and
must run outside timing regions. The public sorter accepts one fixed execution
mode. The Week 11 timing gate selects `minimal`, which disables trace, counters,
and complete backend commit validation while retaining the same algorithm
control flow and always-on local safety checks.

## Worked Trace: `[1, 4, 2, 3]`

Assign:

```text
z1 = 1
z2 = 4
z3 = 2
z4 = 3
```

This candidate is oracle-valid.

### Initialization

Partial sorted order:

```text
NEG_INF, z1=1, z3=2, z2=4, POS_INF
```

Pairs:

```text
P2 = {z1=1, z2=4}, upper
P3 = {z2=4, z3=2}, lower
```

Sibling lists:

```text
upper dummy children: [P2]
lower dummy children: [P3]
```

### Iteration `i = 4`

New pair:

```text
P4 = {z3=2, z4=3}, upper
```

Step 1:

```text
predecessor(z3=2) = z1=1
i is even, so there is no z1 exception
the upper pair containing z1 is P2
A = P2
```

Step 2:

```text
successor(z3=2) = z2=4
the upper pair containing z2 is P2
B = P2
```

Step 3 orientation:

```text
z3=2 < z4=3
use increasing branch
```

Step 3(a):

```text
P2 encloses z3 because 1 < 2 < 4
create singleton sibling list [P4] owned by P2
parent(P4) = P2
```

Step 3(b):

```text
B=P2 encloses z3
no child list is split off
P4 has no children
```

Step 3(c):

```text
insert z4=3 immediately after z3=2
```

Final partial order:

```text
1, 2, 3, 4
```

The result is obtained from the maintained linked order, not from a rank map or
oracle-sorted output.

## Nontrivial Trace A: Existing Sibling-List Insertion

Sequence:

```text
[1, 2, 3, 4]
```

This candidate is oracle-valid. Initialization gives:

```text
partial order: z1=1, z2=2, z3=3
upper dummy child list U1: [P2={z1=1,z2=2}]
lower dummy child list L1: [P3={z2=2,z3=3}]
```

At `i=4`:

```text
previous = z3=3
current = z4=4
orientation = increasing
family = upper
```

Step 1:

```text
predecessor(z3) = z2
the upper pair containing z2 is P2
A = P2
P2 does not enclose z3 because z3 is right of both endpoints
```

Step 2:

```text
successor(z3) = POSITIVE_INFINITY
B = UPPER_DUMMY_PAIR
```

Step 3(a):

```text
P2 is last in U1
insert P4={z3=3,z4=4} after P2
U1 becomes [P2, P4]
parent(P4) = parent(P2) = UPPER_DUMMY_PAIR
owner(P4) = U1
```

Step 3(b):

```text
B is the upper dummy and encloses z3
split is skipped
```

Step 3(c):

```text
P4 has no children
insert z4 immediately after z3
```

Final partial order:

```text
1, 2, 3, 4
```

This trace fixes the inherited-parent postcondition for
`insert_at_boundary`.

## Nontrivial Trace B: Increasing Split and Ownership Transfer

Sequence:

```text
[2, 3, 1, 4]
```

This candidate is oracle-valid. Initialization gives:

```text
partial order: z3=1, z1=2, z2=3
upper dummy child list U1: [P2={z1=2,z2=3}]
lower dummy child list L1: [P3={z2=3,z3=1}]
```

At `i=4`:

```text
previous = z3=1
current = z4=4
orientation = increasing
family = upper
```

Step 1:

```text
predecessor(z3) = NEGATIVE_INFINITY
A = UPPER_DUMMY_PAIR
```

Step 2:

```text
successor(z3) = z1
the upper pair containing z1 is P2
B = P2
P2 does not enclose z3
```

Step 3(a):

```text
A encloses every finite point
create U2=[P4={z3=1,z4=4}] owned by the upper dummy

transient owner view before the atomic split:
upper dummy child lists contain U2=[P4] and U1=[P2]
```

Step 3(b):

```text
split U1 at boundary z4=4
left pair IDs:  [P2] because both endpoints 2 and 3 are below 4
right pair IDs: []
acquired side:  left
retained side:  right
```

Atomic ownership result:

```text
U1 is retired
new list U3=[P2] is owned by P4
parent(P2) changes from UPPER_DUMMY_PAIR to P4
owner(P2) changes from U1 to U3
upper dummy child lists become [U2]
P4 child lists become [U3]
```

Step 3(c):

```text
rightmost child of P4 is P2
P2 runs left-to-right, so right_endpoint(P2) is z2=3
insert z4=4 immediately after z2=3
```

Final partial order:

```text
1, 2, 3, 4
```

This trace fixes increasing acquired-side ownership and the one-empty-side
transaction.

## Nontrivial Trace C: Decreasing Split and Ownership Transfer

Sequence:

```text
[3, 2, 4, 1]
```

This candidate is oracle-valid and is the order-reflected counterpart of Trace
B. Initialization gives:

```text
partial order: z2=2, z1=3, z3=4
upper dummy child list U1: [P2={z1=3,z2=2}]
lower dummy child list L1: [P3={z2=2,z3=4}]
```

At `i=4`:

```text
previous = z3=4
current = z4=1
orientation = decreasing
family = upper
```

Step 1:

```text
predecessor(z3) = z1
the upper pair containing z1 is P2
A = P2
P2 does not enclose z3
```

Step 2:

```text
successor(z3) = POSITIVE_INFINITY
B = UPPER_DUMMY_PAIR
```

Mirrored Step 3(a):

```text
B encloses every finite point
create U2=[P4={z3=4,z4=1}] owned by the upper dummy
```

Mirrored Step 3(b):

```text
split U1 at boundary z4=1
left pair IDs:  []
right pair IDs: [P2] because both endpoints 3 and 2 are above 1
acquired side:  right
retained side:  left
```

Atomic ownership result:

```text
U1 is retired
new list U3=[P2] is owned by P4
parent(P2) changes from UPPER_DUMMY_PAIR to P4
owner(P2) changes from U1 to U3
upper dummy child lists become [U2]
P4 child lists become [U3]
```

Mirrored Step 3(c):

```text
leftmost child of P4 is P2
P2 runs right-to-left, so left_endpoint(P2) is z2=2
insert z4=1 immediately before z2=2
```

Final partial order:

```text
1, 2, 3, 4
```

This trace fixes the decreasing acquired side for a decreasing child.

## Nontrivial Trace D: Increasing Parent with a Decreasing Child

Sequence:

```text
[3, 2, 1, 4]
```

This candidate is oracle-valid. It is also geometrically realizable as a
simple polygonal curve: an inner upper arc joins `3` to `2`, a lower arc joins
`2` to `1`, and an outer upper arc joins `1` to `4`.

One explicit non-self-intersecting polyline witness visits:

```text
(3,-1), (3,0), (2.5,0.5), (2,0), (1.5,-0.5),
(1,0), (2.5,2), (4,0), (4,-1)
```

Its x-axis intersections occur in curve order `3,2,1,4`.

Initialization gives:

```text
partial order: z3=1, z2=2, z1=3
upper dummy child list U1: [P2={z1=3,z2=2}]
lower dummy child list L1: [P3={z2=2,z3=1}]
```

At `i=4`, `P4={z3=1,z4=4}` is increasing. Step 3(a) creates a singleton
list for `P4`, and Step 3(b) transfers `P2` from the upper dummy to `P4`.

Step 3(c) must distinguish curve order from geometric order:

```text
rightmost child of P4 is P2
P2.first  = z1=3
P2.second = z2=2
right_endpoint(P2) = z1=3

insert z4=4 immediately after z1=3
```

Final partial order:

```text
1, 2, 3, 4
```

The rejected literal interpretation would insert after `P2.second=z2=2` and
produce `[1,2,4,3]`.

## Nontrivial Trace E: Decreasing Parent with an Increasing Child

Sequence:

```text
[2, 3, 4, 1]
```

This is the reflected counterpart of Trace D and is oracle-valid. At `i=4`,
`P4={z3=4,z4=1}` is decreasing and acquires the increasing child
`P2={z1=2,z2=3}`.

Mirrored Step 3(c):

```text
leftmost child of P4 is P2
P2.first  = z1=2
P2.second = z2=3
left_endpoint(P2) = z1=2

insert z4=1 immediately before z1=2
```

Final partial order:

```text
1, 2, 3, 4
```

The rejected literal interpretation would insert before `P2.second=z2=3` and
produce `[2,1,3,4]`.

The four parent/child orientation combinations are therefore covered by:

| Parent orientation | Child orientation | Trace | Required anchor |
| --- | --- | --- | --- |
| increasing | increasing | B: `[2,3,1,4]` | child's geometric right endpoint |
| increasing | decreasing | D: `[3,2,1,4]` | child's geometric right endpoint |
| decreasing | increasing | E: `[2,3,4,1]` | child's geometric left endpoint |
| decreasing | decreasing | C: `[3,2,4,1]` | child's geometric left endpoint |

## Nontrivial Trace F: Split with Two Nonempty Outputs

Sequence:

```text
[1, 2, 3, 4, 6, 7, 0, 5]
```

This candidate is oracle-valid. Immediately before `i=8`, the upper dummy owns
one sibling list:

```text
U1 = [
    P2={1,2},
    P4={3,4},
    P6={6,7},
]
```

That state is reachable only if the odd-index insertion at `i=7` is handled
explicitly. Immediately before `i=7`:

```text
partial order: 1, 2, 3, 4, 6, 7
lower dummy child list L1: [P3={2,3}, P5={4,6}]
```

The new lower pair is:

```text
P7={z6=7,z7=0}
orientation = decreasing
```

Mirrored Step 3(a) creates a singleton list for `P7`. Mirrored Step 3(b)
transfers `[P3,P5]` to `P7`. The ordinary geometric base anchor is:

```text
leftmost child = P3={2,3}
base_anchor = left_endpoint(P3) = 2
```

Using only that base anchor would insert `0` before `2` and produce the
incorrect partial order:

```text
1, 0, 2, 3, 4, 6, 7
```

Because `i=7` is odd and:

```text
z7=0 < z1=1 < base_anchor=2
```

the output anchor changes to `z1`. Inserting `z7=0` before `z1=1` produces:

```text
0, 1, 2, 3, 4, 6, 7
```

Now the `i=8` precondition is established. The new upper pair is:

```text
P8={z7=0,z8=5}
orientation = increasing
```

Step 3(a) creates the singleton list `[P8]` under the upper dummy. Step 3(b)
splits `U1` at boundary value `5`:

```text
left pair IDs:  [P2, P4]
right pair IDs: [P6]
acquired side:  left
retained side:  right
```

The atomic ownership result is:

```text
retire U1
new acquired list [P2,P4] is owned by P8
parent(P2) = parent(P4) = P8
new retained list [P6] remains owned by UPPER_DUMMY_PAIR
parent(P6) remains UPPER_DUMMY_PAIR
upper dummy child-list IDs contain [P8] and [P6] in left-to-right order
P8 child-list IDs contain [P2,P4]
```

Step 3(c) uses the geometric right endpoint of the rightmost acquired child:

```text
rightmost child = P4={3,4}
right_endpoint(P4) = 4
insert z8=5 after 4
```

Final partial order:

```text
0, 1, 2, 3, 4, 5, 6, 7
```

This trace fixes the case in which both split outputs are nonempty and both
the old and new parent retain live child lists. It also demonstrates that the
two-sided split trace depends on the odd-index `z1` output-anchor adjustment.

## Nontrivial Trace G: Increasing Odd-Index `z1` Adjustment

Sequence:

```text
[6, 5, 4, 3, 1, 0, 7]
```

This oracle-valid candidate is the order reflection of the first seven points
in Trace F. Before `i=7`:

```text
partial order: 0, 1, 3, 4, 5, 6
lower dummy child list L1: [P5={3,1}, P3={5,4}]
```

The new lower pair is:

```text
P7={z6=0,z7=7}
orientation = increasing
```

Step 3(a) creates a singleton list for `P7`, and Step 3(b) transfers both lower
children to it. The rightmost child is `P3={5,4}`, so:

```text
base_anchor = right_endpoint(P3) = 5
```

Using only the base anchor would insert `7` after `5` and produce:

```text
0, 1, 3, 4, 5, 7, 6
```

Because `i=7` is odd and:

```text
base_anchor=5 < z1=6 < z7=7
```

the output anchor changes to `z1`. Inserting `z7=7` after `z1=6` produces:

```text
0, 1, 3, 4, 5, 6, 7
```

Traces F and G cover the decreasing and increasing forms of the odd-index
`z1` output-anchor adjustment.

## Test Matrix

| Area | Required cases |
| --- | --- |
| index conversion | first point, last point, rejected index 0 |
| parity | `P2/P4` upper, `P3/P5` lower |
| same-family pair selection | point as first endpoint, point as second endpoint |
| endpoint helpers | increasing pair, decreasing pair, left/right identity |
| `z1` boundary exception | lower-family predecessor and successor cases |
| odd Step 3(c) | outside: `[1,2,3,4,5]` / `[5,4,3,2,1]`; adjusted: Trace G / Trace F |
| sentinels | negative and positive infinity, both family dummies |
| small inputs | `n=0`, `n=1`, both orders for `n=2`, all six orders for `n=3` |
| partial order | before/after insertion, duplicate rejection, link consistency |
| make-list | dummy owner, finite owner, duplicate ownership rejection |
| boundary insert | legal front, legal back, illegal middle |
| split | two nonempty sides, empty left, empty right, singleton, straddle rejection |
| initialization | pair parity, dummy ownership, sentinel-free output |
| Step 1 | even, odd, `z1` adjustment, negative sentinel |
| Step 2 | even, odd, `z1` adjustment, positive sentinel |
| Step 3(a) | singleton creation, shared-parent boundary insertion |
| Step 3(b) | no children, one child, multiple children, empty side, two nonempty sides, ownership transfer |
| Step 3(c) | no child, all four parent/child orientations, odd-index `z1` adjustment in both directions |
| full loop | flat, nested, incremental, odd/even lengths |
| independence | no oracle output, no rank map, no full sorting |

## Paper-to-Implementation Ambiguity Table

| Paper statement | Fixed implementation interpretation | Required check |
| --- | --- | --- |
| predecessor of `z_(i-1)` | previous linked node in `SortedOrderList` | left boundary and negative sentinel |
| successor of `z_(i-1)` | next linked node in `SortedOrderList` | right boundary and positive sentinel |
| pair containing `v` or `w` | processed incident pair whose end-index parity matches `i` | first-endpoint, second-endpoint, and `z1` exception |
| odd-index output anomaly | after choosing the geometric base anchor, replace it by `z1` when `z1` lies strictly between the base anchor and `z_i` | increasing and decreasing reflected cases |
| `{-infinity,+infinity}` | one distinct dummy pair per family | both family boundaries |
| pair's first/second endpoint | curve-order identity only | all four parent/child orientation combinations |
| pair's left/right endpoint | endpoint selected by x-coordinate comparison | reversed child orientation |
| insert after left sibling | restricted insertion after a last-list anchor | reject non-boundary anchor |
| mirrored insert before right sibling | restricted insertion before a first-list anchor | decreasing-orientation test |
| split at `z_i` | partition only when every pair has both endpoints on one side | two sides, empty side, and straddle rejection |
| split off children | transfer the enclosed side to the new pair and preserve the other side's old owner | ownership conservation |
| rightmost child | final pair in left-to-right sibling order | Step 3(c) increasing |
| leftmost child | first pair in left-to-right sibling order | Step 3(c) decreasing |
| insert after/before `z_m` | use the child's geometric boundary endpoint, corresponding to the 1986 `u_q` | four-orientation matrix and minimal counterexamples |
| symmetric case | reflect comparisons, boundary roles, child extreme, and output insertion side | mirrored paired examples |

Rows describing Step 3 ownership are proposed executable interpretations. They
remain listed in the open-question section until focused tests confirm them.

## Complexity Boundary

The design intends:

```text
partial-order predecessor/successor:
    O(1) through node links

partial-order insertion:
    O(1) through node links

ordinary sibling boundary insertion:
    append after the final item is amortized O(1)
    insert before the first item in a Python list is O(k)

ordinary sibling split:
    O(length of scanned sibling list)

list materialization and pair sibling-list rebinding:
    O(input sibling-list size)

parent-ownership transfers:
    O(transferred-side size)
```

Other bookkeeping may add ordinary dictionary or list costs. No total linear
bound is claimed.

The current correctness-first backend runs a complete `validate_invariants()`
after each committed split. Validation follows every owned finite pair's
parent chain to its family dummy. With `p` pairs and a chain depth of `O(p)`,
one complete validation can therefore cost `O(p^2)` in the worst case.

This audit cost was deliberately retained during the Week 9 correctness gate.
Week 10 introduced explicit execution policies and selected `minimal` for paper
timing. Timed calls exclude complete invariant validation; every exact case
receives an equivalent complete `checked` diagnostic outside the measured
region.

The theoretical heterogeneous finger-tree backend remains a paper-level
comparison point, not an implemented component.

## Decisions Requiring Executable Step 3 Tests

The design now fixes the following transitions, but documentation alone is not
correctness evidence:

1. Increasing Step 3(b) transfers the left split output to the new pair and
   retains the right output under the old parent.
2. Decreasing Step 3(b) transfers the right split output to the new pair and
   retains the left output under the old parent.
3. Increasing Step 3(c) inserts after the geometric right endpoint of the
   rightmost child.
4. Decreasing Step 3(c) inserts before the geometric left endpoint of the
   leftmost child.
5. Empty split outputs are represented by `None`, with no persistent empty
   list.
6. A two-nonempty-side split updates both parent ownership collections in one
   atomic transition.
7. Odd-index processing uses a separate output-anchor adjustment when `z1`
   lies strictly between the geometric base anchor and `z_i`. This is distinct
   from the Step 1 and Step 2 boundary-pair adjustments.

Focused executable tests must cover Traces B through G and odd-index cases
before the full loop is declared correct.

## Day 1 Acceptance Record

This specification is ready for Day 2 data-structure implementation when:

- paper indexing and parity are stable;
- the core purity boundary is accepted;
- sentinel and dummy identities are accepted;
- pair and sibling-list ownership fields are accepted;
- the two insert operations are clearly separated;
- curve-order and geometric endpoint identities are kept separate;
- all four parent/child orientation combinations use the correct geometric
  Step 3(c) anchor;
- odd-index `z1` output-anchor adjustment is explicit in both orientations;
- the proposed mirrored Step 3 interpretation is treated as testable, not
  silently assumed;
- empty-side and two-nonempty-side ownership transitions are explicit;
- no unresolved item is hidden by oracle-sorted output.

Current status: the Day 1 specification and Day 2 data structures are
implemented. Day 3 adds `PaperJordanState` initialization and executable Step
1/2 boundary selection and is approved after focused ownership, dummy, and
permutation checks. Day 4 adds Step 3(a)/(b). The first Day 5 checkpoint adds
independent increasing/decreasing Step 3(c) output insertion. The complete
paper loop remains unimplemented until this focused gate is reviewed.

## Day 3 Implementation Record

The ordinary-list reconstruction now exposes:

```text
initialize_paper_jordan_state(seq)
select_processed_same_family_pair(state, point_id, iteration)
step1_select_predecessor_boundary(state, iteration)
step2_select_successor_boundary(state, iteration)
```

Initialization uses a fixed comparison procedure for the first three points;
it does not call `sorted`, the oracle, or a rank map. It creates `P2`, `P3`,
the upper/lower dummy roots, and one owned singleton sibling list for each
finite initial pair.

Boundary selection accepts only the next unprocessed paper index. A finite
selection is checked against the original point incidence, pair-family parity,
the processed-prefix boundary, and both directions of live sibling-list
ownership:

```text
pair.sibling_list_id == sibling_list.list_id
pair.parent_pair_id == sibling_list.owner_parent_pair_id
pair ID occurs exactly once in sibling_list.pair_ids
```

Infinity neighbors return the corresponding family dummy only after checking
that the state and backend reference the same dummy object, its family matches
the current iteration, `is_dummy` is true, and it has no ordinary parent/list
ownership. For odd iterations, an immediate `z1` neighbor is skipped with a
second predecessor or successor access before selecting the lower-family pair.

Focused tests cover:

- all six initial three-point orders;
- exact `BoundarySelection` results for all 24 four-point permutations;
- exact odd Step 1/2 results for all 120 five-point permutations;
- negative and positive infinity dummy fallback;
- same-family selection through both endpoints of `P2` and `P3`;
- rejection of `z1` as a finite lower-family selection;
- odd-index predecessor and successor `z1` adjustment;
- adjusted finite-pair and adjusted dummy outcomes;
- rejection of inconsistent pair/list IDs and parent mappings;
- rejection of wrong-family, identity-mismatched, or ordinarily owned dummies;
- trace order, counters, and next-iteration validation.

At the approved Day 3 checkpoint, no Step 3 function, main paper loop, oracle
call, rank map, or ordinary sorting call was present.

## Day 4 Implementation Record

Day 4 adds only Step 3(a) and Step 3(b):

```text
step3a_increasing(state, iteration, left_boundary)
step3a_decreasing(state, iteration, right_boundary)
step3b_increasing(state, iteration, new_pair_id, right_boundary)
step3b_decreasing(state, iteration, new_pair_id, left_boundary)
```

Step 3(a):

- creates `P_i={z_(i-1),z_i}` with parity-derived family;
- creates a singleton list when the direction-specific boundary encloses
  `z_(i-1)`;
- otherwise inserts after the increasing left boundary or before the
  decreasing right boundary;
- verifies in O(1) that the supplied boundary matches the corresponding
  Step 1/2 stage result;
- rolls back backend registration if boundary insertion fails.

The rollback path uses
`OrdinarySiblingListBackend.unregister_unowned_pair()`, which can remove only
a finite pair with no parent, sibling list, or child list.

Step 3(b):

- records a skip when the opposite boundary encloses `z_(i-1)`;
- requires the increasing split boundary to be first and acquires `LEFT`;
- requires the decreasing split boundary to be last and acquires `RIGHT`;
- delegates atomic partition and ownership transfer to
  `split_pairs_at_value`;
- records scanned, copied, and ownership-transferred item counts without
  advancing the processed prefix.

`PaperJordanState.stage_results` stores the Step 1, Step 2, Step 3(a), and
Step 3(b) result for each iteration. Stage preconditions use this mapping
instead of rescanning the complete diagnostic trace. The trace remains an
append-only explanation artifact and is not the control-state index.

Focused tests cover increasing/decreasing singleton creation, both sibling
boundary insertions, both skip paths, one-sided acquisition in both
directions, two-nonempty-side Trace F and its reflected counterpart, wrong
orientation, wrong boundary side, registration rollback, ownership
invariants, trace fields, counters, and O(1) stage validation. Independent
ownership differential validation compares the actual family-tree parent of
every finite pair with strict interval containment for all oracle-valid
permutations through `n=7`: 16 at `n=4`, 50 at `n=5`, 144 at `n=6`, and 462
at `n=7`, for 672 matching cases in total. Oracle output is used only by the
external validator and never feeds the core state.

The current point `z_i` remains absent from `SortedOrderList`,
`processed_count` remains `i-1`, and `output_insertions` remains zero. No Step
3(c) function or complete paper loop is part of Day 4.

## Day 5 Step 3(c) Implementation Record

The first Day 5 checkpoint exposes:

```text
step3c_increasing(state, iteration, new_pair_id)
step3c_decreasing(state, iteration, new_pair_id)
```

Both functions require matching Step 3(a) and Step 3(b) stage results. They
select `z_(i-1)` when the new pair has no children. Otherwise, increasing uses
the geometric right endpoint of the rightmost child pair and decreasing uses
the geometric left endpoint of the leftmost child pair. For odd iterations,
the output anchor changes to `z1` only when `z1` lies strictly between the base
anchor and `z_i`.

Insertion is delegated to `SortedOrderList.insert_after` or
`SortedOrderList.insert_before`, whose local checks finish before link
mutation. A successful call:

```text
inserts z_i exactly once
sets processed_count = i
increments output_insertions
records any z1 output-anchor adjustment
records an immutable Step3CResult and trace event
```

Focused tests cover no-child insertion in both directions, all four
parent/child orientation combinations, odd-index adjustment in both
directions, odd-index non-adjustment, missing Step 3(b), inconsistent child
ownership, repeat-call atomicity, stable trace fields, and all 16 oracle-valid
four-point permutations. Oracle and `sorted` are used only for external test
expectations.

## Day 5 End-to-End Loop Record

The second Day 5 checkpoint adds:

```text
src/paper_jordan_sort.py
tests/test_paper_jordan_sort.py
paper_jordan_sort_valid(seq)
```

The pure core copies the input once, handles lengths zero through two with
fixed comparison logic, uses the existing three-point initializer for length
three, and executes Step 1, Step 2, Step 3(a), Step 3(b), and Step 3(c) for
each later paper index. Its only final output source is:

```text
state.partial_order.to_list()
```

The function assumes a pre-certified valid Jordan sequence with distinct,
mutually comparable values. It does not call the oracle, rank map, Python
`sorted`, the reference skeleton, or a static family-tree builder. Invalid
candidate recognition remains a separate wrapper concern.

Repository tests cover all small-input orders, representative flat/nested/
incremental generators, the two odd-index worked traces, nonnumeric comparable
values, input immutability, a syntax-tree purity audit, and every
oracle-accepted permutation through `n=7`:

```text
n=4:  16
n=5:  50
n=6: 144
n=7: 462
total: 672
```

The loop is not connected to experiment runners. Performance integration
remains pending.

## Day 6 Correctness and Diagnostics Record

Day 6 factors the valid-input implementation into one control-flow owner:

```text
_run_paper_jordan_valid(values, invariant_callback=None)
    -> PaperJordanState

paper_jordan_sort_valid(seq)
    -> state.partial_order.to_list()

paper_jordan_diagnostics_valid(seq)
    -> output + copied metrics + copied trace + invariant result
```

The public function materializes `seq` once. The internal initializer accepts
that already-materialized list and does not copy it again. Both public output
and diagnostics therefore execute the same Step 1/2/3(a)/(b)/(c) loop.

`validate_paper_jordan_state(state)` is a correctness/debug audit. Without
using the oracle, a rank map, or global sorting, it checks:

```text
processed point membership and count
partial-order bidirectional links
exact state/backend pair registry membership
dummy identity, family, endpoints, and backend registration
processed pair/end-index mapping and mapping-key identity
pair endpoint and parity-derived family consistency
sibling-list ownership and acyclic parent chains
metric shape and non-negative values
typed and semantically consistent stage results
exact initialization events
strict seven-event order and exact trace payload for every iteration
operation metrics recomputed from the validated trace
```

The callback runs after initialization and after each completed iteration.
It increments `invariant_checks`. Because it scans ownership and trace state,
its cost is deliberately excluded from the future timed algorithm path.

The audit rejects forged stage objects, changed trace payloads, unknown trace
fields, reordered events, and extra pair aliases. Historical Step 1/2
neighbors are reconstructed by filtering the maintained final point order to
the relevant processed prefix. Step 3(c) anchors are checked against pair
geometry and adjacency in that prefix.

Cross-consistency among mutable stage, trace, and metric records is not treated
as sufficient evidence. The audit deterministically replays the same unique
paper runner from initialization through the audited `processed_count`, then
compares:

```text
partial point order
pair/end-index mapping
all typed stage results
the complete trace
all core operation metrics except the audit-call counter
the canonical sibling-backend snapshot
```

The backend snapshot includes every pair field, parent/list ownership, child
list IDs, all live sibling-list contents, dummy registration, and the next
list ID. Coordinated changes to Step 3(a) ownership, Step 3(b) list IDs or
sizes, Step 3(c) child choice, trace, and metrics are therefore rejected
against replayed algorithm state.

Replay input is accepted only after a point-data trust-root check:

```text
every state point keeps its one-based paper index
every state point value equals the backend's initialization-time value
every processed partial-order point is the identical PointRef object
future points are checked against the backend even before insertion
```

The backend exposes only a read-only `point_value(point_id)` query for this
audit. Replacing the whole `state.points` tuple or changing one unprocessed
future point is rejected before replay.

Replay calls `_run_paper_jordan_state_values(..., stop_after=processed_count)`.
Production sorting and the public compatibility wrapper call that same
function. An AST regression test requires every directional Step 1/2/3 call
site to occur exactly once across the two core modules. Replay does not call
`sorted()` and does not feed data back into the state being audited.

The external script:

```text
experiments/validate_paper_algorithm.py
```

performs two independent checks:

```text
exhaustive oracle-filtered permutations through n=8
reproducible flat/nested/incremental generated cases at n=16,32,64,128
```

The script may compare each maintained prefix with `sorted(processed_prefix)`
and the final output with the external expected order. Those values exist only
inside the callback/validation layer and never feed algorithm state.

The recorded Day 6 run validated:

```text
n=0..8 exhaustive valid permutations: 2,074
  of which n=4..8 exercise the complete loop: 2,064

generated cases:
  flat_valid: 4
  nested_valid: 4
  incremental_valid: 40
  total: 48
```

All prefix invariants and final outputs passed. This is correctness evidence
for the ordinary-list implementation, not a linear-time complexity claim.

## Week 10 Timing-Policy Record

The implementation now has five immutable execution policies:

```text
checked:
    trace on, counters on, complete commit validation on

instrumented:
    trace on, counters on, complete commit validation off

trace_only:
    trace on, counters off, complete commit validation off

counters_only:
    trace off, counters on, complete commit validation off

minimal:
    trace off, counters off, complete commit validation off
```

All modes execute the same Step 1/2/3 loop. Cross-mode tests require identical
output, stage results, partial order, and canonical sibling-backend state.
Complete state audit remains capable of validating a state produced in
`minimal` mode.

The frozen Week 11 boundary is:

```text
before timing:
    oracle-certify the exact generated input
    compute structural metadata
    run one complete checked diagnostic

during paper timing:
    paper_jordan_sort_valid(seq, execution_mode="minimal")

after timing:
    compare output with the precomputed oracle result
```

The timed `minimal` call still performs ordinary-list operations, local safety
checks, rollback, stage-result recording, and output recovery. Removing
diagnostic work does not make the ordinary-list backend equivalent to the
paper's heterogeneous finger-tree implementation and does not create a
linear-time claim.

The canonical not-yet-executed Week 11 gate is stored in:

```text
experiments/week11_experiment_gate.py
```

That file preserves the unexecuted v1 M1 contract. The active M4 replacement
is `experiments/week11_experiment_gate_v2.py`.
