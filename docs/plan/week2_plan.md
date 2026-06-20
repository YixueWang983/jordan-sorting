# Week 2 Plan

Last updated: 2026-06-16

## Goal

Design the simplified Jordan-sorting reference implementation and implement the first intermediate structures needed by the future algorithm.

In Chinese:

```text
设计 simplified Jordan sorting 的 reference implementation，
并实现未来算法需要的第一批中间结构。
```

Week 2 should move from the Week 1 experimental loop into the first algorithm-facing structures. The goal is not to claim that the Jordan-sorting algorithm is complete. The goal is to define notation, design data structures, implement structural helpers, and create a clearly marked reference skeleton.

## Scope

Week 2 should produce:

- `docs/design/notation.md`
- `docs/design/simplified_algorithm_design.md`
- `src/family_tree.py`
- `tests/test_family_tree.py`
- `src/stats.py` structural metrics
- `tests/test_stats.py`
- `src/simplified_jordan.py`
- `tests/test_simplified_jordan.py`
- `docs/progress/week2_summary.md`

Some of these may start as design documents or skeletons. The priority is correctness, clarity, and testability.

## Non-Goals

Week 2 should not attempt to:

- implement dense invalid generators,
- introduce Hypothesis property-based testing,
- produce large-scale charts,
- implement finger search trees,
- implement level-linked search trees,
- implement heterogeneous finger trees,
- claim linear-time performance,
- continue expanding generator families unless a blocker requires it.

The Week 2 main line is:

```text
concept -> data structure -> skeleton -> tests
```

## Week 2 Day 1: Notation + Design Scope

Main output:

```text
docs/design/notation.md
docs/design/simplified_algorithm_design.md
```

`docs/design/notation.md` should be a reusable terminology document. It should define:

- candidate sequence,
- Jordan sequence,
- upper pair,
- lower pair,
- rank,
- rank interval,
- laminar family,
- crossing,
- nesting,
- family tree,
- sibling list,
- split.

`docs/design/simplified_algorithm_design.md` should focus on the design of the simplified reference implementation. First version sections:

1. Scope
2. Non-goals
3. Input assumptions
4. Output contract
5. Relation to the current oracle
6. What this implementation will not claim

Required wording:

```text
This is a correctness-oriented reference implementation.
It does not claim linear-time performance.
It does not implement level-linked search trees.
It does not implement heterogeneous finger trees.
```

Completion criteria:

- [x] notation document exists.  
  Done on 2026-06-16.

- [x] design document exists.  
  Done on 2026-06-16.

- [x] scope and non-goals are explicit.  
  Done on 2026-06-16.

- [x] the design separates reference implementation from the full theoretical algorithm.  
  Done on 2026-06-16.

## Week 2 Day 2: Family Tree Data Structures

Main output:

```text
src/family_tree.py
tests/test_family_tree.py
```

The first implementation should focus on:

- `interval_contains(...)`
- `proper_interval_contains(...)`
- `build_family_intervals(seq, pair_family)`
- `build_family_tree(intervals, pair_family)`
- `build_family_trees(seq, oracle_result=None)`
- `compute_depths(...)`

The goal is to make this chain work:

```text
pairs -> intervals -> family tree
```

`family_tree.py` is preferred over `intervals.py` because the future simplified algorithm needs interval families, parent-child relations, sibling ordering, depths, and tree dumps, not isolated intervals only.

First representation decision:

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

Do not add an artificial root in the first version. Root-level intervals are stored in `FamilyTree.roots`. Sibling lists are represented by each node's ordered `children` list; root-level siblings are represented by `roots`.

Although the structure is named `FamilyTree`, it can have multiple roots. In that sense, the representation is forest-like, with `roots` acting as the top-level sibling list.

In family-tree code, `pair_family` means only `upper` or `lower`. This should not be confused with dataset generator families such as `flat_valid`, `incremental_valid`, or `random_invalid`.

`FamilyTree.nodes` preserves the input interval order. For sequence-derived intervals, this means pair order. Only `roots` and `children` are sorted by `(left, right, pair_index)`.

The interval predicates should be:

```python
def interval_contains(outer, inner):
    outer_left, outer_right = outer
    inner_left, inner_right = inner
    return outer_left <= inner_left and inner_right <= outer_right


def proper_interval_contains(outer, inner):
    outer_left, outer_right = outer
    inner_left, inner_right = inner
    return outer_left < inner_left and inner_right < outer_right
```

The family-tree builder uses `proper_interval_contains` for parent selection.

Responsibility boundary:

- `build_family_trees(seq, oracle_result=None)` rejects invalid sequences using the oracle before constructing trees.
- `build_family_tree(intervals, pair_family)` may also defensively reject crossing intervals if called directly.
- direct interval-level inputs reject malformed intervals, duplicate intervals, shared endpoints, and crossings.
- direct interval-level inputs assign `pair_index` from input order with `enumerate(intervals)`.

Non-blocking note (P2.1):

- `build_family_intervals(seq, pair_family)` does not currently add duplicate-sequence guards.
  The sequence-level entrypoint `build_family_trees(seq, oracle_result=None)` already checks validity via
  `oracle` first. If this helper becomes a public API in the future, add duplicate validation then.

Parent construction rule:

1. for each interval, find all proper containers,
2. choose the smallest proper container as the parent,
3. use root-level status if no container exists,
4. order roots and children by `(left, right, pair_index)`,
5. compute root depth as `0` and child depth as parent depth plus one.

The first implementation may use an `O(k^2)` scan.

Testing should cover:

- flat valid cases,
- nested valid cases,
- multiple disjoint root-level intervals,
- multi-level nesting,
- invalid crossing sequences rejected by the sequence-level entry point.
- direct interval-level crossing inputs rejected defensively by the tree builder.

Recommended concrete tests:

1. flat upper family:

```python
seq = [1, 2, 3, 4, 5, 6]
```

Expected upper roots:

```text
3 root nodes, all depth 0
```

2. nested upper family:

```python
seq = [1, 6, 2, 5, 3, 4]
```

Expected upper intervals:

```text
(1, 6), (2, 5), (3, 4)
```

Expected parent chain:

```text
0 -> 1 -> 2
```

3. nested lower family:

```python
seq = [1, 6, 2, 5, 3, 4]
```

Expected lower intervals:

```text
(2, 6), (3, 5)
```

Expected parent chain:

```text
0 -> 1
```

4. direct crossing reject:

```python
intervals = [(1, 3), (2, 4)]
```

Expected behavior:

```text
raises ValueError
```

5. duplicate interval reject:

```python
intervals = [(1, 4), (1, 4)]
```

Expected behavior:

```text
raises ValueError
```

6. shared endpoint reject:

```python
intervals = [(1, 4), (1, 3)]
```

Expected behavior:

```text
raises ValueError
```

Completion criteria:

- laminar intervals can be converted into a parent/children/depth representation,
- invalid sequences and crossing interval inputs are rejected at the appropriate entry point,
- upper and lower families can be built separately,
- tests describe expected parent-child behavior,
- root-level sibling behavior is represented through `FamilyTree.roots`.

## Week 2 Day 3: Structural Metrics

Main output:

```text
src/stats.py
tests/test_stats.py
```

Week 2 `stats.py` should be limited to structural statistics. Performance instrumentation belongs to a later phase.

Recommended public function:

```python
structure_profile(seq)
```

First version return shape:

```python
{
    "valid": bool,
    "reason": str | None,
    "upper_interval_count": int | None,
    "lower_interval_count": int | None,
    "total_interval_count": int | None,
    "upper_root_count": int | None,
    "lower_root_count": int | None,
    "upper_nesting_count": int | None,
    "lower_nesting_count": int | None,
    "nesting_count": int | None,
    "nesting_density": float | None,
    "upper_max_depth": int | None,
    "lower_max_depth": int | None,
    "max_depth": int | None,
    "category": str,
}
```

Suggested categories:

- `invalid`
- `strict_flat`
- `low_nesting_valid`
- `medium_nesting_valid`
- `nested_heavy_valid`

Important rule:

```text
strict_flat means nesting_count == 0.
Low nesting should not be called flat.
```

Completion criteria:

- `structure_profile(seq)` works for valid and invalid cases,
- invalid cases are marked as `invalid` with structural fields set to `None`,
- flat and nested examples receive conservative categories,
- tests cover generated examples and edge cases.

## Week 2 Day 4: Simplified Algorithm API Design

Main output:

```text
docs/design/simplified_algorithm_design.md
```

Extend the design document with:

- API,
- return format,
- invalid input behavior,
- trace format,
- stats format,
- testing strategy,
- fallback behavior.

Recommended interface:

```python
def simplified_jordan_sort(seq):
    return {
        "valid": bool,
        "sorted": list,
        "reason": str | None,
        "oracle": dict,
        "families": dict | None,
        "stats": dict,
        "trace": list,
        "implementation": "reference_skeleton",
    }
```

Design decision:

For invalid input, keep `sorted` equal to `oracle_result["sorted"]` for consistency with existing experiment infrastructure, while using `valid` and `reason` to signal rejection.

For invalid input, return:

```python
"families": None
```

Family-tree construction is only performed for oracle-valid sequences.

Completion criteria:

- API and return format are documented,
- invalid behavior is explicit,
- trace and stats fields are described,
- skeleton status is clearly stated.

## Week 2 Day 5: Reference Skeleton

Main output:

```text
src/simplified_jordan.py
tests/test_simplified_jordan.py
```

First version logic:

1. `values = list(seq)`
2. `oracle_result = oracle(values)`
3. if invalid, return `valid=False` with reason, oracle-sorted output, and `families=None`
4. if valid, build upper/lower family structures with `build_family_trees(values, oracle_result=oracle_result)`
5. compute `structure_profile`
6. set `sorted = oracle_result["sorted"]`
7. return trace
8. include `"implementation": "reference_skeleton"`

This skeleton is useful because it fixes the interface, exposes intermediate structures, and creates a testing target. It is not yet the actual simplified Jordan-sorting algorithm.

Completion criteria:

- `simplified_jordan_sort(seq)` runs,
- valid inputs return oracle-sorted output,
- invalid inputs are clearly marked invalid,
- family structures are returned,
- stats are returned,
- trace is non-empty,
- return value includes `"implementation": "reference_skeleton"`.

## Week 2 Day 6: Tests + Documentation Pass

Main output:

```text
tests/test_simplified_jordan.py
documentation updates
```

Test cases should cover:

- empty sequence,
- singleton sequence,
- `flat_valid`,
- `nested_valid`,
- `incremental_valid`,
- `invalid_upper_crossing`,
- `invalid_lower_crossing`,
- `random_invalid`,
- `mutation_based_invalid`.

Recommended test names:

- `test_reference_skeleton_matches_oracle_sorted_output`
- `test_reference_skeleton_rejects_invalid_inputs`
- `test_reference_skeleton_returns_family_structures`
- `test_reference_skeleton_records_trace`

Avoid names such as `test_algorithm_correctness`, because the Week 2 implementation is a skeleton, not the final algorithm.

Completion criteria:

- skeleton tests pass,
- family tree tests pass,
- structure metric tests pass,
- documentation matches the code,
- all unit tests pass.

## Week 2 Day 7: Week 2 Summary

Main output:

```text
docs/progress/week2_summary.md
```

The summary should explain:

1. designed notation and scope,
2. designed interval/family tree structures,
3. implemented structural metrics,
4. implemented reference skeleton,
5. what is still only a skeleton,
6. what is not yet simplified Jordan sorting,
7. Week 3 implementation plan.

Completion criteria:

- summary document exists,
- Week 2 work is clearly separated from Week 3 work,
- limitations are explicit,
- next steps are actionable.

## Main Risks

### Risk 1: Family Tree Construction Takes Longer Than Expected

This is the most likely Week 2 bottleneck.

Keep the first version simple:

- input laminar intervals,
- output parent/children/depth,
- reject crossings,
- no split,
- no merge,
- no dynamic updates.

### Risk 2: Skeleton Is Mistaken for the Algorithm

The first `simplified_jordan_sort` should be clearly marked as:

```text
reference_skeleton
```

It may use `oracle_result["sorted"]` as the sorted output. This is acceptable only if the documentation clearly states that the actual simplified sorting operations are future work.

### Risk 3: Structural Metrics Become Performance Instrumentation

Week 2 `stats.py` should focus on structure:

- interval counts,
- nesting counts,
- nesting density,
- max depth,
- category.

Performance metrics such as split counts, traversal steps, list scans, and tree rotations should wait until Week 3 or later.

## Week 2 Exit Criteria

Week 2 is complete if:

1. `docs/design/notation.md` exists.
2. `docs/design/simplified_algorithm_design.md` exists.
3. `src/family_tree.py` exists or the family-tree design is fully documented.
4. `tests/test_family_tree.py` exists if `family_tree.py` is implemented.
5. `src/stats.py` contains `structure_profile(seq)` and `tests/test_stats.py` covers flat, nested, and invalid cases.
6. `src/simplified_jordan.py` contains a clearly marked reference skeleton.
7. `tests/test_simplified_jordan.py` validates skeleton behavior against the oracle.
8. `docs/progress/week2_summary.md` explains what is design, what is skeleton, and what remains for Week 3.

## Immediate Next Step

Current task:

```text
Week 3 Day 1: Reference Pipeline Strengthening
```

Expected outputs:

```text
No new Week 2 artifact.
Use docs/progress/week2_summary.md as the completed handoff.
```

Focus on:

- lock Day6 contract tests,
- explicit skeleton-vs-final distinction,
- preparing the handoff state for Week 3.
