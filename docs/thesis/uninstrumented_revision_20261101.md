# 无插桩树重跑：实现与采样前准备记录

执行日期：1 November 2026。本轮基线为 `0362173f`。依据作者提供的
`codex_uninstrumented_rerun_20261101.md`，本轮先完成实现、验证和校准，
正式采样待作者完成指定的本人审阅和执行步骤。

## 已落实的修改

1. **预登记。** 单独提交 `docs/plan/uninstrumented_rerun_protocol_20261101.md`
   （`4aaf0022603e1abd9550b956c51da98ae89c29cf`），时间早于本轮校准。
   保留原 140 common、12 targeted split 输入、种子、B 阶梯、重复次数、
   配对顺序和统计定义。十八输入的结构补充实验保留为旧插桩配置的独立档案。
2. **同源生成。** 新增 `src/uninstrumented_finger.py`，从原规范源码的 AST
   生成普通记录类和方法，不另写一份算法。构造器与类型检查使用同一私有类族，
   解决 slots 和 isinstance 问题。移除纯计数语句、observed/phase 包装与
   ledger 参数；未知计数访问或会丢失算法副作用的投影直接拒绝生成。
3. **配置隔离。** 默认 `instrumented=True`，旧后端元组、schema 和默认
   identity 保持原样。新标签为 `heterogeneous_finger_uninstrumented`；
   `instrumented=False, detailed_work=True` 明确报错。无插桩配置仍使用原
   公开后端类型，实例方法在构造时绑定；每次实例初始化成本仍在计时内。
4. **运行工具。** 资格检查、计时和独立验证器增加单独的无插桩配置，拒绝把
   旧配置的 qualification 或 calibration 当成新配置使用。实验启动及每个
   输入前后检查并记录 AC Power 和 lowpowermode 0；环境门槛不符则停止。
5. **等价性。** 新增固定 192 输入的 checked/minimal 对照。比较各完成前缀
   状态、输出和完整 trace，同时检查默认插桩 trace 与旧档案一致；固定一例
   再开启详细计数对照。保留原始记录及独立复核结果。这些是有限测试证据，
   不能替代一般等价性、正确性或复杂度证明。
6. **正式执行和分析入口。** 作者入口按 common、targeted_split 顺序运行，
   失败后停止；只读取已有的本人审阅收据，不创建 approval。分析工具从全部
   原始记录独立重建中位数、R7 四分位数和比值，与验证器结果核对。

实现与实验工具提交：`3bfc839fae8da3061938f48f490e936deb0c002e`。

## 验证与保存性结果

- 全量 824 项测试通过，用时 185.306 秒。
- 192 输入等价性验证及独立档案复核通过；每种配置覆盖 50,626 个完成前缀。
- common 140/140、targeted split 12/12 均通过资格检查和独立复核。
- 校准 152/152 均通过；common 的 B 分布为 1:24、2:13、4:27、8:28、16:26、32:22；targeted 全部为 B=8。
- 所有资格检查与校准使用完全相同的绑定源码；电源记录均为 AC Power、lowpowermode 0。预登记提交与首次校准的时间顺序已记录在 [预检档案](../validation/uninstrumented_preflight_20261101/README.md)。
- 旧档案和 PDF 的 18,106 个文件 SHA-256 全部一致，附录 A 完全未改。

证据目录：

- [等价性与测试](../validation/uninstrumented_equivalence_20261101/README.md)
- [资格检查与校准](../validation/uninstrumented_preflight_20261101/README.md)

## 需要作者完成的下一步

作者提供的修改说明第 6.2 节明确要求：“这份 receipt 必须由作者本人确认后
创建，Codex 不得代填。”第 6 节还规定正式采样由作者本人在 Mac 上执行。
因此本轮没有创建获批收据，也没有启动真实正式采样。具体证据、核对项目、
收据格式和连续执行命令见 [作者审阅和执行清单](uninstrumented_author_review_20261101.md)。

正式档案完成并独立复核后，才能依次完成：

- 从原始记录生成新结果和图表；新旧实验分别报告，不把跨 session 差异直接
  当作插桩成本的因果估计。
- 更新摘要、引言、实现、方法、结果、局限和结论，补充 B.1 来源与 B.2 实际
  AI 参与范围；附录 A 的证明不改。
- 完整编译并逐页检查新 PDF，使用实际生成日期和新文件名，保留全部旧 PDF。

当前论文源文件和旧 PDF 保持本轮开始时的内容，没有填入估计的新结果。
