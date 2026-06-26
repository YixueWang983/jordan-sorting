# Week 4 Notes

Last updated: 2026-06-26

## Week 4 scope freeze

本周目标是把 `reference_skeleton` 变成更“算法可读”的 reference pipeline。  
不做完整 Jordan 排序，不引入高级数据结构，不新增复杂性能承诺，优先稳定中间结构与实验可复现行为。

## Day 1

### Completed

- [x] 复核 Week 4 目标边界：保持 reference-skeleton 定位、以结构化 trace + 可复现 pipeline 为主。
- [x] 明确 non-goals：
  - 完整 Jordan 排序
  - level-linked tree / finger tree
  - 线性时间承诺
- [x] 复核复用链：`upper_pairs / lower_pairs / rank_map / pair_to_interval / build_family_intervals / build_family_trees / structure_profile`
- [x] 先行固定返回字段契约：
  `valid, sorted, reason, oracle, families, stats, trace, implementation, implementation_stage, backend`
- [x] 全量测试通过：
  - `Ran 152 tests`（`OK`）
- [x] 检视文件：
  - `src/oracle.py`
  - `src/family_tree.py`
  - `src/stats.py`
  - `src/simplified_jordan.py`
  - `experiments/run_small_tests.py`
  - `tests/test_simplified_jordan.py`

## Day 2

### Completed

- [x] 新增 `src/jordan_operations.py`，提供操作层状态构建与 trace 转换能力：
  - `build_operation_state`
  - `extract_pair_families`
  - `build_rank_intervals`
  - `operation_state_to_trace_fields`
- [x] 新增 `tests/test_jordan_operations.py`，覆盖：
  - empty / singleton
  - odd / even 长度
  - flat / nested
  - 非 1..n 有效排列
  - duplicate 值行为
- [x] 统一文档边界：`src/jordan_operations.py` 明确不是第二个 oracle，依赖 `oracle.oracle(seq)` 的返回约定。
- [x] `build_rank_intervals` 增强鲁棒性：即使显式传 `rank`，对 duplicate 输入也会拒绝。

## Day 3

- [x] 在 `simplified_jordan.py` 接入 `jordan_operations` 的 operation-state trace。
- [x] valid path trace 现在包含：
  - `build_rank_map`
  - `extract_pair_families`
  - `convert_pairs_to_rank_intervals`
- [x] `implementation_stage` 升级为 `week4_algorithm_facing_reference`（实现语义更新，top-level 契约不变）。
- [x] 验证 tests: `Ran 152 tests`（`OK`）。
- [x] Day3 的 additional differential 断言已完成补充。

## Day 4

- [x] 扩展 `simplified_jordan_sort` 的 differential 与边界测试：
  - valid 家族覆盖（flat / nested / incremental）在 `0,1,2,3,4,5,8,16,32,64` 上做全量验证；
  - invalid family 与 known reason（upper/lower crossing、duplicate）；
  - 保持 `stats["category"] == "invalid"`。
  - 额外检验 `stats` 中 interval counts 与序列化 family tree node counts 一致；
  - 对小规模有效长度（`[]` 到 `[1,2,3,4,5]`）做 boundary trace count 验证。
- [x] 回归全量测试：`Ran 152 tests`（`OK`），验证 trace 与 stage 升级兼容。

## Day 5~7

- [x] Day5 完成：完成实验接入（reference pipeline）和 `WEEK4` 测试接入。
- [x] Day6：生成并检查 `results/week4_reference_results.csv`，共 3675 行，含结构字段且无 `error`，`sorted_correct` 全为 `True`。
- [ ] Day7：整理 Week 4 summary，明确 reference pipeline 的实验边界与 non-linear-time 边界。

## Day 5

- [x] 在 `experiments/run_small_tests.py` 增加可选算法：
  - `simplified_jordan_reference(seq) -> simplified_jordan_sort(seq)`
  - 通过 `--with-simplified` 接入实验算法列表，不影响默认模式。
- [x] 更新 `extract_sorted_output`，让简化 reference 的返回结果提取 `sorted`。
- [x] 在 `tests/test_run_small_tests.py` 增加覆盖 `simplified_jordan_reference` 的导出与 CLI 流程测试。
- [x] 补充 `WEEK4_REFERENCE_CONFIG`（`results/week4_reference_cases` / `results/week4_reference_results.csv`）与 `--week4-reference` 模式。
- [x] 明确输出隔离策略：默认模式仍写 `results/week1_baseline_results.csv`，并不包含 `simplified_jordan_reference`。
- [x] `--with-simplified` 在未显式指定输出路径时直接拒绝，避免与 Week 1 baseline 覆盖混淆。
- [x] 默认的 `--week4-reference` 运行包含 structural fields，便于 Week 4 的 correctness/trace/structure 比较。
- [x] 追加测试：
  - 默认配置不包含 `simplified_jordan_reference`；
  - `--with-simplified` 需要显式输出路径或使用 `--week4-reference`；
  - `--week4-reference` 写入独立 `week4_reference_results.csv`，并包含结构字段。
