# Week 4 Summary

Last updated: 2026-06-26

## 目标回顾

Week4 的目标是把 `simplified_jordan_sort` 从“结果正确性骨架”推进为更明确的算法侧 reference pipeline，并接入可复现实验。核心边界没有改动：当前阶段不实现真实线性时间 Jordan 排序，仅做可解释、可复现、可测试的对照参考路径。

## 已完成（稳定项）

- 明确了实验侧调用路径：新增 `simplified_jordan_reference(sequence) -> simplified_jordan_sort(sequence)`，并在实验 runner 中作为可选算法注册。
- 保持默认周线 baseline 配置不变（Week 1 四算法 + Week1 基准输出文件），防止与 `week1_baseline_results.csv` 混淆。
- 新增 `WEEK4_REFERENCE_CONFIG` 与 `--week4-reference`，并输出到独立文件：
  - `results/week4_reference_results.csv`
  - `results/week4_reference_cases`
- `run_small_tests.py` 保护策略到位：
  - 未开启 structural 的 `--structural-output-csv` 会被拒绝；
  - `--with-simplified` 在未显式配置输出路径时会被拒绝；
  - `run_experiment()` 与 CLI 输出解析使用统一的 `_resolve_output_csv()`，避免模式下路径语义不一致。
- 新增/更新了相关测试，覆盖：
  - wrapper 导出与默认算法集合；
  - simplified 与结构输出保护路径；
  - `--week4-reference` 输出和结构字段行为。

## 本周的关键实验结论

我完成并验证了 Week4 reference 运行：

- 命令：

```bash
python experiments/run_small_tests.py --week4-reference
```

- 原始行数：`3675`
- 算法集合：
  - `python_sort`
  - `merge_sort`
  - `quick_sort`
  - `sort_plus_laminarity_check`
  - `simplified_jordan_reference`
- `error`：`0`
- `sorted_correct`：全部为 `True`
- 结构字段存在：`upper_interval_count / lower_interval_count / total_interval_count / upper_root_count / lower_root_count / nesting_count / nesting_density / max_depth / category`
- 使用了可复现脚本产物，不覆盖 Week1 baseline 文件。

## reference pipeline 的性质与边界

- `simplified_jordan_sort` 的 `backend` 仍是 `ordinary_list`，`uses_oracle_sorted_output = True`，`linear_time_claim = False`。
- 有效路径仍返回 `oracle_result["sorted"]`，**不是**完整的 Jordan 变换/更新引擎。
- `implementation`/`implementation_stage` 字段明确区分：
  - `implementation = "reference_skeleton"`
  - `implementation_stage = "week4_algorithm_facing_reference"`
- `families` 与 `stats` 在有效输入下由 family tree 与结构分析产出；无效输入仍返回 `families=None`。

## 非线性时间边界（明确不做）

当前 Week 4 不承诺：

- level-linked search trees
- finger trees / heterogeneous finger trees
- 动态 split-merge 更新树/树结构的真实核心算法
- 线性时间整体复杂度证明

## 与后续周的接续

- Week4 形成了可复现、可解释的参考 pipeline 与实验基线接口。
- 下一步可在该接口上进入更接近真实算法流程的实现：将 operation state 的 trace 化输出作为基础，逐步替换排序后端的来源。
