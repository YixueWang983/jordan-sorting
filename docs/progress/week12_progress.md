# Week 12 Progress

Last updated: 2026-08-05

## Goal

Implement, review, execute once, archive, and analyze the frozen Week 12
formal valid-input sorting experiment without changing the paper algorithm or
mixing recognition into sorting.

Plan:

```text
docs/plan/week12_plan.md
```

## Frozen Contract

```text
protocol:          week12_formal_sorting_v1
gate status at freeze: frozen_not_executed
cases:             60
raw rows:          3,600
case summaries:    180
group summaries:   45
case audits:       60
paper timing:      minimal
paper audit:       checked, outside timing
recognition:       separate
```

## Checkpoint 1: Formal Execution Before Review

Status: approved and complete.

- [x] added the corrected three-checkpoint Week 12 plan;
- [x] derived an immutable execution config from the frozen gate;
- [x] kept all protocol variables out of the CLI;
- [x] kept both CLI and public Python formal execution disabled;
- [x] added reusable formal Git/environment/readiness and exclusive-write
  support without modifying Week 11 run003;
- [x] extracted shared fail-closed parsing and summary recomputation into a
  neutral validator-support module used by Week 11 and Week 12;
- [x] made `config.json` archive the complete `gate_to_dict()` record;
- [x] kept execution identity and anonymous environment in `environment.json`;
- [x] implemented deterministic 60-case generation and seed rules;
- [x] reject duplicate, oracle-invalid, or non-distinct cases before timing;
- [x] call `paper_jordan_diagnostics_valid(sequence)` without an unsupported
  mode argument;
- [x] require all checked audits before any warm-up or measured call;
- [x] reuse reviewed Week 11 timing, GC, scheduling, and summary functions;
- [x] define the 3,600 / 180 / 45 / 60 evidence contract;
- [x] record pipeline wall-clock scope separately from measured-call total;
- [x] start the pipeline clock before formal evidence-directory reservation;
- [x] reject elapsed times shorter than the measured-call total;
- [x] cross-check monotonic elapsed time against UTC timestamps with a bounded
  tolerance;
- [x] record validator wall-clock in validation reports;
- [x] implement an independent fail-closed Week 12 validator;
- [x] regenerate cases, oracle results, profiles, and diagnostics in validation;
- [x] recompute schedules, summaries, measured totals, and hashes;
- [x] require later independent validation reports outside the archive;
- [x] add a full 3,600-row synthetic corruption matrix in temporary directories;
- [x] make preflight report the actual frozen formal-execution switch;
- [x] run 23 focused Week 12 tests;
- [x] run all 529 unit tests;
- [x] pass `compileall` and `git diff --check`;
- [x] reproduce 2,074 exhaustive valid permutations and 48 fixed generated
  cases;
- [x] revalidate Week 9 sorting and recognition evidence;
- [x] revalidate Week 10 contamination evidence;
- [x] revalidate immutable Week 11 run003 evidence after extracting shared
  validation support;
- [x] complete the post-commit commit check;
- [x] push Checkpoint 1 for review;

Current implementation:

```text
experiments/experiment_validation_support.py
experiments/formal_execution_support.py
experiments/run_week12_formal_sorting.py
experiments/validate_week12_formal_sorting_outputs.py
tests/test_run_week12_formal_sorting.py
tests/test_validate_week12_formal_sorting_outputs.py
```

Verification so far:

```text
focused Week 12 tests:
    Ran 23 tests
    OK

full suite:
    Ran 529 tests
    OK

compileall:
    passed

exhaustive/generated algorithm validation:
    2,074 / 48
    all valid = true

historical validators:
    Week 9 sorting = valid
    Week 9 recognition = valid
    Week 10 contamination = valid
    Week 11 run003 = valid

git diff --check:
    passed

formal execution state:
    enabled only for source commit 98868b1
    disabled again after validated evidence archival

formal run001 directory:
    created once after Checkpoint 1 approval
```

## Checkpoint 2: Formal Evidence

Status: complete. The immutable run is archived for review.

- [x] pass Checkpoint 1 review;
- [x] enable only the reviewed formal entry in source commit `98868b1`;
- [x] execute `week12_formal_sorting_v1__run001` exactly once;
- [x] obtain 3,600 / 180 / 45 / 60 rows;
- [x] obtain built-in `valid=true`;
- [x] rerun independent validation to `docs/analysis/`;
- [x] verify zero errors, incorrect outputs, and failed audits;
- [x] archive immutable evidence;
- [x] retire run001 permanently after success.
- [x] disable the public formal execution entry after archival.

Execution record:

```text
execution ID:             week12_formal_sorting_v1__run001
source commit:            98868b1b705f6d5f22404ee8ad7b88ad7a834f52
environment quality:      clean
environment warnings:     none
experiment elapsed:       837,682,385,541 ns
measured-call total:      17,369,623,904 ns
built-in validation:      valid = true
independent validation:   valid = true
raw errors:               0
incorrect outputs:        0
failed audits:            0
manifest SHA-256:         f42ab0b77cb7ea91ed66c66bc6947a81cd8746b5d2b67d526472260d2b47f850
```

Immutable evidence:

```text
results/runs/week12_formal_sorting_v1__run001/
```

Independent report:

```text
docs/analysis/week12_formal_sorting_run001_independent_validation.json
```

## Checkpoint 3: Formal Analysis

Status: not started.

- [ ] live-validate archived evidence before analysis;
- [ ] generate `week12_...` CSV and SVG outputs outside the archive;
- [ ] report size and family results without pooling incompatible scopes;
- [ ] compare Week 11 and Week 12 trends without pooling absolute timings;
- [ ] document ordinary-list observations and all non-claims;
- [ ] add `docs/progress/week12_summary.md`;
- [ ] freeze the Week 13 handoff.

## Current Boundary

Week 12 run001 has completed exactly once and is retired. Its archived evidence
must be treated as immutable and must not be rerun or overwritten. Checkpoint 3
may read and live-validate the archive, but formal timing must not run again.
