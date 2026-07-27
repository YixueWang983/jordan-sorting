# Ordinary-List Reconstruction of the 1990 Jordan-Sorting Algorithm

Last updated: 2026-07-27

Status: Week 9 implementation-facing specification, before main algorithm code.

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

### `split`

Conceptual API:

```python
split(list_id, boundary_value) -> (left_list_id, right_list_id)
```

For every pair in the input list:

```text
left output:
    both finite endpoint values are less than boundary_value

right output:
    both finite endpoint values are greater than boundary_value
```

An existing processed pair cannot have an endpoint equal to the new unprocessed
point `z_i`, because input values are distinct.

If a pair straddles the boundary, the backend raises an invariant error. The
paper's locality argument requires the selected list to partition cleanly.

The input list is retired. Each nonempty output receives a live list ID.
Relative order is preserved, and every moved pair receives its new
`sibling_list_id`.

The algorithm layer, rather than the generic backend, decides which output is
reassigned to the new pair and which remains with the old parent.

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
insert z_i immediately after z_(i-1)
```

Otherwise:

```text
C = rightmost child pair of N
insert z_i immediately after C.second
```

`C.second` means the second endpoint in curve order, matching the paper's
`z_m` in child pair `{z_(m-1), z_m}`. It is not chosen by sorting the two
endpoints inside the pair.

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
insert z_i immediately before z_(i-1)
```

Otherwise:

```text
C = leftmost child pair of N
insert z_i immediately before C.second
```

This mirrored interpretation must be verified with focused tests obtained by
reflecting valid increasing-orientation examples. It must not be implemented
as an untested assumption.

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
output_anchor_point_id
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
split_items_moved
output_insertions
invariant_checks
trace_event_count
```

The uninstrumented path remains available for timing. Detailed diagnostics may
be collected in a separate untimed run.

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

## Test Matrix

| Area | Required cases |
| --- | --- |
| index conversion | first point, last point, rejected index 0 |
| parity | `P2/P4` upper, `P3/P5` lower |
| same-family pair selection | point as first endpoint, point as second endpoint |
| `z1` exception | lower-family predecessor and successor cases |
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
| Step 3(b) | no children, one child, multiple children, ownership transfer |
| Step 3(c) | no child, extreme child, increasing and decreasing |
| full loop | flat, nested, incremental, odd/even lengths |
| independence | no oracle output, no rank map, no full sorting |

## Paper-to-Implementation Ambiguity Table

| Paper statement | Fixed implementation interpretation | Required check |
| --- | --- | --- |
| predecessor of `z_(i-1)` | previous linked node in `SortedOrderList` | left boundary and negative sentinel |
| successor of `z_(i-1)` | next linked node in `SortedOrderList` | right boundary and positive sentinel |
| pair containing `v` or `w` | processed incident pair whose end-index parity matches `i` | first-endpoint, second-endpoint, and `z1` exception |
| `{-infinity,+infinity}` | one distinct dummy pair per family | both family boundaries |
| insert after left sibling | restricted insertion after a last-list anchor | reject non-boundary anchor |
| mirrored insert before right sibling | restricted insertion before a first-list anchor | decreasing-orientation test |
| split at `z_i` | partition only when every pair has both endpoints on one side | two sides, empty side, and straddle rejection |
| split off children | transfer the enclosed side to the new pair and preserve the other side's old owner | ownership conservation |
| rightmost child | final pair in left-to-right sibling order | Step 3(c) increasing |
| leftmost child | first pair in left-to-right sibling order | Step 3(c) decreasing |
| insert after/before `z_m` | use the child's second endpoint in curve order | endpoint-orientation test |
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
    O(1) at Python-list ends when no ownership scan is needed

ordinary sibling split:
    O(length of scanned sibling list)

ownership updates after split:
    O(number of moved pairs)
```

Other bookkeeping may add ordinary dictionary or list costs. No total linear
bound is claimed.

The theoretical heterogeneous finger-tree backend remains a paper-level
comparison point, not an implemented component.

## Open Questions Before Step 3 Implementation

The following interpretations are now explicit but still require direct
confirmation through mirrored examples and focused tests:

1. In increasing Step 3(b), the left split output is reassigned to the new pair
   and the right output remains with the old parent.
2. In decreasing Step 3(b), the right split output is reassigned to the new pair
   and the left output remains with the old parent.
3. In decreasing Step 3(c), the reflected rule inserts `z_i` immediately before
   the second curve-order endpoint of the leftmost child.
4. When one split output is empty, the retired input list is replaced only by
   the nonempty output and no persistent empty list is stored.

These questions do not block implementation of the standalone list backend.
They do block declaring the full Step 3 loop correct.

## Day 1 Acceptance Record

This specification is ready for Day 2 data-structure implementation when:

- paper indexing and parity are stable;
- the core purity boundary is accepted;
- sentinel and dummy identities are accepted;
- pair and sibling-list ownership fields are accepted;
- the two insert operations are clearly separated;
- the proposed mirrored Step 3 interpretation is treated as testable, not
  silently assumed;
- no unresolved item is hidden by oracle-sorted output.
