# Week 10 Progress

Last updated: 2026-07-27

## Goal

Measure and separate paper-algorithm implementation cost from trace,
operation-counter, and global-validation overhead before freezing the formal
timing configuration.

Plan:

```text
docs/plan/week10_plan.md
```

## Day 1: Baseline Freeze and Timing-Mode Design

Status: complete; awaiting review before Day 2.

- [x] fetched and confirmed the latest `origin/main`;
- [x] confirmed local `HEAD == origin/main`;
- [x] confirmed a clean starting worktree;
- [x] recorded commit, Python, platform, clock, GC, and git state;
- [x] ran all 324 unit tests;
- [x] ran `compileall` and `git diff --check`;
- [x] reproduced 2,074 exhaustive valid permutations through `n=8`;
- [x] reproduced all 48 fixed generated validation cases;
- [x] generated a fresh Week 9 pilot under `/tmp`;
- [x] validated sorting output at `108 / 36 / 27` rows;
- [x] validated recognition output at `180 / 60 / 42` rows;
- [x] recorded current paper median timings;
- [x] audited the actual timer call graph;
- [x] located all requested contamination sources by file/function;
- [x] distinguished local safety checks from global audits;
- [x] recorded the second input materialization inside paper timing;
- [x] documented `stage_results` as current control/safety state;
- [x] confirmed deterministic replay and oracle certification are untimed;
- [x] designed five fixed execution modes without implementing them;
- [x] recorded cross-mode state-equivalence requirements;
- [x] recorded open decisions for Day 2 and Day 3.

Outputs:

```text
docs/design/paper_timing_modes.md
docs/analysis/week10_timing_baseline.md
docs/progress/week10_progress.md
```

Day 1 changed documentation only. It did not modify:

```text
src/
experiments/
tests/
```

## Day 1 Verification

```text
baseline HEAD:
7521566e035702eede7e81e28727de6e31ecb67e

python -m unittest discover -s tests:
    Ran 324 tests
    OK

python -m compileall -q src experiments tests:
    passed

python experiments/validate_paper_algorithm.py --max-n 8:
    exhaustive valid permutations = 2,074
    generated valid cases = 48
    all valid = true

sorting pilot validator:
    valid = true
    rows = 108 / 36 / 27

recognition pilot validator:
    valid = true
    rows = 180 / 60 / 42

git diff --check:
    passed before documentation edits
```

## Day 2: Unified Execution Policy

Status: not started.

No `PaperExecutionPolicy`, fixed policy registry, or mode-aware runner exists
yet.

## Day 3: Backend Commit-Audit Separation

Status: not started.

Global backend validation has not been disabled or made optional.

## Day 4: Trace and Counter Decoupling

Status: not started.

Trace dictionaries and operation counters remain active in the current timed
paper path.

## Day 5: Public Wrapper and Contamination Runner

Status: not started.

No certified public wrapper, Week 10 contamination runner, or Week 10 output
validator has been implemented.

## Day 6: Contamination Pilot

Status: not started.

The 1,500-row contamination pilot has not run.

## Day 7: Final Mode and Week 11 Gate

Status: not started.

No final timing mode or Week 11 formal configuration has been frozen.

## Week 10 Status

Week 10 is in progress. Only Day 1 is complete.

