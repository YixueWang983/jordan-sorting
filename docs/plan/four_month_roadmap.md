# Four-Month Thesis Roadmap

Last updated: 2026-06-16

## Goal

Compress the thesis implementation and writing plan into a 3-4 month schedule.

The minimum deliverable should be ready after 12 weeks. Weeks 13-16 are reserved for supervisor feedback, experiment cleanup, thesis polishing, and defense preparation.

The project target is not a full production-grade reimplementation of the original linear-time data structures. The target is a correct, explainable, testable reference framework for simplified Jordan sorting, with experiments that explain where the ordinary implementation differs from the theoretical linear-time algorithm.

## Core Deliverable

The final thesis project should include:

- a correctness oracle for Jordan-sequence validity,
- controlled valid and invalid test-instance generators,
- JSON-based dataset generation,
- baseline sorting algorithms,
- a simplified Jordan-sorting reference implementation,
- correctness tests on generated datasets,
- runtime and instrumentation experiments,
- a clear explanation of bottlenecks and limitations,
- thesis chapters that connect the implementation to the 1986/1990 Jordan-sorting ideas.

## Schedule Overview

```text
Weeks 1-2:
Finish the experimental framework and start the simplified-reference phase.

Week 3:
Strengthen the reference skeleton with algorithm-facing operations, validation, and early instrumentation.

Week 4:
Extend the simplified reference implementation and differential tests.

Week 5:
Debug, validate, and prepare the first simplified-reference experiments.

Weeks 6-8:
Run experiments, collect metrics, and draft analysis.

Weeks 9-11:
Write the thesis body.

Week 12:
Finalize experiments, figures, terminology, and submission draft.

Weeks 13-16:
Handle supervisor feedback, improve related work, clean code, prepare slides, and polish.
```

## Phase 1: Foundation and Experimental Loop

Target time:

```text
Weeks 1-2
```

Main goal:

```text
Close the loop:
generate sequence -> oracle -> baseline -> CSV result -> summary.
```

Required code:

- `src/oracle.py` complete.
- `src/generators.py` complete enough for Week 1 experiments.
- `src/baselines.py` implemented.
- `experiments/run_small_tests.py` implemented.
- JSON test cases generated under `data/`.
- CSV results generated under `results/`.

Required baselines:

- `python_sort(seq)`
- `merge_sort(seq)`
- `quick_sort(seq)`
- `sort_plus_laminarity_check(seq)`
- `time_function(func, seq)`

Required dataset families:

- `flat_valid`
- `nested_valid`
- `incremental_valid`
- `invalid_upper_crossing`
- `invalid_lower_crossing`
- `random_invalid`
- `mutation_based_invalid`

Recommended first sizes:

```text
[8, 16, 32, 64, 128, 256, 512]
```

Required documentation:

- `docs/progress/week1_summary.md`
- `docs/design/notation.md` or `docs/design/paper_notes.md`
- updated progress checklist

Optional but useful:

- a lightweight interval visualization script that draws sorted ranks, upper arcs, lower arcs, and crossings for small examples.

Gate 1 pass criteria:

- all unit tests pass,
- baselines run,
- small experiment CSV is generated,
- Week 1 summary exists,
- basic notation notes exist.

Current status:

```text
Week 1 is complete.
Week 2 foundations and skeleton outputs are complete.
The current target is Week 3 reference-pipeline strengthening.
```

Gate 1 fallback:

- If visualization is unfinished, continue to Phase 2.
- If baselines or CSV output are unfinished, do not continue to Phase 2 yet.

## Phase 2: Simplified Reference Implementation

Target time:

```text
Weeks 2-5
```

Main goal:

```text
Build a correct and explainable simplified Jordan-sorting reference version.
```

This is the highest-risk phase. The priority is correctness and explanation, not linear-time performance.

### Week 2: Design and Skeleton Foundations

Week 2 now covers the first simplified-reference foundations:

- terminology and validity predicate,
- family-tree data structures,
- structural metrics,
- reference skeleton,
- tests and Week 2 summary.

This means the original Week 3 design work has been pulled forward into Week 2.

### Week 3: Algorithm-Facing Operations

Primary deliverable:

```text
strengthened simplified reference implementation
```

Week 3 should build on the Week 2 skeleton by adding more algorithm-facing behavior without claiming theoretical linear time.

The implementation work should clarify:

- traversal or reconstruction logic,
- explicit skeleton-to-reference transition steps,
- additional oracle-based differential checks,
- early instrumentation hooks,
- limitations of the ordinary-list backend.

Important design questions:

- Does the simplified implementation assume valid input, or does it reject invalid input first?
- What does the function return besides the sorted sequence?
- Which intermediate structures should be exposed for debugging and experiments?
- Which theoretical operations are implemented faithfully, and which are simplified?

### Week 4: Minimal Implementation

Recommended new module:

```text
src/simplified_jordan.py
```

Recommended public function:

```python
simplified_jordan_sort(seq)
```

Recommended return shape:

```python
{
    "sorted": [...],
    "valid": True,
    "reason": None,
    "trace": [...],
    "stats": {...},
}
```

The first version may use ordinary Python lists. It does not need to achieve the theoretical linear-time bound.

Minimum implementation steps:

- run the oracle,
- reject or mark invalid input,
- build the rank map,
- build upper/lower pairs,
- convert pairs to intervals,
- build family-tree style structures,
- run the simplified reference pipeline,
- output a sorted sequence,
- compare against Python `sorted(seq)` and/or oracle output.

### Week 5: Testing and Debugging

Recommended new test module:

```text
tests/test_simplified_jordan.py
```

Required tests:

- empty sequence,
- singleton sequence,
- flat valid sequence,
- nested valid sequence,
- incremental valid generated cases,
- invalid upper crossing,
- invalid lower crossing,
- random invalid,
- mutation-based invalid.

Required differential check:

```text
For generated valid cases:
simplified_jordan_sort(seq)["sorted"] == sorted(seq)
```

Gate 2 pass criteria:

- `docs/design/simplified_algorithm_design.md` exists,
- `simplified_jordan_sort(seq)` runs,
- valid generated cases sort correctly,
- invalid generated cases are rejected or clearly marked,
- ordinary-list backend is supported,
- `tests/test_simplified_jordan.py` exists and passes.

Gate 2 fallback:

- If the full simplified pipeline is too large, implement interval-family construction, family-tree construction, and verified sorted output first.
- Clearly document which theoretical operations remain future work.

## Phase 3: Experiments and Analysis

Target time:

```text
Weeks 6-8
```

Main goal:

```text
Turn the code into thesis evidence.
```

Algorithms to compare:

- `python_sort`
- `merge_sort`
- `quick_sort`
- `sort_plus_laminarity_check`
- `simplified_jordan_reference`

Dataset families:

```text
valid:
- flat_valid
- nested_valid
- incremental_valid

invalid:
- invalid_upper_crossing
- invalid_lower_crossing
- random_invalid
- mutation_based_invalid
```

Optional later families:

- split-heavy valid,
- dense invalid.

First experiment sizes:

```text
[8, 16, 32, 64, 128, 256, 512]
```

Second experiment sizes, if performance allows:

```text
[1024, 2048, 4096, 8192]
```

Minimum CSV fields:

- `family`
- `n`
- `case_id`
- `seed`
- `oracle_valid`
- `algorithm`
- `time_ns`
- `correct`
- `reason`

Later instrumentation fields:

- `oracle_calls`
- `interval_count`
- `upper_intervals`
- `lower_intervals`
- `tree_nodes`
- `split_count`
- `traversal_steps`
- `fallback_count`
- `generator_attempts`

Expected outputs:

- `results/baseline_results.csv`
- `results/simplified_results.csv`
- `results/generator_stats.csv`
- `figures/runtime_by_family.png`
- `figures/valid_invalid_distribution.png`
- `figures/bottleneck_analysis.png`
- `docs/experiment_analysis_draft.md`

The goal is not to prove that the simplified reference implementation is faster than Python sort. It probably will not be. The goal is to show:

- correctness on generated cases,
- behavior across valid and invalid families,
- where the ordinary-list backend spends time,
- why the theoretical algorithm needs more advanced data structures.

Gate 3 pass criteria:

- baseline timing CSV exists,
- simplified algorithm timing CSV exists,
- generator or oracle statistics exist,
- at least three figures exist,
- experiment analysis draft exists.

Gate 3 fallback:

- If large sizes are too slow, reduce `n` but preserve family diversity and correctness statistics.

## Phase 4: Thesis Draft

Target time:

```text
Weeks 9-11
```

Main goal:

```text
Turn implementation and experiments into thesis chapters.
```

Recommended chapter structure:

1. Introduction
2. Background and Related Work
3. Jordan Sequences and Definitions
4. Correctness Oracle and Test Instance Generation
5. Simplified Jordan Sorting Framework
6. Implementation
7. Experimental Setup
8. Results and Analysis
9. Limitations
10. Conclusion and Future Work

Separate the algorithm chapter from the implementation chapter:

- The algorithm chapter should explain ideas, invariants, and pseudocode.
- The implementation chapter should explain code structure, ordinary-list backend, instrumentation, and engineering tradeoffs.

Gate 4 pass criteria:

- all main chapters have complete drafts,
- figures and CSV-derived results are integrated,
- terminology is consistent,
- code results and thesis claims match,
- limitations are explicit.

Gate 4 rule:

```text
After Week 9, avoid major algorithm redesign.
Only fix bugs that block experiments or thesis claims.
```

## Phase 5: Finalization and Buffer

Target time:

```text
Week 12 for minimum delivery.
Weeks 13-16 for high-quality finalization.
```

Week 12 should focus on:

- final experiments,
- missing tests,
- figure cleanup,
- terminology consistency,
- submission draft,
- repository reproducibility.

Weeks 13-16 should focus on:

- supervisor feedback,
- related work improvement,
- final graph polishing,
- code cleanup,
- README completion,
- defense slides,
- rehearsal.

Gate 5 pass criteria:

- supervisor feedback is addressed,
- bibliography is complete,
- repository can reproduce the main results,
- final PDF is ready,
- defense slides are ready.

## Risks

### Risk 1: Algorithm Implementation Overruns

The simplified reference implementation is the main risk.

Mitigation:

- write the design document before large code changes,
- start with an ordinary-list backend,
- prioritize correctness,
- use oracle and generated datasets for validation,
- document unimplemented theoretical operations as limitations.

### Risk 2: Generator Work Expands Too Much

The current generators are enough for the first experiment loop.

Mitigation:

- do not block Phase 2 on new generator families,
- treat dense invalid and split-heavy valid generators as Phase 3 or later additions,
- add generator instrumentation only when experiments need it.

### Risk 3: Experiments Only Measure Runtime

Runtime alone will not explain the algorithmic story.

Mitigation:

- add instrumentation,
- record intervals, tree nodes, attempts, fallback counts, and traversal work,
- connect bottlenecks to the missing theoretical data structures.

### Risk 4: Thesis Writing Starts Too Late

The thesis should not wait until all code is done.

Mitigation:

- start design notes in Week 3,
- convert docs into thesis chapters,
- begin experiment analysis as soon as first CSV files exist.

## Immediate Next Step

Current task:

```text
Finish Week 2 Day 7 documentation closure (week2_summary), then start
Week 3 Day 1 reference pipeline strengthening.
```

Week 3 reference pipeline should follow the fixed Day 1 contract:

```text
interval -> family_tree -> pipeline trace/backend metadata -> structure-aware experiment support.
```
