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
notes for slides 1 through 16 contain 1,509 words.

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
5faadec29ec6a0c967472b7b51ddccbaa19b4e886488176174d7225a0755d52a  Jordan_Sorting_Progress_Report.pptx
62839b21bafd7fa6f4f34ed846eecd1fd8d8f62e9bdd8bfe4dc61a0a21c92f69  Jordan_Sorting_Progress_Report_ZH.pptx
64cd8f68f2ead9ec36e62bfa2b99f3c4fcadfa09a3f8664585df2f4b4ca6e993  Jordan_Sorting_Progress_Report_Speaker_Script.txt
3a6a5a21891ca93fd323da1e6c40e159d674e8ef7af68c7823910d9d2f95baae  Jordan_Sorting_Progress_Report_Speaker_Script_ZH.txt
```

These files report the validated ordinary-list implementation as the evidence
baseline. The finger-tree backend remains a proposed extension that requires a
separate implementation, validation pass, and experiment version.
