# Week 13 Progress

Last updated: 2026-08-06

## Goal

Convert the reviewed implementation and immutable Week 12 evidence into
thesis-facing chapters without changing the algorithm, rerunning formal timing,
or strengthening claims beyond their evidence.

## Day 1: Claim-to-Evidence Table

Status: complete; awaiting review before chapter drafting.

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

Authoritative table:

```text
docs/thesis/claim_to_evidence_table.md
```

## Remaining Work

- [ ] revise and expand the Implementation chapter against `I-*` claims;
- [ ] revise Experimental Method against `M-*` claims;
- [ ] draft Results from `R-*` and qualified `E-*` claims;
- [ ] draft Limitations with explicit coverage of every `L-*` row;
- [ ] perform the final chapter-level claim audit.

## Boundary

Day 1 did not modify source code, validators, generated analysis artifacts, or
immutable evidence. No formal timing or validation run was repeated. Chapter
drafting remains blocked until this table is reviewed.
