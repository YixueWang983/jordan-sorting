# Trace recheck and targeted split qualification — 2026-10-15

This increment preserves the original 140 inputs and every byte of their v1/v2
archives. No production tree or sorting-core code changes. The next executions
are a read-only audit of old records and a separately identified 12-case batch.
There is no 380-input expansion, optimization search or formal performance run.

## New read-only trace predicates

`qualification_trace_semantics.py` checks exact initialization fields, all seven
events in each round, their order and types, boundary selections, insertion and
output-anchor fields, live list sizes/owners, and split/skip semantics.
Performed splits require a positive live source size; output IDs exist exactly
when their sizes are positive; sizes conserve the source; output IDs cannot
alias or overwrite another live list. Skips require zero sizes, null related
IDs/acquired side, and the established reason. Input-derived neighbor and anchor
checks use no production trace validator or sorter.

Related counters are reconstructed from trace. Tree scan observations are only
checked as nonnegative integers because the actual backend visits are not in
these records. This checker does not decode physical trees or prove locality.

Historical mode validates the old producing commit against its recorded source
hashes using Git objects. The report separately records the new checker commit
and source hashes. It does not relabel old executions with a new source version.
The original archive is never resealed. Default current-source mode remains
strict and rejects changed sources; historical auditing is explicit.

## Frozen supplementary set

Reuse `values_for(n,k,mirror)` from the existing middle-split construction:
`n=128,129`, `k=3,7,19`, original and mirror, exactly 12 candidates in that order.
The exact values, profiles and SHA-256 are committed in `preselected_split_inputs.json`
with `preselected_split_plan.json` before execution. There are no retries or
replacements. This set has a separate dataset/schema/measurement identity and
must not be pooled with the 140 as independent random samples.

Both backends run synchronous checked v2 (three independent instances) and
separate fresh minimal, with tree `detailed_work=False`. Each case shares a
180-second worker budget; the entire small campaign also has 180 seconds.
The first ERROR/TIMEOUT stops later cases and preserves committed mode records.
A target only passes if actual primary traces contain a two-sided nonempty
split whose smaller output has size `k`; correct output alone is insufficient.

For every performed split, derive source/output/smaller-side sizes, source and
output owners, and direct subsequent insertions / next split of each output ID.
Only events before that output's next split are associated with it; this is not
an arbitrary descendant-lineage claim. Finite owners and later updates are
reported, not presumed present from the generating parameters. Missing coverage
remains explicit rather than triggering unplanned new generation.

## Measurement tools, kept separate from actual samples

`matched_measurement.py` and `validate_matched_measurement.py` implement:

- ascending common batches 1..128, three repetitions/backend/candidate; select
  the first B where both medians reach 10 ms;
- five warmup calls/backend, then 20 paired batches using the common frozen B,
  input order shuffled by the frozen seed, backend first alternating by case
  index and round (ten first positions each over the samples);
- initialization/core/output recovery plus batch loop and append inside the
  timer; comparisons, capture, GC precollection and durable writes outside;
- errors, real process timeouts and partial records retained, no silent retries;
- independent output/schedule/batch-choice/median/R7-IQR/ratio reconstruction.

Original numerical measurement rules remain unchanged. Each dataset retains its
own input identity and reports, calibration limit 600 seconds, formal campaign
limit 1800 seconds and formal per-case limit 120 seconds. The targeted-set
extension is declared separately; calibration or formal samples are not run as
part of this increment. No calibration settings are selected by favorable ratios.

Actual tool entry checks the qualified archive, preserves its producing commit,
and verifies production `src/` hashes are identical to the measurement source.
Changed production requires renewed qualification. Formal execution additionally
requires independently validated same-source calibration, matching interpreter,
platform, machine, CPU/core/RAM metadata and GC configuration, plus an explicit
manual representation/locality/cost review receipt bound to production sources.
Power status is recorded separately at each stage. A receipt is a provenance
record of human review, not an automatic proof. No such approval is created here.

## Tests and remaining gates

66 targeted methods pass, zero skipped: the previous 47 plus 19 new methods
(3 trace semantics, 3 target-set plumbing, 13 measurement-tool mechanics).
Trace negative scenarios are subcases, not extra test methods. Measurement
fixtures use real small minimal calls with synthetic clocks and mocked
qualification/review metadata; their ratios are not observed performance.
Actual timeout subprocess tests exercise durable recovery. The source, protocol
and tests must be committed before the new 12-case qualification and final
read-only recheck reports are generated.

The manual cost/representation/locality review remains open. Common qualification,
trace consistency and the supplemental batch do not close it. Thesis results
must not present historical pilot timings as the current implementation's formal
comparison. Implementation/method integration remains a subsequent manuscript
step, after the evidence boundaries above are preserved.

## 执行后的版本补记

12例实际执行源码为 `668371f`，全部通过。其后仅测量工具增加跨数据集校准拒错，
提交 `ebb3dc1`；生产及资格路径不变。14项测量工具回归通过，含13项重复及1项新增，
与先前66项合并为67个不同方法。最终检查器分别只读复核原140和补充12的旧生产记录，
不将原执行改标为新源码，也不因检查工具身份变化重新跑排序。准确计数、实际覆盖边界
与版本索引见[结果归档](../validation/split_trace_followup_20261015/README.md)。
