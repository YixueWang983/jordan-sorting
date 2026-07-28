# Week 10 Timing-Contamination Pilot

Last updated: 2026-07-28

Status: Day 6 full pilot completed and validated; Day 7 selected `minimal` for
Week 11 paper timing.

## Purpose

This pilot measures how much the ordinary-list paper implementation's runtime
changes when complete backend validation, trace recording, and operation
counters are disabled in controlled combinations.

It does not measure a heterogeneous finger-tree implementation and does not
establish linear-time complexity.

## Run Evidence

```text
run_id:
    week10_contamination_full_20260728

source commit:
    c195a2f3c79df3ebd6f2e7205a5c70bcd956362e

source worktree:
    clean

families:
    flat_valid
    nested_valid
    incremental_valid

sizes:
    32, 64, 128, 256

cases:
    20

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
```

The generated run contains:

```text
raw rows:           1,500
case-summary rows:    100
group-summary rows:    60
errors:                 0
incorrect outputs:      0
failed audits:          0
validator valid:     true
```

The raw CSV SHA-256 recorded by the manifest is:

```text
f200988d37d7e9789275ec8af4321fb21bef425ae270024e230ebc67a1b74e41
```

The complete evidence run is archived under:

```text
results/runs/week10_contamination_full_20260728/
```

The committed archive contains `raw.csv`, both summaries, `config.json`,
`environment.json`, `manifest.json`, and `validation_report.json`. The
analysis command runs the validator again against these live files before
reading `case_summary.csv`; a stale earlier `valid = true` report cannot
authorize modified evidence.

Selected evidence hashes:

| File | SHA-256 |
| --- | --- |
| `raw.csv` | `f200988d37d7e9789275ec8af4321fb21bef425ae270024e230ebc67a1b74e41` |
| `case_summary.csv` | `2b81b5440180c4bc6082bedd4c1f151680ec9c350aad4894012a209d3d9a797c` |
| `group_summary.csv` | `e00a51165be4a65e90c5e8e375380511b2867e0336275e7cfa59674271b23ff7` |
| `config.json` | `e54e5a0492fb580d8676486ccbe483aaf7bf4557797210208df983e71f4cf772` |
| `environment.json` | `2303a766e46a0204abc23dc014b2c8e3818fa8ce6314fc986fbc66a343ae4cc0` |
| `manifest.json` | `d96b736cc654e32b4ef4ff65c45220a90cee44465d7c27b68e46c567dfaa9e8b` |
| `validation_report.json` | `006c0c62a07373287069349bfb71828aa27d94a973daa6cd4d998bfc1340aff0` |

## Aggregation Method

Each execution mode is first summarized by the median of its 15 measured runs
for one case. Slowdown ratios are then calculated within that case using
`minimal` as the baseline.

The tables below report medians and quartiles across equal-weighted cases.
There are 20 cases in total: four flat, four nested, and twelve incremental
cases. Because the frozen experiment deliberately includes three incremental
cases per size, the overall table gives incremental cases more weight. The
family table is therefore also reported separately.

## Component Overhead

| Component | Comparison | Median overhead | Median ratio | Q1-Q3 ratio |
| --- | --- | ---: | ---: | ---: |
| Complete backend validation | checked / instrumented | 0.510 ms | 1.578x | 1.009x-3.779x |
| Trace recording | trace_only / minimal | 0.240 ms | 1.102x | 1.091x-1.114x |
| Operation counters | counters_only / minimal | 0.027 ms | 1.013x | 1.007x-1.018x |
| Trace and counters combined | instrumented / minimal | 0.300 ms | 1.126x | 1.115x-1.135x |

The wide validation IQR shows that complete backend validation does not add a
uniform constant factor. Its effect depends strongly on the case structure
and input size.

## Scaling by Input Size

The values below are median case-level ratios relative to `minimal`.
Each size contains five cases: one flat, one nested, and three incremental.
The size median therefore gives incremental cases three of the five
observations and must not be interpreted as a family-balanced result.

| n | checked | instrumented | trace_only | counters_only |
| ---: | ---: | ---: | ---: | ---: |
| 32 | 1.510x | 1.133x | 1.111x | 1.014x |
| 64 | 2.488x | 1.129x | 1.111x | 1.017x |
| 128 | 4.239x | 1.122x | 1.093x | 1.013x |
| 256 | 7.989x | 1.092x | 1.083x | 1.007x |

![Week 10 slowdown ratios by input size](week10_runtime_ratio_by_size.svg)

The checked-mode ratio increases sharply with `n`, while the trace and counter
ratios remain comparatively stable. This supports the conclusion that
backend-wide correctness validation can mask the runtime of the ordinary-list
paper control flow at larger tested sizes.

The zoomed figure below removes checked mode so that the smaller observation
costs remain visible.

![Week 10 observation overhead by input size](week10_observation_ratio_by_size.svg)

The checked-mode family-by-size breakdown confirms which cases drive the
overall size median:

| Family | n=32 | n=64 | n=128 | n=256 |
| --- | ---: | ---: | ---: | ---: |
| flat_valid | 1.165x | 1.168x | 1.160x | 1.152x |
| nested_valid | 1.129x | 1.139x | 1.114x | 1.090x |
| incremental_valid | 1.548x | 2.591x | 4.287x | 8.428x |

The corresponding reproducible data is stored in
`week10_runtime_ratio_by_family_size.csv`.

## Differences by Family

The values below aggregate all four tested sizes within each family.

| Family | checked | instrumented | trace_only | counters_only |
| --- | ---: | ---: | ---: | ---: |
| flat_valid | 1.162x | 1.155x | 1.128x | 1.008x |
| nested_valid | 1.121x | 1.115x | 1.096x | 1.009x |
| incremental_valid | 3.435x | 1.126x | 1.100x | 1.016x |

The large checked slowdown is concentrated in the incremental cases. Because
checked and instrumented differ in complete backend validation policy, this is
consistent with the incremental cases reaching validation-sensitive backend
states more often. The pilot does not record enough per-commit detail to claim
a complete causal explanation, so this remains an implementation-level
interpretation rather than a structural theorem.

## Main Findings

1. Complete backend validation materially contaminates timing for larger and
   incremental cases. At `n=256`, the median checked slowdown is about `7.99x`.
2. Trace recording adds a stable cost of roughly `10%` at the case level.
3. Operation counters add a much smaller median cost of roughly `1.3%`.
4. Enabling trace and counters together adds a median slowdown of about
   `1.126x`; the five-mode design therefore successfully separates most of the
   observation cost.
5. Removing instrumentation changes measured runtime substantially, but
   `minimal` still includes ordinary-list materialization, local safety checks,
   `stage_results`, and output recovery.

## Interpretation Boundary

The permitted conclusion from this pilot is:

> Removing correctness and debug instrumentation substantially changes the
> measured runtime of the ordinary-list implementation, and complete backend
> validation can dominate checked execution for larger tested inputs.

The pilot does not support any of the following claims:

- `minimal` proves linear-time Jordan sorting;
- the ordinary-list backend has the paper's asymptotic data-structure bounds;
- these three generator families represent all valid Jordan sequences;
- one macOS run is sufficient for final cross-environment performance claims.

Day 7 selected `minimal` for paper timing while retaining one complete
`checked` diagnostic and oracle certification outside timing. The frozen,
unexecuted Week 11 gate is recorded in
`experiments/week11_experiment_gate.py`.

## Reproduction

```bash
python experiments/run_week10_timing_contamination.py \
  --full \
  --run-id week10_contamination_full_20260728 \
  --run-dir results/runs/week10_contamination_full_20260728

python experiments/validate_week10_timing_outputs.py \
  --run-dir results/runs/week10_contamination_full_20260728

python experiments/analyze_week10_contamination.py \
  --run-dir results/runs/week10_contamination_full_20260728 \
  --case-overheads-csv \
    results/runs/week10_contamination_full_20260728/case_overheads.csv \
  --mode-table-csv docs/analysis/week10_mode_overhead_table.csv \
  --component-table-csv docs/analysis/week10_component_overhead_table.csv \
  --size-ratios-csv docs/analysis/week10_runtime_ratio_by_size.csv \
  --family-ratios-csv docs/analysis/week10_runtime_ratio_by_family.csv \
  --family-size-ratios-csv \
    docs/analysis/week10_runtime_ratio_by_family_size.csv \
  --ratio-figure docs/analysis/week10_runtime_ratio_by_size.svg \
  --observation-figure docs/analysis/week10_observation_ratio_by_size.svg
```
