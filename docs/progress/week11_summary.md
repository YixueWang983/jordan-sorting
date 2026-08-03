# Week 11 Summary

Last updated: 2026-08-03

## Goal

Week 11 integrated the ordinary-list implementation of the 1990 paper
algorithm into one controlled valid-input sorting pilot. It separated the
machine-independent protocol from per-run environment evidence, executed one
validated pilot, archived the complete evidence, and produced a reproducible
analysis and an unexecuted Week 12 gate.

## Completed Work

Week 11 added:

- a machine-independent experiment protocol;
- anonymous per-execution environment records and explicit execution IDs;
- one runner with untimed oracle certification and checked diagnostics;
- `minimal` paper timing with correctness comparison outside the timer;
- reproducible case and algorithm ordering;
- fail-closed source, environment, no-overwrite, and evidence checks;
- an independent semantic validator that regenerates every case and audit;
- a permanently archived `run003` evidence directory;
- reproducible runtime, ratio, variability, structure, and counter summaries;
- two deterministic SVG figures;
- a frozen, unexecuted Week 12 formal sorting gate.

## Archived Pilot

The authoritative evidence is:

```text
results/runs/week11_pilot_v1__run003
```

It records source commit:

```text
01f6480fe179dcbe0f99486be86384b61dd4121f
```

Final validation:

```text
raw rows:             1,050
case-summary rows:      105
group-summary rows:      45
case-audit rows:          35
errors:                    0
incorrect outputs:         0
failed audits:              0
validator valid:         true
```

`run001` and `run002` were retired after documented pre-evidence failures.
`run003` succeeded exactly once and is immutable.

## Main Findings

The paper/reference case-median ratio falls from `3.096x` at `n=32` to
`0.564x` at `n=512`. The paper ordinary-list implementation is slower for the
first three tested sizes and faster for the final two in this pilot. The same
broad crossover appears within flat, nested, and incremental families.

Python sort remains orders of magnitude faster than both research pipelines.
The five high-relative-IQR cells all belong to Python sort, whose extremely
short calls are more exposed to timer and system noise. Reference and paper
cells have low relative IQRs in this run.

Checked diagnostic counters show descriptive positive relationships between
sibling-list work and minimal-mode runtime. Because the sample has seven cases
per size and mixes families, these correlations are not causal or asymptotic
evidence.

## Week 12 Gate

The frozen handoff is:

```text
experiments/week12_experiment_gate.py
```

Status:

```text
frozen_not_executed
```

It retains the five pilot sizes and three algorithms, expands incremental
coverage to ten cases per size, and uses five warm-ups and twenty measured
runs. Expected output is `3,600 / 180 / 45 / 60` raw, case-summary,
group-summary, and audit rows. Recognition remains a separate experiment.
The gate also freezes the exact run003 manifest path and SHA-256.

## Process Decision

Preflight is advisory and is not a separately reviewed authorization gate. The
formal runner performs the authoritative source, environment, output, and
readiness checks immediately before evidence initialization. A successful
preflight should not cause an intermediate documentation commit that changes
the source revision being checked.

## Non-Claims

Week 11 does not claim:

- a linear-time ordinary-list implementation;
- implementation of the paper's theoretical tree structures;
- recognition results for invalid inputs;
- asymptotic conclusions from five sizes;
- universal representation by the three valid generators;
- comparability of absolute timing across machines or executions.

## Reproduction

```bash
python experiments/validate_week11_pilot_outputs.py \
  --run-dir results/runs/week11_pilot_v1__run003

python experiments/analyze_week11_pilot.py \
  --run-dir results/runs/week11_pilot_v1__run003 \
  --output-dir docs/analysis

python experiments/week12_experiment_gate.py
```

The first two commands validate and analyze existing evidence. They do not run
the Week 11 pilot again. The third command prints the frozen Week 12 gate; it
does not execute the Week 12 experiment.

## Verification

```text
focused W11D7 tests:
    15 passed

full unit suite:
    506 passed

paper exhaustive validation through n=8:
    2,074 passed

fixed generated validation:
    48 passed

Week 11 live validator:
    valid = true
    rows = 1,050 / 105 / 45 / 35

Week 10 archived validator:
    valid = true
    rows = 1,500 / 100 / 60

Week 9 sorting validator:
    valid = true
    rows = 108 / 36 / 27

Week 9 recognition validator:
    valid = true
    rows = 180 / 60 / 42

Week 12 gate:
    status = frozen_not_executed
    expected rows = 3,600 / 180 / 45 / 60

compileall, SVG XML parsing, and diff checks:
    passed
```
