# Theory-to-Implementation Mapping

Last updated: 2026-07-27

## Purpose

This document maps the theoretical Jordan-sorting concepts discussed in the
source papers to the current codebase. It is intentionally explicit about what is
implemented, simplified, or out of scope.

## Mapping Table

| Theory concept / step | Current implementation | Status |
| --- | --- | --- |
| candidate sequence | all public inputs | complete |
| upper/lower pairs | `src/oracle.py`, `src/jordan_operations.py` | complete |
| rank map | `src/oracle.py` | complete, uses ordinary sorting |
| rank intervals | `src/oracle.py`, `src/jordan_operations.py` | complete |
| laminarity recognition | `src/oracle.py` | complete, `O(n^2)` |
| family trees | `src/family_tree.py` | complete for static interval families |
| sibling lists | `src/sibling_list_backend.py` | complete ordinary-list backend |
| containment relation | `src/family_tree.py`, `src/stats.py` | complete |
| split/search/update | `src/sibling_list_backend.py`, `src/paper_jordan.py` | implemented with ordinary lists |
| sorted-order recovery | `src/paper_jordan_sort.py` | implemented for pre-certified valid inputs |
| level-linked structures | none | out of scope |
| polygon clipping | paper-context discussion | out of scope |

## 1986 and 1990 Algorithm Boundary

The 1986 and 1990 algorithms use specialized data structures to obtain linear
time. The simplified 1990 presentation reduces some conceptual complexity, but
the linear-time result still depends on data-structure behavior that the current
ordinary-list backend does not implement.

This project replaces those structures with explicit Python lists, family-tree
objects, and diagnostic scans. This makes correctness and structure observable,
but it also introduces `O(n^2)` behavior in recognition, tree construction, and
structure profiling.

## Complexity Sources in the Current Code

Current reference-framework stages:

```text
oracle laminarity check       O(n^2)
family-tree interval checks   O(n^2)
parent candidate scan         O(n^2)
containment-pair statistics   O(n^2)
ordinary Python sorting       O(n log n)
```

The paper ordinary-list path avoids global sorting and rank-map recovery, but
its Python backend includes linear sibling scans/list materialization and
correctness-first global ownership validation after committed splits. Its
current runtime is therefore not evidence of the theoretical linear bound.

The project therefore cannot use current runtime results to claim linear-time
Jordan sorting. Runtime and operation counters describe the ordinary-list
reference framework only.

## Oracle, Recognition, and Sorting

The oracle decides whether a candidate sequence satisfies the project validity
predicate:

```text
distinct values
and upper family laminar
and lower family laminar
```

Recognition is not the same as sorting. The reference pipeline validates and
structures the input, but takes sorted output from `oracle_result["sorted"]`.
The separate paper ordinary-list implementation recovers sorted order from its
maintained partial order, but assumes that validity has already been certified.

## Polygon Clipping Relationship

The simplified Jordan-sorting paper relates the sorting framework to polygon
clipping through boundary-order and structural-processing ideas. This thesis uses
polygon clipping as context, but does not implement a clipping pipeline.
