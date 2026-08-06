# Week 12 Plan: Formal Valid-Input Sorting Experiment

Last updated: 2026-08-06

Status: complete; run001 is archived, formal execution is disabled, and the
analysis and Week 13 handoff are frozen.

## Goal

Week 12 upgrades the validated Week 11 pilot into one thesis-facing formal
experiment for oracle-certified valid-input sorting. It does not expand the
algorithm, merge recognition into sorting, or claim linear time.

The frozen authority is:

```text
experiments/week12_experiment_gate.py
```

Frozen scale:

```text
protocol:             week12_formal_sorting_v1
sizes:                32, 64, 128, 256, 512
families:             flat, nested, incremental valid
cases per size:       1 + 1 + 10
total cases:          60
algorithms:           3
warm-ups:             5 per case and algorithm
measured rounds:      20
paper timing mode:    minimal
paper audit mode:     checked
raw rows:             3,600
case summaries:       180
group summaries:      45
case audits:          60
recognition:          separate
```

The gate binds the archived Week 11 `run003` manifest by path and SHA-256.

## Fixed Boundaries

Week 12 must not:

- modify or rerun Week 11 `run003`;
- change frozen sizes, families, cases, seeds, algorithms, modes, or runs;
- send invalid or duplicate inputs to the paper sorter;
- merge recognition into the valid-input timing experiment;
- change Step 1/2/3 or the ordinary-list backend without a real blocker;
- move oracle certification or checked diagnostics into paper timing;
- treat the reference pipeline and paper call as like-for-like end-to-end
  timing scopes;
- claim a linear implementation or infer asymptotic complexity from five
  sizes.

`paper_jordan_diagnostics_valid(sequence)` accepts no execution-mode argument.
It is fixed to checked policy internally. Only the timed paper call explicitly
uses `execution_mode="minimal"`.

## Checkpoint 1: Runner, Validator, and Regression Gate

Checkpoint 1 combines the former Day 1-Day 5 work. It is submitted and
reviewed once before any formal execution.

Required implementation:

```text
experiments/experiment_validation_support.py
experiments/formal_execution_support.py
experiments/run_week12_formal_sorting.py
experiments/validate_week12_formal_sorting_outputs.py
tests/test_run_week12_formal_sorting.py
tests/test_validate_week12_formal_sorting_outputs.py
```

### Runner Contract

The runner derives its internal immutable execution config from the complete
frozen gate. The CLI accepts only:

```text
--execution-id
--preflight-only
```

It does not expose protocol overrides or overwrite controls. Before review,
both the CLI and public Python execution entry remain disabled.

The formal output is:

```text
results/runs/<execution_id>/
```

with exactly these eight evidence products after a successful run:

```text
config.json
environment.json
raw.csv
case_summary.csv
group_summary.csv
case_audit.csv
manifest.json
validation_report.json
```

`config.json` stores `gate_to_dict(WEEK12_EXPERIMENT_GATE)`, including scope,
recognition separation, source-pilot provenance, all frozen variables, and all
derived row counts. `environment.json` stores only execution-specific source,
anonymous benchmark environment, power/load/disk evidence, and formal timing
readiness.

### Case Certification and Audit

For each exact case, before any warm-up or measured call:

1. generate the sequence once;
2. enforce the frozen seed rule;
3. reject duplicate sequence hashes within `(family, n)`;
4. require oracle validity and distinct values;
5. compute structural fields once;
6. call `paper_jordan_diagnostics_valid(sequence)` once;
7. require valid invariants, correct output, and full processed count;
8. archive all checked paper counters in `case_audit.csv`.

Incremental seeds are:

```text
base_seed + n * 1000 + case_number
```

Flat and nested cases have an empty seed.

### Timing and Aggregation

The runner reuses the reviewed Week 11 timing, GC restoration, deterministic
case order, balanced algorithm order, and summary definitions. Paper timing
calls only the pre-certified minimal sorter. Reference timing includes the
complete reference pipeline.

Raw data contains the exact Cartesian product:

```text
60 cases x 3 algorithms x 20 measured rounds = 3,600 rows
```

Case summaries aggregate 20 repeated timings for one exact case and algorithm.
Group summaries aggregate case medians by `(family, n, algorithm)`. Repeated
timings are not treated as independent cases.

### Experiment Wall-Clock

The manifest stores:

```text
experiment_started_at_utc
experiment_completed_at_utc
experiment_elapsed_ns
experiment_elapsed_scope
measured_call_total_ns
```

The frozen elapsed scope is:

> From formal evidence-directory reservation through config/environment
> writes, case generation, oracle certification, checked diagnostics,
> warm-ups, measured calls, summary construction, and CSV writes; excludes
> manifest writing and output validation.

The validator report separately records:

```text
validation_started_at_utc
validation_completed_at_utc
validation_elapsed_ns
```

This prevents measured-call totals from being mistaken for whole-experiment
wall-clock time and avoids a circular manifest/validator timing definition.

### Independent Validator

The dedicated validator does not trust runner-produced metadata. It must:

- require the complete gate in `config.json`;
- recompute formal environment readiness;
- regenerate 60 cases, hashes, oracle results, and structure profiles;
- rerun 60 checked diagnostics and match every audit field;
- verify case and balanced algorithm order from frozen seeds;
- require the exact 3,600-row Cartesian product;
- recompute 180 case and 45 group summaries;
- recompute measured-call total time;
- validate wall-clock fields and exact elapsed scope;
- validate manifest paths, row counts, and SHA-256 hashes;
- return `valid=false` rather than crash on malformed evidence.

The runner's first built-in validation creates the archived
`validation_report.json`. Every later independent or analysis validation must
use `--report-json` outside the archived run, for example:

```bash
python experiments/validate_week12_formal_sorting_outputs.py \
  --run-dir results/runs/week12_formal_sorting_v1__run001 \
  --report-json docs/analysis/week12_run001_independent_validation.json
```

The validator must reject external report paths inside the evidence archive.

### Corruption and Regression Tests

Permanent tests cover missing/duplicate rows, invalid schedule positions,
incorrect output flags, timing changes, seed/hash coordination, audit-counter
changes, summary changes, config/environment drift, manifest changes, missing
files, malformed JSON, and refreshed manifest hashes after coordinated data
tampering.

Checkpoint 1 verification includes:

```bash
python -m unittest \
  tests.test_run_week12_formal_sorting \
  tests.test_validate_week12_formal_sorting_outputs

python -m unittest discover -s tests
python -m compileall -q src experiments tests
python experiments/validate_paper_algorithm.py --max-n 8
```

Historical output checks use the real validator entry points:

```bash
python experiments/validate_experiment_outputs.py \
  --run-dir results/runs/week9_integration_pilot/sorting

python experiments/validate_experiment_outputs.py \
  --run-dir results/runs/week9_integration_pilot/recognition

python experiments/validate_week10_timing_outputs.py \
  --run-dir results/runs/week10_contamination_full_20260728

python experiments/validate_week11_pilot_outputs.py \
  --run-dir results/runs/week11_pilot_v1__run003 \
  --report-json /tmp/week11_checkpoint_validation.json
```

Checkpoint 1 acceptance requires that `run001` is absent, formal execution is
disabled, run003 is unchanged, and all verification gates pass.

## Checkpoint 2: One Formal Execution and Evidence Archive

After Checkpoint 1 review, enable only the reviewed formal entry. Do not submit
or review a successful advisory preflight separately. The formal entry itself
recaptures Git, power, load, disk, and output-directory state immediately
before evidence reservation.

Planned execution ID:

```text
week12_formal_sorting_v1__run001
```

Planned command:

```bash
python experiments/run_week12_formal_sorting.py \
  --execution-id week12_formal_sorting_v1__run001
```

Success requires:

```text
status = validated_formal_complete
validation_valid = true
rows = 3,600 / 180 / 45 / 60
errors = 0
incorrect outputs = 0
failed audits = 0
```

Then rerun the validator with an external report path and archive the eight
immutable evidence files. If any stage fails, preserve partial evidence,
retire the execution ID, and never overwrite or retry that directory.

## Checkpoint 3: Formal Analysis and Week 13 Handoff

Analysis must first live-validate the archive and write its report outside the
run directory. It then reads immutable evidence and writes only `week12_...`
artifacts under `docs/analysis/`.

Required analysis includes:

- correctness and audit totals;
- runtime and relative IQR by size;
- runtime by family and size;
- exact-case paper/reference, paper/Python, and reference/Python ratios;
- Week 11 versus Week 12 trend consistency without pooling absolute timings;
- exploratory ordinary-list counter/structure relationships;
- explicit pipeline-scope, non-causal, non-asymptotic, and non-linear-time
  limitations.

Checkpoint 3 adds the formal analysis, figures, `week12_summary.md`, and the
Week 13 handoff. It must not modify the evidence archive.

## Completion Criteria

Week 12 is complete only when:

- Checkpoint 1 code and corruption tests are reviewed;
- one formal execution is validated and immutably archived;
- external validation independently reports `valid=true`;
- formal analysis is reproducible from the archive;
- recognition remains separate;
- paper oracle/audit work remains outside timing;
- timing-scope and theoretical non-claims are explicit;
- historical validators, exhaustive cases, generated cases, tests, compile,
  and commit checks pass.
