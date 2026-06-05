# Week 1 Progress Checklist

Last updated: 2026-06-05

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

- [ ] `src/baselines.py`  
  Not started.  
  Next step after JSON test-case saving format.

- [ ] Small experiment CSV + Week 1 summary  
  Not started.  
  Planned after baselines are implemented.

## Day 1 - Project Structure + Definitions

- [x] Create project directory.  
  Done on 2026-06-05.

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

- [x] `generate_invalid_upper_crossing()`  
  Done on 2026-06-05.

- [x] `generate_invalid_lower_crossing()`  
  Done on 2026-06-05.

- [x] `generate_random_permutation(n)`  
  Done on 2026-06-05.

- [x] `mutate_by_swap(seq)`  
  Done on 2026-06-05.

- [x] Generator tests.  
  Done on 2026-06-05.

Day 3 status: mostly completed early.

## Day 4 - Input Families and JSON Saving Format

- [ ] Define input families in code.
- [ ] Implement `save_test_case(seq, family, path)`.
- [ ] Implement `load_test_case(path)`.
- [ ] Implement `generate_dataset(family, sizes, repetitions)`.
- [ ] Create a small `data/` directory with JSON test cases.

Day 4 status: next recommended task.

## Day 5 - Baselines Skeleton

- [ ] `python_sort(seq)`.
- [ ] `merge_sort(seq)`.
- [ ] `quick_sort(seq)`.
- [ ] `sort_plus_laminarity_check(seq)`.
- [ ] `time_function(func, seq)`.

Day 5 status: not started.

## Day 6 - Small Experiments

- [ ] Implement `experiments/run_small_tests.py`.
- [ ] Use sizes `[8, 16, 32, 64, 128, 256, 512]`.
- [ ] Use families `flat_valid`, `nested_valid`, `invalid_crossing`, `random_invalid`.
- [ ] Record oracle valid/invalid results.
- [ ] Record baseline timings.
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

## Current Test Status

As of 2026-06-05:

```text
Ran 19 tests
OK
```

