# Week 7 Plan

Last updated: 2026-07-23

## Week 7 Goal

Week 7 is an experiment-design hardening week. It does not extend the
Jordan-sorting algorithm and does not run final thesis-scale experiments.

The goal is to turn the existing reference pipeline into a stronger experimental
object by clarifying:

- why each dataset family is measured,
- which structural properties are actually covered,
- how nesting and crossing metrics are defined,
- which operation counters better approximate cost than trace length,
- and how pilot timing should be measured before final experiments.

## Research Questions for This Week

### H1: Correctness

For oracle-valid inputs, the reference pipeline should return the same sorted
output as ordinary Python sorting.

Comparison:

```text
simplified_jordan_reference output
vs.
Python sorted output
```

### H2: Structure Sensitivity

For fixed input size `n`, different containment density and maximum family-tree
depth should correspond to different diagnostic operation counts, such as
containment checks and node visits.

Comparison:

```text
flat_valid
vs.
nested_valid
vs.
incremental_valid
```

### H3: Cost Decomposition

The reference pipeline's main extra cost should come from validation and
family-tree construction, not from the final sorted-output extraction.

Comparison:

```text
python_sort
sort_plus_laminarity_check
simplified_jordan_reference
```

## Metric Groups

Independent variables:

- generator family,
- sequence length `n`,
- validity class,
- structural category.

Dependent variables:

- median runtime,
- timing IQR,
- operation counters,
- family-tree depth,
- containment density,
- crossing severity.

Correctness metrics:

- `sorted_correct`,
- `oracle_valid`,
- `error`.

Diagnostic metrics:

- `parented_interval_ratio`,
- `containment_pair_count`,
- `containment_pair_density`,
- `upper_crossing_pair_count`,
- `lower_crossing_pair_count`,
- `total_crossing_pair_count`,
- instrumentation counters from oracle and family-tree construction.

## Day 1: Experimental Questions and Metrics

Outputs:

- `docs/plan/week7_plan.md`
- `docs/design/experimental_questions_and_metrics.md`

Completion criteria:

- each metric maps to a research question,
- independent/dependent/correctness/diagnostic variables are separated,
- trace length is explicitly not treated as the primary cost metric.

## Day 2: Structural Metric Semantics

Outputs:

- updated `src/stats.py`
- updated `tests/test_stats.py`
- updated notation/metric documentation

Tasks:

- keep `nesting_density` as a legacy field,
- define `parented_interval_ratio`,
- add containment pair counts and density,
- add crossing pair counts for invalid inputs.

Completion criteria:

- legacy field semantics are unchanged,
- new metric definitions are mathematically documented,
- flat, nested, mixed, invalid, empty, and singleton cases are tested.

## Day 3: Operation Counters

Outputs:

- `src/instrumentation.py`
- `tests/test_instrumentation.py`

Tasks:

- add optional `metrics=None` to oracle/family-tree internals,
- keep default behavior unchanged,
- add an experiment-only `instrumented_reference_run(seq)` wrapper.

Completion criteria:

- counters are deterministic on small cases,
- instrumentation does not change validity or sorted output,
- no linear-time claim is introduced.

## Day 4: Benchmark Protocol and Pilot Runner

Outputs:

- `docs/design/benchmark_protocol.md`
- `experiments/run_week7_pilot.py`
- `tests/test_run_week7_pilot.py`

Timing protocol:

- warm-up runs: `5`,
- measured runs: `20`,
- primary statistic: median,
- variability: Q1, Q3, IQR,
- supplementary: mean and standard deviation,
- no JSON I/O inside timed regions,
- fresh list copy for each timed call,
- GC disabled only during timed execution,
- fixed base seed,
- case-level aggregation before group-level aggregation.

## Day 5: Generator Coverage Audit

Outputs:

- `experiments/audit_generator_coverage.py`
- `tests/test_generator_coverage_audit.py`

The audit does not time algorithms. It measures data quality and structural
coverage.

## Day 6: Pilot Experiment

Outputs:

- `results/week7_pilot_raw.csv`
- `results/week7_pilot_case_summary.csv`
- `results/week7_pilot_group_summary.csv`
- `results/week7_environment.json`
- `docs/analysis/week7_pilot_interpretation.md`

Pilot statements must use cautious language:

```text
observed
suggests
in this pilot
```

They must avoid:

```text
proves
linear complexity
representative of all Jordan sequences
```

## Day 7: Review and Handoff

Outputs:

- `docs/progress/week7_progress.md`
- `docs/progress/week7_summary.md`
- updated README/docs/results indexes

Completion criteria:

- all tests pass,
- Week 1 and Week 4 output semantics remain unchanged,
- generator coverage is measured from actual generated data,
- pilot timing uses warm-up, median, IQR, and case-level aggregation,
- Week 8 next steps are based on measured gaps rather than family names alone.

