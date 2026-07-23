# Week 7 Pilot Interpretation

This pilot is a controlled engineering observation, not a final performance claim.

## Configuration

- Families: flat_valid, nested_valid, invalid_upper_crossing, invalid_lower_crossing, incremental_valid, random_invalid, mutation_based_invalid
- Sizes: [32, 64, 128]
- Algorithms: python_sort, simplified_jordan_reference, sort_plus_laminarity_check
- Warm-up runs: 1
- Measured runs: 5

## Initial Observations

- The pilot records correctness, timing, structural metrics, and operation counters together.
- The pilot suggests that future analysis should compare runtime against containment density and max depth at the case-summary level.
- The pilot keeps `simplified_jordan_reference` as a reference pipeline using oracle-sorted output.
- In this pilot, valid flat, nested, and incremental cases with the same `n`
  show different `containment_pair_density` and `max_depth` values, but the
  current ordinary family-tree builder still performs a deterministic quadratic
  candidate scan. This suggests that the present implementation is useful for
  exposing structural differences, while not yet exploiting them algorithmically.
- In this pilot, `random_invalid` tends to have much larger crossing severity
  than the fixed upper/lower crossing families. This supports treating
  `random_invalid` as a high-entropy invalid stress family rather than as a
  localized near-valid invalid family.
- In this pilot, `mutation_based_invalid` shows variable crossing severity. This
  suggests that swap mutation does not automatically guarantee a single-local
  crossing and should be audited before being described as near-valid.
- The timing observations should be interpreted through case summaries and IQR,
  not by mixing all raw rows from different generated cases into one homogeneous
  sample.

## Boundaries

- This pilot does not prove linear complexity.
- This pilot is not representative of all Jordan sequences.
- This pilot does not implement level-linked search trees or heterogeneous finger trees.
