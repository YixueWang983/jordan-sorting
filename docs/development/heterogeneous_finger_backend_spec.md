# 原论文方向的 sibling-list 后端规格（2026-09-21，尚未实现）

## 来源与核实边界

主要依据是仓库 `docs/papers/simplified_linear_jordan_sorting.pdf`，Fung–Nicholl–Tarjan–Van Wyk，IPL 35 (1990), 85–92；扫描版实际逐页读取，重点 §2 pp.87–89、§3 pp.90–91。1986 年 `docs/papers/finger_search_trees_jordan_sorting.pdf` 是 Hoffmann 等的 level-linked search trees 论文，作为背景，不能与 1990 结构混称。项目 thesis 是重构说明，不是原文证据。

沿 1990 的引用 [12] 读取了 Tarjan–Van Wyk (1988) 的 Appendix pp.171–175、Fig.19–22：[原文扫描件（大学课程镜像）](https://www.ibr.cs.tu-bs.de/courses/ws2324/ag/papers/Ch5/Tarjan-vanWyk_1988.pdf)，[出版社书目](https://doi.org/10.1137/0217010)。它给出外部节点存 item、内部节点存分隔 key 的红黑树；两端路径反向指针与两端 fingers；自两端交错搜索、局部重平衡、沿搜索路径拆解并拼接子树。不能用普通根搜索的红黑树直接替代。附录把 split 的进一步分析指向 Mehlhorn (1984), pp.214–216；本轮没有取得该书对应页。已读取官方 [Erratum p.1061](https://epubs.siam.org/doi/epdf/10.1137/0217067)：原 pp.175–176 的 Fig.22 与 Fig.23 图像互换了；实现必须用勘误后的 heterogeneous Fig.22，而不是原排错的图。Mehlhorn 对应页仍是下一轮操作界核实入口，不能声称整条证明依赖已经复核完毕。

## 原文操作契约与成本

以下界来自 1990 §3，不是当前 Python 代码的界。令输入列表长度为 l，输出长度为 k、l-k。

| 操作 | 前置与后置条件 | 原文成本 |
| --- | --- | --- |
| make-list(x) | x 为新 item；返回只有 x 的列表 | 摊还 O(1) |
| insert(x,y) | y 已在某列表；x<y 时 y 必须为首项，插至最前；x>y 时 y 必须为末项，插至最后；保持严格顺序 | 摊还 O(1) |
| split(x,L) | L 有序；输出 <=x 与 >x 两列表，允许一边为空；集合守恒且顺序不变 | 摊还 O(log(min(k,l-k)+2)) |

原文不是说每次 split 的实际耗时恒定。§3 使用列表势能 c(l-log₂l)，空列表不计势能；非空两边的 split 用势能下降支付搜索代价。加上创建和边界插入，对**初始无列表、仅这三种操作**的 m 次序列得到总 O(m)。这是第二层摊还论证；任意已有大树、额外全局扫描或任意中间插入不自动满足该结论。平衡树内部 join 是 split 的实现工具，不是给上层添加任意拼接操作。

## 目标表示与接口（工程规格，不冒充原文逐字实现）

选择上述附录的 **heterogeneous red-black finger search tree**。外部叶保存稳定 PairHandle；内部节点保存 key、颜色、局部黑高/必要大小信息；两端 ribs 按原文反向，非 ribs 沿子树向下。TreeHandle 保存两端 leaf fingers 和大小；空树用 None。具体旋转必须同步 rib 身份、key、端点和黑高，不能每次遍历树重建元数据。首轮不添加位置查询、secondary heap、任意 finger 或 persistent 操作。

PairHandle 保留曲线身份、两端点引用和 upper/lower family。几何 left/right 通过端点值比较获取，不把曲线第二点当成几何右端点。item 排序用几何左端点；同一 sibling list 区间互不相交，因此与右端点顺序一致。输入必须满足算法认证前提；split_by_value 用新点值找断点，跨区间等非法情况在诊断路径审计，核心不得接收 oracle 排名或 expected output。

最小接口：

| 接口 | 必须做到 |
| --- | --- |
| make_list(pair, owner) -> ListHandle | pair 新建且未归属；在 owner 的最多两个 child slots 中接入 singleton |
| boundary_list(pair, side) -> ListHandle | 仅供 locality lemma 保证的首/末 pair；经端点反向引用 O(1) 找所属列表，无全树搜索 |
| insert_boundary(new, anchor, side) | anchor 正是指定端；比较新端点，插入并维护两端引用 |
| split_value(list, value) -> (left,right) | 退役旧 handle，返回两个可空 handle；不移动/复制全部 leaves |
| adopt_split(old_owner,new_parent,left,right,acquired_side) | 常数个列表 header 与 owner slots 变更；increasing 获得 left，decreasing 获得 right |
| extreme_child(parent, side) -> PairHandle/None | 从至多两个 child lists 取相应端；支持 Step 3(c) 的几何端点选择 |
| materialize_audit() | 遍历生成逻辑 parent/list/顺序视图；仅用于完整 checked/audit，不伪装成常数时间 |

不在当前代码中添加空类或未调用接口。成功的公共排序返回形式保持兼容；后端内部 handle/trace adapter 可以改变，必须另立 schema/version。

## 不能被快 split 掩盖的 ownership 成本

当前每个 PairRecord 都有可直接读的 parent_pair_id 和 sibling_list_id；split 两侧逐 pair 重绑，即使树切分快，这一步仍为 O(l)。不能使用旧字段并只把扫描挪到下一次 owner 查询。

拟议改变：列表 header 是该组 membership 的权威表示，保存 owner；pair 只保留 child-list slots 及作为列表首/末项时的边界反向引用。两端各至多一个 live header 引用（singleton 两端指同一 header）。split 清理旧两端引用、设置至多四个新两端引用、更新旧 owner/new parent 的常数个 slots；内部 pairs 不逐项写 parent/list。逻辑 owner 是所在树 header 的 owner，而不是每片叶上的缓存。

关键前置条件：1990 p.89 locality 保证 Step 3(a) 的非 enclosing anchor 在列表末端（镜像为首端），Step 3(b) 的 boundary 在首端（镜像为末端）。只有这些查询使用 boundary_list。enclosing 分支直接使用该 pair 自己的 children slots，不需要查其所在列表。要逐一替换当前 `_validated_boundary_pair`、Step 3(a)/(b)、`_output_anchor_child_pair` 对 eager ownership 字段的访问；任何遗漏的任意内部 pair owner 查询，都必须记录并解决，不能偷偷爬树当 O(1)。本方案尚需用实际访问轨迹验证上述前置条件。

完整审计遍历所有 child lists，建立临时 pair->logical owner 映射，检查单一归属、守恒、包含关系和 cycles；其成本另记。debug API 若允许任意内部 pair 查询，遍历/爬树成本必须公开，禁止放入 minimal 热路径。当前 checked/replay 本轮不变；未来适配同样的逻辑检查，不要求保留每个 eager 字段。

## S_i 与当前实现差异

1990 p.89 对 curve order 和 x-order 均用双向链；四指针加奇偶 bit 即可标识 pair。当前 `partial_sorted_list.py` 已经是双向节点加 point-id 字典，不是每次线性查找的 Python list。邻居和局部插入在既有 handle 下为 O(1)，字典查找是期望 O(1)；最终 output recovery O(n) 必须计时。

下一后端保留这些语义，建议连续 paper_index 对应预分配数组/稳定 PointHandle，避免把字典平均界当确定最坏界。初始化只排序前三点，创建全部 point handles O(n)；禁止预先全局排序。S_i 不需要换成通用序列 finger-tree。

当前普通后端的额外成本：split partition、元组/list 复制、stale-plan 对照、两侧 ownership 重绑、局部 conservation/postcondition 扫描均 O(l)；边界插入还有列表移位/复制及校验；cycle 检查沿 parent 链；checked 的全局 invariant 与每前缀 replay 更重。去掉 rollback 只去掉恢复备份，不改变这些界。保留的 SplitPlan 仍承担边界计算、stale-plan 防护和结果守恒职责。

## 实施顺序与验收门槛

1. 入口：本规格 + 1990 §3 + 1988 Appendix，取得 Mehlhorn 对应 split 分析，使用已核实的 erratum 图；补全镜像 ribs/旋转规则和成本账本。先做 small operation-sequence tests，与普通列表的数学模型逐步对照，涵盖空边、端插、重复 split、每种重平衡和稳定 handles。
2. 新增 `src/heterogeneous_finger_backend.py` 的真实节点/边界插入/split；每个 operation 实测节点访问、比较、旋转、元数据写入、分配数。不使用 treap 冒名，不做整树 rebuild。先证明实现语义，尚不宣称线性总界。
3. `paper_jordan.py` 接入 backend factory 与上述 owner adapter；`partial_sorted_list.py` 核对稳定 handles；policy 只控制原有诊断区别。Step 1/2、3(a)/(b)/(c)、镜像、几何端点、两个独立 z1 修正的规则保持。现有端点和 z1 executable clarification 不冒充 1990 原文已逐字给出。
4. 小规模有界穷举、所有边界/ownership 回归、两后端各自与外部 sorted 比较；replay 保持 same-core 身份。用本轮冻结输入做后端差分，不能以两个后端相同错误作为通过。
5. 再跑同输入、同环境、同 minimal 范围的普通列表/finger-tree 匹配计时。操作账本覆盖 owner 查询、S_i、初始化、输出、registry，证明目标必须包括所有实际工作。证明缺口与常数成本分别报告；导师没有要求本阶段完成整条线性定理。
