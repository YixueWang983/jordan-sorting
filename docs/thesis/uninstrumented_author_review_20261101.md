# 作者本人审阅与正式执行清单

## 为什么需要这一步

作者提供的修改说明第 6.2 节明确要求：
“这份 receipt 必须由作者本人确认后创建，Codex 不得代填。”
第 6 节还要求正式采样由作者本人在 Mac 上执行。此前的代码修改、测试、
等价性验证、qualification 和校准不等同于这个确认。

## 可核对的已完成结果

- [预登记协议](../plan/uninstrumented_rerun_protocol_20261101.md) 已单独提交，先于校准。
- [实现说明和全量测试日志](../validation/uninstrumented_equivalence_20261101/implementation_notes.md)：824 项测试通过。
- [等价性档案](../validation/uninstrumented_equivalence_20261101/README.md)：192/192 输入通过，每种树配置核对 50,626 个完成前缀；192 份旧 trace 一致。
- [资格检查和校准](../validation/uninstrumented_preflight_20261101/README.md)：140 common 与 12 targeted split 均通过，并已独立复核。
- [生产源码 SHA-256 清单](../validation/uninstrumented_preflight_20261101/production_sha256.json)：19 个文件；上述运行均使用实现提交 `3bfc839fae8da3061938f48f490e936deb0c002e`。
- [实现源码](../../src/uninstrumented_finger.py) 及 [附录 A](../../thesis/appendix/backend_argument.tex) 可对照审阅。本轮附录 A 未改，没有取得新的独立证明审查。
- [保存性核对](../validation/uninstrumented_preflight_20261101/preservation_final.json)：旧档案及 PDF 共 18,106 个文件保持原字节。

两组校准都在 Apple M4、CPython 3.12.14、macOS 27.2、AC Power、lowpowermode 0 下执行，完整绑定源码相同。正式运行必须继续匹配这些条件。

## 审阅内容

- [ ] 已阅读预登记协议，认可固定的 140/12 输入、完整排序计时范围和
  原数值规则；不根据结果挑选输入、剔除样本或重跑。
- [ ] 已阅读同源投影的实现说明：算法方法只维护一份；普通记录类没有
  字段拦截；生成代码移除纯记录调用与 observed/phase 包装，保留算法
  分支和必要检查；每次实例绑定仍算入初始化成本。
- [ ] 已核对全量测试、192 输入等价性及 qualification 记录，并理解
  有限输入上的一致性不是一般等价性或复杂度证明。
- [ ] 已核对本版本的表示、局部性与成本论证、假设及仍待独立审阅的
  问题。附录 A 本轮未修改；这里不声称已有新的外部证明审查。
- [ ] 已核对 production_sha256.json 对应待执行的生产源码；之后若
  代码改变，不能继续使用旧校准和此 receipt。
- [ ] 愿意照实报告任何方向的结果，并保留旧插桩数据和这次数据的
  环境区别，不将跨 session 差异直接归因于插桩本身。

尚未确认的项目应先提出具体问题，不要填入 approved=true。

## 执行条件

保持 Mac 接通交流电、低电量模式关闭。运行期间不进行测试、编译、分析
或其他实验。receipt 与正式输出应放在仓库外，保证源码工作区保持干净；
两个数据集由统一入口依次执行。任何失败后保留全部记录，先诊断，不直接
重跑同一命令换掉结果。

## 作者需要创建的收据

本轮只保存 `production_sha256.json` 源码摘要清单，没有创建获批收据。收据须由作者在核对完成后自行保存为仓库外的 UTF-8 JSON 文件，例如：

`/Users/schnee/Documents/Codex/files-mentioned-by-the-user-thesis/.codex-tmp/author_uninstrumented_review_20261101.json`

收据必须恰好包含四个字段，不能增加或缺少字段：

| 字段 | 内容 |
|---|---|
| `schema` | 固定字符串 `representation_locality_cost_review_v1` |
| `approved` | 作者本人完成审阅后决定的 JSON 布尔值；程序只接受已确认的 `true`，不能用字符串代替 |
| `production_sha256` | 完整复制[生产源码摘要清单](../validation/uninstrumented_preflight_20261101/production_sha256.json) 中的对象，包含所有 19 个 `src/` 文件；不是路径或整个 Git commit |
| `review_references` | 非空字符串数组；填写本人实际审阅的文件、章节、版本与审阅说明，不能写占位文本或把测试通过当成证明审阅 |

尚未完成审阅时，不应创建声称已批准的收据。现有论证尚待独立审阅的状态不因这份收据而改变。收据只记录作者已检查的依据和决定，程序不会验证数学证明是否成立。

## 正式执行命令

以下命令只供作者在审阅并自行创建收据后执行。开始前接通电源、关闭低电量模式，关闭会产生明显负载的其他任务。输出目录必须尚不存在。

```sh
cd /Users/schnee/Documents/Codex/files-mentioned-by-the-user-thesis/jordan-sorting
PYTHONPATH=src:experiments /Users/schnee/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 experiments/run_uninstrumented_formal.py \
  --qualification docs/validation/uninstrumented_preflight_20261101/qualification \
  --calibration docs/validation/uninstrumented_preflight_20261101/calibration \
  --review ../.codex-tmp/author_uninstrumented_review_20261101.json \
  --output ../.codex-tmp/uninstrumented_formal_20261101
```

这个入口先运行 common，再紧接着运行 targeted_split；任一数据集失败就停止。两组运行之间不要执行其他任务。不要同时启动本文档后面的分析命令、测试或论文编译。

如果程序拒绝开始或中途失败，应保留终端输出及全部文件，再诊断原因。不能删除目录、修改 B 表或换输入来覆盖失败。完成后把实际输出目录交给 Codex 做独立档案验证、从原始记录重建统计量和论文更新。若换了 Python、系统版本或改了源码，旧校准可能不再适用，不能绕过一致性检查。

## 两组采样结束后的分析入口

下列命令只在前一个命令成功结束、两个数据集都已经完成之后执行：

```sh
PYTHONPATH=src:experiments /Users/schnee/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 experiments/analyze_uninstrumented_measurement.py \
  --qualification docs/validation/uninstrumented_preflight_20261101/qualification \
  --calibration docs/validation/uninstrumented_preflight_20261101/calibration \
  --formal ../.codex-tmp/uninstrumented_formal_20261101 \
  --output ../.codex-tmp/uninstrumented_analysis_20261101
```

分析工具先验证两组档案，再从原始记录重算全部输入的中位数、R7 四分位数与比值，并与独立验证器核对；这些结果才是论文新数字的来源。
