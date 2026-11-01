# Mac / Windows 跨平台验证与首轮主机对照（2026-11-01）

**两台机器均可运行当前测试和评测入口，但首轮数据不支持“Windows 全面更稳定”。** 两端在同一源码上通过 870/870 单元测试，诊断各完成 10 输入、3 会话和 1200 个采样批次。Mac 在两个后端的会话内波动上均更低；普通列表的会话间漂移也更低。树后端的会话间漂移几乎相同，Windows 仅略低。

因此，Windows 已具备承担日常回归、定向输入检查和独立诊断的条件；**本次不据此宣布正式性能评测迁移完成**。正式分析继续保留主机身份；若后续要迁移，应在更多日期和输入上获得独立重复结果，按迁移后的同机前置链重新取得资格和校准。

## 实际结果

指标均越低越稳定。会话内指标：每输入取三会话 IQR/median 的中位数，再取十输入的中位数。会话间指标：每输入三个会话中位数的 `(max-min)/median`，再取十输入的中位数。末两列为 Windows 指标严格较低的输入数。

| 后端 | Windows 会话内波动 | Mac 会话内波动 | Windows 会话间漂移 | Mac 会话间漂移 | Windows 会话内较低 | Windows 会话间较低 |
|---|---:|---:|---:|---:|---:|---:|
| 普通列表 | 1.342% | 0.904% | 1.512% | 0.828% | 1/10 | 4/10 |
| 未插桩异构 finger tree | 1.236% | 1.044% | 0.967% | 0.975% | 2/10 | 6/10 |

逐输入数值见 [comparison.json](comparison.json) 和 [comparison.csv](comparison.csv)。两台机器的 2400 个批次分别分析，没有合并成一个样本，也没有删掉异常值或挑选重跑中的最好结果。每台机器均为该源码上的第一次完整稳定性尝试。

排序每调用时长的 Windows/Mac 比值按输入取中位数：普通列表为 1.629，树后端为 1.549。这是两台具体主机的描述性结果，不能归因于操作系统本身。回归测试的总耗时不是排序性能指标。

## 环境与执行身份

- 执行提交：`e58841525726b0a7326d0cd730199882f834bad8`；157 个 Python 源文件摘要：`15571418657d234eb08f28c3a7f521eab9c6cafd70579b1c03dbef72fad31b96`。两端执行前后源码一致且工作区干净。
- Windows：Sherry02，Windows 11 `10.0.26300`，Ryzen 5 7500F，6 核/12 线程，32 GB 安装内存；原生 CPython 3.12.14 / MSC 64 位 AMD64，交流供电、节能关闭，平衡电源计划。固定 5.0 GHz 和无竞争负载是用户确认的 BIOS/使用条件，不是软件实测频率。原生记录保留 `hypervisor_present=True`，未修改安全或电源设置。
- Mac：MacBook Air / Apple M4，10 核，16 GiB 内存，macOS 27.2 / arm64，原生 CPython 3.12.14 / Clang，交流供电、低电量模式关闭。作为开发工作站执行；未宣称没有系统后台活动。完整原始电源观测保留在环境 JSON。
- 两端 GC 开启、阈值一致、优化级别 0；分别校准公共 B。Windows 使用 B={1,4,16}，Mac 使用 B={1,8,32}；同一主机三会话固定同一 B 表。
- 测量前已固定五来源最小/最大 n 面板、种子、5 次预热和 20 轮交替配对测量，见[协议补充](../../plan/cross_platform_evaluation_20261101.md)。测试与计时串行进行。
- 两端均只依赖 Python 标准库执行此诊断。全量工具测试使用的 matplotlib 为 Windows 3.11.2、Mac 3.11.1；版本记录分别保存，未将其当作排序运行时依赖。

## 验证与证据

| 验证 | Windows | Mac |
|---|---:|---:|
| 最终全量回归 | 870/870，526.867 秒 | 870/870，221.485 秒 |
| 诊断输入 / 会话 / 采样批次 | 10 / 3 / 1200 | 10 / 3 / 1200 |
| 诊断协议内耗时 | 156.265 秒 | 90.387 秒 |
| 原始档案文件数（含 manifest） | 1905 | 1941 |
| 独立重算和副本验证 | 通过 | 通过 |

- [Windows 原始档案](windows/)；[Mac 原始档案](mac/)。每批原始计时和输出、checked/fresh minimal 正确性记录、校准、供电检查、请求及 manifest 全部保留。
- [Windows 原生检查与日志](windows-checks/)；[Mac 检查与日志](mac-checks/)。最初 Windows `cf4d7a06` 失败尝试也保留：868 个方法中 794 通过、74 出错（共 121 条含子测试错误）；原因是路径分隔符和旧 POSIX load-average 测试夹具。修复后没有跳过测试。
- [Windows 档案在 Mac 上重新验证](windows-revalidated-on-mac.json)；[Mac 独立分析](mac-analysis.json)；[两机对照](comparison.json)。分析从原始记录重算，不信任工作进程 summary。
- 旧 Mac 302 输入的 equivalence、qualification、calibration 档案均已只读验证通过，见[历史验证结果](mac-checks/historical-mac-validation.json)；该检查使用 `cf4d7a06` 校验器，原档案和生产算法没有改动。
- Windows 证据提交 `93306dc77793f303f7d1000f218427d12f9cfc26` 经 Git bundle 和证书指纹校验的临时 TLS 连接传回 Mac；bundle SHA256 为 `6e51d1314ac4add4275b5275e56e68dc878d408c176739eb42ffbcf938c4d6ba`。接收端已自动关闭。两份原始诊断逐字节复制后再次通过验证。

Windows manifest 内容摘要：`d412a5c12d8c10a888f1c83c5eae17c4a9ed85828d58c8b6774ddcfecac2d0f9`。Mac manifest 内容摘要：`8b0cb7e35be92a67c0e4ee796d84964222cedc2f2b87091b211bc41f87ef30b3`。这里为规范 JSON 内容摘要，文件字节哈希由各 manifest 和检查记录单独保存。

## 使用与范围

[跨平台运行手册](../../development/cross_platform_runbook.md)给出 Windows/Mac 环境配置、全量或定向单元测试、`--case-id` 单输入诊断和独立重算命令。当前原生入口为 `run_host_stability.py` 与 `run_input_suite.py`，统一论文协议版本为 `unified_input_suite_run_v2`。历史 week11/week12 执行器保留其原 POSIX 环境语义；相关合成测试已经可以在 Windows 运行。

这是一轮预先选择的 10 输入、3 个连续会话的环境诊断，全部标记 `performance_eligible=false`。没有启动 302 输入的新正式采样，没有创建或代填作者数学审阅收据；原正式数据和门槛中需要真实审阅的部分保持有效。单输入重跑保存为新的独立档案，不能拼接成一次正式完整会话。
