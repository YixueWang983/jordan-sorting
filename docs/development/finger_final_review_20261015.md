# 真实指尖后端：表示、混合成本与 locality 的集中审阅

审阅基线：`b6e1116fa02be1e448c8f47973a3b5b662c46d02`。它与实际校准版本
`c5b5ac3fd20cf89173916f49187f28aafc633434` 的 `src/`、`tests/`、`experiments/`
相同。本次不修改这些目录，不重新取得资格或选择批量。精确文件身份及审阅凭据
见 `docs/validation/final_review_formal_20261015/`。2026-10-16 根据对
`ce0148b` 的审核补正 R3 的红根透传契约及 C1/C2 的依赖；修订记录在
`docs/validation/join_proof_correction_20261016/`。旧凭据绑定的是修订前文本，
仍可从 `ce0148b` 取得；它没有重新签发为对本版的认证，正式数据亦未改动。

这是本项目本次**源码人工审阅**，不是外部第二位审稿人的独立认证，也不是机器
形式化证明。以下结论来自分支、循环不变量和归纳推导；既有有界测试只作旁证，
校准快慢不参与证明。此前笔记中的开放状态是其归档时点，不改写旧记录。

| 项目 | 本次结论 | 具体依据 |
| --- | --- | --- |
| R：物理表示保持 | 通过源码人工审阅 | 第1–4节；显式区分完整表示与短缺暂态，核对根/非根和镜像赋值 |
| C：混合操作成本 | 通过下述计算模型中的推导 | 第5–7节；累计 join、根 rib、两层势能及共享核心均收费 |
| L：locality/精确分组 | 通过文献适用范围与项目补充归纳的人工审阅 | 第8–10节；有限 parent 单列，首次重入和两个 z1 修正不省略 |

三项之间的依赖为 R → C 中的红黑/修复性质，L → 实际排序调用的操作前提，
R+L+C → 第7节总成本。没有把“修复保持不变量”继续留作未经论证的计算模型假设。
本次未发现这些范围内仍阻止正式测量的具体分支或引理；未来反例必须重新打开
相应结论。正式测量仍另受输入、校准、环境和保存协议约束。

## 1. 范围、计算模型和表示 D

输入是互异、全序且已通过 Jordan 合法性判据的值序列；同色区间 laminar。
单位成本模型包括值比较、指针/机器字操作、常数大小分配，以及字典的期望查找
和摊还扩容。大整数位成本、任意用户比较器、解释器调度及墙钟噪声不在该保证内。
成本对象是 `minimal`、`detailed_work=False` 的完整公开排序：输入整理、初始化、
共同主循环和输出恢复。oracle、checked 审计、trace 物化、replay 是另行验证工作。

D 将异构物理树解释为有序外部红黑树。外部叶黑，rank=0，span=1（包括
singleton ROOT）；内部节点 key=max(left)，两个逻辑孩子等 rank，
rank=child.rank+[black]，没有相邻红节点，完整根黑。不计外部黑叶的黑高
约定由此固定。内部 span 在 INTERIOR 为完整叶数，在 rib 为 inward 叶数，
在 ROOT 为0；header.size 单独为总叶数。

LEFT 的 left 槽和 RIGHT 的 right 槽向上；从两端反向链恢复 outward 孩子。
其 inward 孩子朝下，所有非 rib 子树为 INTERIOR。内部 ROOT 的物理孩子槽空，
两条链的最后孩子必须等于 header 的 top 缓存。singleton 的 top 均空。
finger 是极端叶，路径无环，解码的每个节点恰可达一次。

每片叶与 PairHandle/PairRecord 互相绑定且身份稳定。只有极端 handle 的
相应 boundary 槽引用 live header；owner 在 header 上，owner.child_slots
有序且至多两个。列表身份与物理组件身份不同，split 退役 header 不退役叶。

## 2. 转换、端插和向下 join

**R1：转换恒等。** `TreeOperations.expose` 每步先保存 outward 孩子，再将
槽改为向上，span 取未修改 inward 树的完整 span。已反转路径加未处理余树在
D 下始终等于原组件。`unreverse` 先存 above，再连接已处理 below，最后
`refresh_down`，自底向上恢复完整 span/rank。top 由 `rooted_component` 单独
处理；叶、非根 top、ROOT 三条出口分别不走、一条、两条 rib。`fingers` 做
逆变换并黑化根；黑化红根使 rank 加1，不能当作颜色也完全不变。
这些操作不分配/替换叶，也不遍历 inward 子树。

**R2：端插。** `make_list` 创建黑叶 singleton。`insert_boundary` 在指定
finger 接入一个红 connector 和新黑叶，旧叶也是黑且 rank=0，故只可能出现
connector 与其 parent 的红红。singleton 分支建立两个 top 并黑化根；非
singleton 旧端点变 INTERIOR、新端点进入 rib。只清除被替换一侧的 boundary
槽，另一侧（包括旧 singleton 的另一端）保留，list ID 不变。

`_repair_insert` 的红 uncle 分支使 parent/uncle 黑化、grand 红化；孩子 rank
各加1，grand.rank 不变。唯一新冲突在 grand 的上边，循环严格上移。
黑 uncle 分支 `_rotate_outward`，以左侧为例：
`G(P(C,M),F) → P(C,G(M,F))`，P/C 原红、G/F 原黑。C/M/F 的 raw rank
相同；新 G 红且 rank=M.rank，新 P 黑且 rank=G.rank+1，等于旧 G.rank。
G.key 始终 max(M)，P.key 始终 max(C)，叶序/集合不变。

| 原 G 位置 | 赋值及未改边的核对 |
| --- | --- |
| 非根 | G 成 INTERIOR(M,F)，span=M.span+F.span；P 保持 rib，up=原 above、inward=G、span=G.span；C.up 原本即 P；above 为根时更新对应 top |
| 根 | P 成 ROOT、槽空、span=0；G 成对侧 rib、up=P、inward=M、span=M.span；top=C/G；F 的反向 parent 原本即 G；finger 不变 |

右侧源码把 up/inward、LEFT/RIGHT、top 对应交换；逻辑等式为
`G(F,P(M,C)) → P(G(F,M),C)`。此时 G.key=max(F)、P.key=max(M)，也均不变。
这逐项核对了镜像的 separator，不依赖把“max(left)”机械变成“max(right)”。
根黑化、旋转或遇黑 parent 终止，恢复 D。

**R3：向下局部修复。** `rotate_down` 只接收 INTERIOR，普通左旋
`A(X,B(Y,Z)) → B(A(X,Y),Z)` 保持 A.key=max(X)、B.key=max(Y)；右旋为逆式。
以下是 `combine` 沿一次递归更新路径的契约，不是 `balance_down` 对任意损坏
树的修复保证。入口组件有序、等黑高、内部无红红；允许根红。返回始终保持
叶序/集合、两孩子的实际黑高相等、separator、rank 与完整 span。回溯替换
的孩子保持原黑高；只可能带来红根或下面规定的一条红红连接。

| `balance_down` 入口根及出口 | 递归返回契约 |
| --- | --- |
| 黑根，无 LL/LR/RR/RL 冲突 | refresh 后直接返回黑根，内部红黑性质成立，黑高不变 |
| 黑根，有四种冲突之一 | 把四段等黑高子树整理为红中间根及两个黑孩子；内部红黑性质恢复，黑高不变；返回红根可使调用者处产生新的冲突 |
| 红根，直接返回 | 原两个孩子黑，只有递归更新侧可能返回合法的红根；因此至多留下这一条根—孩子红红连接，其余内部边合法、黑高不变；此返回**不是完整合法红黑树** |

四种黑根修复中，内侧分支先旋红孩子，再旋黑祖父；按新颜色自底向上
refresh。旋转中间尚未重着色的临时 rank 不用于新的搜索/高度分支判断。
红根透传时，未更新的孩子仍黑，更新侧的红孩子内部合法（它若红则孩子黑）；
故冲突不会同时出现在两侧或更深处。原红根的父必黑，它在下一层回溯恰好
看到 LL/LR/RR/RL 之一并消除这条冲突。一个黑根修复后再返回红根时，同一
两层归纳继续适用，不能把暂态直接归入完整表示 D。

`join_down` 黑化两个非空输入根，在较高根的内侧单路下降，到同 rank 黑根
用红 connector 相接。基例的 connector 内部合法且保留这个 rank；每次
回溯按上表保持被替换组件的黑高。下降方向不会穿过待修复的暂态：修复在
递归返回后才发生。在红根处因其孩子黑，递归要么命中两个黑根基例，要么
从黑根继续下降；这给出了上表红根分支所需的合法孩子返回前提。
顶层要么就是基例，要么在预先黑化的输入根处完成黑根修复，故返回时内部
已无红红。最后黑化根只处理根颜色；**不能靠最后黑化来消除内部红红**。

例如 `A_B([0],P_R([1],[2]))` 与 `[3]` 拼接时，先返回
`P_R([1],C_R([2],[3]))`，再在 `A_B` 处做 RR 修复；镜像经过 LL 修复。
两个中间返回均符合红根透传契约，最终 join 合法。

connector.key 是
left.maximum；沿右支插入不改变既有左 separator，沿左支插入不改变既有
左子树的最大值。叶集合为两个不交输入之并，size 相加、maximum 取右输入。
空侧直接返回另一组件并退役 connector，不假装已经黑化返回根。

## 3. 删除短缺：暂态 D* 与根/非根修复

**R4：明确暂态。** `detach` 删除完整极端组件及其 parent connector，以
原 sibling 替代 parent。红 parent 不减黑高；黑 parent/红 sibling 黑化后
恢复；黑 parent/黑 sibling 进入 `repair_short`。此时 D* 在 short 上加一个
虚拟黑层：short.rank 是实际值，祖先尚保持含虚拟层的 rank。不能要求暂态
所有实际孩子已等 rank，也不能因此把尚未恢复的 parent 当普通向下树 refresh。

记 short 实际 rank=r，兄弟 rank=r+1，故兄弟不是叶，near/far 访问有定义。
每轮保持叶序、separator 和 span；短缺只在这一条外侧路径。

| `repair_short` 分支 | 消除/移动短缺的依据 |
| --- | --- |
| 红 sibling | parent 必黑；黑化 sibling、红化 parent，向 short 旋转。新 parent 红、新 sibling 黑；虚拟黑高不变，继续在原 short 处处理 |
| 黑 sibling、near/far 均黑、parent 红 | sibling 红化，parent 黑化，双方实际黑高相等，parent.rank=sibling.rank+1，短缺消失 |
| 同上、parent 黑 | sibling 红化，parent.rank 减1；parent 成新的黑 short，短缺上移，循环严格向根推进 |
| near 红、far 黑 | `rotate_near` 黑化 near、红化 sibling，以 near 替代 sibling；保留该局部黑高，变成 far 红情形 |
| far 红 | sibling 取 parent 原色、parent/far 黑化，向 short 旋转；两侧实际黑高恢复原虚拟黑高，终止 |
| short 到根 | 整树黑高降低1，完整根仍黑，短缺无需再向外支付 |

`rotate_short_parent` 左式为 `P(S,B(N,F)) → B(P(S,N),F)`；key P=max(S)、
B=max(N) 均不变。P 进入/保持 LEFT，up=B、inward=N、span=N.span，
rank=N.rank+[P黑]。B.rank=F.rank+[B黑]；红 sibling 分支这一等式包括
尚留在 P 子树的虚拟层，终止分支则已是普通实际 rank。

P 原为根时 B 成 ROOT，槽空/span0，top=P/F；否则 B 成同侧 rib，up=above、
inward=F、span=F.span，必要时更新 above 的 top。S.up=P 未变；F 若在对侧
rib，其 up=B 也未变。右式为 `P(B(F,N),S) → B(F,P(N,S))`，key B=max(F)、
P=max(N) 均不变，代码对称维护右侧。

near 修复在 INTERIOR 用普通旋转。在 ROOT 的对侧 rib 上，左短缺示意
`B(N(X,Y),F) → N(X,B(Y,F))`：B 红，up=N、inward=Y、span/rank=Y.span/rank；
N 黑，up=P、inward=X、span=X.span、rank=X.rank+1，更新 right_top。
F.up=B 原本成立；N.key=max(X)、B.key=max(Y) 不变。右短缺逐项交换得到
left_top 版本。颜色改变不改变任何 span；旋转仅刷新改变了逻辑孩子的节点。
这些分支覆盖源码全部删除出口，不借用端插修复作为通用删除证明。

## 4. 完整 split、大小和 ownership

**R5：路径划分。** `locate_component` 的停止使选中 extremal 组件之外的
余树完整在一个输出侧；组件自身可能跨切口，也可能全在一侧。
`split_down` 用有序 frames 保留未动 sibling；叶按 key<=value / >value
归类，回溯只拼接相应一侧，所以每片原叶恰好出现一次，输出有序且满足切值。
旧 connector 每个或再用一次或退役一次，`retire` 明确拒绝外部叶。

大小由路径导出：finger 开始 size=1；上行非根增加 parent.span（恰为新加入
的 inward 组件），上到 ROOT 用 header.size。detach 余树大小=total-size。
转为向下后 sibling.span 为完整大小；frame/join 加和，最终 header 从 fragment
复制总大小。没有把所有 role 的 span 当总叶数，也没有遍历输出求大小。

`join_fingers` 从大树 finger 找同 rank 黑组件，与小树黑根相接。根分支使用
R3；非根分支只新增“外侧红 connector + 等 rank 黑孩子”，满足 R2 的严格
前提，因此此处可复用 `_repair_insert`。转换及根变换按 R1/R2/R4 更新 top，
各端点始终是保留下来的极端叶。两端与 header 的边界引用在公开 split 末尾
统一重建，内部拆解期间不声称已经是可公开审计的 live forest。

**R6：身份和转移。** `split_value` 总退役旧 header，给每个非空结果分配
从未使用的 list ID（包括单侧快速返回同一物理树的情况），清旧两端引用、设新
两端引用，保留 pending_split。`adopt_split` 核对源、目标、输出 ID、指定
transfer，替换旧 owner 的一个 slot，并把 acquired.header.owner 改为新 parent。
每个 owner 至多两槽，全部循环有常数上界。叶/handle/pair、被移 pair 原有
child groups 均不重建、不逐项改 owner。

目标严格包围 acquired 两个极端，加上有序不交区间，推出包围每个 acquired
成员。既有 owner 边严格包含，因此转移不能形成环。空 acquired 另需目标在
source 外的边界/待转移见证；排序的目标是本轮 fresh childless pair，满足
更强前提。pending_transfer 只允许新 pair 与指定 source 暂时重叠；第9节
证明实际调用满足它。adopt 恢复槽及 owner 后清除 pending，Step3(c) fence
才允许输出插入。非法输入/故障可能导致不可复用中间状态，失败语义仍为抛错并
丢弃本次状态，不主张异常发生后可以继续操作。

## 5. join 累计和较小侧搜索

**C1。** 定义规范化黑高 nu(T)=raw rank+[根红]。非空 `join_down` 的输入
先黑化，令其黑高为 a,b，结果为 c，实际 combine 次数 Q。由 R3 的完整
递归契约（包括红根透传、黑父修复和顶层收尾），
`max(a,b)<=c<=max(a,b)+1`，`Q<=2|a-b|+3`：下降每个黑层降低 rank 差1，
红层不能连续（这里指下降时的合法输入，而非回溯暂态）；回溯每层常数操作。
基例和回溯均保持原 raw rank，红根透传不增加黑高；只有最后根黑化可增1。
若 c>max(a,b)，黑化前的返回红根是基例或黑根四分支修复的产物，内部合法
且两个孩子黑，所以结果黑根且两个孩子黑。顶层不是红根透传出口。
原始红根黑化本身最多再加1，故这里的“加1”不能相对黑化前黑高使用。

**C2。** 对 raw rank=r 的合法向下组件 split，每个非空输出 nu<=r+1；
若原根黑且输出达到 r+1，输出根和两个孩子均黑。这里的输出指一次
`join_down` 完成后的组件，不是 `combine` 的红根暂态；所用 C1 依赖完整 R3。
归纳令原孩子 raw rank=q：
黑根 r=q+1 时两个 join 输入至多 q+1，增高到 q+2 时应用 C1 的强性质；
红根 r=q 时两个原孩子黑。递归输出若至多 q，直接用 C1；若达到 q+1，
由强归纳它的根及孩子黑，与另一黑高 q 组件只下降一层，新红 connector
挂于黑根之下，不再增高。因此最多 q+1。叶和空侧返回直接成立。

每个回溯 join 的累计输出黑高 a<=q+1，未动 sibling 的规范化黑高 b>=q，
故 a-b<=1，`Q<=2(c-a)+5`。左右累计链分别黑高不降，望远镜相消给出
`sum Q<=2(nu(L)+nu(R))+5J`，J 为非空 join 数。空侧返回只增大可用高度差，
没有隐藏昂贵 join。frames、回溯及全部 join 合计 O(r+1)，而不是 O(r²)。

**C3：上行前/后必须区分。** 左端仅在 parent.key<value 时上行，能确定
全在左输出的是**上行前**的组件；刚到达的 parent 可能跨切口。右端在
value<parent.key 时同理。较小输出大小为 s>=1，其端上行前组件 rank t
满足 2^t<=s，上行后至多再加1。无连续红层、两端交替（步数差至多1），
所以首先返回的组件 rank r=O(log(s+1))。这个证明不要求选中组件内部一定
发生两侧非空分裂。s=0 在两次端点比较中直接返回 O(1)。

detach 的 sibling 与选中组件原等 raw rank；最多转换同阶组件。C2 限制两个
输出的规范化黑高，转换成 fingers 也只沿 O(r+1) 层。join_fingers 的 small
黑高不大于这个界，大树仅从端点走到相同 rank；到根意味着整棵大树本来就
只有此黑高。根 join 输入等 rank；非根的插入传播另在下一节收费。

## 6. 另一 rib 与完整混合势能

**C4。** `sibling_children` 只有 sibling 非 INTERIOR 时走 `rib_child`。
非根 parent 的 sibling 是 inward 向下树；只有 ROOT 的 sibling 在对侧 rib。
根处红 sibling 旋转后原 parent 成非根，后续 sibling 是 INTERIOR；根处传播
立即到根终止；near 修复至多再取一次 far，随后 far 修复返回。因此每次
repair_short 至多两次这种行走。若初始 short rank=r0，继续传播 D 次，每次
新 short 实际 rank 加1，终止局部变换只加常数层，根附近 rank<=r0+D+2。
两次路径合计 O(r0+D+1)，r0<=r+O(1)。这里没有将这条行走当 O(1)。

**C5。** 按逻辑孩子计
`Phi = #(黑内部节点、两黑孩子) + 2 #(黑内部节点、两红孩子)`，叶贡献0。
完整状态对所有 live 树求和；拆分暂态对不交逻辑 fragments 求和，每个节点
只计一次，不能把旧 header 和新 fragment 重复计，也不在 split 后重置势能。

插入继续传播：grand 黑 RR 权重2→红0；parent 红→黑但孩子一红一黑，权重仍0；
uncle 红且两黑孩子→黑 BB 权重1。合计 -1。grand 上方为红时其权重0不变；
上方为黑时下一轮停止，边界权重变化为常数。根黑化及终止旋转只涉及固定数量
节点及其邻接 parent。于是 I 次 recolor cascade（非逐节点 recolorings）
有 `Delta Phi <= C-I`，实际费用 O(I+1)。

删除继续传播：parent/short/sibling 均黑，sibling 两孩子黑；sibling 的权重
1→0，parent 从 BB 的1→混色0，合计 -2。parent 颜色未变，祖父权重不变。
红 parent 吸收、红 sibling、near/far、到根这些终止组合涉及固定数量节点，
增量有常数上界；源码 propagation 计数可能包括最后一次吸收，差别吸入常数。
因此可用较松的 -D 支付传播，并以足够大的常数倍支付 C4 的 O(D) rib 费用。

跨组件拆/接边只改变固定数量局部颜色权重；方向转换不改变逻辑颜色，根黑化
也仅改变根及其连接边附近权重。全部向下 joins 有 O(r+1) 局部步骤，每步
改变常数权重；connector 分配/退役也是如此。非根 join_fingers 额外插入传播
适用刚证明的同一 Phi，不能把它当另一条纯插入序列重新起算。
合并得 `Delta Phi <= C(r+1)-D-I`，实际 split 费用 `<=C'(r+D+I+1)`。
选足够大的 K，则费用加 K DeltaPhi 为 O(r+1)。所以任意合法混合序列中，
端插摊还 O(1)，split 摊还 O(log(s+2))，make/adopt 及有界 owner 维护 O(1)。
非空初始森林须计入 K Phi_initial；当前排序从常数规模初始化，不能无条件
忽略任意预装树的势能。

## 7. 从操作到完整排序的成本

再取 `Psi=c sum_{非空L}(|L|-log2|L|)`，非负。
make 增 c，端插增 `c(1-log2(1+1/m))<=c`，adopt 不改变大小。
双侧非空 split m=a+b，1<=a<=b，`DeltaPsi/c=log2((a+b)/(ab))<=1-log2(a)`。
`log2(a+2)<=log2(a)+log2(3)`，故选择固定 c 支付第6节较小侧对数费用，
留下常数；单侧 split 不改变 Psi。Phi/Psi 均非负，从空/常数初始状态起，
整条合法操作序列的总结构费用为操作次数线性上界。

源码 `paper_jordan.py` 的共享迭代器每轮执行固定的 Step1/2/3、常数次接口
查询及常数大小阶段记录。`_validated_live_finite_pair` 使用稳定 handle，
需要边界时才 `boundary_list`；`_owner_slots` 至多两槽；没有祖先/成员扫描。
`partial_sorted_list.py` 用字典定位及相邻指针插入，局部比较常数；入口整理
与最后 `to_list` 各 O(n)。必要 stage_results 累计 O(n) 存储，每轮仅访问本轮
固定键；历史 stage/trace 重建留在完整验证路径。minimal 不构造 detailed
账本/快照，残余字段包装和开关判断是每次访问的常数。yield/resume 每轮常数。

结合第9–10节保证的合法调用，完整 minimal 树排序在第1节的计算模型中有
O(n) 期望/摊还源级工作量。该结论不说所有 Python 比较器都常数、不说 checked
验证线性、不说实测一定快于列表或 sorted，也不由曲线推导。普通列表的扫描/
复制和历史实验保持自己的独立成本与版本解释。

## 8. locality：文献前提与有限 parent 补充

采用仓库 `docs/papers/simplified_linear_jordan_sorting.pdf` 印刷88页引理和
图3/4、89页 Step3 与图5。已核对原引理的前提是最新 P_j 为 family 的
**child**，结论针对离开 z_j 后对仍未改变区域 R 的**首次**重入；允许紧邻
z_j、朝 R 的 gap，dummy 另允许绕到另一无界外端（夹住其余全部有限端点）。
不能将它直接用于最新 pair 是有限 parent，不能写成任意未来点都相邻。

以同色 parent 弧内、直接 child 弧外定义 R。laminar 区间可在上下半平面
实现为不交弧，两色交替形成简单的开放曲线 C。R 的边界由 parent 外弧、
axis gaps 及 child 弧构成一条简单闭边界；children 接在轴上，不是 R 内部
独立的洞。dummy 可在所有有限弧之外截取大边界，但保留两个外端 gap 例外。

**L1：有限 parent 最新。** P_j 是 parent 时，z_j 是其外端点，所有 children
更旧。q 是朝 parent 内侧的首个 child 端点；无 child 则 q=z_(j-1)。首次
重入 z_k 必位于 (z_j,q)。否则取严格位于 z_j 与 z_k 间的 child 端点 a，
取 b=z_(j-1)（另一 parent 端点，在区间外），二者输入下标都小于 j。

在 R 内取简单截弧 S 连接 z_j 与 z_k，仅端点在边界；a、b 分别位于截弧
分开的两段边界。实际 C[j,k] 内部在 R 外，且不能穿过旧 family 边界弧：
曲线无自交；若先在 axis 的 R-gap 相接，交替半平面已构成更早的进入，违反
首次重入。因此 S 与 C[j,k] 只在端点相接，组成简单闭曲线 O。R 边界的上述
两段在 O 两侧，a、b 不在 O 上。旧曲线连接 a,b 的段不能穿 S（R 内无旧弧），
不能碰 S 两端（下标更晚），也不能穿 C[j,k]（简单曲线），与分离矛盾。
无 child 时整个 parent 内部就是允许 gap；有限 parent 没有 dummy 绕行例外。
此为项目补充证明，不标作原文 child 引理的原句。

## 9. 首次重入、端点前提与精确分组归纳

**L2：G。** 每个 pair 的 owner 是最小同色严格包围区间，否则 dummy。
直接 children 按区间排序。令 j 为该 parent/直接 children 的最大 end_index：
最新为 parent 时所有 children 一组；最新为 child 时按 z_j 分为左右两组，
忽略空组。这是88页的精确规则，比“有序、最多两组”更强。

初始化每色 singleton，G 与输出成立。假设 i-1 完成前缀成立，x=z_(i-1)，
p 是包含 x 的最小同色区间（或 dummy）。对应 family 自最近直接成员 P_j
产生后，子孙内部更新不改变 R。若当前 x 之前已于 z_k 首次重入 R，下一条
同色边从 R-gap 开始；laminarity 强制它停在 p 内且不进入旧 child 内部，
从而形成 p 的一个新直接 child（可以收取连续旧 children）。其下标 k+1>j，
且早于当前更新，矛盾。因此当前 x 确是未改变 R 的首次重入。这里使用颜色
交替：重入后下一条边正是该色；不能只凭当前查询成功来推断此前没有重入。

除 x 外的已处理点均为当前颜色端点，奇数 i 唯一例外为 z1。Step1/2 从输出
邻居跳过此例外，得到最近同色端点。祖先的端点被 p 的端点挡住，后代的端点
被直接 child 外端点挡住，所以 A/B 只可能是 p 或相邻直接 children。
文献 child 引理/L1 加 G 给出：内部 gap 恰在两组间，左边界是左组最后成员，
右边界是右组首成员，同 owner、不同 list；外端 gap 及 dummy 绕行只留一组，
另一边界为 enclosing parent。故实际指定端点访问的 locality 前提成立。

**L3：Step3(a/b)。** 以 x<y=z_i 为例。若 p 有限，y 必仍在 p 内，否则新
区间与 p 交叉；y 不能在任何直接 child 内部或端点，否则与该 child 交叉/
重复点。允许 y 位于旧 parent 内，不能写成“不在任何旧同色区间内”。

A=p 时建立 singleton，原至多一组故有空槽；A 为 child 时在左组末端插入，
A.high<x，满足不交。B=p 时无待收取 child，不分裂；B 为 child 时 source
是右组，same owner、different list。预先记录 source 后，3(a) 只改左组或
新 singleton，因此 source 的 live ID/端点/owner 不变。新 P_i 是 fresh、
childless，临时包含 source 的前缀是唯一允许的 overlap。

source 中 low<=y 恰好等价于 x<low<high<y；其余 y<low。所以 key split
与按几何包含取得 children 相同，输出合法并可 adopt。更新后 p 的最新 child
为 P_i，左组=旧左组+P_i、右组=retained，恰按 y 分组；P_i 最新为 parent，
其 children 单一 acquired 组。被移动 pair 的子孙结构和其他 family 的最大 j
不变；strict containment 恢复最小 parent/无环。空侧只删空组，两个 pending
清除。递减用左右顺序镜像，严格不等号反向，全部 owner/组条件相同。

## 10. 输出归纳及审阅边界

**L4：Step3(c)。** x<y 时，(x,y) 中已配对旧端点恰属于 acquired children
及其子孙；最大端点是最右直接 child 的几何右端点，acquired 空则为 x。
这给出忽略奇数 z1 后的 predecessor。仅当 z1 严格在该 base 与 y 之间时
替换 anchor；偶数无遗漏。递减取最左 child 几何左端和 successor。相邻指针
插入得到完整正确输出，G、D 和所有阶段前提在每个完成前缀恢复，归纳闭合。

本次审阅覆盖以上算法路径及计算模型，不把 Python 故障时的中间对象恢复、
任意泛化容器操作或机器形式化认证列为已证明。未进行新的排序正确性批次，
未把既有测试重新计数。原140例与独立12例、实际校准、旧失败记录均原样保留。
后续正式样本必须引用自己的执行提交与冻结 B 表，不能把本文件或审阅 receipt
当成性能数据。源码 `timing_ready=False` 是先前保守能力元数据，未为改变标志
而修改已校准代码；正式 runner 的实际准入是资格/校准/环境核对及本审阅凭据。
