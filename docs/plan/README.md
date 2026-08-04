# Thesis Plan

This folder stores the approved thesis scope and research-question documents.

- `thesis_scope_and_research_questions.pdf`
  Approved draft thesis plan for the Jordan-sorting project, including goals, research questions, planned contributions, implementation scope, and experimental scope.

- `thesis_scope_and_research_questions.md`
  Planned Markdown companion to the approved PDF. This should be created from the approved scope, not invented from memory.

- `four_month_roadmap.md`
  Compressed 3-4 month execution plan for the thesis implementation and writing schedule. It defines the minimum 12-week deliverable, the 16-week high-quality target, phase gates, risks, fallback options, and the immediate next coding task.

- `week2_plan.md`
  Detailed Week 2 execution plan. It focuses on notation, simplified algorithm design scope, family-tree data structures, structural metrics, and a clearly marked reference skeleton.

- `week3_plan.md`
  Week 3 execution plan for converting the Week 2 skeleton into a more explicit
  reference pipeline with stronger experiment support.

- `week4_plan.md`
  Week 4 execution plan for building an algorithm-facing reference pipeline, adding
  differential checks, and preparing seminar-oriented Week 4 outputs.
- `week5_plan.md`
  Week 5 execution plan for debugging and validating the simplified-reference
  experimental workflow, and preparing thesis-facing narrative artifacts.
- `week6_plan.md`
  Week 6 execution plan for experimental revalidation, result interpretation,
  and thesis-facing evidence packing.
- `week7_plan.md`
  Week 7 execution plan for experiment-design hardening, structural metric
  clarification, operation counters, generator audit, and pilot analysis.
- `week8_plan.md`
  Week 8 execution plan for scope freeze, final experiment specification,
  benchmark-runner hardening, generator audit v2, dry runs, and thesis drafts.

- `refined_thesis_direction_after_week8.md`
  Post-Week-8 scope revision and Weeks 9-16 plan. It makes the ordinary-list
  reconstruction of the 1990 paper algorithm the core implementation target,
  fixes the purity and data-structure boundaries, and delays formal performance
  experiments until correctness gates pass.

- `week9_plan.md`
  Detailed daily execution plan for specifying, implementing, validating, and
  lightly integrating the ordinary-list reconstruction of the 1990 algorithm.

- `week10_plan.md`
  Daily plan for decomposing paper-algorithm timing contamination, adding fixed
  execution policies without duplicating the main loop, running a controlled
  overhead pilot, and freezing the Week 11 timing gate.

- `week11_plan.md`
  Daily plan for the immutable paper-sorting integration runner, fail-closed
  validator, formal preflight, single 1,050-row pilot, evidence archive,
  analysis, and Week 12 gate freeze.

- `week12_plan.md`
  Three-checkpoint plan for the frozen 3,600-row formal valid-input sorting
  experiment: runner/validator review, one immutable evidence execution, and
  reproducible thesis-facing analysis.

The frozen, unexecuted Week 12 valid-input sorting choices are in:

```text
experiments/week12_experiment_gate.py
```

The canonical machine-independent Week 11 integration-pilot values are in:

```text
experiments/week11_experiment_protocol.py
```

Per-run identity and machine evidence are defined in
`experiments/week11_execution_context.py`. The unexecuted v1 M1 and v2 M4 gate
files remain historical records.
