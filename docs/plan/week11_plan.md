# Week 11 Plan: Paper Ordinary-List Sorting Integration Pilot

Last updated: 2026-08-03

Status: W11D6 wiring and parser correction approved; run003 read-only preflight
passed and awaits review before formal execution.

## Core Goal

Week 11 implements, validates, executes, and analyzes one controlled
paper ordinary-list sorting integration pilot. It then freezes a separate
Week 12 formal-experiment gate without running the Week 12 experiment.

The required sequence is:

```text
freeze machine and baseline
-> implement dedicated runner
-> implement timing control flow
-> implement dedicated fail-closed validator
-> pass the complete preflight gate
-> execute one immutable pilot
-> archive and analyze evidence
-> freeze Week 12 gate
```

## Frozen Week 11 Configuration

The active machine-independent authority is:

```text
experiments/week11_experiment_protocol.py
```

The earlier unexecuted v1 M1 and v2 M4 gates remain preserved as historical
design records. They are no longer active runner dependencies.

The following values must not be redefined in the runner:

| Field | Frozen value |
| --- | --- |
| Protocol version | `week11_pilot_v1` |
| Sizes | `32, 64, 128, 256, 512` |
| Valid families | `flat_valid, nested_valid, incremental_valid` |
| Incremental cases | 5 per size |
| Total cases | 35 |
| Algorithms | `python_sort`, `simplified_jordan_reference`, `simplified_jordan_paper_ordinary_list` |
| Paper timing mode | `minimal` |
| Untimed audit mode | `checked` |
| Warm-up runs | 3 |
| Measured runs | 10 |
| Base seed | `20260723` |
| Algorithm-order seed | `20268642` |
| Case-order seed | `20262266` |
| Raw rows | 1,050 |
| Case-summary rows | 105 |
| Group-summary rows | 45 |
Any change to these protocol fields requires a new protocol version. A rerun
or benchmark-environment change does not: each execution instead receives a
new execution ID, output directory, environment record, and source commit.

## Execution Context

The run-level contract is defined by:

```text
experiments/week11_execution_context.py
```

One execution records:

```text
execution_id
output_dir
benchmark_environment
source_commit
```

Every preflight, in-memory pilot, and evidence initialization call must receive
an explicit execution ID. No machine-named default is permitted. Anonymous,
performance-relevant metadata appears only in the nested
`benchmark_environment` field; paper/audit modes in `environment.json` must
equal the protocol. Host names, serial numbers, hardware UUIDs, account data,
and device nicknames are not collected.

The original execution ID `week11_pilot_v1__run001` is retired after a
pre-evidence environment-capture failure. `week11_pilot_v1__run002` is also
retired after its read-only preflight rejected the uncovered macOS power state
`finishing charge`. Any later attempt must use a new execution ID, expected to
be `week11_pilot_v1__run003`, while retaining the same `week11_pilot_v1`
protocol. Absolute runtimes from different benchmark environments remain
separate; within-execution ratios and cross-environment trend consistency may
be compared.

## Runner Responsibility

The dedicated runner must:

- import and validate `WEEK11_EXPERIMENT_PROTOCOL`;
- expose no CLI options that mutate the frozen experiment;
- reject every existing evidence output and provide no `--overwrite`;
- require a unique execution ID plus a clean, pushed worktree before formal execution;
- write protocol configuration and execution environment evidence before timing;
- construct exactly 35 valid-input cases;
- oracle-certify every exact case before diagnostics or timing;
- run exactly one complete checked diagnostic per case outside timing;
- pass `execution_mode="minimal"` explicitly for paper timing;
- keep recognition and invalid families out of this pilot;
- restore GC after every timed call, including exceptional calls;
- randomize case and per-round algorithm order from frozen seeds;
- write raw, case-summary, group-summary, environment, config, and manifest
  evidence;
- optionally write one 35-row `case_audit.csv`.

The runner must not trust a family label as validity certification.

## Validator Responsibility

The dedicated validator must not trust runner-produced metadata. It must:

- load the frozen protocol independently;
- validate execution identity and environment evidence separately;
- reject malformed schemas and JSON without crashing;
- regenerate all 35 expected sequences;
- recompute case IDs, seeds, sequence hashes, oracle results, structural
  fields, and case order;
- independently rerun one complete checked diagnostic per case and compare
  output hash, processed count, trace count, and every paper metric;
- verify the complete `35 x 3 x 10` raw-row product;
- verify algorithm order for every measured round;
- require paper mode `minimal` and audit mode `checked`;
- require `oracle_valid`, `output_correct`, and `audit_passed`;
- reject nonempty errors and invalid timing values;
- recompute case and group summaries from raw rows;
- verify every manifest-covered evidence hash;
- return `{"valid": false}` for damaged evidence rather than an unhandled
  exception.

The validator cannot prove that an arbitrary positive timing value was not
manually replaced. Evidence preservation, clean source state, immutable config,
manifest hashes, and execution discipline reduce that risk; they do not
eliminate it.

## Timing Boundary

For every exact case:

```text
outside timing:
    generate sequence
    oracle certification
    structure_profile
    checked paper diagnostic

inside paper timing:
    paper_jordan_sort_valid(sequence, execution_mode="minimal")

outside timing:
    output comparison
    CSV/JSON/hash work
```

The minimal path still includes ordinary-list operations, local safety checks,
rollback, `stage_results`, and final partial-order output recovery.

## Day 1: Plan, Baseline, and Initial Machine Record

Status: complete.

Outputs:

```text
docs/plan/week11_plan.md
docs/progress/week11_progress.md
docs/analysis/week11_machine_preflight_v1_m1.md
```

Tasks:

1. confirm `HEAD == origin/main`;
2. record the exact baseline commit and clean worktree;
3. capture machine, OS, Python, architecture, clock, power, and load data;
4. run the complete unit suite and `compileall`;
5. validate the frozen Week 11 experiment choices;
6. validate 2,074 exhaustive permutations and 48 fixed generated cases;
7. confirm the formal output directory does not exist;
8. record machine-use controls for Day 6.

No runner or pilot execution is permitted on Day 1.

## Day 2: Dedicated Runner Framework

Status: complete after the W11D2 review repair.

Add:

```text
experiments/run_week11_pilot.py
tests/test_run_week11_pilot.py
docs/analysis/week11_machine_baseline_v1_m1.json
```

The runner must import the protocol rather than repeat its values. The only
experiment-control CLI option is:

```text
--preflight-only
```

It may also accept `--execution-id`, which changes only the run identity and
output directory. It must not alter the protocol.

Day 2 implements output contracts, no-overwrite behavior, environment/config
pre-write behavior, and preflight. It does not execute the 1,050-row pilot.

The completed framework additionally requires:

- a direct `git ls-remote` query of `refs/heads/main`, so a stale local
  `origin/main` tracking ref cannot satisfy the pushed-source gate;
- an anonymous structured benchmark-environment record for every execution;
- atomic run-directory reservation with exclusive `config.json` and
  `environment.json` writes;
- immediate JSON read-back verification;
- preservation of a partially initialized evidence directory after failure;
- config and environment initialization before any future case generation,
  diagnostics, warm-up, sorter call, or timing call.

`--preflight-only` remains read-only and never initializes the evidence
directory. Power evidence uses a structured cross-platform status: macOS uses
`pmset`, Linux uses `/sys/class/power_supply`, and a desktop with no battery is
`not_applicable` only after a successful sysfs scan confirms that no battery
exists. Directory enumeration or supply-type read failures are `unavailable`,
and the three power states have mutually exclusive field contracts. An
unavailable power source cannot initialize formal evidence. AC/load timing
readiness remains a Day 5 fail-closed decision. On macOS, the parser selects
the active power profile reported by `pmset -g batt`, reads only that profile's
settings from `pmset -g custom`, supports both `lowpowermode` and `powermode`,
and classifies the semicolon-delimited battery state by exact value.

Suggested commit:

```text
Add frozen Week 11 pilot runner framework
```

## Day 2.5: Historical M4 Rebaseline and v2 Gate Migration

Status: complete as a historical design step; superseded by Day 2.6.

Outputs:

```text
experiments/week11_experiment_gate_v1.py
experiments/week11_experiment_gate_v2.py
docs/analysis/week11_machine_baseline_v1_m1.json
docs/analysis/week11_machine_baseline_v2_m4.json
docs/analysis/week11_machine_preflight_v1_m1.md
docs/analysis/week11_machine_preflight_v2_m4.md
```

The migration:

- preserves the v1 M1 baseline bytes and unexecuted v1 identifiers;
- gives v2 a distinct run ID and output directory;
- binds v2 to the M4 baseline path, SHA-256, and machine identity ID;
- records the same binding in future config and environment evidence;
- rejects any baseline-byte change unless a new gate version is created;
- forces Git status to include all untracked files regardless of local config;
- keeps both formal output directories absent;
- adds no generator, oracle, sorter, diagnostic, warm-up, or timing logic.

Suggested commit:

```text
Freeze Week 11 v2 M4 machine gate
```

## Day 2.6: Separate Protocol from Execution Context

Status: complete; awaiting review before Day 3 resumes.

Outputs:

```text
experiments/week11_experiment_protocol.py
experiments/week11_execution_context.py
tests/test_week11_experiment_protocol.py
```

This correction separates two concerns:

```text
protocol:
    sizes, families, seeds, algorithms, repetitions, modes, timing boundary,
    and expected row counts

execution context:
    execution ID, output directory, benchmark environment, and source commit
```

The v1 M1 and v2 M4 gates and baseline files remain unchanged as historical
records. The active runner no longer imports them. A rerun or environment
change requires a new execution ID, output directory, and `environment.json`;
it does not require a new protocol version. Only a protocol-field change
creates a new protocol version.

## Day 3: Case Audit and Timing Control Flow

Status: implementation complete; awaiting review before Day 4.

Complete:

- exact 35-case generation;
- one oracle and one checked diagnostic call per case;
- ordering guarantees that both occur before warm-up;
- explicit minimal paper calls;
- GC restoration;
- reproducible case and algorithm order;
- raw, case, group, and optional case-audit schemas;
- expected `1,050 / 105 / 45` row counts.

Day 3 may use tiny temporary test configurations internally. It must not write
the frozen formal run directory.

The completed implementation keeps the execution layer in memory and leaves
the formal CLI disabled. It derives its executable configuration from the
machine-independent protocol, builds all cases and audit rows before warm-up,
uses cyclically balanced
per-round algorithm order, restores the caller's GC state after every timed
call, and creates the frozen `1,050 / 105 / 45 / 35` raw, case-summary,
group-summary, and case-audit row products. CSV/manifest writes remain blocked
until the later formal gate.

Suggested commit:

```text
Complete Week 11 pilot timing control flow
```

## Day 4: Dedicated Fail-Closed Validator

Status: implementation complete; awaiting review.

Add:

```text
experiments/validate_week11_pilot_outputs.py
tests/test_validate_week11_pilot_outputs.py
```

Required adversarial tests include:

- changed family, size, seed, hash, or structural field;
- changed case or algorithm order;
- changed paper or audit mode;
- missing, duplicate, or extra raw rows;
- changed summaries, including coordinated manifest changes;
- stale validation report;
- missing or unknown CSV fields;
- invalid integer, float, NaN, infinity, or timing values;
- invalid certification, output, audit, or error fields;
- damaged JSON and wrong JSON container types.

The validator defines its evidence schemas and deterministic case/ordering
rules independently of the runner. It regenerates the frozen 35-case product,
reruns checked diagnostics, compares every audit metric, recomputes both
summary layers, verifies manifest hashes, and rewrites the validation report
on every invocation. Its public boundary converts unexpected validation
failures into `valid=false`; it does not treat a stale
`validation_report.json` as authorization.

Suggested commit:

```text
Add fail-closed Week 11 pilot validator
```

## Day 5: Formal Preflight Gate

Status: implementation complete; final preflight must run against the clean,
pushed checkpoint before approval.

The read-only timing-readiness gate is separate from the frozen protocol. It
requires:

- `available` power with AC connected, low-power mode explicitly disabled,
  and battery `charging` or `full`;
- conditional acceptance of AC-connected `discharging` only when battery
  charge is at least 50% and low-power mode is explicitly disabled;
- a successfully established battery-free `not_applicable` environment;
- at least `1 GiB` of available disk space;
- a clean worktree whose `HEAD` equals the real remote `main` ref;
- an explicit, unused execution ID and absent output directory.

For the Week 11 pilot, one- and five-minute load above `0.25` per logical CPU
or a one-/five-minute difference above `0.10` per logical CPU is advisory. The
preflight remains ready, reports `quality = warning`, preserves the failed load
flags, and records explicit warnings in both the preflight result and the
future `environment.json`. The evidence initializer and independent validator
recompute this record from the raw load, power, and disk measurements. A later
formal experiment uses the same calculations with `execution_stage = formal`,
where either load condition is a fail-closed gate. These thresholds do not
change the machine-independent experiment protocol. `battery_percent` and
`low_power_mode` are recorded as execution-environment evidence. A missing
percentage or unknown low-power-mode state cannot authorize the discharging
exception.

Before formal execution:

1. run focused Week 11 tests;
2. run the complete unit suite and `compileall`;
3. rerun paper validation through `n=8`;
4. revalidate Week 10 archived evidence;
5. revalidate Week 9 sorting and recognition evidence;
6. run `run_week11_pilot.py --preflight-only --execution-id <id>`;
7. confirm the selected benchmark environment is timing-ready and record it;
8. confirm the output directory is absent;
9. commit and push all source changes;
10. require `HEAD == origin/main` and a clean worktree.

Expected preflight status:

```text
ready_not_executed
```

Suggested commit:

```text
Seal Week 11 pilot preflight gates
```

## Day 6: Execute and Archive One Pilot

Status: wiring and parser correction approved; run001 and run002 are retired.
The run003 read-only preflight passed and awaits review before formal execution.

The original command was attempted exactly once:

```bash
python experiments/run_week11_pilot.py \
  --execution-id week11_pilot_v1__run001
```

It failed while the Codex sandbox blocked `sysctl -n hw.memsize`. No run
directory, cases, diagnostics, warm-up, or timing were created. The immutable
record is:

```text
docs/analysis/week11_pilot_run001_failure.md
```

After review, a future attempt must use a new execution ID and should run from
a normal terminal environment in which the required environment probes work.
The independent validator was not run because no evidence directory existed.

The next read-only preflight used `run002` outside the sandbox. It failed closed
because macOS reported `finishing charge`, an exact battery-state phrase not
covered by the current parser. The formal pilot command was not run and no
evidence directory was created. The record is:

```text
docs/analysis/week11_pilot_run002_failure.md
```

`run002` is retired. The approved parser maps only the exact `finishing charge`
phrase to normalized `charging`; near matches remain `unknown`. The subsequent
`run003` read-only preflight returned `ready_not_executed` with clean timing
quality and no warnings. The formal command still requires review first.

Preflight record:

```text
docs/analysis/week11_pilot_run003_preflight.md
```

Required result:

```text
raw rows = 1,050
case-summary rows = 105
group-summary rows = 45
errors = 0
incorrect outputs = 0
failed audits = 0
validator valid = true
```

If the run fails:

- preserve the failed directory;
- do not overwrite it;
- do not reuse the execution ID;
- document the reason;
- create a new execution ID before any rerun under the unchanged protocol.

Validated evidence used in the thesis must be archived in the repository or a
persistent release.

Suggested commit:

```text
Archive validated Week 11 paper sorting pilot
```

## Day 7: Analysis and Week 12 Gate

Add:

```text
experiments/analyze_week11_pilot.py
tests/test_analyze_week11_pilot.py
docs/analysis/week11_pilot_analysis.md
docs/progress/week11_summary.md
experiments/week12_experiment_gate.py
tests/test_week12_experiment_gate.py
```

Analysis must rerun the live Week 11 validator before reading evidence. It
should report:

- algorithm by size;
- algorithm by family;
- algorithm by family and size;
- case-level median and IQR;
- algorithm runtime ratios;
- relative IQR or coefficient of variation;
- total elapsed time;
- descriptive runtime versus nesting-density relationships;
- untimed checked counters versus minimal timing.

Week 12 values must be selected from actual Week 11 elapsed time, maximum-size
runtime, group variability, thermal/load observations, and family differences.
The Week 12 formal protocol must use a new protocol version if its experimental
choices differ. Every execution must use a new execution ID and output
directory and remain:

```text
frozen_not_executed
```

Week 11 must not execute the Week 12 formal experiment.

## Non-Goals

Week 11 does not:

- change Step 1/2/3 semantics;
- implement heterogeneous finger trees or level-linked trees;
- add invalid inputs to the paper sorter;
- merge recognition and valid-input sorting;
- tune the frozen pilot after seeing results;
- run the Week 12 formal experiment;
- claim linear time or infer asymptotic complexity from five sizes;
- claim the generators represent all Jordan sequences.

## Week 12 Handoff

Week 11 is complete only if:

- the dedicated runner and validator exist;
- machine and source state are recorded;
- the immutable pilot produces `1,050 / 105 / 45`;
- all correctness and audit fields pass;
- the validator returns `valid = true`;
- complete evidence is persistently archived;
- analysis is reproducible from archived evidence;
- the Week 12 gate is frozen but unexecuted;
- all tests, `compileall`, commit checks, and historical validators pass;
- `HEAD == origin/main` and the worktree is clean.
