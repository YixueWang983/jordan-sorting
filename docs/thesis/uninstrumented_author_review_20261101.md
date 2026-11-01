# 作者本人审阅与统一正式采样清单

更新：2026 年 11 月 1 日，统一前置阶段已完成。本文是作者审阅清单，不是获批收据。
**全部 302 个输入的等价性验证、qualification 和校准均已完成并独立验证通过；正式采样尚未开始，未创建 receipt。**

## 最终冻结版本与证据

- 最终冻结提交：`bca4c1c6a5480e22c7121987de2c97bb00688264`（阶段三）。三个前置阶段均在该提交的干净工作区上串行执行，期间未改代码，也未并行测试、编译或其他实验。
- 完整 Python 源码摘要：`0cd50e8f3db8199a9d4e0804a6e6d648d4d337aa8f58791af6dbe3a328212a82`，绑定 src、experiments、tests 中的 151 个文件，见[完整冻结清单](../validation/unified_preflight_20261101/freeze.json)。
- [生产源码 SHA-256 清单](../validation/unified_preflight_20261101/production_sha256.json)包含全部 19 个 `src/` 文件。生产代码未改，实例创建仍包含逐个绑定生成方法的现有实现。
- [统一前置档案](../validation/unified_preflight_20261101/README.md)已提交并推送：`d0d47a67`。归档与本清单的提交不改变上述冻结源码。
- [原协议](../plan/uninstrumented_rerun_protocol_20261101.md)及[追加协议](../plan/uninstrumented_rerun_addendum_20261101.md)继续适用，追加协议提交为 `afbbff68525b112ad9bc03c163b435ca74590212`。此前考虑的构造方式修改已取消，没有实施 R1 修订。
- [统一输入清单](../validation/input_suite_registry_20261101/suite.json)身份为 `a8c2fe3aa2fe4b45bbe876db9e9dabe3b7f95fd666b3c3afab0776bef67234b7`：302 个条目、302 个规范输入，重复数为零；8 个 n=1500 的 seeded 条目仍排除。
- [阶段三测试记录](../development/unified_suite_stage3_checks_20261101/tests.log)为 856 项通过。此次前置运行期间没有重跑测试；有限输入一致性和测试通过不代替一般证明。

## 本轮来源完成状态

| 来源 | 输入数 | 等价性 | qualification | 校准 |
|---|---:|---|---|---|
| common | 140 | COMPLETE，140/140 | COMPLETE，140/140 | COMPLETE，140/140 |
| targeted_split | 12 | COMPLETE，12/12 | COMPLETE，12/12 | COMPLETE，12/12 |
| structural | 18 | COMPLETE，18/18 | COMPLETE，18/18 | COMPLETE，18/18 |
| geometric | 100 | COMPLETE，100/100 | COMPLETE，100/100 | COMPLETE，100/100 |
| seeded | 32 | COMPLETE，32/32 | COMPLETE，32/32 | COMPLETE，32/32 |

本轮没有资源超时、非资源类错误或 INCOMPLETE 来源。
三阶段均在 2026 年 11 月 1 日完成，早于 11 月 15 日 00:00 Berlin 的截止点，详见[时序记录](../validation/unified_preflight_20261101/chronology.json)。

[逐输入公共 B 表](../validation/unified_preflight_20261101/batch_sizes.json)已从原始校准记录独立重建，不能改动或复用更早的 B 表。校准时长只用于选 B，不构成正式性能结果。
[资格结构记录](../validation/unified_preflight_20261101/qualification_structure.json)保存每输入 S_i、I_i、较小侧和 p_i；两后端逐项核对一致后只计一份，S=0 时 p 为 NA。

[归档后的等价性验证](../validation/unified_preflight_20261101/checks/archived_equivalence_validation.json)、
[资格验证](../validation/unified_preflight_20261101/checks/archived_qualification_validation.json)及
[校准验证](../validation/unified_preflight_20261101/checks/archived_calibration_validation.json)均通过。
[保存性核对](../validation/unified_preflight_20261101/checks/preservation_final.json)确认 24,105 个既有文件原字节不变，运行后工作区仍干净。

上一轮作者主动中止的部分等价性记录保留在[中止尝试](../validation/unified_preflight_20261101/interrupted_attempt/)中。
本轮在同一版本的新目录中从头执行，没有接续旧进度；[重启决定](../validation/unified_preflight_20261101/restart_decision.json)明确为同版本重跑，不是新源码替代旧源码。
旧 `3bfc839f` 资格/校准及中止尝试都不作为本轮前置凭据。

## 本人审阅事项

以下项目留给作者本人核对，不由程序完成情况自动代勾。

- [ ] 已核对 302 个输入、8 个排除条目、来源归属及去重映射；接受预定报告范围，不按结果调整输入。
- [ ] 已核对冻结提交和全部 151 个 Python 文件的源码摘要；正式执行时源码仍相同，工作区干净，不改数值规则。
- [ ] 已理解[无插桩实现](../../src/uninstrumented_finger.py)及现有逐实例方法绑定成本。正式结果表示冻结实现的完整排序成本，包括正常初始化、绑定、排序 core 和输出恢复。
- [ ] 已对照[附录 A](../../thesis/appendix/backend_argument.tex)核对表示、局部性与成本论证、假设及尚待独立审阅的问题；不把有限输入检查当成一般证明。
- [ ] 已阅读本轮三个阶段的原始档案和独立验证结果，核对所有来源均在截止前完成。
- [ ] 已核对新 B 表及环境。qualification 每输入 180 秒、每来源 1800 秒（包括 targeted_split）；校准每来源 600 秒；正式每输入 120 秒、每来源 1800 秒，预算不跨来源挪用。
- [ ] 已理解准备阶段资源退路只在协议允许的 qualification/校准超时情形下继续其他来源；等价性资源失败不能作为后续前置凭据。正确性、trace、workload、电源、配置、源码或找不到 B 等错误立即停止。
- [ ] 已确认正式采样按 common → targeted_split → structural → geometric → seeded 在一个连续会话中完成；来源间不进行测试、编译、分析或其他实验。
- [ ] 已理解正式阶段任何失败均停止后续来源，不重试、不补测后拼接会话。只报告已完整完成来源的结果，并明确整轮完成范围。
- [ ] 愿意报告任一方向的结果。整体主要报告实际计时 N 个输入中树更快 X 个，总体比值为组成相关的次要描述。
- [ ] 已核对四张图、common 类别与 structural shape 分层、S/I/较小侧/p 的定义；相关构造与镜像不是独立样本，不作显著性检验或因果解释。

## 环境和只读复核

前置阶段环境为同一台 Apple M4、CPython 3.12.14、macOS 27.2、优化级别零、GC 开启且阈值 700/10/10、AC Power、lowpowermode 0。正式阶段须匹配前置环境；程序保存原始 pmset，并在每输入前后检查电源，不等于连续监控。

原始配置中的绝对前置路径未改。原执行位置的三个目录链接指向本仓库归档，详见[路径映射](../validation/unified_preflight_20261101/relocation.json)；它们是前置链可解析的必要条件。迁移仓库后先按归档说明恢复链接，不修改配置或重封 manifest。

在仓库根目录执行下面的命令可只读复核完整前置链，不运行排序或补采样；前置阶段已经完成，不要再次启动它们：

```sh
cd /Users/schnee/Documents/Codex/files-mentioned-by-the-user-thesis/jordan-sorting
PYTHONPATH=src:experiments /Users/schnee/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -B experiments/validate_input_suite_run.py \
  docs/validation/unified_preflight_20261101/calibration
```

正式运行前接通交流电、关闭低电量模式和会产生明显负载的其他任务。receipt 与正式输出放在仓库外，输出目录必须尚不存在。发生失败时保留全部记录并先调查，不删除目录、改 B 或换输入来覆盖失败。

## 作者本人创建 receipt

原修改说明第 6.2 节要求：“这份 receipt 必须由作者本人确认后创建，Codex 不得代填。”第 6 节要求作者本人在 Mac 上执行正式采样；追加协议保留这些要求。当前没有创建 receipt。

本人完成审阅后，收据须恰好包含四个字段：

| 字段 | 内容 |
|---|---|
| `schema` | `representation_locality_cost_review_v1` |
| `approved` | 本人确认后的 JSON 布尔值 `true`，不能提前代填 |
| `production_sha256` | 完整复制本轮 [production_sha256.json](../validation/unified_preflight_20261101/production_sha256.json) 中的 19 个 `src/` 摘要映射，不是路径 |
| `review_references` | 本人实际审阅的文件、章节、冻结提交、统一清单及说明组成的非空字符串数组，不填占位文本 |

未完成审阅不要创建声称已批准的收据。程序只能核对结构与源码，不能认证数学证明。

## 作者正式采样命令（尚未执行）

本人审阅并自行保存收据后，从仓库根目录执行以下一次 `--source all` 会话。后续仅归档或清单提交不改变冻结执行代码，但运行前仍须确保完整源码摘要相同且工作区干净。

```sh
PYTHONPATH=src:experiments /Users/schnee/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -B experiments/run_input_suite.py \
  --stage formal --source all \
  --equivalence docs/validation/unified_preflight_20261101/equivalence \
  --qualification docs/validation/unified_preflight_20261101/qualification \
  --calibration docs/validation/unified_preflight_20261101/calibration \
  --review ../.codex-tmp/author_unified_review_bca4c1c6.json \
  --output ../.codex-tmp/unified_formal_bca4c1c6
```

若程序拒绝开始或中途失败，保留所有输出，停止并汇报。不要自行重试或用多个单来源正式目录拼成完整会话。校准数据不能补充正式样本。

## 正式会话结束后的验证与分析

以下命令只在正式采样会话结束后使用，不与采样并行：

```sh
PYTHONPATH=src:experiments /Users/schnee/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -B experiments/validate_input_suite_run.py \
  ../.codex-tmp/unified_formal_bca4c1c6

PYTHONPATH=src:experiments /Users/schnee/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -B experiments/analyze_input_suite.py \
  --formal ../.codex-tmp/unified_formal_bca4c1c6 \
  --output ../.codex-tmp/unified_analysis_bca4c1c6
```

分析从原始记录重算统计量，输出 JSON、CSV 和四张 PNG/PDF 图；不读取运行汇总作为性能证据，也不触发补采样。绘图依赖应在正式采样之前准备完毕。

## 正式采样完成后的待办

- [ ] 在正式采样完成后，在同一台机器上独立测量插桩树与无插桩树的实例创建时间，只测构造，不运行排序。测量前固定构造参数、预热、重复次数和 GC 设置，预先完成无插桩方法生成以匹配正式配置；保留环境、脚本及原始记录。结果用于论文方法章说明构造路径和方法绑定成本，不从正式时长中扣除这部分成本，不修改正式采样数据、主要分析或冻结生产代码，也不据此重跑正式实验。当前只登记待办，尚未执行。
