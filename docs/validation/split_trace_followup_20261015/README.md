# Trace semantics follow-up and targeted split qualification

**The original 140-case archive passes the strengthened read-only audit. The
separate 12-case split set passes actual v2 qualification and archive rebuild.**
No production sorting/tree code changed. No original input or archive was
replaced, resealed or re-executed; no calibration campaign or formal sample ran.

## Version identities

| Object | Producing/checking source |
| --- | --- |
| Original 140 sorting executions (unchanged) | `3cafb44ac1e127f7c9c208c7a23999a8e0c401ce` |
| Original result archive | `4a952c43bfb586cb7ea11f11a271fcb6847ad5a4` |
| New 12-case execution and initial checks | `668371f0701984112b6a32830ce88390c5ff4d36` |
| Final read-only checks and measurement guard | `ebb3dc1` (full identity in reports) |
| This evidence archive | Later results-only commit |

The post-execution guard only rejects a calibration from a different dataset
before measurement begins. Qualification/controller/trace code and production
sources are unchanged between `668371f` and `ebb3dc1`. Therefore no sorting run
was repeated for that tool-only change. The final read-only checker identity is
separate from each producing source; historical auditing does not upgrade the
source identity of an old execution.

## Trace repair and original records

The independent checker now verifies the exact initialization and seven-event
round schemas/order, input-derived neighbor/anchor fields, live list sizes and
owners, and reconstructible counters. A performed split must have a nonempty
source, size conservation and valid distinct IDs for nonempty outputs; empty
outputs must have null IDs. A skipped split has zero sizes, null split IDs and
acquired side, and the established skip reason. Missing/non-split empty events,
swapped steps, inconsistent flags, boolean IDs and counter changes are rejected.

Thirteen trace-corruption subcases are tested on copies of actual small-input
records. They are subcases of one test method, not thirteen additional tests.
Tree visit counters absent from trace remain typed observations rather than
independently reconstructed work. This is record consistency checking, not a
physical-tree proof or a fresh run of the sorting algorithm.

`original_140_readonly_recheck.json` reconstructs **140 PASS, 560 mode records**
and every manifest entry using the strengthened checker. The old 3,788 splits
per backend still all have an empty side; those facts were not relabeled.
Both prior archives remain byte-identical: 450 hashes in v1 and 995 in the
original v2 archive, plus matching Git directory identities.

## The separate targeted split set

Exact preselected inputs are saved in `preselected_split_inputs.json`; rules
were committed before execution in `preselected_split_plan.json`.

- `n=128,129`, `k=3,7,19`, original and mirror: 12 unique canonical inputs.
- Existing `values_for` construction only, no search or performance-based choice.
- Selection SHA-256:
  `357220a65f52059df647be4189531e981bbef0e2aa13fd744d19ce40819c0454`.
- Original 140 selection SHA-256 remains
  `c8d8f34f7dce619a87d54cffd8567255c80340742f00de072eb5ca771991b17b`.
- No overlapping rank hashes with the original 140. This still does not make
  the combined constructions 152 independent random samples. Results stay separate.

Both backends use synchronous checked v2 with three independent instances and
one separate fresh minimal call; tree `detailed_work=False` remains explicit.
Each case and the whole small campaign have 180-second resource limits. There
was one attempt, no retry/replacement. Summed worker resource time was about
14.24 seconds, maximum per case about 1.22 seconds. These include audit,
observation and persistence, and are not sorting performance measurements.

| Evidence | Result |
| --- | ---: |
| Case statuses | 12 PASS, zero ERROR/TIMEOUT/NOT_RUN |
| Synchronous records | 24 |
| Fresh minimal records | 24 |
| Prefix comparisons | 1,518 per backend |
| Final fresh checked replays | 12 per backend |
| Observed initializations | 48 per backend: 36 checked + 12 minimal |
| Primary performed splits | 24 per backend |
| Primary two-sided nonempty splits | 12 per backend |
| Actual smaller sides | 3, 7 and 19, each four occurrences per backend |

The target checks inspect actual recorded sizes, not the parameter name `k`.
Every target two-sided split occurs at iteration 126 with source size 61 under
finite owner pair 2. The partitions are 3/58, 7/54 and 19/42 and their mirrors.
Thus the control flow passes the single-side early returns and enters the
real two-sided split path; this is not a claim that every internal repair branch
was exercised.

**Remaining coverage limits are explicit.** Each target's retained output
receives one direct boundary insertion at iteration 128. No direct acquired-side
update or subsequent split of either output ID is observed. The second split in
each run has source size 1 and a single nonempty output. Source size, source
owner and split iteration are shared across these related constructions; there
is no general-scale or arbitrary-ratio coverage claim.

`split_recheck_report.json` records every performed split's source/output IDs,
sizes, smaller side, owners and direct later updates up to that output's next
split. `coverage_summary.json` gives aggregates. Peer/fresh replay executions
and minimal calls are not counted again as primary split observations.

## Measurement tooling and test scope

Calibration and paired execution tools now implement the predeclared numerical
rules, separate dataset identities, durable per-batch recording and independent
reconstruction. Calibration chooses the first common B meeting both medians'
10 ms target from 1..128 with three repetitions each. The paired schedule uses
five warmup calls/backend and 20 paired batches with alternate first position;
statistics are batch-based per-call medians and R7 quartiles, with no trimming.

Formal entry checks qualified production identity, same-source validated
calibration, interpreter/platform/hardware/GC consistency and an explicit
representation/locality/cost review record. It rejects cross-dataset calibration
before output creation or warmup. The review record is provenance for a
completed review, not an automatic proof; none was created for this task.

`tests.log`: **66 methods passed**, zero skipped, before the 12-case run.
`measurement_guard_tests.log`: **14 measurement methods passed** after the guard
change: 13 repeats and one new method. Thus **67 distinct methods** were exercised,
including 20 new this increment; these are not 80 distinct tests.

Coverage includes common-batch choice, alternate order, nonconstant R7 examples,
output/count/config corruption, summary rebuilding, resealed archive tampering,
missing records despite exit 0, error retention and actual process termination.
Measurement fixtures use synthetic clocks and explicit qualification/review
stubs. Their times and ratios are not performance results. Actual small minimal
calls and timeout workers test mechanics only. No full repository test suite,
new performance campaign, complete mathematical proof or thesis build is claimed.

## Reproduce the read-only checks

From the current checker revision, without modifying either archive:

```sh
PYTHONPATH=src:experiments python3 experiments/validate_common_qualification_v2.py \
  docs/validation/common_qualification_v2_20261015/qualification --historical

PYTHONPATH=src:experiments python3 experiments/validate_common_qualification_v2.py \
  docs/validation/split_trace_followup_20261015/qualification \
  --dataset targeted_split --historical
```

Historical mode checks source hashes against Git blobs from the named producing
revision and reports the current checker identity separately. At the producing
revision `668371f`, a fresh 12-case execution requires a clean worktree and a
new output directory:

```sh
PYTHONPATH=src:experiments python3 experiments/qualify_common_inputs_v2.py \
  --dataset targeted_split --output /absolute/path/to/new-split-qualification
```

The next experimental step is separate real batch calibration for the two
qualified distributions, followed by formal-tool review and the unresolved
cost/representation/locality review. A successful qualification or a review
receipt does not itself certify the efficient-backend minimum. Neither current
qualification data nor synthetic-clock fixtures replace the historical pilot
with current formal performance results.
