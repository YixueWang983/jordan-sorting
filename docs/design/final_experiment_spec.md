# Final Experiment Specification

Last updated: 2026-07-28

## Status

This document freezes the experiment questions, variables, correctness criteria,
and aggregation rules for the next formal experiment stage.

The reference-framework boundary and formal experiment scope were confirmed by
the supervisor on 2026-07-24.

## Research Questions

### RQ1 / H1: Correctness

Does each compared implementation return the expected sorted output, validity
decision, and invalid reason where applicable?

Metrics:

```text
output_correct
validity_correct
reason_correct
overall_correct
error_count
```

### RQ2 / H2a: Structural Coverage

What structures do the generator families actually produce?

Metrics:

```text
family
n
structural_category
max_depth
parented_interval_ratio
containment_pair_density
crossing_pair_density
```

Generator family names are not treated as proof of structure. Structure is
measured after generation.

### RQ3 / H2b: Ordinary-Backend Sensitivity

For fixed `n`, does the ordinary-list backend exploit structural differences?

Metrics:

```text
containment_checks
laminar_pair_checks
nodes_visited
trace_event_count
```

If containment checks are mostly fixed by `n`, that is a valid negative result:
the current ordinary-list implementation exposes structures but does not exploit
them algorithmically.

### RQ4 / H3: Cost Decomposition

How much overhead comes from validation and reference-pipeline work compared with
ordinary sorting?

Compared algorithms:

```text
python_sort
sort_plus_laminarity_check
simplified_jordan_reference
```

Important boundary:

`simplified_jordan_reference` includes engineering costs such as validation,
family-tree construction, structural stats, trace construction, and serializable
output. It is not a theoretical linear-time implementation.

## Independent Variables

```text
algorithm
family
n
case_id
validity class
max_depth
containment_pair_density
crossing_pair_density
```

## Dependent Variables

```text
runtime
operation counters
correctness fields
error count
```

## Aggregation

Formal timing uses:

```text
primary statistic: median
variability: Q1, Q3, IQR
supplementary: mean, standard deviation
raw run -> case summary -> family/n/algorithm group summary
```

Rules:

- deterministic families have one input case per `n`;
- randomized families support case-to-case variation analysis;
- timing runs are not independent generated cases;
- correlations are exploratory;
- p-values are not part of the initial experiment plan;
- runtime does not prove theoretical complexity;
- operation counts are better for explaining ordinary-list scan behavior.

## Frozen Formal Configuration

### Coverage Experiment

Purpose:

```text
audit generator structural coverage and invalid-reason distribution
```

Configuration:

```text
sizes:
31, 32, 33,
63, 64, 65,
127, 128, 129,
255, 256, 257

families:
flat_valid
nested_valid
incremental_valid
invalid_upper_crossing
invalid_lower_crossing
random_invalid
mutation_based_invalid

deterministic repetitions:
1

randomized repetitions:
30

seed:
20260723

Formal run id:
week9_formal_coverage

Default output directory:
results/runs/week9_formal_coverage/
```

Expected row counts:

```text
coverage audit rows:
12 sizes x (4 deterministic families x 1 + 3 randomized families x 30)
= 1128 rows

coverage summary rows:
12 sizes x 7 families = 84 rows
```

### Pre-Paper Reference Performance Experiment

Purpose:

```text
compare ordinary sorting, validation-plus-sort, and the ordinary-list reference
pipeline under a fixed correctness and structural-observability protocol
```

Configuration:

```text
sizes:
64, 128, 256, 512, 1024

families:
flat_valid
nested_valid
incremental_valid
invalid_upper_crossing
invalid_lower_crossing
random_invalid
mutation_based_invalid

deterministic cases:
1 per family/size

randomized cases:
5 per family/size

warm-up runs:
5

measured runs:
20

seed:
20260723

algorithm-order seed:
20268642

case-order seed:
20262266

algorithms:
python_sort
sort_plus_laminarity_check
simplified_jordan_reference
```

Expected row counts:

```text
cases:
5 sizes x (4 deterministic families x 1 + 3 randomized families x 5)
= 95 cases

raw timing rows:
95 cases x 3 algorithms x 20 measured runs
= 5700 rows

case-summary rows:
95 cases x 3 algorithms
= 285 rows

group-summary rows:
7 families x 5 sizes x 3 algorithms
= 105 rows
```

Formal run id:

```text
week9_formal_reference
```

Default output directory:

```text
results/runs/week9_formal_reference/
```

### Formal Commands

Coverage audit:

```bash
python experiments/audit_generator_coverage.py \
  --run-id week9_formal_coverage \
  --families flat_valid nested_valid incremental_valid invalid_upper_crossing invalid_lower_crossing random_invalid mutation_based_invalid \
  --sizes 31 32 33 63 64 65 127 128 129 255 256 257 \
  --randomized-repetitions 30 \
  --seed 20260723
```

Coverage validation:

```bash
python experiments/validate_generator_audit_outputs.py \
  --run-dir results/runs/week9_formal_coverage
```

Performance experiment:

```bash
python experiments/run_week7_pilot.py \
  --run-id week9_formal_reference \
  --families flat_valid nested_valid incremental_valid invalid_upper_crossing invalid_lower_crossing random_invalid mutation_based_invalid \
  --sizes 64 128 256 512 1024 \
  --randomized-cases 5 \
  --warmup-runs 5 \
  --measured-runs 20 \
  --seed 20260723 \
  --algorithm-order-seed 20268642 \
  --case-order-seed 20262266 \
  --algorithms python_sort sort_plus_laminarity_check simplified_jordan_reference
```

Performance validation:

```bash
python experiments/validate_experiment_outputs.py \
  --run-dir results/runs/week9_formal_reference
```

### Week 9 Paper-Algorithm Integration Pilot

The frozen formal reference experiment above predates the paper ordinary-list
implementation and is not silently redefined. Week 9 adds a separate,
non-final integration pilot:

```bash
python experiments/run_week9_pilot.py \
  --run-id week9_integration_pilot \
  --run-dir results/runs/week9_integration_pilot
```

It uses sizes `8, 16, 32`, one warm-up, three measured runs, and two randomized
cases. Sorting and recognition use separate configurations and output
directories.

For the valid-input-only paper sorter, each generated sequence must be
oracle-certified before paper diagnostics or timing. A valid-family
configuration is not sufficient by itself. Output validation also requires
`oracle_valid = true` on every paper-algorithm row.

This pilot establishes correctness, schema compatibility, manifests, and rough
executability. It must not be used for final performance conclusions because
the Week 9 paper path included trace, counters, and complete backend commit
validation.

### Week 10 Paper Timing Decision

The Week 10 contamination study resolves the Week 9 timing boundary:

```text
paper timing:
    minimal

untimed correctness audit:
    checked

untimed input certification:
    oracle
```

`minimal` runs the same Step 1/2/3 control flow and produces the same output and
canonical backend state as `checked`. It disables:

```text
complete backend commit validation
trace recording
diagnostic operation counters
```

It retains:

```text
ordinary-list search, insertion, split, and ownership transfer
local safety checks and rollback
stage_results required by control flow
partial-order output recovery
```

The archived 1,500-row contamination evidence is in:

```text
results/runs/week10_contamination_full_20260728/
```

Its validator reports `valid = true`. This mode choice removes measured
diagnostic overhead; it does not establish linear-time complexity.

### Frozen Week 11 Paper-Sorting Integration Pilot

The canonical machine-readable gate is:

```text
experiments/week11_experiment_gate_v2.py
```

Status:

```text
frozen_not_executed
```

Configuration:

```text
run_id:
week11_paper_sorting_pilot_v2_m4

output directory:
results/runs/week11_paper_sorting_pilot_v2_m4

machine baseline:
docs/analysis/week11_machine_baseline_v2_m4.json

sizes:
32, 64, 128, 256, 512

valid families:
flat_valid
nested_valid
incremental_valid

deterministic cases:
1 per deterministic family/size

randomized incremental cases:
5 per size

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

algorithms:
python_sort
simplified_jordan_reference
simplified_jordan_paper_ordinary_list

paper execution mode:
minimal

untimed paper audit mode:
checked
```

Expected row counts:

```text
cases:
5 sizes x (1 flat + 1 nested + 5 incremental)
= 35 cases

raw timing rows:
35 cases x 3 algorithms x 10 measured runs
= 1050 rows

case-summary rows:
35 cases x 3 algorithms
= 105 rows

group-summary rows:
3 families x 5 sizes x 3 algorithms
= 45 rows
```

The runtime planning ceiling is 15 minutes on the recorded development
machine. This is a scheduling bound rather than an empirical claim. Week 11
records actual elapsed time and uses it to freeze the separate Week 12 formal
experiment.

The Week 11 runner must not rely on the public sorter's default mode. It must
pass `execution_mode="minimal"` explicitly and store that mode in raw rows,
configuration, environment, and manifest evidence. Every paper case must
receive one oracle certification and one checked diagnostic before warm-up or
measured timing.

Recognition remains a separate experiment. The Week 11 valid-input sorting
pilot does not add invalid families to the paper algorithm.

### Formal Machine

The execution machine must be fixed and recorded before the corresponding
pilot or formal run begins. Any machine change requires a new run ID and a new
environment record. The actual machine metadata must be stored in
`environment.json`; the thesis should cite that evidence rather than memory.

## Failure and Fallback Rules

1. If any raw row has `error != ""`, the formal run fails.
2. If any applicable correctness field is false, the formal run fails.
3. If the applicable experiment-specific validator returns `valid=false`, the
   run fails.
4. Validator checks include manifest SHA-256 verification and raw-to-summary
   recomputation; a summary CSV is not accepted merely because it exists.
5. If a run fails, keep its run directory for debugging and rerun with a new
   `run_id`; do not overwrite failed evidence.
6. Any change to a frozen configuration requires a new gate version and a new
   `run_id`; the previous gate and evidence remain unchanged.
7. Pilot and formal evidence used in the thesis must be archived either in the
   repository or in a persistent release. A manifest hash and reproduction
   command alone do not replace the underlying evidence files.

## Frozen CSV Semantics

Final runners should keep these meanings stable:

```text
time_ns                     measured algorithm runtime only
output_correct              sorted output equals oracle sorted output
validity_correct            reported validity matches oracle when applicable
reason_correct              reported reason matches oracle when applicable
overall_correct             all applicable correctness checks passed
containment_pair_density    containment-pair density, not legacy nesting ratio
parented_interval_ratio     parented intervals / total intervals
```
