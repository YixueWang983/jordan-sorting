# Week 13 Progress

Last updated: 2026-08-07

## Goal

Convert the reviewed implementation and immutable Week 12 evidence into
thesis-facing chapters without changing the algorithm, rerunning formal timing,
or strengthening claims beyond their evidence.

## Day 1: Claim-to-Evidence Table

Status: complete; reviewed with follow-up corrections applied.

- [x] separate implementation, protocol, execution, quantitative, exploratory,
  and scope evidence;
- [x] distinguish the oracle-backed reference pipeline from the independent
  paper ordinary-list core;
- [x] bind every planned headline number to a Week 12 CSV field;
- [x] bind protocol and execution claims to immutable run001 config/manifest;
- [x] preserve the timing-scope boundary beside paper/reference claims;
- [x] record family imbalance and exact-case aggregation requirements;
- [x] restrict Week 11/12 comparison to within-run ratios and direction;
- [x] label structure and checked-counter relationships as exploratory;
- [x] enumerate prohibited linear-time, asymptotic, causal, recognition, and
  end-to-end-speedup claims;
- [x] define which claim IDs belong in each future thesis chapter.
- [x] add the formal execution environment and provenance claim `M-13`;
- [x] correct the I-02 paper-specification locator.

The reviewed table now contains 46 controlled claims:

```text
Implementation: 9
Method:        13
Result:        11
Exploratory:    4
Limitation:     9
```

Authoritative table:

```text
docs/thesis/claim_to_evidence_table.md
```

## Day 2: Implementation Chapter

Status: complete; reviewed with two locator/wording corrections applied.

- [x] separate the oracle-backed reference path from the paper core;
- [x] describe the one-based point/pair model and both maintained structures;
- [x] document initialization and the shared Step 1/2/3 control flow;
- [x] explain increasing/decreasing ownership and output insertion branches;
- [x] record the geometric-endpoint and odd-index `z1` interpretations;
- [x] explain atomic split publication, local postconditions, and rollback;
- [x] describe checked diagnostics, deterministic replay, and policy modes;
- [x] state the ordinary-list and non-linear-time boundaries;
- [x] cover `I-01` through `I-09` plus `L-01`, `L-04`, and `L-09`.
- [x] replace the obsolete I-01 `_reference_sorted_output` locator;
- [x] identify exhaustive checking as repository validation, not external
  replication.

Draft:

```text
docs/thesis/implementation_draft.md
```

## Day 3: Experimental Method Chapter

Status: complete; timing-scope, diagnostic-provenance, and quartile corrections
reviewed and approved.

- [x] fix the Week 12 valid-input sorting scope and recognition separation;
- [x] document five sizes, sixty cases, family balance, and frozen seeds;
- [x] distinguish the three compared timed pipelines;
- [x] place oracle certification and checked diagnostics outside paper timing;
- [x] describe fresh inputs, GC restoration, warm-ups, and measured calls;
- [x] document deterministic case/algorithm scheduling and noise limits;
- [x] define exact-case aggregation and matched-case ratio construction;
- [x] explain no-overwrite evidence, manifest, and live validation;
- [x] bind absolute-time reporting to the run001 environment and source commit;
- [x] cover `M-01` through `M-13` and required method limitations.
- [x] distinguish timed algorithm output construction from untimed runner
  normalization and correctness comparison;
- [x] state that diagnostic output matches, rather than comes from, the oracle
  result;
- [x] define Q1/Q3 with the median-of-halves convention.

Draft:

```text
docs/thesis/experimental_methodology_draft.md
```

## Day 4: Results Chapter

Status: complete; reviewed and approved after the Week 11/12 provenance
correction.

- [x] establish correctness and evidence validity from `R-01`;
- [x] report absolute runtimes with run001 environment and scope context;
- [x] place the pipeline-scope boundary beside the first ratio table;
- [x] report all five size ratios and the observed tested-size crossover;
- [x] preserve family imbalance beside family-specific results;
- [x] retain the flagged IQR cell without deletion or causal explanation;
- [x] separate measured-call totals from whole-pipeline wall-clock;
- [x] compare Week 11/12 through within-run ratios and direction only;
- [x] isolate `E-01..E-04` in explicitly exploratory subsections;
- [x] cover `R-01..R-11` without linear-time or asymptotic claims.

Draft:

```text
docs/thesis/results_draft.md
```

## Day 5: Limitations Chapter

Status: complete; reviewed and approved.

- [x] distinguish the ordinary-list reconstruction from the theoretical
  level-linked and heterogeneous finger-tree backend;
- [x] prohibit linear-time and five-size asymptotic conclusions;
- [x] explain the non-equivalent paper/reference timing scopes;
- [x] preserve independent paper output provenance while stating the external
  valid-input certification boundary;
- [x] separate recognition from the Week 12 valid-input sorting evidence;
- [x] state the controlled, unbalanced generator and sample limitations;
- [x] restrict Week 11/12 comparison to within-run ratios and direction;
- [x] limit absolute runtime to the recorded execution environment;
- [x] label structure and checked-counter relationships exploratory and
  non-causal;
- [x] cover `L-01` through `L-09` without introducing a new empirical result.

Draft:

```text
docs/thesis/limitations_draft.md
```

## Day 6: Final Chapter-Level Claim Audit

Status: complete; reviewed and approved with one non-blocking metadata note.

- [x] confirm the 46-claim inventory and category counts;
- [x] confirm every controlled ID appears in its assigned chapter;
- [x] resolve all local evidence and source links;
- [x] verify Week 11 `run003` and Week 12 `run001` manifest-bound hashes;
- [x] recheck Results headline numbers against generated artifacts;
- [x] audit reference/paper output provenance across all chapters;
- [x] audit timing-scope, recognition, backend, complexity, sampling,
  cross-week, and exploratory boundaries;
- [x] rerun 537 unit tests, `compileall`, 2,074 exhaustive valid permutations,
  and 48 fixed generated cases;
- [x] avoid formal timing, formal validation, and evidence modification.

Audit record:

```text
docs/thesis/final_claim_audit.md
```

## Remaining Review Gate

- [x] review the final claim audit and close Week 13.
- [x] begin FU LaTeX integration only after Week 13 closure.

The review reported no claim, evidence, or conclusion finding. Its only LOW
note was that the four hash-bound Markdown drafts still contain historical
`awaiting review` status lines. They remain unchanged deliberately so the
audited SHA-256 baseline remains valid. This progress record is the current
status authority.

## Boundary

Days 1 through 6 did not modify source code, validators, generated analysis
artifacts, or immutable evidence. No formal timing or validation run was
repeated. Week 13 is closed. The separate FU LaTeX integration phase may use
the audited drafts as immutable content baselines but must not silently change
a controlled claim.
