# Jordan Sorting — revised supervisor reading note

20 October 2026. This is a review draft, not completed school-submission paperwork.

The shared Python core reconstructs Simplified Jordan Sorting with ordinary
lists and a heterogeneous red-black finger tree. Both recover their own output.
The tree supports stable identities, endpoint insertion, split and header-based
ownership transfer.

Read Chapter 3 for the algorithm and exact grouping invariant, Chapter 4 for
implementation and the version-bound correctness table, and Appendix A for the
English representation, locality and mixed-cost proofs. Appendix B gives source
and evidence bindings. The appendix explicitly preserves the red-root join
transient and distinguishes the published child-locality lemma from the
project's finite-parent supplement.

The claimed linear total is source-level work under unit-cost comparisons,
machine-word operations, expected dictionary lookup and amortized growth.
It is a manual argument, not a Python wall-clock guarantee or machine proof.

Chapters 5–7 cover method, results and limitations. The frozen formal study has
140 common inputs and a separate 12-input targeted set, producing 6,080 sample
batches. Its measured tree retains field-access hooks even with detailed
collection disabled. Its input-median tree/list ratios are 1.114–3.535 and
3.147–3.213. These results apply to that configuration; they do not determine
hook-free performance. The common workload has no two-sided splits, while the
small targeted set covers source size 61 and smaller sides 3/7/19.

Reviewer-supplied stress and overhead files are preserved separately. Their
aggregates lack complete execution bindings. A separate local M4 diagnostic
on fifteen fixed cases saves and checks every output: removing access hooks
reduces tree medians by 37.7–52.1%, reversing the four large heavy-case ratios.
It is exploratory, not a replacement formal experiment or a qualified new
backend. Forty additional fixed seeded correctness cases up to 1,500 points
passed, including 678 two-sided splits; eight small cases also use checked
fresh-prefix replay. Full inputs and records are saved for this bounded run.

Feedback is especially welcome on the finite-parent crosscut argument, the
recursive repair and mixed-potential induction, and whether the experimental
interpretation is sufficiently precise. Current production source, inputs,
calibration tables and formal data are unchanged. The package includes the
paper, buildable LaTeX and proof/check notes; full code and raw data remain in
the fixed-version repository. No message has been sent to a supervisor.
