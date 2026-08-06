# Week 12 Formal Valid-Input Sorting Analysis

Last updated: 2026-08-06

## Main Result

The archived Week 12 experiment is internally valid and reproduces the Week 11
pilot's principal size trend on a larger incremental sample and with twice as
many measured runs per case.

Across the five tested sizes, the median exact-case paper/reference ratio falls
from `3.226x` at `n=32` to `0.567x` at `n=512`. It crosses below `1.0` between
`n=128` and `n=256`, as it did in Week 11. All three within-run ratio series
have the same direction at every size transition in Weeks 11 and 12.

This is not a like-for-like end-to-end speedup claim. The reference algorithm
is timed as its complete oracle-backed reference pipeline. The paper algorithm
is timed only as a pre-certified `minimal` sorting call; oracle certification
and checked diagnostics are outside its timed region. The result is therefore
a comparison of the implemented pipeline scopes, not evidence of superior
asymptotic complexity or a linear-time implementation.

## Evidence and Reproduction

The analysis reads only this immutable run:

```text
results/runs/week12_formal_sorting_v1__run001
```

The run records source commit:

```text
98868b1b705f6d5f22404ee8ad7b88ad7a834f52
```

Reproduce the analysis without rerunning timing:

```bash
python experiments/analyze_week12_formal_sorting.py \
  --run-dir results/runs/week12_formal_sorting_v1__run001 \
  --output-dir docs/analysis
```

The command first reruns the independent Week 12 validator, writes a fresh
validation report outside the archive, and verifies that every archived file
has the same SHA-256 before and after analysis.

Validated evidence:

```text
raw rows:             3,600
case-summary rows:      180
group-summary rows:      45
case-audit rows:          60
raw errors:                0
incorrect outputs:         0
oracle-invalid rows:        0
failed audits:              0
validator valid:         true
```

## Method

The experiment contains 60 oracle-certified valid cases over five sizes. Each
size has one flat case, one nested case, and ten seeded incremental cases.
Every case-algorithm cell contains 20 measured calls after five warm-ups.

The primary runtime for a cell is its median. Size and family summaries give
every generated case equal weight. Ratios are computed within each exact case
before aggregation, rather than by dividing separately aggregated runtimes.

Relative IQR is defined as:

```text
(Q3 - Q1) / median
```

Rows at or above `0.25` are flagged for inspection and remain in the data.
Spearman coefficients are descriptive within each fixed size and use only 12
mixed-family cases.

## Runtime by Size

Median exact-case runtimes are:

| n | Python sort | Reference pipeline | Paper ordinary-list |
| ---: | ---: | ---: | ---: |
| 32 | 0.000791 ms | 0.181 ms | 0.587 ms |
| 64 | 0.001417 ms | 0.586 ms | 1.282 ms |
| 128 | 0.002635 ms | 2.078 ms | 2.815 ms |
| 256 | 0.005208 ms | 7.930 ms | 6.721 ms |
| 512 | 0.010584 ms | 33.014 ms | 18.717 ms |

![Week 12 median runtime by size](week12_runtime_by_size.svg)

Python's built-in sort remains much faster than either research pipeline. The
paper implementation is slower than the reference pipeline at the first three
sizes and faster at the last two under the frozen timing scopes.

## Runtime Ratios

The primary paper/reference result is:

| n | Cases | Paper / reference |
| ---: | ---: | ---: |
| 32 | 12 | 3.226x |
| 64 | 12 | 2.202x |
| 128 | 12 | 1.351x |
| 256 | 12 | 0.851x |
| 512 | 12 | 0.567x |

Across all 60 exact cases, the median ratios are:

```text
paper / reference:       1.351x
paper / Python:      1,117.903x
reference / Python:    784.016x
```

![Week 12 runtime ratios by size](week12_runtime_ratio_by_size.svg)

The logarithmic ratio axis is needed because comparisons with Python sort are
orders of magnitude larger than paper/reference.

Timing-scope boundary: `simplified_jordan_reference` includes oracle
validation, family-tree construction, structural profiling, and reference
output work inside its timed call. The paper path times only
`paper_jordan_sort_valid(..., execution_mode="minimal")` after untimed oracle
certification and checked diagnostics. Consequently, paper/reference ratios
must be described as pipeline-scope comparisons, not end-to-end speedups.

## Family Results

Paper/reference ratios by family and size are:

| Family | n=32 | n=64 | n=128 | n=256 | n=512 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Flat | 2.551x | 1.609x | 0.919x | 0.510x | 0.281x |
| Nested | 2.564x | 1.748x | 1.099x | 0.727x | 0.525x |
| Incremental | 3.282x | 2.217x | 1.358x | 0.860x | 0.570x |

The downward trend appears in all three families. Flat crosses below `1.0` at
`n=128`; nested and incremental cross at `n=256`.

Overall size medians should not be interpreted as a balanced family average.
Ten of the twelve cases at each size are incremental, while flat and nested
each contribute one deterministic case. The family-by-size table is therefore
required beside any overall size result.

## Variability

| Algorithm | Median relative IQR | Maximum | Rows at or above 0.25 |
| --- | ---: | ---: | ---: |
| Python sort | 0.0556 | 0.2520 | 1 |
| Reference pipeline | 0.0119 | 0.0661 | 0 |
| Paper ordinary-list | 0.0152 | 0.0242 | 0 |

The only flagged cell is Python sort on
`incremental_valid_n512_001`, with relative IQR `0.2520`. It is retained.
Research-pipeline cells remain below the threshold. Very short Python calls
remain more exposed to timer granularity and ordinary system activity.

## Measured Time and Pipeline Time

The raw measured calls sum to:

```text
Python sort:          0.004750632 s
Reference pipeline: 10.445239255 s
Paper ordinary-list: 6.919634017 s
All measured calls: 17.369623904 s
```

The frozen pipeline wall-clock is `837.682385541 s`. It covers evidence
reservation, config and environment writes, case generation, oracle
certification, checked diagnostics, warm-ups, measured calls, summary
construction, and CSV writes. It excludes manifest writing and validation.
It is not an algorithm runtime and should not be divided among algorithms.

## Structure and Checked Counters

Within each size, reference runtime has consistently positive descriptive
associations with maximum depth and containment-pair density. The paper
runtime associations are smaller and vary more by size. These coefficients
describe this generated sample only; they do not establish causal structure
effects.

Checked diagnostic counters for sibling scans, list splits, copied items, and
transferred items generally have positive associations with the paper's
minimal runtime. The strongest values occur at `n=32`; coefficients are more
moderate at larger sizes. `paper_invariant_checks` is constant within each
size, so its within-size coefficient is undefined.

The counters and runtimes come from different execution policies by design:
counters are collected by an untimed checked diagnostic, while runtime uses
minimal mode. This avoids instrumentation contamination but limits the result
to a descriptive relationship between input-specific diagnostic work and
minimal-mode timing.

## Week 11 Trend Replication

Week 11 and Week 12 are compared only through within-run exact-case ratios.
Their absolute runtimes are never pooled.

| n | Week 11 paper/reference | Week 12 paper/reference |
| ---: | ---: | ---: |
| 32 | 3.096x | 3.226x |
| 64 | 2.148x | 2.202x |
| 128 | 1.354x | 1.351x |
| 256 | 0.818x | 0.851x |
| 512 | 0.564x | 0.567x |

For paper/reference, paper/Python, and reference/Python:

```text
size-rank Spearman across Week 11 and Week 12: 1.0
matching adjacent-size directions:             4 / 4
same side of ratio 1.0:                        5 / 5
```

This is evidence that the pilot's directional pattern was reproducible under
the larger Week 12 protocol. It is not a cross-run equality test, a pooled
estimate, or a substitute for broader family and size coverage.

## Limitations and Non-Claims

Week 12 does not establish:

- linear-time Jordan sorting;
- asymptotic complexity from five input sizes;
- performance of level-linked trees or heterogeneous finger trees;
- recognition behavior on invalid inputs;
- equal-weight representation of the three valid families;
- generality beyond the flat, nested, and incremental generators;
- like-for-like end-to-end superiority over the reference pipeline;
- causal effects from structure or checked-counter correlations;
- comparability of absolute Week 11 and Week 12 timings.

The implemented paper algorithm maintains the paper-facing Step 1/2/3 control
flow and sorts from its partial order, but it deliberately uses ordinary Python
lists instead of the theoretical linear-time data structures.

## Conclusion

Week 12 confirms correctness, evidence integrity, and a stable directional
runtime pattern for the ordinary-list implementation on oracle-certified valid
inputs. The central result is the reproducible decline in the paper/reference
pipeline-scope ratio, including the same `n=128` to `n=256` crossover as the
pilot. The thesis should present this as an implementation and evaluation
result with explicit scope boundaries, not as a proof of the paper's
theoretical complexity.
