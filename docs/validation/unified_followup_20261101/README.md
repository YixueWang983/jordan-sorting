# 正式实验之后的构造微基准与事后稳定性描述

阶段二已完成：只测构造的微基准及首次完整完成的 170 个输入的两次比值比较。两项结果均独立校验通过，原始记录按原字节归档。**没有重跑排序、修改正式时间、合并两次尝试或更新论文。**

## 方案固定与证据身份

[方案](PLAN.md)、[参数](protocol.json)和三个脚本在测量前单独提交固定，提交为 `70d47e9141dbcc95a232bd133093e99e7260fca3`。没有先试跑再调整参数。构造测量执行一次，预热 5 轮、测量 50 个配对轮次、每组每批 256 个实例；每组正式创建 12,800 个实例。50 个配对轮次中两种配置各先执行 25 次。

冻结的生产和实验源码仍为 `bca4c1c6` 所绑定的 151 个文件，未修改 `src/`、`experiments/` 或 `tests/`。新脚本仅放在本补充档案目录，并在微基准配置中单独绑定其 SHA-256。原 [302 输入正式结果档案](../unified_formal_20261101/README.md)及其主分析保持原字节。

## 构造微基准

两组直接构造同一个公开后端类，使用同一预绑定 `dict.__getitem__` 回调、`MINIMAL_POLICY` 和 `detailed_work=False`，只切换 `instrumented=True/False`。因此这里的“插桩”指保留插桩代码但关闭详细计数的旧计时配置。没有生成树节点、调用排序或树更新/查询操作。无插桩类和 54 个方法在计时前准备并缓存。

环境匹配正式尝试：Apple M4、macOS 27.2、CPython 3.12.14、优化级别零，GC 开启，阈值 700/10/10。每批前后电源门槛通过并保留原始 `pmset` 输出。测量时段（Europe/Berlin）：2026-11-01T23:06:14.222404+01:00 至 2026-11-01T23:06:17.358417+01:00；批次流程墙钟 3.113 秒，不是性能统计量。使用 `caffeinate -i`；测量前后的进程快照保留，没有绑核或声称独占系统资源。

下表单位为 **μs/实例**；每个观测是该批的 `elapsed_ns/256`，每组 50 个观测。

| 配置 | 中位数 | Q1–Q3 | 最小值–最大值 |
|---|---:|---:|---:|
| instrumented | 0.419760 | 0.405313–0.431397 | 0.394371–0.574383 |
| uninstrumented | 5.303711 | 5.236532–5.387696 | 5.097004–6.132324 |

配对的“无插桩减插桩”差值中位数为 **4.880859 μs/实例**，两组中位数之比为 12.635110。配对比值本身的中位数为 12.655424；它与两组中位数之比是不同统计量。

计时包括构造调用、循环及预分配列表写入。对象保持存活直到计时结束，之后才检查并释放；主动 GC、清理、记录和电源检查在计时外。自动 GC 保持开启，实际计时内插桩配置共发生 100 次第 0 代回收，无插桩配置共发生 950 次第 0 代和 50 次第 1 代回收。

这些值描述**本固定批量设计下的构造路径开销**。差值还受账本创建、自动 GC、对象保留和共同的循环/存储开销影响，不能把它等同于逐个绑定方法的纯成本，也不能直接推算完整排序中该部分的精确占比。先前口头使用的约 10 μs 估计不替代这份实测；本次观测不从正式排序时间扣除，不据此修改实现或重新采样。

- [原始压缩批次记录](results/constructor/records/)（10 条预热、100 条测量）
- [环境与时钟](results/constructor/environment.json)、[冻结配置及脚本摘要](results/constructor/config.json)
- [构造统计](results/analysis/constructor_summary.json)、[逐批 CSV](results/analysis/constructor_batches.csv)、[配对观测](results/analysis/constructor_pairs.json)
- [测量日志](results/benchmark.console.log)

## 两次尝试的事后描述性比较

**不在原协议内、不进入主要统计，只作稳定性描述。** 这项检查由作者在第二次主结果完成后提出。仅纳入首次 COMPLETE 的 common 140、targeted_split 12、structural 18，共 170 个输入；不纳入首次 geometric 的部分记录。两次档案各自独立验证，从原始正式批次重算 `median(tree elapsed_ns/B)/median(list elapsed_ns/B)`，逐项确认输入摘要和 B 一致。

两次各有 32/170 个输入树更快、138/170 个输入列表更快；**170/170 个输入的快慢方向一致**。绝对相对变化定义为 `100*abs(r2/r1-1)`，中位数 **0.425627%**，最大 **1.984380%**。这描述两次比值之间的变化，不是比值本身距 1 的距离，也不是等效性检验或精度保证。

| 来源 | 输入数 | 首次比值中位数 | 第二次比值中位数 | 绝对相对变化中位数 | 最大绝对相对变化 | 方向一致 |
|---|---:|---:|---:|---:|---:|---:|
| common | 140 | 1.236035 | 1.230987 | 0.436106% | 1.984380% | 140/140 |
| targeted_split | 12 | 1.348115 | 1.352014 | 0.305298% | 0.712026% | 12/12 |
| structural | 18 | 1.274198 | 1.268999 | 0.443894% | 1.394248% | 18/18 |
| 合计 | 170 | 1.250183 | 1.247303 | 0.425627% | 1.984380% | 170/170 |

全部 170 个输入的首次比值范围为 0.584470–1.512991，第二次为 0.590223–1.517609。逐输入有符号差 `r2-r1` 的中位数为 0.002014，范围为 -0.022303–0.025949；“差的中位数”不等于“两组中位数之差”。完整分层和逐输入值保留在数据表中。

这两次运行共享输入、源码、配置和机器，镜像及构造也有依赖关系；不是独立重复样本。结果不能消除首次电源失败或第二次重启偏离，不能推广到未比较的 geometric/seeded，也不能证明长期可重复性。没有显著性检验、置信区间或因果解释。第二次主结果仍为原有的 44/302 个输入树更快。

- [比较摘要](results/analysis/stability_summary.json)
- [170 输入比较 CSV](results/analysis/stability_cases.csv)与[JSON](results/analysis/stability_cases.json)
- [来源、manifest 与脚本摘要](results/analysis/provenance.json)

## 独立验证、迁移与复核

[独立验证脚本](verify.py)采用另一套统计计算，重读原始批次核对构造统计和 170 个输入的两次比值，检查 CSV/JSON、调度、电源、GC、源码和脚本身份。还逐文件核对整个前置归档包和正式归档包，确认主数据未变。

- [迁移前验证结果](results/verification.json)
- [迁移后验证结果](checks/archived_verification.json)
- [迁移前 131 个文件的摘要](checks/pre_move_inventory.json)
- [路径迁移记录](relocation.json)

原 `.codex-tmp/unified_followup_20261101/` 目录已原字节移入本目录的 `results/`，原位置保留目录链接，保证分析来源引用继续有效。原始构造与分析 manifest 均未重封；[归档包摘要](package_manifest.json)仅用于本目录整体保存性，不替换它们。

从仓库根目录只读复核，不触发构造或排序：

```sh
PYTHONPATH=src:experiments /Users/schnee/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -B docs/validation/unified_followup_20261101/verify.py \
  --benchmark docs/validation/unified_followup_20261101/results/constructor \
  --analysis docs/validation/unified_followup_20261101/results/analysis
```

阶段二到此结束。论文改写及论文版图表尚未执行，另按作者给出的顺序开展。
