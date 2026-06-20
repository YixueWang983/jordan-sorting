# Week 2 Summary

Last updated: 2026-06-20

## Goal

Week 2 的目标是把 Week1 的实验基础设施转成可以承载“简化 Jordan 序列算法”前置结构的参考实现闭环：

1. 明确术语与定义（notation）；
2. 从 upper/lower 对构建 family tree；
3. 增加结构统计 `structure_profile`；
4. 定义并实现 `simplified_jordan_sort` 的 reference skeleton；
5. 做完整契约测试，保证接口、日志和实验可复现性。

## Completed Work

### Week2 Day 1: Notation + Design Scope

- 新建了 `docs/design/notation.md`，统一了术语：
  - Jordan sequence
  - upper/lower pair
  - rank / rank interval
  - crossing / nesting
  - sibling list
  - family tree
- 明确了论文文档语境下“先做 correctness-oriented reference 的边界”。

### Week2 Day 2: Family Tree Data Structures

- 新建 `src/family_tree.py`，实现：
  - `IntervalNode`, `FamilyTree`
  - `validate_pair_family`, `interval_contains`, `proper_interval_contains`
  - `build_family_intervals`, `build_family_tree`, `build_family_trees`
  - `compute_depths`
  - `family_tree_to_dict`
- 关键约束已在实现和测试中固定：
  - 无效 family 直接拒绝；
  - `nodes` 保留输入区间顺序；
  - `roots` 与 `children` 按结构顺序排序；
  - 通过 interval 级别非法输入检查（交叉、重复、共端点、形状错误）。

### Week2 Day 3: Structural Metrics

- 新建 `src/stats.py`，实现 `structure_profile(seq)`。
- 结构指标包括：
  - `upper_interval_count`, `lower_interval_count`, `total_interval_count`
  - `nesting_count`, `max_depth`, `nesting_density`
  - `category`
- 为可复用性支持了 `oracle_result` 与 `family_trees` 的可选参数复用。

### Week2 Day 4: Simplified Algorithm API Design

- 更新 `docs/design/simplified_algorithm_design.md`：
  - 明确输入输出 contract；
  - 明确错误行为；
  - 明确 trace、stats、families、backend 与 implementation 字段。
- 记录了“reference skeleton 边界”：
  - 不主张线性时间；
  - 不实现真实简化 Jordan 排序操作；
  - 暂以 `oracle_result["sorted"]` 作为排序输出。

### Week2 Day 5: Reference Skeleton

- 实现 `src/simplified_jordan.py`：
  - `simplified_jordan_sort(seq)` 的 top-level contract：
    `valid`, `sorted`, `reason`, `oracle`, `families`, `stats`, `trace`, `implementation`, `implementation_stage`, `backend`
  - `implementation = "reference_skeleton"`
  - `implementation_stage = "week2_interface_skeleton"`
  - `backend = {"name": "ordinary_list", "uses_oracle_sorted_output": True, "linear_time_claim": False}`
- 无效输入不构造 family trees，`families=None`；valid 输入返回序列化后的上下树。
- `trace` 明确记录 pipeline：
  - copy_input → oracle → build_family_trees → structure_profile → prepare_reference_backend → extract_rank_order → return_reference_sorted_output
- 通过 `dict(BACKEND_REFERENCE)` 避免返回对象被外部共享污染。

### Week2 Day 6: Tests + Documentation Pass

- 完成并通过了 contract-level 与行为级测试：
  - `tests/test_family_tree.py`
  - `tests/test_stats.py`
  - `tests/test_simplified_jordan.py`
- 覆盖项包括：
  - empty/singleton/flat/nested/incremental 有效序列；
  - upper/lower crossing 与随机/变异 invalid 序列；
  - duplicate 值路径（reason 与回传一致）；
  - trace 步骤与 contract 字段完整性；
  - backend 不可共享性（per-result 独立）。
- 文档与代码契约同步：
  - `docs/design/simplified_algorithm_design.md`
  - `README.md` 与 day6状态指引。

## Test Status

```text
Ran 128 tests in 0.2s
OK
```

## What is Design vs Skeleton

- 已完成是“可复现、可测试、可说明”的结构/契约基础；
- 尚未完成的是“真正简化 Jordan 排序算法”的线性时间核心（包括后续可能的 level-linked structure / finger-search 方向）。

## What is Explicitly Not Implemented yet

- 没有实现真实的简化 Jordan 排序变换流程（split/merge、动态 family 更新）。
- 没有线性时间性能主张。
- 没有新增性能级指标（split 次数、树旋转、对比计数等）到主线实验。

## Week 3 Handoff (ready state)

Week 2 的产物已经可以直接进入 Week 3：

1. `family_tree` 提供了可序列化的上下树结构；
2. `structure_profile` 提供了结构分类输入；
3. `simplified_jordan_sort` 已固定 contract，可作为后续 pipeline 的稳定接口；
4. Day6 契约测试为后续重构提供回归保护。

因此可开始 Week 3 的 reference pipeline strengthen / 文档和实验拓展。
