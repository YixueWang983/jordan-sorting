# 作者本人审阅与统一重跑执行清单

更新：2026 年 11 月 1 日，阶段三。本文是待执行清单，不是获批收据。
本阶段没有运行登记输入的等价性验证、qualification、校准或正式采样。

## 当前依据与需要冻结的版本

- [原协议](../plan/uninstrumented_rerun_protocol_20261101.md)与[追加协议](../plan/uninstrumented_rerun_addendum_20261101.md)共同适用；冲突处以追加协议为准。
- 追加协议提交为 `afbbff68525b112ad9bc03c163b435ca74590212`；阶段二输入注册已提交并推送为 `b599c67f`。
- [统一清单](../validation/input_suite_registry_20261101/suite.json)包含 common 140、targeted_split 12、structural 18、geometric 100、seeded 32，共 302 个条目，302 个规范输入，重复数为零。8 个 n=1500 的 seeded 条目另列排除清单。
- 清单 SHA-256 为 `a8c2fe3aa2fe4b45bbe876db9e9dabe3b7f95fd666b3c3afab0776bef67234b7`。
- [阶段三说明](../development/unified_suite_stage3_20261101.md)及[候选源码清单](../development/unified_suite_stage3_source_20261101.json)描述当前待审阅实现。阶段三尚未提交；最终冻结的是审阅后包含全部实验工具与测试的提交，不能只冻结阶段二的提交。
- **冻结后全部五个来源重做等价性、qualification 和校准。** [旧等价性](../validation/uninstrumented_equivalence_20261101/README.md)与[旧资格/校准](../validation/uninstrumented_preflight_20261101/README.md)仅保留为历史证据，不能用作本轮前置目录或复用 B 表。工具也会拒绝旧 schema。
- `src/` 未改；[同源投影实现](../../src/uninstrumented_finger.py)及[附录 A](../../thesis/appendix/backend_argument.tex)仍须本人对照理解。工具测试和有限输入一致性不代替证明审查。

## 本人审阅事项

- [ ] 已核对 302 个输入、8 个排除条目、来源归属及去重映射；接受既定报告范围，不按运行结果调整输入。
- [ ] 已核对最终 Git 提交与完整 `source_sha256`，包含 src、experiments、tests；工作区干净，此后不改源码或数值规则。
- [ ] 已理解树的无插桩投影、必要绑定与 fresh minimal 计时范围，核对表示、局部性与成本论证及尚待独立审阅的问题。
- [ ] 已检查本轮全部新前置记录及独立验证结果，确认每个拟计时来源的前置阶段在 11 月 15 日 00:00 Berlin 前完成。记录明确的 INCOMPLETE 来源，不用其已完成小输入另组性能子集。
- [ ] 已核对新资格预算：每输入 180 秒，每来源 1800 秒，包括 targeted_split；旧 targeted 档案的 180 秒 campaign 记录保持历史身份。
- [ ] 已核对逐输入公共 B 表及相同环境。校准每来源 600 秒，正式每输入 120 秒、每来源 1800 秒；预算不跨来源挪用。
- [ ] 已理解 qualification/校准资源超时允许其余来源继续；正确性、trace、workload、电源、配置或源码错误停止后续执行。没有满足阈值的 B 也不是资源超时。
- [ ] 已确认正式会话按 common → targeted_split → structural → geometric → seeded 连续执行；不在来源间测试、编译或分析，不追加另一会话补齐缺失来源。
- [ ] 愿意报告任一方向的结果和未完成来源。整体主要报告实际计时 N 个输入中树更快 X 个；总体比值只是组成相关的次要描述。
- [ ] 已核对四张图、common 类别与 structural shape 分层、S/I/较小侧/p 的定义，理解镜像和相关构造不是独立样本，不作显著性或因果解释。

## 环境与输出位置

统一入口检查 Apple M4、CPython 3.12.14、优化级别零、GC 启用、AC Power、lowpowermode 0；记录 OS、CPU、内存、GC、时钟及原始 pmset 输出，并匹配前置档案中的环境与源码。逐输入前后检查电源，不声称连续监控。

使用仓库外的新输出目录。失败目录不能覆盖，原始失败与 NOT_RUN 必须保留；修复后先审阅并重新冻结，不能自行重试以替换结果。以下路径均为未来执行示例；本阶段没有创建它们。

## 版本冻结并获得启动授权后的前置命令

以下顺序不能颠倒，也不能引用旧的 `uninstrumented_preflight_20261101` 目录。

```sh
cd /Users/schnee/Documents/Codex/files-mentioned-by-the-user-thesis/jordan-sorting
PYTHONPATH=src:experiments /Users/schnee/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -B experiments/run_input_suite.py \
  --stage equivalence --source all \
  --output ../.codex-tmp/unified_rerun/equivalence

PYTHONPATH=src:experiments /Users/schnee/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -B experiments/run_input_suite.py \
  --stage qualification --source all \
  --equivalence ../.codex-tmp/unified_rerun/equivalence \
  --output ../.codex-tmp/unified_rerun/qualification

PYTHONPATH=src:experiments /Users/schnee/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -B experiments/run_input_suite.py \
  --stage calibration --source all \
  --equivalence ../.codex-tmp/unified_rerun/equivalence \
  --qualification ../.codex-tmp/unified_rerun/qualification \
  --output ../.codex-tmp/unified_rerun/calibration

PYTHONPATH=src:experiments /Users/schnee/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -B experiments/validate_input_suite_run.py \
  ../.codex-tmp/unified_rerun/calibration
```

每个阶段先只读验证其前置档案，逐作业也从原始记录核对输出和调度。最后一条递归核对全部绑定的前置档案，不启动排序。各阶段目录保存请求、原始记录、来源与逐输入状态、环境及文件摘要；没有作为证据来源的运行汇总。

`--source` 也接受一个原来源名。若前置工作分来源执行，可向对应 `--equivalence`、`--qualification`、`--calibration` 参数依次传入多个目录；同一来源的多个尝试会被拒绝，不能从多个尝试中选成功部分。未请求来源标为 NOT_RUN。

CLI 的退出码 2 表示未完整完成，不一定是全局错误。只有独立验证确认的 qualification/校准资源退路才允许其余来源进入后续阶段；错误不能当作超时跳过。

## 作者本人创建 receipt 与执行正式会话

作者原修改说明第 6.2 节要求：“这份 receipt 必须由作者本人确认后创建，Codex 不得代填。”第 6 节要求正式采样由作者本人在 Mac 上执行；追加协议继续保留这两项要求。本文未创建 receipt。

本人完成审阅后，收据须恰好包含四个字段：

| 字段 | 内容 |
|---|---|
| `schema` | `representation_locality_cost_review_v1` |
| `approved` | 本人确认后的 JSON 布尔值 `true`，不得提前代填 |
| `production_sha256` | 最终冻结源码摘要中全部 `src/` 文件的映射，不是路径；可从候选清单的同名对象核对，但必须再次确认与最终版本一致 |
| `review_references` | 本人实际审阅的文件、章节、最终提交、统一清单及说明组成的非空字符串数组，不能填占位文本 |

尚未完成审阅不要创建声称已批准的收据。程序只能核对收据结构与源码，不能认证数学证明。保存至仓库外后，由作者执行：

```sh
PYTHONPATH=src:experiments /Users/schnee/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -B experiments/run_input_suite.py \
  --stage formal --source all \
  --equivalence ../.codex-tmp/unified_rerun/equivalence \
  --qualification ../.codex-tmp/unified_rerun/qualification \
  --calibration ../.codex-tmp/unified_rerun/calibration \
  --review ../.codex-tmp/author_unified_review.json \
  --output ../.codex-tmp/unified_rerun/formal
```

主结果使用上面一次 `--source all` 会话。接口虽支持单来源正式执行，但它仅是一份部分会话；分析只接受一个正式会话，不把多个单来源会话拼成预定的完整会话。正式失败停止后续来源；只报告已完整完成的来源，中途失败来源的部分时间仅保留为失败记录。

## 正式会话结束后的独立验证与分析

```sh
PYTHONPATH=src:experiments /Users/schnee/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -B experiments/validate_input_suite_run.py \
  ../.codex-tmp/unified_rerun/formal

PYTHONPATH=src:experiments /Users/schnee/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -B experiments/analyze_input_suite.py \
  --formal ../.codex-tmp/unified_rerun/formal \
  --output ../.codex-tmp/unified_rerun/analysis
```

分析重算每后端 20 个 elapsed_ns/B 的中位数与 R7 四分位数，再核对独立验证器；结构来自完整通过的新资格 primary trace，两个后端逐项一致后只计一份。输出 JSON、CSV 及四张 PNG/PDF 图。绘图依赖 matplotlib；依赖安装应在正式采样前完成。没有双侧 split 时较小侧分布为空；S=0 的 p 为 NA，图中明确计数。
