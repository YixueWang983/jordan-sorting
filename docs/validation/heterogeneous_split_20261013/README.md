# 真实 heterogeneous split / adopt 与交错更新

本增量基于 `f0c4e1d9befcb4561dd491a57636ffd828a93bf1`，范围为 **部分操作验证**。实现位于 [split machinery](../../../src/heterogeneous_finger_split.py) 与 [后端](../../../src/heterogeneous_finger_backend.py)。没有使用第三方实现源码，没有普通列表兜底；未修改共享核心、论文、正式输入或历史实验。`sorting_ready=False` 保持，尚不满足 10 月 15 日的完整排序中非零真实 split 检查点。

## 实际实现

- 从两端 fingers 交错上行定位较近的 rib 分支；将选中组件的边界指针临时转为向下，沿搜索路径拆解、按黑高拼接。没有转换/复制整棵树的所有节点。
- 大侧余树保留 heterogeneous 表示。删除一个 rib 父节点后独立处理黑高短缺：传播、红兄弟、近侧与远侧旋转。内部组件的 join 有四种红红修复；只有最终在外侧 rib 插入等黑高黑子树的红连接点时复用端插修复。
- 上行时累计 rib 的朝内 `span`，大侧大小用原 header 总数减去选中组件大小；向下组件使用完整 `span`，拼接相加，局部旋转更新局部值。两个输出 header 的大小之和另作常数项检查。没有切完后遍历输出求大小。
- 原有内部连接节点被复用；非空两侧分裂退役一个内部节点，空侧分裂不退役节点。所有叶、PairHandle、PairRecord 和已有 child groups 保留。旧 list ID 退役，只新建非空输出 header，清理旧两端、设置新两端引用。
- `split_value` 采用 key 的 `<= / >` 语义，留下必须 `adopt_split` 的中间状态；其间其他更新、header 查询及完整审计被拒绝。Jordan 组合入口 `split_pairs_at_value` 还用两个输出端点拒绝切在区间内部或端点上。失败后丢弃状态，未增加回滚。
- adopt 只修改输出 header 的 owner、旧 owner 与新 parent 的至多两个 slots。获得侧首尾区间的严格包含条件，加上既有 owner 边的严格包含关系，排除循环；不爬祖先链，不逐叶重绑。新 parent 已有 child group 时保留它并检查接入后的两个 group。

## 显式阶段前置与接入限制

首轮 make/insert 对两个 child groups 强制互不相交；这个完整森林条件不适用于新 parent 已插入、但尚未取得另一 group 中子项的中间状态。本轮增加 **可选 keyword `transfer_from=source_list_id`**，用于 make/端插新 parent。它只放行与指定另一 group 的暂时重叠，要求相同 owner；新 parent 仍须全新、同 family、在自身列表内端插合法、严格位于 owner 内。原来不传 keyword 的调用及其错误测试保持严格行为。

后端记录 `(new_parent, source_header)`，强制接下来的 split/adopt 消费对应 source 和 parent；完整审计及完整快照拒绝未结束的转移。测试通过这个真实入口构造阶段中间态，没有直接写 registry 或伪造 pair/叶来绕过检查。可以在获得侧既有 pair 下保留子孙，也可在阶段中给新 parent 建立一个不与获得侧冲突的 child group。

**这尚未接入 Step 3(a)/(b)。** 下一步必须在真实调用中核实同 owner 的适用范围、确定 source 的时机及 checked/replay 的阶段审计边界，并接通该前置；不能只把 `sorting_ready` 改为 true。若实际调用超过这里的前置，应实现并验证对应情形，不能静默降级。

对于空 acquisition，adopt 需要“新 parent 已明确位于 source 外”的局部见证：已记录的 transfer parent，或另一个 live header 的有效端点。没有见证的任意内部 parent 会明确拒绝。这是当前操作入口的限制；并非已经通过更宽泛的通用容器契约。非空 acquisition 的严格包含检查本身排除 source 内的 parent 及获得侧后代。

## 本轮验证

[真实操作测试日志](development_tests.log)：**53 个方法，0 跳过**（原 make/insert 31 个，新增 split/adopt 22 个）。包括：

- singleton、空侧、大小 2–32 的全部断点 × 三种建树历史 × 两种获得侧，共 3,348 个 split/adopt 子案例；128 条七次左右插入历史的全部非空断点；257 项的极不均衡与不同断点。
- 分裂后两侧继续左右插入，再分裂、再次插入；重复嵌套分裂、已有 child/grandchild 保留、原 parent 与新 parent 的 slots、稳定叶对象、退役 ID 和失效端点。
- 真实红黑、rib、separator、rank、span、header size 不变量；近侧删除修复及其结构镜像；内部 join 两子项均红时的右侧红红冲突回归；upper/lower family 与曲线端点反向。
- 禁止正常路径枚举三个 registry、物化或调用完整审计后仍可 split/adopt；非法几何、错误 family、源 owner、输出 ID、parent、重复 adopt、缺少中间状态与错误注入均拒绝。
- minimal 与 counters-only 在这些操作上的逻辑/物理快照一致；计数对象不继承普通列表的复制量。二者的详细 WorkLedger 均仍开启，这不是无记账运行的验证。

[原有核心回归](core_regression.log)：**173 个方法，0 跳过**；对象仍为普通生产后端和原路由夹具，不能算真实树端到端排序。合计 226 个不同测试方法。没有复跑完整仓库、原 16 例资格探测、论文构建或抽象适配器的严格完整契约验收。

## 成本记录及未闭合的界

`metrics_schema=heterogeneous-record-access-v2`。除原 record 读写、几何/key 比较、旋转、重着色和分配，增加组件记录、路径栈项、节点退役、size/rank 写入、搜索与各种修复步数。更新分为 `search / detach / join / rebalance / ownership / other`，逐字段求和等于该次操作。size/rank 写入是 metadata 写入的子集，不能相加当作互不重叠的成本。独立查询、完整审计继续另记 bucket。

[探测程序](../../../experiments/probe_heterogeneous_split.py) 保存 15 条固定的小型操作历史、375 条逐操作记录，含 45 次非零真实 split（每条历史三次）。12 条以 32/128 项、三个断点和两种获得侧组成，另三条触发删除修复。每次完成的 split/adopt 或端插后，对照独立序列并检查完整结构。初始建树计数作为 baseline 单独保存，逐操作原始记录从 baseline 之后开始；重算的是账本增量，不混称包含初始化的排序成本。

以下数值是每条历史内 **三次 split 的合计**，不包括生成 parent 与八次端插：

| 历史 | 节点字段访问 | 旋转 | 重着色 | size 写入 | 树节点新分配 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 32 / 首断点 1 / left / seed39 | 691 | 0 | 9 | 80 | 0 |
| 32 / 首断点 16 / left / seed39 | 1,179 | 0 | 19 | 124 | 0 |
| 128 / 首断点 64 / left / seed39 | 1,893 | 0 | 29 | 191 | 0 |
| 5 / 首断点 4 / left / seed1 | 393 | 1 | 4 | 47 | 0 |
| 7 / 首断点 6 / left / seed2 | 426 | 1 | 9 | 51 | 0 |

0 树节点分配不等于 0 分配：新 header、临时组件与 slots 均有记录。节点访问按字段读写累计，包含重复访问；不是不同节点数。分配不统计解释器全部临时对象/字节，dict 扩容、GC 和记账开销未换算成 CPU 指令。详细记账仍始终开启，不能据此做与普通列表的正式性能比较。

实际额外成本公开保留：根附近删除修复会沿另一条 rib 找 outward child（`rib_child`），并非 O(1) 查询；组件边界方向转换与逐段 join、根黑化也按实际步数记账。这些没有扫描所有叶，但 **它们与文献势能的完整摊还论证尚未闭合**，不能把目标 `O(log(min(k,n-k)+2))` 或整体线性界直接写成已证成的代码复杂度。共享核心的实际费用也未纳入本操作归档。

[summary.json](summary.json) 与 [原始 JSONL gzip](operation_work.jsonl.gz) 包含上述全部历史；[verification.json](verification.json) 绑定源码/日志哈希、运行命令及独立解压求和结果。旧 make/insert 归档保持原样，不能跨 v1/v2 schema 混加。

复跑（输出目录须不存在）：

```sh
PYTHONPATH=src:tests python3 -m unittest test_heterogeneous_finger_backend test_heterogeneous_finger_split -v
python3 experiments/probe_heterogeneous_split.py --output-dir /tmp/jordan-split-work-new
```
