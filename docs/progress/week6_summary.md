# Week 6 Summary

Last updated: 2026-07-08

## 本周目标回顾

Week 6 目标是把 Week 4 的实验结果从“可运行”推进到“可复核、可解释、可直接用于论文证据链”。  
本周不新增核心算法实现，重点完成验证、聚合、解释和文档收口。

## 已完成工作

### 1) 全流程可复核性

- 全量测试通过：
  - 命令：`python -m unittest discover -s tests`
  - 结果：当前版本测试稳定通过（152 tests）
- 基线 smoke：
  - 命令：`python experiments/run_small_tests.py --smoke`
  - 输出：`results/week1_baseline_smoke_results.csv`
- Week 4 reference 复跑：
  - 命令：`python experiments/run_small_tests.py --week4-reference`
  - 输出：`results/week4_reference_results.csv`
- Week 4 summary 复跑：
  - 命令：`python experiments/summarize_results.py --input-csv results/week4_reference_results.csv --output-csv results/week4_reference_summary.csv`

### 2) Week 4 reference 输出核验

对 `results/week4_reference_results.csv` 的关键检查：

- 行数：`3675`（`7 families × 7 sizes × 3 cases × 5 algorithms × 5 runs`）
- `error`：`0`
- `sorted_correct`：全部 `True`
- 结构字段完整：`upper_interval_count`, `lower_interval_count`, `total_interval_count`, `upper_root_count`, `lower_root_count`, `nesting_count`, `nesting_density`, `max_depth`, `category`

`results/week4_reference_summary.csv` 核验：

- 汇总行数：`245`
- 每组 `run_count = 15`（`3 cases × 5 runs`）
- `all_correct` 全为 `True`

### 3) 运行时/结构口径的边界确认

- `simplified_jordan_reference` 与 Week 4 参考链路未发生线性时间承诺扩展；
- 当前 backend 为 `ordinary_list`；
- 输出仍使用 `oracle_result["sorted"]`；
- 无效输入继续保持 `families=None`，并与 reason/分类路径一致。

### 4) 文档/阶段化收口

- 新增 `docs/plan/week6_plan.md` 与 `docs/progress/week6_progress.md`；
- 更新阶段计划：Week 5 的“结果验证任务”已转接到 Week 6 的“复核 + 解释 + 收口”。

## Thesis-facing Interpretation

### 可以讲

- 当前实验链路已经可复现：从生成测试序列、运行 oracle、执行 baseline/reference pipeline，到输出 raw CSV 和 summary CSV，均有脚本支持。
- `simplified_jordan_reference` 已经可以作为实验中的 reference-pipeline 对照项，与普通排序 baseline 一起运行。
- Week 4 reference 实验覆盖 `7` 个 generator family、`7` 个 size、`5` 个 algorithm，总计 `3675` 行 raw timing records。
- 所有 Week 4 reference raw rows 都满足 `error=""` 与 `sorted_correct=True`，说明当前 reference pipeline 在排序输出上与 oracle/ordinary sorted order 一致。
- Structural fields 已经进入 Week 4 reference result，可以支持后续按 `category`, `nesting_density`, `max_depth` 等结构指标解释实验样本。
- Summary CSV 已经能按 `(algorithm, family, n)` 聚合 timing rows，并记录 `run_count` 与 `all_correct`。

### 不能讲

- 不能声称当前实现已经完成理论上的 linear-time Jordan sorting。
- 不能声称 `simplified_jordan_reference` 已经实现 level-linked search trees、heterogeneous finger trees 或真实 dynamic split/merge engine。
- 不能把当前 timing 结果解释为理论复杂度证明；它们只能作为 ordinary-list reference pipeline 和 baseline 的工程实验观察。
- 不能把 generator family 名称直接等同于 structural category；结构类别仍应由 `structure_profile` 计算得到。

### 下一步推进

- Week 7 应优先把 Week 6 的结果事实整理成论文结果章节草稿，而不是继续扩大代码范围。
- 需要把 raw timing/summary 结果转化为少量可解释表格：例如每个 algorithm/family/size 的 median timing、正确性状态和结构类别分布。
- 需要为论文正文补清楚 reference pipeline 的边界：它是 correctness-oriented and explainable，不是 theoretical linear-time implementation。
- 后续如果要推进真正算法实现，应另起阶段，并保持现有 reference pipeline 作为 regression oracle。

## 结论

- Week 6 已完成可复核实验闭环，形成可复用的 reference-pipeline 验证记录；
- 从工程上，项目进入稳定复用阶段，后续工作可安全地切到第 7 周的论文写作与分析深化；
- 风险仍在于解释层面的“性能断言边界”：当前实现是可解释 reference pipeline，而不是完整 Jordan 理论线性时间引擎。

## Week 7 接续（不可回退边界）

1. 不改变 `run_small_tests.py` 的输出语义（尤其 Week1/Week4 分离输出）。
2. 不将 `uses_oracle_sorted_output` 修改为真实 Jordan 更新过程，除非另行重构新阶段。
3. 下一步先做“论文结果章节”图表/案例表述，再推进新功能。
