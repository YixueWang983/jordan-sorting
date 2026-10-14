# 超时保存、证明范围修订与开发性 pilot（2026-10-14）

审核基线：`29c1af83ef4e2ea2a7b5b39ef9767e3e5c6294dd`。
本轮不改变 `src/`、论文或历史数据，不把人工论证／开发性 pilot 当作最低交付验收。

## 修复与回归

`validate_finger_refinement.py` 的新归档格式为 `finger_refinement_records_v2`：
每例独立写入 `records/NNNNNN.json.gz`，完成压缩、关闭、文件同步后原子重命名，
然后同步目录。`progress.json` 在开始每例前原子记录当前输入。强制终止时父进程
等待 worker 退出，再独立读取已提交记录并写 failure；不依赖子进程 finally。
临时 `.partial` 文件不是已提交记录，不需要解压／拼接截断的 gzip 流。
即使 worker 刚写完成功汇总，超时仍覆盖其成功标志。

该保证针对可写本地文件系统上的进程终止；I/O 故障继续向外传播，不声称硬件
断电恢复或分布式存储保证。`committed_records.py` 为 refinement 与本次 pilot
共用同一小型提交机制，不更改旧 v2 synthetic fixture 的协议。

24 项测试通过、0 跳过：7 项审核回归、8 项 pilot 流程测试、9 项已有 refinement
测试。机械超时测试使用明确的非排序替身，实际启动并终止 Python 子进程：
第二例／首个 warmup 阻塞时，先前完整记录仍可读取，当前 action 可恢复。
还有普通异常、未提交临时文件和“成功汇总刚写出就超时”的回归。
这些机械测试不算生产排序正确性案例或性能测量。旧 80 项回归本轮未另行重跑。

两个证明反例分别由真实 oracle／共享核心、真实 `locate_component` 与 tree split
检查，已明确：y 可在有限 parent 内但不在其直接 children 内；选中的组件可整块
位于切值一侧而无相等 key。
[证明草稿](../../development/heterogeneous_representation_locality_20261014.md)还按原文
印刷 p.88 图3–4明确了 child 分支引理的条件、具体 gap、辅助截弧、两个旧端点
及旧曲线段，单列有限 parent 最新时的补充论证。人工论证仍待审阅。

旧 `finger_refinement_20261014/` 的 694 例正常完成归档保持原样，绑定旧提交；
没有改装为新格式，也没有重跑该独立批次。已有9项测试内部的小规模穷举不是
一次新的扩展资格批次。

## 固定的 pilot 协议

实际执行前将 `preselected_plan.json` 和源码提交。固定8个输入：32/33/128/129
各两个方向；k 分别为3/3/7/19。k是生成构造参数，未用计时结果选择输入。

- 独立身份 `development_backend_pilot_v1`，真实 `perf_counter_ns`，始终
  `performance_eligible=False`。旧 synthetic tick 文件未修改。
- 所有输入先经合法性检查；两后端分别执行 checked 输出／结构和同配置 replay
  检查，要求 processed_count 是等于输入长度的整数。全部16次 preflight 完成
  后才进入 warmup 与测量。这不是最终比较集的资格认证。
- minimal；树显式 `detailed_work=False`。每次公开排序都建立新状态；初始化、
  主循环、输出恢复在计时内。批量循环与输出列表 append 也在计时内并如实披露；
  oracle、expected 比较、GC预清理、压缩和 fsync 在计时外。
- GC 在排序内保持开启，每批前统一 gc.collect。每后端每输入2次 warmup；
  批量1/4/16各3次重复。按输入／批量档／轮次交替先运行的后端。
- 最多180秒，首个被检测到的错误停止；批量输出在计时结束后检查，因此错误
  输出的检测可能发生在整批调用完成后。不删除失败输入、不换例、不重试。
- 共计划192条提交记录：16条 preflight、32条 warmup、144个 sample batches；
  sample 内共1,008次公开排序调用。批内调用不是独立统计样本。

本轮执行期间不并行运行开发测试或 checked 审计。常规操作系统后台活动未隔离；
逐条落盘虽在计时外，仍可能影响批次之间的机器状态。pilot 仅用于检查粒度和
协议可执行性，不能据此给出后端优劣或理论复杂度结论。

## 复跑入口

```sh
PYTHONPATH=src:tests:experiments python3 -m unittest \
  test_finger_review_hardening test_development_backend_pilot test_finger_refinement -v
python3 experiments/development_backend_pilot.py --output /tmp/jordan-development-pilot-new
python3 experiments/validate_development_backend_pilot.py /tmp/jordan-development-pilot-new
```

输出目录必须不存在。成功归档的验证器独立重建完整 action 顺序、逐次输出、
样本数和分组统计，并验证配置、源码、环境、文件集合和哈希。超时或失败归档
返回恢复到的提交前缀，绝不返回计时资格；完整成功才检查最终 manifest。
实际执行结果在下一次归档提交中补入本目录，不在源码冻结时预写通过结论。
