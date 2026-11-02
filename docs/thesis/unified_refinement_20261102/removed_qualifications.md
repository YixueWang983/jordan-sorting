# 重复限定的删除与缩短清单

下列原文按章节列出；部分引用保留少量定位上下文。完整替换前后文字与原因见 [sentence_changes.json](sentence_changes.json)。

完整的外推、输入族代表性和操作成本边界集中在局限章；完整的首次失败及重跑偏离说明保留在方法章。摘要只保留作者指定的一句简短范围说明，局限章只用一句话指回重跑说明。

## thesis/frontmatter/abstract.tex（修改 1）

Use the author-supplied abstract, generated scale medians, and one short scope sentence; remove restart disclosure here.

```tex
In a paired experiment on \UnifiedN{} unique inputs from five construction
families, the uninstrumented tree is faster on \UnifiedWins{} inputs and the
ordinary list on the remainder. The median tree/list ratio is
\UnifiedMedian{}, with range \UnifiedMinimum{}--\UnifiedMaximum{}.
Median ratios decrease across the measured size bands, and the common
source's more heavily nested categories favor the tree more often. These
observations describe the selected inputs of lengths 32--\UnifiedMaxN{};
they do not establish performance on larger or application-derived inputs.
The strongest tree advantages occur on heavily nested inputs with almost no
splitting. Complete-sort measurements therefore do not identify a split's
cost or the operations responsible for those advantages. The main results
come from a complete second attempt after a power-check failure; the restart
is disclosed as a departure from the no-retry protocol.
```

## thesis/chapters/introduction.tex（修改 2）

Move the full population qualification to Limitations.

```tex
range \UnifiedMinimum{}--\UnifiedMaximum{}. These are descriptive summaries
of related constructions, not estimates for a population of Jordan sequences.
```

## thesis/chapters/introduction.tex（修改 3）

Keep source-composition detail with the size analysis.

```tex
Ratios decrease across the measured size bands, whose source compositions
differ.
```

## thesis/chapters/introduction.tex（修改 4）

Remove repeated operation-cost limitation and restart disclosure from the introduction.

```tex
The complete-sort timings do not identify the cost of one split or the
specific operations responsible for a tree advantage. The first attempt
stopped on a power check; the authorized restart and the separation of the
two attempts are explained in \cref{sec:method-deviation}.
```

## thesis/chapters/results.tex（修改 5）

Keep full attempt-selection and restart account in Experimental Method.

```tex
\cref{sec:method-aggregation}. Only the second, complete attempt supplies these
results. The first attempt and the departure from the no-retry rule are
reported in \cref{sec:method-deviation}.
```

## thesis/chapters/results.tex（修改 6）

Remove repeated population qualification.

```tex
range \UnifiedMinimum{}--\UnifiedMaximum{}. This is a secondary description
of the five-source collection, whose composition is given in
\cref{tab:results-sources}; it is not an estimate of performance on an
application's input distribution. \Cref{fig:results-distribution} shows the
spread.
```

## thesis/chapters/results.tex（修改 7）

Keep the operational definition here; explain non-equivalence in Limitations.

```tex
which was added after sampling. The band is not an equivalence test and does
not change the strict $r_i<1$ count above.
```

## thesis/chapters/results.tex（修改 8）

Add the archive-checked within-source endpoint comparison; move extrapolation restriction to Limitations.

```tex
The bands have different source compositions, so their pooled medians do not
isolate a size effect. \Cref{fig:results-size} retains individual observations
and the median at each exact length within each source. These observations do
not establish the behavior above $n=\UnifiedMaxN{}$.
```

## thesis/chapters/results.tex（修改 9）

Describe the figure directly without repeated extrapolation warning.

```tex
and per-source medians at each exact length. Lines connect observed medians
only; they are not fits or predictions between lengths. The count panel gives
```

## thesis/chapters/results.tex（修改 10）

Keep the systematic-design limitation in Input Coverage and Scale.

```tex
tree-faster inputs occur in the medium and heavy categories. This is a
comparison of the selected constructions, not an experiment that varies
nesting depth while holding all other features fixed.
```

## thesis/chapters/results.tex（修改 11）

Remove repeated operation-cost decomposition limitation.

```tex
remaining work of complete sorting. For inputs with one split, the total time
does not separate that split from the other operations. These measurements
cannot identify the contributions of insertion, navigation, ownership,
initialization or output recovery.
```

## thesis/chapters/results.tex（修改 12）

Keep the shape observation and move the isolation limitation to Limitations.

```tex
construction from the single-interior-split balanced and skew inputs. Their
ratios are not isolated comparisons of split implementations.
```

## thesis/chapters/results.tex（修改 13）

Keep construction coverage facts; consolidate design limitations in Limitations.

```tex
and balanced settings are available. Parameter, shape, size, parity and mirror
coverage are not balanced. These points do not identify a general effect of
$k$, and the repeated construction has no single comparable $k$.
```

## thesis/chapters/results.tex（修改 14）

Replace repeated operation-cost warning with a pointer to measured structural descriptions.

```tex
all main timing summaries. A fraction alone omits both the absolute number
and the sizes of the splits. Neither panel measures the cost of one split:
the timed call also includes construction, insertion, navigation, ownership
updates and output recovery.
```

## thesis/chapters/results.tex（修改 15）

Keep the statistical interpretation boundary in Limitations.

```tex
source. Neither panel supports an independent-sample or causal interpretation.
```

## thesis/chapters/results.tex（修改 16）

Remove repeated population qualification.

```tex
none occurs in targeted or structural. The inputs' generation rules and
coverage differ, so the source medians describe these collections rather
than ranking generators as populations.
```

## thesis/chapters/methodology.tex（修改 19）

Consolidate interpretation of component costs in Limitations.

```tex
excludes observation machinery from the final timing comparison. It does not
assign an additive share of total algorithm cost to instrumentation, nor
extend the diagnostic result beyond its selected inputs. The earlier
```

## thesis/chapters/methodology.tex（修改 20）

Add the generated constructor-to-shortest-sort percentage; keep binding-cost interpretation in Limitations.

```tex
paired difference was \UnifiedCtorDifference{}~$\mu$s. These measure constructor
paths, including automatic GC and loop/storage overhead, not pure method
binding. Objects were released after timing. Nothing was subtracted from the
formal sorting observations.
```

## thesis/chapters/methodology.tex（修改 21）

Remove repeated equivalence and restart qualification after the full restart account.

```tex
This check is outside the protocol and excluded from the main statistics.
It describes these two sessions, without establishing equivalence or undoing
the first failure.
```

## thesis/chapters/limitations.tex（修改 22）

Keep the complete operation-cost limitation once, including the new scale-reference interpretation.

```tex
when each instance is created. Complete-sort measurements do not separate
these contributions. The constructor microbenchmark describes its own fixed
batch design, including automatic GC and object retention, and cannot provide
an exact binding-only cost or a fraction to subtract from sorting time.
```

## thesis/chapters/limitations.tex（修改 23）

Replace repeated procedural-deviation account with one short method reference.

```tex
of unrelated system activity. The first attempt's power failure and the
authorized restart remain a departure from the no-retry protocol, despite
successful validation of the second archive.
```

## thesis/chapters/limitations.tex（修改 24）

Remove the second operation-cost and restart caveats within Limitations itself; retain statistical boundaries once.

```tex
2\% near-equality band are post hoc descriptive additions. The comparison of
\UnifiedStabilityN{} overlapping inputs from the two attempts is also post hoc,
outside the protocol and outside the main statistics. Its small observed
changes neither establish equivalence nor cancel the restart deviation.

Neither split fraction nor the selected smaller-side parameter isolates a
single operation's contribution to complete sorting. Operation counts can
describe the work mix, but counts alone do not assign runtime shares. No
significance tests, independent-sample confidence intervals or causal
conclusions are drawn from these dependent constructions.
```

## thesis/chapters/conclusion.tex（修改 25）

Remove repeated population, scale and restart limitations from the research-question answer.

```tex
source's more heavily nested categories have lower ratios. These observations
apply to the selected families and lengths up to \UnifiedMaxN{} on one host.
The main statistics use only the complete second attempt; the first power
failure and the departure from the no-retry rule remain disclosed.
```

## thesis/chapters/conclusion.tex（修改 26）

Remove repeated operation-cost limitation.

```tex
a fixed length. Complete-sort time does not isolate a split's cost or explain
which remaining operations account for the tree's advantages.
```

## thesis/chapters/conclusion.tex（修改 27）

Keep the future-work action without repeating the limitation on counts.

```tex
measurements of candidate explanations; they cannot alone assign runtime
contributions. Independent review
```
