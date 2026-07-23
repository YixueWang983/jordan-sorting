# Experimental Questions and Metrics

Last updated: 2026-07-23

## Purpose

This document fixes the Week 7 experimental questions and maps each metric to a
specific role. The goal is to avoid measuring values simply because they are easy
to compute.

## Hypotheses

### H1: Correctness

For oracle-valid inputs, `simplified_jordan_reference` should return the same
sorted sequence as ordinary Python sorting.

Metric mapping:

```text
sorted_correct -> H1
oracle_valid   -> H1 input class
error          -> H1 failure diagnosis
```

### H2: Structure Sensitivity

For fixed `n`, more containment and deeper family trees should be visible in
diagnostic operation counts.

Metric mapping:

```text
max_depth                  -> H2 structural variable
parented_interval_ratio    -> H2 legacy-compatible nesting signal
containment_pair_count     -> H2 structural containment count
containment_pair_density   -> H2 normalized containment signal
containment_checks         -> H2 implementation cost signal
nodes_visited              -> H2 tree traversal signal
```

### H3: Cost Decomposition

The reference pipeline's additional work should mainly come from validation and
family-tree construction rather than final sorted-output extraction.

Metric mapping:

```text
upper_pair_checks/lower_pair_checks -> validation cost
containment_checks                  -> family-tree construction cost
trace_event_count                   -> process description, not primary cost
median_time_ns                      -> timing observation
iqr_time_ns                         -> timing stability
```

## Structural Metrics

### Legacy Nesting Density

`nesting_density` is kept for backward compatibility. Its current meaning is:

```text
nesting_density = parented intervals / total intervals
```

This field does not count all interval-containment pairs. It should be treated as
a legacy alias for the newer, clearer `parented_interval_ratio`.

### Parented Interval Ratio

```text
parented_interval_ratio = parented_interval_count / total_interval_count
```

This measures the share of intervals that have a parent in their family tree.

### Containment Pair Count

For one interval family, a containment pair is an unordered interval pair
`(outer, inner)` where:

```text
outer.left < inner.left and inner.right < outer.right
```

The combined count is:

```text
containment_pair_count =
    upper_containment_pair_count + lower_containment_pair_count
```

### Containment Pair Density

Let `m_u` be the number of upper intervals and `m_l` the number of lower
intervals.

```text
containment_pair_density =
    containment_pair_count / (C(m_u, 2) + C(m_l, 2))
```

If the denominator is zero, the density is defined as `0.0`.

### Crossing Pair Counts

For invalid candidates, crossing severity is measured by:

```text
upper_crossing_pair_count
lower_crossing_pair_count
total_crossing_pair_count
```

These counts are diagnostic metrics. They do not replace the oracle validity
decision.

## Timing Protocol Variables

Independent variables:

```text
family
n
case_id
algorithm
```

Dependent variables:

```text
median_time_ns
q1_time_ns
q3_time_ns
iqr_time_ns
mean_time_ns
stdev_time_ns
```

Correctness metrics:

```text
sorted_correct
error
oracle_valid
```

Diagnostic metrics:

```text
containment_pair_density
max_depth
total_crossing_pair_count
instrumentation counters
```

## Interpretation Boundaries

The current implementation is a correctness-oriented reference pipeline. Timing
and operation counters can describe this implementation, but they do not prove
the theoretical linear-time Jordan-sorting bound.

