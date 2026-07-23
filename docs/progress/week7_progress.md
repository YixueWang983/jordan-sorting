# Week 7 Progress

Last updated: 2026-07-23

## Day 1: Experimental Questions and Metrics

### Completed

- [x] Added `docs/plan/week7_plan.md`.
- [x] Added `docs/design/experimental_questions_and_metrics.md`.
- [x] Fixed three Week 7 hypotheses:
  - H1 correctness,
  - H2 structure sensitivity,
  - H3 cost decomposition.
- [x] Separated independent variables, dependent variables, correctness metrics,
  and diagnostic metrics.

## Day 2: Structural Metric Semantics

### Completed

- [x] Kept legacy `nesting_density` unchanged.
- [x] Added `parented_interval_ratio` as the clearer name for the legacy ratio.
- [x] Added containment metrics:
  - `upper_containment_pair_count`
  - `lower_containment_pair_count`
  - `containment_pair_count`
  - `containment_pair_density`
- [x] Added crossing severity metrics for invalid distinct-value candidates:
  - `upper_crossing_pair_count`
  - `lower_crossing_pair_count`
  - `total_crossing_pair_count`
- [x] Documented the metric definitions in `docs/design/notation.md`.

## Day 3: Operation Counters

### Completed

- [x] Added `src/instrumentation.py`.
- [x] Added `OperationMetrics`.
- [x] Added `instrumented_reference_run(seq)` as an experiment-only wrapper.
- [x] Added optional `metrics=None` support to oracle/family-tree internals while
  keeping default behavior unchanged.
- [x] Added deterministic counter tests.

## Day 4: Benchmark Protocol and Pilot Runner

### Completed

- [x] Added `docs/design/benchmark_protocol.md`.
- [x] Added `experiments/run_week7_pilot.py`.
- [x] Added `tests/test_run_week7_pilot.py`.
- [x] Pilot runner supports warm-up runs, measured runs, GC control, fresh list
  copies, case-level aggregation, group-level aggregation, and environment JSON.

## Day 5: Generator Coverage Audit

### Completed

- [x] Added `experiments/audit_generator_coverage.py`.
- [x] Added `tests/test_generator_coverage_audit.py`.
- [x] Ran default audit:

```text
python experiments/audit_generator_coverage.py
```

Result:

```text
results/week7_generator_coverage_audit.csv
376 rows
```

## Day 6: Pilot Experiment

### Completed

- [x] Ran a small Week 7 pilot:

```bash
python experiments/run_week7_pilot.py \
  --sizes 32 64 128 \
  --randomized-cases 2 \
  --warmup-runs 1 \
  --measured-runs 5
```

Result:

```text
results/week7_pilot_raw.csv: 450 rows
results/week7_pilot_case_summary.csv: 90 rows
results/week7_pilot_group_summary.csv: 63 rows
results/week7_environment.json
docs/analysis/week7_pilot_interpretation.md
```

All pilot raw rows had:

```text
error = ""
sorted_correct = True
```

## Day 7: Review and Handoff

### Completed

- [x] Ran full unit test suite:

```text
Ran 167 tests
OK
```

- [x] Confirmed Week 1 / Week 4 output semantics are not changed by the new Week
  7 scripts.
- [x] Prepared Week 7 summary and handoff boundaries.
