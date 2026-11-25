# Master's defence rehearsal script · Yixue Wang

**Main talk: 23:20.** Start the clock on the title slide. Each heading gives the slide time and the running clock. Read the paragraphs aloud. Bracketed italic cues are silent. Advance after the last sentence of each slide. On slides 7–11, enter on the first overlay, then click at the marked breaks. Overlay times run from the start of that slide. Aim for about 110 words per minute averaged over the talk, including clicks and pauses.

## 1. Implementation and Evaluation of the 1990 Simplified Jordan Sorting Algorithm · 0:10 · 0:00–0:10

Good afternoon. I'm Yixue Wang. This thesis, supervised by Professor Wolfgang Mulzer, began with a question about sorting intersections.

## 2. Intersections arrive in curve order · 1:10 · 0:10–1:20

Imagine clipping a polygon against a window. As I walk around the polygon, I can record every place its boundary crosses a window edge. The points arrive in the order I visit them. To work along the edge, I need those same points in order of position.

*[Trace the curve, then move left to right along the axis.]*

Here the curve visits point one, then five, two, four and three. Along the axis I read one, two, three, four, five. If those points could arrive in an arbitrary order, comparison sorting would take order n log n comparisons in the worst case. But this curve is simple. Some visit orders would force it to cross itself. Jordan sorting uses that restriction. My question was what it buys us in an actual implementation.

## 3. Research questions · 1:10 · 1:20–2:30

I started with the simplified algorithm published by Fung and colleagues in 1990. Throughout the talk, the coordinates are distinct and comparable, and the input has already been certified as a Jordan sequence.

My first question was about correctness. If I stop the algorithm after any crossing, can I recover the sorted points seen so far just by reading its state? My second question was about runtime. If I keep the geometric algorithm fixed and change the structure holding its sibling lists, how much does that change the time for a complete sort? And how do both versions compare with merge sort and quicksort? Finally, there is a cost question. Which properties of those list operations actually deliver the linear bound?

## 4. Contributions · 1:00 · 2:30–3:30

To turn the paper into code, I had to settle where the next point goes in the output, when the first crossing needs special treatment, and exactly how siblings are grouped. I implemented those rules in a shared core with two interchangeable backends. Both maintain enough information to return every sorted prefix.

I then timed the backends on 302 paired inputs and ran a separate comparison with general-purpose sorts. On the proof side, I worked out a locality case where the latest pair is the parent. I also connected the cost argument to the red–black tree that the code actually maintains. Let me start with the geometry behind a single insertion.

## 5. Why same-side intervals nest · 1:10 · 3:30–4:40

Each arc in this picture joins consecutive crossings along the curve. Its endpoints define an interval on the horizontal axis. Suppose the first arc is above the axis. The next arc is below, and the sides alternate from there. That gives us an upper family and a lower family.

*[Trace the long lower arc, then a shorter arc inside it.]*

Look at two arcs on the same side. If their endpoints interleaved, one arc would have to cross the other to reach its far endpoint. Simplicity rules that out. Their intervals can be disjoint, or one can contain the other. So I can give each pair a parent, namely the smallest enclosing pair on its own side. Each family gets a dummy root for its outermost pairs.

## 6. What must survive each insertion? · 1:15 · 4:40–5:55

I keep two views of the processed crossings. The list S sub k gives their sorted order after the first k crossings. The family trees tell me who encloses whom. In the diagram, P four owns both children. The left-to-right order of the children agrees with the order of their intervals along the axis.

There is a further rule about the two boxes at the bottom. Among the parent and its direct children, look for the finite pair completed most recently in curve order. If that pair is the parent, its children form a single group whenever it has children. If it is a child, that child's last crossing determines the cut between the left and right groups. Empty groups disappear. Knowing exactly where this cut is will let us insert a pair at a known list boundary.

## 7. Step 1. Find the predecessor-side boundary · 1:00 · 5:55–6:55

Let's follow the last insertion in an example. The numbers in circles are axis values. The labels underneath tell us when the curve encountered them. The previous crossing is z seven, at three. The pending crossing is z eight, at six. Its dashed circle shows us the target. Six is still absent from the sorted prefix. This new pair belongs to the upper family.

*[Click → overlay 2 at about 0:35. Follow the left arrow.]*

Starting at three, I take its predecessor in the current prefix. That's two. The upper pair incident to two is P two, so P two becomes boundary A eight. I'll use it to place the new pair. I still need to know which old pairs it will enclose.

## 8. Step 2. Which sibling list can split? · 1:40 · 6:55–8:35

I come back to three, the previous crossing. This time I look to its right. The algorithm already knows where three is in the sorted prefix, so finding the next processed point is just a neighbor query. The family matters here because a point can have an incident arc on each side of the axis.

*[Click → overlay 2 at about 0:30. Trace the right arrow to the dashed upper arc.]*

The successor is four. Following its upper arc takes me to P six, the pair with endpoints four and five. That gives me B eight. P six is the first member of the sibling list that also contains P four. I've located a whole candidate list by following a single incidence. To decide what to do with it, I test whether B eight encloses the previous crossing.

*[Click → overlay 3 at about 1:05. Point first to three, then to six.]*

Three is outside the interval from four to five. So B eight does not enclose z seven, and its list is split at z eight, which is six. Four found the list. Six supplies the cut. If B eight had enclosed the previous crossing, the new pair would acquire no children in this branch.

## 9. Step 3(a–b). Insert and split · 1:50 · 8:35–10:25

We can now draw the new upper arc from three to six. I'll call it N. First I follow the boundary we found on the left. P two does not enclose three, so I put N immediately after P two in its sibling list. Both have the upper dummy as parent. At this point I've placed N, and I can use the other boundary to get its children.

*[Click → overlay 2 at about 0:35. Trace the cut through the pending point.]*

Here is the list beginning at P six. When I cut it at six, the pair over four and five falls entirely on the left. The pair over seven and eight falls entirely on the right. An old sibling with endpoints straddling this cut would cross the new upper arc. That's why this partition can transfer whole pairs. The enclosed left group becomes a child list of N.

*[Click → overlay 3 at about 1:15. Point to each arc as you name its owner.]*

P six now belongs to N. P four stays with the dummy. We can check the update directly in the drawing. Both old pairs are accounted for, and each has exactly one owner. We have also learned something about the output position of six. Its new child gives us an endpoint we can use straight away.

## 10. Step 3(c). Insert at the geometric anchor · 0:45 · 10:25–11:10

Look at the dashed child arc. It's the rightmost child of N, and its right endpoint on the axis is five. The word “right” matters here. A curve can traverse an arc in either direction. For this increasing insertion I need the geometric right endpoint. If N had acquired no children, my base anchor would have been the previous crossing.

*[Click → overlay 2 at about 0:30. Follow the arrow from five to six.]*

I insert six immediately after five. Reading the updated list now gives every value from one to eight in increasing order.

## 11. Why skip z one and then use it as the anchor? · 1:25 · 11:10–12:35

Here is a small example where the base anchor needs a correction. The curve visits three, five, one, two, four. The square marks the first crossing, z one, whose value is three. We have reached two, and four is pending. On this odd iteration we need a lower pair. The immediate successor of two is the square, but the curve starts there and its only incident pair is upper.

*[Click → overlay 2 at about 0:35. Follow the dashed arrow past the square.]*

I skip the square and reach five. Its lower pair, P three, encloses two. The new pair becomes its child and acquires no children of its own. That leaves two as the base anchor. Inserting four right after two would leave four before three.

*[Click → overlay 3 at about 1:00. Point to the square and the new point.]*

The output test catches precisely that case. Three lies strictly between two and four, so I insert four after three. We skipped the first crossing when we needed an incident lower pair. We use it now because it is the adjacent coordinate in the output.

## 12. What a sibling split costs · 1:20 · 12:35–13:55

Think back to the moment P six moved under N. In the ordinary-list implementation, I scan the sibling list, copy the pieces into new lists and update the ownership of the transferred pairs. Even inserting at a known end copies the existing pair identifiers. On an increasing input, repeated copying alone can accumulate quadratic work.

The tree backend represents that same ordered list as a red–black tree with fingers at its ends. I can search from the ends, split and rejoin along local paths, then assign the resulting list headers to their owners. A pair retains its handle when its group changes hands. The amortized cost of insertion at an end is constant. The amortized split cost grows logarithmically with the size of the smaller piece, with a constant cost even when that piece is empty. The timing experiment asks how these differences play out across an entire sort.

## 13. What does “uninstrumented” remove? · 1:00 · 13:55–14:55

To measure the tree, I had to distinguish switching off a counter from removing the machinery that feeds it. In the instrumented implementation, even with detailed counting disabled, field access still goes through an interceptor. For the timed tree, I generate ordinary field accesses from the same source and remove the observation wrappers. Local algorithmic checks stay in place.

Generation and compilation happen before timing. Once the clock starts, a fresh tree still has to be constructed and its methods bound. The timed call runs the sorting loop and recovers the output. Checking that output against the expected answer comes afterwards. Both backends run with the same minimal execution policy.

## 14. Five input sources · 1:00 · 14:55–15:55

The common source varies nesting, from strict-flat to heavy, across five length bands. It gives us a way to look at nesting at the same length. The targeted inputs fix the length at 128 or 129 and vary the smaller side of an interior split. The structural inputs add balanced and skew shapes at larger sizes, and cases that split previous results again.

The geometric inputs come from cutting orthogonal polygons with a horizontal line. The seeded generator builds valid sequences by inserting into gaps that preserve the noncrossing condition. The distinction I want to carry forward is at the bottom of the table. Common has no two-sided splits. Each of the other sources includes inputs that exercise them.

## 15. Paired timing on 302 certified inputs · 1:00 · 15:55–16:55

For each input, both backends sort exactly the same sequence. Before timing, I compare the checked prefix states and verify the outputs. Then I calibrate a common batch size for that input. Each backend gets five warm-ups and twenty measured batches. I alternate which backend goes first to balance the order of measurement. Every saved output in the completed formal run passed its check.

Each dot in the next plot represents one input. I take its median tree time and divide by its median list time. A ratio below one means that the tree finished sooner. However many calls a batch contains, that input still contributes just one ratio to the overall summary.

## 16. The tree/list gap narrows with length · 0:45 · 16:55–17:40

*[Point to the horizontal parity line, then follow the coloured curves to the right.]*

Each marker is an input, and each line connects medians for a single source at its measured lengths. The figures underneath pool the sources within length bands. From the smallest band to the largest, the pooled median falls from 1.373 to 1.037. That brings the two backends much closer in time. The mix of sources also changes across bands, so this plot doesn't give us a general crossover length. We can look more closely at nesting within the common source.

## 17. Heavy nesting favors the finger tree · 1:10 · 17:40–18:50

Within the common source we can compare inputs of the same length and move from strict-flat through low and medium to heavy nesting. Follow the heavy curve along the bottom. As length increases, it drops below the line of equal time. Across the forty heavy inputs, the tree is faster on twenty-four.

The split history gives us a clue about that result. Each heavy input has at most one split, and none has a split with two nonempty sides. That rules out frequent splitting as the explanation for these particular wins. One candidate is the ordinary backend's liveness check. It walks the owner's parent chain and scans sibling lists at each ancestor. A deep family can make that work expensive. Isolating its contribution would require a targeted measurement.

## 18. How fast do the sorting times grow? · 1:45 · 18:50–20:35

I also ran a separate session that interleaved the Jordan backends with Python merge sort, Python quicksort and CPython's built-in sort. In absolute time, merge sort and quicksort each finished sooner than either Jordan backend on every one of the 302 inputs.

To ask about growth, I used a subset with the same source composition at every size band, twenty-eight common and twenty geometric inputs. For each method I took the median time in each band and divided by that method's own first-band median. That's why all the lines start together on the left. The legend tells us how many times longer each method took in its last band than in its first.

*[Trace the tree, merge sort and quicksort lines to the right edge.]*

For the finger tree the factor is 17.8. For merge sort it's 20.4, and for quicksort it's 22.3. The ordinary Jordan list grows by a factor of 26.7. The built-in sort has the smallest factor here, 14.3. So the finger tree grew more slowly than either Python baseline over these lengths. The absolute timings still favor those baselines. The linear-work claim rests on a separate argument.

## 19. What the implementation proof adds · 1:45 · 20:35–22:20

The table shows where that argument draws on Fung and colleagues and where I needed to extend it. In the first row, their locality lemma addresses a region whose most recently completed pair is a child. The paper also mentions the case where the finite parent itself was completed last. I show that the first re-entry into that unchanged region must use the gap immediately inward from the parent's latest endpoint. That supplies the missing case for the induction on prefixes. In particular, it justifies the boundary calls we used in the example.

In the middle row, the paper describes a balanced tree with upward-pointing ribs. For my implementation, I have to show what the stored red–black structure represents and why insertion, join and split preserve it. A potential on the nodes pays for repairs even when insertions and splits are interleaved.

The last row puts those local costs together. The paper's potential on list sizes pays the smaller-side split charges over the run. Including ownership updates, the shared core and output recovery gives linear total work with expected dictionary costs and amortized tree operations. Here comparisons and machine-word operations have unit cost, and the analysis allows amortized growth of the underlying storage.

## 20. Conclusions and limits · 0:55 · 22:20–23:15

Both backends recover the sorted prefix from their own state. The finger tree also realizes the linear work bound under the model I've described. On the measured inputs, it finished ahead of the ordinary list on 44 out of 302, with a median tree-to-list ratio of 1.257. Its largest advantages occurred with heavy nesting.

Merge sort and quicksort were faster on every input, although the tree's time grew more slowly. The measurements stop at length 513 on one CPython host. I'd next test larger inputs from geometric applications and measure the parent-chain checks directly. That would tell us both whether the gap continues to narrow and how much those checks contribute.

## 21. Questions? · 0:05 · 23:15–23:20

Thank you. I'd be happy to take your questions.

*[Hold on Questions. Open a backup page only if it answers the question.]*

# Discussion only · backup pages

Each reply stands on its own. PDF page numbers below include overlays.

### The reflected z one correction · PDF 30 · about 0:40

In the decreasing case we take the right side of the split. When there are children, the left endpoint of the leftmost child supplies the base anchor. In this example the new value is zero, the first crossing is one and the base anchor is two. Inserting zero just before two would leave one ahead of it. On this odd step the strict between-test moves the anchor to one, so zero goes immediately before one.

### Absolute time per sort · PDF 31 · about 0:35

The vertical axis is time per complete sort, in microseconds, on a log scale. The methods were interleaved in the supplementary session. Taking paired ratios on each input, the median tree time relative to merge sort was 63.2 times as long. Relative to quicksort it was 110.1 times as long. Those ratios help explain how the tree could grow more slowly and still finish later throughout this experiment.

### Growth exponent per doubling · PDF 32 · about 0:35

For each method, I divide the median time in one band by its median in the preceding band, then take the base-two logarithm. An exponent of one corresponds to linear growth under doubling. The finger tree ranges from 1.02 to 1.06 across these transitions. Those are observations on the fixed-source subset. The proof is what lets me make a statement about total work beyond those measurements.

### Key comparisons per element · PDF 33 · about 0:30

I counted order comparisons in a separate untimed pass with wrapped keys. That includes order comparisons with numeric sentinels. Equality tests and hashing are outside this count. On seven inputs the tree used fewer comparisons than quicksort and still took longer. So even on the same input, a comparison count alone doesn't capture the cost of maintaining the sorting structures.

### Finite-parent re-entry and exact grouping · PDF 34 · about 0:35

Take the latest endpoint of the finite parent and move inward to the nearest child endpoint, or to the other parent endpoint if there are no children. That's the gap in the claim. Suppose the curve first re-entered farther away. A crosscut inside the region, together with the later curve outside it, would separate two boundary points still connected by the older curve. Simplicity rules out that separation.

### How the two potentials pay for a run · PDF 35 · about 0:30

The node potential covers repair propagation inside the red–black tree. It gives amortized constant insertion at an end and a split bound that depends on the smaller side. The list-size potential then pays for those split terms across the sequence of operations. Once we include the bounded header updates and the shared core, the total is linear under the stated model.

### Qualification and the timing boundary · PDF 36 · about 0:30

Before timing, I compare checked prefix states and use a fresh checked replay and a fresh minimal call. Inside the interval, I include initialization, per-instance method binding for the tree, sorting, output recovery and batch overhead. Automatic garbage collection stays enabled. After timing, I check the saved outputs and independently reconstruct the timing summaries from the archive.
