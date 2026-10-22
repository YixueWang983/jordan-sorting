# AI-assistance wording clarification — 22 October 2026

Baseline: `160a0fa3180f164b7a451f64484ed821fc164206`.

The author requested wording that emphasizes framework suggestions and
translation, without claiming that AI drafted most of the thesis. No authorship
percentage is asserted. Appendix B.5 now describes writing assistance as outline
suggestions and translation support, with the author's confirmed academic-wording
and LaTeX-syntax assistance. Recorded code, test, check-execution and
proof-exposition assistance remains separately stated. The writing summary is
not presented as the full scope of all tool use.

The accompanying author-review record is
`docs/development/AI_USE_RECORD_20261022_r2.md`. Its predecessor remains unchanged
at the identity recorded by the numeric-citation manifest. The 410-word personal
reflection remains a separate draft for the author to check; it is not newly
inserted into the PDF.

## Checks

- Fresh isolated LuaLaTeX/latexmk/Biber build: **70 pages, zero final warnings**.
- Numeric citations and all typography settings are retained.
- Rendered and compared all 70 pages against the numeric-citation PDF: only
  physical page **68** changes; the other **69 pages are pixel-identical**.
  Visually inspected page 68: no clipping, overlaps or damaged references.
- The earlier numeric-citation manifest still verifies all seven files.
- Production code, tests, experimental tools and measurements are unchanged.
  No tests, qualifications, calibrations or measurements were rerun for this
  wording change.

The PDF is `output/pdf/jordan_thesis_supervisor_review_20261022_ai_wording.pdf`.
Build logs, source and PDF hashes are recorded here. Prior PDFs and packages are
preserved; no replacement ZIP is produced. The disclosure remains a review draft,
not a signed declaration or a certification of university submission compliance.
