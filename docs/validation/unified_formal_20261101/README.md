# 统一 302 输入正式尝试与分析档案（2026-11-01）

本目录按原字节保存首次电源失败尝试、作者授权的重启决定、第二次完整正式尝试及其验证与分析输出。**主结果仅来自第二次尝试：302 个唯一输入中树更快 44 个，列表更快 258 个，相等 0 个。** 两次尝试没有拼接或合并统计。

这是分阶段任务的**阶段一：归档**。本阶段没有执行实例创建微基准，没有进行两次尝试的 170 输入比值比较，也没有修改论文。

## 冻结身份、作者确认与重启披露

- 生产和实验代码冻结提交：`bca4c1c6a5480e22c7121987de2c97bb00688264`；两次执行均从干净的 `main` 提交 `2ae92952d1968add2e46b8610a6270fab828f60b` 进行。
- 151 个 Python 源文件的完整身份摘要：`0cd50e8f3db8199a9d4e0804a6e6d648d4d337aa8f58791af6dbe3a328212a82`。完整映射与 19 个生产文件摘要见[前置冻结档案](../unified_preflight_20261101/freeze.json)。本次仅归档文档和证据，不改变冻结代码。
- 作者在聊天中确认已亲自完成第 1–11 项审阅，包括附录 A 的 A.1–A.3 全部引理与定理，并明确授权 Codex 在本机创建 receipt、启动采样。[作者审阅收据](author_unified_review_bca4c1c6.json)保留该确认与实际执行方式，不将 Codex 的技术检查写成作者独立人工证明。
- 首次尝试在 `geometric--geometric-n256-08` 的执行后检查中记录 `Battery Power`；执行前为 `AC Power`，两次低电量模式均为 0。该输入已有 50 条 PASS 批次记录，仍因电源门槛失败被标记 `accepted=false`、`performance_eligible=false`。原始观测不能确定供电改变的具体原因或发生时刻。
- 作者在收到失败诊断后明确要求“重新开始”“继续吧”。[重启决定](unified_formal_bca4c1c6_restart_20261101_01.restart_decision.json)在第二次执行前保存；恢复交流电后，从全部 302 个输入的起点重新执行，输入、B、源码、预算和顺序规则不变。
- **第二次尝试偏离原协议“不重试”的条款，须与首次失败一起披露。** 它不是原定不重试会话的首次完整成功；验证器通过仅确认档案和技术条件，不消除流程偏离。决定重启前没有计算性能比值。

两次运行及分析的历史说明、JSON 与 manifest 均原样保留。旧说明中“尚未分析”“尚未修改论文”等表述是各自生成时的状态，不回写历史文件。

## 两次尝试的完成范围

| 来源 | 首次尝试 | 第二次尝试 |
|---|---|---|
| common | COMPLETE，140 PASS | COMPLETE，140 PASS |
| targeted_split | COMPLETE，12 PASS | COMPLETE，12 PASS |
| structural | COMPLETE，18 PASS | COMPLETE，18 PASS |
| geometric | ERROR，23 PASS、1 ERROR、76 NOT_RUN | COMPLETE，100 PASS |
| seeded | NOT_RUN，32 NOT_RUN | COMPLETE，32 PASS |

首次尝试的完整来源共 170 个输入；其余部分记录保留为失败证据，未进入第二次的主要统计。第二次来源采样时段为 2026-11-01 22:08:31–22:13:47 Europe/Berlin，约 315.36 秒，不包含启动时的前置链验证。这是流程墙钟时间，不是排序性能指标。

环境与[前置档案](../unified_preflight_20261101/README.md)一致：Apple M4、macOS 27.2、CPython 3.12.14、优化级别零、GC 开启且阈值 700/10/10。两次均使用 `caffeinate -i`。程序保存开始及逐输入前后的原始电源观测；检查不等于持续电源监控。

## 第二次尝试的描述性结果

每输入比值为 tree 的 20 个 `elapsed_ns/B` 观测的中位数除以 list 对应中位数。小于 1 表示树更快；判定使用未四舍五入的值。每个输入贡献一个比值，不把批次或批内调用当作额外独立输入。

| 来源 | 实际计时输入 | 树更快 | 比值中位数 | 最小值 | 最大值 |
|---|---:|---:|---:|---:|---:|
| common | 140 | 32 | 1.230987 | 0.590223 | 1.517609 |
| targeted_split | 12 | 0 | 1.352014 | 1.341997 | 1.357443 |
| structural | 18 | 0 | 1.268999 | 1.040820 | 1.358582 |
| geometric | 100 | 5 | 1.302312 | 0.955689 | 1.441070 |
| seeded | 32 | 7 | 1.167471 | 0.891726 | 1.426384 |

全部输入等权的比值中位数为 1.257264，范围为 0.590223–1.517609；这是受来源组成影响的次要描述，不能解释为真实应用分布的总体加速比。只做描述，不做显著性检验、独立样本置信区间或因果解释。40 个输入的 `S_i=0`，`p_i` 保持 NA。

分析直接读取原始批次并独立重建中位数、R7 四分位数/IQR 和比值，与验证器结果核对。每个输入的每个后端都有 20 个正式批次，总计 12,080 个正式批次和 3,020 个预热记录。

- [完整结果说明及四图索引](unified_formal_bca4c1c6_restart_20261101_01.report.md)
- [分析摘要与分层](unified_analysis_bca4c1c6_restart_20261101_01/summary.json)
- [逐输入 CSV](unified_analysis_bca4c1c6_restart_20261101_01/cases.csv)与[完整逐输入统计](unified_analysis_bca4c1c6_restart_20261101_01/cases.json)
- [全部输入总图](unified_analysis_bca4c1c6_restart_20261101_01/overview.pdf)
- [比值随规模](unified_analysis_bca4c1c6_restart_20261101_01/ratio_by_n.pdf)
- [values_for 构造族随 k](unified_analysis_bca4c1c6_restart_20261101_01/values_for_by_k.pdf)
- [比值与双侧 split 占比](unified_analysis_bca4c1c6_restart_20261101_01/ratio_by_split_fraction.pdf)

四张图均保留冻结分析脚本生成的 PNG/PDF 原件。`ratio_by_n` 的部分计数标签重叠，后续论文版另行调整布局，不改原图或数据。

## 文件索引

保留原文件名，使历史报告和摘要映射中的相对引用仍可解析。

| 内容 | 路径 |
|---|---|
| 首次失败的原始请求、批次、电源、状态及 manifest | [unified_formal_bca4c1c6/](unified_formal_bca4c1c6/) |
| 首次失败终端输出 | [console.log](unified_formal_bca4c1c6.console.log) |
| 首次失败诊断 | [diagnosis.md](unified_formal_bca4c1c6.diagnosis.md) |
| 首次独立验证报告 | [validation.json](unified_formal_bca4c1c6.validation.json) |
| 首次 sidecar 摘要 | [evidence_sha256.json](unified_formal_bca4c1c6.evidence_sha256.json) |
| 采样前的作者重启决定 | [restart_decision.json](unified_formal_bca4c1c6_restart_20261101_01.restart_decision.json) |
| 第二次完整原始档案 | [unified_formal_bca4c1c6_restart_20261101_01/](unified_formal_bca4c1c6_restart_20261101_01/) |
| 第二次终端输出与独立验证 | [console.log](unified_formal_bca4c1c6_restart_20261101_01.console.log)、[validation.json](unified_formal_bca4c1c6_restart_20261101_01.validation.json) |
| 第二次分析输出及其原 manifest | [unified_analysis_bca4c1c6_restart_20261101_01/](unified_analysis_bca4c1c6_restart_20261101_01/) |
| 分析命令输出与历史交付摘要 | [console.json](unified_analysis_bca4c1c6_restart_20261101_01.console.json)、[delivery.json](unified_formal_bca4c1c6_restart_20261101_01.delivery.json) |
| 作者审阅收据 | [author_unified_review_bca4c1c6.json](author_unified_review_bca4c1c6.json) |

空的 stderr 日志也一并保留，不删除或重写。

## 原字节迁移与独立复核

本次移动 17 个顶层条目、27,435 个原始文件，共 39,801,471 字节。

- [迁移前逐文件摘要](checks/pre_move_inventory.json)覆盖全部待迁移文件，包括原 manifest 和 sidecar 文件。
- [迁移记录](relocation.json)记录每个原路径、归档路径、类型、文件数、字节数和摘要。
- [字节保存性检查](checks/byte_preservation.json)确认所有原文件内容不变，原路径链接有效，归档内部没有符号链接，151 个 Python 源文件身份不变。
- `checks/before_*_validation.json` 为迁移前重新执行的只读验证，逐项等于原有独立验证报告。
- `checks/archived_*_validation.json` 为迁移后重新执行的只读验证，逐项等于迁移前结果。首次报告 `archive_valid=true, complete=false, hard_error=true`；第二次报告 `archive_valid=true, complete=true, hard_error=false, all_sources_complete=true`。首次档案验证通过不表示首次采样完整成功。
- 原始两份运行 manifest、分析 manifest 和已有 sidecar 摘要均保持原字节，未重封。新增的[归档包摘要](package_manifest.json)仅覆盖本目录除自身之外的文件，不替换这些原 manifest。

## 路径绑定与只读命令

原文件中的绝对路径保持原文。在仓库外的原 `.codex-tmp/` 位置，为迁移的 17 个目录或文件分别保留符号链接，指向本目录中同名的原件。目录内部都是普通文件和目录。前置阶段已有的三个原路径链接继续保留。

不要删除这些链接。迁移机器或仓库位置时，按本目录及前置档案的 `relocation.json` 恢复原路径别名；不要修改配置中的前置路径或重封 manifest。

在本机、冻结源码未变时，从仓库根目录只读复核：

```sh
PYTHONPATH=src:experiments /Users/schnee/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -B experiments/validate_input_suite_run.py \
  docs/validation/unified_formal_20261101/unified_formal_bca4c1c6

PYTHONPATH=src:experiments /Users/schnee/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -B experiments/validate_input_suite_run.py \
  docs/validation/unified_formal_20261101/unified_formal_bca4c1c6_restart_20261101_01
```

这些命令不运行排序或补采样。后续源码若改变，应使用冻结版本，或明确使用 `--historical` 做历史只读审计，不能把旧证据绑定到新实现。

## 后续阶段（本次未执行）

阶段二按作者要求：在同一台机器上预先固定参数，只测插桩树与无插桩树的实例构造，保留环境与原始记录；另对首次尝试三个完整来源的 170 个输入，做两次 tree/list 比值的事后描述性比较。比较不在原协议内、不进入主要统计，不将其视为独立重复或显著性检验。

后续 `results.tex` 修改要求已收到：依次组织整体、随规模、随结构、切分影响和五来源表，统计距 1 不到 2% 的比值，保留四张预定图并另存修复标签的论文版，加一张标为补充图的比值直方图，删除旧插桩结果小节及 15 输入诊断表。涉及嵌套、split 和其他操作的解释须以数据支持的描述为限，不能由完整排序时间识别单次 split 成本或具体因果来源。原始档案和原图继续保留。
