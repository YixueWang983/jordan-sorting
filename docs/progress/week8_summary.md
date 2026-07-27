# Week 8 Summary

Last updated: 2026-07-24

## Goal

Week 8 froze the thesis scope, froze the experiment specification, and prepared
the formal-experiment workflow.

The supervisor confirmed the reference-framework boundary on 2026-07-24, so the
formal experiments can be treated as thesis evidence if the technical validation
gate remains clean.

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
- supervisor decision record.

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
  --run-id week8_generator_audit_dry_run \
  --overwrite \
  --sizes 31 32 33 63 64 65 \
  --randomized-repetitions 3
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

## Post-Review Fixes

After the first Week 8 review, the experiment gate was tightened further:

- `validate_experiment_outputs.py` now verifies manifest SHA-256 values for
  generated files.
- The validator checks raw, case-summary, and group-summary row counts against
  the manifest.
- The validator checks `run_id` consistency across config, environment, and
  manifest files.
- The validator checks manifest/environment commit SHA consistency.
- Case and group summaries are recomputed from raw rows and compared with saved
  summary CSVs.
- The runner now records and randomizes case execution order via
  `case_order_seed` and `case_execution_position`.
- Generator audit output now includes `audit_config.json` and
  `audit_manifest.json`.
- Generator audit summaries include category, invalid-reason, depth, density,
  and fallback distributions.
- Timing validation now checks scheduling fields: `case_execution_position`,
  `run_index`, `measured_round`, and `algorithm_position`.
- Timing validation now rejects malformed summary numeric fields rather than
  crashing.
- Generator audit output now has a separate validator:
  `experiments/validate_generator_audit_outputs.py`.
- Results documentation now labels the old 2940-row setup as the historical
  Week 1 baseline and lists the frozen Week 9 formal configuration separately.

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
4. the supervisor-confirmed reference-framework boundary remains unchanged;
5. no core CSV semantic changes are introduced without updating
   `docs/design/final_experiment_spec.md`;
6. generated result CSVs are either committed intentionally or explicitly marked
   as reproducible local artifacts.

## Post-Week-8 Direction Revision

On 2026-07-27, the post-Week-8 plan was revised to align the implementation
deliverable with the thesis title. Week 9 no longer starts with the formal
performance experiment. It starts with an executable specification and
ordinary-list reconstruction of the 1990 paper algorithm.

The historical Week 8 dry-run and technical gate remain valid evidence about the
experiment infrastructure. The new algorithm and experiment gates are defined
in:

```text
docs/plan/refined_thesis_direction_after_week8.md
```
