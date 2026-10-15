# ID lifecycle repair and calibration freeze (2026-10-15)

This source commit freezes the trace checker before read-only archive rechecks
and actual calibration. No production sorter, input selection, timing rule or
prior archive is changed. The result commit records the exact source identity.

- Check all list allocations against `seen_ids` for the lifetime of one trace.
  Initialization seeds the set; singleton creation and nonempty split outputs
  require new IDs; retirement does not erase history. Boundary insertion keeps
  the existing live ID. No monotonic numbering assumption is added.
- Three new negative test methods failed on the preceding checker (eight backend/
  side subcases accepted incorrectly). After repair, 37 targeted methods pass,
  including four new lifecycle methods and existing qualification/measurement
  tests. These counts are not additional production-input qualifications.
- Read both the original 140 and separate 12 archives using historical audit;
  preserve old files and hashes, report producer and new checker separately.
  Do not rerun either qualification batch.
- Calibrate common and targeted_split separately, sequentially on this machine.
  Unchanged candidates B=1,2,4,8,16,32,64,128; three batches/backend/candidate;
  select the first common B with both medians >=10ms. Explicit tree
  detailed_work=False, minimal, fresh public calls and output checks.
- Each dataset has its existing 600-second calibration budget. Keep every
  attempted batch and first failure; no retry, input replacement or candidate
  adjustment. A failure is evidence, not permission to report completion.
- Use distinct external output directories while the source checkout remains
  clean; independently validate each archive before copying it into Git.
  Do not run tests, checked qualification, compilation or profiling concurrently
  with timing. No formal sample, no fabricated manual-review approval.

The calibration outcomes and B tables will be archived separately from old
pilot/performance results. Calibration does not close cost/representation/
locality proof review or certify the efficient-backend minimum.
