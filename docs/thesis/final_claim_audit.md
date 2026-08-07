# Final Chapter-Level Claim Audit

Last updated: 2026-08-07

Status: complete; awaiting final Week 13 review.

## Audit Scope

This audit checks the Week 13 thesis-facing claim authority and four reviewed
chapter drafts at source baseline commit
`752e2791f972c10604a532d5c98fbdb653471bb8`:

```text
docs/thesis/claim_to_evidence_table.md
docs/thesis/implementation_draft.md
docs/thesis/experimental_methodology_draft.md
docs/thesis/results_draft.md
docs/thesis/limitations_draft.md
```

It does not audit an Introduction, Background, Conclusion, or final LaTeX
assembly because those artifacts are outside the Week 13 drafting scope. It
also does not rerun formal timing or modify archived evidence.

## Bound Draft Inputs

The audited files have the following SHA-256 values:

| File | SHA-256 |
| --- | --- |
| `claim_to_evidence_table.md` | `7f48e28a2ea0324dcc81a28330957bc280989e509f8c1f4f29a3f525ea77d6d4` |
| `implementation_draft.md` | `2f849e67fa5a2938e2652692ffb911d0afb568c932246ec6d7a1628fe5ae6675` |
| `experimental_methodology_draft.md` | `bd37eafdc477fbc5f18bc0a05e513ea224df09a631fe62be3673b53afc757e0a` |
| `results_draft.md` | `969dec6a08461903a1c8dcdc71f5daaf2fc1f07530aa2de54bf9fd1cf28306a1` |
| `limitations_draft.md` | `be8dfc590b7da5df331da5340de04200a3486cfee11bfd59b4d9fdc6be1f4f2a` |

These hashes identify the exact prose reviewed by this audit. Later wording
changes that alter a controlled claim require another claim audit.

## Controlled Claim Inventory

The claim-to-evidence table contains 46 unique controlled claims:

| Category | IDs | Count | Assigned chapter | Audit result |
| --- | --- | ---: | --- | --- |
| Implementation | `I-01..I-09` | 9 | Implementation | Complete |
| Method | `M-01..M-13` | 13 | Experimental Method | Complete |
| Result | `R-01..R-11` | 11 | Results | Complete |
| Exploratory | `E-01..E-04` | 4 | Results, labeled exploratory | Complete |
| Limitation | `L-01..L-09` | 9 | Limitations and local chapter boundaries | Complete |

Every assigned ID occurs in its target chapter with substantive prose rather
than only in a coverage statement.

## Evidence and Link Audit

The claim table and four drafts contain 133 local Markdown references to 35
unique targets. Every target exists in the repository. The targets cover source
files, design authority, immutable Week 11 and Week 12 evidence, generated
analysis tables, and presentation figures.

The SHA-256 values of all six manifest-bound files in Week 11 `run003` and all
six manifest-bound files in Week 12 `run001` match their archived manifests.
No archived file was rewritten. The Week 12 frozen protocol and environment
fields used in Method, Results, and Limitations also match `config.json` and
`environment.json`.

The Results headline tables were checked against the generated artifacts. This
includes correctness counts, runtime by size, overall and size-level ratios,
the relative-IQR flag, measured-call totals, pipeline wall-clock, Week 11/12
directional replication, and the exploratory structure/counter relationships.
No numerical mismatch was found.

## Cross-Chapter Consistency Audit

### Reference and Paper Output Provenance

The chapters consistently restrict oracle-derived sorted output to the
simplified reference pipeline. The paper core is described as recovering its
output from the maintained partial order and not reading
`oracle_result["sorted"]`. The certified wrapper's oracle call is limited to
valid-input certification before the core. Result: pass.

### Valid-Input Sorting and Recognition

The Method fixes Week 12 as oracle-certified valid-input sorting, Results do
not report recognition performance, and Limitations explicitly reserve
recognition as a separate experimental question. Result: pass.

### Timing Scopes

The Method, first Results ratio interpretation, and Limitations all state that
the reference measurement includes its complete oracle-backed pipeline while
the paper measurement contains only the pre-certified `minimal` call. The
paper/reference ratio is consistently called a pipeline-scope comparison, not
a like-for-like end-to-end speedup. Result: pass.

### Backend and Complexity

Implementation and Limitations identify ordinary Python lists as the evaluated
backend and explicitly state that level-linked search trees, heterogeneous
finger trees, and the theoretical split/update backend are not implemented.
No chapter claims linear time or infers asymptotic complexity from the five
tested sizes. Result: pass.

### Statistical Units and Sampling

Method and Limitations distinguish repeated measured calls from independent
generated cases. Results and Limitations retain the one-flat, one-nested,
ten-incremental family imbalance and do not describe the generators as
representative of all Jordan-sequence distributions. Result: pass.

### Cross-Week Comparison and Environment

Week 11 and Week 12 absolute runtimes are not pooled. Results use within-run
ratios and directional comparisons only, while Method and Limitations bind
absolute Week 12 time to its single recorded environment. Result: pass.

### Exploratory Relationships

Structure and checked-counter coefficients are isolated in exploratory Results
subsections and described as non-causal associations. The checked/minimal
policy difference is preserved, and an undefined constant-counter correlation
is not represented as zero. Result: pass.

## Prohibited-Claim Audit

| Prohibited interpretation | Required treatment found | Result |
| --- | --- | --- |
| Ordinary-list implementation is linear time | Ordinary-list and missing-theoretical-backend boundary | Pass |
| Five sizes establish asymptotic complexity | Finite observed-trend wording | Pass |
| Paper/reference is a like-for-like speedup | Both timed scopes stated beside ratio interpretation | Pass |
| Paper output comes from oracle-sorted output | Independent partial-order output provenance | Pass |
| Week 12 evaluates recognition | Valid-input scope and recognition separation | Pass |
| Week 11/12 absolute runtimes can be pooled | Within-run ratio and direction-only comparison | Pass |
| Structure or counters cause runtime changes | Descriptive exploratory wording | Pass |
| Three generators represent all Jordan sequences | Controlled, unbalanced sample limitation | Pass |
| Theoretical trees/backend were implemented | Explicit ordinary-list backend limitation | Pass |

No unsupported positive occurrence of these interpretations was found in the
four audited chapters.

## Dynamic Verification

The following non-formal-experiment checks were run after the chapter audit:

```text
python -m unittest discover -s tests
    Ran 537 tests in 121.864s
    OK

python -m compileall -q src experiments tests
    passed

python experiments/validate_paper_algorithm.py --max-n 8
    exhaustive valid permutations: 2,074 passed
    fixed generated cases: 48 passed
```

The Week 12 formal runner, formal timing, and live formal validator were not
rerun. Their immutable inputs remain manifest-bound and unchanged.

## Findings and Gate

```text
BLOCKER: 0
HIGH:    0
MEDIUM:  0
LOW:     0
```

The four Week 13 chapter drafts satisfy the controlled claim inventory and the
fixed interpretation boundaries. Week 13 may close after this audit is
reviewed. FU LaTeX template integration remains a separate post-Week 13 phase
and must not silently strengthen or change an audited claim.
