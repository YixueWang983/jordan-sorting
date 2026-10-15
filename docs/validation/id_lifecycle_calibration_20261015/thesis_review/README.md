# Thesis implementation/method synchronization

The revised PDF is `output/pdf/jordan_thesis_20261015.pdf` at the repository root:
**68 physical pages**, implementation pages 35–40, method pages 41–46. Blank
pages are 2,4,10,12,34. Font size, spacing, margins and right-page chapter rules
are unchanged. `build_report.json` binds the PDF, all TeX/Bib sources and page count.

Implementation now describes the real external-leaf/rib/header representation,
split/adopt and fresh header IDs, shared-core pending checks, v2 qualification
and separately disabled detailed work. Method distinguishes the original 60-case
historical study, current 140 and targeted twelve qualification sets, actual
calibration and still-unexecuted formal samples. The original 20 implementation
and 18 method labels remain. Appendix producer/checker bindings were updated;
abstract/introduction/limitations/conclusion only received necessary scope fixes.
Old results, figures, measurement files and their numerical claims are unchanged.
Cost/representation/locality arguments remain conditional and awaiting full review.

A separate clean source copy was built using the existing TeX Live 2026 toolchain,
LuaLaTeX and native arm64 Biber. The first generic Biber executable failed because
it requested unavailable Command Line Tools; `initial_toolchain_failure.log`
retains that attempt. Using the already-present native Biber resolved it, without
installing software. A long unbreakable length list was corrected; repeated
wording was shortened to avoid mostly empty new pages. No layout parameter changed.
Final `main.log`/`main.blg` have no warning, undefined reference/citation, overfull
or underfull box. Four final all-page contact sheets were inspected, together
with larger renderings of physical pages 36,38,40,41,43,64,65. No clipping,
overlap or illegible table/figure was observed within that review.

This is an implementation/method update and build/visual check, not complete
editorial approval of every old chapter or general-proof acceptance. The PDF
still contains registration/personal placeholders to resolve for delivery.
No new formal performance table is inserted. The compiler and image rendering
ran only after both actual calibration campaigns and their validators finished.

Reproduction in a source copy, with the recorded toolchain on PATH:

```sh
mkdir -p build/texmf-var build/texmf-cache
TEXMFVAR=build/texmf-var TEXMFCACHE=build/texmf-cache latexmk -lualatex main.tex
```
