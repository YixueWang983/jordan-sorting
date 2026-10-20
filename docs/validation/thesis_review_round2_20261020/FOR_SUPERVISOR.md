# Jordan Sorting — second revised reading note

20 October 2026. Author-directed research with disclosed AI assistance.
This is a supervisor review draft; personal submission details, the complete
AI-tool inventory, personal reflection and signed declaration are not finalized.

Read Chapter 3 for the reconstructed algorithm and exact grouping invariant,
Chapter 4 for the implementation and version-bound correctness coverage,
and Appendix A for the representation, locality and mixed-operation argument.
The linear-work claim uses unit-cost comparisons and machine-word operations,
expected dictionary access and amortized growth. It is a source-level manual
argument, not machine verification or a wall-clock guarantee.

The formal comparison remains unchanged: 140 common inputs and 12 targeted
split inputs, 6,080 sample batches. The measured tree retains access hooks and
has higher per-input medians throughout; tree/list ratio ranges are
1.114–3.535 and 3.147–3.213. The common group has no two-sided splits.

Table 6.5 now displays every one of the fifteen separately selected diagnostic
inputs. Hook removal reduces tree medians by 37.7–52.1%, but only four large
heavy cases favor the hook-free tree. **Eleven of fifteen still take
1.09–1.68 times the list time.** These exploratory, process-local variants are
not new qualified production backends or a replacement formal experiment.

This round also restores the dummy outer-gap bracketing premise from Fung's
page 88 lemma (b), and explains why it leaves a free ownership slot. The
seeded generator rule and parameters are now in the main text; external-review
provenance is in repository documentation. Forty saved supplemental inputs were
regenerated, not rerun through the sorter.

All 805 existing unit tests passed, both formal archives passed read-only
validation, and all fifteen diagnostic rows were reconstructed from raw records.
Production source, frozen inputs, B tables and measurements are unchanged.
Full evidence is indexed by the accompanying README and manifests.

The package supplies a readable PDF and buildable LaTeX, proof text and review
records. Full earlier raw formal archives remain in the repository at baseline
`2da8b662bf3c50c1bd51ee85ed2215a72a34f7c7`:
https://github.com/YixueWang983/jordan-sorting/tree/2da8b662bf3c50c1bd51ee85ed2215a72a34f7c7

Independent review of the finite-parent locality extension and mixed-operation
argument would strengthen confidence in the source-level claim. No external
mathematical certification or supervisor acceptance is asserted here.
