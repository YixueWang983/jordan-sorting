# Week 4 Day 1 Notes（scope freeze）

Last updated: 2026-06-25

## Scope freeze for Week 4

本周聚焦：把 `reference_skeleton` 变成更“算法可读”的 reference pipeline。

- 不实现完整 Jordan 排序；
- 不引入 level-linked / finger-tree 等高级结构；
- 不新增复杂性能承诺；
- 先把中间结构（rank / pair / interval / tree / profile / trace）接口和可复现行为稳定下来；
- 保持与现有实验与现有测试向后兼容。

保持的顶层返回字段（不会在 Day1 改动）：

```text
valid, sorted, reason, oracle, families, stats, trace,
implementation, implementation_stage, backend
```

## Day1 tasks completed

- [x] 跑全量测试：`python -m unittest discover -s tests`
  - 结果：`Ran 139 tests`，全部通过（`OK`）。
- [x] 复核现有接口边界：`reference_skeleton` 定位不变，不宣称完整线性时间实现。
- [x] 复核复用链：`upper_pairs / lower_pairs / rank_map / pair_to_interval / build_family_intervals / build_family_trees / structure_profile`。
- [x] 复核并冻结 Week 4 任务边界（见本文件）。

## Repository files reviewed in this day

- [x] `src/oracle.py`
- [x] `src/family_tree.py`
- [x] `src/stats.py`
- [x] `src/simplified_jordan.py`
- [x] `experiments/run_small_tests.py`
- [x] `tests/test_simplified_jordan.py`

## Next day plan（Day2）

- 新增 `src/jordan_operations.py`，提供：
  - `build_operation_state`
  - `extract_pair_families`
  - `build_rank_intervals`
  - `operation_state_to_trace_fields`
- 增加 `tests/test_jordan_operations.py` 的边界测试（empty/singleton/odd/even/flat/nested/重复值）。

## Day2 progress（today）

- [x] 新增 `src/jordan_operations.py`，提供操作层快照和 trace 转换能力。
- [x] 新增 `tests/test_jordan_operations.py`，覆盖：
  - empty / singleton
  - odd / even
  - flat / nested
  - 非 1..n 有效排列
  - 重复值行为
