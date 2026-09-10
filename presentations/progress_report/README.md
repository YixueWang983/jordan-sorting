# Jordan Sorting Progress Report

This directory archives the thesis-facing progress presentation current as of
September 2026.

## Presentation files

- `Jordan_Sorting_Progress_Report.pptx`: English presentation, 21 slides
  (16 main slides and 5 backup slides).
- `Jordan_Sorting_Progress_Report_ZH.pptx`: Chinese presentation with the same
  21-slide structure.
- `Jordan_Sorting_Progress_Report_Speaker_Script.txt`: English speaker script.
- `Jordan_Sorting_Progress_Report_Speaker_Script_ZH.txt`: Chinese reference
  script.

Both PPTX files contain speaker notes on all 21 slides. Each notes page includes
a `[Sources]` block that uses repository-relative paths or bibliographic
references. The visible English and Chinese decks share the same technical
claims, experiment boundaries, and slide structure.

The main presentation is written for a midterm progress discussion rather than
as a final-defense or repository-audit deck. Slides 7 through 10 retain the
technical reconstruction detail; validation mechanics and the proposed
finger-tree backend boundary remain available in the backup slides. The English
notes for slides 1 through 16 contain 1,926 words.

## Source and rebuild boundary

`scripts/build-progress-deck.mjs` is the editable source for the English deck
and English speaker script. It uses the local images in `assets/` and resolves
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
f681d50b595917eede9652b27198d491d7c86d66b6ebfdf36d9af4ca8f3905b6  Jordan_Sorting_Progress_Report.pptx
7a86702d525944dc9b42a8da9f2090d0565b2f07ffd20c4bb01dcbd51367bbbe  Jordan_Sorting_Progress_Report_ZH.pptx
eb2c36ad84c854e3baad473a8f22decb3a4052db34424fbadb78725ac2aa9758  Jordan_Sorting_Progress_Report_Speaker_Script.txt
dcc10f366ab8686ca4a4da731afcb098f72ea7ccb05d875f06d07331fc3f19d5  Jordan_Sorting_Progress_Report_Speaker_Script_ZH.txt
```

These files report the validated ordinary-list implementation as the evidence
baseline. The finger-tree backend remains a proposed extension that requires a
separate implementation, validation pass, and experiment version.
