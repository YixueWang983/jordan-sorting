# Week 6 Progress

Last updated: 2026-07-08

## Day 1: 结果复核与实验重跑

### Completed

- [x] 运行全量测试：`python -m unittest discover -s tests`
- [x] 运行 Week 1 smoke：`python experiments/run_small_tests.py --smoke`
- [x] 运行 Week 4 reference：`python experiments/run_small_tests.py --week4-reference`
- [x] 重跑 Week 4 summary：
  `python experiments/summarize_results.py --input-csv results/week4_reference_results.csv --output-csv results/week4_reference_summary.csv`

### Results

- `results/week4_reference_results.csv`：`3675` rows
- `results/week4_reference_summary.csv`：`245` rows
- `results/week1_baseline_smoke_results.csv`：`1` row

## Day 2: Correctness and Structural Gate

### Completed

- [x] `week4_reference_results.csv` 全量核验：
  - `error` 为空的行数 = `3675`
  - `sorted_correct == True` 的行数 = `3675`
- [x] 结构列完整，包含：
  - `upper_interval_count`
  - `lower_interval_count`
  - `total_interval_count`
  - `upper_root_count`
  - `lower_root_count`
  - `nesting_count`
  - `nesting_density`
  - `max_depth`
  - `category`

### Data notes

- 算法集合：`merge_sort`, `python_sort`, `quick_sort`, `sort_plus_laminarity_check`, `simplified_jordan_reference`
- Family 分布每类均为 `525` 行（共 `7` 个 family）
- 每算法/每 family 的 run_count 在 summary 中为 `15`
- `all_correct` 全部为 `True`

## Day 3: 解释性契约复核

### Completed

- [x] 复核 `simplified_jordan_sort` 的关键 trace 顺序稳定性与测试覆盖（基于既有 Day 3/Day 4 测试）。
- [x] 复核边界长度样例在 trace 计数和 `stats/families` 一致性上的覆盖（空序列到长度 5 范围）。

## Day 4: 论文友好证据整理

### Completed

- [x] 输出 Week 6 证据草案结构，确认结论口径：
  - Week 4 是可复现实验与 reference-pipeline 对齐阶段；
  - 无法宣称线性时长或真实 split-merge 核心；
  - 当前算法后端为 `ordinary_list`。
- [x] 将 Day1~2 的核验结果写入本周阶段汇总文件（本文件 + week6_summary）。

## Day 5: 文档索引同步

### Completed

- [x] 完成 week6 计划文件 `docs/plan/week6_plan.md` 创建。
- [x] 将 week6 进度/总结与核心状态入口同步（见下一步 root/docs/README 计划说明更新）。

## Day 6: Week 6 收口

### Completed

- [x] 完成本周核心复核：实验可复现、结果无错误、trace 契约复核通过、输出字段清晰。
- [x] 进入下一周：在 Week 6 summary 中冻结不可回退边界与下周任务边界。

## Day 7: 与 Week 7 交接

- [x] 在 Week 6 收口时，Week 7 可交接约束已冻结到 `docs/progress/week6_summary.md`。
