# Ownership wording and U diagnostic summary — 22 October 2026

Baseline: `94c9fff6263f0de75428db31ac0ab8ba5035826e`.

The manuscript changes are limited to Chapter 3's ownership-transfer paragraph
and Chapter 6's diagnostic explanation. The former distinguishes logical
parenthood from ordinary-backend per-pair writes and tree-backend header
updates. The latter reports that U has lower per-input medians than the list
in six of fifteen cases, including the two large medium-nesting cases. This
remains a separate diagnostic protocol, not a qualified production comparison.

## Read-only numeric check

`diagnostic_recheck.json` reconstructs L and U medians from 450 existing batch
records (15 cases × 2 variants × 15 batches), with 30 identity records. It
matches the saved reference ratios: six cases below one, nine above one, no
ties. Each per-input ratio is median(elapsed_ns / calls) for U divided by the
corresponding list median. The report records all input-file hashes. This is
not a new sorting or timing run, nor a fresh validation of every stored output
or the complete original archive manifest.

## Build and layout check

A clean isolated LuaLaTeX/latexmk/Biber build produced 70 physical pages with
no final warnings. All pages were rendered and compared with the prior PDF;
66 are pixel-identical. Physical pages 27, 29, 30 and 49 changed and were
visually inspected, including all 15 diagnostic rows. No clipping or overlap
was observed. The approved 418-word reflection and numeric bibliography
mapping are unchanged.

`build_report.json` binds the PDF and all 38 thesis source files and records
the frozen production-directory identities. `manifest.json` binds this new
validation record and PDF; it does not replace any historical manifest.

No production code, experiment tool, test, input, B table, or saved timing
record was changed. No test suite, qualification, calibration, or formal
sample was rerun. Formal measurements retain execution identity `4a83fa6`.
