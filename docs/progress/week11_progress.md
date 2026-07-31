# Week 11 Progress

Last updated: 2026-07-31

## Goal

Implement, validate, execute, archive, and analyze one immutable paper
ordinary-list sorting integration pilot, then freeze the separate Week 12
formal gate without running it.

Plan:

```text
docs/plan/week11_plan.md
```

## Frozen Pilot

```text
gate:
    experiments/week11_experiment_gate_v2.py

run_id:
    week11_paper_sorting_pilot_v2_m4

status:
    frozen_not_executed

expected rows:
    raw = 1,050
    case summary = 105
    group summary = 45
```

Historical unexecuted gate:

```text
gate:
    experiments/week11_experiment_gate.py

run_id:
    week11_paper_sorting_pilot_v1

machine:
    MacBookAir10,1 / Apple M1
```

## Day 1: Plan, Baseline, and Machine Freeze

Status: complete.

- [x] fetched `origin/main`;
- [x] confirmed `HEAD == origin/main`;
- [x] confirmed a clean starting worktree;
- [x] recorded baseline commit `d6f9f2f`;
- [x] captured machine, OS, Python, architecture, clock, power, and load data;
- [x] documented Day 6 machine-use controls;
- [x] ran all 383 unit tests;
- [x] ran `compileall`;
- [x] validated the frozen Week 11 gate;
- [x] reproduced 2,074 exhaustive valid permutations through `n=8`;
- [x] reproduced all 48 fixed generated cases;
- [x] passed `git diff --check`;
- [x] confirmed the formal output directory is absent;
- [x] did not implement the runner;
- [x] did not execute timing.

Day 1 outputs:

```text
docs/plan/week11_plan.md
docs/progress/week11_progress.md
docs/analysis/week11_machine_preflight_v1_m1.md
```

## Day 1 Verification

```text
baseline commit:
    d6f9f2ffb2a4af49097a80b2b8cec7e6accbd5d0

python -m unittest discover -s tests:
    Ran 383 tests
    OK

python -m compileall -q src experiments tests:
    passed

python experiments/week11_experiment_gate.py:
    status = frozen_not_executed
    cases = 35
    expected rows = 1,050 / 105 / 45

python experiments/validate_paper_algorithm.py --max-n 8:
    exhaustive valid permutations = 2,074
    generated valid cases = 48
    all valid = true

results/runs/week11_paper_sorting_pilot_v1:
    absent

git diff --check:
    passed
```

## Day 2: Dedicated Runner Framework

Status: complete after review repair; formal execution remains disabled.

- [x] added `experiments/run_week11_pilot.py`;
- [x] added `tests/test_run_week11_pilot.py`;
- [x] imported and validated the exact frozen gate;
- [x] avoided redefining sizes, families, seeds, algorithms, modes, or row
  counts;
- [x] added the fixed run-directory and eight-file evidence contract;
- [x] rejected an existing run directory, including an empty one;
- [x] provided no `--overwrite` or mutable experiment CLI options;
- [x] exposed only `--preflight-only` as an operational option;
- [x] rejected ordinary execution until the Day 5 gate;
- [x] required a clean worktree and `HEAD == origin/main` in preflight;
- [x] queried the real remote `refs/heads/main` instead of trusting a stale
  local tracking ref;
- [x] required the machine-preflight document and structured machine baseline;
- [x] compared the current machine identity with the frozen Day 1 identity;
- [x] added atomic, exclusive config/environment prewrite behavior;
- [x] reread both JSON files and verified their exact content;
- [x] preserved partial initialization evidence after a write failure;
- [x] included machine model, architecture, OS/build, Python executable,
  available disk, and power/load command success without device identifiers;
- [x] kept preflight read-only and verified it creates no output directory;
- [x] kept generator, paper sorter, and timing calls out of the Day 2 module;
- [x] rejected modified gate objects;
- [x] added a two-clone stale-remote regression test;
- [x] added success, no-overwrite, partial-failure, ordering, and
  machine-mismatch evidence-initialization tests;
- [x] ran all 403 unit tests and `compileall`;
- [x] reproduced 2,074 exhaustive valid permutations and 48 generated cases;
- [x] confirmed the formal output directory remains absent.

Day 2 outputs:

```text
experiments/run_week11_pilot.py
tests/test_run_week11_pilot.py
docs/analysis/week11_machine_baseline_v1_m1.json
```

## Day 2 Verification

```text
focused Week 11 gate and runner tests:
    Ran 26 tests
    OK

python -m unittest discover -s tests:
    Ran 403 tests
    OK

python -m compileall -q src experiments tests:
    passed

python experiments/validate_paper_algorithm.py --max-n 8:
    exhaustive valid permutations = 2,074
    generated valid cases = 48
    all valid = true

Week 11 gate:
    status = frozen_not_executed
    expected rows = 1,050 / 105 / 45

formal output directory:
    absent

git diff --check:
    passed
```

The current checkout is now running on `Mac16,13 / Apple M4 / macOS 26.5.2`,
while the frozen v1 baseline is `MacBookAir10,1 / Apple M1 / macOS 26.5`.
The repaired preflight therefore reports `blocked_machine_mismatch` for v1.
This is the intended safety behavior: v1 must not run on the replacement
computer. A new machine preflight, versioned gate, run ID, and output directory
were required before later Week 11 execution work could continue; Day 2.5
implements that migration without running either pilot.

## Day 2.5: M4 Rebaseline and v2 Gate Migration

Status: complete; awaiting review before Day 3.

- [x] preserved the v1 gate, run ID, output directory, and M1 baseline bytes;
- [x] added an explicit v1 compatibility entry point;
- [x] captured a non-sensitive M4 structured baseline and preflight document;
- [x] created a distinct v2 gate, run ID, and output directory;
- [x] bound v2 to its baseline path, SHA-256, and machine identity ID;
- [x] included the binding in config and environment evidence contracts;
- [x] rejected a changed baseline when the frozen gate hash is unchanged;
- [x] forced clean-worktree checks to include every untracked file;
- [x] verified the v1 baseline still rejects the current M4 identity;
- [x] kept v1 and v2 formal output directories absent;
- [x] did not add Day 3 experiment logic or execute timing.

Migration outputs:

```text
experiments/week11_experiment_gate_v1.py
experiments/week11_experiment_gate_v2.py
docs/analysis/week11_machine_baseline_v1_m1.json
docs/analysis/week11_machine_baseline_v2_m4.json
docs/analysis/week11_machine_preflight_v1_m1.md
docs/analysis/week11_machine_preflight_v2_m4.md
tests/test_week11_experiment_gate_v2.py
```

## Day 2.5 Verification

```text
focused v1/v2 gate and runner tests:
    Ran 37 tests
    OK

python -m unittest discover -s tests:
    Ran 414 tests
    OK

v1 M1 baseline SHA-256:
    0a18befd93257c2ce4f625cdc17ceafd537d1c7349ed2a5601d684ebba41e617

v2 M4 baseline SHA-256:
    d59a3d265985d781d3368366ac1553635b5fbfca20f6a03e6df4efef43fe7f69

v1 and v2 formal output directories:
    absent

formal timing:
    not executed
```

## Day 3: Case Audit and Timing Control Flow

Status: not started.

Do not execute the frozen pilot.

## Day 4: Dedicated Fail-Closed Validator

Status: not started.

## Day 5: Formal Preflight Gate

Status: not started.

The frozen pilot cannot run until this gate is formally approved.

## Day 6: Execute and Archive One Pilot

Status: blocked by the Day 5 gate.

## Day 7: Analysis and Week 12 Gate

Status: blocked by validated Day 6 evidence.

## Current Status

Week 11 Day 1, the repaired Day 2 framework, and the Day 2.5 M4 rebaseline are
complete. W11D3 must wait for review. Both v1 and v2 pilots remain unexecuted.
