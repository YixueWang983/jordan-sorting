# Week 8 Plan

Last updated: 2026-07-24

## Week 8 Goal

Week 8 is the scope-freeze, experiment-specification-freeze, and final
experiment preparation week.

This week does not run the final experiment and does not expand the algorithm
without boundaries. The goal is to make Week 9 safe: once final experiments
start, metric definitions, generator audit fields, benchmark protocol, output
schema, and thesis positioning should not need disruptive changes.

## Required Outcomes

1. Prepare a proposed thesis contribution and implementation-boundary freeze
   pending supervisor confirmation.
2. Map theoretical Jordan-sorting concepts to current code and missing pieces.
3. Harden the benchmark runner for dry runs and future formal experiments.
4. Upgrade generator coverage audit with parity, metadata, hashes, and duplicate
   case analysis.
5. Produce dry-run outputs and thesis-methodology drafts.

## Day 1: Final Scope and Success Criteria

Output:

- `docs/design/final_scope_and_contributions.md`

Completion criteria:

- thesis contributions are stated in a few clear proposed claims;
- non-contributions are explicit;
- success is not defined as implementing full linear-time Jordan sorting;
- supervisor confirmation questions are listed.

## Day 2: Theory-to-Code Mapping

Output:

- `docs/design/theory_to_implementation_mapping.md`

Completion criteria:

- each theory concept maps to code or is marked not implemented;
- oracle/recognition/sorting are separated;
- 1986/1990 algorithm boundaries and polygon-clipping relationship are stated.

## Day 3: Benchmark Runner Hardening

Outputs:

- hardened `experiments/run_week7_pilot.py`;
- `experiments/validate_experiment_outputs.py`;
- tests for scheduling, validation, no-overwrite behavior, and failed timing
  groups.

Requirements:

- randomized block scheduling per measured round;
- randomized case execution order;
- fresh input copied before timing;
- enhanced environment manifest;
- CLI validation for sizes, runs, families, algorithms, and output paths;
- default output directory `results/runs/<run_id>/`;
- no silent overwrite of existing run directories;
- output validation script.
- manifest SHA-256 validation for generated files.

## Day 4: Generator Coverage Audit v2

Output:

- upgraded `experiments/audit_generator_coverage.py`

Requirements:

- parity sizes: `31,32,33,63,64,65,127,128,129,255,256,257`;
- generation metadata for incremental, random invalid, and mutation invalid
  families;
- duplicate generated-case analysis via `sequence_hash`;
- audit run config and manifest files;
- distinction between `has_duplicate_values` and duplicate generated cases.

## Day 5: Final Experiment Specification

Output:

- `docs/design/final_experiment_spec.md`

Completion criteria:

- RQ/H mapping is frozen;
- independent and dependent variables are frozen;
- aggregation rules are frozen;
- limitations and non-claims are explicit.

## Day 6: Week 8 Dry Runs

Dry Run A: coverage/parity

```text
sizes = [31, 32, 33, 63, 64, 65]
randomized_cases = 3
```

Dry Run B: timing feasibility

```text
sizes = [64, 128, 256]
randomized_cases = 2
warmup_runs = 2
measured_runs = 7
```

Completion criteria:

- output validator passes;
- error count is zero;
- correctness checks pass;
- density values are in `[0, 1]`;
- duplicate generated cases are reported;
- runtime feasibility for Week 9 is estimated.

## Day 7: Writing, Review, and Week 9 Gate

Outputs:

- `docs/thesis/experimental_methodology_draft.md`
- `docs/thesis/implementation_draft.md`
- `docs/progress/week8_summary.md`

Completion criteria:

- Week 9 can start final experiments without changing core CSV schema or metric
  definitions.
