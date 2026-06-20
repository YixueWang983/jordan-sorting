# Structural Examples

This document shows concrete examples used for debugging, checking the contract
between code and notation, and writing thesis sections on structure.

## Flat Valid Example

`seq = [1, 2, 3, 4, 5, 6]`

### Oracle

```python
{
    "valid": True,
    "sorted": [1, 2, 3, 4, 5, 6],
    "distinct_values": True,
    "upper_ok": True,
    "lower_ok": True,
    "reason": None,
}
```

### Intervals

Upper pairs:

```text
(1, 2), (3, 4), (5, 6) -> intervals: [(1, 2), (3, 4), (5, 6)]
```

Lower pairs:

```text
(1, 2), (3, 4), (5, 6) -> intervals: [(2, 3), (4, 5)]
```

### Family Trees

Upper tree dump:

```text
[1, 2]
[3, 4]
[5, 6]
```

Lower tree dump:

```text
[2, 3]
[4, 5]
```

### `structure_profile(...)`

```python
{
    "valid": True,
    "reason": None,
    "upper_interval_count": 3,
    "lower_interval_count": 2,
    "total_interval_count": 5,
    "upper_root_count": 3,
    "lower_root_count": 2,
    "upper_nesting_count": 0,
    "lower_nesting_count": 0,
    "nesting_count": 0,
    "nesting_density": 0.0,
    "upper_max_depth": 0,
    "lower_max_depth": 0,
    "max_depth": 0,
    "category": "strict_flat"
}
```

### `simplified_jordan_sort(...)` excerpt

```python
{
    "valid": True,
    "sorted": [1, 2, 3, 4, 5, 6],
    "reason": None,
    "implementation": "reference_skeleton",
    "implementation_stage": "week2_interface_skeleton",
    "backend": {
        "name": "ordinary_list",
        "uses_oracle_sorted_output": True,
        "linear_time_claim": False,
    },
    "trace": [
        "copy_input",
        "oracle",
        "build_family_trees",
        "structure_profile",
        "prepare_reference_backend",
        "extract_rank_order",
        "return_reference_sorted_output"
    ],
}
```

## Nested Valid Example

`seq = [1, 6, 2, 5, 3, 4]`

### Oracle

```python
{
    "valid": True,
    "sorted": [1, 2, 3, 4, 5, 6],
    "distinct_values": True,
    "upper_ok": True,
    "lower_ok": True,
    "reason": None,
}
```

### Intervals

Upper intervals:

```text
(1, 6), (2, 5), (3, 4)
```

Lower intervals:

```text
(2, 6), (3, 5)
```

### Family Trees

Upper:

```text
[1, 6]
  [2, 5]
    [3, 4]
```

Lower:

```text
[2, 6]
  [3, 5]
```

### `structure_profile(...)`

```python
{
    "valid": True,
    "reason": None,
    "upper_interval_count": 3,
    "lower_interval_count": 2,
    "total_interval_count": 5,
    "upper_root_count": 1,
    "lower_root_count": 1,
    "upper_nesting_count": 2,
    "lower_nesting_count": 1,
    "nesting_count": 3,
    "nesting_density": 0.6,
    "upper_max_depth": 2,
    "lower_max_depth": 1,
    "max_depth": 2,
    "category": "medium_nesting_valid",
}
```

### `simplified_jordan_sort(...)` excerpt

```python
{
    "valid": True,
    "reason": None,
    "families": {
        "upper": {"roots": [0], ...},
        "lower": {"roots": [0], ...},
    },
    "stats": {
        "nesting_count": 3,
        "max_depth": 2,
        "category": "medium_nesting_valid",
    },
}
```

## Invalid Crossing Example

`seq = [1, 3, 2, 4]`

### Oracle

```python
{
    "valid": False,
    "sorted": [1, 2, 3, 4],
    "distinct_values": True,
    "upper_ok": False,
    "lower_ok": True,
    "reason": "upper crossing",
}
```

### Family Tree / Profile

`family trees` are not built for invalid cases.  
`structure_profile(...)` returns invalid category.

### `simplified_jordan_sort(...)` excerpt

```python
{
    "valid": False,
    "reason": "upper crossing",
    "families": None,
    "stats": {
        "valid": False,
        "reason": "upper crossing",
        "category": "invalid",
    },
    "backend": {
        "name": "ordinary_list",
        "uses_oracle_sorted_output": True,
        "linear_time_claim": False,
    },
    "trace": [
        "copy_input",
        "oracle",
        "structure_profile",
        "reject_invalid_input",
    ],
}
```

## Mapping to Terms in `notation.md`

- `upper / lower`: two interval families generated from pair offsets.
- `rank`: order position in sorted values.
- `rank interval`: mapped from a pair `(x_i, x_j)` via rank endpoints.
- `family tree`: containment hierarchy from rank intervals.
- `crossing / nesting`: reflected in validation and `structure_profile["category"]`.
- `strict_flat`: no nesting, no parent pointers.
