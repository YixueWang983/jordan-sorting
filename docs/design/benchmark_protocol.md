# Benchmark Protocol

Last updated: 2026-07-23

## Purpose

Week 7 pilot timing is not a final performance experiment. It is a controlled
pilot used to check whether the reference pipeline, structural metrics, and
operation counters are ready for thesis-scale analysis.

## Timing Rules

- Use `time.perf_counter_ns()`.
- Generate test cases outside the timed region.
- Do not include JSON I/O in timed regions.
- Pass a fresh list copy to every timed function call.
- Disable GC only during the timed function call.
- Run warm-up calls before measured calls.
- Record raw measured calls, then summarize by case before summarizing by group.
- Time the plain algorithm implementation. Diagnostic operation counters are
  collected once per case outside the timed region so counter overhead is not
  mixed into runtime measurements.

Default protocol:

```text
warmup_runs = 5
measured_runs = 20
primary_statistic = median
variability = Q1, Q3, IQR
supplementary = mean, standard deviation
```

## Algorithms

Week 7 pilot keeps only algorithms tied directly to the current research
questions:

```text
python_sort
sort_plus_laminarity_check
simplified_jordan_reference
```

`merge_sort` and `quick_sort` remain useful transparent baselines, but they do
not directly isolate validation or reference-pipeline overhead.

## Aggregation

Raw rows are grouped in two stages:

1. `(case_id, algorithm)` case summary;
2. `(family, n, algorithm)` group summary over case medians.

This avoids treating different generated cases as identical runtime samples.

## Interpretation Rules

Allowed wording:

```text
observed
suggests
in this pilot
```

Avoid:

```text
proves
linear complexity
representative of all Jordan sequences
```

The current implementation is a correctness-oriented reference pipeline using an
ordinary-list backend and oracle-sorted output. Pilot timing does not prove a
linear-time Jordan-sorting implementation.

## Correctness Fields

Week 7 pilot rows distinguish several checks:

```text
output_correct
validity_correct
reason_correct
overall_correct
```

`sorted_correct` is retained as a backward-compatible alias for output
correctness. Invalid inputs should not be judged only by sorted-output equality;
validity and reason checks are recorded for algorithms that expose them.
