# 反向指针表示保持与 Jordan 分组归纳

后续集中审阅见 [2026-10-15逐项结案](finger_final_review_20261015.md)。以下保留原写作时点的状态；新结论和计算模型以该审阅为准。

状态注（2026-10-15）：下文基线状态保留。8例开发性pilot已在 `1ae75aa` 执行并
于 `b87e043` 归档；[最终共同资格尝试](../validation/common_qualification_20261015/README.md)
因树checked/replay资源超时而未通过。本文仍为待审阅人工论证，`timing_ready=False`。

分析基线：`6c259a8` 的 `src/paper_jordan.py`、
`src/heterogeneous_finger_backend.py` 和 `src/heterogeneous_finger_split.py`。
本轮未改生产算法；源码身份和有界反例搜索见
[验证记录](../validation/finger_refinement_20261014/README.md)。

本文给出人工的表示保持论证和合法调用归纳，不是机器检查的形式化证明。
它补充[源码成本引理](heterogeneous_cost_lemmas_20261014.md)所依赖的两个前提。
成本模型仍要求严格全序、单位成本比较和期望／摊还字典操作；checked 审计、
replay、这里的 ghost model 不属于 minimal 排序成本。正式共同输入资格和实际
计时 pilot 尚未完成，`timing_ready=False` 不变。

## 1. 两种 family 与论证范围

代码的 `family=UPPER/LOWER` 是边的颜色；本文称之为“颜色”。原论文的 family
是一个 parent 与它的直接 children；下文称“parent family”，不能混为一谈。
`P_i=(z_{i-1},z_i)`，偶数 i 为 upper，奇数 i 为 lower；同色区间严格包含或
不交。各色另有一个 dummy owner。

合法输入指 distinct、可一致比较的值，且两色区间各自 laminar，与仓库 oracle
的数学判据一致；不覆盖 NaN、不一致比较器或比较过程中修改状态的对象。
这些区间可在各自半平面画成嵌套／不交的弧；同色边无共同端点，异色边只在
相邻输入点相接，故输入序列表示一条简单开曲线。论证不额外假设输入已经闭合。

物理保持部分的起点是一个满足操作契约的逻辑红黑森林；算法部分再说明实际
Jordan 调用为何满足契约。两者不能循环地用“后端没有报错”作依据。

## 2. 从物理对象到逻辑树的映射 D

每张非空 list 对应一棵外部叶存 pair、内部节点存分隔键的满二叉树。
内部节点的 `key=max(left leaves)`；叶键为 pair.low。叶按键递增且 pair 区间
互不相交。外部叶黑、rank=0；内部节点两孩子 rank 相等，
`rank=child.rank+[node is black]`；红节点孩子黑，完整树根黑。

D 先从两个 finger 沿反向边到根，记下每个节点的逻辑外侧孩子，再按下表解码。
根的两个 top 缓存必须与这两条链给出的孩子相同；缓存不能作为独立的真实性依据。

| 物理 role | 逻辑 left / right | 存储的 span |
| --- | --- | --- |
| ROOT 内部节点 | 两条反向链最后一条边的孩子；等于 header.left_top/right_top | 0 |
| LEFT rib | 从 left finger 上行的下一个反向孩子 / node.right | 右侧 inward 子树叶数 |
| RIGHT rib | node.left / 从 right finger 上行的下一个反向孩子 | 左侧 inward 子树叶数 |
| INTERIOR | node.left / node.right | 完整子树叶数 |
| 外部叶 | 无逻辑孩子；rib 指针可指向 parent | 1 |

左右 rib 除根外不交，其他节点都是 INTERIOR。两条反向链无环、到达同一个根；
逻辑遍历无重复节点。header.size 是整树叶数，两个 fingers 是极端叶。
单叶树的同一叶兼任根和两个 fingers，两个 top 均为空。

PairHandle、PairRecord、ExternalLeaf 的身份在移动已有 pair 时不变。
每片叶的 handle.leaf 指回它；只有列表首／尾 handle 的相应 boundary 槽指向
该 live header。内部叶不保存逐项 owner，归属由所属 header.owner 决定。
owner.child_slots 有序、无空列表、至多两个。完整状态下所有注册叶恰好属于一张
live list，所有内部节点也恰好可达一次。

## 3. 方向转换：D 下的恒等变换

`expose(root,parent,side)` 只走给定组件的外侧路径。每步先保存原外侧孩子，
再把该指针反转到 parent；另一指针不动，span 改为 inward 子树原有的完整 span。
因此循环不变量是：已经反转的路径和未处理的向下余树解码后，仍为原来的逻辑
组件；未改的 inward 树保持全部字段。到叶时返回的就是原极端叶，没有新建叶。

`unreverse(finger,top,side)` 反向执行：先保存 above，把当前外侧槽改成已处理
的 below，再用两个完整子树 span 求和并刷新 rank。归纳得到从 finger 到 top
以下的同一逻辑树。它不处理 top，调用者负责最终连接，避免把 top 的 up 指针
误当孩子。

`rooted_component` 的三种出口分别处理叶、非根 rib top、全树 root。非根只解开
一条路径；根解开两条路径。设置 top.span=size 合法的依据是下面的路径大小
归纳，不是声称原 span 本来就是总大小。`fingers` 反向建立两条路径、top 缓存和
根角色。唯一有意改变的逻辑字段是根黑化；若原根红，rank 增一，其余树不变。

由此，先规范化根颜色后有 `D(fingers(T))=T`；再 rooted_component 得到同一逻辑
形状、节点身份、分隔键、rank 和完整子树大小。探测覆盖包括红根组件，比较前
显式支付／实施这次根黑化，不把它遗漏。

## 4. 局部旋转怎样落实到四种物理角色

以下括号表示逻辑内部节点。左右镜像交换 left/right、LEFT/RIGHT 和 top 缓存，
所有等式相同。

### 4.1 外侧插入修复 `_rotate_outward`

左侧情形是 `G(P(C,M),F) -> P(C,G(M,F))`。旧 P、C 红，G 黑，uncle F 黑。
旋转后 P 黑、G 红，C 不变。M、F 与 C 的 rank 相同；因此 G 的新 rank 等于
M.rank，P.rank=G.rank+1，等于旧 G 的 rank。消除这一处红红，边界黑高不变。

分隔键无需重新搜索：G.key 旋转前是 `max(P)=max(M)`，旋转后仍是 `max(M)`；
P.key 原来和后来都是 `max(C)`。叶序 `C,M,F` 不变。

- G 非根：G 离开 rib，成为向下的 `INTERIOR(M,F)`，span 为两者之和；
  P 仍在同一 rib，up 指向旧 above，inward 指向 G，span=G.span。
  C 的 up 本来就是 P；above 在 root 时只更新相应 top。
- G 是根：P 成为 ROOT，根指针置空、span=0；G 进入对侧 rib，up=P，
  inward=M，span=M.span；top 改为 C/G。F 在对侧 rib 的反向 parent 本来
  就是 G，无需扫另一条 rib。原 fingers 仍是同一极端叶。

`_repair_insert` 的另一分支是黑 G 的两个红孩子同时黑化、G 红化。
孩子 rank 各增一，G.rank 不变；只有 G 与其 parent 可能新出现红红。
循环上移 G，最终根黑化或上述旋转，因而终止且恢复红黑性质。
端插产生的连接节点在外侧 rib 上且两个孩子黑、等 rank；`join_fingers` 非根
拼接也明确满足这项前提，才允许复用此修复。

### 4.2 向下组件旋转 `rotate_down/balance_down`

这段只处理 INTERIOR 组件，不可直接处理反向指针。普通左旋
`A(X,B(Y,Z)) -> B(A(X,Y),Z)` 保持叶序 X,Y,Z；A.key=max(X)、B.key=max(Y)
都不变。`refresh_down` 自下而上重算完整 span 和 rank。
四个黑／红／红位置分别归约成中间根红、两孩子黑的同一形式；内部情形先旋
红孩子，再旋黑祖父。三个挂接子树（内部情形为四段）原等黑高，因此旋转加
重着色后等黑高、无内部红红；这些**黑根修复分支**的返回根可在调用者处引发冲突。
2026-10-16补正：红根不进入四分支，可能透传一条根—孩子红红连接，
须由原黑父在回溯时修复；顶层预先黑化输入保证不会以该暂态收尾。
完整递归契约及其成本依赖以[集中审阅 R3/C1/C2](finger_final_review_20261015.md)
为准。最后根黑化不能独自修复内部红红。旧归档仍绑定其原文版本。

### 4.3 删除短缺 `repair_short`

循环不变量：逻辑树和叶序完整；short 外侧组件少一个黑层，只有它与兄弟的
rank 可能相差一，其余子树已合法。记 short 实际 rank 为 r。兄弟不能是叶：
兄弟 rank 为 r+1；因此读取 near/far 有定义。

| 分支 | 逻辑变化与 rank 结果 |
| --- | --- |
| 红 sibling | parent 必黑，sibling 黑化、parent 红化后向 short 侧旋转；原 sibling 的两个孩子黑，短缺留在原 parent 下，新的 sibling 黑 |
| 黑 sibling，near/far 都黑 | sibling 红化降一 rank；若 parent 红，parent 黑化吸收短缺；否则 parent.rank 减一，short 上移 parent |
| 黑 sibling，near 红、far 黑 | near 黑化、sibling 红化并作内旋，保持 sibling 组件 rank，把它化成 far 红情形 |
| 黑 sibling，far 红 | sibling 取 parent 原颜色，parent 和 far 黑化后外旋；新 parent 子树和 far 均为 rank r+1，修复完成 |

外旋在左短缺侧是 `P(S,B(N,F)) -> B(P(S,N),F)`，与 4.1 相反。
`rotate_short_parent` 把 P 设为同侧 rib，inward=N、span=N.span；
B 非根时仍为同侧 rib、inward=F、span=F.span；B 为新根时改两个 top。
S 的 up 原本指 P，F 若在对侧 rib 上其 up 原本指 B，均保留。
key 同样由保持的叶分段决定，无需改值。

near 内旋的 sibling 若为 INTERIOR，就调用向下旋转。若它是根的对侧 rib
顶点，`rotate_near` 将 near 提升到该 rib，旧 sibling 留在其下：旧 sibling 的
inward 改为 middle，near 的 inward 为 inner，二者 span 分别取该分支完整大小，
并更新相应 top。外侧 far 的反向 parent 仍指旧 sibling。
这些赋值就是同一个逻辑内旋的物理编码，不把另一条 rib 当作向下树。

传播严格向根移动，终止旋转次数有界。根收到短缺时允许整体黑高减一，根仍黑。
常数修复／另一 rib 的实际行走费用由成本引理另行支付，正确性不假定它是常数。

## 5. 搜索、分裂与大小守恒

`locate_component` 从每端的单叶组件开始，累计 size=1。每次升到非根 rib
parent，新的逻辑组件恰由旧外侧组件和该 parent 的 inward 分支组成，所以
`size += parent.span`；到根用原 header.size。separator 的序关系保证左端已
越过的组件全在切值左边，右端已越过的组件全在右边。第一次停止时选中组件
可能跨越切口，也可能整块位于切值一侧；不能假定其内部一定发生非空分裂。
其余树完整落在同一输出侧。组件的空侧结果与后续拼接／connector 退役共同
完成分裂，`split_down` 的叶判断始终按 `key <= value` 分配。例如叶键 [4,8]、
separator=4、切值 6 时，右端先停止于组件 [8]，余树 [4]；这里没有相等键。

`detach`：移除选中组件和紧邻 connector，将 sibling 接到 above。原 parent
红时 sibling 黑，移除红 parent 不改黑高；parent 黑而 sibling 红时黑化 sibling
补一层；两者黑时交给短缺修复。根特例的另一输出可独立黑化成根，黑高无需与
已分开的组件一致。rest.size=old.size-component.size，不枚举叶。

`split_down` 的 frame 保存 connector、下降方向、未动 sibling 的大小和最大键。
叶基例按 `<=value` 唯一分配。回溯时只在正确一侧拼接 sibling：下降左则并入
右输出，下降右则并入左输出。不同 frame 的 sibling 不交，与最后叶一起恰为
原叶集。`join_down` 在等黑高黑根处放入红 connector，沿较高侧回溯进行 4.2
的修复；key=left.maximum，size=left.size+right.size，maximum=right.maximum。
空侧只退役 connector，不退役任何叶。归纳得到有序、互斥、集合守恒的两棵树。

`join_fingers` 将小 rank 树与大树近端相同 rank 的黑组件拼接，必能找到：从
黑叶 rank=0 沿 rib 上行，黑节点 rank 逐层增加，且大树根 rank 足够。
根情形使用向下 join；非根红 connector 的 inward span 等于 inside.size，
新大小增加 outside.size，满足 4.1 前提。separator 仍来自左组件 maximum。
因此 split 的所有输出大小来自已有完整大小、路径累加、和／差；不会把 rib.span
当完整子树大小，也不需要事后扫描。

## 6. header、稳定身份与转移阶段

make/端插只创建新 pair 的叶和必要 connector；同表端插保持原 live ID。
原极端叶移到内部时只清理被替换方向的 boundary 槽，另一端未变。旋转和方向
转换均移动引用、不换叶，故旧 PairRecord/PairHandle/leaf 身份保持。

split 完成树操作后退役输入 header，清理两个旧端点引用，为非空输出建立新
header 和相应端点引用；只操作常数个 header/端点。空输出没有 header。
在 adopt 之前 owner slots 仍可能含旧 header，因此该阶段不声称满足完整森林
映射，只允许匹配的消费操作。完整审计拒绝这段状态是预期行为。

adopt 只将 retained 替换旧 owner 槽中的输入，将 acquired 挂到新 parent 并改
其 header.owner。已有叶及其 child_slots 完全保留，所以子孙 family 不变。
两端几何检查加有序不交区间说明 acquired 的所有 pair 均严格在新 parent 内。
严格包含沿 parent 链传递，不可能形成环，否则会推出一个区间严格包含自身。
空 acquired 分支要求新 parent 在 source 外的身份见证，不能凭空推断成员归属。
排序中新 parent 总是本轮新建、原无子项，满足这一更强的前提。

Step 3(a) 可以临时使新 parent 与另组将转移的 children 重叠；pending_transfer
明确限制这个例外。它没有改 source 的 header、叶、两端或 owner，Step 3(b)
仍消费原 live source。adopt 后两种 pending 清除，才允许 Step 3(c) 恢复输出。

## 7. 精确分组不变量 G

在一个完成前缀中，parent 是每个 pair 的同色最小严格包围区间；没有包围区间
时为该色 dummy。children 按区间从左到右排列。对每个 parent family F：

1. 若没有 children，slots 为空。
2. 令 j 为 parent（有限时）与所有直接 children 中最大的 end_index。
3. 若 P_j 就是 parent，所有 children 是一张列表。
4. 否则按 z_j 切为 `high <= z_j` 与 `low >= z_j` 两组，去掉空组，各为一张
   列表，顺序为左、右。P_j 本身在其中一组，不从 child 集合中删除。

这是原论文 p.88 的分组规则。它强于“最多两个有序列表”：在同一 child 集合
上任意选个切口仍可能违反 G。基于输入前缀的 ghost model 独立求最小 parent、
最大 j 和切口；不以生产当前分组、实际成功的 boundary 查询作为预期结果。

## 8. 局部重入引理及 G 如何给出端点

### 8.1 原文命题：最近 pair 是 child

本轮重新查看仓库扫描件印刷 p.88 的完整引理、图3和图4，以及其后的分组规则。
以下将原文的已处理末下标改记 j，邻接端点改记 q，避免与本轮 i 混淆。

- 已处理前缀是 z1..z_j，F 含 P_j=(z_{j-1},z_j) **作为 child**；R 是 F 的区域，
  即同色 parent 弧内、直接 child 弧外的半平面区域，dummy 时无界。
- 取 F 端点中与 z_j 相邻且不等于 z_{j-1} 的 q。这是 z_j 朝 R 一侧的那个
  gap 的另一端；朝 P_j 内侧的 partner 不是该入口。dummy 情形允许 q 为无穷端点。
- 令 z_k 为曲线经过 z_j 后**首次进入仍未改变的 R**的点。则 z_k 位于开 gap
  (z_j,q) 中；或者 parent 是 dummy，z_j 与 z_k 之间严格夹住 F 除 z_j 外的
  全部有限端点。后一种是从另一无界外端 gap 重入。

这才是本文采用的文献结论；不是“任意未来点都与最近 pair 相邻”。同色区间
laminar、值互异以及第1节的简单曲线实现，分别提供 family 区域、互异端点及
曲线无自交前提。原文图3上图对应有限 gap，下图对应 dummy 的两个外端入口。

### 8.2 分离论证中的点与弧

为说明命题如何使用图4，设第8.1节两个结论都不成立。按 F 沿轴的端点次序，
可选两个**旧有限端点** a=z_p、b=z_r，均不等于 z_j：a 严格处于 z_j 与 z_k
之间，b 在该区间之外。有限 parent 的外边界保证存在外侧见证 b；dummy 时
若找不到这样的 b，恰好就是已单列的“夹住所有有限端点”例外，而非反例。
因为 F 最近 pair 是 P_j，两个见证的输入下标均小于 j。

R 的轴上开 gaps 与 child/parent 弧构成它的边界，边界的循环次序由沿轴的
端点次序和 parent 外弧闭合给出。连接 z_j 与 z_k 的简单辅助弧 S 取在 R 内，
仅两个端点在边界；R 内部无旧曲线。这是该区域的一条截弧：a、b 位于它分开
的两段边界上。实际后续曲线段 C[j,k] 除端点外在 R 外（首次重入条件）。
故 S 与 C[j,k] 只在端点相接，组成简单闭曲线 O；截弧两侧的上述边界段，
从 R 内稍作扰动后位于 O 两侧，a、b 本身不在 O 上，因而也被 O 分隔。
这是原文图4的分离步骤；无界区域可在所有有限弧以外闭合边界描述，不能把
dummy 外端例外当作有限 gap。

旧曲线中连接 a 与 b 的段 C[min(p,r),max(p,r)] 全部早于 j。它不能穿过 S
的内部，因为旧曲线不在 R 内；不能经过 S 的两个端点 z_j、z_k，因为它们的
下标更大；也不能穿过 C[j,k]，因为简单曲线的不相邻段不交。这与连接 O
两侧必穿过 O 矛盾。辅助闭曲线是为这一步构造的，不要求整个输入曲线闭合。

### 8.3 本文补充：最近 pair 是有限 parent

这不直接满足第8.1节“P_j 为 child”的命题，必须单列。F 在新 parent P_j
建立时形成，全部 children 的下标小于 j；z_j 是有限外边界的一端。
若有 children，令 q 是从 z_j **朝 parent 内侧**遇到的第一个 child 端点；
所允许的入口是 (z_j,q)，即紧邻该外边界端点的 gap。若没有 children，
q=z_{j-1}，允许的 gap 为整个 parent 内部。

证明：首次重入点 z_k 必在有限 parent 内且不在 child 的内部。若没有进入
上述 gap，就越过了至少一个 child 端点；取这样的端点 a 位于 z_j 与 z_k
之间，取 parent 的另一端点 b=z_{j-1}，它在区间之外且早于 j。
用第8.2节同样的截弧和旧曲线连接段即得矛盾。这里既没有 dummy 的无界例外，
也没有把任一外端 gap 都当作允许入口；只需这一个靠 z_j 的 gap，便与 G 的
单列表表示相容。这段是项目给出的补充论证，仍属于待审阅的人工证明。

### 8.4 与当前 family 和分组 G 的对应

令 x=z_{i-1} 落在当前 parent family 的 gap。该 family 最近一次建立／改变
直接 child 集合时，最新 pair 是 G 中的 P_j：新 child P_j 会留下，新的 parent
P_j 则创建 family。只更新子孙而未改变 F，不改变 F 的区域。
若自 j 以来已在 R 内开始另一条同色边的更新，那次更新会改变 F 并产生更大
的最新下标。因此在 F 尚未改变时，当前所用的入口适用“首次重入”的前提。

结合第8.1/8.3节和 G：

- gap 若在两个 children 之间，恰为 G 的两组之间；左边 child 是左组最后一个，
  右边 child 是右组第一个，两个组同 owner、不同 list。
- 最近 pair 为有限 parent 时，入口在 children 的外端，全部 children 属一个
  列表，邻接 child 就是该列表极端。
- 最近 pair 为 child 而 gap 在外端时，或发生 dummy 绕行时，z_j 是相应的
  极端有限端点，G 只留下一个非空部分；仍由一个列表极端和 enclosing parent
  给出两侧边界。dummy 绕行没有内部两组间跨越。

这些是 locality 前提成立的论证来源。运行期 `boundary_list` 拒错和有界反例
搜索检查其后果，不能代替该引理及本节扩展的审阅。

## 9. 从初始化到 Step 3 的归纳

### 9.1 初始化与 Step 1/2

前三点已正确排序；每色只有一个 finite pair，在 dummy 下为 singleton，G 成立。
假设前缀 i-1 的输出、最小 parent、G 及物理表示均成立。

除 x 外，已处理点都是当前颜色某一 pair 的端点，唯一例外是奇数 i 的 z1。
所以 Step 1/2 取 x 两侧的输出邻居、仅在奇数时跳过 z1，正好得到同色端点集
的最近左右邻居。每个邻居属于唯一已完成同色 pair，`_same_family_end_index`
用索引奇偶直接取它；无邻居则使用 dummy。

令 p 为包含 x 的最小同色区间（或 dummy）。最近邻 pair 不可能是 p 的祖先，
因为 p 的端点更近；也不可能是相邻直接 child 的严格后代，因为该 child 的
外端点更近。因此边界 pair 只能是 p 或 gap 两侧的直接 child。结合第8节，
非 enclosing A/B 正是代码所查询的 RIGHT/LEFT 端点；减向交换两者。

### 9.2 插入、分裂与所有组的恢复

只写增向 x<y=z_i，减向为值顺序镜像。新 P_i 不与任何同色旧区间交叉：
若 p 有限则 y 必仍在 p 内，否则 P_i 会与 p 交叉。新 P_i 只能收取 x 右侧
连续的直接 children；其所有子孙随直接 child 留在原子树内。

左边界 A=p 时，新 P_i 建 singleton。由外端 gap 性质原 p 至多有一个 child
列表，所以有空 slot。否则 A 是左组最后一个，将新 P_i 插在其 RIGHT 端；
A.high<x，故端插的区间不交前提成立。左侧组不包含任何待收取 child。

右边界 B=p 时右侧无 child，不需 split。否则 B 是右组第一个，右侧所有可能
收取的 children 都在这一组，它与插入列表同 p、不同 ID。预先记录 transfer
source 因而合法。Step 3(a) 只改左组／新 singleton；source 不变。新 P_i 可能
包住 source 的前缀，这恰是 pending_transfer 唯一允许的临时重叠。

y 不位于 p 的任何**直接 child** 区间内，也不等于这些区间的端点；若 p 有限，
y 仍位于 p 内。增向时 y 不可能退入 x 左侧的 child；若进入右侧 child，
P_i 与之交叉，违反 laminarity。因此 source 中 low<=y 的 children 也满足
high<y，且 x<low；其余满足 y<low。
按 low 分裂与按“被新 P_i 严格包含”分裂相同，不会切开 pair。
acquired 的整个组移到新 P_i，retained 留在 p。合法输入
`[10,1,9,8,5,4,3,6]` 的第8轮是具体例子：p=P2=[1,10]，x=3、y=6，
取得 child P6=[4,5]，保留 P4=[8,9]；y 位于 p 内，不能写成不在任何旧同色区间内。

更新后 p 的最新 child 是 P_i；其左组为原左组加 P_i，右组为 retained，恰按
新 z_i=y 分组。P_i 比取得的所有 children 新，是新 family 的 parent，所以
其 children 必为单一 acquired 列表。其他 family 的直接 child 集合和最大 j
均未改变（被移动 child 自己的 descendants 不变）。因此所有 family 的 G、
最小 parent、严格包含和无环同时恢复；空 acquired/retained 只省略空列表。

### 9.3 Step 3(c) 与第二个 z1 修正

增向时，在 (x,y) 中所有当前颜色已配对的旧点，都位于 acquired children
及其后代。若 acquired 非空，最大的这种点是最右直接 child 的**几何右端点**；
后代严格在其内。若 acquired 空，候选就是 x。它是忽略奇数阶段 z1 后 y 的
真正 predecessor，不能简单以 child.end_index 所指端点替代几何右端点。

偶数阶段没有其他遗漏点。奇数阶段只有 z1 可能位于 base 与 y 之间；严格介于
二者时换用 z1，否则保留 base。因此最终 anchor 就是完整前缀中 y 的最近邻。
减向取几何左端点与 successor。局部插入产生正确的 i 点输出，闭合归纳。

## 10. 结论及证据边界

在上述输入模型、文献 locality 引理和逐函数表示论证下，实际共享核心的端点、
同 owner／不同组、fresh childless parent、split 几何和阶段消费前提均可由归纳
推出；不需要引入任意 owner 搜索或逐叶重绑。表示论证覆盖成本引理调用的
插入、方向转换、split/join、删除短缺修复和 header 转移契约。

本轮将原来“尚无展开”的两项依赖推进为可逐段审阅的人工论证，并用独立 ghost
model 做有界反例搜索。**人工论证仍需审阅；通过案例不把它提升为形式化认证。**
源级成本结论仍按既有成本模型作条件性表述，不保证任意 Python 对象的无条件
最坏墙钟耗时，也不凭此开启正式计时。后续受预算限制的开发性 pilot 仅检查真实计时粒度和流程，不能反向认证本文。
最终共同输入资格与协议冻结仍单独完成。

参考：Fung, Nicholl, Tarjan, Van Wyk, *Simplified Linear-Time Jordan Sorting
and Polygon Clipping*, IPL 35 (1990), 85–92，尤其 pp.87–89；仓库
`docs/papers/simplified_linear_jordan_sorting.pdf`（上述为印刷页码）。
另见 Tarjan–Van Wyk (1988) 附录的 heterogeneous trees；本文的 span、根缓存及
删除实现以当前源码为准，不声称与论文所有指针字段逐字相同。
