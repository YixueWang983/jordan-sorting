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
1,644 words.

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
13773fb6274deac8d6cbe5fbfeba07b549c7c45110e34c9bfe0b9192062a0f44  Jordan_Sorting_Progress_Report.pptx
269c8e7bd486dcc706e884b2a8628eec4643bc95abca10550d53d0034da405c3  Jordan_Sorting_Progress_Report_ZH.pptx
05f2d8f63a812fede2fb7272f3cae4366205b3c5726b8e83fc1a0d1bcbc5871c  Jordan_Sorting_Progress_Report_Speaker_Script.txt
a7aa191903e439fbdd7ee7cb04656e439acd71d29735613eb83535f904088161  Jordan_Sorting_Progress_Report_Speaker_Script_ZH.txt
```

These files report the validated ordinary-list implementation as the evidence
baseline. The finger-tree backend remains a proposed extension that requires a
separate implementation, validation pass, and experiment version.
