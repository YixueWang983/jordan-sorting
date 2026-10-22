# AI assistance: affected material and proposed marking

Prepared on 22 October 2026 against `46ac95db7d771b503e3eca5afe28b7661fd697d5`.
This is an evidence-based inventory and a **proposal for supervisor confirmation**,
not an approval of the disclosure format or a declaration that all use is documented.
The author sets the research objectives and accepts or rejects revisions.
No percentages or whole-chapter authorship are inferred from tool activity.

## 1. Dates and the limits of the available record

| Tool | Supported period | What that period does not establish |
| --- | --- | --- |
| Codex desktop / OpenAI | The recorded revision sequence runs from 11 to 22 October 2026. | It does not establish the first use, exclude earlier use, or constitute a complete account history. |
| Claude / Anthropic | The supplied reviewer account identifies review rounds on 17 and 20 October and disclosure discussion on 22 October 2026. | These are reviewer-reported dates, not an independently recovered complete conversation history. |
| ChatGPT web / OpenAI | The author confirmed on 22 October that it was used during thesis preparation for translation, algorithm explanations, review discussion and planning. | The confirmation date is not a usage start date. Exact dates and passage-level provenance cannot be reconstructed from the records currently supplied. No account export was inspected in this revision. |

Model versions remain unverified. If further history is recovered, add dated
evidence to this inventory; do not invent a start date or silently convert an
incomplete history into a complete one. The limitation is now explicit in the PDF.

## 2. Affected material identifiable from the revision record

Locations refer to the current manuscript; labels are more stable than page numbers.
The activity column separates proposed English formulations, revision, translation/
transfer and technical review. It does not claim that the underlying research
ideas, every sentence in a chapter, or the original pre-revision draft came from AI.
Git commits identify revisions, not authorship by themselves: the attribution also
uses the recorded assistance account and the exchanges supplied by the author.

| Current location | Identifiable assistance and adoption | Evidence / precision limit |
| --- | --- | --- |
| Abstract, especially the measurement and hook-diagnostic paragraph; Chapter 1, contributions and findings | Codex-assisted restructuring and revised English formulations to match the implementation and formal results. Claude's later review led to the four-of-fifteen / eleven-of-fifteen qualification in the abstract. | `b6a40746`, `ce0148bf`, `962dff8e`; formal-review and second-review records below. This identifies revisions, not the original authorship of the entire abstract/introduction. |
| Chapter 3, reconstruction boundary, executable anchors, ownership/failure semantics and correctness/complexity boundaries | Codex-assisted technical explanation and revisions to align the exposition with the maintained output and no-rollback implementation. | `b6a40746`; current labels `sec:algorithm-boundary`, `sec:algorithm-anchor-clarifications`, `sec:algorithm-ownership`, `sec:algorithm-correctness-boundary`. Earlier source provenance is not reconstructed here. |
| Chapter 4, backend representation, interfaces, replay, coverage and costs | Codex-assisted consistency checking, English revision and integration as the backend and evidence changed. The prose explaining the gap generator in §4.4.1 was revised following Claude's request that the rule be explicit. | `b6e1116f`, `ce0148bf`, `2da8b662`, `962dff8e`; `sec:implementation-coverage`. The October 12 compaction package was supplied for integration; this does not establish who initially wrote every sentence in that package. |
| Chapter 5, current qualification, timing/calibration, aggregation and acceptance | Codex-assisted restructuring and revised method descriptions from the frozen protocol and stored records; technical checking of execution and statistical terminology. | `ce0148bf`, `2da8b662`; `sec:method-scope`, `sec:method-timing`, `sec:method-aggregation`, `sec:method-evidence`. Input-selection and measurement rules are not attributed to a text generator simply because it helped explain them. |
| Chapter 6, formal results and interpretation; §6.5 table and adjacent paragraphs | Codex-assisted construction/revision of the results presentation from saved data. Claude identified the incomplete diagnostic table; Codex-assisted reconstruction supplied all 15 rows and revised the accompanying interpretation. | `ce0148bf`, `2da8b662`, `962dff8e`; `tab:results-hooks`, `sec:results-hooks`. Saved measurements supply the numbers; they are not generated observations. |
| Chapter 7, scope, coverage and timing limits; Chapter 8, research-question answers and further work | Codex-assisted English revision and alignment of claims with measured configurations and evidence limits. Claude's review led to the explicit four/eleven diagnostic outcome in the RQ2 paragraph and revised further-work wording. | `ce0148bf`, `2da8b662`, `962dff8e`; `sec:limitations-timing-scopes`, `sec:conclusion-rq2`, `sec:conclusion-future-work`. Technical review findings and the author's acceptance decisions are distinct. |
| Appendix A, §§A.1–A.3 | Codex-assisted transfer of the existing review argument into English/LaTeX and new English formulations of that argument; source correspondence and subsequent proof-exposition revision. Claude's review identified the omitted dummy-bracketing premise, restored in A.5/A.6. | `2da8b662`, `962dff8e`; the October 20 record maps the English appendix to R1–R6, L1–L4 and C1–C5. This is drafting/transfer of an argument, not mere spelling correction or a claim of independent proof certification. |
| Appendix B, disclosure; §B.3 reflection | Codex-assisted organization and language revision of the author's supplied account and English draft, plus a Chinese review translation. The author approved inclusion. | `46ac95db`; `ai_reflection_integration_20261022/`. The 418-word reflection already has a local language-assistance note. It remains unchanged in this revision. |
| Figures showing representation, split/adopt and the experimental pipeline; tables and references | Codex-assisted LaTeX/TikZ construction, layout, syntax/build correction and numeric citation formatting. | `2da8b662`, `160a0fa3`; figure sources and build records. This is a separate typesetting/visualization activity, not an additional claim about mathematical authorship. |

The author's confirmation also supports literature search, architecture discussion
and academic-language assistance as process-level uses. It does not identify
specific newly adopted passages in Chapter 2. ChatGPT translation and discussion
cannot currently be assigned to particular paragraphs; **that gap remains open**.
The table is therefore an identifiable minimum scope, not an exhaustive lifetime
inventory and not evidence that unlisted passages had no AI assistance.

### Evidence locators

- [Recorded assistance and concrete revisions, October 20](../validation/thesis_review_round2_20261020/AI_USE_RECORD.md).
- [Formal-result manuscript synchronization](../validation/final_review_formal_20261015/README.md), especially §4.
- [English proof transfer and review-driven restructuring](../validation/thesis_revision_20261020/README.md), especially “Changes” and “Proof correspondence”.
- [Fifteen diagnostic rows, generator rule and A.5/A.6 correction](../validation/thesis_review_round2_20261020/README.md).
- [Approved reflection integration](../validation/ai_reflection_integration_20261022/README.md).
- [Current inventory, representative exchanges and unchanged reflection](../development/AI_USE_RECORD_20261022_scope.md).

## 3. Proposed marking: local notes plus an overview

The [FU Informatik recommendation dated 5 November 2025](https://www.imp.fu-berlin.de/fbv/pruefungsbuero/Informationen-Anleitungen-FAQ/Informationen-und-Anleitungen/Handreichung-KI-Nutzung-Informatik.pdf)
was reread on 22 October. Section 3 asks for documentation and reflection and
recommends a direct indication for paraphrased AI-generated passages; supervisors
may specify additional detail. **A chapter-level overview alone is not assumed
to replace the recommended local indication.**

Proposed application:

1. Keep Appendix B's tool/date overview, this scope map and the representative
   exchanges as the overall record. Do not mark a whole chapter as AI-authored.
2. For identifiable adopted or substantially reformulated passages, place a
   short footnote at the passage or immediately after the clearly delimited
   group of paragraphs. Specify language/drafting assistance separately from
   a technical review finding. Ask the supervisor whether grouping is acceptable.
3. Use section-level notes only to summarize a documented continuous revision;
   the note must state its scope. Ask whether additional local notes are needed.
4. Retain the existing local note for the reflection. Resolve the unlocated
   ChatGPT passages with further history if available; otherwise disclose the
   remaining uncertainty and ask the supervisor how to handle it before formal submission.

### Concrete candidate notes (not yet inserted or approved)

| Location | Proposed text |
| --- | --- |
| §6.5, paragraph beginning “Removing hooks lowers…” | “This interpretation was revised with Codex following a Claude-assisted review of the diagnostic table; the figures come from the saved measurements.” |
| Abstract diagnostic sentences and Chapter 8 RQ2 diagnostic sentences | “The diagnostic qualification was revised with Codex following Claude-assisted review; see Appendix B for the scope of assistance.” |
| Appendix A opening, covering the English exposition in A.1–A.3 | “The English exposition was developed with Codex from the project's existing review argument and subsequently revised against source and review comments; the scope is documented in Appendix B.” |
| A.5 bracketing sentence and A.6 free-slot explanation | “Claude-assisted review identified this omitted premise; the wording was revised with Codex and checked against Fung et al., p. 88.” |
| §4.4.1 gap-generator explanation | “This description was revised with Codex following a request in Claude-assisted review to make the generator rule explicit.” |

These are proposed examples, not the complete set of final notes. The source
locations in §2 provide the remaining review inventory. Inserting only these
examples must not be reported as completion of all passage marking.

## 4. Ready-to-share request for the supervisor (not sent)

> I have documented the tools, the revision periods supported by the available
> records, identifiable affected sections and representative exchanges, and
> included my reflection in Appendix B. Some earlier usage dates and the exact
> passages translated with ChatGPT cannot be reconstructed from my current
> records. I propose an appendix overview with local footnotes for identifiable
> adopted or reformulated passages, and scoped section notes for continuous
> revisions such as the English proof exposition. Would this combination meet
> your expected format, which passages require separate notes, and how should
> I address the remaining gaps in the history? I can supply the scope table
> and candidate notes alongside the review draft.

No supervisor reply has been supplied, and no message was sent in preparing
this document. The proposal is ready for the author to share. The remaining
submission work is to obtain the applicable format decision, apply the agreed
local markings, and address unresolved provenance explicitly. These items are
not closed by the reflection's inclusion or by a successful PDF build.
