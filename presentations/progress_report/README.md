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
notes for slides 1 through 16 contain 1,455 words.

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
8d4c4a16f1dc40d73ef2a0aa83a507d2fb53de76ff9006a3745c1d197fd4ba95  Jordan_Sorting_Progress_Report.pptx
14a4667d1c90dbb8a6814c626cea1749adace586114405f11f17b3c2fe3f3f87  Jordan_Sorting_Progress_Report_ZH.pptx
3e9192503edd6d627b6de7355e799d7eb89ed06d439486ed27ba89cb0fb693a4  Jordan_Sorting_Progress_Report_Speaker_Script.txt
1cfc694f836292146914fb2ac5bce119768027ffe784c45894166732510e7bf9  Jordan_Sorting_Progress_Report_Speaker_Script_ZH.txt
```

These files report the validated ordinary-list implementation as the evidence
baseline. The finger-tree backend remains a proposed extension that requires a
separate implementation, validation pass, and experiment version.
