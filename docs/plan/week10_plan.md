# Week 10 Plan: Paper Algorithm Timing-Contamination Study

Last updated: 2026-07-28

Status: complete; `minimal` selected and Week 11 gate frozen.

## Core Goal

Week 9 completed the ordinary-list paper algorithm, correctness audit, and
small experiment integration. Week 10 does not change the Step 1/2/3 algorithm
semantics. It answers:

> How much of the current `paper_jordan_sort_valid()` runtime belongs to the
> algorithm and ordinary-list operations, and how much belongs to trace
> recording, operation counters, and backend-wide validation?

Week 10 must deliver:

1. one policy-driven execution architecture without duplicating the main loop;
2. a minimal timing mode without full backend validation, trace, or counters;
3. one complete untimed correctness audit for every timed case;
4. a reproducible timing-contamination comparison;
5. a justified final paper execution mode;
6. an explicit separation between implementation cost and diagnostic cost;
7. a frozen Week 11 formal-experiment configuration.

## Non-Goals

- no heterogeneous finger trees;
- no level-linked search trees;
- no changes to Step 1/2/3 semantics;
- no oracle call inside the paper-algorithm timed region;
- no thesis-scale formal run;
- no claim that the ordinary-list implementation is linear time.

## Week 9 Frozen Baseline

```text
baseline commit:
cc9f65606ff9ba176b60889ed3ad72c872d43376

full tests:
324 passed

exhaustive valid permutations:
n=0..8
2,074 passed

generated validation:
48 passed
```

The Week 9 pilot evidence to preserve includes:

- raw, case-summary, and group-summary row counts;
- output-validator reports;
- current paper-algorithm median timings;
- environment and commit metadata;
- sorting and recognition manifests.

## Timing-Work Classification

| Work | Algorithm-required | Final timing |
| --- | ---: | ---: |
| Step 1/2/3 control flow | yes | yes |
| ordinary-list search, insertion, split, and ownership transfer | yes | yes |
| necessary local precondition checks | yes | yes |
| stale split-plan and ownership checks | yes | yes |
| complete backend `validate_invariants()` | no | no |
| trace-event construction and append | no | measure first |
| operation-counter updates | no | measure first |
| deterministic replay | no | no |
| oracle certification | input contract | no |
| CSV, JSON, hashing, and summary work | experiment infrastructure | no |

## Fixed Execution Modes

| Mode | Trace | Counters | Complete commit validation |
| --- | ---: | ---: | ---: |
| `checked` | on | on | on |
| `instrumented` | on | on | off |
| `trace_only` | on | off | off |
| `counters_only` | off | on | off |
| `minimal` | off | off | off |

Definitions:

- `checked` preserves the Week 9 behavior.
- `instrumented` isolates the effect of removing backend-wide commit audits.
- `trace_only` estimates trace overhead.
- `counters_only` estimates operation-counter overhead.
- `minimal` is the candidate final timing mode.

The initial study does not implement all eight possible boolean combinations.
Additional combinations are permitted only if the first results show material
interaction effects.

## Day 1: Freeze the Baseline and Design Timing Modes

### Goal

Locate every contamination source and freeze unambiguous mode contracts before
changing code.

### Tasks

1. Record the Week 9 baseline commit, test evidence, validation evidence,
   pilot row counts, current timings, manifests, and environment.
2. Audit these paths:

```text
paper_jordan_sort_valid()
_run_paper_jordan_valid()
_run_paper_jordan_state_values()
_record_trace()
metric updates
OrdinarySiblingListBackend.commit_split()
validate_invariants()
SortedOrderList validation
stage_results recording
```

3. Document the five fixed modes and the local/global validation boundary.
4. Add:

```text
docs/design/paper_timing_modes.md
```

5. Document:
   - checks that can never be disabled;
   - work that must remain outside timing;
   - cross-mode state equivalence requirements;
   - diagnostics/timing linkage;
   - allowed and prohibited thesis claims.

### Acceptance

- algorithm behavior is unchanged;
- every contamination source maps to a concrete function;
- all five modes are unambiguous;
- local safety checks are distinguished from global audits;
- all Week 9 tests still pass.

Suggested commit:

```text
Define Week 10 paper timing modes
```

## Day 2: Implement One Execution-Policy Architecture

### Goal

Add execution policies without duplicating the Step 1/2/3 control flow.

### Planned API

```python
@dataclass(frozen=True)
class PaperExecutionPolicy:
    record_trace: bool
    count_operations: bool
    validate_backend_commits: bool
```

Fixed registry:

```text
CHECKED_POLICY
INSTRUMENTED_POLICY
TRACE_ONLY_POLICY
COUNTERS_ONLY_POLICY
MINIMAL_POLICY
```

The call graph must remain:

```text
public API
    -> one input materialization
    -> _run_paper_jordan_state_values(...)
    -> one shared Step 1/2/3 control flow
```

Separate checked/minimal main loops are prohibited.

The existing default call must remain compatible:

```python
paper_jordan_sort_valid(seq)
```

An explicit mode-aware API may be added, but experiment algorithms must come
from a fixed mode registry rather than anonymous lambdas.

### Tests

- every mode uses the same internal runner;
- default behavior remains Week 9-compatible;
- `n=0,1,2,3` outputs agree across modes;
- all valid inputs produce the same output across modes;
- unknown modes are rejected;
- policies are immutable;
- duplicate-value behavior remains unchanged;
- an AST/structure guard confirms only one main loop exists.

### Acceptance

- one algorithm control flow;
- default API compatibility;
- cross-mode output agreement;
- all existing tests pass.

Suggested commit:

```text
Add unified paper execution policies
```

## Day 3: Move Complete Backend Validation Out of Timing

### Goal

Allow the minimal path to skip backend-wide scans without removing local
safety, atomicity, or rollback.

### Always-On Local Checks

- `SplitPlan` type and stale-plan checks;
- acquired-side legality;
- new-parent legality;
- retired-list and owner agreement;
- boundary membership in the target list;
- pair/list ID existence;
- basic ownership-transfer consistency;
- rollback after mutation failure.

### Optional Global Check

The following complete registry/parent-chain scan may be disabled by policy:

```python
self.validate_invariants(require_all_owned=False)
```

No monkey patch or global flag may control this behavior.

Initialization must also distinguish required local checks from complete
`partial_order.validate_links()` and `sibling_backend.validate_invariants()`
audits. Each timed case must still receive one complete untimed checked audit.

### State-Equivalence Gate

Run the same input under `checked`, `instrumented`, and `minimal`, then compare:

```text
final partial order
processed_count
pair registry
sibling-list registry
parent ownership
child-list ownership
dummy registration
canonical backend snapshot
```

Only trace, metrics, and invariant-check counts may differ.

### Atomicity Tests

With complete validation both enabled and disabled, test:

- stale split plan;
- invalid acquired side;
- invalid new parent;
- ownership mismatch;
- exception during mutation;
- exact rollback to the pre-call snapshot.

### Acceptance

- minimal mode performs no full registry/global invariant scan;
- local checks and rollback remain active;
- checked and minimal backend snapshots match;
- checked diagnostics still detect injected corruption.

Suggested commit:

```text
Separate backend commit audit from timed operations
```

## Day 4: Decouple Trace and Counters

### Goal

Make trace and counters pure observation mechanisms that do not affect
branching or results.

### Trace

When trace is disabled, do not construct event dictionaries and then discard
them. Event construction itself must be skipped.

### Counters

When counters are disabled:

- do not perform dictionary lookup/increment work;
- do not scan a structure solely for a metric;
- do not change split or ownership behavior.

A counter sink/no-op sink or explicit policy-aware helper is acceptable.

`stage_results` may remain because it provides O(1) algorithm precondition
state. It must be documented as implementation cost, not diagnostic trace.

### Diagnostics Compatibility

```python
paper_jordan_diagnostics_valid(seq)
```

must continue to provide complete trace, metrics, deterministic replay, and
invariant-audit results.

### Differential Gate

- all repository oracle-valid permutations through at least `n=7`;
- standalone exhaustive validation through `n=8`;
- all 48 fixed generated cases;
- all five modes equal the oracle-sorted output;
- checked and minimal canonical backend snapshots agree.

### Acceptance

- minimal records no trace;
- minimal updates no diagnostic counters;
- neither trace nor counters controls a branch;
- diagnostics remain Week 9-compatible;
- every mode passes differential validation.

Suggested commit:

```text
Decouple paper trace and counters from execution
```

## Day 5: Add Safe Public and Experiment Interfaces

### Goal

Separate input certification from certified-input sorting and add a dedicated
contamination runner.

### Public Boundaries

```python
paper_jordan_sort_valid(seq, execution_mode=...)
```

- caller supplies an already certified valid sequence;
- core does not call the oracle.

```python
certified_paper_jordan_sort(seq)
```

- oracle certifies the actual sequence first;
- invalid input receives an explicit rejection;
- valid input is passed to the paper sorter;
- wrapper is not used inside pure paper timing.

### Required Case Flow

```text
generate sequence
-> oracle certification
-> reject an invalid actual sequence
-> checked diagnostics once, untimed
-> run every timing mode
-> compare every output with the certified oracle result
```

### New Experiment Files

```text
experiments/run_week10_timing_contamination.py
experiments/validate_week10_timing_outputs.py
```

The frozen reference experiment remains unchanged.

### Raw CSV Minimum Fields

```text
run_id
case_id
family
n
seed
execution_mode
record_trace
count_operations
validate_backend_commits
run_index
mode_position
time_ns
oracle_valid
output_correct
audit_passed
error
```

### Case-Summary Minimum Fields

```text
case_id
family
n
execution_mode
median_time_ns
q1_time_ns
q3_time_ns
iqr_time_ns
mean_time_ns
stdev_time_ns
median_over_minimal_ratio
all_correct
```

### Group-Summary Minimum Fields

```text
family
n
execution_mode
case_count
median_case_time_ns
median_over_minimal_ratio
all_cases_correct
```

### Validator Must Reject

- a paper case with `oracle_valid = false`;
- a missing execution mode;
- mode flags inconsistent with the mode name;
- any wrong output;
- `audit_passed = false`;
- incomplete measured runs;
- missing or invalid mode order/position;
- summaries inconsistent with raw rows;
- manifest hash mismatch;
- malformed or negative timing;
- structural fields changing between modes for one case.

### Acceptance

- oracle never enters a timed call;
- each case receives one complete untimed audit;
- all modes receive the same sequence;
- mode order is balanced by measured round;
- runner and validator include independent tamper tests.

Suggested commit:

```text
Add Week 10 timing contamination runner
```

## Day 6: Run and Analyze the Contamination Pilot

### Frozen Pilot

```text
families:
    flat_valid
    nested_valid
    incremental_valid

sizes:
    32, 64, 128, 256

deterministic cases:
    1 per family and size

incremental randomized cases:
    3 per size

execution modes:
    checked
    instrumented
    trace_only
    counters_only
    minimal

warm-up runs:
    3

measured runs:
    15

seed:
    20260723

GC:
    disabled only during each timed call

timer:
    time.perf_counter_ns()
```

Expected data volume:

```text
20 cases
1,500 raw rows
100 case-summary rows
60 group-summary rows
```

Run a smoke configuration first:

```text
sizes: 8, 16, 32
warm-up runs: 1
measured runs: 3
```

The full pilot may run only after the smoke output validator passes.

### Analysis

For each case calculate:

```text
validation overhead = checked - instrumented
trace overhead = trace_only - minimal
counter overhead = counters_only - minimal
combined instrumentation overhead = instrumented - minimal
relative slowdown = mode median / minimal median
```

Report median, Q1, Q3, IQR, relative slowdown, scaling by `n`, differences by
family, whether global validation masks ordinary-list split cost, and whether
trace/counters should remain in final timing.

Permitted conclusion form:

> Removing correctness/debug instrumentation substantially changes the
> measured runtime of the ordinary-list implementation.

Potential conclusion form, only if supported:

> Backend-wide validation dominates checked execution time for larger tested
> inputs.

Prohibited:

> Minimal mode proves the algorithm is linear.

### Acceptance

- exactly 1,500 complete raw rows;
- all mode outputs correct;
- all untimed case audits pass;
- validator reports `valid = true`;
- no timing error;
- one mode-overhead table;
- at least one runtime-ratio figure;
- conclusions distinguish algorithm and instrumentation cost.

Suggested commit:

```text
Record Week 10 timing contamination pilot
```

## Day 7: Select the Final Mode and Freeze the Week 11 Gate

### Final-Mode Requirements

The expected candidate is `minimal`, but it may be selected only if:

- output equals checked mode;
- canonical backend snapshot equals checked mode;
- exhaustive validation passes;
- every case has an independent untimed checked audit;
- timed path contains no oracle;
- timed path contains no deterministic replay;
- timed path contains no complete backend `validate_invariants()`;
- timed path records no trace;
- timed path updates no diagnostic counters;
- manifest records the execution mode explicitly.

If any condition fails, minimal cannot enter the formal experiment.

### Recommended Separation

```text
timing:
    minimal mode

operation counts:
    one checked/instrumented diagnostic call per case outside timing

correctness:
    one complete checked audit per case outside timing
```

### Freeze, Do Not Run, the Week 11 Configuration

Record:

- formal sizes;
- valid families;
- randomized case count;
- warm-up and measured runs;
- execution mode;
- case-order and algorithm-order seeds;
- estimated runtime and raw-row count;
- output directory and run ID.

### Documentation

Update:

```text
README.md
docs/design/final_experiment_spec.md
docs/design/benchmark_protocol.md
docs/design/paper_algorithm_ordinary_list.md
docs/progress/week10_progress.md
docs/progress/week10_summary.md
docs/plan/week10_plan.md
```

### Final Regression

```bash
python -m unittest discover -s tests
python -m compileall -q src experiments tests
python experiments/validate_paper_algorithm.py --max-n 8
python experiments/validate_week10_timing_outputs.py --run-dir ...
git diff --check
```

Revalidate the Week 9 sorting and recognition pilots to prove that the policy
refactor did not break old experiment outputs.

### Acceptance

- exactly one formal paper timing mode is selected;
- certification, diagnostics, and timing boundaries are explicit;
- Week 9 API and output behavior do not regress;
- contamination pilot is reproducible;
- formal configuration is frozen but not executed;
- documents contain no linear-time claim;
- repository is clean and pushed.

Suggested commit:

```text
Complete Week 10 paper timing study
```

## Final Deliverables

### Code

```text
PaperExecutionPolicy
five fixed execution modes
policy-aware shared paper runner
optional backend commit audit
optional trace recorder
optional operation-counter sink
certified public wrapper
Week 10 contamination runner
Week 10 output validator
```

### Tests

```text
single-control-flow AST guard
cross-mode output differential tests
cross-mode backend-snapshot tests
validation-on/off rollback tests
trace-disabled tests
counter-disabled tests
invalid-mode tests
invalid actual-input certification tests
CSV and manifest tamper tests
```

### Experiment

```text
smoke run
1,500-row contamination pilot
case summary
group summary
validation report
environment record
manifest
runtime-ratio analysis
```

### Documents

```text
docs/design/paper_timing_modes.md
docs/plan/week10_plan.md
docs/progress/week10_progress.md
docs/progress/week10_summary.md
updated docs/design/final_experiment_spec.md
```

## Definition of Done

```text
[x] Step 1/2/3 still has one main loop
[x] all five modes produce identical algorithm output
[x] minimal runs no complete backend validation
[x] minimal records no trace
[x] minimal updates no diagnostic counters
[x] oracle certification is entirely outside timing
[x] every case receives one complete untimed audit
[x] exhaustive n=0..8 passes
[x] all 48 fixed generated cases pass
[x] every contamination-pilot output passes its validator
[x] validation, trace, and counter overhead are quantified
[x] the Week 11 paper timing mode is selected
[x] no linear-time claim is made
[x] full tests, compileall, and diff check pass
```

The main Week 10 result is not simply a faster program. It is an explainable,
reproducible performance-evidence chain that states exactly what is measured,
what is excluded, and what ordinary-list costs remain.
