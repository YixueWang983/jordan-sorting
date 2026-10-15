# Full common qualification v2 — 2026-10-15

**140 PASS, 0 ERROR, 0 TIMEOUT, 0 NOT_RUN.** The independent archive validator
rebuilds the same result from the complete records. This closes qualification
of the original frozen set for the producing source/configuration below.
It does **not** accept the efficient-backend minimum or enable formal timing.

Producing source: `3cafb44ac1e127f7c9c208c7a23999a8e0c401ce`, committed before
execution with a clean worktree. Results are saved by a later archive commit.
The production `src/`, thesis, historical data and results trees are unchanged
from `16b31cc`. No tree optimization or measurement was performed.

Selection SHA-256 (unchanged):
`c8d8f34f7dce619a87d54cffd8567255c80340742f00de072eb5ca771991b17b`.
All original values, input order, ten sizes, four strata and mirror origins are
preserved. Each size retains 2 strict-flat and 4 each low/medium/heavy inputs.
Unique rank hashes do not make mirrors or related constructions independent
statistical samples. The old v1 TIMEOUT/NOT_RUN archive and all its 450 hashed
files remain unchanged.

## Coverage limit discovered in this batch

Each backend's **primary checked traces** contain 3,788 performed splits:
1,894 with empty left side and 1,894 with empty right side. There are **zero
splits with both output sides nonempty**. Raw traces were independently counted
again after the validator reported this result; `coverage_audit.json` records
that reconstruction. Per backend the split totals by stratum are 0 strict-flat,
844 low, 2,924 medium and 20 heavy.

Nesting strata therefore do not certify coverage of split ratios. This is a
limitation of the frozen input distribution, not an observed sorting error.
The selected cases were not changed or replaced after seeing these results.
Earlier targeted two-sided split evidence remains separate; it is not counted
as part of this campaign. A later performance comparison on these inputs must
retain this limitation and cannot claim representative two-sided split costs.
Any supplementary coverage set would need its own predeclared identity and
qualification, not retroactive insertion into this successful set.

## What actually ran

| Evidence | Count |
| --- | ---: |
| Selected input statuses | 140 |
| Synchronous v2 runs | 280 (140 per backend) |
| Separate fresh public minimal runs | 280 (140 per backend) |
| Durable mode records | 560 |
| Synchronous completed-prefix comparisons | 27,566 per backend |
| Final fresh checked replays | 140 per backend |
| Observed initialized instances | 560 per backend: 420 checked + 140 minimal |
| Primary checked split events | 3,788 per backend |
| Primary checked two-sided nonempty splits | 0 per backend |

Two independent checked states advance in the same production loop; both are
locally/history audited and compared at each prefix. A third fresh checked
instance replays at the end, with a fresh main-state audit before comparison.
A separate minimal call follows. All instances retain the selected backend and
configuration; tree `detailed_work=False` is explicit. The v2 controller's
existing independence checks reject mutable registry/node/handle sharing.
External prefix and final output expectations never enter the sorting core.

Replayed/peer updates are not counted again as independent inputs, primary
prefixes or split observations. This is v2's versioned coverage, **not** the old
fresh-constructor-at-every-prefix schedule. The independent archive checker
validates the recorded coverage and output hashes; it does not independently
rerun all states or prove their physical invariants from integrity hashes.

## Validation and resource scope

`tests.log`: **47 methods passed, zero skipped**, including 13 new full-v2
runner/validator tests, 11 synchronous-controller tests, 6 prior refactor
mechanical tests, and 17 existing common-qualification/pilot tests. These were
run before the freeze. The small fixture plans and mocked clean-source metadata
are explicitly test-only. The earlier full production regression totals were
not rerun or added to this number.

The tests exercise explicit v2 routing, actual initialization/config checks,
wrong/missing coverage, actual process termination after a completed mode,
recovered failure archives, input/config/environment/coverage/summary tampering
after resealing, and optimization-mode rejection. Ordinary Python errors and
serialization failures are preserved. Disk I/O failures remain fatal and may
leave an incomplete archive; they cannot produce a passing result.

The original per-case budget remained 180 seconds shared by **both** backends
and all checks/startup/persistence; the full budget remained 1800 seconds. There
was one attempt, no retry, no filtered failure and no budget increase. Summed
worker resource wall time is about 713.56 seconds; this includes observation
and persistence and is **not sorting performance**. No warmup, calibration or
formal sample was run. `resource_review.json` records the exact totals.

## Reproduction and contents

Use the producing revision above (or this results-only revision, whose bound
Python sources match), Python 3.12 without `-O`, and the archived environment.
The validator also checks that the named producing Git commit actually contains
the bound source blobs; a plausible-looking arbitrary commit ID is insufficient.

```sh
PYTHONPATH=src:experiments python3 experiments/validate_common_qualification_v2.py \
  docs/validation/common_qualification_v2_20261015/qualification

# Fresh execution requires a clean worktree and a nonexistent output directory.
PYTHONPATH=src:experiments python3 experiments/qualify_common_inputs_v2.py \
  --output /absolute/path/to/new-qualification-v2
```

- `preselected_plan.json`: rules committed before execution.
- `qualification/`: exact selection and measurement rules, source/environment,
  requests, per-case statuses, per-mode gzip records, progress, summary and manifest.
- `recheck_report.json`: independent full archive reconstruction.
- `source_binding.json`: producing revision, immutable prior archive and directory identities.
- `coverage_audit.json`: post-run raw primary-trace split coverage reconstruction.
- `resource_review.json`: resource accounting only.
- `SHA256SUMS.json`: hashes of this archive, excluding itself.

Next steps are independent batch calibration and formal runner/validator
acceptance, alongside the outstanding manual representation/locality/cost
review. Any subsequent source/config changes require assessment and renewed
qualification of affected execution paths. `performance_eligible=false` and
`efficient_backend_accepted=false` remain explicit.
