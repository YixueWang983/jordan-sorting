# Experimental Method Draft

Last updated: 2026-08-06

Status: Week 13 experimental-method chapter draft; awaiting review.

## Study Scope

The Week 12 formal experiment evaluates sorting on oracle-certified valid
Jordan sequences. It does not evaluate recognition of arbitrary candidates or
invalid-input classification. Recognition remains a separate experimental
question and no Week 12 sorting result is used as recognition evidence. [M-01,
L-05]

Within that scope, the experiment asks three empirical questions:

1. Do all three implementations return the expected sorted output on the
   frozen valid cases?
2. How do their measured-call runtime distributions vary across the tested
   sizes and controlled input families?
3. What descriptive relationships appear between structural measurements,
   checked paper-operation counters, and runtime?

The design answers these questions for one frozen collection of cases and one
recorded execution environment. Five input sizes are not used to infer
asymptotic complexity, and exploratory relationships are not interpreted as
causal effects. [M-01, M-02, M-09, L-02, L-07]

## Frozen Protocol

The formal protocol identifier is `week12_formal_sorting_v1`. Its complete
configuration was written to `run001/config.json` before case generation or
timing. The experiment uses the following five input sizes: [M-02]

```text
32, 64, 128, 256, 512
```

At each size, the generator produces one `flat_valid` case, one `nested_valid`
case, and ten seeded `incremental_valid` cases. This gives twelve exact cases
per size and sixty cases overall. The base generation seed is `20261201`; each
incremental case receives a deterministic size- and case-specific seed. The
flat and nested constructions are deterministic. [M-02, M-03]

The family balance is intentionally unequal. A size-level summary contains ten
incremental cases but only one flat and one nested case, so it mainly reflects
the incremental construction. Family-specific summaries preserve that
distinction. These controlled generators do not represent a probability
sample from all valid Jordan sequences. [M-03, L-08]

## Compared Implementations

The frozen algorithm set contains three implementations: [M-04]

```text
python_sort
simplified_jordan_reference
simplified_jordan_paper_ordinary_list
```

`python_sort` is the ordinary optimized sorting baseline. Its timed call
returns a sorted list and does not report Jordan validity or structure. [M-04]

`simplified_jordan_reference` times the complete reference function
`simplified_jordan_sort`. That call includes its oracle validation,
operation-state preparation, family-tree construction for valid inputs,
structural statistics, reference trace construction, and serializable result
assembly. The timed result is therefore a complete oracle-backed reference
pipeline rather than only a sorting primitive. [M-04, M-07]

`simplified_jordan_paper_ordinary_list` times
`paper_jordan_sort_valid(..., execution_mode="minimal")` after the exact case
has already passed oracle certification and a separate checked diagnostic.
`minimal` disables trace recording, selected operation counters, and complete
backend commit validation, while retaining the ordinary-list Step 1/2/3 work,
local safety checks, stage results, rollback, and final output recovery. [M-04,
M-06]

These timed scopes are deliberately different. In particular, the reference
call includes certification and structural/reference work while the paper call
uses a pre-certified input and times only its minimal sorting core. A
paper/reference ratio is therefore a pipeline-scope comparison, not a
like-for-like end-to-end speedup. [M-06, M-07, L-03]

## Case Construction and Pre-Timing Audit

For each family, size, and case number, the runner generates the sequence once,
checks its length, and computes a SHA-256 digest of the serialized sequence.
Duplicate sequence hashes within a family-size group are rejected. The exact
sequence object is retained for all algorithms so that comparisons use matched
inputs. [M-03]

Every sequence is passed to the oracle before any warm-up or measured call.
The runner requires a valid result with distinct values. It then computes the
structural profile, including interval counts, roots, nesting, depth, density,
and category fields. Failure at generation, certification, or profiling stops
the formal run rather than silently dropping the case. [M-01, M-03]

The paper implementation also receives one untimed checked diagnostic per
exact case. The diagnostic output must match `oracle_result["sorted"]`, process
all `n` points, and report valid state invariants. Its trace length and complete
paper-operation metrics are saved in `case_audit.csv`. All sixty cases finish
certification and checked audit before the first warm-up begins. [M-01, M-06,
M-11]

## Timing Procedure

Each exact case-algorithm cell receives five warm-up calls followed by twenty
measured calls. The twenty calls estimate the timing distribution for one
fixed case and algorithm; they are not treated as twenty independent generated
inputs. [M-05]

For every warm-up and measured call, the runner creates a fresh Python list
from the stored sequence before starting the clock. It records elapsed time
with `time.perf_counter_ns()` around only the selected algorithm call. If
garbage collection is enabled before the call, the runner disables it for the
timed region and restores the caller's original GC state afterward. Each
algorithm's own output construction or recovery remains inside that call:
Python sort constructs its list, the reference pipeline constructs its result
dictionary, and the paper core executes `state.partial_order.to_list()` before
returning. [M-05, M-06, M-07]

After the timer stops, the runner normalizes the already constructed return
value, for example by reading `result["sorted"]` from the reference result. It
then compares the normalized list with the oracle-sorted reference and records
correctness or error fields. These runner-level operations are outside timing;
they do not move any algorithm's own output construction outside its timed
call. [M-05]

Warm-up failures abort the experiment. A measured-call exception is retained as
an error row with no valid timing rather than omitted. The formal evidence
contract and validator require every archived measured row to have a positive
time, valid oracle certification, correct output, a passed case audit, and no
error. [M-05, M-11, M-12]

## Scheduling and Noise Controls

Case execution order is a deterministic shuffle under seed `20261203`.
Algorithm order is derived from seed `20261202` and the case index. Within the
twenty measured rounds, the initially shuffled three-algorithm order is rotated
cyclically, distributing algorithms across first, second, and third positions.
The warm-up order is generated by the same deterministic rule. [M-08]

This schedule improves reproducibility and limits a fixed position bias, but it
does not remove all operating-system, thermal, frequency, or background-load
noise. Variability remains visible in the raw calls and case summaries. [M-08,
M-09]

## Aggregation and Statistical Units

The raw evidence contains one row per exact case, algorithm, and measured
round:

```text
60 cases x 3 algorithms x 20 measured calls = 3,600 raw rows
```

The first aggregation level is the exact case-algorithm cell, giving 180 case
summaries. Its primary statistic is the median of the twenty measured calls.
Q1, Q3, IQR, mean, and sample standard deviation are retained to expose
dispersion. Q1 and Q3 use the median-of-halves convention: after sorting the
measured times, Q1 is the median of the lower half, Q3 is the median of the
upper half, and IQR is `Q3 - Q1`. [M-05, M-09, M-11]

The second stored level groups case medians by family, size, and algorithm,
giving 45 group summaries. Higher-level size and family tables used in the
analysis are also constructed from exact-case medians, not by pooling all raw
calls. This keeps the exact generated case as the unit of comparison. [M-09,
M-11]

Runtime ratios are first calculated within each exact case from its algorithm
medians. The case ratios are then aggregated with equal weight by size, family,
or family-size. This avoids dividing two independently pooled runtime
distributions and preserves the matched-case design. [M-10]

Structural and checked-counter correlations are descriptive analyses over
matched case records. They are reported with explicit sample composition and
are not used as causal estimates, formal cost decompositions, or complexity
proofs. [M-03, M-09, L-02, L-07]

## Evidence and No-Overwrite Contract

The execution ID `week12_formal_sorting_v1__run001` identifies one immutable
formal run. Before generation, the runner confirms the frozen configuration,
recaptures the environment, reserves an unused output directory, and writes
`config.json` and `environment.json` with exclusive-create semantics. Existing
directories or files are not overwritten. [M-11, M-13]

The completed archive contains: [M-11]

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

The manifest records protocol and execution identifiers, source commit, row
counts, UTC and monotonic pipeline elapsed time, the sum of measured-call
times, and SHA-256 values for the four CSV files plus config and environment.
Its pipeline elapsed scope starts at formal directory reservation and ends
after CSV writing; manifest writing and validation are excluded. This
whole-pipeline duration is distinct from algorithm runtime. [M-11]

## Independent Validation

The Week 12 validator does not trust row-to-row consistency alone. It reads the
frozen gate, independently regenerates all sixty cases, recomputes case seeds
and sequence hashes, reruns oracle certification and structural profiling, and
executes checked paper diagnostics again. It compares the reconstructed
diagnostic output, processed count, trace count, and every paper metric with
`case_audit.csv`. [M-12]

It also verifies the complete case/round/algorithm product, deterministic case
and algorithm positions, positive timing values, correctness fields, schema,
row counts, and the absence of recorded errors. Case and group summaries are
recomputed from `raw.csv`. Environment readiness, source provenance,
wall-clock consistency, manifest paths, and file hashes are checked before a
run is accepted. Malformed or inconsistent evidence produces `valid=false`
rather than authorizing analysis. [M-11, M-12]

The archived validation report is retained with the run, and the analysis
performs a new validation pass before reading the evidence. This establishes
validation under the repository's explicit evidence contract; it is not a
proof-theoretic formal verification of the algorithm. [M-12]

## Execution Environment and Provenance

The accepted formal execution was `week12_formal_sorting_v1__run001`, produced
from source commit `98868b1b705f6d5f22404ee8ad7b88ad7a834f52`. The recorded
benchmark environment was Apple M4/arm64 with 16 GB memory, ten logical CPUs,
macOS 26.6, and CPython 3.12.4. [M-13]

Before timing, the runner recorded a clean Git worktree whose HEAD matched
remote `main`, AC power, a full battery, low-power mode disabled, low and stable
load, sufficient disk space, and no readiness warnings. These fields describe
the performance environment class rather than a personally identifiable
device. [M-13]

Absolute runtimes in the Results chapter apply to this one recorded execution.
They must not be generalized to other processors, operating systems, Python
versions, or machine states. Week 11 and Week 12 absolute times are not pooled;
their comparison is restricted to within-run ratios and directional patterns.
[M-13, L-06]

## Method Boundaries

The formal method fixes the following interpretation limits:

- recognition is separate from valid-input sorting; [M-01, L-05]
- five tested sizes support observed-trend descriptions, not asymptotic
  inference; [M-02, L-02]
- family imbalance must remain visible in aggregate interpretation; [M-03]
- paper/reference ratios compare different pipeline scopes; [M-06, M-07,
  L-03]
- repeated timing calls are not independent generated cases; [M-05, M-09]
- one execution environment does not establish hardware-independent absolute
  time; [M-13]
- cross-week comparison must not pool absolute runtimes; [L-06]
- structural and counter relationships remain exploratory and non-causal.
  [L-07]

## Claim Coverage

This chapter covers experimental-method claims `M-01` through `M-13` and the
required boundaries `L-02`, `L-03`, `L-05`, `L-06`, `L-07`, and `L-08`.
Quantitative results and observed coefficients are intentionally reserved for
the Results chapter.
