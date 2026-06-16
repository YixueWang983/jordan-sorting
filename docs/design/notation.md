# Notation

Last updated: 2026-06-16

This document defines the project notation used by the oracle, generators, future family-tree structures, and the simplified Jordan-sorting reference implementation.

The purpose is to keep the implementation terminology stable before adding more algorithm-facing code.

## Sequence

Definition:

A sequence is a finite ordered list of comparable values:

```text
x1, x2, x3, ..., xn
```

Example:

```text
[6, 9, 8, 2, 4, 5]
```

Implementation note:

The code generally accepts any iterable and immediately converts it to a list:

```python
values = list(seq)
```

This prevents helper functions from mutating the caller's original input.

## Candidate Sequence

Definition:

A candidate sequence is an input sequence that may or may not satisfy the project's Jordan-sequence validity condition.

In this project, most public functions accept candidate sequences. The oracle decides whether a candidate is valid.

Example:

```text
[1, 3, 2, 4]      candidate sequence
```

Implementation note:

Use `candidate sequence` or `invalid candidate` when discussing inputs that may be rejected. Avoid calling a rejected input an invalid Jordan sequence, because a valid Jordan sequence is already a candidate that passed the oracle.

## Valid Jordan Sequence

Definition:

In this project, a candidate sequence is oracle-valid as a Jordan sequence if and only if:

```text
V(seq) =
    distinct_values(seq)
    and laminar(upper_rank_intervals(seq))
    and laminar(lower_rank_intervals(seq))
```

In words, a valid Jordan sequence is a candidate sequence with distinct values whose upper pair family and lower pair family are both laminar after converting pairs to sorted-order rank intervals.

Implementation note:

Duplicate values are rejected before rank intervals are built, because duplicate values make the one-based rank map ambiguous.

The current oracle uses this operational validity predicate:

```text
valid = distinct values and upper family is laminar and lower family is laminar
```

This is the project's current correctness condition. It is not a claim that this predicate alone implements the full theoretical Jordan-sorting algorithm.

An invalid candidate is rejected because of duplicate values, an upper crossing, a lower crossing, or both.

## Distinct Values

Definition:

A sequence has distinct values if no value appears more than once.

Example:

```text
[1, 3, 2, 4]      distinct
[1, 2, 2, 3]      not distinct
```

Implementation note:

The oracle rejects duplicate values before building rank intervals:

```text
reason = "duplicate values"
```

Duplicate rejection is separate from upper/lower crossing failure.

## Upper Pair

Definition:

Upper pairs are consecutive pairs starting from the first element:

```text
(x1, x2), (x3, x4), (x5, x6), ...
```

Example:

For:

```text
[6, 9, 8, 2, 4, 5]
```

the upper pairs are:

```text
(6, 9), (8, 2), (4, 5)
```

Implementation note:

Upper pairs use zero-based indices:

```text
(values[0], values[1]), (values[2], values[3]), ...
```

If the sequence length is odd, the final element has no upper partner.

## Lower Pair

Definition:

Lower pairs are consecutive pairs starting from the second element:

```text
(x2, x3), (x4, x5), (x6, x7), ...
```

Example:

For:

```text
[6, 9, 8, 2, 4, 5]
```

the lower pairs are:

```text
(9, 8), (2, 4)
```

Implementation note:

Lower pairs use zero-based indices:

```text
(values[1], values[2]), (values[3], values[4]), ...
```

The first element is not part of the lower family. If the sequence length is even, the final element has no lower partner.

## Rank

Definition:

The rank of a value is its one-based position in the sorted order of the sequence.

Example:

For:

```text
seq = [6, 9, 8, 2, 4, 5]
sorted(seq) = [2, 4, 5, 6, 8, 9]
```

the ranks are:

```text
rank(2) = 1
rank(4) = 2
rank(5) = 3
rank(6) = 4
rank(8) = 5
rank(9) = 6
```

Implementation note:

The project uses one-based ranks for readability:

```python
{value: index for index, value in enumerate(sorted(values), start=1)}
```

## Rank Interval

Definition:

A pair `(a, b)` becomes the closed interval:

```text
[min(rank(a), rank(b)), max(rank(a), rank(b))]
```

Example:

For:

```text
seq = [6, 9, 8, 2, 4, 5]
```

the upper pair `(6, 9)` becomes:

```text
[4, 6]
```

because:

```text
rank(6) = 4
rank(9) = 6
```

Implementation note:

The code usually stores rank intervals as tuples:

```python
(left, right)
```

where `left <= right`.

## Interval Family

Definition:

An interval family is a collection of rank intervals from either the upper pairs or the lower pairs.

Example:

For:

```text
[6, 9, 8, 2, 4, 5]
```

the upper family consists of the intervals generated from:

```text
(6, 9), (8, 2), (4, 5)
```

Implementation note:

Upper and lower interval families are checked separately. An upper interval is not compared with a lower interval when checking laminarity.

## Disjoint Intervals

Definition:

Two intervals `[a, b]` and `[c, d]` are disjoint if one ends before the other begins:

```text
b < c
```

or:

```text
d < a
```

Example:

```text
[1, 2] and [4, 5]
```

are disjoint.

## Nesting

Definition:

One interval properly nests inside another if it is strictly contained in the other interval.

For intervals `[a, b]` and `[c, d]`, `[c, d]` properly nests inside `[a, b]` if:

```text
a < c and d < b
```

Example:

```text
[2, 3] is nested inside [1, 6]
```

Implementation note:

Week 2 will use nesting to build family trees and structural profiles. A sequence can be valid while still having nesting.

## Crossing

Definition:

Two intervals cross if one starts inside the other but ends outside it:

```text
a < c < b < d
```

or:

```text
c < a < d < b
```

Example:

```text
[1, 3] and [2, 4]
```

cross.

Implementation note:

Crossing intervals make the corresponding upper or lower family invalid.

## Laminar Family

Definition:

A family of intervals is laminar if every pair of intervals is either disjoint or properly nested.

Example:

```text
[1, 6], [2, 3], [4, 5]
```

is laminar.

```text
[1, 3], [2, 4]
```

is not laminar.

Implementation note:

The current oracle checks laminarity with a simple `O(n^2)` pairwise crossing check.

## Family Tree

Definition:

A family tree represents the nesting structure of a laminar interval family.

An interval's parent is the smallest interval that properly contains it. Intervals with no parent are root-level intervals.

Strictly speaking, a family tree may be forest-like because a laminar family can have multiple root-level intervals. The project keeps the name `FamilyTree`, but its representation allows multiple roots.

Example:

```text
[1, 8]
  [2, 3]
  [4, 7]
    [5, 6]
```

Implementation note:

Week 2 will use:

```python
@dataclass
class IntervalNode:
    id: int
    interval: tuple[int, int]
    pair_index: int
    parent: int | None
    children: list[int]
    depth: int


@dataclass
class FamilyTree:
    pair_family: str
    nodes: list[IntervalNode]
    roots: list[int]
```

The first version will not use an artificial root. Root-level intervals are stored in `FamilyTree.roots`.

The root-level intervals form the top-level sibling list. Any artificial root used later for printing or visualization should be treated as a debugging convenience, not as a real interval from the input.

## Sibling List

Definition:

Sibling intervals are intervals with the same parent. Root-level intervals are siblings of each other.

Sibling lists are ordered by increasing left endpoint. Ties should not normally occur inside one pair family with distinct input values, but if an implementation needs a deterministic tie-breaker it can use the right endpoint.

Implementation note:

In the first family-tree representation:

- root-level siblings are represented by `FamilyTree.roots`,
- non-root siblings are represented by a node's ordered `children` list.

Sibling order should be deterministic, normally by interval start rank and then end rank.

Do not confuse this with future `prev_sibling` or `next_sibling` links. Week 2 only needs ordered Python lists.

## Split

Definition:

A split is a future algorithm operation that separates or processes part of a family-tree or sibling-list structure.

Implementation note:

Week 2 only defines the term. It does not implement split operations.

The first simplified reference skeleton should expose structures that make future split operations possible, but it must not claim that the full split-based Jordan-sorting algorithm is implemented.

## Structural Category

Definition:

A structural category is a post-generation label assigned by structural metrics, not by the generator name.

Example categories planned for Week 2:

```text
invalid
strict_flat
low_nesting_valid
medium_nesting_valid
nested_heavy_valid
```

Implementation note:

Generator family and structural category are different concepts:

- generator family describes how the sequence was produced,
- structural category describes what the generated sequence looks like after analysis.

For example, `nested_valid` is a generator family name, not a structural category name.

Similarly, `family` can mean different things in different contexts. In interval code, pair family should mean only `upper` or `lower`. In dataset code, generator family means labels such as `flat_valid`, `incremental_valid`, or `random_invalid`.
