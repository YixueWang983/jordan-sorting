# Week 13 Plan: Thesis Synthesis and Claim Audit

Last updated: 2026-08-06

Status: frozen handoff; not started.

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
```

The archive is read-only. Analysis may be regenerated only through the live
validator and `experiments/analyze_week12_formal_sorting.py`.

## Tasks

1. Draft the implementation chapter from the paper-facing Step 1/2/3 design,
   ordinary-list backend, invariants, and deterministic replay audit.
2. Draft the experimental-method chapter from the frozen protocol, timing
   boundaries, correctness certification, evidence contract, and validator.
3. Draft the results chapter using the Week 12 size, family, ratio,
   variability, structure, and counter artifacts.
4. Include the Week 11/Week 12 ratio-trend replication without pooling
   absolute timings across executions.
5. Build a claim-to-evidence table linking every quantitative statement to a
   CSV field, figure, report section, and archived source file.
6. Audit all wording for pipeline-scope, ordinary-list, non-causal,
   non-asymptotic, and non-linear-time boundaries.
7. Keep recognition results in their own subsection and do not infer them from
   the valid-input sorting experiment.

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
- the claim audit contains no unsupported linear-time, asymptotic, or causal
  statement;
- all existing validators and tests remain green without a formal rerun.
