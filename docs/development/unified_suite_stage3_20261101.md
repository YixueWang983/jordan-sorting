# 统一实验工具阶段三：待审阅实现

日期：2026 年 11 月 1 日。阶段二已单独提交并推送为
`b599c67fffa880fe70747d8be1c6ca7ef314185e`，提交信息为
`Register unified 302-input suite and verify against source archives`。

本阶段接入统一执行、原始记录验证与分析，更新作者清单；**尚未提交阶段三**。
没有启动统一清单上的等价性、qualification、校准或正式 campaign，没有创建作者 receipt。
测试中的微型输入、合成时长和临时收据桩仅用于工具测试，不是资格或性能证据。

## 执行与状态

统一入口 `experiments/run_input_suite.py` 提供 `equivalence`、`qualification`、
`calibration`、`formal` 四个阶段，`--source all` 或单个原来源名。
每次调用写入新的不可覆盖目录；前置目录可传多个单来源档案，同一来源的重复尝试被拒绝。
各阶段引用的前置链必须一致，不能把另一轮等价性记录与已有 qualification 混用。

来源顺序固定为 common、targeted_split、structural、geometric、seeded。
后端固定为 ordinary_list 与 heterogeneous_finger_uninstrumented；等价性阶段另对照插桩树，
包括既有 trace、每个完成前缀的输出/状态/审计、fresh minimal 和固定 targeted 的详细计数对照。

预算严格沿用追加协议：

| 阶段 | 每输入 | 每来源或整轮 |
|---|---:|---:|
| 等价性 | 600 秒 | 整轮 7200 秒 |
| qualification | 180 秒 | 每来源 1800 秒 |
| 校准 | 来源剩余预算 | 每来源 600 秒 |
| 正式 | 120 秒 | 每来源 1800 秒 |

新 targeted qualification 为 1800 秒 campaign，测试明确对照旧身份中的 180 秒。
各来源预算不共享。资源观测用于限定作业与调度，不能作为后端排序时间。

qualification/校准资源超时令整个来源 INCOMPLETE，来源内后续输入 NOT_RUN，其他来源继续。
截止点为 2026-11-14 23:00 UTC，即 11 月 15 日 00:00 Berlin。
未满足截止或前置条件的来源不进入正式采样。无可用来源时正式入口不创建输出目录。
正确性、trace、workload、源码或环境错误停止后续执行；未找到公共 B 也按错误处理。
等价性资源失败不能作为后续阶段的前置档案；等价性失败或正式采样失败停止后续来源，不把失败来源的部分时间纳入完整来源结果。

逐输入请求、状态、资源额度、时间戳与来源区间保存为原始记录；状态由验证器重建。
来源最终预算检查覆盖逐作业核对等调度工作。所有阶段检查 AC/低功耗、机器/Python、GC、
完整源码与前置环境；正式阶段检查作者已有 receipt。没有 receipt 时拒绝正式启动。

正式 `--source all` 是预定的一次连续会话；单来源接口保留，但分析只接受一个正式会话，
不能拼接多个单来源正式目录。原数值规则、公共 B 选择、预热、配对轮数、交替顺序、
洗牌种子及 fresh minimal 测量核心全部复用。

## 独立验证与分析

`validate_input_suite_run.py` 不导入运行入口，也不解析运行程序的 summary 内容。
它从固定注册清单、原始请求/记录、前置 manifest、Git 源码对象、环境、时间戳及实际输出，
独立重建输入身份、请求顺序、B、完整状态和每后端统计量。
worker 遗留的 summary 文件只作为普通文件检查其字节摘要，不用作统计依据。
测试把 summary 改成非 JSON 仍能重建相同结果；改动原始 batch 轮次则被拒绝。

`analyze_input_suite.py` 再次从二十个 elapsed_ns/B 重算中位数、R7 四分位数、IQR 与比值，
与验证器结果比较。资格结构只取完整通过输入的 primary checked trace，核对两后端一致后
仅累计一份：S_i、I_i、逐次较小侧、完整频数分布、p_i；S=0 时 p 为 NA。
部分来源的结构分母与实际计时分母分别保留，资格中断输入另存状态。

输出包括整体计数与次要比值摘要、五来源分层、common 类别、structural shape、
规范归属映射、资格/正式执行状态、每输入 JSON/CSV，以及四张 PNG/PDF 图：

1. 全输入总图，按来源着色；登记、规范、实测数标在图中，编号顺序另存 `overview_order.json`。
2. 比值随 n 的变化，每输入点和同来源同 n 的中位线，标注数量。
3. values_for 的比值随 k 变化，按 n 分面、shape/镜像区分；repeated 不入此图。
4. 比值对 p_i 的散点图，另计 S=0 不落在横轴上的输入。

全部只做描述，不做显著性检验、因果结论或独立样本推断。完整来源可在未完成会话中
报告，但输出明确标明会话未完成/错误及各来源状态。绘图需要 matplotlib；本机测试版本
为 3.11.2。合成数据的四张图均已生成，另检查了总图与 k 图的布局。

## 文件变更

新增 Python 文件：

- `experiments/input_suite_protocol.py`：固定阶段、预算、前置链、workload 与请求适配。
- `experiments/input_suite_worker.py`：四阶段逐输入 worker，复用现有排序与测量实现。
- `experiments/run_input_suite.py`：来源调度、资源边界、不可覆盖输出与失败保留。
- `experiments/validate_input_suite_run.py`：原始记录与前置链独立重建。
- `experiments/analyze_input_suite.py`：描述统计、分层、结构、数据导出与四图。
- `tests/test_input_suite_pipeline.py`：23 项受控测试，微型输入和合成时长。

修改的既有文件：

- `experiments/qualify_common_inputs_v2.py`：增加可选 on_start 回调，在新 worker 中先保存电源证据；原调用默认行为不变。
- `experiments/validate_matched_measurement.py`：允许新验证器跳过 worker summary，增加显式历史只读模式；历史源码与档案记录的生产提交比较，仍验证 Git blob。
- `experiments/validate_uninstrumented_equivalence.py`：增加显式历史只读检查；`--historical` 必须配合 `--check`。
- `docs/thesis/uninstrumented_author_review_20261101.md`：改为统一 302 输入清单、新执行命令、前置重做及作者审阅项目。

新增文档与工具检查记录：

- 本说明。
- [候选源码清单](unified_suite_stage3_source_20261101.json)。
- [全量测试日志](unified_suite_stage3_checks_20261101/tests.log)。
- [旧档案复核](unified_suite_stage3_checks_20261101/legacy_validation.json)。
- [十五输入诊断复核](unified_suite_stage3_checks_20261101/diagnostic_validation.json)。
- [原字节保存性检查](unified_suite_stage3_checks_20261101/preservation.json)。

## 验证结果

最终全量测试：**856 项全部通过**，其中阶段三新增 23 项。最终日志见上方链接。

命令：

```sh
PYTHONPATH=src:experiments:tests /Users/schnee/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -B -m unittest discover -s tests
```

新增 23 项测试涵盖端到端阶段适配、1800 秒 targeted 预算、来源内/跨来源超时状态、
正确性错误停止、找不到 B、正式失败只汇总先前完整来源、截止点、旧 schema 拒绝、
环境/收据门槛、混用前置尝试拒绝、summary 不依赖、raw tamper 拒绝、空结构及四图。
初次全量 849 项通过；补充前置链、历史验证及等价性失败拦截后，最终全量 856 项通过。
中间一次定向测试命令误写了不存在的模块名 `test_uninstrumented_tools`，该命令失败；
其余 37 项通过。最终使用完整 discovery，覆盖实际存在的全部测试模块。

旧档案只读检查全部通过：插桩 common 140、targeted 12、structural 18 的正式档案及其
资格/校准链；旧无插桩 common 140、targeted 12 的资格/校准；旧等价性 192 输入、
每配置 50,626 个完成前缀及 192 份旧 trace。
显式 historical 模式逐项验证记录中的生产提交与所有源码 blob，不改写档案身份。

十五输入诊断与四十输入 seeded supplement 使用原 `check_local_supplement.py`：
在临时目录放置其协议绑定的 `19a553fb` 源码，并使用检查脚本入库时 `2da8b662` 的论文表格，
只读挂接原档案。原检查脚本未改；900 个旧 batch、11,700 个旧计时输出、40 个 stress 输入
均核对通过。它们保留诊断/历史身份，未运行排序、未补采样，临时目录已删除。

对开始本阶段前保存的 24,084 个文件逐项比较 SHA-256，全部原字节不变，包括
`src/`、已有验证档案、results、论文与输出。`src/` 的 19 个文件完全未改。
`git diff --check` 通过。

## 待冻结对象与停止点

最终要冻结的是以 `b599c67fffa880fe70747d8be1c6ca7ef314185e` 为基础、包含上述阶段三
工具和测试的下一份提交。当前阶段三尚未提交，不能把阶段二提交当作最终执行版本。

当前完整 Python 源码身份包含 151 个文件，摘要为：

`0cd50e8f3db8199a9d4e0804a6e6d648d4d337aa8f58791af6dbe3a328212a82`

对应清单身份仍为：

`a8c2fe3aa2fe4b45bbe876db9e9dabe3b7f95fd666b3c3afab0776bef67234b7`

审阅后如有代码更改，源码摘要和测试结论需相应更新；提交后再确定实际 Git 提交号。
旧资格/B 表不能沿用。当前停止在阶段三交付；下一步的版本冻结与实际前置运行尚未开始。
