# Week 12 Summary

Last updated: 2026-08-06

## Goal

Week 12 upgraded the validated Week 11 pilot into one formal, thesis-facing
experiment for oracle-certified valid-input sorting. It froze the protocol,
implemented and reviewed a dedicated runner and validator, executed one run,
archived immutable evidence, and produced a reproducible analysis.

## Completed Work

Week 12 completed:

- a frozen 60-case valid-input sorting protocol;
- a dedicated runner with untimed certification and checked diagnostics;
- `minimal` paper timing and complete reference-pipeline timing;
- fail-closed environment, scheduling, summary, wall-clock, and hash checks;
- an independent validator that regenerates all cases and diagnostics;
- one formal execution, `week12_formal_sorting_v1__run001`;
- immutable `3,600 / 180 / 45 / 60` evidence;
- built-in, independent, and live analysis validation;
- reproducible correctness, runtime, ratio, variability, structure, counter,
  and Week 11 trend-comparison artifacts;
- two deterministic SVG figures;
- a frozen Week 13 thesis-synthesis handoff.

The public formal execution entry was disabled after evidence archival.
`run001` is permanently retired and must not be modified or rerun.

## Evidence

Authoritative archive:

```text
results/runs/week12_formal_sorting_v1__run001
```

Execution record:

```text
source commit:          98868b1b705f6d5f22404ee8ad7b88ad7a834f52
raw rows:               3,600
case summaries:           180
group summaries:           45
checked case audits:        60
errors:                      0
incorrect outputs:           0
failed audits:               0
built-in validation:      true
independent validation:   true
live analysis validation: true
```

## Findings

The median exact-case paper/reference ratio falls across every tested size:

```text
n=32:  3.226x
n=64:  2.202x
n=128: 1.351x
n=256: 0.851x
n=512: 0.567x
```

The ratio crosses below `1.0` between `n=128` and `n=256`, reproducing the
Week 11 pilot pattern. All three ratio series match Week 11's direction at all
four adjacent-size transitions. The comparison uses within-run ratios only;
Week 11 and Week 12 absolute timings are not pooled.

Python sort remains orders of magnitude faster. Only one of 180
case-algorithm cells reaches relative IQR `0.25`, and it belongs to Python
sort. No reference or paper cell reaches that threshold.

The family-specific downward trend is visible for flat, nested, and
incremental cases. Since incremental cases make up ten of twelve cases at each
size, family-by-size results must accompany overall size medians.

## Interpretation Boundary

The paper/reference ratio compares different implemented timing scopes. The
reference call includes its complete oracle-backed structural pipeline. The
paper call times only pre-certified minimal sorting; oracle certification and
checked diagnostics remain outside timing. It is not a like-for-like
end-to-end speedup or an asymptotic result.

The ordinary-list backend does not implement the paper's theoretical
level-linked or heterogeneous finger-tree structures. Week 12 therefore makes
no linear-time claim. Structure and counter relationships are descriptive,
not causal.

Recognition remains a separate experiment and is not inferred from this
valid-input sorting evidence.

## Reproduction

```bash
python experiments/validate_week12_formal_sorting_outputs.py \
  --run-dir results/runs/week12_formal_sorting_v1__run001 \
  --report-json /tmp/week12_validation.json

python experiments/analyze_week12_formal_sorting.py \
  --run-dir results/runs/week12_formal_sorting_v1__run001 \
  --output-dir docs/analysis
```

Both commands read existing evidence. Neither command runs formal timing.

## Verification

```text
focused Week 12 analysis tests:  8 passed
full unit suite:                537 passed
exhaustive valid permutations: 2,074 passed
fixed generated cases:            48 passed

Week 12 live validator:         valid, 3,600 / 180 / 45 / 60
Week 11 archived validator:     valid, 1,050 / 105 / 45 / 35
Week 10 archived validator:     valid, 1,500 / 100 / 60
Week 9 sorting validator:       valid, 108 / 36 / 27
Week 9 recognition validator:   valid, 180 / 60 / 42

analysis CSV and SVG checks:     passed
run001 archive hashes:           unchanged
compileall and diff checks:      passed
```

## Handoff

Week 13 is frozen as thesis-facing synthesis and claim audit. It may convert
the validated Week 12 artifacts into methods, implementation, results, and
limitations sections. It must not rerun formal timing, alter archived evidence,
extend the algorithm, merge recognition into sorting, or strengthen the
ordinary-list observations into theoretical claims.

The detailed handoff is:

```text
docs/plan/week13_plan.md
```
