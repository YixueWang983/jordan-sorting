# Implementation Revision Claims and Evidence

Date: 2026-10-11. Scope: first revision for the planned 2026-10-25 supervisor review.

This record supplements the historical 46-claim inventory. It corrects the thesis description of the current ordinary-list implementation after rollback removal and preserves the original scope of the archived experiments. It does not add new runtime results or certify a finger-tree implementation.

## Version Bindings

| Role | Identity | Applicable evidence |
| --- | --- | --- |
| Measured formal implementation | `98868b1b705f6d5f22404ee8ad7b88ad7a834f52` | Week 12 manifest, original protocol, 60 cases and 3,600 measured rows |
| Rollback removal | `337903ab725c72744fbe617feadbd1a6d4cbeaff` | Changes to insertion, split, public-call contracts and failure tests |
| Current implementation inspected | `6f7468324672e6f5abe9d95862cd5f296b792614` | Current source and relevant regression tests; no new formal timing |
| Current thesis revision | Working-tree changes based on the current implementation above | This amendment record and the separate revision audit; not included in the historical thesis audit |

The exact source hashes are recorded in `revision_source_bindings_20261011.json`. The historical pilot and formal manifests retain their original source identities. Historical Markdown drafts, claim inventory, audit reports, result CSVs and figures are not rewritten by this revision.

## Version Specific Amendments

| Claim | Current wording and boundary | Evidence | Thesis locations |
| --- | --- | --- | --- |
| I-05, current version | Ordinary Python lists retain split planning, ownership updates, local safety and invariant checks. A failed internal update propagates its exception; already performed mutations are not restored, and failed state must be discarded. | `src/sibling_list_backend.py`: `commit_split`; `src/paper_jordan.py`: `_step3a`; `src/paper_jordan_sort.py`: public entry points | Algorithm ownership section; Implementation versions, Step 3(a), Step 3(b), output and validation sections |
| I-05, retained planning | `SplitPlan` supports boundary partitions, stale-plan checks, ordered-set conservation and update preparation. New lists and normal partition copies remain necessary update work. | `src/sibling_list_backend.py`: `split_by_key`, `_validate_live_split_plan`, `commit_split`, `_validate_split_commit_postconditions` | Implementation Step 3(b); Algorithm ownership section |
| I-07, current version | Policies still control complete backend audits, trace and selected counters. Local checks, stage results and output recovery remain; no policy restores rollback in the revised core. Logical counters do not account for every backup or Python copy. | `src/paper_execution_policy.py`; `src/paper_jordan.py`; `src/sibling_list_backend.py`; historical/current source comparison | Implementation policy section; Method paper implementation section |
| I-09 and L-01/L-09 | The implemented backend remains ordinary-list. A heterogeneous finger-tree specification exists, but no such backend is implemented or measured here. Removing rollback does not establish a linear-time bound. | Current `src` inventory; `docs/development/heterogeneous_finger_backend_spec.md` | Implementation complexity; Limitations backend; Introduction contributions; Conclusion future work |
| Historical M/R/E claims | Original protocol, numerical results and exploratory associations continue to describe their archived versions. In particular, the measured minimal implementation included recovery preparation. Successful calls do not imply that a rollback occurred. | Week 11 and Week 12 manifests and source bindings; historical split implementation | Method experiment stages and timing scope; Results evidence status and boundary; Abstract; Introduction; Conclusion |
| Revision performance boundary | No new runtime or speedup is claimed for the revised core. Quantifying the effect of rollback removal requires an appropriate matched experiment. | New formal timing absent from this revision; historical evidence identity | Implementation versions and policy; Results; Limitations version section; Abstract; Conclusion |

These amendments qualify the historical inventory by version. They do not silently replace the historical I-05 wording or alter the SHA-256 printed for that inventory in the traceability appendix.

## Executable Failure Contract Evidence

The existing tests distinguish failed updates from successful valid-input sorting:

- `test_step3a_boundary_failure_propagates_and_state_must_be_discarded` checks propagation after registration may have occurred.
- `test_commit_split_propagates_final_invariant_failure_without_restoration` checks the checked split failure contract.
- `test_minimal_commit_propagates_local_failure_without_restoration` checks the minimal local postcondition path.
- `test_minimal_local_postconditions_detect_ownership_corruption` retains detection without promising recovery.
- `test_split_failure_aborts_public_calls_without_output_or_retry` checks public checked/minimal sorting and diagnostics, one split attempt, propagation of the original exception and no output recovery.

On 2026-10-11, the four relevant test modules (`test_paper_jordan`, `test_paper_jordan_sort`, `test_sibling_list_backend`, `test_paper_execution_policy`) ran successfully: **133 tests passed**. This is a targeted regression run on the current code, not a full repository run, a new exhaustive campaign or a performance experiment. Source files and tests were not changed.

## Review Boundary

This first revision updates failure semantics and evidence attribution. It does not yet integrate the expanded-input validation campaign as a new empirical chapter, generate a larger dataset, run expanded timing, implement the proposed backend, or change numerical results. These remain separate stages of the development plan. The build, text, visual and integrity checks for this revision are recorded in `revision_audit_20261011.md`.
