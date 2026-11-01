# Structural split formal extension — 1 November 2026

All eighteen existing structural inputs were requalified, calibrated and
formally timed. The common set's 3,788 splits per backend have an empty side;
nesting-depth strata did not ensure interior-split coverage. The original
twelve targeted inputs contain one two-sided split each, of a 61-item source.
This extension adds larger balanced/skew cuts and repeated split histories.

## Fixed scope and execution identity

- Producer for all three stages: `bdfcdcf8f13da2a88151ae0524b388181ea7e5a6`.
- The plan, exact eighteen inputs and tests were committed before execution.
  Selection SHA-256: `e91e7a3ecfdc1506b621d7e7b286b3830f0bf48a993b279eb3f15902a914cf3b`.
- Lengths 128, 129, 256, 257, 512, 513 crossed with balanced, skew and repeated
  constructors. Values exactly match the October structural archive. Odd
  lengths use mirrors; parity and direction are coupled.
- Production `src/` hashes match the original measured version. Only experiment
  tools and tests changed to admit and verify the additional dataset.
- The existing formal review receipt was reused unchanged for those production
  sources. `review_binding.json` distinguishes its original review document
  from the later corrected one. No new human proof review is claimed.
- One calibration and one formal campaign, with no retries, filtering or input
  replacement. Tests and compilation were not run during measurement.

## Results

All eighteen inputs passed both backends' synchronous qualification, final
fresh replay and fresh minimal call. Each backend's primary traces contain
460 splits, 230 two-sided splits, 666 direct later insertions into split
outputs and 212 re-splits of earlier outputs. All two-sided splits have finite
owners. Direct updates before the next split affect retained outputs only;
this campaign does not cover direct updates to acquired outputs.

The unchanged timing rules use enabled GC, fresh complete minimal sorting calls,
three-batch calibration medians at least 10 ms on both backends, five warm-up
calls per backend and twenty paired batches per input. The tree retains its
instrumentation hooks with detailed collection disabled. Calibration selected
batch sizes 1, 2, 4 and 8 for 2, 6, 6 and 4 inputs respectively.

All 2,800 sample calls in 720 batches and all 180 warm-up calls returned correct
outputs. No execution, output or coverage failure occurred. The maximum
within-input/backend relative IQR was 2.401%; no formal batch fell below 10 ms.

| Shape | Inputs | Median tree/list ratio | Range |
| --- | ---: | ---: | ---: |
| Balanced | 6 | 3.045 | 2.837–3.222 |
| Skew | 6 | 3.036 | 2.785–3.217 |
| Repeated | 6 | 2.863 | 2.376–3.092 |
| All eighteen | 18 | 2.987 | 2.376–3.222 |

Every input favors the list. `analysis/cases.csv` and `cases.json` retain all
eighteen rows, including both medians, ratio, calibrated batch size and actual
coverage. `analysis/summary.json` contains per-shape and per-length descriptive
summaries and call accounting. These are complete sorting times, not isolated
split costs or an estimate over independent randomly sampled inputs.

## Environment and separation from older experiments

CPython 3.12.14, optimization level zero, Apple M4/arm64, ten logical CPUs,
16 GiB RAM, GC thresholds 700/10/10. Calibration and formal execution record
macOS 27.2 and battery power at 32%, discharging. Their required environment
fields and all bound Python source hashes match.

The original common/targeted archives recorded macOS 26.6 and 100% battery.
Although the production code and interpreter match, these are different
sessions and operating-system versions. Report the new dataset separately;
between-campaign differences cannot isolate a workload effect.

## Files and verification

- `preselected_inputs.json`, `preselected_plan.json`, `measurement_protocol.json`:
  pre-execution selection and rules; the prose plan is
  `docs/development/structural_split_measurement_20261101.md`.
- `tests.log`: 42 relevant test methods passed, including five new structural
  dataset methods. Synthetic-clock tests are tooling checks only.
- `qualification/`, `calibration/`, `formal/`: original manifest-bound archives,
  copied byte-for-byte from the execution location outside the checkout.
- `analysis/`: independent reconstruction of all three archives and all rows;
  its manifest binds the analysis outputs. `analysis_noise_check.json` records
  the additional variability and minimum-batch check.
- `original_common_recheck.json`, `original_targeted_recheck.json`: successful
  read-only audits using the corresponding pre-extension tooling in a temporary
  clean checkout at `2498e79596a5ffaaca42a02fa5cde627c460bd27`. That checkout was
  removed. The old archives were not rerun or resealed. The newer checker
  correctly rejects their older tooling hashes, so its check was not bypassed.
- `old-archive-hashes.json`, `preservation_check.json`: all 13,256 original files
  in seven archive trees retain their SHA-256 hashes.
- `thesis_validation.json` and `thesis_*.log`: source and PDF bindings, successful
  compilation and visual/numerical checks for the revised 78-page draft.
- `package_manifest.json`: SHA-256 hashes of every other file in this evidence
  package, including its pre-execution plan and post-execution records.

From the repository root, with the matching Python version and producer's
experiment tools, rebuild into a new directory outside the checkout:

```sh
PYTHONPATH=src:experiments python3 experiments/analyze_structural_split.py \
  --qualification docs/validation/structural_split_formal_20261101/qualification \
  --calibration docs/validation/structural_split_formal_20261101/calibration \
  --formal docs/validation/structural_split_formal_20261101/formal \
  --output /tmp/structural-split-reconstruction
```

The output directory must not already exist. This command validates and analyzes
saved records; it does not collect new timing samples. Tooling source bindings
are strict: later Python tool changes require a clean checkout of the producer
to audit these archives. Stored records retain their original execution paths,
timestamps and source identity.
