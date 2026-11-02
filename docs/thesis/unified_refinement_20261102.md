# 正文小修订记录：2026 年 11 月 2 日

基线：`a0543049b68926044b95c63cad3a57095bef9c74`。按作者确认的阶段三小修订要求修改正文，完成后提交并 push。未运行新的排序、采样或微基准。

## 本轮修改

1. 摘要第二段采用作者给出的表述，解释计时不含操作计数插桩，补充规模档中位数 1.373 → 1.037；第二段全部数据通过宏引用，删去重跑说明。
2. 引言去除重跑和重复限定；结果 6.2 加入来源内部最大/最小规模的比较，6.5 末尾增加四句 Summary of Observations。
3. 构造微基准补充相对最短树中位排序时间的比例，不把跨设计的数量比较改写为纯绑定成本。
4. 结果章三张图、四个表全部改为 `[htbp]`。物理第 48 页现完整容纳规模表和规模图，原来的大片空白已消除；图形文件和绘图数据未变。
5. 重复限定集中处理。摘要保留作者指定的一句；引言、结果和结论删除相同边界的重复说明。局限章完整解释外推、输入族代表性及单次操作成本，方法章完整保留重跑事实和偏离。详细原句见 [删改句清单](unified_refinement_20261102/removed_qualifications.md)，逐项 before/after 见 [结构化记录](unified_refinement_20261102/sentence_changes.json)。
6. 新增独立的数值生成脚本及宏，不改写 11 月 1 日的生成器、分析记录或图表。同步当前 PDF 导航，保留上一版 PDF。

## 新数字核对

来源：[正式分析 cases.json](../validation/unified_formal_20261101/unified_analysis_bca4c1c6_restart_20261101_01/cases.json)及[构造微基准汇总](../validation/unified_followup_20261101/results/analysis/constructor_summary.json)。精确值、全部规模中位数与原始文件哈希见 [derived.json](unified_refinement_20261102/derived.json) 和 [provenance.json](unified_refinement_20261102/provenance.json)。

| 来源 | 最小 n | 该档中位比值 | 最大 n | 该档中位比值 |
| --- | ---: | ---: | ---: | ---: |
| common | 32 | 1.381192 | 513 | 0.909568 |
| targeted_split | 128 | 1.352067 | 129 | 1.351938 |
| structural | 128 | 1.336676 | 513 | 1.190720 |
| geometric | 32 | 1.370940 | 512 | 1.031554 |
| seeded | 32 | 1.364123 | 513 | 1.031663 |

五个来源的端点比较均成立。targeted 只有 128/129 两档，差异很小；该检查只支持已测端点的陈述，不将来源内部曲线写为处处单调。

- 最短树中位时间来自 `common--n32-nested_heavy_valid-00-mirror`：605462.25 ns，即 605.46225 μs。已从该输入的 20 个正式树 sample 记录重建。
- 构造配对差中位数为 4880.859375 ns。使用未舍入值计算 `100 × 配对差 / 最短树中位时间`，结果为 0.806137686536%，正文显示 **0.81%**。
- 最小/最大规模档中位数从 cases.json 重算，并与上一轮精确统计一致；新增宏位于 `thesis/generated/unified_refinement.tex`。

## 保存性、编译及交付

- 附录 A 和整个附录 B 原字节不变；其 PDF 页面也与上一版逐像素一致。
- 63,100 个基线文件的路径/哈希汇总保持一致，包括源码、实验与审阅档案、旧生成数据、图形和上一版 PDF。
- LuaLaTeX + Biber 完整编译通过，最终日志无警告、未定义引用、缺字及 overfull/underfull box。全书 80 页逐页渲染并与上一版比对，18 个变化页均已目视复查，其余 62 页渲染一致。
- [独立核对结果](unified_refinement_20261102/verification.json)；[构建与页面检查记录](unified_refinement_20261102/build_report.json)。
- 新 PDF：[Wang_Thesis_Refined_Results_2026-11-02.pdf](../../output/pdf/Wang_Thesis_Refined_Results_2026-11-02.pdf)，**80 页**；上一版未覆盖。

## 附录 B 待更新清单

**本稿仍不能发送给导师；先完成附录 B 的事实更新和作者确认。** 本轮按要求不改其中任何文字。

- [ ] B.1 加入统一准备、两次正式尝试、验证与分析、构造微基准和稳定性检查的路径及版本；保留旧档案索引，更新“Current experiments”的指代。
- [ ] B.2 工具表：Claude 使用期间改为 October–November 2026。
- [ ] B.2 Review 行：补入技术/稿件审阅、措辞与实验设计讨论、给 Codex 的修改说明等实际范围；核对输出定位。
- [ ] B.2 示例 1：按实际情况说明 Claude 指出重复限定，Codex 执行修订，并调整署名。
- [ ] B.2 Implementation 行及 B.3 开头的实现归属：等待作者确认字面属实的措辞，不代填。
- [ ] B.2 补充 11 月 1 日记录：作者提出无插桩计时；Claude 参与设计及修改说明；Codex 实现、验证、准备、分析及论文修订；receipt 在作者明确确认审阅完成后按其指示写入。
- [ ] B.3 将旧运行结果表述更新为本次结果；仅更新事实，不替作者增加观点。
- [ ] **新增：B.2 示例 3 的 “The complete table and revised interpretation were incorporated into the results section ...” 与当前稿不符，十五输入诊断表已删除。更新其输出说明和定位。**

## 同日后续更正：来源内部规模观察

按作者指正，6.2 节及结果小结将“每个来源”的表述改为明确列出的四个跨规模档来源：common、structural、geometric、seeded。targeted 只有同一规模档内的 128/129，虽然端点中位数在算术上略低，也不将其用于这条规模下降观察。原表格、图形、统计值和档案均不变。

更正稿：[Wang_Thesis_Refined_Results_2026-11-02_r2.pdf](../../output/pdf/Wang_Thesis_Refined_Results_2026-11-02_r2.pdf)，仍为 **80 页**，旧稿未覆盖。编译无警告；只有物理第 48、51 页发生变化，两页已目视复查，其余 78 页渲染一致。附录 A、B 未改，附录 B 待办及暂不能发送导师的状态仍有效。核对见 [source_scope_correction.json](unified_refinement_20261102/source_scope_correction.json)。
