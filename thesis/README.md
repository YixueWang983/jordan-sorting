# FU Berlin LaTeX Thesis Scaffold

Status: thesis narrative and claim-traceability appendix complete; final audit
in progress pending personal and examination metadata.

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

The old course example includes the FU Logo, but the current Informatik thesis
FAQ explicitly prohibits using the Logo on Abschlussarbeiten. The current FU
Corporate Design guidance likewise reserves Logo use for authorized contexts.
This scaffold therefore contains no FU Logo file or Logo reference. See the
[Informatik thesis FAQ](https://www.mi.fu-berlin.de/stud/beratungszentrum/FAQ-Hilfe/FAQ-Abschlussarbeit/faq_abschlussarbeit_info/index.html)
and the current
[FU Logo guidance](https://www.fu-berlin.de/presse/service/logo/logo-leitfaden/index.html).

The public template is a useful historical FU resource, not a claim that the
Institute of Computer Science mandates one exact thesis layout. Current faculty
and university rules take precedence over the old example.

## Build

Requirements: LuaLaTeX, Latexmk, Biber, and the system font
`DejaVu Sans Mono`. The body fonts come from the TeX-distributed Libertinus
package, while `main.tex` selects `DejaVu Sans Mono` through LuaLaTeX's system
font lookup. Confirm that it is discoverable before a clean build, for example
with `fc-match "DejaVu Sans Mono"` where Fontconfig is available.

```bash
cd thesis
make pdf
```

The generated PDF is `thesis/build/main.pdf`. Build artifacts are ignored by
Git. Use `make clean` for auxiliary files or `make distclean` for all generated
outputs.

## Before Submission

Replace every personal placeholder in `config/metadata.tex` and confirm the
exact registered title, supervisor, second examiner, and submission date. The
scaffold is configured as a Master's Thesis.

The current joint Mathematics/Computer Science and Physics examination office
provides an official `Declaration of Authorship` form and states that its
signed original must be submitted to the examination office. The declaration
is therefore kept separate from this PDF instead of copying potentially stale
wording into the thesis. Current forms and submission instructions:

- [Declaration of Authorship](https://www.imp.fu-berlin.de/fbv/pruefungsbuero/Formulare/Selbstaendigkeitserklaerung_EN.pdf)
- [Examination-office forms](https://www.imp.fu-berlin.de/fbv/pruefungsbuero/Formulare/index.html)
- [Computer Science submission instructions](https://www.imp.fu-berlin.de/fbv/pruefungsbuero/index.html)

As of the final audit, Computer Science theses are submitted electronically;
the signed declaration original is submitted separately. Recheck the live
instructions immediately before submission.

## Audited Content Boundary

The four reviewed Markdown chapters and the claim table are immutable content
baselines identified by `docs/thesis/final_claim_audit.md`. Their older
`awaiting review` header text is intentionally preserved because changing it
would invalidate the recorded hashes. Project status documents, not those
headers, record that review has passed.

LaTeX migration must preserve claim meaning. Any wording change that alters a
controlled claim requires a new claim audit. Formatting, citation syntax,
cross-references, table layout, and figure placement do not by themselves
change claim authority.
