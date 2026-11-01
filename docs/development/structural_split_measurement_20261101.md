# Structural split timing extension — 1 November 2026

## Question and fixed inputs

The 140 common inputs have no two-sided split. The existing 12 targeted timing
inputs each contain one two-sided split of a 61-item source group. This extension
measures the 18 constructions already checked in the October 13 structural
campaign, to describe larger balanced/skew cuts and repeated split/update histories.
It does not change the sorting implementation or search for faster tree cases.

Use all combinations of lengths 128, 129, 256, 257, 512 and 513 with the original
`balanced`, `skew`, and `repeated` constructors. Odd lengths retain the original
mirror choice. The exact values must match the original saved structural inputs.
No case is filtered, replaced or chosen by measured speed. These are dependent
constructions; parity and direction are coupled and cannot be estimated separately.

## Qualification and coverage

Use the existing synchronous qualification on both backends, including checked
prefix comparisons, a fresh checked replay and a fresh minimal call. The tree's
`detailed_work` setting stays false. Stop at the first execution, correctness,
coverage or resource failure; keep the failure and mark later inputs not run.
The existing limits remain 180 seconds per input and 1800 seconds per campaign.

Both primary checked traces must additionally satisfy these workload predicates:

- Balanced: one two-sided split of size m=(even_n-6)/2, smaller side floor(m/2).
- Skew: one two-sided split of the same source size, smaller side one.
- Repeated: floor((even_n-4)/8) two-sided splits and at least one fewer re-splits
  of outputs produced by earlier splits. All target two-sided splits have finite owners.

Reconstruct actual source/output sizes, smaller sides, owners, and direct later
output insertions and splits. Do not infer full descendant histories or count
peer/replay/minimal runs as extra primary observations. Record missing updates
to either side rather than claiming that every lifecycle is covered.

## Measurement and reporting

Retain the existing numerical protocol: choose the first common B from
1,2,4,8,16,32,64,128 where three-batch median times reach 10 ms on both backends;
five warmup calls/backend; twenty paired sample batches with alternating first
backend; enabled GC; the complete fresh minimal sorting call inside the timer.
Preserve all raw observations, with no duration-based exclusions or retries.

Commit the protocol, tools, tests and exact selection before the qualification
campaign. Use a clean source revision and one interpreter/machine configuration
through qualification, calibration and formal sampling. Run these stages serially;
do not run tests, compilation or other development loads during timing.

The existing formal review receipt may be reused only if every production-source
hash matches. Preserve its original identity and review reference rather than
creating a new human-review approval. Existing review documents and later proof
corrections remain separately identifiable; the receipt is not proof certification.

Report all 18 per-input medians/ratios and descriptive summaries by workload and
length, alongside qualification coverage. Analyze this November campaign separately
from the original common and targeted timing campaigns. Full sorting timings do
not isolate the causal cost of a split. Do not pool related inputs as independent
random samples or infer an asymptotic crossover from these lengths.

The original common, targeted and structural archives remain unchanged. The
supplementary result must be incorporated into the method, results, limitations
and conclusions, with source/evidence references and any affected numerical summaries.
