# Week 10 Progress

Last updated: 2026-07-28

## Goal

Measure and separate paper-algorithm implementation cost from trace,
operation-counter, and global-validation overhead before freezing the formal
timing configuration.

Plan:

```text
docs/plan/week10_plan.md
```

## Day 1: Baseline Freeze and Timing-Mode Design

Status: complete.

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

commit diff check:
    passed
```

## Day 2: Unified Execution Policy

Status: complete.

- [x] added the immutable `PaperExecutionPolicy` value object;
- [x] added fixed `checked`, `instrumented`, `trace_only`,
  `counters_only`, and `minimal` registry entries;
- [x] rejected unknown public mode names and caller-created policy copies;
- [x] kept `checked` as the default public mode;
- [x] passed one fixed policy through the public sorter, shared runner,
  `PaperJordanState`, and `OrdinarySiblingListBackend`;
- [x] required the state and backend to hold the same registry policy object;
- [x] kept `paper_jordan_diagnostics_valid()` explicitly checked;
- [x] preserved one Step 1/2/3 control flow;
- [x] verified small and representative valid inputs across all five modes;
- [x] permanently verified all 682 oracle-valid permutations through `n=7`
  across all five modes, for 3,410 mode executions;
- [x] verified duplicate-input behavior remains unchanged;
- [x] verified each mode preserves list inputs and consumes single-pass
  iterables exactly once;
- [x] rejected non-string, empty, and unknown modes before small-input
  shortcuts;
- [x] verified diagnostics always enter the shared runner with
  `CHECKED_POLICY`;
- [x] rejected state/backend policy disagreement, caller-created policy
  copies, and invalid policy types during complete state audit;
- [x] verified all five modes still record trace, count operations, and run
  backend commit validation at the Day 2 checkpoint;
- [x] ran all 340 unit tests and `compileall`;
- [x] reproduced 2,074 exhaustive valid permutations through `n=8`;
- [x] reproduced all 48 fixed generated validation cases;
- [x] passed `git diff --check`.

Outputs:

```text
src/paper_execution_policy.py
tests/test_paper_execution_policy.py
```

Day 2 implements policy selection and parameter plumbing only. The policy
flags are deliberately not consumed yet. In particular, selecting `minimal`
does not yet produce a minimal timed path.

## Day 2 Verification

```text
python -m unittest discover -s tests:
    Ran 340 tests
    OK

python -m compileall -q src experiments tests:
    passed

python experiments/validate_paper_algorithm.py --max-n 8:
    exhaustive valid permutations = 2,074
    generated valid cases = 48
    all valid = true

git diff --check:
    passed
```

## Day 3: Backend Commit-Audit Separation

Status: complete.

- [x] retained split-plan, acquired-side, parent, ownership, and stale-plan
  checks in every mode;
- [x] retained descendant/cycle prevention and rollback snapshots in every
  mode;
- [x] added an always-on constant-size initialization postcondition for P2/P3,
  both dummy roots, and their singleton lists;
- [x] added always-on local split postconditions for the retired list, staged
  lists, owners, transferred pairs, and next-list ID;
- [x] kept local postconditions inside the atomic rollback boundary;
- [x] made initialization and post-split complete backend scans conditional on
  `validate_backend_commits`;
- [x] preserved complete backend scans in the default `checked` mode;
- [x] removed complete backend scans from `instrumented`, `trace_only`,
  `counters_only`, and `minimal` execution;
- [x] verified touched ownership corruption is detected and rolled back
  without a global scan;
- [x] verified invalid-side and stale-plan guards remain active in `minimal`;
- [x] verified invalid-side, unowned-parent, and ownership-mismatch guards
  produce no additional mutation with complete audits both enabled and
  disabled;
- [x] verified checked global-audit failure and minimal local-postcondition
  failure both restore the exact pre-call backend snapshot;
- [x] verified checked, instrumented, and minimal backend snapshots agree;
- [x] verified complete state diagnostics still reject corruption in a
  minimal-produced state;
- [x] kept trace construction and operation counters active in all modes;
- [x] ran all 348 unit tests and `compileall`;
- [x] reproduced 2,074 exhaustive valid permutations through `n=8`;
- [x] reproduced all 48 fixed generated validation cases;
- [x] passed `git diff --check`.

Day 3 changes only complete backend audit scheduling. It does not change
Step 1/2/3, trace, counters, stage results, split materialization, local safety
checks, rollback, or output recovery.

## Day 3 Verification

```text
python -m unittest discover -s tests:
    Ran 348 tests
    OK

python -m compileall -q src experiments tests:
    passed

python experiments/validate_paper_algorithm.py --max-n 8:
    exhaustive valid permutations = 2,074
    generated valid cases = 48
    all valid = true

git diff --check:
    passed
```

## Day 4: Trace and Counter Decoupling

Status: implementation complete; awaiting review before Day 5.

- [x] activated `record_trace` without creating a second Step 1/2/3 loop;
- [x] avoided calling the trace recorder when trace is disabled;
- [x] avoided calling boundary-pair and Step 3(b) trace helpers when trace is
  disabled;
- [x] guarded event dictionary construction so trace-disabled modes do not
  construct event payloads;
- [x] required trace-disabled states to retain an empty `trace` list;
- [x] activated `count_operations` without changing algorithm branches;
- [x] used an empty metrics mapping when counters are disabled;
- [x] verified counter-disabled runs do not read or write the metrics mapping;
- [x] kept `trace_event_count` at zero in `counters_only`;
- [x] retained complete operation metrics in `checked`, `instrumented`, and
  `counters_only`;
- [x] retained complete trace output in `checked`, `instrumented`, and
  `trace_only`;
- [x] skipped observation-only input/left/right/transferred split-size work in
  `minimal`;
- [x] verified `trace_only` and `counters_only` still collect the split sizes
  required by their enabled observation contract;
- [x] retained `stage_results` in all five modes;
- [x] verified all five modes produce identical partial order, pair mapping,
  stage results, and canonical backend state;
- [x] kept complete diagnostics fixed to `CHECKED_POLICY`;
- [x] made complete state audit accept and verify each mode's trace/metric
  contract through same-policy deterministic replay;
- [x] permanently retained the 682 valid permutations through `n=7` across
  five modes, for 3,410 output-equivalence executions;
- [x] ran all 354 unit tests and `compileall`;
- [x] reproduced 2,074 exhaustive valid permutations through `n=8`;
- [x] reproduced all 48 fixed generated validation cases;
- [x] passed `git diff --check`.

Day 4 changes observation work only. It does not change Step 1/2/3,
`stage_results`, local safety checks, rollback, backend audit scheduling, or
output recovery.

## Day 4 Verification

```text
python -m unittest discover -s tests:
    Ran 354 tests
    OK

python -m compileall -q src experiments tests:
    passed

python experiments/validate_paper_algorithm.py --max-n 8:
    exhaustive valid permutations = 2,074
    generated valid cases = 48
    all valid = true

git diff --check:
    passed
```

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

Week 10 is in progress. Day 1, Day 2, and Day 3 are complete. Day 4
implementation is complete and awaiting review. Day 5 has not started.
