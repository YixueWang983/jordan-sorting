# Week 7 Summary

Last updated: 2026-07-23

## 本周定位

Week 7 完成的是实验设计加固、成本指标实现和小规模 pilot analysis。

本周没有继续扩展 Jordan-sorting 理论算法，也没有运行最终 thesis-scale
实验。核心目标是回答导师可能追问的实验设计问题：

- 为什么测这些数据？
- generator family 实际覆盖什么结构？
- `nesting_density` 到底是什么意思？
- trace 是否可以代表计算成本？
- 当前 timing protocol 是否足够严谨？

## 已完成内容

### 1) 实验问题与指标映射

新增：

- `docs/plan/week7_plan.md`
- `docs/design/experimental_questions_and_metrics.md`

固定三条实验假设：

- H1: correctness
- H2: structure sensitivity
- H3: cost decomposition

同时明确了 independent variables、dependent variables、correctness metrics 和
diagnostic metrics。

### 2) 结构指标语义修正

保留旧字段：

```text
nesting_density
```

其含义不改变，仍为：

```text
parented intervals / total intervals
```

新增更清楚的字段：

```text
parented_interval_ratio
upper_containment_pair_count
lower_containment_pair_count
containment_pair_count
containment_pair_density
```

并为 invalid distinct-value candidates 新增 crossing severity：

```text
upper_crossing_pair_count
lower_crossing_pair_count
total_crossing_pair_count
```

Duplicate candidates 的 crossing counts 保持 unavailable，因为重复值没有可靠的
rank-interval interpretation。

### 3) Operation counters

新增：

- `src/instrumentation.py`
- `OperationMetrics`
- `instrumented_reference_run(seq)`

Instrumentation 不改变 `simplified_jordan_sort(seq)` 的 public return contract。
当前 counters 覆盖 selected validation and family-tree construction operations：

```text
laminar_pair_checks
upper_pair_checks
lower_pair_checks
crossings_found
interval_validation_checks
containment_checks
parent_candidate_checks
nodes_created
nodes_visited
trace_event_count
```

Trace 仍然用于描述流程；operation counters 用于诊断部分计算成本，但不代表
total computational cost。

### 4) Benchmark protocol

新增：

- `docs/design/benchmark_protocol.md`
- `experiments/run_week7_pilot.py`
- `tests/test_run_week7_pilot.py`

Pilot runner 支持：

- warm-up runs,
- measured runs,
- `perf_counter_ns()`,
- timed region 内 GC 控制,
- fresh list copy,
- case-level summary,
- group-level summary,
- environment JSON。

### 5) Generator coverage audit

新增：

- `experiments/audit_generator_coverage.py`
- `tests/test_generator_coverage_audit.py`

默认 audit 已运行：

```text
results/week7_generator_coverage_audit.csv
376 rows
```

初步观察：

- `random_invalid` 更像 high-entropy invalid stress input；
- fixed upper/lower invalid families 是 localized crossing examples；
- mutation-based invalid 的 crossing severity 有波动，不能未经 audit 就称为 near-valid。

### 6) 小规模 pilot

本周运行的小规模 pilot：

```bash
python experiments/run_week7_pilot.py \
  --sizes 32 64 128 \
  --randomized-cases 2 \
  --warmup-runs 1 \
  --measured-runs 5
```

输出：

```text
results/week7_pilot_raw.csv: 450 rows
results/week7_pilot_case_summary.csv: 90 rows
results/week7_pilot_group_summary.csv: 63 rows
results/week7_environment.json
docs/analysis/week7_pilot_interpretation.md
docs/analysis/week7_pilot_auto_report.md
```

Raw pilot rows 满足：

```text
error = ""
sorted_correct = True
overall_correct = True
```

## Pilot Interpretation

本周 pilot observed：

- 同一 `n` 下，flat/nested/incremental valid cases 的
  `containment_pair_density` 和 `max_depth` 不同；
- 当前 ordinary family-tree builder 仍然执行确定性的 candidate scan，因此同一
  `n` 下 valid cases 的 containment checks 不会因为结构更 flat 而自动下降；
- `random_invalid` 的 crossing severity 通常明显高于 fixed crossing families；
- mutation-based invalid 的 crossing severity 有波动，需要 audit 后再解释。

这些结果 suggest：

- 当前 structural metrics 对解释输入结构有价值；
- 当前 operation counters 能帮助定位 ordinary implementation 的二次扫描成本；
- 后续 generator 设计应基于 measured structural gaps，而不是只依据 family 名称。

因此 Week 7 将 H2 拆成更准确的两个说法：

- H2a：结构指标可以区分 flat、nested 和 incremental inputs；
- H2b：当前 ordinary-list implementation 没有利用这些结构差异，成本主要由输入规模和二次扫描策略决定。

## 测试状态

全量测试通过：

```text
Ran 168 tests
OK
```

## 本周没有承诺

Week 7 没有实现：

- level-linked search trees,
- heterogeneous finger trees,
- dynamic split/merge engine,
- polygon clipping,
- random-tree valid generator,
- final large-scale thesis experiment。

Week 7 也没有改变：

- `oracle_result["sorted"]` 的语义；
- Week 1/Week 4 existing output semantics；
- `simplified_jordan_sort(seq)` 的 public return contract。

## Week 8 Handoff

Week 8 应优先做：

1. 把 Week 7 audit/pilot 结果整理成论文实验设计章节草稿；
2. 决定是否需要新增 generator，但必须基于 coverage audit 的实际缺口；
3. 若继续做 timing，应扩大 pilot 配置，而不是直接宣称 final experiment；
4. 若推进算法实现，应保持 `instrumented_reference_run` 作为 regression and
   diagnostic wrapper。
