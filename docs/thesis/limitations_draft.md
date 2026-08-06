# Limitations Draft

Last updated: 2026-08-06

Status: Week 13 Limitations chapter draft; awaiting review.

## Scope of the Limitations

The implementation and formal experiment establish a reproducible
ordinary-list reconstruction of the paper-facing sorting control flow and its
behavior on the frozen valid inputs. They do not establish every property of
the theoretical 1990 algorithm or every behavior of Jordan-sequence inputs.
The following boundaries determine how the implementation and empirical
results may be interpreted.

## Paper Reconstruction and Backend Fidelity

The implemented paper core follows the reconstructed Step 1/2/3 control flow,
maintains a partial sorted order and sibling-list ownership state, and recovers
its final output from that maintained order. Some executable details, including
the geometric endpoint used by Step 3(c) and the odd-index `z_1` output-anchor
adjustment, resolve omissions in the short 1990 description through
counterexamples, the related 1986 account, mirrored cases, and repository
validation. This supports a paper-facing reconstruction, but not a claim that
the implementation is the unique verbatim interpretation of every omitted
detail. [I-04]

More importantly, the backend uses ordinary Python lists. Sibling-list scans,
front insertions, slicing, list materialization, and ownership rebinding may
require work proportional to the represented list. The implementation does not
instantiate level-linked search trees, heterogeneous finger trees, or the
theoretical dynamic split/update backend. Consequently, its observed runtime
cannot be presented as an implementation of the paper's linear-time data
structures or as evidence that the ordinary-list program runs in linear time.
[L-01, L-09]

Sources: [ordinary-list algorithm specification](../design/paper_algorithm_ordinary_list.md),
"Complexity Boundary," and [current scope amendment](../design/final_scope_amendment_paper_ordinary_list.md),
"Backend Boundary" and "Non-Claims."

## Tested Sizes and Asymptotic Interpretation

The formal protocol contains five input sizes: `32`, `64`, `128`, `256`, and
`512`. The decreasing paper/reference ratio and the observed crossing between
the tested sizes `128` and `256` describe this finite set of measurements.
Five size points do not identify a Big-O class, prove a crossover outside the
tested constructions, or establish the asymptotic behavior of either pipeline.
The result must therefore remain an observed trend over the tested sizes rather
than an asymptotic-complexity conclusion. [L-02]

Sources: Week 12 [`config.json`](../../results/runs/week12_formal_sorting_v1__run001/config.json)
and [formal analysis](../analysis/week12_formal_sorting_analysis.md),
"Limitations and Non-Claims."

## Non-Equivalent Timing Scopes

The paper/reference ratio does not compare equivalent end-to-end pipelines.
`simplified_jordan_reference` is timed as its complete oracle-backed reference
pipeline, including oracle validation, family-tree construction, structural
profiling, and reference output work. The paper measurement times only the
pre-certified ordinary-list core in `minimal` mode. Oracle certification and
the full checked diagnostic occur before paper timing. [L-03]

The ratio is therefore useful as a reproducible comparison of the two frozen
timed scopes, but it is not a like-for-like end-to-end speedup. In particular,
the ratios below one at `n=256` and `n=512` mean only that the paper timed call
has the lower exact-case median under these scopes. They do not establish
general superiority of the paper pipeline or its theoretical algorithm.
[R-03, L-03]

Sources: [Experimental Method](experimental_methodology_draft.md), "Compared
Implementations," and [Results](results_draft.md), "Matched-Case Runtime
Ratios."

## Output Provenance and Recognition

The two sorting paths have different output provenance. The reference pipeline
returns an oracle-derived sorted list. In contrast,
`paper_jordan_sort_valid` does not read `oracle_result["sorted"]`; for inputs of
length at least three, it returns values traversed from
`state.partial_order.to_list()`. Oracle-derived-output statements must therefore
remain restricted to the reference path. [L-04]

The paper core also assumes a pre-certified valid input. The public
`certified_paper_jordan_sort` wrapper invokes the oracle to enforce that
precondition before calling the core, but certification is outside the timed
paper call and does not make the core a recognition algorithm. Week 12 contains
only oracle-certified valid-input sorting cases and explicitly records
`recognition_separate=true`. It cannot support claims about invalid-input
recognition accuracy, failure reasons, or recognition runtime. [L-04, L-05]

Sources: [`paper_jordan_sort.py`](../../src/paper_jordan_sort.py),
[`certified_paper_jordan.py`](../../src/certified_paper_jordan.py), and Week 12
[`config.json`](../../results/runs/week12_formal_sorting_v1__run001/config.json).

## Case Construction and Generality

The formal experiment contains sixty controlled cases from three generators.
At each size, the sample contains one flat case, one nested case, and ten seeded
incremental cases. It is therefore intentionally unbalanced, and the ten
incremental cases have the greatest influence on each overall size median.
[M-03, L-08]

These constructions expose selected flat, nested, and incremental patterns;
they are not a representative sample of all Jordan-sequence distributions.
The all-correct result is empirical evidence for the frozen cases, not a proof
for every valid Jordan sequence. Generalization to other valid constructions,
other family balances, or larger sizes is not established by this experiment.
[R-01, L-08]

Sources: Week 12 [`config.json`](../../results/runs/week12_formal_sorting_v1__run001/config.json),
[`week12_runtime_ratios.csv`](../analysis/week12_runtime_ratios.csv), and the
[scope amendment](../design/final_scope_amendment_paper_ordinary_list.md),
"Non-Claims."

## Execution Environment and Cross-Week Replication

The absolute Week 12 runtimes come from one execution on the recorded Apple M4
and CPython 3.12.4 environment. Warm-ups, repeated calls, randomized scheduling,
and environment checks reduce selected sources of measurement noise, but one
run on one machine does not establish hardware- or software-independent
absolute time. [M-13]

Week 11 and Week 12 also used distinct executions. Their absolute runtimes are
not pooled. The replication analysis forms ratios within each run and compares
size ordering, adjacent-size direction, and position relative to ratio one.
Matching directions support reproducibility of the observed ratio pattern, but
they do not prove equality between runs or provide a pooled performance
estimate. [R-11, L-06]

Sources: Week 12 [`environment.json`](../../results/runs/week12_formal_sorting_v1__run001/environment.json),
[`week12_week11_ratio_trends.csv`](../analysis/week12_week11_ratio_trends.csv),
and [`week12_analysis_summary.json`](../analysis/week12_analysis_summary.json),
`week11_absolute_timings_pooled=false`.

## Exploratory Structure and Counter Relationships

The reported Spearman coefficients use twelve mixed-family cases within each
size. Their family composition is unbalanced, and the sample is too small and
controlled to identify causal structural effects. The coefficients describe
associations in the generated cases only; they do not show that depth,
containment, or family membership causes a runtime change. [L-07, L-08]

The operation counters introduce an additional scope difference. They are
collected by an untimed `checked` diagnostic, whereas paper runtime comes from
the `minimal` call. Positive counter/runtime associations are therefore not a
causal cost decomposition of the timed implementation. The undefined
within-size coefficient for constant `paper_invariant_checks` must likewise
remain undefined rather than being reported as zero. [E-03, E-04, L-07]

Sources: [`week12_structure_runtime_relationships.csv`](../analysis/week12_structure_runtime_relationships.csv)
and [`week12_paper_counter_runtime_relationships.csv`](../analysis/week12_paper_counter_runtime_relationships.csv).

## Runtime Variability and Statistical Reach

Each exact case-algorithm cell contains twenty measured calls, summarized by
its median and median-of-halves IQR. These repeated calls characterize timing
variation for a fixed generated case; they are not twenty independent input
samples. Median and IQR reduce the influence of isolated fluctuations but do
not remove persistent system effects. The single cell at or above the study's
relative-IQR inspection threshold remains included, and the evidence does not
identify its cause. [M-05, M-09, R-08]

The overall ratios are medians across exact-case ratios. They summarize the
frozen case set and its unbalanced family composition, not a population
parameter for all valid Jordan sequences. Absolute runtime and ratio precision
should consequently be reported only to the level needed to reproduce the
archived tables, without implying broader statistical certainty.

## Consequences for the Thesis Conclusions

Within these limits, the thesis may conclude that the ordinary-list paper core
independently recovers sorted output for the frozen oracle-certified cases;
that the evidence and diagnostics for those cases validate successfully; and
that the paper/reference pipeline-scope ratio declines across the five tested
sizes with the same directional pattern in Week 11 and Week 12. It may also
report the explicitly exploratory associations preserved in the analysis.

The thesis may not convert those observations into claims of linear time,
asymptotic complexity, theoretical-backend performance, end-to-end speedup,
recognition behavior, causal structural effects, representative sampling, or
hardware-independent absolute runtime.

## Claim Coverage

This chapter explicitly covers limitations `L-01` through `L-09`. It also
preserves the execution, correctness, variability, and exploratory boundaries
attached to `M-05`, `M-09`, `M-13`, `R-01`, `R-03`, `R-08`, `R-11`, `E-03`, and
`E-04`. No new empirical result is introduced.
