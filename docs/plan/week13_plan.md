# Week 13 Plan: Thesis Synthesis and Claim Audit

Last updated: 2026-08-06

Status: claim-to-evidence table reviewed; Implementation draft complete and awaiting review.

## Goal

Week 13 converts the reviewed implementation and immutable Week 12 evidence
into thesis-facing prose, tables, and figures. It is a synthesis week, not an
algorithm-development or experiment-execution week.

## Authoritative Inputs

```text
results/runs/week12_formal_sorting_v1__run001/
docs/analysis/week12_formal_sorting_analysis.md
docs/analysis/week12_*.csv
docs/analysis/week12_*.svg
docs/design/paper_algorithm_ordinary_list.md
docs/design/final_scope_and_contributions.md
docs/design/final_scope_amendment_paper_ordinary_list.md
```

The archive is read-only. Analysis may be regenerated only through the live
validator and `experiments/analyze_week12_formal_sorting.py`.

Scope authority is layered rather than interchangeable:

- `final_scope_and_contributions.md` is the historical supervisor decision
  accepted on 2026-07-24;
- `final_scope_amendment_paper_ordinary_list.md` is the current technical
  scope for implementation and evaluation claims;
- `paper_algorithm_ordinary_list.md` specifies the implemented control flow;
- the Week 12 report and artifacts are the authority for empirical claims.

The historical statement that sorted output comes from
`oracle_result["sorted"]` applies to the reference pipeline, not to
`paper_jordan_sort_valid`.

## Tasks

1. [x] Build and review the claim-to-evidence table before drafting chapters.
2. [x] Draft the implementation chapter from the paper-facing Step 1/2/3 design,
   ordinary-list backend, invariants, and deterministic replay audit.
3. Draft the experimental-method chapter from the frozen protocol, timing
   boundaries, correctness certification, evidence contract, and validator.
4. Draft the results chapter using the Week 12 size, family, ratio,
   variability, structure, and counter artifacts.
5. Include the Week 11/Week 12 ratio-trend replication without pooling
   absolute timings across executions.
6. Audit all wording for pipeline-scope, ordinary-list, non-causal,
   non-asymptotic, and non-linear-time boundaries.
7. Keep recognition results in their own subsection and do not infer them from
   the valid-input sorting experiment.
8. Distinguish every reference-pipeline statement from every independent
   paper-core statement, especially sorted-output provenance.

## Fixed Non-Goals

Week 13 must not:

- rerun Week 12 formal timing or create a new execution ID;
- modify `run001` or any manifest-bound evidence;
- change the paper algorithm or ordinary-list backend;
- add new generators, sizes, seeds, or timing repetitions;
- pool Week 11 and Week 12 absolute runtimes;
- claim a like-for-like paper/reference end-to-end speedup;
- claim linear time or infer asymptotic complexity from five sizes;
- treat exploratory correlations as causal evidence.

## Completion Gate

Week 13 is complete when:

- methods, implementation, results, and limitations drafts exist;
- every headline number is traceable to immutable evidence;
- tables preserve family balance and timing-scope context;
- recognition and valid-input sorting remain distinct;
- reference and paper output provenance are never conflated;
- the claim audit contains no unsupported linear-time, asymptotic, or causal
  statement;
- all existing validators and tests remain green without a formal rerun.
