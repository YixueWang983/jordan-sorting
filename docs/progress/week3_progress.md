# Week 3 Progress

Last updated: 2026-06-20

## Day 1: Reference Pipeline Contract Audit

- 确认 `simplified_jordan_sort(seq)` 的顶层字段已稳定：
  - `valid`, `sorted`, `reason`, `oracle`, `families`, `stats`, `trace`,
    `implementation`, `implementation_stage`, `backend`。
- 确认 trace 的稳定步骤序列：
  `copy_input` → `oracle` → `build_family_trees` → `structure_profile`
  → `prepare_reference_backend` → `extract_rank_order` → `return_reference_sorted_output`。
- `backend` 已用 `dict(BACKEND_REFERENCE)` 返回，避免跨调用共享可变对象。
- 对应契约测试通过（contract keys、trace、backend 隔离、invalid behavior 等）。

结论：Week3 Day1 主要工作改为文档/测试确认，不再重复实现。

## Day 2: Debug/Inspection Utility

- 已新增 `family_tree_to_debug_lines(tree)` 到 `src/family_tree.py`。
- 已补齐测试：`tests/test_family_tree.py`。
- 该工具输出区间树的确定性文本表示（根序列化 + 缩进层次）。

接下来 Day3 产出：

- `docs/design/structural_examples.md`：三类结构例子（flat/nested/invalid）。
- Day4 dataset 审计脚本雏形（见 `experiments/profile_generated_cases.py`）。
- Day5 实验汇总脚本雏形（见 `experiments/summarize_results.py`）。
- Day6 决定是否把 `structure_profile` 字段并入 `run_small_tests.py`（已先用可选参数实现）。

## Day 3: Structural Examples

- 已产出 `docs/design/structural_examples.md`。
- 已将示例与 `notation.md` / `structure_profile` / `simplified_jordan_sort` 合并对齐。

## Day 4: Dataset Structural Audit Script

- 已新增 `experiments/profile_generated_cases.py`。
- 脚本会对生成 family-size-case 进行结构剖析并输出分类汇总 CSV（默认路径：
  `results/generator_structure_profile.csv`）。

## Day 5: Result Summary Utility

- 已新增 `experiments/summarize_results.py`。
- 支持把 baseline raw 结果按 `(algorithm, family, n)` 聚合，输出包含
  `min / median / mean / max` 及 `all_correct`。

## Day 6: Structural Fields for `run_small_tests` (Optional)

- 已在 `experiments/run_small_tests.py` 增加 `--with-structure` 开关，
  对 `run_experiment`/`make_result_rows`/`write_csv` 做轻量扩展，
  默认行为不变；结构字段通过独立文件名输出：
  `week1_baseline_results_with_structure_fields.csv`（或 CLI 指定路径）。
