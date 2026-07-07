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

## 结论

- Week 6 已完成可复核实验闭环，形成可复用的 reference-pipeline 验证记录；
- 从工程上，项目进入稳定复用阶段，后续工作可安全地切到第 7 周的论文写作与分析深化；
- 风险仍在于解释层面的“性能断言边界”：当前实现是可解释 reference pipeline，而不是完整 Jordan 理论线性时间引擎。

## Week 7 接续（不可回退边界）

1. 不改变 `run_small_tests.py` 的输出语义（尤其 Week1/Week4 分离输出）。
2. 不将 `uses_oracle_sorted_output` 修改为真实 Jordan 更新过程，除非另行重构新阶段。
3. 下一步先做“论文结果章节”图表/案例表述，再推进新功能。
