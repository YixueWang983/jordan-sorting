# Final Scope Amendment: Ordinary-List Paper Algorithm

Last updated: 2026-08-06

Status: current implementation and evaluation scope for thesis drafting.

## Relationship to the Historical Decision

`docs/design/final_scope_and_contributions.md` preserves the minimum
reference-framework scope accepted by the supervisor on 2026-07-24. It is a
historical decision record and is not silently rewritten by this amendment.

After that decision, the project direction was expanded to implement and
evaluate an ordinary-list reconstruction of the 1990 Simplified Jordan Sorting
algorithm. This amendment records the resulting implementation facts and the
scope boundaries that must govern Week 13 thesis synthesis.

This amendment does not claim that the expanded implementation was already
part of the 2026-07-24 supervisor decision. It supersedes the historical file
only when describing current repository behavior and current technical
contributions.

## Two Distinct Sorting Paths

The repository now contains two intentionally different paths.

### Oracle-Backed Reference Pipeline

```text
simplified_jordan_reference
simplified_jordan_sort
```

This path remains a correctness-oriented reference framework. It performs
oracle validation, family-tree construction, structural profiling, and
reference-output work. Its sorted output remains oracle-backed.

Required thesis statement:

```text
The simplified reference pipeline is an oracle-backed experimental baseline;
it is not the independent paper-algorithm implementation.
```

### Ordinary-List Paper Algorithm

```text
paper_jordan_sort_valid
paper_jordan_diagnostics_valid
```

For a pre-certified valid input, the paper core:

- executes the paper-facing Step 1, Step 2, and Step 3(a-c) control flow;
- maintains partial sorted order and upper/lower sibling-list families;
- uses ordinary Python-list sibling-list storage;
- recovers final output from `state.partial_order.to_list()`;
- does not read `oracle_result["sorted"]`;
- has `uses_oracle_sorted_output = False` as an implementation boundary.

The certification and experiment wrappers may call the oracle to establish the
valid-input precondition and compare correctness outside the timed paper call.
That external certification does not supply the paper core's sorted output.

Required thesis statement:

```text
The paper ordinary-list implementation independently recovers sorted order
from maintained algorithm state for oracle-certified valid inputs.
```

## Current Contributions

The current thesis implementation contributions are:

1. a correctness oracle, controlled generators, structural profiles, and an
   oracle-backed reference pipeline used as infrastructure and baseline;
2. an executable ordinary-list reconstruction of the 1990 paper's incremental
   Step 1/2/3 sorting control flow;
3. explicit partial-order and sibling-list ownership data structures with
   local safety checks, rollback, and invariant validation;
4. deterministic replay and full state-audit support outside timed paths;
5. execution policies that separate trace, counters, and complete validation
   from the minimal timed paper call;
6. immutable pilot and formal evidence with independent fail-closed validators;
7. an empirical comparison of the implemented ordinary-list paper call,
   oracle-backed reference pipeline, and Python sort under documented timing
   scopes.

## Backend Boundary

The implemented backend uses ordinary Python lists. It may perform linear
scans, list materialization, slicing, and ownership rebinding. These choices
support correctness, observability, and reproducible evaluation, but they do
not reproduce the theoretical data-structure complexity of the paper.

The project does not implement:

- level-linked search trees;
- heterogeneous finger trees;
- the theoretical linear-time dynamic split/update backend;
- polygon clipping.

## Evaluation Boundary

The Week 12 formal experiment evaluates oracle-certified valid-input sorting.
Recognition remains a separate experimental question.

The frozen timing scopes are different:

- `simplified_jordan_reference` is timed as its complete oracle-backed
  reference pipeline;
- `paper_jordan_sort_valid` is timed only as the pre-certified `minimal`
  sorting call;
- oracle certification and checked paper diagnostics occur outside paper
  timing.

Paper/reference ratios are therefore pipeline-scope comparisons. They are not
like-for-like end-to-end speedups.

## Non-Claims

The thesis must not claim:

- that the ordinary-list implementation runs in linear time;
- that five tested sizes establish asymptotic complexity;
- that theoretical level-linked or heterogeneous finger-tree structures were
  implemented;
- that the reference and paper timing scopes are identical;
- that structure or checked-counter correlations are causal;
- that valid-input sorting results establish invalid-input recognition;
- that flat, nested, and incremental generators represent every Jordan
  sequence distribution.

## Authority for Week 13

Week 13 must use these documents together:

```text
historical supervisor decision:
    docs/design/final_scope_and_contributions.md

current technical scope amendment:
    docs/design/final_scope_amendment_paper_ordinary_list.md

algorithm specification:
    docs/design/paper_algorithm_ordinary_list.md

formal empirical result:
    docs/analysis/week12_formal_sorting_analysis.md
```

No thesis chapter may use the historical statement that all current sorted
output comes from `oracle_result["sorted"]` without restricting that statement
to the reference pipeline.
