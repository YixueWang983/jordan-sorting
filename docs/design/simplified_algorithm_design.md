# Simplified Algorithm Design

Last updated: 2026-06-16

## Purpose

This document defines the scope and first design boundary for the simplified Jordan-sorting reference implementation.

Week 1 built the experimental infrastructure:

```text
generator -> oracle -> JSON case -> baselines -> CSV
```

Week 2 starts the transition from experimental infrastructure to algorithm-facing structures:

```text
notation -> family tree -> structural metrics -> reference skeleton
```

The first implementation should be honest about what it is:

```text
This is a correctness-oriented reference implementation.
It does not claim linear-time performance.
It does not implement level-linked search trees.
It does not implement heterogeneous finger trees.
```

## Scope

The simplified reference implementation should:

1. accept a candidate sequence,
2. run the existing oracle,
3. reject or mark invalid inputs clearly,
4. build upper and lower family-tree structures for oracle-valid inputs,
5. compute structural statistics,
6. return a stable dictionary result,
7. expose a trace that explains the reference pipeline,
8. use the oracle-sorted output as the first skeleton output,
9. provide a testable interface for later replacement by real simplified sorting operations.

The purpose of the first skeleton is not speed. The purpose is to make future algorithm work testable and explainable.

## Non-Goals

The Week 2 reference implementation should not:

- claim linear-time complexity,
- implement level-linked search trees,
- implement heterogeneous finger trees,
- implement dynamic split or merge operations,
- implement the full 1990 Jordan-sorting algorithm,
- replace the oracle as the source of validity checking,
- expand generator families,
- make final performance claims from Week 1 timing data.

The first version is allowed to use ordinary Python data structures, including lists and dictionaries.

## Input Assumptions

The public entry point will be:

```python
simplified_jordan_sort(seq)
```

The input `seq` may be any iterable of comparable values.

The implementation should immediately copy the input:

```python
values = list(seq)
```

This keeps the function from mutating the caller's original sequence.

The oracle is responsible for duplicate-value rejection. If values are duplicated, the result should be invalid with:

```text
reason = "duplicate values"
```

The first reference skeleton should support:

- empty sequences,
- singleton sequences,
- valid flat-like sequences,
- valid nested-like sequences,
- oracle-certified incremental valid sequences,
- upper crossing invalid sequences,
- lower crossing invalid sequences,
- random invalid sequences,
- mutation-based invalid sequences.

## Output Contract

The recommended return format is:

```python
{
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

Field meanings:

`valid`  
Whether the input candidate is oracle-valid as a Jordan sequence.

`sorted`  
The sorted output. In the first reference skeleton, this is `oracle_result["sorted"]`.

`reason`  
The oracle rejection reason, or `None` for valid inputs.

`oracle`  
The complete oracle result.

`families`  
Upper and lower family-tree structures for valid inputs. For invalid inputs, this should be `None`.

`stats`  
Structural profile output, such as interval counts, nesting counts, depth, density, and category.

`trace`  
A list of steps describing what the reference skeleton did.

`implementation`  
Always set to:

```text
reference_skeleton
```

until the implementation is replaced by real simplified sorting operations.

## Invalid Input Behavior

Invalid inputs should not construct family trees.

For invalid input, return:

```python
{
    "valid": False,
    "sorted": oracle_result["sorted"],
    "reason": oracle_result["reason"],
    "oracle": oracle_result,
    "families": None,
    "stats": structure_profile(values),
    "trace": [...],
    "implementation": "reference_skeleton",
}
```

Design choice:

`sorted` remains equal to `oracle_result["sorted"]` for invalid inputs. This keeps the return contract consistent with the existing experiment infrastructure, where invalid sequences can still have a well-defined ordinary sorted order.

The validity decision is represented by:

```text
valid
reason
```

not by whether `sorted` is present.

For invalid inputs, `families` is `None` because family-tree construction is defined only for oracle-valid candidate sequences. The function still returns `sorted` for comparison and debugging.

## Valid Input Behavior

For oracle-valid inputs, the skeleton should:

1. copy the sequence,
2. run the oracle,
3. build upper family tree,
4. build lower family tree,
5. compute structural stats,
6. set `sorted = oracle_result["sorted"]`,
7. return trace and metadata.

The first valid result should have:

```python
{
    "valid": True,
    "reason": None,
    "families": {
        "upper": ...,
        "lower": ...,
    },
    "implementation": "reference_skeleton",
}
```

## Relation to the Current Oracle

The oracle remains the source of truth for Week 2.

The reference skeleton should use the oracle for:

- duplicate rejection,
- validity classification,
- sorted reference output,
- invalid reason reporting.

The reference skeleton should not silently disagree with the oracle. Tests should compare skeleton results against oracle results.

Important distinction:

```text
oracle correctness target:
    valid/invalid classification and sorted reference output

reference skeleton target:
    expose intermediate structures and a stable algorithm-facing return format
```

The first skeleton may return the same sorted list as the oracle. That is acceptable only because the implementation is explicitly marked as `reference_skeleton`.

## Family Structures

Week 2 should use `src/family_tree.py` for family-tree data structures.

The planned representation is:

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

Field meanings:

`IntervalNode.id`  
Stable index into `FamilyTree.nodes`.

`IntervalNode.interval`  
The rank interval `(left, right)`.

`IntervalNode.pair_index`  
The zero-based index of the pair inside the upper or lower pair family.

`IntervalNode.parent`  
The parent node id, or `None` for root-level intervals.

`IntervalNode.children`  
Ordered child node ids.

`IntervalNode.depth`  
Root-level depth is `0`.

`FamilyTree.pair_family`  
Either `upper` or `lower`.

The serialized node shape should be stable:

```python
{
    "id": 0,
    "interval": [1, 6],
    "pair_index": 0,
    "parent": None,
    "children": [1],
    "depth": 0,
}
```

The first version should not use an artificial root.

Although the name is `FamilyTree`, the structure can be forest-like. A flat or partially flat family can have multiple root-level intervals.

Root-level intervals are stored in:

```python
FamilyTree.roots
```

Sibling lists are represented by:

```python
node.children
```

Root-level siblings are represented by:

```python
FamilyTree.roots
```

Both `FamilyTree.roots` and each node's `children` list should be ordered by increasing interval left endpoint, with the right endpoint as a deterministic tie-breaker if needed.

The sequence-level entry point should be:

```python
build_family_trees(seq, oracle_result=None)
```

It should use the oracle to reject invalid sequences before constructing family trees. If `oracle_result` is provided, it can reuse that result instead of calling the oracle again.

The raw interval-level builder:

```python
build_family_tree(intervals)
```

may defensively reject crossing intervals if called directly.

For direct interval-level inputs, the first builder accepts only normalized intervals `(left, right)` with `left < right`.

It rejects:

- malformed intervals,
- duplicate intervals,
- intervals with shared endpoints,
- crossing intervals.

This matches the assumptions of intervals generated from distinct candidate sequences.

When naming helper functions, avoid confusing pair families with generator families. In family-tree code, `pair_family` should mean only:

```text
upper
lower
```

Dataset generator families are separate labels such as `flat_valid`, `incremental_valid`, or `random_invalid`.

## Family Tree Construction Rule

Input: a validated laminar interval family.

For each interval `I`:

1. find every interval `J` that properly contains `I`,
2. choose the containing interval `J` with the smallest interval length as `I`'s parent,
3. if no such `J` exists, mark `I` as root-level,
4. sort root ids by `(left, right, pair_index)`,
5. sort each node's children by `(left, right, pair_index)`,
6. compute root depth as `0` and child depth as `parent depth + 1`.

The first implementation may use an `O(k^2)` scan over intervals. Week 2 does not claim linear-time family-tree construction.

## Error Policy

`simplified_jordan_sort(seq)`:

- does not raise for oracle-invalid candidates,
- returns `valid=False`, `reason`, and `families=None`.

`build_family_trees(seq, oracle_result=None)`:

- raises `ValueError` for oracle-invalid candidates.

`build_family_tree(intervals)`:

- raises `ValueError` for malformed, duplicate, shared-endpoint, or crossing intervals.

`interval_contains(...)` and `proper_interval_contains(...)`:

- are pure predicates,
- do not call the oracle.

## Structural Stats

Week 2 `src/stats.py` should focus on structural metrics only.

The main public function should be:

```python
structure_profile(seq)
```

The first profile shape should include:

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

For invalid candidates, the first version should use a conservative contract:

```python
{
    "valid": False,
    "reason": oracle_result["reason"],
    "upper_interval_count": None,
    "lower_interval_count": None,
    "total_interval_count": None,
    "upper_root_count": None,
    "lower_root_count": None,
    "upper_nesting_count": None,
    "lower_nesting_count": None,
    "nesting_count": None,
    "nesting_density": None,
    "upper_max_depth": None,
    "lower_max_depth": None,
    "max_depth": None,
    "category": "invalid",
}
```

This keeps invalid candidates from being mistaken for inputs with valid family-tree structure.

Suggested structural categories:

- `invalid`
- `strict_flat`
- `low_nesting_valid`
- `medium_nesting_valid`
- `nested_heavy_valid`

`strict_flat` should be reserved for:

```text
nesting_count == 0
```

Low nesting should not be called flat.

Performance instrumentation such as split counts, traversal steps, list scans, and tree rotations belongs to a later phase.

## Trace Format

The trace should be simple and stable.

The first version can use a list of dictionaries:

```python
[
    {"step": "copy_input", "n": 8},
    {"step": "oracle", "valid": True, "reason": None},
    {"step": "build_family_trees", "upper_nodes": 3, "lower_nodes": 2},
    {"step": "structure_profile", "category": "strict_flat"},
    {"step": "return_oracle_sorted_output"},
]
```

Trace entries should help explain the skeleton pipeline. They do not need to record every low-level operation.

## Testing Strategy

Week 2 tests should distinguish skeleton correctness from final algorithm correctness.

Recommended test names:

- `test_reference_skeleton_matches_oracle_sorted_output`
- `test_reference_skeleton_rejects_invalid_inputs`
- `test_reference_skeleton_returns_family_structures`
- `test_reference_skeleton_records_trace`

Avoid names such as:

```text
test_algorithm_correctness
```

because the Week 2 implementation is not yet the final simplified Jordan-sorting algorithm.

Test cases should include:

- empty sequence,
- singleton sequence,
- `flat_valid`,
- `nested_valid`,
- `incremental_valid`,
- `invalid_upper_crossing`,
- `invalid_lower_crossing`,
- `random_invalid`,
- `mutation_based_invalid`.

## What This Implementation Will Not Claim

The Week 2 reference skeleton will not claim:

- linear time,
- full Jordan sorting,
- full reproduction of the 1990 algorithm,
- implementation of level-linked search trees,
- implementation of heterogeneous finger trees,
- final performance results.

The correct claim is:

```text
The Week 2 skeleton exposes the intermediate structures and return contract needed for a future simplified Jordan-sorting implementation.
```

## First Implementation Outline

The first `simplified_jordan_sort` implementation should follow this outline:

```python
def simplified_jordan_sort(seq):
    values = list(seq)
    oracle_result = oracle(values)

    trace = [
        {"step": "copy_input", "n": len(values)},
        {
            "step": "oracle",
            "valid": oracle_result["valid"],
            "reason": oracle_result["reason"],
        },
    ]

    if not oracle_result["valid"]:
        stats = structure_profile(values)
        trace.append({
            "step": "structure_profile",
            "category": stats["category"],
        })
        trace.append({
            "step": "reject_invalid_input",
            "reason": oracle_result["reason"],
        })
        return {
            "valid": False,
            "sorted": oracle_result["sorted"],
            "reason": oracle_result["reason"],
            "oracle": oracle_result,
            "families": None,
            "stats": stats,
            "trace": trace,
            "implementation": "reference_skeleton",
        }

    families = build_family_trees(values, oracle_result=oracle_result)
    trace.append({
        "step": "build_family_trees",
        "upper_nodes": len(families["upper"].nodes),
        "lower_nodes": len(families["lower"].nodes),
    })
    stats = structure_profile(values)
    trace.append({
        "step": "structure_profile",
        "category": stats["category"],
    })
    trace.append({"step": "return_oracle_sorted_output"})

    return {
        "valid": True,
        "sorted": oracle_result["sorted"],
        "reason": None,
        "oracle": oracle_result,
        "families": families,
        "stats": stats,
        "trace": trace,
        "implementation": "reference_skeleton",
    }
```

This outline is intentionally conservative. It should become executable only after `family_tree.py` and structural `stats.py` are defined.
