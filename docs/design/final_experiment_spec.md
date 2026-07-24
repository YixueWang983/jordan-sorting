# Final Experiment Specification

Last updated: 2026-07-24

## Status

This document freezes the experiment questions, variables, correctness criteria,
and aggregation rules for the next formal experiment stage.

The formal scope is proposed and frozen for implementation purposes, pending
supervisor confirmation of the reference-framework boundary.

## Research Questions

### RQ1 / H1: Correctness

Does each compared implementation return the expected sorted output, validity
decision, and invalid reason where applicable?

Metrics:

```text
output_correct
validity_correct
reason_correct
overall_correct
error_count
```

### RQ2 / H2a: Structural Coverage

What structures do the generator families actually produce?

Metrics:

```text
family
n
structural_category
max_depth
parented_interval_ratio
containment_pair_density
crossing_pair_density
```

Generator family names are not treated as proof of structure. Structure is
measured after generation.

### RQ3 / H2b: Ordinary-Backend Sensitivity

For fixed `n`, does the ordinary-list backend exploit structural differences?

Metrics:

```text
containment_checks
laminar_pair_checks
nodes_visited
trace_event_count
```

If containment checks are mostly fixed by `n`, that is a valid negative result:
the current ordinary-list implementation exposes structures but does not exploit
them algorithmically.

### RQ4 / H3: Cost Decomposition

How much overhead comes from validation and reference-pipeline work compared with
ordinary sorting?

Compared algorithms:

```text
python_sort
sort_plus_laminarity_check
simplified_jordan_reference
```

Important boundary:

`simplified_jordan_reference` includes engineering costs such as validation,
family-tree construction, structural stats, trace construction, and serializable
output. It is not a theoretical linear-time implementation.

## Independent Variables

```text
algorithm
family
n
case_id
validity class
max_depth
containment_pair_density
crossing_pair_density
```

## Dependent Variables

```text
runtime
operation counters
correctness fields
error count
```

## Aggregation

Formal timing uses:

```text
primary statistic: median
variability: Q1, Q3, IQR
supplementary: mean, standard deviation
raw run -> case summary -> family/n/algorithm group summary
```

Rules:

- deterministic families have one input case per `n`;
- randomized families support case-to-case variation analysis;
- timing runs are not independent generated cases;
- correlations are exploratory;
- p-values are not part of the initial experiment plan;
- runtime does not prove theoretical complexity;
- operation counts are better for explaining ordinary-list scan behavior.

## Frozen Formal Configuration

### Coverage Experiment

Purpose:

```text
audit generator structural coverage and invalid-reason distribution
```

Configuration:

```text
sizes:
31, 32, 33,
63, 64, 65,
127, 128, 129,
255, 256, 257

families:
flat_valid
nested_valid
incremental_valid
invalid_upper_crossing
invalid_lower_crossing
random_invalid
mutation_based_invalid

deterministic repetitions:
1

randomized repetitions:
30

seed:
20260723
```

Expected row counts:

```text
coverage audit rows:
12 sizes x (4 deterministic families x 1 + 3 randomized families x 30)
= 1128 rows

coverage summary rows:
12 sizes x 7 families = 84 rows
```

### Performance Experiment

Purpose:

```text
compare ordinary sorting, validation-plus-sort, and the ordinary-list reference
pipeline under a fixed correctness and structural-observability protocol
```

Configuration:

```text
sizes:
64, 128, 256, 512, 1024

families:
flat_valid
nested_valid
incremental_valid
invalid_upper_crossing
invalid_lower_crossing
random_invalid
mutation_based_invalid

deterministic cases:
1 per family/size

randomized cases:
5 per family/size

warm-up runs:
5

measured runs:
20

seed:
20260723

algorithm-order seed:
20268642

case-order seed:
20262266

algorithms:
python_sort
sort_plus_laminarity_check
simplified_jordan_reference
```

Expected row counts:

```text
cases:
5 sizes x (4 deterministic families x 1 + 3 randomized families x 5)
= 95 cases

raw timing rows:
95 cases x 3 algorithms x 20 measured runs
= 5700 rows

case-summary rows:
95 cases x 3 algorithms
= 285 rows

group-summary rows:
7 families x 5 sizes x 3 algorithms
= 105 rows
```

Formal run id:

```text
week9_formal_reference
```

Default output directory:

```text
results/runs/week9_formal_reference/
```

### Formal Machine

The formal machine is the same local development machine unless explicitly
changed before Week 9. The actual machine metadata must be recorded in
`environment.json`; the thesis should cite the recorded environment rather than
memory.

## Failure and Fallback Rules

1. If any raw row has `error != ""`, the formal run fails.
2. If any applicable correctness field is false, the formal run fails.
3. If `validate_experiment_outputs.py` returns `valid=false`, the formal run
   fails.
4. Validator checks include manifest SHA-256 verification and raw-to-summary
   recomputation; a summary CSV is not accepted merely because it exists.
5. If a run fails, keep its run directory for debugging and rerun with a new
   `run_id`; do not overwrite failed evidence.
6. If formal runtime is too high, reduce maximum size only after documenting the
   change in this file and in the Week 9 summary.
7. Generated CSVs may remain uncommitted only if the manifest hash and
   reproduction command are recorded.

## Frozen CSV Semantics

Final runners should keep these meanings stable:

```text
time_ns                     measured algorithm runtime only
output_correct              sorted output equals oracle sorted output
validity_correct            reported validity matches oracle when applicable
reason_correct              reported reason matches oracle when applicable
overall_correct             all applicable correctness checks passed
containment_pair_density    containment-pair density, not legacy nesting ratio
parented_interval_ratio     parented intervals / total intervals
```
