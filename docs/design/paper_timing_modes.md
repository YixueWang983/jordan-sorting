# Paper Algorithm Timing Modes

Last updated: 2026-07-27

Status: Week 10 Day 1 design contract; modes are designed but not implemented.

## Purpose

The Week 9 ordinary-list paper sorter is correct for oracle-certified valid
inputs, but its current timed path includes correctness and observation work.
This document separates:

```text
paper control flow
ordinary-list backend cost
local safety checks
global correctness audits
trace construction
operation counters
experiment infrastructure
```

The goal is not to prove linear time. It is to make later timing evidence
explicit about what was measured and what was excluded.

## Current Timing Call Graph

Case construction occurs before timing:

```text
generate_sequence()
-> oracle(sequence)
-> reject an invalid actual paper input
-> structure_profile()
-> paper_jordan_diagnostics_valid() once per case
   -> complete invariant callback
   -> deterministic replay
```

The current measured call is:

```text
make_raw_rows()
-> run_timed_algorithm()
-> _time_once()
   -> values = list(sequence)              outside timer
   -> disable GC when initially enabled   outside timer
   -> start = time.perf_counter_ns()
   -> configured paper algorithm
      -> paper_jordan_sort_valid(values)
         -> values = list(seq)             inside timer
         -> _run_paper_jordan_valid()
         -> _run_paper_jordan_state_values()
            -> _initialize_paper_jordan_state_values()
               -> initialize partial order and pair families
               -> record two initialization trace events
               -> partial_order.validate_links()
               -> sibling_backend.validate_invariants()
            -> for i = 4..n:
               -> Step 1
               -> Step 2
               -> Step 3(a)
               -> Step 3(b)
                  -> optional ordinary-list split
                  -> commit_split()
                  -> validate_invariants(require_all_owned=False)
               -> Step 3(c)
         -> state.partial_order.to_list()
   -> end = time.perf_counter_ns()
   -> restore GC state                    outside timer
-> compare output with oracle result      outside timer
-> write CSV/JSON/summary/manifest        outside timer
```

Code locations at the Day 1 baseline:

```text
experiments/run_week7_pilot.py:
    build_cases()              lines 340+
    _time_once()               lines 407+
    make_raw_rows()            lines 508+
    run_pilot()                lines 840+

src/paper_jordan_sort.py:
    paper_jordan_sort_valid()  lines 10+
    _run_paper_jordan_valid()  lines 56+

src/paper_jordan.py:
    initialization             lines 138+
    shared main loop           lines 917+
    Step 1/2                   lines 1005+
    Step 3                     lines 1105+
    stage guards/results       lines 1605+
    _record_trace()            lines 1723+

src/sibling_list_backend.py:
    split planning             lines 268+
    commit_split()             lines 324+
    global validation          lines 446+
```

Line numbers describe commit `7521566` and may move after implementation.
Function names are the stable reference.

## Input Materialization Boundary

The experiment runner first creates a fresh list before starting the timer:

```python
values = list(sequence)
start = time.perf_counter_ns()
result = func(values)
```

The paper public API then performs another materialization inside the timer:

```python
values = list(seq)
```

Therefore the current paper timing contains a second input list copy.

Current algorithm boundaries are not identical:

| Algorithm | Outer copy before timer | Work that creates/copies a list inside timer |
| --- | ---: | --- |
| `python_sort` | yes | `sorted(seq)` creates and sorts the output list |
| `simplified_jordan_reference` | yes | `list(seq)` before oracle/reference work |
| paper ordinary-list sorter | yes | `list(seq)` before paper state initialization |

Day 1 records this asymmetry but does not change it. Day 2/Day 5 must decide
whether formal timing uses public APIs as-is or fixed pre-materialized internal
entry points. The decision must be applied consistently and documented.

## Contamination Classification

| Operation | File/function | Inside timer | Required for output | Debug/instrumentation | Current complexity | Week 10 decision |
| --- | --- | ---: | ---: | ---: | --- | --- |
| outer fresh input copy | `run_week7_pilot._time_once` | no | experiment isolation | no | `O(n)` | keep outside |
| inner paper input copy | `paper_jordan_sort_valid` | yes | API ownership, not control flow | no | `O(n)` | open fairness decision |
| point/state initialization | `paper_jordan._initialize_paper_jordan_state_values` | yes | yes | no | `O(n)` for `PointRef` tuple; fixed first-three setup | keep |
| initialization link audit | `SortedOrderList.validate_links` | yes | no | correctness/debug | `O(3)` at current fixed initialization | remove from minimal |
| initialization backend audit | `OrdinarySiblingListBackend.validate_invariants` | yes | no | correctness/debug | general worst case `O(p^2)`; constant-size state at initialization | remove from minimal |
| predecessor/successor access | `SortedOrderList.predecessor/successor` | yes | yes | no | `O(1)` | keep |
| partial-order insertion | `SortedOrderList.insert_before/after` | yes | yes | local safety included | `O(1)` after anchor | keep |
| sibling boundary insertion | `insert_at_boundary` | yes | yes | no | Python-list reconstruction `O(k)` | keep as ordinary-list cost |
| sibling-list straddle scan | `split_pairs_at_value` | yes | yes for safe split adapter | local safety | `O(k)` | keep |
| ordinary split scan | `split_by_key` | yes | yes | no | `O(k)` | keep |
| split materialization | `commit_split` | yes | yes | no | `O(k)` list copies | keep as ordinary-list cost |
| ownership transfer/rebinding | `commit_split` | yes | yes | local checks included | `O(k)` | keep |
| split-plan type/stale checks | `commit_split`, `_validate_live_split_plan` | yes | safe mutation | local safety | `O(k)` where plan membership is checked | keep |
| live-parent/descendant checks | `_require_live_parent`, `_reject_descendant_parent` | yes | safe ownership | local safety | up to tree depth | keep initially |
| complete commit audit | `commit_split -> validate_invariants(False)` | yes | no | correctness/debug | worst case `O(p^2)` | disable outside checked |
| rollback snapshots | `commit_split` | yes | atomicity | local safety | `O(k)` affected state | keep |
| trace dictionary construction | Step 1/2/3 call sites | yes | no | instrumentation | seven events per completed iteration plus two initialization events | policy-aware; avoid construction when off |
| trace append | `_record_trace` | yes | no | instrumentation | amortized `O(1)` per event | policy-aware |
| metrics dictionary initialization | state initialization | yes | no | instrumentation | `O(number of metrics)` | no-op/minimal representation needed |
| operation-counter updates | Step 1/2/3 and `_record_trace` | yes | no | instrumentation | mostly `O(1)` updates using existing values | policy-aware |
| invariant-check counter | `validate_paper_jordan_state` | no for plain timed API | no | diagnostics | `O(1)` update after full audit | keep outside timing |
| `stage_results` | `_record_stage_result`, `_require_*_stage` | yes | current implementation safety/control state | not trace | `O(1)` per stage | retain in all initial modes |
| final output recovery | `SortedOrderList.to_list` | yes | yes | no | `O(n)` | keep |
| deterministic replay | `validate_paper_jordan_state` | no | no | complete audit | reruns processed prefix and compares state | keep outside |
| backend audit snapshot | diagnostics/replay comparison | no | no | complete audit | `O(p + list items)` | keep outside |
| oracle certification | `build_cases` | no | input contract | experiment correctness | current oracle includes sorting and `O(n^2)` checks | keep outside |
| output comparison | `run_timed_algorithm` | no | experiment correctness | infrastructure | `O(n)` | keep outside |
| CSV/JSON/summary/hash | `run_pilot` writers | no | evidence packaging | infrastructure | output-size dependent | keep outside |

## Important Current Findings

### Global Backend Validation Is Timed

`OrdinarySiblingListBackend.commit_split()` unconditionally runs:

```python
self.validate_invariants(require_all_owned=False)
```

after publishing the staged mutation. `validate_invariants()` scans all live
lists and pairs and follows parent chains for owned finite pairs. Its worst
case is `O(p^2)` for `p` registered pairs. Repeating it after splits can create
an aggregate cost approaching `O(n^3)` in the ordinary-list implementation.

The current backend docstring says the global check does not belong to the
timed path, but the actual call graph shows that it is currently timed. Week
10 must make implementation and documentation agree.

### Trace Is Timed

Initialization records two events. Each completed iteration records seven:

```text
Step 1 neighbor
Step 1 selected pair
Step 2 neighbor
Step 2 selected pair
Step 3(a)
Step 3(b)
Step 3(c)
```

Event dictionaries are built before `_record_trace()` is called. Making
`_record_trace()` a no-op would still pay dictionary-construction cost.

Trace does not control algorithm branches. Stage results, not trace scans,
enforce Step 3 sequencing.

### Counters Are Timed

The metrics dictionary is initialized inside the paper state. Step 1/2/3 and
trace recording update counters inside the timer.

Most counters reuse values already computed by the algorithm. No current
counter introduces a separate structural scan. `invariant_checks` is different:
it is updated only by full diagnostics and remains outside the plain timed API.
It does not count the global commit audits currently performed by the backend.

### Stage Results Must Remain

`stage_results` is used by:

```text
_require_stage_absent
_require_boundary_stage
_require_step3a_stage
_require_step3b_stage
```

It supplies O(1) precondition checks and replaced earlier trace scans.
Consequently it is current algorithm-control/safety bookkeeping, not optional
trace. All initial Week 10 modes retain it. Removing or replacing it would
require a separate design and correctness gate.

### Complete Diagnostics Are Outside Timing

`build_cases()` performs actual-sequence oracle certification and one
`paper_jordan_diagnostics_valid()` call before warm-up/measured timing.
`validate_paper_jordan_state()`, deterministic replay, audit snapshots, full
trace/metric cross-validation, and paper diagnostic metrics therefore remain
outside `_time_once()`.

### Final `to_list()` Is Timed and Required

The sorter must return values in sorted order. `partial_order.to_list()` is the
paper implementation's output recovery and costs `O(n)`. It remains in all
timing modes.

## Checks That Must Remain Inside Execution

The initial policy design keeps:

- point/pair/list type and identity checks needed by the operation;
- next-iteration, orientation, and stage-order checks;
- boundary membership and local sorted-order checks;
- split-plan type, acquired-side, and stale-plan checks;
- pair/list/owner existence and family compatibility;
- checks that acquired/retained items belong to the expected owner;
- descendant-parent/cycle-prevention checks local to the mutation;
- adjacency and local ordering checks for output insertion;
- rollback snapshots and rollback after mutation failure;
- local postconditions required to prevent silent ownership corruption.

These checks protect the mutation being executed. They are not replaced by
post-hoc diagnostics.

## Complete Audits That Move Outside Minimal Timing

- complete pair/list registry scans;
- parent-chain scans for every owned finite pair;
- complete partial-order link scans beyond local insertion checks;
- deterministic replay;
- complete trace payload and ordering audit;
- metrics/trace cross-validation;
- complete backend snapshot comparison.

Every experiment case must still run one complete untimed checked diagnostic
audit on the exact sequence used for timing.

## Fixed Mode Contracts

### `checked`

```text
trace: on
counters: on
complete backend commit validation: on
```

Includes the Week 9 timed behavior. Complete deterministic replay remains
outside timing. Use: correctness-first baseline and contamination comparison.
Not a final timing candidate.

### `instrumented`

```text
trace: on
counters: on
complete backend commit validation: off
```

Retains observation overhead while removing backend-wide commit scans. One
checked diagnostic runs outside timing. Use: estimate global-validation
overhead. Not the preferred final timing mode.

### `trace_only`

```text
trace: on
counters: off
complete backend commit validation: off
```

Keeps trace construction/append and stage results. A checked diagnostic runs
outside timing. Use: estimate trace overhead. Not a final timing candidate.

### `counters_only`

```text
trace: off
counters: on
complete backend commit validation: off
```

Keeps counter updates and stage results. A checked diagnostic runs outside
timing. Use: estimate counter overhead. Not a final timing candidate.

### `minimal`

```text
trace: off
counters: off
complete backend commit validation: off
```

Keeps Step 1/2/3, ordinary-list operations, required local checks,
`stage_results`, rollback, and final output recovery. A checked diagnostic runs
outside timing on the exact case. Use: candidate final paper timing mode only
after cross-mode state equivalence and exhaustive validation pass.

## Cross-Mode Invariants

For the same input, all modes must agree on:

```text
final output
processed_count
pair registry
sibling-list registry
parent ownership
child-list ownership
dummy registration
canonical backend snapshot
```

Permitted differences:

```text
trace contents
metric contents
invariant-check count
```

No mode may change branch decisions or Step 1/2/3 semantics.

## Implementation Constraints for Day 2+

1. Use one immutable `PaperExecutionPolicy` and five fixed registry entries.
2. Keep one `_run_paper_jordan_state_values()` control flow.
3. Do not create checked/minimal copies of the main loop.
4. Do not use monkey patches or mutable global flags.
5. Avoid constructing trace dictionaries when trace is disabled.
6. Avoid metric lookups/updates when counters are disabled.
7. Retain `stage_results` in all initial modes.
8. Preserve the Week 9 default API behavior.
9. Keep oracle certification and complete diagnostics outside timed calls.
10. Validate cross-mode backend equivalence before any performance conclusion.

## Open Design Questions

1. Should policy be passed into the backend constructor, `commit_split()`, or
   both through one state-owned policy?
2. Which explicit local postconditions must replace the safety signal formerly
   supplied by the global post-commit scan before minimal mode is allowed?
3. Should fixed initialization-wide validation be disabled in every
   non-checked mode or retained because its state size is constant?
4. Should formal timing use public APIs, including their inner materialization,
   or pre-materialized internal entry points for all compared algorithms?
5. Are the five modes sufficient, or will interaction effects require another
   trace+counters combination?
6. Should metrics in disabled mode be an empty mapping, zero-filled mapping,
   or unavailable object while preserving diagnostics compatibility?

These questions are intentionally unresolved on Day 1.

## Non-Claim Boundary

Week 10 may quantify instrumentation and audit overhead. It may not claim:

- theoretical linear time;
- implementation of heterogeneous finger trees;
- that minimal mode removes ordinary Python-list scan/copy costs;
- that a small contamination pilot represents all Jordan sequences;
- that faster minimal timing proves an asymptotic bound.

