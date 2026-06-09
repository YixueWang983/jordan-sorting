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

- [ ] `src/baselines.py`  
  Not started.  
  Next step after JSON test-case saving format.

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

- [ ] `python_sort(seq)`.
- [ ] `merge_sort(seq)`.
- [ ] `quick_sort(seq)`.
- [ ] `sort_plus_laminarity_check(seq)`.
- [ ] `time_function(func, seq)`.

Day 5 status: not started.

## Day 6 - Small Experiments

- [ ] Implement `experiments/run_small_tests.py`.
- [ ] Use sizes `[8, 16, 32, 64, 128, 256, 512]`.
- [ ] Use families `flat_valid`, `nested_valid`, `incremental_valid`, `invalid_upper_crossing`, `invalid_lower_crossing`, `random_invalid`.
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

## Open Generator Ideas

- [x] Incremental valid extension generator.  
  Completed on 2026-06-09.  
  Implemented as `generate_incremental_valid(n, seed=None, max_attempts_per_step=20)`.

- [ ] Random tree / polygon-decomposition based valid generator.  
  Added on 2026-06-05.  
  Explore whether complex valid Jordan sequences can be generated by first sampling a random laminar tree structure or a random non-crossing polygon decomposition, then mapping that structure back to a Jordan sequence. This may provide efficient, large-scale, 100% valid, structurally complex, split-heavy instances. The hard part is defining the inverse mapping so that both upper and lower pair families remain laminar.

- [x] Document limitations of the incremental generator.  
  Completed on 2026-06-09.  
  The generator is described as constructive and oracle-certified, but not uniform over all valid Jordan sequences.

## Open Testing Ideas

- [ ] Property-based testing with Hypothesis.  
  Added on 2026-06-05.  
  Consider adding Python's `hypothesis` library after the basic generators and JSON dataset format are stable. It could generate edge cases automatically, test mutation rules, and shrink failures to minimal counterexamples. This is likely most useful once dynamic family trees, splitting, and more complex generator logic exist.

## Open Instrumentation Ideas

- [ ] Design detailed metrics for `stats.py`.  
  Added on 2026-06-05.  
  Time alone will not be enough for a strong experimental chapter. Candidate metrics include comparisons, oracle interval checks, generator attempts, rejected candidates, split counts, split region sizes, traversal steps, node visits, merge counts, relabel operations, tree rotations, and finger-search steps.

- [ ] Integrate metrics into baselines and future Jordan-sorting implementations.  
  Added on 2026-06-05.  
  Baselines can start with timing and comparison-style counters. The ordinary-list backend should later record split and traversal work, so the thesis can explain exactly where it loses the linear-time bound.

## Open Visualization Ideas

- [ ] Lightweight interval visualization script.  
  Added on 2026-06-05.  
  Build a small script that draws the sorted order as a horizontal line and draws upper/lower intervals as arcs. This can make laminarity and crossing visible for debugging and for thesis figures. It should focus on small or local examples rather than huge sequences.

## Current Test Status

As of 2026-06-09:

```text
Ran 50 tests
OK
```
