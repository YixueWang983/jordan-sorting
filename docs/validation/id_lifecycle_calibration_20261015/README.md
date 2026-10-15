# ID lifecycle repair, read-only rechecks and actual calibration

This is a new increment after `2df69b3`. Execution/checking tools were committed
as **`c5b5ac3fd20cf89173916f49187f28aafc633434`** before both actual campaigns.
The later results commit does not replace this producer identity. No production
sorter/tree code, frozen input selection or measurement rule changed.

## Repair and regression

`seen_ids` lasts for the complete trace, seeded by both initial list IDs.
Singleton creation and every nonempty split output require never-before-seen
IDs. Retiring a source removes it only from `live`; boundary insertion retains
its live ID. The checker does not add an unrelated monotone-numbering rule.

The preceding checker was actually exercised with three negative test methods:
source-ID reuse on either output, later singleton reuse, and later split reuse
of an earlier retired ID. Eight backend/side subcases were wrongly accepted;
`before_fix_negative_tests.log` preserves that expected pre-fix failure.
Mutations also rename all subsequent references, so stale references do not
mask the lifecycle defect. After repair, **37 targeted test methods pass, zero
skipped**, including four new lifecycle methods and existing qualification and
measurement regressions. Normal repeated boundary insertion and globally
renumbered fresh IDs also pass. The eight subcases are not eight extra methods.

## Read-only archive rechecks

| Existing dataset | Original producer | New checker | Result |
| --- | --- | --- | --- |
| Common 140 | `3cafb44` | `c5b5ac3` | 140 PASS, 560 mode records |
| Targeted split 12 | `668371f` | `c5b5ac3` | 12 PASS, 48 mode records |

`original_140_recheck.json` and `split_12_recheck.json` retain full identities.
These runs read saved records and source Git blobs; they did not rerun sorting
qualification or rewrite/reseal old archives. `prior_archive_preservation.json`
checks 450, 995 and 103 existing hashes in the v1, v2 and split-followup archives.
The original common selection hash remains
`c8d8f34f7dce619a87d54cffd8567255c80340742f00de072eb5ca771991b17b`;
the targeted selection hash remains
`357220a65f52059df647be4189531e981bbef0e2aa13fd744d19ce40819c0454`.

## Actual calibration, not formal samples

Both datasets ran once, sequentially with a clean source checkout and separate
600-second budgets. No testing, qualification campaign, compilation or profiling
ran concurrently. Every actual timed batch uses `perf_counter_ns`, fresh public
minimal calls, explicit tree `detailed_work=False`, GC enabled and output checks.
The runner's preflight reads saved qualification evidence; that is not a new
checked sorting run. Environment/source/clock/GC observations are in each archive.

For each input the unchanged rule tries B=1,2,4,8,16,32,64,128, three batches per
backend per attempted B, alternating first position. The first B with both
median batch durations >=10ms is selected. All tried candidates and outputs
remain in `jobs/*/records`; no case was retried, replaced, dropped or tuned to a
favorable speed ratio. Independent validators reconstructed both complete
archives, including every attempted batch, outputs, decisions and manifests.

| Dataset | PASS | B distribution (B: input count) | Timed batches | Sorting calls inside batches |
| --- | ---: | --- | ---: | ---: |
| Common | 140 | 1:24, 2:20, 4:20, 8:28, 16:21, 32:27 | 3,018 | 17,976 |
| Targeted split | 12 | 8:12 | 288 | 1,080 |

No ERROR, TIMEOUT or NOT_RUN remains. `*_batch_table.json` gives each case's
input hash, n, chosen B, attempted Bs, number of batches/calls and chosen median
batch durations. The smallest chosen median across either backend/common case
was 10,018,458ns; all twelve targeted cases' medians also exceed the threshold.
These are clock-granularity checks, not accuracy/power guarantees or speed claims.

Controller wall times including preflight/storage were about 58.35s and 6.68s.
They are resource observations, not sorting performance. Each batch is one
observation; the 19,056 contained calls are not independent statistical samples.
Datasets/mirrors remain dependent constructions and are analyzed separately.
**Zero formal sample batches ran.** `performance_eligible=False` remains explicit.

## Review and thesis scope

[Manual review notes](../../development/proof_review_calibration_20261015.md)
record source-level header/identity, join/rib checks and an actual visual reading
of original locality pp.88–89. Full representation preservation, mixed-potential
and extended-locality review remains open; no approved review receipt was made.
The thesis implementation/method chapters and necessary stale scope statements
are updated. The rebuilt PDF remains **68 pages**; build/page/visual evidence is recorded
separately in `thesis_review/` and the deliverable is `output/pdf/jordan_thesis_20261015.pdf`.
Historical result numbers and data are untouched. Efficient-backend minimum
acceptance and formal measurement are not inferred from calibration success.

## Reproduce

Use source `c5b5ac3` with its Python/runtime dependencies. Rechecks are read-only:

```sh
PYTHONPATH=src:experiments python3 experiments/validate_common_qualification_v2.py \
  docs/validation/common_qualification_v2_20261015/qualification --historical
PYTHONPATH=src:experiments python3 experiments/validate_common_qualification_v2.py \
  docs/validation/split_trace_followup_20261015/qualification --dataset targeted_split --historical
```

For each dataset, a new actual calibration requires a new output directory and
clean checkout; never overwrite these records:

```sh
PYTHONPATH=src:experiments python3 experiments/matched_measurement.py \
  --stage calibration --dataset common \
  --qualification docs/validation/common_qualification_v2_20261015/qualification \
  --output /absolute/path/to/new-common-calibration
PYTHONPATH=src:experiments python3 experiments/validate_matched_measurement.py \
  docs/validation/id_lifecycle_calibration_20261015/calibration_common \
  --qualification docs/validation/common_qualification_v2_20261015/qualification
```

For targeted_split use that dataset flag, its existing qualification directory
and the separate `calibration_targeted_split` archive. Calibration decisions are
bound to source, configuration and environment; future changes must be checked
before reusing B. Formal execution additionally requires actual proof-review
acceptance and reviewed tooling; the user has not requested formal sampling here.
