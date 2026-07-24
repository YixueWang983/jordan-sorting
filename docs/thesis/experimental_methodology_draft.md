# Experimental Methodology Draft

Last updated: 2026-07-24

## Research Questions

The experiments are organized around correctness, structural coverage,
ordinary-backend sensitivity, and cost decomposition.

## Implementations Compared

```text
python_sort
sort_plus_laminarity_check
simplified_jordan_reference
```

`python_sort` is the optimized ordinary sorting baseline.
`sort_plus_laminarity_check` isolates validation plus ordinary sorted output.
`simplified_jordan_reference` is the ordinary-list reference pipeline and is not
a theoretical linear-time implementation.

## Input Families

Generator families:

```text
flat_valid
nested_valid
incremental_valid
invalid_upper_crossing
invalid_lower_crossing
random_invalid
mutation_based_invalid
```

Generator family names describe construction procedures. Structural labels are
computed after generation.

## Coverage Audit

Coverage audit records validity, invalid reason, structural category, depth,
containment density, crossing density, generator metadata, and sequence hashes.

Odd/even parity sizes are included because upper/lower pairing handles unpaired
endpoints differently depending on length.

## Variables

Independent variables:

```text
algorithm
family
n
case_id
validity class
structural metrics
```

Dependent variables:

```text
runtime
operation counters
correctness fields
error count
```

## Correctness Criteria

Correctness is not only sorted-output equality. The pilot records:

```text
output_correct
validity_correct
reason_correct
overall_correct
```

For algorithms that do not report validity or reasons, only applicable checks are
used.

## Timing Protocol

Timing uses warm-up runs, measured runs, `perf_counter_ns`, fresh input copies
outside the timed region, GC control during the timed region, randomized block
scheduling, and case-level aggregation before group-level aggregation.

## Aggregation Method

```text
raw timing rows
-> case summary
-> family/n/algorithm group summary
```

The primary statistic is median. Variability is represented with Q1, Q3, and IQR.
Mean and standard deviation are supplementary.

## Runtime Noise Controls

- fixed seeds;
- no JSON I/O inside timed regions;
- fresh list copy before starting the timer;
- balanced algorithm order within measured rounds;
- environment manifest with platform and clock metadata.

## Reproducibility

Each run directory contains:

```text
config.json
environment.json
raw.csv
case_summary.csv
group_summary.csv
manifest.json
auto_report.md
validation_report.json
```

## Threats to Validity

- The ordinary-list backend does not exploit theoretical linear-time structures.
- Runtime is sensitive to local machine state.
- Generator families are controlled constructions, not samples from all possible
  Jordan inputs.
- Operation counters cover selected validation and family-tree construction
  operations, not total cost.
- Correlation analyses are exploratory.

