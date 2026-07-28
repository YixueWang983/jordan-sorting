# Week 11 Progress

Last updated: 2026-07-28

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
    experiments/week11_experiment_gate.py

run_id:
    week11_paper_sorting_pilot_v1

status:
    frozen_not_executed

expected rows:
    raw = 1,050
    case summary = 105
    group summary = 45
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
docs/analysis/week11_machine_preflight.md
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

Status: not started.

Do not execute the frozen pilot.

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

Week 11 Day 1 is complete. The next task is Day 2 runner scaffolding with
`--preflight-only`. The pilot remains unexecuted.
