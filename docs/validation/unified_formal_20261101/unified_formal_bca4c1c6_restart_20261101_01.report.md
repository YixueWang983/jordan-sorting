# 统一 302 输入：第二次正式尝试的验证与分析

本次连续运行完成全部 302 个唯一输入，五个来源均 COMPLETE。正式命令、独立验证和分析程序退出码均为 0。**302 个输入中，树更快 44 个，列表更快 258 个，相等 0 个。** 本文只使用第二次尝试的原始批次，未混入第一次运行的任何时间。

## 执行身份与重启披露

- 冻结提交：bca4c1c6a5480e22c7121987de2c97bb00688264；执行 checkout：main 2ae92952d1968add2e46b8610a6270fab828f60b。
- 完整 151 个 Python 源文件摘要：0cd50e8f3db8199a9d4e0804a6e6d648d4d337aa8f58791af6dbe3a328212a82。运行后再次核对一致，工作区仍干净。
- 作者已在聊天中确认完成第 1–11 项本人审阅，授权创建 receipt 并执行采样。随后在第一次失败诊断后明确要求“重新开始”“继续吧”。
- 第一次会话在 geometric--geometric-n256-08 的执行后检查中记录 Battery Power，因电源门槛失败停止；前三来源共 170 个输入完整完成。原始失败档案、终端输出和诊断均保留，10,785 个档案文件及其 sidecar 摘要逐一核对未变。
- **本次是电源恢复后作者授权的第二次尝试，偏离原先“不重试”的条款。** 重启决定在第二次采样前保存，报告时须与首次失败一起披露；不能称作原定不重试会话的首次完整成功。
- 全部五个来源从头运行，无续跑、拼接、补选输入、改 B 或改预算。决定重启前没有计算性能比值。
- 来源采样时段（Europe/Berlin）：2026-11-01 22:08:31–2026-11-01 22:13:47，约 315.360 秒；不含启动时的准备链验证。
- 本次技术验证：archive_valid=true，complete=true，all_sources_complete=true，hard_error=false。技术验证并不抹去上述流程偏离。

## 描述性结果

比值为每输入 tree 的 20 个 elapsed_ns/B 观测的中位数，除以 list 对应中位数；比值小于 1 表示树更快。更快/相等的判断使用未经四舍五入的比值。

| 来源 | 实际计时数 | 树更快 | 列表更快 | 比值中位数 | 比值范围 |
|---|---:|---:|---:|---:|---|
| common | 140 | 32 | 108 | 1.230987 | 0.590223–1.517609 |
| targeted_split | 12 | 0 | 12 | 1.352014 | 1.341997–1.357443 |
| structural | 18 | 0 | 18 | 1.268999 | 1.040820–1.358582 |
| geometric | 100 | 5 | 95 | 1.302312 | 0.955689–1.441070 |
| seeded | 32 | 7 | 25 | 1.167471 | 0.891726–1.426384 |

所有输入等权的比值中位数为 1.257264，范围为 0.590223–1.517609。这是受来源组成影响的次要描述性汇总，不代表真实应用分布的总体加速比。每个输入贡献一个比值；批内调用和 20 个批次不作为额外独立输入。

common 中 nested_heavy_valid 为 24/40 个树更快，medium_nesting_valid 为 8/40 个；其余 common 类别没有树更快输入。targeted_split 与 structural 的全部输入均为列表更快。这些仅描述固定构造集，不作显著性检验、独立样本置信区间、因果解释或复杂度证明。

## 校验与图表

分析直接重读原始记录，独立重算中位数、R7 四分位数/IQR 和 tree/list 比值，并与验证器结果核对。302 个输入的两个后端均保留 20 个正式批次，共 12,080 个正式批次记录；另外每后端每输入 5 次预热，共 3,020 个预热记录。40 个输入的 S=0，p 保持 NA。分析输出的 16 个文件均通过 manifest 摘要核对。

四张图均提供 PNG/PDF，已目视检查：

1. [全部输入总图](unified_analysis_bca4c1c6_restart_20261101_01/overview.png)（[PDF](unified_analysis_bca4c1c6_restart_20261101_01/overview.pdf)）。
2. [比值随 n](unified_analysis_bca4c1c6_restart_20261101_01/ratio_by_n.png)（[PDF](unified_analysis_bca4c1c6_restart_20261101_01/ratio_by_n.pdf)）。原脚本中相邻 n 和来源的样本数标注有局部重叠，论文排版时应另做标签布局优化；这里保留冻结脚本原始输出。
3. [values_for 构造族中比值随 k](unified_analysis_bca4c1c6_restart_20261101_01/values_for_by_k.png)（[PDF](unified_analysis_bca4c1c6_restart_20261101_01/values_for_by_k.pdf)）。repeated 不纳入此图。
4. [比值与双侧 split 占比](unified_analysis_bca4c1c6_restart_20261101_01/ratio_by_split_fraction.png)（[PDF](unified_analysis_bca4c1c6_restart_20261101_01/ratio_by_split_fraction.pdf)）。40 个 p=NA 输入不放入横轴，但保留在数据表中。

## 证据索引

- [本次原始档案](unified_formal_bca4c1c6_restart_20261101_01/)
- [本次终端日志](unified_formal_bca4c1c6_restart_20261101_01.console.log)
- [本次独立验证报告](unified_formal_bca4c1c6_restart_20261101_01.validation.json)
- [采样前重启决定](unified_formal_bca4c1c6_restart_20261101_01.restart_decision.json)
- [分析摘要](unified_analysis_bca4c1c6_restart_20261101_01/summary.json)
- [逐输入 CSV](unified_analysis_bca4c1c6_restart_20261101_01/cases.csv)
- [逐输入完整统计](unified_analysis_bca4c1c6_restart_20261101_01/cases.json)
- [首次失败诊断](unified_formal_bca4c1c6.diagnosis.md)
- [首次失败原始档案](unified_formal_bca4c1c6/)
- [作者审阅 receipt](author_unified_review_bca4c1c6.json)

本次完成执行、验证和分析。论文源文件尚未修改；后续写入论文时需同时交代重启偏离，并保留既有档案和 PDF。
