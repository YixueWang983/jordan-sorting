# Week 6 Plan

Last updated: 2026-07-08

## Week 6 Goal

把 Week 4 的 reference 实验结果从“可运行”升级为“可复核、可解释、可直接用于论文的阶段性证据”。  
本周不做新的核心算法实现，专注于 **实验复核 + 结果解释 + 文档收口 + 下一周交接**。

## Day 1: Reference Result Revalidation

### Main output

- `docs/progress/week6_progress.md`（记录 Day1 结果）

### Tasks

1. 全量测试复核：

   ```bash
   python -m unittest discover -s tests
   ```

2. 复跑 Week 1 快速链路（防止 baseline 回归）：

   ```bash
   python experiments/run_small_tests.py --smoke
   ```

3. 复跑 Week 4 参考实验：

   ```bash
   python experiments/run_small_tests.py --week4-reference
   ```

4. 复跑 summary：

   ```bash
   python experiments/summarize_results.py \
     --input-csv results/week4_reference_results.csv \
     --output-csv results/week4_reference_summary.csv
   ```

### Completion check

- `Ran 152 tests` 通过（或项目现有版本对应数）。
- `week4_reference_results.csv` 再次生成，`results = 3675`。
- `week4_reference_summary.csv` 再次生成，`results = 245`。

## Day 2: Results Correctness Sanity Gate

### Main output

- `docs/progress/week6_summary.md` 的初始 section（结果核验事实）。

### Tasks

1. 核对 `week4_reference_results.csv`：
   - `error == ""` 总数为 0；
   - `sorted_correct == True` 总数为全部；
   - 结构字段完整（包含 `upper_interval_count`, `lower_interval_count`, `nesting_count`, `max_depth`, `category` 等）。

2. 核对 `week4_reference_summary.csv`：
   - `(algorithm, family, n)` 汇总存在；
   - `run_count` 对应每组 `3 x 5 = 15`；
   - `all_correct == True` 全部为真。

### Completion check

- 关键字段和数值不变量都通过脚本或手工核对。

## Day 3: Contract Lockdown for Interpretability

### Main output
- `tests` 保持现有覆盖不变，确认可复用标准。

### Tasks

1. 复核 trace contract 在 valid path 上是稳定的（无需新增测试代码时先做回归复用）：
   - `build_rank_map`
   - `extract_pair_families`
   - `convert_pairs_to_rank_intervals`
   - `build_family_trees`
   - `structure_profile`
   - `prepare_reference_backend`
   - `extract_rank_order`
   - `return_reference_sorted_output`

2. 复核边界长度样例（小规模）：
   - `[]`, `[1]`, `[1,2]`, `[1,2,3]`, `[1,2,3,4,5]`
   - 验证 trace count 与 interval/tree 计数一致。

### Completion check

- 现有测试集中已覆盖相关边界与 Trace 关键字段。

## Day 4: Thesis-facing Evidence Pack

### Main output

- `docs/progress/week6_summary.md`（实验解释章节草稿）

### Tasks

1. 抽 6~8 个关键观察点，整理成“论文可复用的结果叙述”：
   - 复杂度/速度结论仅限于本实验范围；
   - `simplified_jordan_reference` 的边界声明保持一致（ordinary-list backend、`uses_oracle_sorted_output=True`）。
2. 列出 “可以讲，不能讲，待推进” 三段式结论。

### Completion check

- week6_summary 能直接被第七周“写作阶段”引用。

## Day 5: Documentation and Index Sync

### Main output

- `README.md`
- `docs/README.md`
- `docs/plan/README.md`
- `docs/progress/week5_progress.md`（收口说明）
- `docs/progress/week6_progress.md`（每日记录）

### Tasks

1. 补齐 Week 6 相关文档索引与链接。
2. 在“当前状态”里移除过时的 Week 4/5 停留文案。
3. 将 `week6_plan.md` 和 `week6_progress.md` 纳入文档清单。

### Completion check

- 文档入口一致，能从 docs/README 找到 week6 计划与进度。

## Day 6: Week 6 Finalization

### Main output

- `docs/progress/week6_summary.md`（含收官结论 + 下一周边界）

### Tasks

1. 形成最终总结（What worked / What still missing / what moved to Week7）。
2. 明确 Week 6 可交付和不承诺的范围。

### Completion check

- 第 6 周任务有明确结论，且无阻塞性问题。

## Day 7: Week 7 Handoff

### Main output

- `docs/progress/week6_summary.md` 的交接段。

### Tasks

1. 写出 Week 7 启动前的不可回退约束：
   - `backend` 与理论边界不混淆；
   - 现有实验口径不变；
   - 先复核再加速优化。

### Completion check

- Week 7 计划可直接从 Week 6 收敛结论延续。
