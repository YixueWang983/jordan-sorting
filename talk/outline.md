# Sorting a Jordan sequence from curve order

Master’s thesis defence in English for two reviewers in computational geometry and algorithms. The main talk runs **23:20**, including the title and handoff, leaving **1:40** in the 25-minute slot. Discussion follows. Page timings are speaking estimates. Figure and table paths are relative to the repository root. The numerical notes identify the thesis sources for values to quote.

## 1. Motivation and research questions · 3:30

### 1. Implementation and Evaluation of the 1990 Simplified Jordan Sorting Algorithm · 0:10

- Introduce Yixue Wang, Freie Universität Berlin.
- Acknowledge Supervisor: Prof. Dr. Wolfgang Mulzer. Leave the defence date as [Defence date].

**Reuse** — No figure or table.

**Numbers** — Title from `thesis/config/metadata.tex`.

### 2. A clipping algorithm encounters the right points in the wrong order · 1:10

- Trace the polygon boundary to explain how clipping encounters intersections. The next stage needs those intersections in order along the clipping edge.
- Follow the simple curve through the labelled points, then read the same points from left to right. Ask what the first traversal already tells us about the second.
- The worst-case comparison lower bound for arbitrary permutations is $\Omega(n\log n)$. A simple curve can realize only a restricted set of permutations.

**Reuse** — `fig:jordan-sorting-problem`, adapted in `talk/figures/jordan_sorting_problem.tex` from `thesis/figures/source/jordan_sorting_problem.tex`.

**Numbers** — The five-point example and both orders are in the figure caption in `thesis/chapters/background.tex`. The lower bound is in `sec:introduction-motivation`, `thesis/chapters/introduction.tex`.

### 3. What does the linear-time algorithm buy in practice? · 1:10

- **Reconstruction.** Can the procedure of Fung et al. recover each sorted prefix using its own state? Assume a certified Jordan sequence with distinct, comparable coordinates.
- **Runtime.** On the same inputs, how do ordinary lists and a finger tree compare with each other and with Python merge sort and quicksort?
- **Cost.** Which properties of the sibling-list operations give linear total work, and how much of the measured timing difference can those properties explain?

**Reuse** — No figure or table.

**Numbers** — The 1990 attribution and linear bound are in `sec:background-1990`, `thesis/chapters/background.tex`. The three questions follow `sec:introduction-questions`, `thesis/chapters/introduction.tex`.

### 4. Contributions · 1:00

- Completed reconstruction details of the 1990 algorithm, including both first-point corrections, geometric output anchors and exact sibling grouping.
- Implemented two backends that recover every sorted prefix from their own state.
- Ran a paired experiment on 302 inputs and compared growth with general-purpose sorts.
- Proved the finite-parent locality case and gave a linear-cost argument for the implemented red–black representation.

**Reuse** — No figure or table.

**Numbers** — `\UnifiedN` in `thesis/generated/unified_numbers.tex`. Reconstruction and proof contributions follow `sec:conclusion-contributions` in `thesis/chapters/conclusion.tex`.

## 2. Jordan sequences and nesting · 2:25

### 5. Why intervals on the same side can nest · 1:10

- Join consecutive crossings into pairs $P_i=\{z_{i-1},z_i\}$. With the first arc above the axis, even-indexed pairs are upper arcs and odd-indexed pairs are lower arcs.
- Trace two arcs on the same side. Interleaving endpoints would force a crossing, so their intervals must be disjoint or nested.
- Give each interval its smallest enclosing same-side interval as parent. A dummy root collects the outermost intervals on each side.

**Reuse** — `fig:algorithm-step-example`, panel (a), arcs only, drawn in `thesis/figures/source/step_walkthrough_example.tex`.

**Numbers** — Pair indexing, parity and the two families follow `sec:algorithm-families`, `thesis/chapters/algorithm.tex`.

### 6. What must survive each insertion? · 1:15

- Read $S_k$ as the processed crossings in increasing coordinate order. In parallel, the upper and lower trees record enclosure.
- Follow one parent to its direct children and then to their stored sibling lists. Each child has one owner, and siblings appear in left-to-right order.
- State the grouping rule. If the parent is the latest finite member, its children form one group when nonempty. If a child is latest, its latest endpoint divides the children into at most two nonempty groups. This is what makes a boundary update possible.

**Reuse** — `fig:implementation-family-sibling-structure`, panels (a–b), drawn in `thesis/figures/source/family_sibling_structure.tex`.

**Numbers** — Group counts and the prefix invariant are in `sec:algorithm-sibling-lists` and `eq:algorithm-prefix-invariant`, `thesis/chapters/algorithm.tex`.

## 3. One iteration, followed by the first-point correction · 6:40

### 7. Step 1 finds the predecessor-side boundary · 1:00

- Start panel (a) just before the final crossing of $(1,2,8,7,5,4,3,6)$. The previous value is $z_7=3$, the pending value is $z_8=6$, and the new pair belongs to the upper family.
- Reveal the left arrow in panel (b). The predecessor of $3$ in the sorted prefix is $2$. Its incident upper pair is $A_8=P_2$. Keep that pair marked for insertion.

**Reuse** — `fig:algorithm-step-example`, panels (a) and (b), predecessor side, `thesis/figures/source/step_walkthrough_example.tex`.

**Numbers** — Input, indices, coordinates and pair IDs come from the caption and `sec:algorithm-step1`, `thesis/chapters/algorithm.tex`.

### 8. Step 2 identifies the list that may have to split · 1:40

- Start at $z_7=3$ again. Its immediate successor is $w=4$. Following the upper pair incident to that point gives $B_8=P_6$, the first member of $[P_6,P_4]$.
- Ask whether $B_8$ encloses the previous point. It does not, so this is the list to partition. If the boundary enclosed the previous point, the new pair would acquire no children.
- Point to $4$ and then to $6$. The old neighbor $4$ selects the sibling list. The incoming value $6$ determines where to cut it.

**Reuse** — `fig:algorithm-step-example`, panel (b), successor arrow and dashed arc, `thesis/figures/source/step_walkthrough_example.tex`.

**Numbers** — Both coordinates, boundary IDs and split key are stated in `sec:algorithm-step2`, `thesis/chapters/algorithm.tex`.

### 9. Step 3(a–b) changes who owns the enclosed siblings · 1:50

- Follow $A_8$ first. Insert $N=P_8$ after $P_2$ under the upper dummy, changing $[P_2]$ to $[P_2,N]$.
- Now cut $[P_6,P_4]$ at $6$. A same-side arc straddling the cut here would cross the new arc. The enclosed left group $[P_6]$ becomes the child list of $N$, while the right group $[P_4]$ stays with the dummy.
- Point back to the arcs to check conservation. Both old pairs are still present, each has exactly one owner, and the new parent encloses its child.

**Reuse** — `fig:algorithm-step-example`, panel (c), `thesis/figures/source/step_walkthrough_example.tex`.

**Numbers** — The before/after lists and split value are in `sec:algorithm-step3a-increasing` and `sec:algorithm-step3b-increasing`, `thesis/chapters/algorithm.tex`.

### 10. Step 3(c) turns enclosure into an output position · 0:45

- Follow the new pair to its rightmost child $P_6$. Its geometric right endpoint is $5$, so insert $6$ immediately after $5$. Read back the completed prefix.
- Without children, the base anchor would be the previous crossing.

**Reuse** — `fig:algorithm-step-example`, panel (d), `thesis/figures/source/step_walkthrough_example.tex`.

**Numbers** — Anchor, pending value and output appear in `sec:algorithm-step3c-increasing` in `thesis/chapters/algorithm.tex`.

### 11. Why skip $z_1$ in the search and use it for insertion? · 1:25

- Switch to $(3,5,1,2,4)$ at $i=5$. The successor of $z_4=2$ is $z_1=3$. This first crossing has no lower incident pair, so Step 2 passes it and reaches $5$. The boundary is $P_3$, which encloses $2$.
- The new pair acquires no children. Its base anchor is therefore $2$. Inserting $4$ there would produce $(1,2,4,3,5)$.
- For output, $2<z_1<4$ makes $z_1$ the anchor. Inserting after $3$ restores $(1,2,3,4,5)$. The boundary search needs an incident pair, while output insertion needs the adjacent coordinate.

**Reuse** — `fig:algorithm-z1-example`, panels (a–c), drawn in `thesis/figures/source/z1_boundary_and_anchor_example.tex`.

**Numbers** — Input, boundary and both output orders appear in the figure and `sec:algorithm-z1-anchor`, `thesis/chapters/algorithm.tex`.

## 4. Two backends and the timed configuration · 2:20

### 12. The same sibling split has different costs · 1:20

- Recall the transfer of $[P_6]$. The ordinary backend scans and partitions the list, materializes the outputs and rebinds ownership. Even insertion at a known end copies existing pair IDs in this implementation.
- The heterogeneous red–black tree keeps endpoint fingers and stable pair handles. It splits along local paths and adopts the resulting headers without visiting every transferred leaf.
- On increasing inputs, list insertion alone can incur $\Omega(n^2)$ copying. The tree has amortized constant endpoint insertion and a split cost logarithmic in the smaller side, with a constant base cost for an empty side.

**Reuse** — `fig:proof-split-flow`, drawn in `thesis/figures/source/heterogeneous_split_flow.tex`.

**Numbers** — The example pair ID is from `fig:algorithm-step-example`. See `eq:implementation-boundary-copy-lower-bound` in `thesis/chapters/implementation.tex` and the operation-cost row of `tab:proof-relation` in `thesis/appendix/backend_argument.tex` for the bounds.

### 13. What does “uninstrumented” remove? · 1:00

- Both timed backends run the minimal policy. It disables traces, selected counters and full post-split validation. In the instrumented tree, switching off detailed counting still routes field access through an interceptor.
- The timed tree is generated from the same source with ordinary field access and the observation wrappers removed. Local algorithmic checks remain. Qualification compares the two tree configurations on the registered inputs.
- Draw the timing boundary verbally. Generation and compilation precede the clock. Each timed sort includes construction and method binding for the tree, the sorting loop and output recovery. Expected-output checks follow timing.

**Reuse** — No figure or table.

**Numbers** — None. Configuration and timing boundary follow `sec:implementation-policies` in `thesis/chapters/implementation.tex` and `sec:method-implementations` in `thesis/chapters/methodology.tex`.

## 5. Experimental design and results · 5:40

### 14. Five input sources · 1:00

- Common varies nesting across length bands. Targeted controls the smaller side of an interior split. Structural includes balanced, skew and repeated splits.
- Geometric records crossings of orthogonal polygons. Seeded generates valid sequences by inserting into non-crossing gaps.
- Common has no two-sided splits; the other four sources exercise them.

**Reuse** — Five-row table based on `sec:method-qualification` in `thesis/chapters/methodology.tex`. Two-sided split coverage is reported in `thesis/generated/unified_structure.tex`.

**Numbers** — Source counts come from `\UnifiedCommonN`, `\UnifiedTargetedN`, `\UnifiedStructuralN`, `\UnifiedGeometricN` and `\UnifiedSeededN` in `thesis/generated/unified_numbers.tex`. Lengths, nesting levels and smaller-side parameters come from `sec:method-qualification`.

### 15. Paired timing on 302 certified inputs · 1:00

- Before timing, qualify both backends against the expected order and check how their states evolve along each prefix.
- Calibrate a common batch size per input. Each backend receives 5 warm-ups and 20 measured batches, alternating first position. All saved outputs in the completed formal attempt passed comparison.
- Give each input one vote. Divide its median tree time by its median list time. A ratio below 1 means the tree finished sooner.

**Reuse** — `fig:method-formal-pipeline`, drawn in `thesis/figures/source/current_experiment_pipeline.tex`.

**Numbers** — `\UnifiedN`, `\UnifiedWarmups` and `\UnifiedRounds` in `thesis/generated/unified_numbers.tex`. The ratio is defined in `sec:method-aggregation`, `thesis/chapters/methodology.tex`.

### 16. Ordinary lists usually finish sooner, but the gap narrows · 0:45

- Follow the plotted medians across source-specific lengths and point out the changing source mix.
- Quote only the pooled smallest-to-largest band medians, 1.373 → 1.037. These summarize the bands across sources, whereas each line in the figure follows a single source.

**Reuse** — `fig:results-size`, slide version `talk/figures/ratio_by_length.pdf` uses the same plotted observations as the figure defined in `thesis/chapters/results.tex`.

**Numbers** — `\UnifiedSmallBandMedian` and `\UnifiedLargeBandMedian` in `thesis/generated/unified_refinement.tex`, also reported in `\UnifiedSizesRows` in `thesis/generated/unified_sizes.tex`.

### 17. The strongest tree advantage occurs with heavy nesting · 1:10

- Read the heavy-nesting curve in the common source. Trace how its median tree/list ratio falls across the measured even lengths.
- Of the 40 heavy inputs, 24 favor the tree. Each has at most one split, and none has a two-sided split. Frequent splitting cannot explain this group's advantage.
- The list backend walks the parent chain and scans sibling lists during liveness checks. This is a candidate cost on deep inputs. The complete-sort timings leave its contribution unresolved.

**Reuse** — `fig:results-nesting-by-length`, generated by `thesis/figures/source/plot_common_nesting_by_length.py`.

**Numbers** — Lengths and medians in `sec:results-nesting-by-length`, split counts in `sec:results-structure`, both in `thesis/chapters/results.tex`. Heavy input and win counts are `\UnifiedHeavyN` and `\UnifiedHeavyWins` in `thesis/generated/unified_numbers.tex`.

### 18. How fast do the general-purpose sorts grow? · 1:45

- First give the absolute result. In a separate session on the same 302 inputs, Python merge sort and quicksort each finished sooner than either Jordan backend on every input.
- For growth, use the post hoc fixed-source comparison. Each size band contains 28 common and 20 geometric inputs. Normalize each method’s band median to its own first-band median. This lets us compare growth across the measured range.
- Read the first-to-last factors in the legend (rounded to one decimal place). In the thesis, median time grows **17.81×** for the finger tree, **20.36×** for Python merge sort, **22.25×** for Python quicksort and **26.71×** for the ordinary Jordan list. CPython’s built-in sort, the practical reference, grew **14.33×**.
- The tree’s time grew more slowly than either Python baseline over this range. A faster absolute tree time at larger sizes remains unobserved.

**Reuse** — `fig:baseline-growth`, panel (a), redrawn for the main talk as `talk/figures/growth_curves.pdf` using the data and band medians from `docs/thesis/baseline_comparison_revision_20261120/generate.py`.

**Numbers** — `thesis/generated/baseline_comparison.tex` defines `\BaselineInputs`, `\BaselineCommon`, `\BaselineGeometric`, `\BaselineTreeGrowth`, `\BaselineMergeGrowth`, `\BaselineQuickGrowth`, `\BaselineListGrowth`, and `\BaselineBuiltinGrowth`. The absolute ordering and normalization are in `sec:results-baselines`, `thesis/chapters/results.tex`.

## 6. The proof and its relation to the 1990 paper · 1:45

### 19. Which parts of the linear bound needed a new argument? · 1:45

- **Locality and correctness.** Fung et al. give the latest-child locality lemma and note the finite-parent case. The thesis proves re-entry for the finite-parent case, then uses exact grouping and ownership in a prefix induction to justify each boundary call.
- **Representation.** The paper outlines a balanced tree with upward-pointing ribs. The thesis shows how to decode the implemented red–black tree and preserve it through insertion, join and split. A node potential pays for repairs across mixed operation histories.
- **Total cost.** The paper’s list-size potential pays the smaller-side split charges. The thesis carries that accounting through ownership, core and output work to obtain $O(n)$ expected/amortized work for the minimal tree configuration, assuming unit-cost comparisons and word operations, expected dictionary lookup and amortized growth.

**Reuse** — `tab:proof-relation` in `thesis/appendix/backend_argument.tex`. Show only a condensed table with the rows Locality / Representation and operations / Total cost. Put the proof details above in the speaker notes.

**Numbers** — The 1990 attribution, operation bounds and total-work result are in `tab:proof-relation` and `thm:proof-total`, `thesis/appendix/backend_argument.tex`.

## 7. Conclusion and limits · 1:00

### 20. What the reconstruction establishes, and what remains open · 0:55

- The reconstruction specifies which list to split and which coordinate anchors the output. Both backends recover the sorted prefix from that state. The tree realizes the linear work argument under the stated model.
- The tree is faster on 44 of 302 inputs, with a median tree/list ratio of 1.257. The finger tree gains most on heavy nesting, and its measured growth is slower than that of Python merge sort and quicksort.
- The measurements stop at length 513 on one CPython host and cover certified valid inputs. Larger application-derived inputs and targeted measurements of parent-chain checks would test how far the timing observations carry. Open the discussion here.

**Reuse** — No figure or table.

**Numbers** — The win count, input count, median and maximum length are `\UnifiedWins`, `\UnifiedN`, `\UnifiedMedian` and `\UnifiedMaxN` in `thesis/generated/unified_numbers.tex`. Host and scope are in `sec:method-environment` and `sec:method-scope`, `thesis/chapters/methodology.tex`. The conclusions and proposed tests follow `thesis/chapters/conclusion.tex`.

### 21. Questions? · 0:05

- Invite questions and leave this page on screen for discussion.
- Use the appendix to revisit a worked example, measurement or proof detail on request.

**Reuse** — No figure or table.

**Numbers** — None.

## 8. Backup pages for discussion

| Title | Use |
| --- | --- |
| The reflected $z_1$ correction | Work a decreasing example, reflect the split side and child endpoint, and show the strict between-test for replacing the base anchor. |
| Absolute time per sort | Compare times in physical units across methods and lengths when asked how large the wall-clock differences are. |
| Growth exponent per doubling | Read the adjacent-band exponents from panel (b) and compare them with the linear and quadratic references. |
| Key comparisons per element | Explain the untimed wrapped-key pass and why fewer comparisons on some inputs can still accompany a longer runtime. |
| Finite-parent re-entry and exact grouping | Trace the admissible re-entry gap when the finite parent is the latest member of its region. |
| How the two potentials pay for a run | Separate local tree repair charges from the aggregate cost of splitting sibling lists. |
| Qualification and the timing boundary | Walk through prefix replay, checked versus minimal execution, constructor cost and independent output validation. |
