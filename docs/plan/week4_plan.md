# Week 4 Plan

Last updated: 2026-06-25

## Week 4 Goal

把当前 `reference_skeleton` 继续推进成“算法可读的 reference pipeline”，而不是实现完整 Jordan 排序。

核心路径固定为：

```text
input sequence
  -> oracle
  -> rank map
  -> upper/lower pairs
  -> upper/lower rank intervals
  -> family trees
  -> structure_profile
  -> reference sorted output
  -> differential tests / experiment rows
```

这周目标是把论文里的中间结构（rank/pair/interval/tree/profile）以更清晰、可调试、可复现实验的方式串起来。

## Non-Goals (Important)

这周不做：

- level-linked search trees
- heterogeneous finger trees
- 全量 split/update 的动态树引擎
- 最终线性时间实现与复杂度证明
- 大规模绘图流水线
- 论文最终实验结论（主要关注接口/正确性/可解释性）

## Day 1: Audit Current Pipeline and Freeze Scope

### Main output

- `docs/plan/week4_plan.md`（本文件，冻结 scope）
- `docs/progress/week4_notes.md`（本周起始说明）

### Tasks

1. 跑完整测试：

```bash
python -m unittest discover -s tests
```

2. 复盘 Week 3 约定的输入输出边界（保持 `reference_skeleton` 非完整算法定位）。

3. 明确 Week 4 接口边界说明：

- 保持 correctness-oriented；
- 以算法可读中间结构为主；
- 不宣称线性时间；
- 不实现高级数据结构。

4. 明确现有复用函数链：

- `upper_pairs`, `lower_pairs`
- `rank_map`
- `pair_to_interval`
- `build_family_intervals`
- `build_family_trees`
- `structure_profile`

### Completion check

- 全量测试通过；
- Week 4 scope 在文档里写清楚；
- 之后的开发不再改动当前阶段以外目标。

## Day 2: Add Algorithm-Facing Operations Layer

### Main output

- `src/jordan_operations.py`（新增）
- `tests/test_jordan_operations.py`（新增）

### Tasks

新增一个轻量操作层，把序列解析与中间结构显式化：

- `build_operation_state(seq, oracle_result=None)`
- `extract_pair_families(seq)`
- `build_rank_intervals(seq, rank=None)`
- `operation_state_to_trace_fields(state)`

建议返回形状（可选字段）：

```python
{
    "n": 6,
    "rank_map": {...},
    "upper_pairs": [...],
    "lower_pairs": [...],
    "upper_intervals": [...],
    "lower_intervals": [...],
}
```

强调：优先复用已有函数，不重复实现 rank/pair/interval 逻辑。

### Tests

覆盖：

- empty / singleton
- odd length / even length
- flat valid
- nested valid
- 非 1..n 的有效排列输入（如 [10, 60, 20, 50, 30, 40]）
- duplicate values path

### Completion check

- `jordan_operations.py` 存在且可构建状态；
- `test_jordan_operations.py` 覆盖关键边界；
- 没有重复实现现有 oracle/family_tree 的核心逻辑。

## Day 3: Integrate Operation State into `simplified_jordan_sort`

### Main output

- `src/simplified_jordan.py`（trace 更细）
- `tests/test_simplified_jordan.py`（更新）

### Tasks

保持 top-level result contract 不变（当前 Week 3 已锁定）：

```text
valid, sorted, reason, oracle, families, stats, trace, implementation,
implementation_stage, backend
```

将 valid 路径 trace 增加算法可读阶段：

```text
copy_input
oracle
build_rank_map
extract_pair_families
convert_pairs_to_rank_intervals
build_family_trees
structure_profile
prepare_reference_backend
extract_rank_order
return_reference_sorted_output
```

同步更新：

```python
implementation_stage = "week4_algorithm_facing_reference"
```

`backend` 保持：

```python
{
    "name": "ordinary_list",
    "uses_oracle_sorted_output": True,
    "linear_time_claim": False,
}
```

### Completion check

- 回归现有 `simplified_jordan_sort` 契约；
- valid trace 覆盖新增步骤；
- invalid 行为（`families=None`）不变。

## Day 4: Expand Differential and Boundary Tests

### Main output

- `tests/test_simplified_jordan.py`
- `tests/test_jordan_operations.py`

### Tasks

1. 加强 valid differential 检查：

```python
simplified_jordan_sort(seq)["sorted"] == sorted(seq)
simplified_jordan_sort(seq)["sorted"] == oracle(seq)["sorted"]
```

2. 使用生成家族：

```text
flat_valid, nested_valid, incremental_valid
```

3. 有效性/长度边界：`0,1,2,3,4,5,8,16,32,64`。

4. 继续固定 invalid 边界（upper/lower crossing、random invalid、mutation based、duplicate）。

### Completion check

- valid cases 都满足 `sorted` 等价；
- invalid cases 保持 `valid=False`, `families=None`, `stats["category"]=="invalid"`；
- `reason` 在关键 invalid path 明确。

## Day 5: Add Reference Pipeline to Experiment Runner (optional, controlled)

### Main output

- `experiments/run_small_tests.py`
- `tests/test_run_small_tests.py`

### Tasks

新增可选算法：

```python
simplified_jordan_reference(seq) -> simplified_jordan_sort(seq)
```

把其接入 `extract_sorted_output()`，不改变 Week 1 baseline 默认配置。

建议通过 CLI 开关控制：

```bash
python experiments/run_small_tests.py --with-simplified --with-structure
```

推荐 Week 4 配置（可独立执行）：

- sizes: `[8,16,32,64,128]`
- families: flat/nested/incremental + 两类 invalid + mutation invalid
- algorithms: `python_sort, sort_plus_laminarity_check, simplified_jordan_reference`
- cases_per_size: `2`
- timing_runs: `3`

### Completion check

- 默认模式不受影响；
- 新算法可复现跑通；
- 结构字段与排序正确性日志保持兼容。

## Day 6: Week 4 Small Run + Summary

### Main output

- `results/week4_reference_results.csv`（可复现产物）
- `results/week4_reference_results_with_structure_fields.csv`（可复现产物）
- `docs/progress/week4_summary.md`

### Tasks

1. 小规模运行 Week 4 配置；
2. 写 `week4_summary.md`，重点记录：
   - 与 Week 3 的变化；
   - 新增操作层和 trace；
   - 新测试与边界；
   - 实验结果与当前局限；
3. 不做性能主张，强调 correctness + 可解释性。

### Completion check

- Week 4 小样本 CSV 可复现；
- week4_summary 已创建；
- 接口/行为一致性仍满足旧测试。

## Day 7: Cleanup, Reproducibility, Seminar Handoff

### Main output

- `docs/progress/seminar_status.md`
- `README.md`（可选更新）

### Tasks

1. 全量测试 + smoke 实验；
2. Week 4 结果脚本复现；
3. 产出 seminar 状态文档（完成项 / 待办项 / 讨论问题）；
4. 确保没有“半实现算法”被误表述为最终算法。

### Completion check

- 全量测试通过；
- smoke + week4 复现实验可跑；
- `seminar_status.md` 存在；
- `week4_summary.md` 存在；
- 保持论文范围陈述一致。

## Week 4 Exit Criteria

按期完成应具备：

- `src/jordan_operations.py`
- `tests/test_jordan_operations.py`
- `src/simplified_jordan.py`（trace/operation-state 集成）
- `tests/test_simplified_jordan.py`（差分与边界扩展）
- 实验可选项 `simplified_jordan_reference` 与结构模式可运行；
- `docs/progress/week4_summary.md`
- `docs/progress/seminar_status.md`

实现仍应明确声明为：

```text
week4_algorithm_facing_reference
```

而非“完整 Jordan sorting 算法”。
