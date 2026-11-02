# Documentation

## Current manuscript and experiment

Start with the [current thesis](../thesis/README.md) and its
[Appendix B revision record](thesis/appendix_b_revision_20261102.md), with a
[Chinese review copy](thesis/appendix_b_chinese_review_20261102.md). The earlier
[results revision](thesis/unified_refinement_20261102.md) maps numerical
statements to archived inputs, timing records and follow-up data.

| Topic | Entry point |
| --- | --- |
| Input scope and exclusions | [Unified registry](validation/input_suite_registry_20261101/README.md) |
| Fixed measurement and reporting rules | [Protocol](plan/uninstrumented_rerun_protocol_20261101.md), [addendum](plan/uninstrumented_rerun_addendum_20261101.md) |
| Preparation evidence | [Unified preparation](validation/unified_preflight_20261101/README.md) |
| Formal attempts, deviation and analysis | [Unified formal archive](validation/unified_formal_20261101/README.md) |
| Constructor and stability follow-ups | [Follow-up archive](validation/unified_followup_20261101/README.md) |
| Manuscript numbers, figures and checks | [Generation and audit files](thesis/unified_results_20261101/) |
| Earlier evidence cited in the thesis | [Dated evidence/source index](thesis/evidence_source_index_20261022.md) |
| Removed old deliverables | [Cleanup and recovery record](maintenance/repository_cleanup_20261102.md) |

The current main results use the complete second formal attempt. The first
failed attempt remains archived. Follow-up statistics are kept separate from
the main results. Appendix B now includes the current evidence index and the
author-supplied account of AI use and implementation attribution.

## Document families

| Directory | Contents |
| --- | --- |
| `validation/` | Original experimental, correctness and manuscript-review archives |
| `thesis/` | Revision records, generated manuscript data and earlier audited chapter drafts |
| `plan/` | [Current protocol pointers and historical plans](plan/README.md) |
| `development/` | Implementation notes, proof reviews and development probes |
| `design/` | Definitions, interfaces, scope decisions and algorithm designs |
| `analysis/` | Earlier analyses and their derived tables and figures |
| `progress/` | Dated progress and handoff records |
| `papers/` | [Reference-paper notes and local copies](papers/README.md) |
| `maintenance/` | Repository organization and recovery records |

Dated plans and reports retain the state of their original milestone. Statements
such as “current” or “pending” inside those records must be read with that date
and source revision. The root README describes the present project state.

The four Markdown chapter drafts and their claim audit are historical evidence,
not the active manuscript. They remain unchanged because their hashes are part
of the recorded review. Current editing belongs in `thesis/` at repository root.

Old delivery PDFs and ZIPs are recoverable through the cleanup record. Their
original review reports and links remain unchanged; reproduce a historical
whole-checkout audit at its recorded revision, where those files still exist.
