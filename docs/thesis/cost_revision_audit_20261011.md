# Cost explanation revision and qualification evidence

Date: 2026-10-11. Base checkout: `b6a407461c2f94a4b491016376861142f4b14577` plus the recorded local changes. The sorting core in `src/` is unchanged.

This revision addresses the external review's cost and evidence findings. It does not implement a finger-search backend or create new sorting-performance results.

## Changes

- Explain that both insertion boundaries reconstruct the entire sibling list.
- Derive `(m-1)^2` existing-ID copies for increasing input of length `2m`, even with zero splits. This is a source-derived quadratic lower bound on copying, not a fitted curve or tight overall bound.
- Explain always-on membership scans and per-ancestor containing-list scans in `minimal`.
- Define split scan/copy counters as logical input volume; preserve archived values and distinguish them from element accesses and runtime.
- Mark historical Results captions and clarify their timing scope; no historical numeric cell or archived plot is replaced.
- Label README's 537-test result as historical; preserve the separate first-revision record of 133 targeted tests.
- Move the backend progress checkpoint to October 16 and integration-validation deadline to October 18; preserve October 22 full draft and October 25 supervisor review.
- Reference literature for the future backend; implement our code independently without copying or porting third-party implementations.

## Current verification

- 155 targeted tests passed. Includes the four core/policy suites, the extended validator, the existing preflight runner, and the new probe's scope and failure-control tests. This is not a full repository suite.
- 16 frozen large-input qualification cases passed with no errors/timeouts. Both public modes were separately checked against external output criteria. Full checked/replay remained enabled.
- 16 separate monotone cost probes matched the copy formula, with correct output and zero splits.
- Read-only archive verification checked 79 nested/top-level manifest entries plus source hashes, frozen configuration and recorded input/output identities. It is not a rerun of the qualification campaign.
- Fresh LaTeX build: 76 pages; final compiler and bibliography logs have no warnings, errors, undefined references or overfull/underfull boxes. Visual review is recorded in the [build record](cost_revision_build_record_20261011.json). All 76 pages were checked through contact sheets, with detailed inspection of nine affected pages; the final abstract fits one page. The 649 other original tracked files, including the sorting core and historical evidence, retain their original hashes.

The command used for the regression run, from the repository root, was:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:experiments:tests python3 -m unittest test_paper_jordan test_paper_jordan_sort test_sibling_list_backend test_paper_execution_policy test_validate_ordinary_list_extended test_preflight_next_stage test_probe_large_qualification -v
```

The [qualification evidence](../validation/cost_and_qualification_20261011/README.md) provides raw records, reproducible commands and limitations. The portable review package includes the current PDF, complete tracked repository snapshot with new files, original test/build logs, current source hashes, package manifest and verification scripts. No authentication configuration or local toolchain binaries are included.

## Evidence boundary

The resource total of 88.277 seconds covers validation work, not sorting time. One deep-nesting construction at each length does not establish eligibility for all heavy inputs, the entire 380-input target, or independent random sampling. Same-core replay checks execution/state consistency, not an independent algorithm.

The first revision's 74-page PDF and 133-test audit remain historical records. Current performance still requires new qualified timing evidence. Legacy timing archives and their original claims retain their existing version identities. Formal timing, backend implementation and a complete supervisor-review draft remain pending.
