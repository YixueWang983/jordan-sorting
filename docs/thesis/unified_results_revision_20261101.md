# 统一正式结果：论文修订记录

执行日期：2026 年 11 月 1 日（Europe/Berlin）。本轮属于阶段三，仅修改论文、生成论文图表和复核已有记录；没有重新采样，也没有提交或 push。工作基线为 `7006629fa93a43001ce32c73f9446be90ba15ba8`。

## 已落实的修改

1. **结果顺序。** 主结果改为完整第二次会话的 302 个输入，依次报告整体、规模、结构、切分和五个来源。删除旧插桩结果小节及十五输入诊断表，清理其引用。整体首先报告树更快的计数，混合来源的中位数只作为辅助描述。
2. **图表安排。** 正文保留三张图：新增的补充直方图、规模图、合并为两个面板的 k/p 图。预定的全部输入总览放入新附录 C。因此四张预定图的内容全部保留，另增加一张直方图。规模图使用独立计数面板解决标签重叠；总览按论文尺寸重新排版，顺序和观测值不变。原始归档图均未覆盖。
3. **结构解释。** 加入 common 四类和 structural 三种 shape 的分层表。重嵌套的 40 个输入中 24 个树更快，每个输入至多一次 split，其中 20 个完全没有 split。只据此说明优势不需要频繁切分；有一次 split 的输入不把全部差异归给其他操作。操作计数不解释各操作的耗时份额。
4. **方法与偏离。** 写明五个来源、同源 AST 生成、准备在计时外而实例构造在计时内、环境、固定预算、配对顺序、汇总定义和档案位置。明确第一次因电源检查失败停止，作者在比值计算前批准重启；这是对“不重试”规则的偏离，两次不混合。170 输入稳定性检查仅作事后补充，不进入主要统计。
5. **构造微基准。** 报告同机固定设计的实测构造时间和配对差值，不将其称为纯方法绑定成本，也不从排序时间扣除。较早插桩结果和诊断仅保留在 Configuration choice 段，数字回读旧档案。
6. **摘要、引言、局限与结论。** 改用新计数和比值，限定在已测输入、规模与主机。删除未经证据支持的“每层 sibling list 都是 singleton”、插桩解释全部差距、调度造成离群等断言；CPU affinity 和实际调度只按运行记录陈述。未来工作中的操作计数用于描述工作组成及指导进一步测量，不称其可以直接分解运行时间。
7. **参考文献判断。** 核对 Di Francesco 等人的 [Meanders: exact asymptotics](https://arxiv.org/abs/cond-mat/9910453) 后，没有把其渐近公式的猜想及 meander 问题直接当作所有有效 Jordan 输入的计数结论。省去该句和引用，原 bibliography.bib 保持不变。
8. **作者暂缓的第 7 项。** 附录 B 的内容、日期、贡献归属和反思更新均未执行。仅把已删除的 `tab:results-hooks` 引用改为现有旧档案索引；其余 B.1/B.2/B.3 保留原文。因此附录 B 尚不是本轮新实验的完整来源与工具参与索引，待作者另行审阅处理。新档案路径暂在方法章明确列出。

## 数字的来源与重建

所有比值使用未舍入值判断更快与否，显示时才舍入。新统计均从下列归档读取；表格、宏和图由 [generate.py](unified_results_20261101/generate.py) 生成，未导入或执行排序器。

| 代号 | 原始或归档来源 |
| --- | --- |
| C | [第二次正式分析 cases.json](../validation/unified_formal_20261101/unified_analysis_bca4c1c6_restart_20261101_01/cases.json) |
| S | [第二次正式分析 summary.json](../validation/unified_formal_20261101/unified_analysis_bca4c1c6_restart_20261101_01/summary.json) |
| Q | [qualification 结构记录](../validation/unified_formal_20261101/unified_analysis_bca4c1c6_restart_20261101_01/qualified_structure.json) |
| R | [第二次正式运行目录](../validation/unified_formal_20261101/unified_formal_bca4c1c6_restart_20261101_01/)：config.json、environment.json、manifest.json，以及 sources/*/jobs/*/records/*.json.gz |
| U | [统一输入清单 suite.json](../validation/input_suite_registry_20261101/suite.json) |
| M | [构造微基准汇总](../validation/unified_followup_20261101/results/analysis/constructor_summary.json)及[事先固定的参数](../validation/unified_followup_20261101/protocol.json) |
| T | [两次尝试的稳定性汇总](../validation/unified_followup_20261101/results/analysis/stability_summary.json) |
| O | [较早 common 正式档案](../validation/final_review_formal_20261015/formal_common/jobs/)各输入 summary.json |
| D | [较早十五输入诊断独立复核](../validation/thesis_review_round2_20261020/local_supplement_recheck.json) |
| H | [跨主机诊断来源绑定](unified_results_20261101/cross_host_provenance.json)：保存可解析的 Git 版本、文件哈希、10 个输入的计数和完成时间；只读该分支，没有合并 |

| 正文或表中的数字 | 出处与计算 |
| --- | --- |
| 302、44、258、0 个精确平局；中位比值 1.257，范围 0.590–1.518 | C 的 ratio；S.overall；宏由精确值生成。摘要、引言、结果和结论共用同一组宏 |
| 比值距 1 不到 2% 的 14 个输入 | C 上 `abs(ratio - 1) < .02`；完整 ID 在 derived.json。2% 是事后描述性区间，并非等价性检验 |
| 五个规模档的输入数、更快数、中位数、范围 | C 按 n 分组；完整精确值在 derived.json.size_bins，显示值自动生成至 unified_sizes.tex |
| 五个来源的登记、重复、canonical、qualification、计时、更快数、中位数和范围 | U、S.per_source、C；输入数依次为 140/12/18/100/32，各来源重复数为 0 |
| common 四类、structural 三种 shape 的全部表格数字 | S.strata，并从 C 核对；split 总数使用每输入一个 qualification 主 trace，未累计第二后端、peer 或 replay |
| heavy 的 40、24、20，以及 S_i≤1；没有双侧 split | C 按 nested_heavy_valid 筛选，核对 S.strata.common；Q 提供结构记录 |
| S_i、I_i、p_i；40 个 p_i=NA；附录 C 的 S/I/N_I/N_0、较小侧 min/median/max、完整频数 | C、Q、S.per_source.*.structure；S_i=0 时 p_i=NA。较小侧单位为 sibling-list pair entries，事件不是独立运行样本 |
| 几何输入较小侧最大 17；最大规模 513；预先排除 8 个 n=1500 | C/Q 的事件列表；U 的 canonical 输入与 exclusions |
| 相对 IQR：list 中位 0.965%、最大 2.601%；tree 中位 0.942%、最大 3.080% | C 各 backend 的 IQR/median ×100；精确值保存在 derived.json.variability_percent |
| 12080 个正式批次、102080 次批内排序调用 | 逐条读取 R 中正式 sample 记录，累加批次数与 B；不包括 warm-up。重建每个输入/后端中位数并与 C 对照 |
| 5 次 warm-up、20 个测量批次、每后端 10 次先执行、顺序种子 20261015 | R/config.json 与既定配对调度规则；总批次数与原始记录交叉核对 |
| B 阶梯 1–128；每值每后端 3 批；10 ms 门槛；180/1800、600、120/1800 秒预算 | [追加协议](../plan/uninstrumented_rerun_addendum_20261101.md)、[基础协议](../plan/uninstrumented_rerun_protocol_20261101.md)及准备/正式阶段 config.json；属于事先参数，不是新增测量 |
| 0.420/5.304 μs 构造中位数、4.881 μs 配对差中位数；5/50 对、每批 256 个保留实例 | M，ns 换算 μs；差值为配对差的中位数，不以两组中位数之差替代 |
| 170 个重合输入、170 个更快方向相同、变化中位 0.426%、最大 1.984% | T，指标为 `100*abs(r_second/r_first - 1)`；事后补充，不进入主要统计 |
| Apple M4/arm64、10 逻辑 CPU、16 GiB、macOS 27.2、CPython 3.12.14、optimize=0、GC 700/10/10、AC/low-power=0 | R/environment.json 的执行环境与逐输入电源记录；不推断具体核心调度 |
| 较早 140 个输入全部树慢、中位 2.898；十五输入诊断降幅 37.7–52.1% | O 各输入 ratio 的中位数；D 复核记录。仅描述各自范围，不把跨会话差值作因果分解 |
| 正式采样前 10 输入跨主机诊断 | H，完成时间早于正式采样；不引用其时间进入本轮统计 |
| 几何仅偶数规模、targeted 的 n=128/129 与 k=3/7/19、structural 六个规模、seeded 七个规模 | U 和各输入元数据；来源生成方式同时对照对应生成器源码，只读、不运行 |
| 直方图宽度 0.05；规模图每来源/精确 n 的计数与中位数 | 前者为事后展示参数，20 个箱的计数共 302；后者直接汇总 C。所有图点、箱边和计数保存在 derived.json.graph_inputs/histogram |

[derived.json](unified_results_20261101/derived.json)保存未舍入统计及全部图形输入；[provenance.json](unified_results_20261101/provenance.json)保存输入文件哈希、原始记录摘要和生成脚本哈希。相关构造、镜像与批内调用均不作为新增独立样本；本轮没有显著性检验、置信区间或因果拟合。

## 文件范围

- 章节：`thesis/frontmatter/abstract.tex`；`thesis/chapters/` 下的 introduction、implementation、methodology、results、limitations、conclusion。implementation 仅同步配置和历史证据范围，避免与新方法章矛盾。
- 组装与日期：`thesis/main.tex`、`thesis/config/metadata.tex`。
- 附录：新建 `thesis/appendix/supplementary_results.tex`；ai_documentation.tex 仅修复失效表引用。backend_argument.tex、claim_traceability.tex、ai_reflection.tex 均原字节不变。
- 图：更新 current_experiment_pipeline 的源文件和 PDF；新增 unified_distribution.pdf、unified_ratio_by_n.pdf、unified_split_panels.pdf、unified_overview.pdf。
- 生成数值：`thesis/generated/` 下统一宏文件及六份表格行宏。
- 本轮记录：本文件，以及 `docs/thesis/unified_results_20261101/` 下的生成/验证脚本、精确统计、来源、验证结果与编译记录。
- 新审阅 PDF：见下方交付信息。已有 PDF 均保留，没有覆盖。

## 验证与交付

[verification.json](unified_results_20261101/verification.json)记录全部检查通过：

- 三个归档的 39,787 个文件逐字节哈希与原清单一致；原图未修改。
- 151 个 Python 源文件、15 份已有 PDF、附录 A/B.1/B.3 和书目共 170 个受保护文件与基线一致。
- 附录 A 整个文件 SHA-256 为 `dc621f87b09366239c6b5495affe0c0ac44a843692a64dda599c12e454d7782c`；公式、定义、引理及证明环境因此全都原样保留。
- 所有引用目标存在；没有重复 label；已移除旧诊断表引用；正文用语及哈希位置检查通过。
- LuaLaTeX + Biber 完整构建及逐页图像检查结果见 [build_report.json](unified_results_20261101/build_report.json)。临时编译器在仓库外，不修改系统 TeX 配置。所有 TeX 生成文件留在忽略的 build 子目录。

最终 PDF 页数、名称、哈希以及实际检查页码由构建记录给出。作者审阅前保持未提交状态；附录 B 第 7 项仍待处理。

交付文件：[Wang_Thesis_Unified_Results_2026-11-01.pdf](../../output/pdf/Wang_Thesis_Unified_Results_2026-11-01.pdf)，共 **80 页**。最终 LuaLaTeX 与 Biber 日志均无警告、未定义引用及 overfull/underfull box。
