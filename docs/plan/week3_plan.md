# Week 3 Plan

Last updated: 2026-06-17

## Goal

Turn the Week 2 reference skeleton into a clearer algorithm-facing reference
pipeline while keeping correctness-oriented behavior and without claiming
theoretical linear-time guarantees.

Week 3 is the bridge from `reference_skeleton` output to
`reference_pipeline` explainability.

## Scope

Week 3 should focus on:

- explicit pipeline stages and backend metadata,
- richer trace and contract checks,
- lightweight debug/inspection helpers,
- structure-aware experiment outputs,
- and dataset quality summaries that support thesis analysis.

Do not implement level-linked trees or finger trees in Week 3.

## Non-Goals

Week 3 should still not attempt:

- full linear-time Jordan-sorting proof or replacement,
- dynamic tree updates as final algorithm behavior,
- large-scale plotting pipelines before Week 6.

## Day 1: Strengthen the Reference Pipeline Contract

Main output:

- `src/simplified_jordan.py` (interface evolution)
- `tests/test_simplified_jordan.py` (pipeline-contract tests)

Recommended work:

Note:

Most of these steps were stabilized during Week2 Day5/Day6:
`prepare_reference_backend`, `extract_rank_order`, `return_reference_sorted_output`,
`implementation_stage`, and `backend` metadata already exist.

For Week3 Day1, use this day to audit and lock these contracts in tests/docs, and
prepare any minimal helper functions if needed.

1. Keep the existing return fields from Week 2.
2. Add explicit pipeline step traces (stable sequence):

```text
copy_input
oracle
build_family_trees
structure_profile
prepare_reference_backend
extract_rank_order
return_reference_sorted_output
```

3. Add backend metadata in return value while keeping `implementation` field:

```python
"implementation": "reference_skeleton",
"implementation_stage": "week2_interface_skeleton",
"backend": {
    "name": "ordinary_list",
    "uses_oracle_sorted_output": True,
    "linear_time_claim": False,
}
```

4. Keep compatibility with existing tests; only extend the contract.

Completion checks:

- trace includes stable pipeline stage sequence,
- `implementation_stage` and `backend` are present,
- existing Day 2/Day 3 tests remain green.

## Day 2: Add Debug/Inspection Utility

Main output:

- `src/family_tree.py`
- `tests/test_family_tree.py` (optional small helper coverage)

Recommended work:

1. Add a text dump helper (for small examples and thesis notes):

```python
family_tree_to_debug_lines(tree)
```

2. Format is deterministic:

```text
[1, 6]
  [2, 5]
    [3, 4]
```

3. Use this helper in docs or temporary debug snippets.

Completion checks:

- helper present and testable,
- output is deterministic,
- no runtime dependency changes.

## Day 3: Structural Examples and Contract Documentation

Main output:

- `docs/design/structural_examples.md`

Include:

- flat valid example,
- nested valid example,
- invalid crossing example,
- family-tree dump output,
- `structure_profile(...)` output,
- `simplified_jordan_sort(...)` output excerpt.

Completion checks:

- all examples map terminology consistently to `notation.md`,
- examples are small and directly used for debugging/review.

## Day 4: Structural Metrics in Experiments (optional Week3 expansion)

Main output:

- `experiments/run_small_tests.py` (CSV schema extension)

Recommended work:

1. Add optional fields from `structure_profile` to experiment rows:

```text
upper_interval_count
lower_interval_count
total_interval_count
upper_root_count
lower_root_count
nesting_count
nesting_density
max_depth
category
```

2. Keep old schema fields for compatibility.

Completion checks:

- generated CSV includes both raw timing and structural columns,
- downstream scripts still parse baseline rows correctly.

## Day 5: Experiment Summary Utilities

Main output:

- `experiments/summarize_results.py` (or `experiments/` helper)
- `results/week1_baseline_summary.csv`
  - reproducible generated output (not committed by default unless explicitly tracked)

Recommended work:

- aggregate raw timing rows by

```text
algorithm, family, n, run_count, min_time_ns, median_time_ns, mean_time_ns, max_time_ns
```

- keep `*_raw` rows committed as audit source.

Completion checks:

- summary file can be generated on the current raw CSV,
- at least one figure-ready view can be produced later from the summary.

## Day 6: Dataset Structural Audit (Paper Support)

Main output:

- `experiments/profile_generated_cases.py` (or dedicated script)
- `results/generator_structure_profile.csv`
  - reproducible generated output (not committed by default unless explicitly tracked)

Recommended work:

1. For each generated family and size:

- run `structure_profile`,
- collect structural category distribution,
- collect invalid reason distribution.

2. Confirm whether `nested_valid` and `incremental_valid` produce intended
   structure variety.

Completion checks:

- per-family counts by `category` and `reason` exist,
- summary file is reproducible.

## Day 7: Week 3 Summary

Main output:

- `docs/progress/week3_summary.md` (to be created)

Include:

1. what is stabilized in contract and pipeline,
2. what remains scaffold/skeleton,
3. what is now blocked by true simplified algorithm implementation,
4. how Week 4+ will start full algorithm-facing operations.

## Week 3 Exit Criteria

- `simplified_jordan_sort` has stable pipeline-stage trace and backend metadata,
- debug dump helper exists,
- structural examples are documented,
- experiment rows can include structural fields,
- summary/audit scripts can reproduce structural distributions,
- Week 3 summary exists.
