# Jordan Sorting Progress Report

This directory archives the thesis-facing progress presentation current as of
September 2026.

## Presentation files

- `Jordan_Sorting_Progress_Report.pptx`: English presentation, 16 main slides.
- `Jordan_Sorting_Progress_Report_ZH.pptx`: Chinese presentation with the same
  16-slide structure.
- `Jordan_Sorting_Progress_Report_Speaker_Script.txt`: English speaker script.
- `Jordan_Sorting_Progress_Report_Speaker_Script_ZH.txt`: Chinese reference
  script.

Both PPTX files contain speaker notes on all 16 slides. Each notes page includes
a `[Sources]` block that uses repository-relative paths or bibliographic
references. The visible English and Chinese decks share the same technical
claims, experiment boundaries, and slide structure.

The main presentation is written for a midterm progress discussion rather than
as a final-defense or repository-audit deck. Slides 7 through 10 retain the
technical reconstruction detail. Slide 14 shows an ordinary-list runtime
baseline against Python sort. The English notes for slides 1 through 16 contain
1,608 words.

## Source and rebuild boundary

`scripts/build-progress-deck.mjs` is the editable source for the English deck
and the 16-page English speaker script. Slide 14 uses a native two-series
chart with a logarithmic millisecond axis and data from the frozen formal run.
It uses the local images in `assets/` and resolves
all repository sources relative to this checkout. The script requires a Node.js
runtime in which `@oai/artifact-tool` is available. It writes temporary renders
to the ignored `build/` directory and overwrites the English PPTX and script, so
it should only be run when an intentional presentation revision is required.

The Chinese deck and script are a reviewed language adaptation of the same
presentation. They are archived as final deliverables; the current repository
does not claim a fully automated Chinese-deck generation path.

`scripts/count-speaker-words.mjs` reports English speaker-note word counts for
slides 1 through 16. `scripts/deck-design.txt` and
`scripts/source-notes.txt` record the design and source basis used during deck
development.

## Archived file hashes

SHA-256 at the time of archival:

```text
5da1ae6c99b2fc0270fd7622ee0298ddc30ac6a603d766f00677cf3f35ffec90  Jordan_Sorting_Progress_Report.pptx
c7d54128924733383f0659568fec6fba1473c16ed7831b426ee67cc02be622b9  Jordan_Sorting_Progress_Report_ZH.pptx
57763074233ae0fee16a3ee5af62127a18f010c2a34b637489685db1dff55c80  Jordan_Sorting_Progress_Report_Speaker_Script.txt
9313b731c64c40cc1c2bf64a04c3b1c2c7470c762f5a5a02b7ae48794f799696  Jordan_Sorting_Progress_Report_Speaker_Script_ZH.txt
```

These files report the validated ordinary-list implementation as the evidence
baseline. The finger-tree backend remains a proposed extension that requires a
separate implementation, validation pass, and experiment version.
