# 统一 302 输入前置阶段档案（2026-11-01）

本次等价性验证、qualification 和校准全部完成并独立复核通过。
**未开始正式采样，未创建作者 receipt，也未开展实例创建微基准。**

## 冻结身份与执行

- 冻结提交：`bca4c1c6a5480e22c7121987de2c97bb00688264`。
- 151 个 Python 源文件的完整身份摘要：`0cd50e8f3db8199a9d4e0804a6e6d648d4d337aa8f58791af6dbe3a328212a82`。
- [完整源码映射](freeze.json)与[19 个生产源码文件的 SHA-256](production_sha256.json)。归档和后续作者清单提交不改变冻结源码。
- 统一清单身份：`a8c2fe3aa2fe4b45bbe876db9e9dabe3b7f95fd666b3c3afab0776bef67234b7`，302 个条目、302 个规范输入；8 个 n=1500 的排除条目未参与。
- 每阶段均以 `--source all` 执行，顺序 common → targeted_split → structural → geometric → seeded。
- 三阶段在同一冻结提交的干净工作区串行执行，期间没有修改源码，也未并行进行测试、编译或其他实验。阶段间仅作档案验证与正常调度。
- 环境为 Apple M4、CPython 3.12.14、macOS 27.2、优化级别零、GC 开启（阈值 700/10/10）、AC Power、lowpowermode 0；逐输入前后电源检查通过。原始 pmset 输出保留，检查不等于连续监控。
- [执行时序](chronology.json)：等价性 16:46:17–17:16:33 UTC；qualification 17:17:22–17:36:50 UTC；校准 17:38:24–17:40:32 UTC。这些是工作流程时间，不是排序性能结果，全部早于 11 月 15 日的准备截止点。

## 来源完成状态

| 来源 | 输入数 | 等价性 | qualification | 校准 |
|---|---:|---|---|---|
| common | 140 | COMPLETE | COMPLETE | COMPLETE |
| targeted_split | 12 | COMPLETE | COMPLETE | COMPLETE |
| structural | 18 | COMPLETE | COMPLETE | COMPLETE |
| geometric | 100 | COMPLETE | COMPLETE | COMPLETE |
| seeded | 32 | COMPLETE | COMPLETE | COMPLETE |

没有资源超时、非资源类错误或未完成来源。每个输入的新公共 B 都按原阶梯与双后端阈值确定，没有复用旧 B、改输入、追加样本或调整预算。
[逐输入 B 表](batch_sizes.json)来自校准原始批次的独立重建；校准时长不作为后端性能比较。

| 来源 | B 的频数（B: 输入数） |
|---|---|
| common | 1: 24, 2: 15, 4: 25, 8: 29, 16: 27, 32: 20 |
| targeted_split | 8: 12 |
| structural | 1: 6, 2: 2, 4: 6, 8: 4 |
| geometric | 1: 20, 2: 20, 4: 20, 8: 19, 16: 16, 32: 5 |
| seeded | 1: 16, 4: 8, 8: 2, 16: 2, 32: 4 |

## 新资格 trace 的结构描述

以下每个规范输入只计一份 primary checked trace，两个后端的结构已逐项验证一致；
不重复累计同步 peer、fresh replay 或另一后端。S 是实际 performed split 总数，I 是两侧均非空的数量。
较小侧单位为 sibling list 中的 pair 条目。来源不同、镜像及相关构造不视为独立随机样本。

| 来源 | S 总数 | I 总数 | 含双侧 split 的输入数 | 较小侧 min / median / max |
|---|---:|---:|---:|---|
| common | 3788 | 0 | 0/140 | NA |
| targeted_split | 24 | 12 | 12/12 | 3 / 7.0 / 19 |
| structural | 460 | 230 | 18/18 | 1 / 1.0 / 126 |
| geometric | 9272 | 1774 | 99/100 | 1 / 1.0 / 17 |
| seeded | 2946 | 307 | 30/32 | 1 / 1 / 8 |

common 中 40 个输入的 S=0，其 p=I/S 保存为 null（NA），不写成零。
[逐输入结构记录](qualification_structure.json)保留 S_i、I_i、全部较小侧值与 p_i；
[来源摘要](status_summary.json)保留完整较小侧频数；
[common 嵌套类别与 structural shape 分层](qualification_structure_strata.json)另行保留。
这里仅描述结构，没有正式比值、显著性检验或因果分析。

## 独立验证与保存性

- `equivalence/`、`qualification/`、`calibration/` 保存原请求、环境、逐输入状态、原始记录及各自 manifest；配置、文件内容和原 manifest 均未改写或重封。
- `checks/final_*_validation.json` 是归档前的独立验证报告。最终校准链验证递归读取所有前置记录，从原始数据重建状态、输出、workload、配置、顺序和 B；不依赖 worker summary 内容。
- `checks/archived_*_validation.json` 是移入本目录后的再次独立核对，同样全部通过。
- [保存性核对](checks/preservation_final.json)：运行结束时工作区仍干净，源码身份不变，24,105 个既有文件保持原字节，包括生产代码、旧档案、协议、论文与输出。
- [迁移核对](relocation.json)逐阶段记录文件数、原/新路径及原 manifest 摘要，确认移动未改变字节。
- [整个归档包文件摘要](package_manifest.json)覆盖本目录中除自身之外的所有文件；它不替换三个原始 manifest。

## 上一轮主动中止记录

`interrupted_attempt/` 完整保留此前作者主动中止的同版本尝试：common 140、targeted_split 12、structural 12 个输入已提交 PASS，structural 的下一例被中止；geometric、seeded、qualification 和校准尚未启动。
它没有完整的等价性 manifest，也不是本次前置凭据。本次从新目录重新执行了全部 302 个输入，没有接续旧进度。

当时计划修改源码，曾创建 `superseded.json`；随后作者取消修改，决定保持 `bca4c1c6`。
[restart_decision.json](restart_decision.json)据此明确标记为 **AUTHOR_INTERRUPTED_RESTARTED_SAME_VERSION**。
旧 marker 原样保留为当时的决定记录，不能解释为存在一个替代 `bca4c1c6` 的新源码版本。
原有 831 个文件的摘要已逐项复核，未删除或改写；待审阅的 R1 草案不构成本次适用协议。

## 路径绑定与只读复核

原配置中的前置路径是执行时的绝对路径，保持原文。三个阶段目录已移至本归档，
在原执行根目录
`/Users/schnee/Documents/Codex/files-mentioned-by-the-user-thesis/.codex-tmp/unified_preflight_20261101_bca4c1c6_rerun/`
下分别保留 `equivalence`、`qualification`、`calibration` 的目录链接，指向本归档的同名目录。
这些链接在仓库外，归档内部全部是普通文件与目录；验证器解析路径后读到的是本归档原始记录。

迁移到另一位置时，应先按 `relocation.json` 恢复这三个原路径的目录链接，再检查；不要直接修改配置中的前置路径并重封 manifest。
在本机、源码身份不变时，从仓库根目录只读复核：

```sh
PYTHONPATH=src:experiments /Users/schnee/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -B experiments/validate_input_suite_run.py \
  docs/validation/unified_preflight_20261101/calibration
```

该命令递归复核三阶段，不运行排序或补采样。未来若实验工具源码改变，应在冻结版本核对，或明确使用 `--historical` 做历史只读审计；不能因此把旧准备记录绑定到新实现。

正式执行命令及作者需要确认的项目见[作者审阅清单](../../thesis/uninstrumented_author_review_20261101.md)。
