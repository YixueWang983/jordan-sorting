# Jordan Sorting

Implementation and experimental evaluation of a simplified Jordan-sorting framework.

This repository is part of a master's thesis preparation project. The long-term goal is to study and implement a simplified reference version of Jordan sorting, then compare it with ordinary sorting baselines and explain the gap between a straightforward implementation and the theoretical linear-time framework.

## Current Status

Week 1, Week 2, Week 3, and Week 4 are complete.

Week 5 verification, Week 6 experimental interpretation, Week 7 pilot
experiment design hardening, and Week 8 formal-experiment preparation are
complete for this stage.

The repository now contains the first reproducible experimental loop:

```text
generate sequence -> oracle checks valid/invalid -> save JSON case -> run baselines -> write experiment CSV
```

Implemented so far:

- correctness oracle for upper/lower laminarity checks,
- controlled valid and invalid test-instance generators,
- JSON test-case save/load and dataset generation pipeline,
- baseline sorting algorithms,
- repeated timing helper,
- Week 1 baseline experiment runner,
- committed Week 1 baseline CSV results,
- unit tests for oracle, generators, baselines, and experiment runner.

The full Week 1 summary is in [docs/progress/week1_summary.md](docs/progress/week1_summary.md).

Week 2 completed the simplified-reference phase:

- [docs/design/notation.md](docs/design/notation.md) defines candidate sequences, valid Jordan sequences, pair families, rank intervals, laminarity, family trees, sibling lists, and split terminology.
- [docs/design/simplified_algorithm_design.md](docs/design/simplified_algorithm_design.md) defines the reference-skeleton scope, API contract, invalid-input behavior, family-tree representation, structural stats contract, trace format, error policy, and non-claims.

Week 2 Day 5 is now complete: `simplified_jordan_sort(seq)` in [src/simplified_jordan.py](src/simplified_jordan.py) is a reference skeleton that:

- runs the oracle,
- returns oracle-sorted output,
- builds upper/lower family trees for valid candidates,
- emits structural stats,
- records an execution trace,
- marks invalid candidates without raising,
- and clearly sets `implementation` to `"reference_skeleton"`.

Week 3 is now complete, with:

- `family_tree_to_debug_lines(tree)` helper and structural examples,
- optional structural columns in `run_small_tests.py` (`--with-structure`),
- experimental summary/audit scripts for structural coverage,
- and stable documented scope boundaries for the reference skeleton.

Week 4 is now complete, with:

- `simplified_jordan_reference` 的实验接入（`--week4-reference`）和独立输出策略；
- `week4_reference_results.csv` 的可复现生成；
- 参考 pipeline 在 `3675` 行原始实验中的 `error=""` 与 `sorted_correct=True` 前置检查通过。

Week 5 completed the first thesis-facing validation chain.  
Week 6 completed revalidation, interpretation, and handoff: result reruns, error checks, structural-field checks, and documentation sync.

Week 7 completed experiment-design hardening:

- mathematically clearer containment/crossing metrics,
- experiment-only operation counters,
- generator coverage audit,
- warm-up/median/IQR pilot benchmark protocol,
- and a small pilot analysis with case-level and group-level summaries.

Week 8 completed the supervisor-confirmed scope freeze and formal-experiment
gate:

- final scope, contribution, and non-contribution documents;
- theory-to-code mapping for implemented and missing Jordan-sorting pieces;
- hardened benchmark runner with run directories, manifests, and output validation;
- generator coverage audit v2 with parity sizes, generation metadata, hashes, and duplicate-case summaries;
- dry-run validation for the Week 9 formal experiment gate.
- the reference-framework boundary was confirmed by the supervisor on
  2026-07-24.

Week 9 has implemented and independently validated the ordinary-list
reconstruction of the high-level 1990 paper algorithm through Day 6:

- the existing `simplified_jordan_reference` remains a separate baseline;
- the new core must recover output from a maintained partial sorted order;
- the new core may not use oracle-sorted output, a global rank map, or full
  sorting;
- `PaperJordanState` initializes `z1`, `z2`, `z3`, `P2`, `P3`, both dummy
  roots, and their sibling-list ownership;
- predecessor/successor boundary selection supports family dummies,
  processed same-family incident pairs, and the odd-index `z1` adjustment;
- increasing/decreasing Step 3(a) supports singleton-list creation and legal
  sibling-boundary insertion;
- increasing/decreasing Step 3(b) supports skipped, one-sided, and two-sided
  split/ownership transfer;
- increasing/decreasing Step 3(c) uses geometric child endpoints and the
  odd-index `z1` output-anchor adjustment;
- `paper_jordan_sort_valid(seq)` now runs the complete ordinary-list paper
  control flow for pre-certified valid inputs;
- the public sorting API and diagnostic API share one internal main loop;
- full state audits can run after every processed prefix outside timed paths;
- `validate_paper_algorithm.py` exhaustively validates through `n=8` and also
  checks reproducible generated cases through `n=128`;
- heterogeneous finger trees and a linear-time claim remain out of scope.

## Project Structure

```text
src/
  oracle.py
  generators.py
  baselines.py
  stats.py
  family_tree.py
  jordan_operations.py
  instrumentation.py
  simplified_jordan.py
  partial_sorted_list.py
  sibling_list_backend.py
  paper_jordan.py
  paper_jordan_sort.py

tests/
  test_oracle.py
  test_generators.py
  test_baselines.py
  test_run_small_tests.py
  test_family_tree.py
  test_stats.py
  test_simplified_jordan.py
  test_jordan_operations.py
  test_instrumentation.py
  test_generator_coverage_audit.py
  test_run_week7_pilot.py
  test_partial_sorted_list.py
  test_sibling_list_backend.py
  test_paper_jordan.py
  test_paper_jordan_sort.py
  test_validate_paper_algorithm.py

experiments/
  run_small_tests.py
  summarize_results.py
  profile_generated_cases.py
  audit_generator_coverage.py
  run_week7_pilot.py
  validate_experiment_outputs.py
  validate_generator_audit_outputs.py
  validate_paper_algorithm.py

results/
  week1_baseline_results.csv
  week1_baseline_smoke_results.csv
  README.md
  # generated via scripts (reproducible, not committed by default):
  #   - week1_baseline_summary.csv
  #   - generator_structure_profile.csv
  #   - week4_reference_results.csv
  #   - week4_reference_summary.csv
  #   - week7_generator_coverage_audit.csv
  #   - week7_pilot_raw.csv
  #   - week7_pilot_case_summary.csv
  #   - week7_pilot_group_summary.csv
  #   - runs/<run_id>/

docs/
  README.md
  design/
    notation.md
    oracle_and_test_generation.md
    simplified_algorithm_design.md
    final_scope_and_contributions.md
    final_experiment_spec.md
    theory_to_implementation_mapping.md
    paper_algorithm_ordinary_list.md
  progress/
    week1_progress.md
    week1_summary.md
    week5_progress.md
    week6_progress.md
    week6_summary.md
    week7_progress.md
    week7_summary.md
    week8_summary.md
    week9_progress.md
  thesis/
    experimental_methodology_draft.md
    implementation_draft.md
  analysis/
    week7_pilot_interpretation.md
    week7_pilot_auto_report.md
  backlog/
    future_work_todo.md
  notes.md
  plan/
    README.md
    four_month_roadmap.md
    week2_plan.md
    thesis_scope_and_research_questions.pdf
    week3_plan.md
    week4_plan.md
    week5_plan.md
    week6_plan.md
    week7_plan.md
    week8_plan.md
    refined_thesis_direction_after_week8.md
    week9_plan.md
  papers/
```

## Core Concepts

The current oracle treats a sequence as a candidate Jordan sequence by:

1. extracting upper pairs `(x1, x2), (x3, x4), ...`,
2. extracting lower pairs `(x2, x3), (x4, x5), ...`,
3. converting values to sorted-order ranks,
4. converting pairs to rank intervals,
5. checking each interval family for crossings.

The oracle returns:

```text
valid
sorted
distinct_values
upper_ok
lower_ok
reason
```

## Generator Families

Week 1 includes these generator families:

```text
flat_valid
nested_valid
incremental_valid
invalid_upper_crossing
invalid_lower_crossing
random_invalid
mutation_based_invalid
```

Generator family names describe how a sequence is produced. Later structural labels such as flat, shallow, deep, or mixed should be measured after generation by `stats.py` or a classifier.

## Baseline Algorithms

Week 1 includes:

```text
python_sort
merge_sort
quick_sort
sort_plus_laminarity_check
```

`python_sort` is the practical optimized baseline. `merge_sort` and `quick_sort` are transparent classical baselines. `sort_plus_laminarity_check` measures a naive oracle-check-plus-sort pipeline.

## Running Tests

Run all tests from the repository root:

```bash
python -m unittest discover -s tests
```

Current status:

```text
Ran 318 tests
OK
```

Note: a full Week 4 reference run is reproducible from the current scripts; all generated
artifact outputs are committed only when explicitly tracked.

## Running Week 1 Experiments

Run the smoke experiment:

```bash
python experiments/run_small_tests.py --smoke
```

Run the full Week 1 baseline experiment:

```bash
python experiments/run_small_tests.py
```

The full experiment writes:

```text
results/week1_baseline_results.csv
```

The smoke experiment writes:

```text
results/week1_baseline_smoke_results.csv
```

The full Week 1 baseline experiment contains 2940 raw timing rows:

```text
7 families x 7 sizes x 3 cases x 4 algorithms x 5 timing runs
```

See [results/README.md](results/README.md) for the CSV schema and field meanings.

## Documentation

Important project documents:

- [docs/README.md](docs/README.md): guide to the documentation structure.
- [docs/progress/week1_summary.md](docs/progress/week1_summary.md): Week 1 completed work, experiment configuration, validation results, limitations, and next steps.
- [docs/progress/week1_progress.md](docs/progress/week1_progress.md): checklist-style Week 1 progress tracker.
- [docs/progress/week8_summary.md](docs/progress/week8_summary.md): Week 8 scope freeze, dry-run validation, and Week 9 gate.
- [docs/progress/week9_progress.md](docs/progress/week9_progress.md): Week 9 daily execution record and current gate.
- [docs/design/paper_algorithm_ordinary_list.md](docs/design/paper_algorithm_ordinary_list.md): implementation-facing state, pseudocode, invariants, and worked trace for the 1990 paper algorithm.
- [docs/plan/week9_plan.md](docs/plan/week9_plan.md): detailed Day 1-Day 7 ordinary-list implementation plan.
- [docs/design/final_experiment_spec.md](docs/design/final_experiment_spec.md): frozen experiment variables, correctness checks, aggregation rules, and non-claims.
- [docs/design/oracle_and_test_generation.md](docs/design/oracle_and_test_generation.md): definitions and design notes for the oracle and generators.
- [docs/design/notation.md](docs/design/notation.md): reusable terminology for candidate sequences, valid Jordan sequences, pair families, rank intervals, laminarity, family trees, sibling lists, and structural categories.
- [docs/design/simplified_algorithm_design.md](docs/design/simplified_algorithm_design.md): Week 2 reference-skeleton design, including API contract, family-tree representation, stats contract, trace format, and error policy.
- [docs/progress/week2_summary.md](docs/progress/week2_summary.md): Week 2 completion summary, limitations, and Week 3 handoff.
- [docs/progress/week3_progress.md](docs/progress/week3_progress.md): Week 3 execution notes (contract audit, debug helper, script scaffolding).
- [docs/progress/week3_summary.md](docs/progress/week3_summary.md): Week 3 completion summary and Week 4 handoff.
- [docs/progress/week4_notes.md](docs/progress/week4_notes.md): Week 4 execution notes and milestone log.
- [docs/progress/week4_summary.md](docs/progress/week4_summary.md): Week 4 completion summary and reference-pipeline boundary statement.
- [docs/progress/week5_progress.md](docs/progress/week5_progress.md): Week 5 execution log and checkpoint record.
- [docs/progress/week6_progress.md](docs/progress/week6_progress.md): Week 6 execution log and checkpoint record.
- [docs/progress/week6_summary.md](docs/progress/week6_summary.md): Week 6 summary and Week 7 handoff constraints.
- [docs/progress/week7_progress.md](docs/progress/week7_progress.md): Week 7 execution log for metrics, counters, audit, and pilot work.
- [docs/progress/week7_summary.md](docs/progress/week7_summary.md): Week 7 summary and Week 8 handoff constraints.
- [docs/design/structural_examples.md](docs/design/structural_examples.md): concrete structural examples for papers and debugging.
- [docs/design/experimental_questions_and_metrics.md](docs/design/experimental_questions_and_metrics.md): Week 7 experiment questions and metric definitions.
- [docs/design/benchmark_protocol.md](docs/design/benchmark_protocol.md): Week 7 pilot timing protocol.
- [docs/analysis/week7_pilot_interpretation.md](docs/analysis/week7_pilot_interpretation.md): initial Week 7 pilot interpretation.
- [docs/backlog/future_work_todo.md](docs/backlog/future_work_todo.md): follow-up ideas that should not block the Week 1 loop.
- [docs/plan/four_month_roadmap.md](docs/plan/four_month_roadmap.md): compressed 3-4 month thesis execution plan.
- [docs/plan/week3_plan.md](docs/plan/week3_plan.md): Week 3 plan for reference pipeline strengthening and experimental support expansion.
- [docs/plan/week4_plan.md](docs/plan/week4_plan.md): Week 4 execution plan and checkpoint criteria.
- [docs/plan/week5_plan.md](docs/plan/week5_plan.md): Week 5 plan for validation and thesis-facing experimental artifacts.
- [docs/plan/week6_plan.md](docs/plan/week6_plan.md): Week 6 plan for result revalidation and evidence packaging.
- [docs/plan/week7_plan.md](docs/plan/week7_plan.md): Week 7 plan for experiment-design hardening and pilot analysis.

## Known Limitations

- The oracle currently uses an `O(n^2)` pairwise interval crossing check.
- Timing results support raw baseline rows; additional structure summaries are now also available.
- The timing results are preliminary and should not be interpreted as final performance claims.
- `simplified_jordan_sort(seq)` is currently a **reference skeleton**.
  It returns `oracle_result["sorted"]`, and the current implementation
  does not yet implement the real simplified Jordan-sorting operations.
- No level-linked search trees or heterogeneous finger trees are implemented.
- Visualization is still future work.

## Next Steps

Immediate next task:

- review the Week 9 Day 6 correctness, invariant, and diagnostics checkpoint;
- after approval, begin Day 7 integration and a deliberately small pilot;
- keep diagnostic trace validation and full backend invariant checks outside
  future timed performance regions.

Later cleanup:

- create a Markdown version of the approved thesis scope and research questions,
- optionally generate a baseline summary CSV with min, median, and mean timing values,
- optionally add a lightweight interval visualization script.
