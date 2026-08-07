# FU Berlin LaTeX Integration Plan

Last updated: 2026-08-07

Status: Phase 1 correction complete; awaiting scaffold review before audited
prose migration.

## Goal

Promote the audited Week 13 Markdown baseline into a buildable FU Berlin thesis
structure without changing claim meaning, modifying immutable evidence, or
rerunning formal experiments.

## Content Authority

The content baseline is commit
`752e2791f972c10604a532d5c98fbdb653471bb8`, as bound by
`docs/thesis/final_claim_audit.md` at commit
`f676215b0dfb4415dee8afe42e36e7b1f7ce6814`.

The four audited drafts retain their historical `awaiting review` headers.
They are not edited merely to update status because their exact bytes are
recorded by SHA-256. Week 13 progress and this handoff plan are the current
status authority.

## Template Authority

The scaffold uses the FU Berlin Bachelor-/Masterarbeit example linked from:

```text
https://latex.userpage.fu-berlin.de/WS1920/
```

Downloaded template ZIP:

```text
https://latex.userpage.fu-berlin.de/Materialien/VOrlageFUmitTitel.zip
SHA-256: 09cde171fbe210b3ede1644844ab57594b19e40136e7b50832bbb6f6fe8e6423
```

The source is an FU-hosted course resource rather than a current
Computer-Science-specific mandatory format. Supervisor or examination-office
requirements take precedence if they differ.

The old course example includes the FU Logo. Current Informatik thesis and FU
Corporate Design guidance prohibit student use of that Logo on an
Abschlussarbeit, so the active scaffold deliberately excludes the Logo and its
asset. Sources:

- [Informatik thesis FAQ](https://www.mi.fu-berlin.de/stud/beratungszentrum/FAQ-Hilfe/FAQ-Abschlussarbeit/faq_abschlussarbeit_info/index.html)
- [FU Logo guidance](https://www.fu-berlin.de/presse/service/logo/logo-leitfaden/index.html)

The active metadata identifies the document as a Master's Thesis.

## Phases

1. [x] Create a clean `scrreprt` scaffold, FU title page, bibliography, chapter
   tree, figure area, appendix, and reproducible LuaLaTeX build.
2. [ ] Migrate Implementation while retaining `I-01..I-09` and local
   limitations.
3. [ ] Migrate Experimental Method while retaining `M-01..M-13` and exact
   timing/statistical definitions.
4. [ ] Migrate Results and validated figures while retaining `R-01..R-11`,
   separately labeled `E-01..E-04`, and pipeline-scope context.
5. [ ] Migrate Limitations while retaining `L-01..L-09`.
6. [ ] Draft Introduction, Background, Algorithm Reconstruction, Abstract, and
   Conclusion from primary literature and the audited claim inventory.
7. [ ] Complete bibliography, cross-reference, figure-source, and
   claim-traceability passes.
8. [ ] Perform final PDF layout, accessibility, metadata, and submission-format
   checks after personal and examination metadata are confirmed.

## Phase 1 Verification

```text
make pdf:
    passed with LuaLaTeX, Biber, and resolved cross-references
    29-page A4 scaffold PDF
    no LaTeX warnings, undefined references, or overfull/underfull boxes

visual PDF review:
    unbranded title page, contents, chapter page, and bibliography passed

unit tests:
    537 passed

audited Markdown SHA-256 values:
    unchanged from docs/thesis/final_claim_audit.md
```

The generated PDF and all TeX caches remain under ignored `thesis/build/` and
are not content authority or submission artifacts.

## Fixed Boundaries

- Do not edit Week 11 `run003` or Week 12 `run001` evidence.
- Do not rerun formal timing or enable a new formal execution ID.
- Do not silently strengthen, weaken, or merge a controlled claim.
- Do not describe the ordinary-list implementation as linear time.
- Do not treat paper/reference ratios as like-for-like end-to-end speedups.
- Do not pool Week 11 and Week 12 absolute runtimes.
- Record the source and hash of every thesis-facing figure copied or converted
  from validated analysis output.
