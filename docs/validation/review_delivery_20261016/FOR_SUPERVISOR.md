# Jordan Sorting: note for supervisor review

Review package completed 17 October 2026. This is a thesis review draft;
registration details and the personally confirmed declaration are not final
submission documents.

The thesis reconstructs Simplified Jordan Sorting as one Python core with an
ordinary-list backend and a heterogeneous red-black finger-tree backend.
Both recover the output from maintained state. The tree supplies endpoint
insertion, split, stable pair handles and header-based ownership transfer.

The source-level argument claims linear total work for the valid-input minimal
core under unit-cost comparisons and machine-word operations, expected
dictionary lookup and amortized dictionary growth. It is a manual argument
about this implementation, not machine verification or an unconditional
wall-clock bound. Bounded correctness checks are separate evidence.

The current formal study contains 140 common inputs and a separate 12-input
targeted split set, with 6,080 sample batches at execution source `4a83fa6`.
The tree/list ratios of per-input medians are 1.114–3.535 and 3.147–3.213,
respectively. The tree is slower on every measured input. The common set has
no two-sided splits; the targeted set covers source size 61 and smaller sides
3/7/19. Older complex-update checks extend correctness coverage, not this
performance sample. No future crossover or broad stress coverage is claimed.

Suggested reading order: Chapters 3–4 (algorithm and implementation), Table 4.1
(coverage and versions), Chapters 5–7 (method, results and limitations), then
Appendix A (evidence bindings). The full argument is in
`docs/development/finger_final_review_20261015.md`, with supporting cost and
representation/locality documents included in this package.

Feedback would be especially useful on:

1. Whether the physical representation and recursive join/deletion transient
   contracts cover every relevant source branch.
2. Whether the mixed-operation potential accounting and finite-parent locality
   argument justify the stated total-cost claim under the specified model.
3. Whether the separation of bounded validation, theoretical work and negative
   runtime results is sufficiently clear, and what should be shortened or
   strengthened before submission.

The recent R3 red-root return and nonempty-split formula corrections are already
included. This package adds the correctness coverage table and optimization-mode
protection for an auxiliary evidence checker. It changes no production sorting
code or formal measurements. Full source and raw archives remain in the
[project repository](https://github.com/YixueWang983/jordan-sorting); package
hashes bind the supplied subset. Nothing has been sent to a supervisor by the
automation preparing this package.
