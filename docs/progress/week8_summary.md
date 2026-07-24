# Week 8 Summary

Last updated: 2026-07-24

## Goal

Week 8 froze the current thesis scope, experiment specification, output schema,
and formal-experiment preparation workflow.

This week deliberately did not run final thesis-scale experiments and did not
expand the reference skeleton into a claimed linear-time Jordan-sorting
implementation.

## Completed Work

### Scope Freeze

Added:

```text
docs/design/final_scope_and_contributions.md
docs/design/theory_to_implementation_mapping.md
```

These documents separate:

- implemented reference-framework contributions;
- non-contributions;
- theoretical Jordan-sorting concepts that are discussed but not implemented;
- supervisor confirmation questions.

### Experiment Specification Freeze

Added:

```text
docs/design/final_experiment_spec.md
```

The experiment specification freezes:

- RQ/H mapping;
- independent variables;
- dependent variables;
- correctness fields;
- aggregation rules;
- CSV semantics;
- non-linear-time boundaries.

### Benchmark Runner Hardening

Updated:

```text
experiments/run_week7_pilot.py
```

The runner now supports:

- configurable algorithm lists;
- randomized block scheduling per measured round;
- fresh input copies before timing starts;
- stricter CLI/config validation;
- default no-overwrite run directories under `results/runs/<run_id>/`;
- enhanced `environment.json`;
- generated `config.json`;
- generated `manifest.json` with file hashes.

Added:

```text
experiments/validate_experiment_outputs.py
```

The validator checks expected files, CSV schemas, row counts, correctness fields,
error counts, density ranges, per-round algorithm coverage, and manifest row
counts.

### Generator Coverage Audit v2

Updated:

```text
experiments/audit_generator_coverage.py
```

The audit now includes:

- odd/even boundary default sizes;
- generation metadata for incremental-valid cases;
- rejection-sampling metadata for random-invalid cases;
- base hash and swap metadata for mutation-based invalid cases;
- duplicate generated-case summary rows;
- clearer distinction between `has_duplicate_values` and duplicate generated
  cases.

### Thesis Drafts

Added:

```text
docs/thesis/experimental_methodology_draft.md
docs/thesis/implementation_draft.md
```

These drafts are thesis-facing starting points, not final chapters.

## Dry Runs

### Dry Run A: Generator Coverage / Parity

Command:

```bash
python experiments/audit_generator_coverage.py \
  --sizes 31 32 33 63 64 65 \
  --randomized-repetitions 3 \
  --output-csv results/runs/week8_generator_audit_dry_run/coverage_audit.csv \
  --summary-csv results/runs/week8_generator_audit_dry_run/coverage_summary.csv
```

Result:

```text
78 audit rows
42 summary rows
```

The generated CSV files are local reproducible artifacts and are not committed
by default.

### Dry Run B: Timing Feasibility

Command:

```bash
python experiments/run_week7_pilot.py \
  --run-id week8_timing_dry_run \
  --overwrite \
  --sizes 64 128 256 \
  --randomized-cases 2 \
  --warmup-runs 2 \
  --measured-runs 7 \
  --algorithms python_sort sort_plus_laminarity_check simplified_jordan_reference
```

Result:

```text
630 raw rows
90 case-summary rows
63 group-summary rows
```

Validation:

```bash
python experiments/validate_experiment_outputs.py \
  --run-dir results/runs/week8_timing_dry_run
```

Validator result:

```text
valid: true
errors: []
```

The dry run confirms that the formal-experiment pipeline can generate,
summarize, manifest, and validate benchmark outputs end to end.

## Frozen Boundaries

The current implementation still does not claim:

- level-linked search trees;
- heterogeneous finger trees;
- dynamic split/update operations;
- polygon clipping;
- theoretical linear-time performance;
- sorted-output recovery from theoretical Jordan-sorting operations.

`simplified_jordan_reference` remains an ordinary-list, correctness-oriented
reference pipeline. Its sorted output still comes from `oracle_result["sorted"]`.

## Week 9 Gate

Week 9 may start formal experiments if:

1. the full unit-test suite passes;
2. `git diff --check` passes;
3. dry-run validation remains clean;
4. no core CSV semantic changes are introduced without updating
   `docs/design/final_experiment_spec.md`;
5. generated result CSVs are either committed intentionally or explicitly marked
   as reproducible local artifacts.

