# Week 10 Timing Baseline

Last updated: 2026-07-27

Status: Week 10 Day 1 baseline frozen.

## Repository Baseline

```text
HEAD:
7521566e035702eede7e81e28727de6e31ecb67e

origin/main:
7521566e035702eede7e81e28727de6e31ecb67e

commit subject:
Add Week 10 timing study plan

git dirty before validation:
false
```

The Week 9 algorithm/certification checkpoint immediately below this
documentation-only commit is:

```text
cc9f65606ff9ba176b60889ed3ad72c872d43376
Enforce paper input certification
```

## Environment

```text
Python:
3.12.4 | packaged by Anaconda, Inc.

implementation:
CPython

compiler:
Clang 14.0.6

platform:
macOS-26.5-arm64-arm-64bit

kernel:
Darwin 25.5.0

machine:
arm64

logical CPUs:
8

perf_counter implementation:
mach_absolute_time()

perf_counter resolution:
4.166666666666667e-08 seconds

perf_counter monotonic:
true

perf_counter adjustable:
false

GC initial state:
enabled
```

`platform.processor()` and the existing environment recorder report the CPU
model only as `arm`; no more specific model is claimed in this checkpoint.

## Baseline Verification

### Unit and Build Checks

```text
python -m unittest discover -s tests:
    Ran 324 tests
    OK

python -m compileall -q src experiments tests:
    passed

git diff --check:
    passed
```

### Paper Algorithm Validator

```text
python experiments/validate_paper_algorithm.py --max-n 8:
    all_valid = true
    exhaustive valid permutations = 2,074
    generated valid cases = 48
```

Exhaustive distribution:

| n | Valid permutations |
| ---: | ---: |
| 0 | 1 |
| 1 | 1 |
| 2 | 2 |
| 3 | 6 |
| 4 | 16 |
| 5 | 50 |
| 6 | 144 |
| 7 | 462 |
| 8 | 1,392 |

Generated distribution:

```text
flat_valid: 4
nested_valid: 4
incremental_valid: 40
sizes: 16, 32, 64, 128
```

## Fresh Week 9 Pilot Reproduction

The Day 1 baseline was generated outside the repository:

```bash
python experiments/run_week9_pilot.py \
  --run-id week10_d1_baseline \
  --run-dir /tmp/week10_d1_baseline
```

The `/tmp` outputs are not committed.

Sorting:

```text
raw rows: 108
case-summary rows: 36
group-summary rows: 27
validator valid: true
validator errors: []
```

Recognition:

```text
raw rows: 180
case-summary rows: 60
group-summary rows: 42
validator valid: true
validator errors: []
```

The generated environment record confirms:

```text
git commit: 7521566e035702eede7e81e28727de6e31ecb67e
git dirty: false
seed: 20260727
algorithm-order seed: 20268646
case-order seed: 20262270
warm-up runs: 1
measured runs: 3
```

## Current Paper Median Timing

These medians reproduce the current checked-like Week 9 implementation. They
are environment-specific baseline observations, not final performance
evidence.

| Family | n | Median case time (ns) | Approx. ms |
| --- | ---: | ---: | ---: |
| `flat_valid` | 8 | 135,583 | 0.136 |
| `flat_valid` | 16 | 294,250 | 0.294 |
| `flat_valid` | 32 | 616,417 | 0.616 |
| `nested_valid` | 8 | 142,958 | 0.143 |
| `nested_valid` | 16 | 323,750 | 0.324 |
| `nested_valid` | 32 | 707,041 | 0.707 |
| `incremental_valid` | 8 | 197,396 | 0.197 |
| `incremental_valid` | 16 | 473,458 | 0.473 |
| `incremental_valid` | 32 | 1,389,354 | 1.389 |

Deterministic families have one case per size; incremental medians aggregate
two cases. Each case median is based on only three measured runs. The table is
appropriate for freezing the starting point, not for inferential analysis.

## Actual Timing Boundary

### Inside Timer

- second paper input materialization;
- paper state/point initialization;
- two initialization trace events;
- initialization link and backend invariant scans;
- Step 1/2/3 control flow;
- ordinary-list search, insertion, split, list materialization, and ownership
  transfer;
- local operation checks and rollback snapshots;
- full backend invariant scan after every committed split;
- seven trace events per completed iteration;
- operation-counter updates;
- `stage_results` recording and stage guards;
- final `partial_order.to_list()`.

### Outside Timer

- generator execution;
- oracle certification of the actual sequence;
- structure profile;
- complete paper diagnostics once per case;
- deterministic replay and backend snapshot comparison;
- the first fresh input list copy in `_time_once()`;
- output comparison with oracle-sorted values;
- GC state lookup/disable/restore;
- CSV/JSON writing, summaries, environment data, hashes, and manifest.

## Day 1 Findings

1. Current Week 9 paper timing includes backend global validation.
2. It includes trace construction and append.
3. It includes operation-counter updates.
4. It does not include deterministic replay.
5. It does not include oracle certification.
6. It includes a second input materialization after the timer starts.
7. `stage_results` cannot currently be disabled safely because Step 3 uses it
   for O(1) sequencing and boundary-result preconditions.
8. Final `to_list()` belongs inside timing because it produces the sorter
   output.
9. Local operation checks protect the mutation being executed; global audits
   rescan complete registries/parent chains and may move outside minimal
   timing only if equivalent untimed evidence and sufficient local
   postconditions remain.
10. Week 9 timing cannot support final performance conclusions because the
    measured value combines ordinary-list work with trace, counters,
    initialization audits, and repeated post-split global scans.

## Open Questions

1. Where should the immutable execution policy live so the runner and backend
   cannot disagree?
2. What local post-commit checks are sufficient before the global scan can be
   disabled safely?
3. Should the fixed-size initialization audits remain in minimal mode?
4. How should input-copy fairness be defined across Python sort, reference,
   and paper implementations?
5. What disabled-metrics representation preserves diagnostics compatibility
   without paying update cost?
6. Will the five-mode matrix expose interaction effects clearly enough?

## Day 2 Handoff

Day 2 has not started. It may implement execution policies only after review
of:

```text
docs/design/paper_timing_modes.md
docs/analysis/week10_timing_baseline.md
```

Day 2 must preserve one Step 1/2/3 control flow and the Week 9 default API.

