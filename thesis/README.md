# FU Berlin LaTeX Thesis Scaffold

Status: scaffold complete; audited chapter prose not yet migrated.

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

Requirements: LuaLaTeX, Latexmk, and Biber.

```bash
cd thesis
make pdf
```

The generated PDF is `thesis/build/main.pdf`. Build artifacts are ignored by
Git. Use `make clean` for auxiliary files or `make distclean` for all generated
outputs.

## Before Submission

Replace every personal placeholder in `config/metadata.tex` and obtain the
current required declaration wording from the responsible FU office or
supervisor. The scaffold is configured as a Master's Thesis. The declaration
is intentionally not included yet.

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
