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

The original `FULogoRGB.pdf` is retained at `assets/FULogoRGB.pdf` with
SHA-256:

```text
d07b8f4abe1e53507e66d1a6a8d8dea76749764e57574e3704a9a62aefe8af2d
```

The downloaded example includes demonstration prose and stale build outputs.
Those files are not part of this repository. The scaffold retains the FU title
page composition and KOMA-Script basis, uses English as the main language, and
adapts the affiliation to the Department of Mathematics and Computer Science.
The public template is a useful FU resource, not a claim that the Institute of
Computer Science mandates one exact thesis layout.

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

Replace every placeholder in `config/metadata.tex`, confirm the thesis type,
and obtain the current required declaration wording from the responsible FU
office or supervisor. The declaration is intentionally not included yet.

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
