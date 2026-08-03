# Week 11 Progress

Last updated: 2026-08-03

## Goal

Implement, validate, execute, archive, and analyze one immutable paper
ordinary-list sorting integration pilot, then freeze the separate Week 12
formal gate without running it.

Plan:

```text
docs/plan/week11_plan.md
```

## Active Protocol and Planned Execution

```text
protocol:
    experiments/week11_experiment_protocol.py

protocol_version:
    week11_pilot_v1

status:
    frozen; run001 retired after a pre-evidence environment-capture failure

execution IDs:
    week11_pilot_v1__run001 = retired, no evidence created
    next ID = pending failure review; expected run002

expected rows:
    raw = 1,050
    case summary = 105
    group summary = 45
```

Historical unexecuted gates:

```text
v1:
    experiments/week11_experiment_gate.py
    MacBookAir10,1 / Apple M1

v2:
    experiments/week11_experiment_gate_v2.py
    Mac16,13 / Apple M4
```

These gate files are preserved for audit history. The active runner does not
import them.

## Day 1: Plan, Baseline, and Initial Machine Record

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
were initially treated as requiring a new gate; Day 2.5 records that historical
migration. Day 2.6 later corrects the architecture by separating protocol from
execution context.

## Day 2.5: Historical M4 Rebaseline and v2 Gate Migration

Status: complete as a historical design step; superseded by Day 2.6.

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

## Day 2.6: Protocol and Execution Separation

Status: complete; awaiting review before Day 3 resumes.

- [x] added the machine-independent protocol authority;
- [x] moved execution ID, output directory, anonymous benchmark environment,
  and source commit into a run-level execution context;
- [x] removed active runner dependencies on the v1/v2 machine-bound gates;
- [x] retained the old gate and baseline files unchanged as historical records;
- [x] made `config.json` contain only protocol fields and derived row counts;
- [x] made `environment.json` contain the execution context and current machine
  environment;
- [x] allowed the same protocol to run on different machines under distinct
  execution IDs and directories;
- [x] kept formal execution disabled and all historical/new formal directories
  absent;
- [x] added protocol drift, execution isolation, path safety, machine
  independence, and evidence-contract tests.
- [x] removed the machine-named default execution ID;
- [x] required an explicit execution ID for CLI, preflight, evidence
  initialization, and in-memory pilot paths;
- [x] kept anonymous performance metadata only in the nested
  `benchmark_environment` field;
- [x] excluded host names, model identifiers, serial numbers, hardware UUIDs,
  account data, and device nicknames from active execution evidence;
- [x] rejected environment paper/audit modes that differ from the protocol;
- [x] restored the caller's GC state even if a timed algorithm changes it.

Day 2.6 outputs:

```text
experiments/week11_experiment_protocol.py
experiments/week11_execution_context.py
tests/test_week11_experiment_protocol.py
```

Interpretation rule:

```text
protocol-field change -> new protocol version
machine or rerun change -> new execution ID and environment record
```

Absolute runtimes from different machines must remain separate. Within-run
ratios and cross-machine trend consistency may be compared.

## Day 2.6 Verification

```text
focused protocol and runner tests:
    Ran 49 tests
    OK

python -m unittest discover -s tests:
    Ran 439 tests
    OK

python -m compileall -q src experiments tests:
    passed

python experiments/validate_paper_algorithm.py --max-n 8:
    exhaustive valid permutations = 2,074
    generated valid cases = 48
    all valid = true

historical v1/v2 and planned execution directories:
    absent

formal timing:
    not executed
```

## Day 3: Case Audit and Timing Control Flow

Status: implementation migrated to the protocol model; paused for review.

- [x] derived the executable contract from the machine-independent protocol;
- [x] implemented the exact 35-case generation and stable seed/ID rules;
- [x] required the generated length and oracle-valid result for every case;
- [x] ran exactly one complete checked diagnostic per case;
- [x] completed all case certifications and audits before any warm-up;
- [x] added a 35-row case-audit schema with structural and paper metrics;
- [x] timed only the selected algorithm call on an isolated input list;
- [x] passed `execution_mode="minimal"` explicitly to the paper sorter;
- [x] restored the caller's GC state on success and exception paths;
- [x] added reproducible case shuffling and cyclic algorithm ordering;
- [x] added raw, case-summary, and group-summary row builders;
- [x] protected the `1,050 / 105 / 45 / 35` frozen row counts;
- [x] kept the formal CLI disabled and all Week 11 formal output directories
  absent;
- [x] did not implement the Day 4 validator or write formal evidence.

Day 3 outputs:

```text
experiments/run_week11_pilot.py
tests/test_run_week11_pilot.py
```

## Day 3 Verification

```text
focused Week 11 runner tests:
    Ran 36 tests
    OK

python -m unittest discover -s tests:
    Ran 426 tests
    OK

paper algorithm validation:
    2,074 exhaustive valid permutations passed
    48 fixed generated cases passed

exact frozen case construction and checked audit:
    cases = 35
    audit rows = 35
    oracle-valid = 35
    audit-passed = 35
    wall-clock = 411.742 seconds

formal timing:
    not executed

historical v1/v2 and active planned execution directories:
    absent
```

The 411.742-second observation is not an algorithm timing result. It measures
the complete case-construction, structural-profile, and checked-diagnostic
phase on this machine. It is recorded so the Day 5/6 wall-clock plan does not
confuse the 15-minute timing ceiling with total process duration.

Do not execute the frozen pilot.

## Day 4: Dedicated Fail-Closed Validator

Status: implementation complete; awaiting review.

- [x] added `experiments/validate_week11_pilot_outputs.py`;
- [x] added `tests/test_validate_week11_pilot_outputs.py`;
- [x] defined validator schemas independently of the runner;
- [x] regenerated all 35 frozen cases, seeds, hashes, oracle results,
  structural profiles, and case positions;
- [x] independently reran one complete checked diagnostic per case;
- [x] compared diagnostic output hash, processed count, trace count, and every
  `paper_*` metric with the reconstructed checked result;
- [x] checked the complete 1,050-row case/round/algorithm product and cyclic
  algorithm order;
- [x] required minimal paper mode, checked audit mode, valid certification,
  correct output, passed audit, empty errors, and non-negative timing;
- [x] recomputed 105 case summaries and 45 group summaries from raw rows;
- [x] verified exact manifest labels, row counts, paths, and SHA-256 values;
- [x] returned `valid=false` for malformed CSV/JSON rather than raising;
- [x] guarded out-of-range scheduling values before indexing and added a final
  unexpected-exception fail-closed boundary;
- [x] rejected coordinated metadata and summary changes even after manifest
  hashes were refreshed;
- [x] confirmed stale validation reports cannot authorize changed evidence;
- [x] replaced macOS-only power command evidence with structured macOS/Linux
  status and accepted Linux desktop `not_applicable` power state;
- [x] made Linux sysfs enumeration and supply-type read failures return
  `unavailable` instead of being mistaken for a confirmed battery-free host;
- [x] enforced the exact `available`, `not_applicable`, and `unavailable`
  field combinations in both runner and validator power contracts;
- [x] rejected unavailable or internally inconsistent power evidence before
  formal evidence initialization;
- [x] kept formal execution disabled and created no formal evidence directory.

Focused validator regression coverage:

```text
tests/test_validate_week11_pilot_outputs.py:
    18 test methods

runner + validator focused suite:
    Ran 66 tests
    OK
```

Current repository verification:

```text
python -m unittest discover -s tests:
    Ran 466 tests
    OK

python -m compileall -q src experiments tests:
    passed

python experiments/validate_paper_algorithm.py --max-n 8:
    exhaustive valid permutations = 2,074
    generated valid cases = 48
    all valid = true

real validator checked-diagnostic reconstruction:
    cases = 35
    audits = 35
    all expected paper metrics present = true

formal Week 11 execution directories:
    absent
```

## Day 5: Formal Preflight Gate

Status: implementation complete; clean/pushed checkpoint execution and review
pending.

- [x] required AC power for systems with an applicable battery state;
- [x] accepted `charging` and `full` directly, and accepted `discharging` only
  at 50% charge or higher with low-power mode explicitly disabled;
- [x] added anonymous `battery_percent` and `low_power_mode` fields to runner,
  validator, and environment-evidence contracts;
- [x] retained `not_applicable` for successfully confirmed battery-free
  systems;
- [x] normalized one- and five-minute load by logical CPU count;
- [x] retained `0.25` normalized load and `0.10` normalized one-/five-minute
  difference thresholds as pilot warnings and formal-experiment hard gates;
- [x] required at least `1 GiB` of available disk space;
- [x] retained clean worktree, real remote-main equality, explicit execution
  ID, and unused output-directory gates;
- [x] kept the final preflight read-only and formal execution disabled;
- [x] added focused high-charge discharging success, low-charge rejection,
  low-power-mode rejection, high-load, unstable-load, and insufficient-disk
  regression coverage.
- [x] restricted macOS low-power parsing to the currently active `pmset`
  profile, supported `lowpowermode` and `powermode`, and rejected ambiguous
  battery-state substrings such as `not charging`.
- [x] separated pilot timing-quality warnings from formal fail-closed load
  checks while preserving actual load flags in the preflight result;
- [x] persisted the same readiness measurements and warnings in the future
  `environment.json` contract and independently recomputed them in the output
  validator;
- [x] required low-power mode to be explicitly disabled for every applicable
  battery-backed pilot, including `charging` and `full` states.

Implementation verification before the final clean/pushed preflight:

```text
tests/test_run_week11_pilot.py:
    Ran 67 tests
    OK

runner + validator focused suite:
    Ran 88 tests
    OK

python -m unittest discover -s tests:
    Ran 488 tests
    OK

python -m compileall -q src experiments tests:
    passed

python experiments/validate_paper_algorithm.py --max-n 8:
    exhaustive valid permutations = 2,074
    generated valid cases = 48
    all valid = true

Week 10 archived contamination evidence:
    valid = true
    rows = 1,500 / 100 / 60

Week 9 sorting evidence:
    valid = true
    rows = 108 / 36 / 27

Week 9 recognition evidence:
    valid = true
    rows = 180 / 60 / 42
```

The final read-only preflight passed against the clean pushed checkpoint with
`ready = true` and one advisory load warning. No output directory was created.

## Day 6: Execute and Archive One Pilot

Status: wiring approved; the first execution attempt failed before evidence
initialization and is awaiting failure review.

- [x] recaptured Git, power, low-power mode, load, and disk immediately before
  evidence initialization;
- [x] reused the `execution_stage = pilot` readiness policy;
- [x] prewrote and revalidated `config.json` and `environment.json` before any
  case generation, warm-up, or timed call;
- [x] wired the frozen in-memory pipeline to exclusive CSV writes and a
  SHA-256 manifest;
- [x] wired the independent fail-closed validator after archival;
- [x] preserved partial or failed evidence and prohibited execution-ID reuse;
- [x] tested the complete control flow with stubbed timing in temporary
  directories only;
- [x] attempted `week11_pilot_v1__run001` exactly once after wiring review;
- [x] recorded the sandbox-blocked physical-memory capture failure;
- [x] confirmed no run directory, case generation, diagnostics, warm-up, or
  timing occurred;
- [x] retired `week11_pilot_v1__run001` permanently;
- [ ] select a new execution ID only after the failure record is reviewed;
- [ ] produce and independently validate one complete pilot evidence set.

Failure record:

```text
docs/analysis/week11_pilot_run001_failure.md
```

## Day 7: Analysis and Week 12 Gate

Status: blocked pending failure review and validated Day 6 evidence.

## Current Status

Week 11 Day 1, the repaired Day 2 framework, the historical Day 2.5 migration,
Day 3 timing control flow, and the approved Day 4 validator are complete.
The active protocol is machine-independent; each run records an anonymous
benchmark environment and explicit execution ID. W11D5 preflight and W11D6
wiring are approved. The single `run001` attempt failed during physical-memory
capture in the Codex sandbox, before evidence initialization or timing. The ID
is retired, no output directory exists, and W11D7 remains blocked.
