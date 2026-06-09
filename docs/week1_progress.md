# Week 1 Progress Checklist

Last updated: 2026-06-09

## Week 1 Goal

Build the first minimal working loop:

```text
generate sequence -> oracle checks valid/invalid -> expected sorted order -> save test case -> run baselines
```

## Priority Items

- [x] `src/oracle.py` + unit tests  
  Completed on 2026-06-05.  
  Implemented upper/lower pairs, rank map, interval conversion, crossing checks, laminarity checks, duplicate rejection, and oracle output.

- [x] `docs/oracle_and_test_generation.md`  
  Completed on 2026-06-05.  
  Added definitions for Jordan sequences, upper/lower pairs, intervals, laminarity, crossing, oracle output, and initial test families.

- [x] Simple valid/invalid generators in `src/generators.py`  
  Completed on 2026-06-05.  
  Added flat, nested candidate, invalid upper crossing, invalid lower crossing, random permutation, swap mutation, and small handmade valid cases.

- [x] `src/baselines.py`  
  Completed on 2026-06-09.  
  Added Python sort, merge sort, quick sort, laminarity-check-plus-sort, timing helper, and baseline unit tests.

- [ ] Small experiment CSV + Week 1 summary  
  Not started.  
  Planned after baselines are implemented.

## Day 1 - Project Structure + Definitions

- [x] Create project directory.  
  Done on 2026-06-05.

- [x] Distinguish duplicate-value rejection from laminarity failures.  
  Done on 2026-06-09.  
  Duplicate inputs now report `distinct_values: False` and leave `upper_ok` / `lower_ok` as `None`.

- [x] Create project structure.  
  Done on 2026-06-05.

```text
src/
  oracle.py
  generators.py
  baselines.py
  stats.py

tests/
  test_oracle.py
  test_generators.py

experiments/
  run_small_tests.py

docs/
  oracle_and_test_generation.md
  notes.md
  week1_todo.pdf
  week1_progress.md
```

- [x] Write `docs/oracle_and_test_generation.md`.  
  Done on 2026-06-05.

- [x] Define Jordan sequence.  
  Done on 2026-06-05.

- [x] Define upper pairs and lower pairs.  
  Done on 2026-06-05.

- [x] Define intervals using sorted-order ranks.  
  Done on 2026-06-05.  
  Ranks are now 1-based for readability.

- [x] Define laminarity and crossing.  
  Done on 2026-06-05.

- [x] Define oracle output format.  
  Done on 2026-06-05.

Day 1 status: completed.

## Day 2 - Correctness Oracle

- [x] `upper_pairs(seq)`  
  Done on 2026-06-05.

- [x] `lower_pairs(seq)`  
  Done on 2026-06-05.

- [x] `rank_map(seq)`  
  Done on 2026-06-05.  
  Uses 1-based ranks in sorted order.

- [x] `pair_to_interval(pair, rank)`  
  Done on 2026-06-05.

- [x] `crosses(interval1, interval2)`  
  Done on 2026-06-05.

- [x] `is_laminar(pairs, rank)`  
  Done on 2026-06-05.  
  Current version uses a simple `O(n^2)` pairwise check.

- [x] `oracle(seq)`  
  Done on 2026-06-05.

- [x] Unit tests for flat valid case.  
  Done on 2026-06-05.

- [x] Unit tests for nested valid case.  
  Done on 2026-06-05.

- [x] Unit tests for invalid upper crossing.  
  Done on 2026-06-05.

- [x] Unit tests for invalid lower crossing.  
  Done on 2026-06-05.

- [x] Unit tests for random permutation sanity check.  
  Done on 2026-06-05.

- [x] Unit tests for duplicated values rejection.  
  Done on 2026-06-05.

- [x] Unit tests for empty and singleton sequences.  
  Done on 2026-06-05.

Day 2 status: completed early.

## Day 3 - Minimal Test Generators

- [x] `generate_flat(n)`  
  Done on 2026-06-05.

- [x] `generate_nested(n)`  
  Done on 2026-06-05.  
  Currently treated as a nested candidate generator and checked with the oracle in tests.

- [x] `generate_small_handmade_valid_cases()`  
  Done on 2026-06-05.

- [x] `generate_invalid_upper_crossing(n)`  
  Done on 2026-06-05.

- [x] `generate_invalid_lower_crossing(n)`  
  Done on 2026-06-05.

- [x] `generate_random_permutation(n)`  
  Done on 2026-06-05.

- [x] `generate_random_invalid(n)`  
  Done on 2026-06-09.  
  Uses oracle-certified rejection sampling and is distinct from neutral `random_permutation`.

- [x] `generate_incremental_valid(n)`  
  Done on 2026-06-09.  
  Uses rank insertion, oracle certification, and adjacent-rank fallback to construct valid sequences.

- [x] `mutate_by_swap(seq)`  
  Done on 2026-06-05.

- [x] `generate_mutation_based_invalid(seq)`  
  Done on 2026-06-09.  
  Uses oracle-certified swap mutations and is distinct from low-level mutation candidates.

- [x] `generate_mutation_based_invalid_case(n)`  
  Done on 2026-06-09.  
  Makes `mutation_based_invalid` available as a standard dataset family.

- [x] Generator tests.  
  Done on 2026-06-05.

Day 3 status: mostly completed early.

## Day 4 - Input Families and JSON Saving Format

- [x] Define input families in code.  
  Done on 2026-06-09.

- [x] Implement `save_test_case(seq, family, path)`.  
  Done on 2026-06-09.

- [x] Implement `load_test_case(path)`.  
  Done on 2026-06-09.

- [x] Implement `generate_dataset(family, sizes, repetitions)`.  
  Done on 2026-06-09.

- [x] Create a small `data/` directory with JSON test cases.  
  Done on 2026-06-09.  
  Sample files are stored under `data/sample_cases/`.

- [x] Design and implement an incremental valid generator.  
  Completed on 2026-06-09.  
  Starts from an empty valid sequence, appends one rank at a time, uses oracle certification after each extension, and falls back to an adjacent-rank insertion that preserves validity.

Day 4 status: completed.

## Day 5 - Baselines Skeleton

- [x] `python_sort(seq)`.  
  Done on 2026-06-09.  
  Uses Python's built-in `sorted` as the optimized practical baseline.

- [x] `merge_sort(seq)`.  
  Done on 2026-06-09.  
  Implements a transparent classical merge-sort baseline.

- [x] `quick_sort(seq)`.  
  Done on 2026-06-09.  
  Uses a deterministic middle pivot for reproducible experiments.

- [x] `sort_plus_laminarity_check(seq)`.  
  Done on 2026-06-09.  
  Runs the oracle before returning the sorted output, so experiments can measure the cost of a naive structure-check-plus-sort pipeline.

- [x] `time_function(func, seq)`.  
  Done on 2026-06-09.  
  Measures elapsed time with `perf_counter_ns` and runs functions on an input copy to protect reusable test cases.

- [x] Baseline unit tests.  
  Done on 2026-06-09.  
  Added tests for correctness, empty/singleton inputs, duplicate values, input preservation, oracle reporting, and timing output.

Day 5 status: completed.

## Day 6 - Small Experiments

- [ ] Implement `experiments/run_small_tests.py`.
- [ ] Use sizes `[8, 16, 32, 64, 128, 256, 512]`.
- [ ] Use families `flat_valid`, `nested_valid`, `incremental_valid`, `invalid_upper_crossing`, `invalid_lower_crossing`, `random_invalid`, `mutation_based_invalid`.
- [ ] Record oracle valid/invalid results.
- [ ] Record baseline timings.
- [ ] Run repeated timings in `experiments/run_small_tests.py`.  
  Added on 2026-06-09.  
  Keep `time_function(func, seq)` as a single-run helper. The experiment runner should handle repetitions, such as 5 or 10 runs per algorithm/case, and record or summarize min, median, and mean timings.
- [ ] Output `results/week1_baseline_results.csv`.

Day 6 status: not started.

## Day 7 - Week 1 Summary

- [ ] Write `docs/week1_summary.md`.
- [ ] Summarize implemented components.
- [ ] Summarize what works.
- [ ] List open issues.
- [ ] List next steps.

Day 7 status: not started.

## Extra Work Completed

- [x] Initialized Git repository.  
  Done on 2026-06-05.

- [x] Added `.gitignore`.  
  Done on 2026-06-05.

- [x] Pushed project to GitHub.  
  Done on 2026-06-05.

- [x] Expanded `README.md`.  
  Done on 2026-06-05.

- [x] Copied original Week 1 TODO PDF into the project.  
  Done on 2026-06-05.  
  File: `docs/week1_todo.pdf`.

## Future Work Backlog

Longer-term generator, testing, instrumentation, and visualization ideas have been moved to [future_work_todo.md](future_work_todo.md).

## Current Test Status

As of 2026-06-09:

```text
Ran 74 tests
OK
```
