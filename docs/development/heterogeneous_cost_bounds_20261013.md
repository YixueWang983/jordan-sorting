# 真实指尖后端：保守成本分析基线

基线 `d6622ce976b8b71d3dbe23618606d6d471e32069` 加本次详细记账开关改动；精确源码身份绑定于 [验证归档](../validation/heterogeneous_work_modes_20261013/README.md) 的 `structural_campaign/provenance.json`。本文是源码循环范围的条件性上界分析，不是完整正确性证明，也不把文献目标界当作已经实现的界。本轮没有重新核实文献的完整摊还证明。

## 模型与前提

令一次操作的源列表有 `m` 片叶；`H` 为操作中参与处理的树、子树和暂时修复路径的最大高度，singleton 取至少 1。计算字段读写、比较、常数大小对象创建和指针调整；key 比较及大小/索引算术按单位成本计，Python 字典使用期望查找与摊还扩容成本。不把这些假设写成 Python 任意大整数、自定义比较器、内存分配或墙钟时间的确定最坏界。

分析以成功操作的结构契约为前提：输入满足红黑、rib、几何顺序与 owner slots 不变量；拆解保留完整子树；修复的暂时冲突沿单条路径传播。完成的红黑树若黑高为 `b`，每条路径具有相同黑高、没有相邻红节点，所以至少有指数于 `b` 的叶数，路径长度至多 `2b+O(1)`，即 `O(log(m+1))`。拆下的子树不高于源树；`join_down` 先黑化两个输入根，其结果黑高至多比**黑化后的**较大输入黑高加一。相对黑化前的输入则至多加二，不能直接写成加一。`split_down` 只有源路径长度个 join，因此即使逐次支付这个常数增量，中间高度仍为 `O(log(m+1))`。删除/端插修复只有沿路径的局部冲突，不另造线性高的链。

**10-14 补正与进展：** 上述基准修正由真实红根反例支持。[后续引理](heterogeneous_cost_lemmas_20261014.md)给出了相邻 join 的 rank 累计、根附近 rib 行走收费及 mixed 操作的统一势能推导。下表保留 10-13 的宽松上界和当时的未闭合状态，不再将它误作目前分析的唯一进展；新推导仍以操作契约和局部修复为前提。

这说明如何从 `H` 界推到对数界，但仍依赖这些局部修复保持契约；有界结构测试没有证明其对所有输入都成立。下面先明确每个真实循环按 `H` 能支付什么。

## 正常操作与实际循环

函数位置以名称索引，避免后续行号漂移。树操作在 `src/heterogeneous_finger_backend.py`，split 助手在 `src/heterogeneous_finger_split.py`。

| 操作/函数 | 访问范围及为什么有限 | 当前可支持的保守结构成本 |
| --- | --- | --- |
| `register_pair`、`make_list` | 常数个对象、字段和 registry 操作；owner 至多两个 slots；新 item 无 child | `O(1)` |
| `validate_live_pair`、`boundary_list`、`list_owner/size`、`extreme_child` | 稳定 handle、指定端点、header 和至多两个 slots；`_owner_slots` 的重复调用也是有界常数次；不求任意内部 item 的 owner | `O(1)` |
| `insert_boundary` / `_repair_insert` | 创建叶与一个 connector；一次修复要么常数次旋转后返回，要么令 `node=grand` 严格向上；至多 `O(H)` 次 | `O(H)`，尚不声称混合操作序列中摊还 `O(1)` |
| `locate_component` | 左右位置交错，每次相应位置严格移到 parent；到根即返回。两边各至多 `H` 步 | `O(H)`；没有因此证明整个 split 的较小侧敏感界 |
| `unreverse`、`expose`、`rooted_component`、`fingers` | 每条循环单向经过一条 extremal path；各封装只调用常数条路径 | 每次 `O(H)`；不遍历组件内部全部叶 |
| `join_down` | `combine` 每层只递归到一个 child；回溯做固定种类的旋转/重着色与 `refresh_down` | 每次 `O(H)` |
| `split_down` | 向下保存至多 `H` 个 frame；回溯每个 frame 最多一次 `join_down`。这里暂不假定相邻 join 的代价抵消 | `O(H²)` |
| `rib_child` | 从另一端 finger 向上找到目标 child，严格沿 rib 行走 | 每次 `O(H)`，不是常数查询 |
| `repair_short` | 传播分支令 `short=parent`；红兄弟处理后继续本轮，近/远旋转分支本轮结束。最多 `O(H)` 轮，每轮常数次 `sibling_children`，其中可含 `rib_child` | 宽松计为 `O(H²)`，明确支付另一 rib 行走 |
| `detach` | 常数条方向转换路径，加至多一次 `repair_short`；整组件留存大侧余树 | `O(H²)` |
| `join_fingers` | 沿大侧 rib 找黑高相等的节点，常数条转换路径；根分支一次 `join_down`，非根分支一次 `_repair_insert` | `O(H)` |
| `split_value` 的 header 后处理 | 两个输出、固定六个 header 字段、至多四个端点反向引用；检查两个已算大小之和 | 路径处理之外 `O(1)` |
| `adopt_split` | 两个 owner，各至多两个 slots；严格包含与无关成员见证只读端点；保留已有子孙的 handle/leaf | `O(1)`，不逐叶重绑、不做祖先扫描 |

`span` 没有被当作统一 subtree size：内部区域为完整子树大小，rib 为朝内分支大小，root 为零。搜索与拼接沿实际路径累加组件大小，输出 header 取路径结果及源 header 总量。以上循环上界已包括每个所访问节点的 `rank/span` 更新；没有切完后遍历两侧来计数的另一步。

`split()` 依次执行一次双端定位、detach、split_down、常数次 fingers 转换和至多一次 join_fingers；不是这些过程的笛卡尔嵌套。因此一次 split/adopt 的保守上界为 **`O(H²)`**。在上述红黑与修复契约下，对应 **`O(log²(m+1))`**。端点判断得到空侧时不进入拆解，header 退役与 adopt 仍是常数规模。单次辅助存储为 `O(H)`：frame 栈与当前一次 join 的递归栈可以同时存在，但各次 join 顺序执行，不同时保留 `H` 个递归栈。

## 从树操作到完整主循环

`src/paper_jordan.py` 的 `_run_paper_jordan_state_values` 每处理一个新点执行固定的 Step 1/2/3。边界选择及两个 z1 修正只取固定数量邻居与几何字段；转移预检、插入后复核、分裂前复核重复调用接口，但每轮数量有常数界。`_require_next_iteration`、阶段缺失/参数检查用字典索引，不遍历以前的阶段。

`stage_results` 每轮保存固定五项必要结果，总空间 `O(n)`；`minimal` 不记录 trace 和高层工作计数。输出链表的邻居、局部插入是稳定 point ID 到节点的字典访问，最终 `to_list` 才遍历 `O(n)` 点。初始化物化输入/point handles 为 `O(n)`，只排序前三点。树上的 pending fence 是固定两项状态检查；`minimal` 不调用完整森林审计。

因此在同样的有效输入、修复契约和单位成本/字典假设下，可先给出较弱的累计界：

```
O(n) 初始化、阶段状态、核心查询与输出恢复
  + Σinsert O(log(m_i+1))
  + Σsplit  O(log²(m_i+1))
  ⊆ O(n log²(n+1)).
```

这不是文献的线性界，也不保证跑赢普通列表或 Python `sorted`。树、handles、headers、输出链与阶段状态的总持久空间为 `O(n)`；退役 header 不留在 live registry，必要阶段结果保存 ID。完整审计、逻辑/物理快照、外部几何模型、oracle 与 replay 不在以上 `minimal` 正常排序界内。普通列表的成员与祖先扫描不能套用这张树成本表。

## 开关后的记账与剩余成本

`detailed_work=False` 不分配字段 bucket/phase 字典，不逐字段累计读写，不建立操作前快照、phase 快照或 `last_operation` 报告，也不进入计数用 generator context。`WorkLedger.snapshot()` 在关闭时明确拒绝，不能把“未测量”表示为零工作。replay 从同一不可变 spec 新建相同配置后端；运行期私自更改配置会被审计拒绝。

开关仍有成本：`_Tracked` 的属性包装、字段集合判断和 enabled 检查保留；显式 `add/allocate` 调用在关闭时直接返回；若代码显式使用 phase，上下文使用共享 `nullcontext`；操作/phase 装饰器保留分支与调用层。没有复制一套算法来追求零开销。详细计数开启时，固定字段集合和固定 phase 数使快照相对 `m` 是常数规模，但 Python 常数开销可能很大。

高层 `SplitWork` 与详细账本独立：只有 `count_operations=True` 才建立两个 split 局部整数累计比较和叶检查，得到原四字段报告；`minimal` 没有这两个累计器。tree 的 `metrics_schema` 保持原含义，开关前后 trace、metrics 和阶段状态必须相同。树账本只覆盖树操作及被追踪字段，**仍不是整个 Python 主循环的完整工作量计数**。

## 10-13 尚未闭合的目标（历史清单）

1. 将 `split_down` 的逐段 join 代价收紧，需要证明 rank 差或势能如何在相邻 join 间累计；当前表直接按每次 `O(H)` 支付。
2. 将 `repair_short` 中另一 rib 行走与组件转换、根处理收紧到较小侧敏感界，需要明确收费或势能来源；目前按 `O(H²)` 支付，未声称已完成该对应。
3. mixed make/insert/split 序列中的端插摊还常数界、完整 split 的 `O(log(min(k,m-k)+2))` 界仍待闭合。没有先得到这些结构操作界，就不能直接套第二层列表势能来推出整次 Jordan Sorting 线性。
4. 所有合法输入的 locality 与局部修复保持不变量仍需一般性论证；定向大结构验证只补覆盖。
5. 正式比较仍需最终源码下的共同输入资格、runner/validator/pilot 与冻结计时协议。无详细记账路径解除一项阻塞，不等于整个高效后端最低交付或正式计时获准。

10-14 对 1–3 的具体推导及 4 的剩余 gap/locality 归纳义务见[新引理第 2–6 节](heterogeneous_cost_lemmas_20261014.md)。第 5 项只推进到合成 tick 的机械 runner/validator 夹具，尚无实际计时或最终输入资格。
