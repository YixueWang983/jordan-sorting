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
class FamilyTree:
    family: str
    nodes: list[IntervalNode]
    roots: list[int]
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
build_family_trees(seq)
```

It should use the oracle to reject invalid sequences before constructing family trees.

The raw interval-level builder:

```python
build_family_tree(intervals)
```

may defensively reject crossing intervals if called directly.

When naming helper functions, avoid confusing pair families with generator families. In family-tree code, `pair_family` should mean only:

```text
upper
lower
```

Dataset generator families are separate labels such as `flat_valid`, `incremental_valid`, or `random_invalid`.

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
    "upper_interval_count": int,
    "lower_interval_count": int,
    "upper_nesting_count": int,
    "lower_nesting_count": int,
    "nesting_count": int,
    "nesting_density": float,
    "max_depth": int,
    "category": str,
}
```

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
    {"step": "build_family_trees"},
    {"step": "structure_profile"},
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

    stats = structure_profile(values)

    if not oracle_result["valid"]:
        trace.append({"step": "reject_invalid_input"})
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

    families = build_family_trees(values)
    trace.append({"step": "build_family_trees"})
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
