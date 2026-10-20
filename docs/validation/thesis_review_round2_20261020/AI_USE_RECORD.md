# AI assistance record for the author to finalize

Status: factual review-draft record, not a signed independence declaration.
The author directs the research and uses Codex as an assistant. This record
describes assistance by activity; it does not estimate percentages of authorship
or infer the author's work outside the recorded conversations.

## Applicable public guidance checked on 20 October 2026

The [FU Bachelor/Master Informatik recommendation, 5 November 2025](https://www.mi.fu-berlin.de/bioinf/stud/bachelor/bachelorarbeit/Handreichung_KI_Nutzung_Bachelor_Master_Informatik.pdf)
is specifically for these degree programmes. It calls for an appendix describing
tools, provider/version where available, period, representative requests and
responses, their use and affected parts, together with a personal reflection
(approximately 400 words). Paraphrased AI passages should be identified locally.
The supervisor may specify further requirements; uncertainty about permitted
scope should be discussed with them. Core analysis and conclusions must remain
the student's own work. Code assistance is permitted on the basis of
independently developed code. Disclosure alone does not establish that a
particular use satisfies those conditions.

The [FU university-wide framework, updated 7 October 2025](https://www.ki.fu-berlin.de/_dokumente/Eckpunkte-zum-Umgang-mit-KI-basierten-Systemen-und-Tools-in-Studium-und-Lehre.pdf)
provides the broader transparency and examination context. No exception written
for a different research group has been assumed to apply to this thesis.

These public documents were checked; no private supervisor agreement or
complete inventory of other tools has been supplied.

## Recorded assistance

| Tool | Provider / version | Known period | Activities and affected material |
| --- | --- | --- | --- |
| Codex desktop | OpenAI; model versions across sessions not reliably recorded here | October 11–20, 2026 revision sequence | Assisted with code/test edits, running and inspecting checks, experimental tooling, proof exposition and revision, English/LaTeX drafting, tables and delivery checks |
| AI-assisted external review | Tool/model/provider to be confirmed by the author | Reviews supplied during the revision sequence | Comments on code, proof premises, evidence checks, experimental interpretation and manuscript presentation |

The first row is not a claim that every line in the named areas was generated
by Codex. The author sets the research goals and directs the work. Source diffs,
test logs and saved records identify concrete changes and executions; they do
not by themselves establish authorship percentages or certify mathematical
correctness.

## Representative exchanges and how the suggestions were used

These are concise descriptions, not invented verbatim transcripts. The author
should select the actual request/response excerpts required by their supervisor.

1. **Diagnostic-table revision (this round).** The supplied review requested all
   fifteen rows rather than a selected large-input subset. Codex reconstructed
   them from saved batches and revised the table, abstract and conclusion to
   report four hook-free wins and eleven slower cases. The read-only report
   `local_supplement_recheck.json` binds the resulting numbers. No timing was
   repeated or discarded.
2. **Locality wording (this round).** The review identified the missing dummy
   bracketing condition. Codex inspected the original printed page 88, added
   the premise in Lemma A.5 and connected it to the free slot in A.6. This is a
   source-checked correction to exposition, not a new independently certified
   proof or a change to the sorter.
Affected current manuscript locations: abstract; Chapter 4 generator description;
Chapter 6 diagnostic table and interpretation; Chapter 8 conclusions; Appendix A
locality explanation; Appendix B provenance/disclosure. Earlier code, validation
and proof assistance should also be included in the author's final inventory,
not narrowed retrospectively to this round's language editing.

## Items requiring the author's own confirmation

- Complete the tools/models/providers and usage periods, including external
  review tools, without guessing missing version names.
- Confirm the supervisor's permitted scope and requested disclosure format.
- Select genuine prompt/response examples and identify adopted passages at the
  granularity required by the supervisor.
- Write the personal reflection in the author's own words: effects on the
  research process, helpful and unhelpful uses, how suggestions were checked,
  and lessons learned. No personal experience or reflection has been fabricated.
- Complete and sign the applicable independence declaration personally.

The appendix currently gives an explicit review-draft disclosure and marks
these remaining items. This record does not claim that final university
submission formalities have been completed.
