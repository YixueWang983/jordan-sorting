# LaTeX Thesis-Wide Final Audit

Last updated: 2026-08-20

Status: thesis content ready and frozen; technical assembly passed locally;
submission metadata and external procedure pending.

## Gate Separation and Freeze Baseline

The three completion gates are intentionally independent:

| Gate | Status | Meaning |
| --- | --- | --- |
| Thesis Content Gate | **READY / FROZEN** | The research content, algorithm account, method, results, limitations, conclusion, and claim boundaries are frozen. |
| Technical Assembly Gate | **PASS (local clean-checkout evidence)** | The full tests, validator, clean LaTeX build, PDF inspection, and hash checks passed on the recorded local environment. |
| Submission Gate | **NOT READY** | Personal and examination metadata, the registered title, the official declaration, and the examination-office submission procedure remain external prerequisites. |

The current thesis content-freeze baseline is:

```text
e2f1af3ebafda7abd49b06f83914e8041e10c8d2
```

The repository tests and immutable-evidence validator results supporting the
Technical Assembly Gate remain the recorded clean-checkout results because the
changes leading to this freeze are thesis-only. The complete LuaLaTeX/Biber
build, citation resolution, figure rendering, and figure hash checks were
rerun against the exact tracked thesis content frozen at this commit. These are
local verification results, not GitHub Actions or independently re-executed
third-party evidence.

## Scope

This audit begins from commit
`1004d542a28db2a51b08c20a7efc743b93347c7f`, after the Abstract and all eight
main chapters passed individual review. It checks the assembled thesis without
adding new research claims, rerunning formal timing, or modifying immutable
Week 11 or Week 12 evidence.

The audit covers:

- thesis-wide claim and timing-scope consistency;
- cross-references, citations, bibliography, and PDF metadata;
- figure provenance and SHA-256 records;
- title page, Abstract, contents, lists, appendix, and bibliography;
- placeholder and stale-status scans;
- A4 page layout and representative full-document visual review;
- current public FU Computer Science format and submission guidance.

## Claim and Evidence Audit

All 46 controlled claims remain represented in the LaTeX chapters under the
boundaries established by `docs/thesis/claim_to_evidence_table.md` and
`docs/thesis/final_claim_audit.md`. The thesis-wide scan found no unsupported
positive occurrence of the prohibited interpretations:

- ordinary-list linear time;
- asymptotic complexity inferred from five sizes;
- like-for-like paper/reference end-to-end speedup;
- oracle-derived output attributed to the paper core;
- Week 12 recognition performance;
- pooled Week 11/12 absolute runtimes;
- causal structure/counter effects;
- representative sampling; or
- implementation of the historical theoretical backend.

The completed Claim Traceability appendix maps the implementation, method,
result, exploratory, and limitation claim groups to their thesis locations and
evidence classes. It also records the Week 11 and Week 12 manifest SHA-256
bindings.

## Citations, References, and Figures

The bibliography contains 16 cited works spanning the primary Jordan-sorting
lineage, ordered-list and finger-search data structures, computational-geometry
applications, and experimental-algorithmics methodology. LuaLaTeX/Biber
resolves all citations and cross-references. The final log contains no
undefined reference, citation warning, overfull box, or underfull box.

The thesis contains seven vector PDF figures: two converted from the validated
Week 12 analysis outputs and five explanatory figures generated from committed
TikZ sources. Source and generated SHA-256 values match the records in
`thesis/figures/README.md`. No analysis source or immutable evidence file was
modified.

## FU Format and Submission Guidance

The current FU Computer Science thesis FAQ permits a Master's thesis in
English, recommends an Abstract of approximately half a page to one page
between the title page and contents, and describes a typical length of 50--80
pages. The assembled thesis is A4, places its one-page Abstract before the
contents, and remains within that page range after the traceability appendix is
included. The title page contains no FU Logo, consistent with the current Logo
prohibition for student theses.

Current examination-office instructions state that Computer Science theses
are submitted electronically. The office supplies a separate official
Declaration of Authorship and requires the signed original to be submitted to
the examination office. The repository therefore does not duplicate that
declaration inside the thesis PDF. These live instructions must be rechecked
immediately before submission.

Official sources checked on 2026-08-08:

- `https://www.mi.fu-berlin.de/stud/beratungszentrum/FAQ-Hilfe/FAQ-Abschlussarbeit/faq_abschlussarbeit_info/index.html`
- `https://www.imp.fu-berlin.de/fbv/pruefungsbuero/Formulare/index.html`
- `https://www.imp.fu-berlin.de/fbv/pruefungsbuero/Formulare/Selbstaendigkeitserklaerung_EN.pdf`
- `https://www.imp.fu-berlin.de/fbv/pruefungsbuero/index.html`

The FAQ describes IEEE as a usual citation style rather than an explicit
mandatory format. The current `authoryear` bibliography style remains a
supervisor-confirmation item, not a technical defect.

## Remaining Submission Inputs

The technical content and layout are complete, but a submission PDF must not
be produced until these placeholders in `thesis/config/metadata.tex` are
replaced and confirmed:

```text
Author Name
Matriculation Number
Supervisor Name
Second Examiner Name
Submission Date
```

The exact registered thesis title should be confirmed at the same time. The
PDF author metadata currently inherits the author placeholder, so this is a
submission blocker rather than a cosmetic issue.

The official Declaration of Authorship must be completed and signed separately
under the examination-office instructions current at submission time.

## Submission-Review Follow-Up

The submission-level review identified three repository-local clarifications,
all resolved without changing experiment evidence or rerunning formal timing:

- `R-01` now distinguishes the 3600 measured rows from the 60 exact-case
  checked audits. Each case was audited once before timing; the raw-row audit
  field carries that case-level result rather than representing 3600 separate
  audit executions. The wording is synchronized across the claim authority,
  Introduction, Results, and Conclusion.
- The odd-index $z_1$ output-anchor anomaly is now pinpointed to page 175 of
  Hoffmann et al. (1986), verified directly against the repository copy of the
  primary paper.
- The build requirements now record the system-font dependency on
  `DejaVu Sans Mono` selected by `main.tex`.

The resulting claim-to-evidence table has SHA-256
`cc88363a5aa25d55a56b614b02826aa1862d7c48c8a1a54bd2c66da17715e2ea`,
which is also recorded in the Claim Traceability appendix.

Follow-up verification reran all 537 repository tests and `compileall`, then
ran the independent Week 12 validator against immutable `run001`. The live
report returned `valid=true`, no errors, and row counts
`3600 / 180 / 45 / 60`; the report was written outside the archive. A clean
LuaLaTeX/Biber build produced a 70-page A4 PDF with resolved references and no
box warnings, and the changed pages plus full-document contact sheets passed
visual inspection.

The 2026-08-14 literature-and-figure follow-up expanded the cited bibliography
to 13 works and added five committed TikZ explanatory figures. Targeted
re-review corrected the running-example arrow direction and the family/sibling
layout, updated the affected source and generated hashes, distinguished the two
validated Week 12 result figures from the five explanatory figures in the
traceability appendix, and added the Brown--Tarjan 1978 DOI. A fresh
LuaLaTeX/Biber build again produced a 70-page A4 PDF with 13 resolved citekeys,
no reference, citation, or box warnings, and visually verified corrected figure
pages. No source, experiment, validator, or immutable evidence file changed.

A subsequent targeted visual correction tightened the seven-node row in the
Step~3(c) explanatory figure so that its final node remains inside the panel
frame. The committed TikZ source and generated PDF hashes were updated, and a
fresh 70-page LuaLaTeX/Biber build plus inspection of the standalone figure and
its thesis page confirmed the corrected boundary with no new warnings.

A second targeted visual correction constrained the three Step~3 boxes in the
running-example figure and recentered its seven-node input and output rows.
The committed TikZ source and generated PDF hashes were updated, and a fresh
70-page LuaLaTeX/Biber build plus inspection of the standalone figure and
physical PDF page 32 confirmed that every element remains inside its panel with
no new warnings.

The 2026-08-20 first-stage optimization follow-up added three directly relevant
Jordan-sorting works: Aurenhammer's convex-hull approach and Sojka's 1997
worst-case and 1999 average-case alternatives. The Background positions them as
distinct directions rather than implementations or experimental comparators in
this thesis. The Conclusion now distinguishes same-core deterministic
replay-based state-consistency validation from the separate evidence-contract
validator, avoiding an unsupported claim of independent state validation. A
clean LuaLaTeX/Biber build produced a 70-page A4 PDF with 16 resolved citekeys,
no reference, citation, or box warnings. The changed Background and Conclusion
pages and a full-document contact sheet passed visual inspection. No algorithm
source, experiment, validator, formal timing, or immutable evidence file
changed.

The 2026-08-20 terminology follow-up replaced thesis-facing week-number,
repository-audit, and gate language with academic pilot/formal-experiment,
bounded-validation, checked-state-audit, and evidence-contract terminology.
Exact archived execution identifiers remain only in the Method and Claim
Traceability appendix as provenance. The formal-experiment pipeline figure was
regenerated from its tracked TikZ source and both hashes were updated. A clean
LuaLaTeX/Biber build produced a 70-page A4 PDF with 16 resolved citekeys and no
reference, citation, or box warnings. The standalone changed figure, selected
affected pages, and a full-document contact sheet passed visual inspection. No
algorithm source, experiment, test, validator, formal timing, or archived
evidence file changed.

## Gate

```text
research claim consistency:       passed
cross-references and bibliography: passed
figure provenance:                passed
technical PDF layout:             passed
immutable evidence boundary:      passed
personal/examination metadata:    pending
official signed declaration:      pending external action
```

No general polishing or new research prose should be added after this point.
Content changes are accepted only for explicit supervisor requests, newly
identified factual/algorithmic/numerical/citation errors, or defects exposed
by the final build. Any such change requires a targeted review. The remaining
routine repository work is limited to confirmed submission metadata, any
supervisor-requested citation style change, and one final build and visual
check of the resulting submission PDF.
