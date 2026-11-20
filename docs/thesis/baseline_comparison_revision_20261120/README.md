# 通用排序补充比较的论文修订记录

## 单图版（2026 年 11 月 20 日）

按作者反馈，补充比较在整篇论文中只保留图 6.5（正文第 43 页、PDF 第 55 页）。左图按每种方法的首档耗时归一化；右图给出相邻规模档的经验增长指数。耗时倍数和键比较例外写入正文，移去补充比较的表格、键比较图以及附录 C 的绝对耗时图。原始数据、实验报告和主实验图表保留。使用同一档案重新生成矢量图并编译，最终日志通过检查。 [单图版论文](../../../output/pdf/Wang_Thesis_Growth_Comparison_2026-11-20.pdf)

## 初版修订记录

**2026 年 11 月 20 日。** 英文论文以当日工作区中的最新稿为底稿。主实验仍回答两个 Jordan 后端之间的性能问题；新增的五方法会话回答它们与纯 Python 归并排序、快速排序的性能差距。两项实验分别报告。摘要保留两种 Python 基线在全部实测输入上均更快的结论，事后增长分析放在结果章。[初版论文](../../../output/pdf/Wang_Thesis_Baseline_Comparison_2026-11-20.pdf)

## 章节变更

- 引言保留 1990 年论文“提出异构指树实现”的表述，并明确端点插入和分裂的摊还界。期望时间界的例子指明为随机化快排。RQ2 增加对通用排序的比较；CPython 的内置排序作为实用参考。已有的 Cormen、Leiserson、Rivest、Stein《Introduction to Algorithms》第三版书目保留一份，图 2.1 的链接已在成品 PDF 中核对。[出版社书目](https://mitpress.mit.edu/9780262033848/introduction-to-algorithms/)
- 5.7 节说明导师建议、测前登记、302 个输入、冻结源码、三路中间主元快排、独立校准及轮换、输出核验、计时外键比较和事后分析。主实验旧句已限定为内部树操作计数，以区别于本次的输入键比较次数。
- 6.6 节的表 6.5 报告逐输入时间比的中位数与严格胜数。图 6.5 描述固定来源后各档相对增长及相邻档经验指数，图 6.6 描述所有来源按精确长度汇总的每元素比较次数。特别写明指树在 7 个输入上比快排少做键比较却仍耗时更长。6.7 节汇总两项实验。局限章说明测量范围、输入构成、内置 C 实现和操作计数边界；结论补全 RQ2，Further Work 延续原有优化段落。
- 附录 C 开头更新了图的来源说明，C.2 节单列新会话的绝对耗时图 C.2。附录 A、B 的工作区源码与本轮开始时逐字节一致。旧稿同日 PDF 已核对 SHA-256，原文件保留。新版 PDF 包含编译时工作区中已有的第 4 章与附录 A、B 修订；这些此前的本地差异不随本次提交发布。

## 增长复算

每个输入、每种方法先取 20 个正式批次的每调用时间中位数，再取档内输入的中位数。固定组成的每档含 common 28 个、geometric 20 个。五档覆盖 240 个输入，完整输入集含 302 个。下表给出末档中位数与首档中位数之比。第二幅面板用名义规模计算相邻档的经验增长指数。这是测后描述，没有新增测量。[生成脚本](generate.py) · [原始记录](../../validation/baseline_comparison_20261120/raw_records.tar.gz)

| 方法 | common + geometric（32/33 → 512/513） | 全部输入（同档） |
|---|---:|---:|
| 普通列表 | 26.71 | 26.00 |
| 指树 | 17.81 | 18.11 |
| 归并 | 20.36 | 20.41 |
| 快排 | 22.25 | 23.58 |
| 内置排序 | 14.33 | 14.73 |

## 新增宏及档案出处

以下名称均带前缀 `\Baseline`。由仓库根目录运行 `python3 docs/thesis/baseline_comparison_revision_20261120/generate.py`，即可根据原始记录和冻结协议常量重新生成所有宏及当前单图版的增长图。提交的正文引用生成值，协议上限为测前规则，实际选中的 B 由原始校准和正式记录复核。[宏文件](../../../thesis/generated/baseline_comparison.tex)

| 宏名（省略共同前缀） | 值 | 出处与计算 |
|---|---:|---|
| `Inputs` | 302 | 登记清单 suite.json（身份与正式配置核对），按输入、长度及来源计数 |
| `MinLength` | 32 | 登记清单 suite.json（身份与正式配置核对），按输入、长度及来源计数 |
| `MaxLength` | 513 | 登记清单 suite.json（身份与正式配置核对），按输入、长度及来源计数 |
| `Warmups` | 5 | formal/records.jsonl，按阶段、顺位或电源事件计数 |
| `Rounds` | 20 | formal/records.jsonl，按阶段、顺位或电源事件计数 |
| `First` | 4 | formal/records.jsonl，按阶段、顺位或电源事件计数 |
| `Samples` | 30,200 | formal/records.jsonl，按阶段、顺位或电源事件计数 |
| `Power` | 604 | formal/records.jsonl，按阶段、顺位或电源事件计数 |
| `Minutes` | 8 | formal/config.json 和 complete.json 的 UTC 起止时间差，四舍五入到秒 |
| `Seconds` | 41 | formal/config.json 和 complete.json 的 UTC 起止时间差，四舍五入到秒 |
| `CapExponent` | 20 | 测前协议 03e87e1cb、测量代码 0a0dcbd8a（候选上限或选取阈值） |
| `TargetMs` | 10 | 测前协议 03e87e1cb、测量代码 0a0dcbd8a（候选上限或选取阈值） |
| `JordanMaxB` | 32 | preparation/records.jsonl 三批校准中位数及 calibration.json，取两个 Jordan 后端最大选中 B |
| `Common` | 28 | 登记清单 suite.json（身份与正式配置核对），按输入、长度及来源计数 |
| `Geometric` | 20 | 登记清单 suite.json（身份与正式配置核对），按输入、长度及来源计数 |
| `PerBand` | 48 | 登记清单 suite.json（身份与正式配置核对），按输入、长度及来源计数 |
| `Subset` | 240 | 登记清单 suite.json（身份与正式配置核对），按输入、长度及来源计数 |
| `ListLast` | 1.35 | formal/records.jsonl 和 suite.json，档内中位数的首尾比、相邻指数或两种来源口径的最大相对差 |
| `TreeMin` | 1.02 | formal/records.jsonl 和 suite.json，档内中位数的首尾比、相邻指数或两种来源口径的最大相对差 |
| `TreeMax` | 1.06 | formal/records.jsonl 和 suite.json，档内中位数的首尾比、相邻指数或两种来源口径的最大相对差 |
| `TreeFewerQuick` | 7 | preparation/records.jsonl，每个输入逐项合计四种键序关系后配对比较 |
| `TreeMoreQuick` | 295 | preparation/records.jsonl，每个输入逐项合计四种键序关系后配对比较 |
| `MaxSensitivity` | 5.9 | formal/records.jsonl 和 suite.json，档内中位数的首尾比、相邻指数或两种来源口径的最大相对差 |
| `ListMerge` | 51.9 | formal/records.jsonl，逐输入 Jordan / 基线时间比的中位数 |
| `ListMergeWins` | 0 | formal/records.jsonl，逐输入计算配对时间比后统计严格小于 1 的个数 |
| `ListQuick` | 88.7 | formal/records.jsonl，逐输入 Jordan / 基线时间比的中位数 |
| `ListQuickWins` | 0 | formal/records.jsonl，逐输入计算配对时间比后统计严格小于 1 的个数 |
| `TreeMerge` | 63.2 | formal/records.jsonl，逐输入 Jordan / 基线时间比的中位数 |
| `TreeMergeWins` | 0 | formal/records.jsonl，逐输入计算配对时间比后统计严格小于 1 的个数 |
| `TreeQuick` | 110.1 | formal/records.jsonl，逐输入 Jordan / 基线时间比的中位数 |
| `TreeQuickWins` | 0 | formal/records.jsonl，逐输入计算配对时间比后统计严格小于 1 的个数 |
| `ListGrowth` | 26.71 | formal/records.jsonl 和 suite.json，档内中位数的首尾比、相邻指数或两种来源口径的最大相对差 |
| `ListAllGrowth` | 26.00 | formal/records.jsonl 和 suite.json，档内中位数的首尾比、相邻指数或两种来源口径的最大相对差 |
| `TreeGrowth` | 17.81 | formal/records.jsonl 和 suite.json，档内中位数的首尾比、相邻指数或两种来源口径的最大相对差 |
| `TreeAllGrowth` | 18.11 | formal/records.jsonl 和 suite.json，档内中位数的首尾比、相邻指数或两种来源口径的最大相对差 |
| `MergeGrowth` | 20.36 | formal/records.jsonl 和 suite.json，档内中位数的首尾比、相邻指数或两种来源口径的最大相对差 |
| `MergeAllGrowth` | 20.41 | formal/records.jsonl 和 suite.json，档内中位数的首尾比、相邻指数或两种来源口径的最大相对差 |
| `QuickGrowth` | 22.25 | formal/records.jsonl 和 suite.json，档内中位数的首尾比、相邻指数或两种来源口径的最大相对差 |
| `QuickAllGrowth` | 23.58 | formal/records.jsonl 和 suite.json，档内中位数的首尾比、相邻指数或两种来源口径的最大相对差 |
| `BuiltinGrowth` | 14.33 | formal/records.jsonl 和 suite.json，档内中位数的首尾比、相邻指数或两种来源口径的最大相对差 |
| `BuiltinAllGrowth` | 14.73 | formal/records.jsonl 和 suite.json，档内中位数的首尾比、相邻指数或两种来源口径的最大相对差 |

## 引言与背景 2.5.2 的重合

背景章保留原文。以下列出重合的背景句，作者名按正文显示，略去数字引文标记。

- 1990 年简化算法的裁剪应用、纠错版本的三角剖分应用与引言第 3 段重合。“The later simplification connected Jordan sorting to polygon clipping, while the error-correcting task appears in the polygon-triangulation algorithm of Tarjan and Van Wyk.”
- 同段也概述了不相交链的应用。背景多交代了点定位和区间树。“Subsequent work by Bar-Yehuda and Chazelle used a generalized form of Jordan sorting together with point location and interval trees to triangulate collections of disjoint Jordan polygonal chains.”
- 引言第 4 段与 Sojka 的实践动机重合，背景另给出具体的两个理论界。“Sojka instead emphasized simpler algorithms intended to be practical at moderate input sizes, including an O(n log n) worst-case method and an O(n log log n) worst-case method.”
- 理论与实际性能的取舍、本文重建对象，与引言第 4、5 段部分重合。“These alternatives address different trade-offs between structural complexity, worst-case bounds and practical performance.” “The present study focuses on reconstructing the 1990 procedure.”
- 曲线顺序的动机与有效输入范围分别见引言第 3、6 段。“The geometric applications explain why curve order is a useful input format.” “The present thesis studies the valid-input sorting step using the existing heterogeneous finger-tree approach.”
- 引言提到 1986 年期刊版的线性时间结果；背景首句另给出 1985 年会议首发的沿革。“The first symposium publication of the linear-time Jordan-sorting result appeared in 1985; the 1986 journal article used throughout this thesis gives the expanded algorithm and data-structure account.”

## 编译与检查

LuaLaTeX、Biber 和 latexmk 完整编译，成品 88 页。最终日志无警告、未定义引用、overfull 或 underfull box。已核对摘要、引言、方法、结果表、增长图两个面板、比较次数图、局限、结论和附录 C 的版面。正文只讨论补充排序的相对耗时、胜数、增长及键比较；校准门槛和整个会话历时属于方法参数。五种方法的绝对排序耗时图仅出现在附录 C。全稿复核未发现九月进度报告的提法。附录 B 原有的月份使用记录保留。

档案中的代码提交、日期和协议上限属于实验元数据。主实验的宏和结果沿用原值；补充比较的两种输入范围、逐输入配对比值和键比较例外均追溯到同一套补充原始记录。[实验报告与独立复核](../../validation/baseline_comparison_20261120/README.md)
