# LaTeX Thesis

## Current review draft

[Wang_Thesis_Refined_Results_2026-11-02.pdf](../output/pdf/Wang_Thesis_Refined_Results_2026-11-02.pdf)
is the current **80-page** draft, built on 2 November 2026. It reports the
complete 302-input unified comparison, with three main result figures and the
prespecified overview in Appendix C.

- [Revision details and every new number's source](../docs/thesis/unified_refinement_20261102.md)
- [Compilation and visual-review record](../docs/thesis/unified_refinement_20261102/build_report.json)
- [Data and preservation checks at the revision](../docs/thesis/unified_refinement_20261102/verification.json)
- [Formal evidence, both attempts and restart decision](../docs/validation/unified_formal_20261101/README.md)

Appendix A is unchanged. The requested Appendix B content update remains
deferred; only the deleted diagnostic-table reference was repaired. This is a
review manuscript; it must not be sent to the supervisor until Appendix B is updated.

## Build

Requirements: LuaLaTeX, Latexmk, Biber, Libertinus fonts and `DejaVu Sans Mono`.
The checked build used LuaHBTeX 1.24.0 (TeX Live 2026) and Biber 2.22.

From the repository root:

```sh
cd thesis
make pdf
```

The result is `thesis/build/main.pdf`; build artifacts are ignored by Git.
Use `make clean` for auxiliary files or `make distclean` for generated outputs.
The checked-in result figures and generated number macros are sufficient for
compilation; building the manuscript does not require another experiment.

The exact isolated build command and source/PDF hashes are in the build record.
Manuscript generation and preservation audits are version-bound: run the
November 1 whole-checkout audit at its recorded revision. It checks historical
PDFs that were subsequently removed from the current checkout. The
[cleanup record](../docs/maintenance/repository_cleanup_20261102.md) provides
that snapshot and individual recovery links.

## Editing and submission status

Edit the current manuscript in `chapters/`, `frontmatter/` and `appendix/`.
The generated number macros under `generated/` come from existing archived
records through `docs/thesis/unified_results_20261101/generate.py`. Keep
measurement data and predetermined inputs unchanged when editing prose.

`config/metadata.tex` controls review mode and cover metadata. Confirm the
registered title, personal and examiner information, submission date and
applicable university requirements before producing a submission version.
Historical Markdown chapter drafts and their audits remain in `docs/thesis/`;
they are not the active manuscript.

Older PDFs and packages are available through the
[deliverable recovery index](../docs/maintenance/repository_cleanup_20261102.md).

## Template Basis


This scaffold is based on the FU Berlin Bachelor-/Masterarbeit example linked
from the university LaTeX course page:

```text
Page: https://latex.userpage.fu-berlin.de/WS1920/
ZIP:  https://latex.userpage.fu-berlin.de/Materialien/VOrlageFUmitTitel.zip
ZIP SHA-256:
09cde171fbe210b3ede1644844ab57594b19e40136e7b50832bbb6f6fe8e6423
```

The downloaded example includes demonstration prose and stale build outputs.
Those files are not part of this repository. The scaffold retains the
KOMA-Script basis and general title-page structure, uses English as the main
language, and adapts the affiliation to the Department of Mathematics and
Computer Science.

The old course example includes the FU Logo. This review scaffold contains no
FU Logo file or Logo reference and does not infer permission from that example.
The October 16 check did not find a Logo prohibition in the currently retrieved
FAQ, so the earlier attribution of that instruction to the FAQ is withdrawn.
Consult the
[Informatik thesis FAQ](https://www.mi.fu-berlin.de/stud/beratungszentrum/FAQ-Hilfe/FAQ-Abschlussarbeit/faq_abschlussarbeit_info/index.html)
and the current
[FU Logo guidance](https://www.fu-berlin.de/presse/service/logo/logo-leitfaden/index.html).

The public template is a useful historical FU resource, not a claim that the
Institute of Computer Science mandates one exact thesis layout. Current faculty
and university rules take precedence over the old example.
