# Week 5 Plan

Last updated: 2026-06-26

## Week 5 Goal

在 Week 4 的 reference pipeline 基础上，进入“可以论文可复现、可解释、可复查”的第一阶段：

- 稳定实验输出与 trace/统计字段
- 形成第一套简化 reference 的结果汇总与复核流程
- 把实验结果可直接用于论文第 4 章/评估章节的初稿

仍不实现真实线性时间 Jordan 排序，不实现动态树更新算法，不引入新复杂数据结构。

## Non-Goals (重要)

- level-linked search trees
- heterogeneous finger trees
- 完整 split / merge 动态更新引擎
- 复杂可视化流水线
- 直接给出线性时间复杂度证明

## Day 1: Week 5 审核与基线对齐

### Main output

- `docs/progress/week5_notes.md`（建议新建）
- `tests` 全量通过

### Tasks

1. 重新统一“当前状态”文本（README / docs 索引）到 Week 5 起始。
2. 跑全量回归：

   ```bash
   python -m unittest discover -s tests
   ```

3. 重新跑一次实验入口 smoke/参考链路复核：

   ```bash
   python experiments/run_small_tests.py --smoke
   python experiments/run_small_tests.py --week4-reference
   ```

4. 复核 `run_small_tests.py` 输出策略：Week 4 与 Week 1 不混写。

### Completion check

- 全量测试绿灯（当前为 152 tests）。
- Week 4 和 Week 1 输出文件路径策略确认后续不变。

## Day 2: 生成并检查 Week 4 reference 汇总

### Main output

- `results/week4_reference_summary.csv`（按需生成）
- `docs/progress/week5_notes.md`（记录命令和关键指标）

### Tasks

1. 跑 Week 4 参考实验：

   ```bash
   python experiments/run_small_tests.py --week4-reference
   ```

2. 用 `summarize_results.py` 生成聚合摘要：

   ```bash
   python experiments/summarize_results.py \
     --input-csv results/week4_reference_results.csv \
     --output-csv results/week4_reference_summary.csv
   ```

3. 在 notes 里记录：
   - 原始行数是否为 3675
   - `all_correct` 分布是否全真
   - 错误是否为 0

### Completion check

- `results/week4_reference_summary.csv` 能在本地正常生成。
- 结构：`(algorithm, family, n)` 分组聚合行数、统计字段存在。

## Day 3: Trace 可复核性补强

### Main output

- `tests/test_simplified_jordan.py`（如有必要补充 trace 稳定性测试）

### Tasks

1. 固化 trace 条目顺序和关键字段检查（重点保留有效路径）：

   - `build_rank_map`
   - `extract_pair_families`
   - `convert_pairs_to_rank_intervals`
   - `build_family_trees`
   - `structure_profile`
   - `prepare_reference_backend`
   - `extract_rank_order`
   - `return_reference_sorted_output`

2. 补一条“小长度边界 + traces 一致性”测试，防止后续修改打乱 contract。

### Completion check

- valid case 的 trace contract 保持稳定且可被测试锁死。

## Day 4: 结果解读与论文友好文档整理

### Main output

- `docs/design/structural_examples.md`（与 Day 4 实验输出 cross-check）
- `docs/notes.md`（补充一段 `simplified` reference 与真实算法边界说明）

### Tasks

1. 按关键 family 选 1~2 个代表序列，记录：
   - 家族
   - trace snippet
   - family trees（可用 `family_tree_to_debug_lines`）
   - `simplified_jordan_sort` 输出
2. 把这些样例整理成“论文可直接引用文本块”。

### Completion check

- 关键示例可直接映射到实验配置里的可复现对象。

## Day 5: Week 5 文档与脚本约束检查

### Main output

- `docs/plan/week5_plan.md`（作为正式约束）
- `docs/backlog/future_work_todo.md`（如有新超纲想法移入）

### Tasks

1. 清理可选项：把未来工作 ideas 从核心执行文档移到 backlog。
2. 补 `results/README.md` / `docs/README.md` 中 Week 5 产物说明（若仍未更新）。
3. 确认 Week 5 之前“未实现”的事项继续保留在 backlog，不进入任务主线。

### Completion check

- 计划与文档索引一致。

## Day 6: 最终复核（Week 5）

### Main output

- `docs/progress/week5_summary.md`

### Tasks

1. 复核所有 Day1-5 结果是否齐全，尤其是：
   - 全量测试状态
   - Week 4 复现命令
   - summary 文件是否按需可生成
   - trace contract 是否稳定

2. 输出一段“下一周只做什么不做什么”的边界清单。

### Completion check

- Week 5 的可交付清单可支持直接进入下一周实现。

## Day 7: 与 Week 6 交接（可留）

### Main output

- 下一周 Week 6 目标（算法侧调试到可解释性增强）

### Tasks

- 整理 Week 5 经验，写成 Week 6 计划中的“不可回退边界条件”和“最小可交付列表”。

### Completion check

- Week 6 计划可直接从 Week 5 复盘内容续接。
