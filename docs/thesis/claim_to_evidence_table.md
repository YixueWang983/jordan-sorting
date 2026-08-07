# Claim-to-Evidence Table

Last updated: 2026-08-06

Status: Week 13 drafting authority.

## Purpose

This table controls which implementation, method, result, and limitation claims
may enter the thesis. It is written before the four thesis chapters so that
prose cannot silently become stronger than the available evidence.

During drafting, every material statement should carry a claim ID such as
`I-02`, `M-05`, or `R-02`. IDs may be removed from the final submitted prose
only after the chapter-level claim audit confirms that the wording and evidence
locator remain unchanged.

The existing `implementation_draft.md` and `experimental_methodology_draft.md`
predate the Week 12 formal evidence. They are drafting inputs, not evidence
authorities, until they are revised against this table.

## Evidence Authority

Evidence authority depends on claim type:

1. implementation facts use current source code plus the reviewed algorithm
   specification;
2. protocol facts use immutable `run001/config.json` and the frozen gate;
3. execution and provenance facts use immutable `run001/manifest.json`,
   `environment.json`, and the independent validator;
4. quantitative findings use the generated Week 12 CSV artifacts, which are
   reproducible from the immutable archive;
5. scope and non-claims use the dated ordinary-list scope amendment together
   with the historical supervisor decision.

README files, weekly summaries, and thesis drafts are navigation or narrative
documents. They are not primary evidence for numerical claims.

## Implementation Claims

| ID | Permitted thesis claim | Primary evidence locator | Required boundary |
| --- | --- | --- | --- |
| I-01 | The simplified reference pipeline is oracle-backed and returns oracle-derived sorted output. | [`src/simplified_jordan.py`](../../src/simplified_jordan.py): `simplified_jordan_sort`, `BACKEND_REFERENCE`, `oracle_result["sorted"]`, and the `_build_result(...)` return paths; [scope amendment](../design/final_scope_amendment_paper_ordinary_list.md), “Oracle-Backed Reference Pipeline” | Applies only to `simplified_jordan_sort` / `simplified_jordan_reference`, not to the paper core. |
| I-02 | For a pre-certified valid input of length at least three, the paper core recovers output from its maintained partial order. | [`src/paper_jordan_sort.py`](../../src/paper_jordan_sort.py): `paper_jordan_sort_valid`, `state.partial_order.to_list()`; [paper specification](../design/paper_algorithm_ordinary_list.md), “Public Return Contracts” | Say “independently recovers sorted order from maintained state”; do not say the core recognizes arbitrary input. |
| I-03 | The pure paper core does not call the oracle or consume `oracle_result["sorted"]`. | [`src/paper_jordan_sort.py`](../../src/paper_jordan_sort.py): imports and `paper_jordan_sort_valid`; [`src/certified_paper_jordan.py`](../../src/certified_paper_jordan.py): wrapper boundary | Oracle certification may occur before the core and correctness comparison may occur after it. |
| I-04 | The implementation executes one shared paper-facing Step 1/2/3 control flow with partial-order and sibling-list state. | [`src/paper_jordan.py`](../../src/paper_jordan.py): `_run_paper_jordan_state_values`; [paper specification](../design/paper_algorithm_ordinary_list.md) | Call it an implementation-facing reconstruction, not a verbatim reproduction of every omitted paper detail. |
| I-05 | Sibling lists and split ownership are implemented with ordinary Python lists and explicit local safety, rollback, and invariant checks. | [`src/sibling_list_backend.py`](../../src/sibling_list_backend.py); [scope amendment](../design/final_scope_amendment_paper_ordinary_list.md), “Backend Boundary” | Ordinary-list behavior is the evaluated implementation, not the theoretical linear-time backend. |
| I-06 | Diagnostics and production sorting share the same core runner; full state audit and deterministic replay are outside the minimal timed path. | [`src/paper_jordan_sort.py`](../../src/paper_jordan_sort.py): `_run_paper_jordan_valid`, `paper_jordan_diagnostics_valid`; [`src/paper_jordan.py`](../../src/paper_jordan.py): `validate_paper_jordan_state` | Do not describe diagnostics runtime as paper sorting runtime. |
| I-07 | Fixed execution policies independently control complete backend validation, trace recording, and operation counters without changing Step 1/2/3 semantics. | [`src/paper_execution_policy.py`](../../src/paper_execution_policy.py); [timing modes](../design/paper_timing_modes.md) | `minimal` still includes ordinary-list work, local safety, stage results, and output recovery. |
| I-08 | The safe public wrapper uses the oracle only to enforce the valid-input precondition before calling the paper core. | [`src/certified_paper_jordan.py`](../../src/certified_paper_jordan.py): `certified_paper_jordan_sort` | Certification is not independent recognition and must not be timed as part of the minimal paper call. |
| I-09 | The project does not implement level-linked search trees, heterogeneous finger trees, or the theoretical linear-time split/update backend. | [scope amendment](../design/final_scope_amendment_paper_ordinary_list.md), “Backend Boundary”; [paper specification](../design/paper_algorithm_ordinary_list.md), complexity boundary | This is a fixed limitation, not unfinished evidence that may be ignored in the results chapter. |

## Experimental-Method Claims

| ID | Permitted thesis claim | Primary evidence locator | Required boundary |
| --- | --- | --- | --- |
| M-01 | Week 12 evaluates oracle-certified valid-input sorting and keeps recognition separate. | [`run001/config.json`](../../results/runs/week12_formal_sorting_v1__run001/config.json): `scope`, `recognition_separate` | Do not infer invalid-input recognition performance from Week 12. |
| M-02 | The protocol uses sizes 32, 64, 128, 256, and 512 with 60 total cases. | [`run001/config.json`](../../results/runs/week12_formal_sorting_v1__run001/config.json): `sizes`, `case_count` | The five sizes do not establish asymptotic complexity. |
| M-03 | Each size contains one flat, one nested, and ten seeded incremental cases. | [`run001/config.json`](../../results/runs/week12_formal_sorting_v1__run001/config.json): `valid_families`, `randomized_cases`; [`case_audit.csv`](../../results/runs/week12_formal_sorting_v1__run001/case_audit.csv): `family`, `n`, `case_id` | Family composition is intentionally unbalanced; overall size medians mainly reflect incremental cases. |
| M-04 | The compared algorithms are Python sort, the simplified reference pipeline, and the paper ordinary-list implementation. | [`run001/config.json`](../../results/runs/week12_formal_sorting_v1__run001/config.json): `algorithms` | Their timed scopes are not identical. |
| M-05 | Each exact case-algorithm cell uses five warm-ups and twenty measured calls. Every call receives a fresh list before `perf_counter_ns` timing, and the caller's GC state is restored after the call. | [`run001/config.json`](../../results/runs/week12_formal_sorting_v1__run001/config.json): `warmup_runs`, `measured_runs`; [`experiments/run_week11_pilot.py`](../../experiments/run_week11_pilot.py): `_time_once_algorithm`, reused by Week 12; [`case_summary.csv`](../../results/runs/week12_formal_sorting_v1__run001/case_summary.csv): `measured_run_count` | Repeated calls estimate one cell; they are not twenty independent input cases. Correctness extraction and comparison occur after the timed call. |
| M-06 | Paper timing uses `minimal`; its oracle certification and checked diagnostic are outside timing. | [`run001/config.json`](../../results/runs/week12_formal_sorting_v1__run001/config.json): `paper_execution_mode`, `audit_execution_mode`; [formal analysis](../analysis/week12_formal_sorting_analysis.md), “Runtime Ratios” | Always state this boundary beside a paper/reference ratio. |
| M-07 | The reference algorithm is timed as its complete oracle-backed reference pipeline. | [`experiments/run_week11_pilot.py`](../../experiments/run_week11_pilot.py): algorithm registry and timed call reused by Week 12; [formal analysis](../analysis/week12_formal_sorting_analysis.md), “Runtime Ratios” | Therefore paper/reference is a pipeline-scope comparison, not an end-to-end speedup. |
| M-08 | Case order and algorithm order are deterministic under frozen seeds. | [`run001/config.json`](../../results/runs/week12_formal_sorting_v1__run001/config.json): `case_order_seed`, `algorithm_order_seed`; [`raw.csv`](../../results/runs/week12_formal_sorting_v1__run001/raw.csv): execution-position fields | Do not claim that scheduling removes all system noise. |
| M-09 | The primary cell statistic is the median; Q1, Q3, IQR, mean, and standard deviation are retained. | [`case_summary.csv`](../../results/runs/week12_formal_sorting_v1__run001/case_summary.csv); [`week12_case_runtime_metrics.csv`](../analysis/week12_case_runtime_metrics.csv) | Size/family summaries aggregate exact-case medians, not raw repeated calls. |
| M-10 | Runtime ratios are computed within each exact case before equal-weight aggregation. | [`experiments/analyze_week12_formal_sorting.py`](../../experiments/analyze_week12_formal_sorting.py): `build_case_ratio_records`, `summarize_ratios`; [`week12_runtime_ratios.csv`](../analysis/week12_runtime_ratios.csv) | Do not divide two independently pooled runtime distributions. |
| M-11 | The immutable archive contains 3,600 raw rows, 180 case summaries, 45 group summaries, and 60 checked audits. | [`run001/manifest.json`](../../results/runs/week12_formal_sorting_v1__run001/manifest.json): `row_counts`; [`week12_live_validation_report.json`](../analysis/week12_live_validation_report.json) | Counts establish evidence completeness, not algorithmic correctness by themselves. |
| M-12 | The independent validator regenerates cases and diagnostics, recomputes schedules and summaries, and verifies hashes. | [`experiments/validate_week12_formal_sorting_outputs.py`](../../experiments/validate_week12_formal_sorting_outputs.py); [`week12_live_validation_report.json`](../analysis/week12_live_validation_report.json) | Say “validated under the repository contract,” not formally verified in the proof-theoretic sense. |
| M-13 | The Week 12 formal evidence was produced by execution `week12_formal_sorting_v1__run001` from source commit `98868b1` on Apple M4/arm64 with 16 GB memory, macOS 26.6, and CPython 3.12.4. The recorded Git tree was clean and matched remote `main`; the machine used AC power with low-power mode disabled, low and stable load, and no readiness warnings. | [`run001/environment.json`](../../results/runs/week12_formal_sorting_v1__run001/environment.json): execution, source, benchmark environment, Git, power, and readiness fields; [`run001/manifest.json`](../../results/runs/week12_formal_sorting_v1__run001/manifest.json): `execution_id`, `source_commit` | This is one execution in one recorded environment. Absolute runtimes must not be generalized to other hardware or software environments. |

## Quantitative Result Claims

| ID | Permitted thesis claim | Primary evidence locator | Required boundary |
| --- | --- | --- | --- |
| R-01 | All 3,600 measured rows belong to 60 exact cases that each passed one untimed checked audit before timing. Every row has valid oracle certification, correct output, and no recorded error; all 180 case summaries are correct and error-free, and all 60 case audits pass. | [`week12_correctness_audit_totals.csv`](../analysis/week12_correctness_audit_totals.csv): all failure-count fields equal zero; [`week12_live_validation_report.json`](../analysis/week12_live_validation_report.json): `valid=true` | This is empirical correctness over the frozen cases, not a proof for every Jordan sequence. The row-level `audit_passed` field copies the case-level outcome and does not represent 3,600 independent audits. |
| R-02 | The median exact-case paper/reference ratio declines from 3.226 at `n=32` to 0.567 at `n=512`. | [`week12_runtime_ratios.csv`](../analysis/week12_runtime_ratios.csv): `scope=size`, `comparison=paper/reference`, `median_ratio` | Include all five sizes or link the full table; call it a pipeline-scope ratio. |
| R-03 | The paper/reference ratio is above 1 through `n=128` and below 1 at `n=256` and `n=512`. | [`week12_runtime_ratios.csv`](../analysis/week12_runtime_ratios.csv): size rows for `paper/reference` | “Faster” is allowed only as “lower timed call under the frozen pipeline scopes,” never as a general end-to-end claim. |
| R-04 | Median case runtimes at `n=512` are 0.010584 ms for Python sort, 33.014 ms for the reference pipeline, and 18.717 ms for the paper implementation. | [`week12_runtime_by_size.csv`](../analysis/week12_runtime_by_size.csv): `n=512`, `median_case_time_ns` | Name the machine/run context and timing scopes when reporting absolute time. |
| R-05 | Across the 60 exact cases, median paper/Python and reference/Python ratios are 1,117.903 and 784.016. | [`week12_runtime_ratios.csv`](../analysis/week12_runtime_ratios.csv): `scope=overall` | “Orders of magnitude larger” is permitted; do not interpret the overall median as an asymptotic rate. |
| R-06 | The paper/reference ratio decreases with size within flat, nested, and incremental families. | [`week12_runtime_ratios.csv`](../analysis/week12_runtime_ratios.csv): `scope=family_size`, `comparison=paper/reference` | Flat and nested have one deterministic case per size; incremental has ten. |
| R-07 | Flat crosses below ratio 1 at `n=128`; nested and incremental cross at `n=256`. | [`week12_runtime_ratios.csv`](../analysis/week12_runtime_ratios.csv): family-size rows | Describe only the tested cases and sizes. |
| R-08 | One of 180 case-algorithm cells reaches relative IQR 0.25; it is a Python-sort cell. No reference or paper cell reaches the threshold. | [`week12_case_runtime_metrics.csv`](../analysis/week12_case_runtime_metrics.csv): `relative_iqr`; [`week12_analysis_summary.json`](../analysis/week12_analysis_summary.json): `high_relative_iqr_rows`, `maximum_relative_iqr` | The threshold is an analysis flag, not a universal outlier rule; the row remains included. |
| R-09 | Captured measured calls total 17.369623904 s: 0.004750632 s Python, 10.445239255 s reference, and 6.919634017 s paper. | [`week12_measured_elapsed.csv`](../analysis/week12_measured_elapsed.csv) | Sums are measured-call totals, not whole-experiment elapsed time. |
| R-10 | The frozen pipeline wall-clock is 837.682385541 s. | [`run001/manifest.json`](../../results/runs/week12_formal_sorting_v1__run001/manifest.json): `experiment_elapsed_ns`, `experiment_elapsed_scope` | It includes generation, diagnostics, warm-ups, and CSV work and excludes manifest writing/validation; it is not algorithm runtime. |
| R-11 | Week 11 and Week 12 have identical size-rank ordering and adjacent-size direction for all three within-run ratio series. | [`week12_week11_trend_summary.csv`](../analysis/week12_week11_trend_summary.csv): `ratio_spearman=1.0`, `matching_transition_count=4`, `transition_count=4` | This is directional replication, not pooled estimation or equality of runs. |

## Quantitative Evidence Chain

The derived CSV is the numerical citation target. The archived source permits
independent recomputation, while the figure and report are presentation layers.

| Claim IDs | Immutable source | Derived numerical table | Figure or report section |
| --- | --- | --- | --- |
| R-01 | [`raw.csv`](../../results/runs/week12_formal_sorting_v1__run001/raw.csv), [`case_summary.csv`](../../results/runs/week12_formal_sorting_v1__run001/case_summary.csv), [`case_audit.csv`](../../results/runs/week12_formal_sorting_v1__run001/case_audit.csv) | [`week12_correctness_audit_totals.csv`](../analysis/week12_correctness_audit_totals.csv) | [Formal analysis, “Evidence and Reproduction”](../analysis/week12_formal_sorting_analysis.md) |
| R-02, R-03, R-05 | [`case_summary.csv`](../../results/runs/week12_formal_sorting_v1__run001/case_summary.csv) | [`week12_runtime_ratios.csv`](../analysis/week12_runtime_ratios.csv) | [`week12_runtime_ratio_by_size.svg`](../analysis/week12_runtime_ratio_by_size.svg); [Formal analysis, “Runtime Ratios”](../analysis/week12_formal_sorting_analysis.md) |
| R-04 | [`case_summary.csv`](../../results/runs/week12_formal_sorting_v1__run001/case_summary.csv) | [`week12_runtime_by_size.csv`](../analysis/week12_runtime_by_size.csv) | [`week12_runtime_by_size.svg`](../analysis/week12_runtime_by_size.svg); [Formal analysis, “Runtime by Size”](../analysis/week12_formal_sorting_analysis.md) |
| R-06, R-07 | [`case_summary.csv`](../../results/runs/week12_formal_sorting_v1__run001/case_summary.csv) | [`week12_runtime_ratios.csv`](../analysis/week12_runtime_ratios.csv): `scope=family_size` | [Formal analysis, “Family Results”](../analysis/week12_formal_sorting_analysis.md) |
| R-08 | [`case_summary.csv`](../../results/runs/week12_formal_sorting_v1__run001/case_summary.csv) | [`week12_case_runtime_metrics.csv`](../analysis/week12_case_runtime_metrics.csv); [`week12_analysis_summary.json`](../analysis/week12_analysis_summary.json) | [Formal analysis, “Variability”](../analysis/week12_formal_sorting_analysis.md) |
| R-09 | [`raw.csv`](../../results/runs/week12_formal_sorting_v1__run001/raw.csv) | [`week12_measured_elapsed.csv`](../analysis/week12_measured_elapsed.csv) | [Formal analysis, “Measured Time and Pipeline Time”](../analysis/week12_formal_sorting_analysis.md) |
| R-10 | [`manifest.json`](../../results/runs/week12_formal_sorting_v1__run001/manifest.json) | [`week12_analysis_summary.json`](../analysis/week12_analysis_summary.json): `pipeline_wall_clock_seconds` | [Formal analysis, “Measured Time and Pipeline Time”](../analysis/week12_formal_sorting_analysis.md) |
| R-11 | Week 11 [`case_summary.csv`](../../results/runs/week11_pilot_v1__run003/case_summary.csv) and Week 12 [`case_summary.csv`](../../results/runs/week12_formal_sorting_v1__run001/case_summary.csv), each manifest-bound | [`week12_week11_ratio_trends.csv`](../analysis/week12_week11_ratio_trends.csv); [`week12_week11_trend_summary.csv`](../analysis/week12_week11_trend_summary.csv) | [Formal analysis, “Week 11 Trend Replication”](../analysis/week12_formal_sorting_analysis.md) |

## Exploratory Claims

These claims may appear only with “descriptive,” “exploratory,” or equivalent
language.

| ID | Permitted thesis claim | Primary evidence locator | Required boundary |
| --- | --- | --- | --- |
| E-01 | Within the twelve cases at each size, reference runtime has positive descriptive associations with depth and containment density. | [`week12_structure_runtime_relationships.csv`](../analysis/week12_structure_runtime_relationships.csv): reference rows and Spearman fields | Mixed and unbalanced families; no causal or asymptotic interpretation. |
| E-02 | Paper runtime associations with structural metrics are smaller or more variable than the reference associations in this sample. | [`week12_structure_runtime_relationships.csv`](../analysis/week12_structure_runtime_relationships.csv): paper/reference rows | This is a comparison of observed coefficients, not evidence that paper runtime is structure-independent. |
| E-03 | Checked sibling scans, splits, copied items, and transferred items generally have positive within-size associations with minimal paper runtime. | [`week12_paper_counter_runtime_relationships.csv`](../analysis/week12_paper_counter_runtime_relationships.csv): `runtime_spearman` | Counters come from untimed checked diagnostics while runtime comes from minimal mode; association is not a cost decomposition or causal estimate. |
| E-04 | `paper_invariant_checks` has no within-size Spearman value because it is constant within each size. | [`week12_paper_counter_runtime_relationships.csv`](../analysis/week12_paper_counter_runtime_relationships.csv): invariant rows | Undefined correlation must not be represented as zero correlation. |

## Required Limitations and Prohibited Claims

| ID | Required limitation or prohibited wording | Authority | Required treatment |
| --- | --- | --- | --- |
| L-01 | No linear-time claim. | [scope amendment](../design/final_scope_amendment_paper_ordinary_list.md), “Non-Claims” | Every complexity discussion must state that the backend uses ordinary lists. |
| L-02 | No asymptotic-complexity conclusion from five sizes. | [`run001/config.json`](../../results/runs/week12_formal_sorting_v1__run001/config.json): five `sizes`; [formal analysis](../analysis/week12_formal_sorting_analysis.md), “Limitations and Non-Claims” | Use “observed trend over tested sizes,” not Big-O inference. |
| L-03 | Do not call paper/reference a like-for-like end-to-end speedup. | [scope amendment](../design/final_scope_amendment_paper_ordinary_list.md), “Evaluation Boundary” | State both timing scopes wherever the ratio is interpreted. |
| L-04 | Do not claim that the paper core uses oracle-sorted output. | [`src/paper_jordan_sort.py`](../../src/paper_jordan_sort.py); [scope amendment](../design/final_scope_amendment_paper_ordinary_list.md) | Restrict oracle-output statements to the reference pipeline. |
| L-05 | Do not claim that Week 12 evaluates recognition. | [`run001/config.json`](../../results/runs/week12_formal_sorting_v1__run001/config.json): `recognition_separate=true` | Recognition requires its separate evidence and subsection. |
| L-06 | Do not pool Week 11 and Week 12 absolute runtimes. | [`week12_week11_ratio_trends.csv`](../analysis/week12_week11_ratio_trends.csv); [`week12_analysis_summary.json`](../analysis/week12_analysis_summary.json): `week11_absolute_timings_pooled=false` | Compare within-run ratios and direction only. |
| L-07 | Do not claim causal effects from structure or counters. | [formal analysis](../analysis/week12_formal_sorting_analysis.md), “Structure and Checked Counters” | Label all such coefficients descriptive and exploratory. |
| L-08 | Do not treat the three generators as representative of all Jordan-sequence distributions. | [scope amendment](../design/final_scope_amendment_paper_ordinary_list.md), “Non-Claims” | State the controlled-construction and family-balance limitations. |
| L-09 | Do not imply that theoretical level-linked or heterogeneous finger-tree structures were implemented. | [scope amendment](../design/final_scope_amendment_paper_ordinary_list.md), “Backend Boundary” | Separate high-level paper control flow from the missing theoretical backend. |

## Chapter Use Order

1. The Implementation chapter should use `I-*` and `L-01`, `L-04`, `L-09`.
2. Experimental Method should use `M-*` and state `L-03`, `L-05`, `L-06`.
3. Results should use `R-*`; exploratory subsections may use `E-*` only with
   the required qualifiers.
4. Limitations should explicitly cover every `L-*` row rather than relying on
   a generic “future work” paragraph.
5. Before a chapter is marked complete, search every number and comparative
   adjective back to one row in this table and its primary evidence locator.
