# Numeric citations — 22 October 2026

Baseline: `962dff8efcf20b618f440a6f7874d8445d684a2f`.

The author requested numbered citations and a numbered bibliography. The only
LaTeX source change in this increment is `thesis/main.tex`: biblatex now uses
`style=numeric-comp` and `sorting=none`. Numbers follow first citation order.
Narrative citations retain author names (for example, Fung et al. [2]);
parenthetical citations use bracketed numbers. Existing page locators remain.

## Actual checks

- Fresh isolated LuaLaTeX/latexmk/Biber build: **70 physical pages**, no final
  warnings, overfull/underfull reports, or bibliography errors.
- All **15 bibliography entries** are retained. Their numbers are consecutive
  and match first-citation order in the generated auxiliary file.
- Rendered all 70 pages and compared pixels with the October 20 r2 PDF:
  **15 changed pages** (13, 15–19, 21, 23, 27, 31, 33, 42, 61, 69, 70);
  **55 identical pages**. Visually inspected all 15 changed pages, including
  both bibliography pages. No clipping, overlap, missing numbering or broken
  reference rendering was observed.
- The bibliography database, chapter text, fonts, spacing, margins and
  right-page chapter starts are unchanged.
- Production code, experiment tools, tests, data and old validation archives
  have no tracked changes against the baseline. No algorithm tests,
  qualification, calibration or performance measurements were rerun for this
  formatting change. This is not a new mathematical or experimental review.

The PDF is
`output/pdf/jordan_thesis_supervisor_review_20261022_numeric.pdf`.
`build_report.json` records its SHA-256, all thesis-source hashes, citation
mapping and checks. The final TeX/Biber logs and build driver log are retained.
The old PDF and delivery ZIP are unchanged; no replacement ZIP was created.

Rebuild from the repository root with the required LuaLaTeX/Biber toolchain:

```sh
cd thesis
latexmk -lualatex main.tex
```

## Separate AI disclosure draft

`docs/development/AI_USE_RECORD_20261022.md` incorporates the author's newly
confirmed uses: literature search, architecture discussion, academic wording,
ChatGPT web translation and LaTeX syntax troubleshooting. It contains a
410-word English reflection and Chinese review translation. The personal
wording remains for the author to confirm; it is **not inserted into this
PDF**. The existing appendix's review-draft disclosure remains unchanged.
This increment does not certify completion of university submission formalities.
