# Documentation

This folder is organized by document type so the thesis notes, plans, progress records, and papers do not get mixed together.

## Design Documents

Path:

```text
docs/design/
```

Use this folder for technical design notes and implementation-facing definitions.

Current files:

- `oracle_and_test_generation.md`
  Week 1 design notes for the oracle, upper/lower pairs, rank intervals, laminarity checks, generator families, and JSON test-case format.

- `notation.md`
  Reusable terminology for the project and thesis.

- `simplified_algorithm_design.md`
  Design document for the simplified Jordan-sorting reference implementation.

- `structural_examples.md`
  Concrete flat / nested / invalid structural examples used for debug and thesis drafts.

- `experimental_questions_and_metrics.md`
  Week 7 research questions, metric definitions, and interpretation boundaries.

- `benchmark_protocol.md`
  Timing, correctness-audit, aggregation, and frozen Week 11 paper-pilot
  protocol.

- `final_scope_and_contributions.md`
  Week 8 supervisor-confirmed scope freeze, contribution claims, non-contributions, success
  criteria, and supervisor decision record.

- `theory_to_implementation_mapping.md`
  Week 8 mapping from theoretical Jordan-sorting concepts to current code,
  explicit gaps, and non-implemented algorithmic structures.

- `final_experiment_spec.md`
  Week 8 frozen experiment questions, variables, correctness fields,
  aggregation rules, CSV semantics, and non-claims.

- `paper_algorithm_ordinary_list.md`
  Week 9 implementation-facing reconstruction of the 1990 paper algorithm,
  including state, parity, sibling-list ownership, Step 1/2/3 pseudocode,
  invariants, and an initial worked trace.

- `paper_timing_modes.md`
  Week 10 timing call graph, contamination classification, fixed five-mode
  execution-policy architecture, checked-only complete backend audit boundary,
  independently controlled trace/counters, always-on local split safety, and
  non-claim contract.

## Progress Documents

Path:

```text
docs/progress/
```

Use this folder for weekly checklists and weekly summaries.

Current files:

- `week1_progress.md`
  Checklist-style Week 1 progress tracker.

- `week1_summary.md`
  Completed Week 1 summary, including implemented components, experiment configuration, validation results, limitations, and next steps.

- `week2_summary.md`
  Week 2 completion summary, including design/skeleton boundary and Week3 handoff.

- `week3_progress.md`
  Week 3 execution note log for contract audit and debug utility rollout.

- `week3_summary.md`
  Week 3 completion summary and Week 4 handoff.

- `week4_notes.md`
  Week 4 Day 1 notes and scope freeze record.

- `week4_summary.md`
  Week 4 completion summary and reference-pipeline handoff notes.

- `week5_progress.md`
  Week 5 execution log and checkpoint record.

- `week6_progress.md`
  Week 6 execution log and verification checkpoint.

- `week6_summary.md`
  Week 6 completion summary and Week 7 handoff constraints.

- `week7_progress.md`
  Week 7 execution log for metrics, instrumentation, audit, and pilot analysis.

- `week7_summary.md`
  Week 7 completion summary and Week 8 handoff constraints.

- `week8_summary.md`
  Week 8 scope freeze, benchmark hardening, generator audit v2, dry-run
  validation, and Week 9 gate.

- `week9_progress.md`
  Week 9 daily implementation log from the executable specification through
  the complete ordinary-list loop, adversarial state audit, and integration
  pilot.

- `week9_summary.md`
  Week 9 completion summary, correctness evidence, pilot results, timing
  boundary, and Week 10 handoff.

- `week10_progress.md`
  Week 10 daily execution record. Day 1 freezes the baseline, Day 2 implements
  immutable policy plumbing, Day 3 separates complete backend scans from
  always-on local split safety, Day 4 decouples trace and counters, and Day 5
  adds safe certification plus the contamination runner/validator. Day 6 runs,
  validates, and analyzes the full 1,500-row contamination pilot. Day 7 selects
  `minimal` and freezes the unexecuted Week 11 gate.

- `week10_summary.md`
  Week 10 final timing-mode decision, correctness/timing boundary,
  contamination evidence, and Week 11 handoff.

- `week11_progress.md`
  Week 11 daily execution record through the archived pilot, reproducible
  analysis, and frozen Week 12 gate.

- `week11_summary.md`
  Week 11 validated run003 evidence, runtime findings, limitations, process
  decision, and Week 12 handoff.

## Analysis Documents

Path:

```text
docs/analysis/
```

Current Week 11 analysis:

- `week11_pilot_analysis.md`
  Reproducible runtime, ratio, variability, structure, and checked-counter
  analysis derived from immutable run003 evidence.

## Plan Documents

Path:

```text
docs/plan/
```

Use this folder for schedule, thesis scope, and planning documents.

Current files:

- `README.md`
- `four_month_roadmap.md`
- `week2_plan.md`
- `week3_plan.md`
- `week4_plan.md`
- `week5_plan.md`
- `week6_plan.md`
- `week7_plan.md`
- `week8_plan.md`
- `refined_thesis_direction_after_week8.md`
- `week9_plan.md`
- `week10_plan.md`
- `week11_plan.md`
- `thesis_scope_and_research_questions.pdf`

Planned files:

- `thesis_scope_and_research_questions.md`
  Markdown version of the approved thesis scope, research questions, goals, planned contributions, implementation scope, and experimental scope.

## Papers

Path:

```text
docs/papers/
```

Use this folder for source papers and paper-specific notes.

Current files:

- `finger_search_trees_jordan_sorting.pdf`
- `simplified_linear_jordan_sorting.pdf`
- `README.md`

## Backlog

Path:

```text
docs/backlog/
```

Use this folder for future work ideas that should not block the current weekly plan.

Current files:

- `future_work_todo.md`

## Analysis

Path:

```text
docs/analysis/
```

Use this folder for small pilot interpretations and thesis-facing analysis
drafts that are derived from generated results.

Current files:

- `week7_pilot_interpretation.md`
- `week7_pilot_auto_report.md`
- `week10_timing_baseline.md`
- `week10_contamination_pilot.md`
- `week10_component_overhead_table.csv`
- `week10_mode_overhead_table.csv`
- `week10_runtime_ratio_by_size.csv`
- `week10_runtime_ratio_by_family.csv`
- `week10_runtime_ratio_by_family_size.csv`
- `week10_runtime_ratio_by_size.svg`
- `week10_observation_ratio_by_size.svg`
- `week11_machine_preflight_v1_m1.md`
  Preserved preflight record for the unexecuted historical v1 M1 gate.

- `week11_machine_preflight_v2_m4.md`
  Preserved v2 M4 identity, source baseline, and power/load snapshot from the
  historical machine-bound design.

- `week11_machine_baseline_v1_m1.json`
  Preserved structured v1 M1 identity.

- `week11_machine_baseline_v2_m4.json`
  Preserved structured M4 identity from the historical v2 gate. Neither
  baseline contains a serial number or hardware UUID.

## Thesis Drafts

Path:

```text
docs/thesis/
```

Use this folder for thesis-facing prose drafts promoted from implementation and
experiment notes.

Current files:

- `experimental_methodology_draft.md`
- `implementation_draft.md`

## Other Files

- `notes.md`
  General notes that have not yet been promoted into a structured design or plan document.

- `week1_todo.pdf`
  Original Week 1 TODO PDF copied into the project.
