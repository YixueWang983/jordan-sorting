# Week 7 Pilot Auto Report

This pilot is a controlled engineering observation, not a final performance claim.

## Configuration

- Families: flat_valid, nested_valid, invalid_upper_crossing, invalid_lower_crossing, incremental_valid, random_invalid, mutation_based_invalid
- Sizes: [32, 64, 128]
- Algorithms: python_sort, simplified_jordan_reference, sort_plus_laminarity_check
- Warm-up runs: 1
- Measured runs: 5

## Initial Observations

- The pilot records correctness, timing, structural metrics, and selected operation counters together.
- The pilot suggests that future analysis should compare runtime against containment density and max depth at the case-summary level.
- The pilot times plain `simplified_jordan_reference`; diagnostic counters are collected once per case outside the timed region.

## Boundaries

- This pilot does not prove linear complexity.
- This pilot is not representative of all Jordan sequences.
- This pilot does not implement level-linked search trees or heterogeneous finger trees.
