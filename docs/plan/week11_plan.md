# Week 11 Plan: Paper Ordinary-List Sorting Integration Pilot

Last updated: 2026-07-28

Status: Day 1 complete; frozen pilot not executed.

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

The machine-readable authority is:

```text
experiments/week11_experiment_gate.py
```

The following values must not be redefined in the runner:

| Field | Frozen value |
| --- | --- |
| Run ID | `week11_paper_sorting_pilot_v1` |
| Output directory | `results/runs/week11_paper_sorting_pilot_v1` |
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
| Runtime planning ceiling | 15 minutes |

Any configuration change requires a new gate version, run ID, and output
directory. Existing evidence must not be overwritten.

## Runner Responsibility

The dedicated runner must:

- import and validate `WEEK11_EXPERIMENT_GATE`;
- expose no CLI options that mutate the frozen experiment;
- reject every existing evidence output and provide no `--overwrite`;
- require a clean, pushed worktree before formal execution;
- write configuration and environment evidence before timing;
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

- load the frozen gate independently;
- reject malformed schemas and JSON without crashing;
- regenerate all 35 expected sequences;
- recompute case IDs, seeds, sequence hashes, oracle results, structural
  fields, and case order;
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

## Day 1: Plan, Baseline, and Machine Freeze

Status: complete.

Outputs:

```text
docs/plan/week11_plan.md
docs/progress/week11_progress.md
docs/analysis/week11_machine_preflight.md
```

Tasks:

1. confirm `HEAD == origin/main`;
2. record the exact baseline commit and clean worktree;
3. capture machine, OS, Python, architecture, clock, power, and load data;
4. run the complete unit suite and `compileall`;
5. validate the frozen Week 11 gate;
6. validate 2,074 exhaustive permutations and 48 fixed generated cases;
7. confirm the formal output directory does not exist;
8. record machine-use controls for Day 6.

No runner or pilot execution is permitted on Day 1.

## Day 2: Dedicated Runner Framework

Add:

```text
experiments/run_week11_pilot.py
tests/test_run_week11_pilot.py
```

The runner must import the gate rather than repeat its values. The only
permitted operational CLI option is:

```text
--preflight-only
```

Day 2 implements output contracts, no-overwrite behavior, environment/config
pre-write behavior, and preflight. It does not execute the 1,050-row pilot.

Suggested commit:

```text
Add frozen Week 11 pilot runner framework
```

## Day 3: Case Audit and Timing Control Flow

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

Suggested commit:

```text
Complete Week 11 pilot timing control flow
```

## Day 4: Dedicated Fail-Closed Validator

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

Suggested commit:

```text
Add fail-closed Week 11 pilot validator
```

## Day 5: Formal Preflight Gate

Before formal execution:

1. run focused Week 11 tests;
2. run the complete unit suite and `compileall`;
3. rerun paper validation through `n=8`;
4. revalidate Week 10 archived evidence;
5. revalidate Week 9 sorting and recognition evidence;
6. run `run_week11_pilot.py --preflight-only`;
7. confirm the fixed machine is timing-ready;
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

Run exactly once:

```bash
python experiments/run_week11_pilot.py

python experiments/validate_week11_pilot_outputs.py \
  --run-dir results/runs/week11_paper_sorting_pilot_v1
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
- do not reuse the run ID;
- document the reason;
- create a new gate version before any rerun.

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
The Week 12 gate must use a new version, run ID, and output directory and remain:

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
