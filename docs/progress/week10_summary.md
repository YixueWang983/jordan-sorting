# Week 10 Summary

Last updated: 2026-07-28

## Goal

Week 10 separated the ordinary-list paper algorithm from correctness and
observation work that had contaminated its Week 9 pilot timing. It selected one
explicit timing mode and froze, but did not execute, the Week 11 integration
pilot gate.

## Completed Work

Week 10 added:

- one immutable `PaperExecutionPolicy` registry;
- five fixed modes: `checked`, `instrumented`, `trace_only`,
  `counters_only`, and `minimal`;
- one shared Step 1/2/3 control flow for every mode;
- policy-controlled complete backend commit audits;
- policy-controlled trace recording and operation counters;
- always-on local safety checks, local postconditions, and rollback;
- a certified public wrapper that keeps oracle work outside pure paper timing;
- a dedicated contamination runner and fail-closed semantic validator;
- a complete archived 1,500-row evidence run;
- reproducible overhead tables and runtime-ratio figures;
- a machine-readable Week 11 configuration gate.

## Final Timing Decision

The selected paper-algorithm timing mode is:

```text
minimal
```

It is selected because all required gates pass:

```text
algorithm output:
    identical to checked

canonical backend state:
    identical to checked

exhaustive correctness:
    2,074 oracle-valid permutations through n=8 pass

fixed generated validation:
    48 cases pass

timed path:
    no oracle
    no deterministic replay
    no complete backend validate_invariants()
    no trace
    no diagnostic operation counters
```

`minimal` still includes the actual ordinary-list algorithm work:

```text
Step 1/2/3 control flow
ordinary-list predecessor/successor access
sibling-list search, insertion, split, and ownership transfer
always-on local safety checks and rollback
stage_results needed by algorithm control
partial-order output recovery
```

## Correctness and Timing Separation

Every timed paper case must use this order:

```text
1. generate the case outside timing
2. certify actual input validity with the oracle outside timing
3. compute structural metadata outside timing
4. run one complete checked diagnostic outside timing
5. run warm-up and measured paper calls in minimal mode
6. compare measured output with the precomputed oracle result outside timing
```

The checked diagnostic is also the source of paper operation counters. A
separate instrumented call is unnecessary unless a later experiment requires
different diagnostic semantics.

## Contamination Pilot

The archived run is:

```text
results/runs/week10_contamination_full_20260728/
```

It contains:

```text
raw rows:             1,500
case-summary rows:      100
group-summary rows:      60
errors:                   0
incorrect outputs:        0
failed audits:            0
validator valid:       true
```

Median case-level ratios relative to `minimal` were:

```text
checked:       1.789x
instrumented:  1.126x
trace_only:    1.102x
counters_only: 1.013x
```

The evidence supports removing complete backend validation, trace, and counters
from paper timing. It does not establish a theoretical complexity result.

## Frozen Week 11 Gate

Canonical configuration:

```text
experiments/week11_experiment_gate.py
```

Status:

```text
frozen_not_executed
```

Configuration:

```text
run_id:
    week11_paper_sorting_pilot_v1

output directory:
    results/runs/week11_paper_sorting_pilot_v1

sizes:
    32, 64, 128, 256, 512

valid families:
    flat_valid
    nested_valid
    incremental_valid

cases:
    1 flat + 1 nested + 5 incremental per size
    35 total

algorithms:
    python_sort
    simplified_jordan_reference
    simplified_jordan_paper_ordinary_list

paper timing mode:
    minimal

untimed paper audit mode:
    checked

warm-up runs:
    3

measured runs:
    10

seed:
    20260723

algorithm-order seed:
    20268642

case-order seed:
    20262266
```

Expected output:

```text
raw rows:
    35 cases x 3 algorithms x 10 runs = 1,050

case-summary rows:
    35 cases x 3 algorithms = 105

group-summary rows:
    3 families x 5 sizes x 3 algorithms = 45

runtime planning ceiling:
    15 minutes on the recorded development machine
```

The runtime value is a planning ceiling, not a performance claim. Week 11 must
record actual elapsed time before deciding the Week 12 formal configuration.

## Week 11 Gate

Week 11 may execute the pilot only after its runner and validator prove:

- paper timing explicitly passes `execution_mode="minimal"`;
- the manifest records `minimal` rather than relying on a default;
- every actual paper input is oracle-certified before diagnostics or timing;
- every case receives exactly one untimed checked diagnostic;
- recognition remains separate from valid-input sorting;
- case and algorithm order are reproducible from the frozen seeds;
- output validation regenerates cases and recomputes summaries;
- existing Week 9 sorting and recognition evidence remains valid.

## Non-Claims

Week 10 does not claim:

- a heterogeneous finger-tree implementation;
- a level-linked tree implementation;
- a linear-time ordinary-list backend;
- that the tested generators represent all Jordan sequences;
- that the Week 10 contamination pilot is the final thesis experiment.

## Verification

```text
full unit suite:
    passed

paper exhaustive validation through n=8:
    2,074 passed

fixed generated validation:
    48 passed

Week 10 archived validator:
    valid = true

Week 9 sorting validator:
    valid = true

Week 9 recognition validator:
    valid = true
```

Week 10 is complete. Week 11 should implement the frozen integration runner
and validator, run only the 1,050-row pilot, inspect runtime and schema
stability, and then freeze the separate Week 12 formal experiment.
