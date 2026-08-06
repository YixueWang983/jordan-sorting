# Week 13 Progress

Last updated: 2026-08-06

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

Status: complete; awaiting review before Experimental Method drafting.

- [x] separate the oracle-backed reference path from the paper core;
- [x] describe the one-based point/pair model and both maintained structures;
- [x] document initialization and the shared Step 1/2/3 control flow;
- [x] explain increasing/decreasing ownership and output insertion branches;
- [x] record the geometric-endpoint and odd-index `z1` interpretations;
- [x] explain atomic split publication, local postconditions, and rollback;
- [x] describe checked diagnostics, deterministic replay, and policy modes;
- [x] state the ordinary-list and non-linear-time boundaries;
- [x] cover `I-01` through `I-09` plus `L-01`, `L-04`, and `L-09`.

Draft:

```text
docs/thesis/implementation_draft.md
```

## Remaining Work

- [ ] revise Experimental Method against `M-*` claims;
- [ ] draft Results from `R-*` and qualified `E-*` claims;
- [ ] draft Limitations with explicit coverage of every `L-*` row;
- [ ] perform the final chapter-level claim audit.

## Boundary

Days 1 and 2 did not modify source code, validators, generated analysis
artifacts, or immutable evidence. No formal timing or validation run was
repeated. Experimental Method drafting remains blocked until the Implementation
chapter is reviewed.
