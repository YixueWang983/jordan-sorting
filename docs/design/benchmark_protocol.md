# Benchmark Protocol

Last updated: 2026-07-28

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
If every measured run for a case fails, the case summary keeps an empty timing
statistic and a positive `error_count`. The group summary must still emit a row
with empty timing aggregates instead of crashing.

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

The `simplified_jordan_reference` implementation is an oracle-backed reference
pipeline. The separately named `simplified_jordan_paper_ordinary_list`
implementation recovers output from its maintained partial order. Neither
ordinary-list timing nor oracle-backed reference timing proves a linear-time
Jordan-sorting implementation.

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

## Paper-Algorithm Timing Boundary

Week 11 paper timing uses:

```text
execution_mode = minimal
```

Before timing each exact sequence:

1. generate the sequence;
2. certify it with the oracle;
3. compute structural metadata;
4. run one complete checked paper diagnostic;
5. retain the checked diagnostic counters outside timing.

Inside the paper timed region:

```text
paper_jordan_sort_valid(sequence, execution_mode="minimal")
```

The timed region excludes:

```text
oracle certification
structure_profile
complete checked diagnostics
deterministic replay
complete backend validate_invariants()
trace recording
diagnostic counter updates
CSV/JSON/hash work
```

The timed region includes:

```text
input materialization performed by the public sorter
Step 1/2/3 control flow
ordinary-list backend operations
local safety checks and rollback
stage_results
partial-order output recovery
```

GC is disabled only around the timed function call and restored immediately
afterward. Output is compared with the precomputed oracle result after timing.

## Frozen Week 11 Pilot

The authoritative configuration is validated by:

```bash
python experiments/week11_experiment_gate.py
```

It fixes:

```text
sizes = 32, 64, 128, 256, 512
families = flat_valid, nested_valid, incremental_valid
randomized incremental cases = 5
warm-up runs = 3
measured runs = 10
paper mode = minimal
audit mode = checked
seed = 20260723
algorithm-order seed = 20268642
case-order seed = 20262266
expected raw rows = 1050
```

The gate is frozen but not executed during Week 10. Week 11 must implement the
dedicated runner and validator without changing these values. Any necessary
change requires a documented new gate version and run ID; existing evidence
must not be overwritten.
