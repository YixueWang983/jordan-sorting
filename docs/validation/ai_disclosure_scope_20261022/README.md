# AI-use periods, affected material and marking proposal

22 October 2026. Baseline: `46ac95db7d771b503e3eca5afe28b7661fd697d5`.

## Changes

- Appendix B.2 now states that the recorded Codex revision period of October
  11–22 is neither a first-use date nor a complete usage history. Claude dates
  remain reported dates; missing ChatGPT dates/passages are not invented.
- The PDF names the identifiable affected manuscript areas and points to the
  new `docs/development/AI_USE_RECORD_20261022_scope.md`. The prior inventory
  remains an immutable historical record, not a current completeness claim.
- `docs/thesis/ai_disclosure_scope_20261022.md` separates revised/drafted English
  formulations, proof transfer, technical review and typesetting support, with
  revision and location evidence. It is a minimum identifiable scope, not an
  exhaustive provenance reconstruction or a percentage of authorship.
- That document contains concrete proposed local notes and a short request
  for supervisor confirmation. Neither was sent, approved or comprehensively
  inserted into the manuscript. Chapter notes are not assumed to replace local
  marking of adopted passages. The existing reflection note is retained.
- The FU Informatik recommendation of 5 November 2025 was reread from the
  examination-office URL linked in the scope document. The recommendation and
  the proposed implementation are distinguished; no supervisor exception is
  inferred and no completed-disclosure status is asserted.

## Checks performed

- Fresh isolated LuaLaTeX / latexmk / Biber build: **70 physical pages**, no final
  warnings, overfull/underfull boxes or bibliography errors.
- All pages rendered and compared against the reflection-integration PDF:
  physical pages **67 and 68** change; **68 pages are pixel-identical**.
  Both changed pages were visually inspected at full-page resolution.
- The approved **418-word reflection** is unchanged in source and matches PDF
  extraction after typographic normalization. Its local assistance note remains.
- Numeric bibliography entry order is unchanged; all 38 thesis build inputs
  are hash-bound in `build_report.json` and checked against the working files.
- Relative Markdown evidence links in the two new records resolve. Earlier
  disclosure/build manifests remain unchanged and verify.
- Production code, tests, experiment tools, data, main chapters, Appendix A,
  reflection source and bibliography are unchanged relative to the baseline.
  No algorithm tests, qualification, calibration or formal samples were rerun.

Output: `output/pdf/jordan_thesis_supervisor_review_20261022_disclosure_scope.pdf`.
The source and rendered-output checks are not approval of the disclosure format.
The earlier PDFs, ZIP packages and manifests are retained. No replacement ZIP
or signature is produced by this revision.
