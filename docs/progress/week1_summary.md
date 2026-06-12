# Week 1 Summary

Last updated: 2026-06-11

## Goal

The Week 1 goal was to build the first minimal working loop for the Jordan-sorting thesis project:

```text
generate sequence -> oracle checks valid/invalid -> save test case -> run baselines -> write experiment CSV
```

This goal is now complete. The project has a correctness oracle, several test-instance generators, a JSON test-case pipeline, baseline sorting algorithms, a small experiment runner, committed Week 1 baseline CSV files, and unit tests for the implemented components.

## Completed Components

### Correctness Oracle

Implemented in `src/oracle.py`.

The oracle checks whether a sequence satisfies the simplified Jordan-sequence validity condition used in this project:

- upper pairs are extracted as `(x1, x2), (x3, x4), ...`,
- lower pairs are extracted as `(x2, x3), (x4, x5), ...`,
- values are converted to sorted-order ranks,
- each pair becomes a rank interval,
- each family is checked for interval crossings,
- duplicate values are rejected separately from crossing failures.

The oracle returns a structured result containing:

- `valid`
- `sorted`
- `distinct_values`
- `upper_ok`
- `lower_ok`
- `reason`

The current laminarity check is intentionally simple and uses an `O(n^2)` pairwise interval comparison.

### Test-Instance Generators

Implemented in `src/generators.py`.

Week 1 includes the following generator families:

- `flat_valid`
- `nested_valid`
- `incremental_valid`
- `invalid_upper_crossing`
- `invalid_lower_crossing`
- `random_permutation`
- `random_invalid`
- `mutation_based_invalid`

The valid and invalid families are oracle-certified where needed. In particular:

- `random_invalid` uses rejection sampling and returns only oracle-invalid permutations.
- `incremental_valid` grows a valid sequence one element at a time using rank insertion, oracle certification, and adjacent-rank fallback.
- `mutation_based_invalid` starts from a valid base sequence, applies swap mutations, and returns only oracle-invalid results.

Generator family names describe how a sequence is produced. Future structural labels such as flat, shallow, deep, or mixed should be measured after generation by `stats.py` or a classifier.

### JSON Test-Case Pipeline

Implemented in `src/generators.py`.

Week 1 added a reusable JSON case format. Each saved case contains:

- stable case id,
- family,
- size,
- seed,
- sequence,
- oracle result.

The dataset pipeline is built around:

- `make_test_case`
- `save_test_case`
- `load_test_case`
- `generate_dataset`

The Week 1 Day 6 experiment runner reuses this pipeline instead of generating sequences directly.

### Baseline Algorithms

Implemented in `src/baselines.py`.

Week 1 includes four baseline algorithms or baseline-style procedures:

- `python_sort`
- `merge_sort`
- `quick_sort`
- `sort_plus_laminarity_check`

It also includes:

- `time_function`

`python_sort` is the optimized practical baseline based on Python's built-in `sorted`. `merge_sort` and `quick_sort` are transparent classical baselines. `sort_plus_laminarity_check` runs the oracle and returns the sorted order already computed by the oracle, so it measures a naive structure-check-plus-sort pipeline without sorting twice.

### Small Baseline Experiment Runner

Implemented in `experiments/run_small_tests.py`.

The runner supports two modes:

```bash
python experiments/run_small_tests.py --smoke
python experiments/run_small_tests.py
```

The smoke mode runs a minimal end-to-end check. The full mode generates cases, runs all baseline algorithms, records repeated timings, writes CSV output, and validates the result rows.

The runner includes:

- experiment configurations,
- algorithm registry,
- CSV schema,
- JSON case generation,
- timing logic,
- sorted-output extraction,
- error recording,
- row validation,
- coverage validation,
- command-line entry point.

### Tests

The current test suite covers:

- oracle behavior,
- pair extraction,
- rank mapping,
- interval crossing detection,
- duplicate-value rejection,
- generator correctness and reproducibility,
- JSON save/load behavior,
- baseline correctness,
- timing helper behavior,
- experiment runner behavior,
- coverage validation for family, size, and algorithm sets.

Current test status:

```text
Ran 83 tests
OK
```

### Repository Organization and Reproducibility

The project is tracked in Git and pushed to GitHub. The repository now contains:

- source code under `src/`,
- tests under `tests/`,
- experiment runner under `experiments/`,
- documentation under `docs/`,
- Week 1 baseline CSV outputs under `results/`.

Large or reproducible intermediate result files remain ignored. The Week 1 CSV files are small enough to commit and are included so the first experiment loop is visible from the repository.

## Working End-to-End Pipeline

The Week 1 implementation now supports the following complete pipeline:

```text
generate sequence
-> oracle checks valid/invalid
-> save JSON case
-> load JSON case
-> run baseline algorithms
-> run repeated timing
-> write raw CSV rows
-> validate correctness and coverage
```

This is the main Week 1 outcome. It does not yet implement simplified Jordan sorting, but it establishes the reproducible infrastructure needed to test that implementation later.

## Week 1 Baseline Experiment

### Configuration

The full Week 1 baseline experiment uses:

```text
sizes:
[8, 16, 32, 64, 128, 256, 512]

families:
flat_valid
nested_valid
incremental_valid
invalid_upper_crossing
invalid_lower_crossing
random_invalid
mutation_based_invalid

algorithms:
python_sort
merge_sort
quick_sort
sort_plus_laminarity_check

cases_per_size:
3

timing_runs:
5
```

This produces:

```text
7 families x 7 sizes x 3 cases x 4 algorithms x 5 timing runs = 2940 raw timing rows
```

### CSV Schema

The main CSV file is:

```text
results/week1_baseline_results.csv
```

The smoke-test CSV file is:

```text
results/week1_baseline_smoke_results.csv
```

The CSV schema is:

```text
case_id
family
n
seed
oracle_valid
oracle_reason
distinct_values
upper_ok
lower_ok
algorithm
run_index
time_ns
sorted_correct
error
```

`sorted_correct` means that the algorithm's sorted output matches `oracle["sorted"]`. It does not mean the input is a valid Jordan sequence.

### Validation Results

The full Week 1 experiment passed the built-in validation checks:

- all rows had empty `error` fields,
- all rows had `sorted_correct = True`,
- all valid families were oracle-valid,
- all invalid families were oracle-invalid,
- the generated rows covered all configured families,
- the generated rows covered all configured sizes,
- the generated rows covered all configured algorithms,
- the row count matched the expected 2940 raw timing rows.

These checks validate the Week 1 experiment pipeline. They should not be interpreted as final performance conclusions about Jordan sorting.

## Reproduction Commands

Run all tests:

```bash
python -m unittest discover -s tests
```

Run the smoke experiment:

```bash
python experiments/run_small_tests.py --smoke
```

Run the full Week 1 baseline experiment:

```bash
python experiments/run_small_tests.py
```

## Known Limitations

- The current oracle uses an `O(n^2)` pairwise interval check.
- The current `flat_valid` family is a canonical flat construction, not a sampler over all flat instances.
- The current `nested_valid` family is a construction family; structural depth should be measured after generation.
- The `incremental_valid` generator is oracle-certified but not uniform over all valid Jordan sequences.
- The baseline CSV stores raw timing rows only; no summary statistics or plots are generated yet.
- The timing results are preliminary and should not be interpreted as final performance claims.
- No simplified Jordan-sorting implementation exists yet.
- No level-linked search trees or heterogeneous finger trees are implemented.
- Visualization is still future work.

## Week 1 Cleanup

Completed cleanup items:

- Updated `README.md` to reflect the JSON pipeline, baselines, experiment runner, and Week 1 CSV.
- Added `results/README.md` to explain the committed Week 1 baseline CSV files and field meanings.
- Kept reproducible intermediate JSON case files ignored while committing the small Week 1 CSV outputs.

Optional follow-up cleanup:

- Generate a baseline summary CSV with min, median, and mean timing values.
- Add a lightweight interval visualization script for small examples.

## Next Steps

### Phase 2 / Week 2-3 Preparation

- Write `docs/design/simplified_algorithm_design.md`.
- Define data structures for upper and lower family trees.
- Define sibling-list representation.
- Define the reference simplified sorting pipeline.
- Add oracle-based differential tests for the future implementation.
- Keep the first simplified implementation focused on correctness and explanation rather than the full theoretical linear-time bound.
