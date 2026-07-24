# Final Experiment Specification

Last updated: 2026-07-24

## Status

This document freezes the experiment questions, variables, correctness criteria,
and aggregation rules for the next formal experiment stage.

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

