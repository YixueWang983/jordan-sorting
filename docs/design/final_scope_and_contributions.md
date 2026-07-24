# Final Scope and Contributions

Last updated: 2026-07-24

## Thesis Position

This thesis studies a simplified Jordan-sorting reference framework. The project
does not claim to be a full implementation of the theoretical linear-time
Jordan-sorting algorithms.

The implementation is a correctness-oriented and experiment-oriented framework
that makes Jordan-sequence recognition, structure extraction, reference
execution, and cost diagnostics testable.

## Contributions

1. Reconstruct and explain the relevant 1986 and 1990 Jordan-sorting ideas from
   an implementation perspective.
2. Define a testable candidate-sequence model with upper/lower pair families,
   rank intervals, laminarity, and crossing diagnostics.
3. Implement a correctness oracle, controlled generators, family-tree structures,
   structural metrics, and an ordinary-list reference backend.
4. Build reproducible experiment runners that compare ordinary sorting,
   validation-plus-sort, and the simplified reference pipeline.
5. Use structural metrics and operation counters to explain where the ordinary
   implementation differs from the theoretical linear-time framework.

## Non-Contributions

This thesis does not implement:

- level-linked search trees;
- heterogeneous finger trees;
- a full dynamic split/update engine;
- polygon clipping;
- a proof or empirical demonstration of linear-time Jordan sorting;
- sorted-order recovery from the theoretical family-tree operations.

Current sorted output is obtained from `oracle_result["sorted"]`. This is an
explicit reference-framework choice, not a hidden claim of theoretical
algorithmic completeness.

## Success Criteria

The thesis is successful if:

1. the reference framework behaves correctly on all tested inputs;
2. valid/invalid classification agrees with the oracle;
3. generator coverage is quantified with structural and crossing metrics;
4. formal experiments are reproducible from scripts and run manifests;
5. ordinary-list backend costs can be explained by validation, family-tree
   construction, structure profiling, and sorted-output handling;
6. theory, implementation, and missing pieces are clearly separated;
7. every conclusion is supported by code, CSV outputs, generated reports, or
   cited papers.

## Supervisor Confirmation Questions

1. Is an oracle-sorted-output reference framework acceptable for the thesis
   scope if the non-linear-time boundary is made explicit?
2. Must the implementation recover sorted order from family-tree operations, or
   is that a future-work boundary?
3. Can the ordinary-list quadratic implementation be used as an experimental
   object for explaining the gap to the theory?
4. Can polygon clipping remain a paper-context discussion without implementing a
   clipping pipeline?
5. Should the final title include `Reference Framework` to avoid implying a full
   theoretical implementation?

