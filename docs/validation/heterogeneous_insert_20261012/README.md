# 真实 heterogeneous 树首个增量：make / 端插

**范围是部分操作验证，不是完整后端验收。** 在 `d245adfc369744df73b5cc63d170cc429252c5e8` 上新增真实节点与操作，未修改论文或启动 Jordan 输入的大批生成、资格检查和计时。`split_value`、`adopt_split`、`split_pairs_at_value` 明确抛出 `NotImplementedError`，没有普通列表兜底。`sorting_ready=False` 同时阻止显式 `SiblingBackendSpec` 用它运行排序，公共名字注册仍只有 `ordinary_list`。

## 实际表示与更新

实现位于 [heterogeneous_finger_backend.py](../../../src/heterogeneous_finger_backend.py)，没有使用第三方实现源码。依据 Tarjan–Van Wyk (1988) [Appendix pp.171–175](https://www.ibr.cs.tu-bs.de/courses/ws2324/ag/papers/Ch5/Tarjan-vanWyk_1988.pdf) 的外部红黑树、端点反向路径与 Fig.20 插入变换，并按[官方勘误](https://epubs.siam.org/doi/epdf/10.1137/0217067) 使用原文 p.176 所印的 heterogeneous 图（应为 Fig.22）。未采用普通根搜索树作为替代，未使用可持久化树或通用容器实现。

- `ExternalLeaf` 保存稳定 `PairHandle`；`get_pair` 返回注册时的原 `PairRecord`，其曲线端点身份不变。几何 low/high 从固定数据源建立，允许曲线端点方向相反。
- 左 rib 的 left、右 rib 的 right 指针朝向父节点；内部区域指针朝子节点。根两指针均为空。header 保存两端 fingers、根、两个根分支引用、总大小、owner 和 live ID；根分支引用只服务根部局部变换。
- 内部 key 为逻辑左子树的最大 item key；端插不改已有分隔 key。`rank` 是逻辑黑高（不含外部黑叶）。`span` 在内部区域为子树叶数，在 rib 为**直接朝内分支**的叶数，在根为零。这不是整棵逻辑子树大小，也不是论文可选的“指针可达叶数”位置索引；本增量不支持位置或 secondary-heap 搜索。header 总大小另行 O(1) 更新。
- 端插从指定外部 finger 出发，分配一个新叶与一个内部节点，仅沿出现红红冲突的 rib 向上修复；修复包含根变黑、连续重着色、左右单旋转及根/非根两类方向转换。纯端插的冲突路径总在外侧，Fig.20(d) 的内侧双旋转不属于本操作的可达情况；split/join 的修复仍待实现。
- ownership 权威在 header；pair 只保存至多两个 child slots，以及恰为端点时的反向 header 引用。端插保留 list ID，清除旧端对应引用，不逐项写 owner/list 字段。make/insert 检查 family、严格区间顺序、有限 owner 的包含关系、最多两个有序 slots 和端点身份。新 item 必须无归属且无子项，所以不会在本增量中创建祖先环；完整审计另行核对整个森林。

异常向上传播，不提供更新回滚；遇到失败后须丢弃该实例。归属和几何检查依赖此前成功操作维护的结构以及固定的点值数据源，完整审计可检测结构/记录/数据源篡改，不把任意受损状态的全局恢复放进端插路径。

## 验证结果

[实际树测试](../../../tests/test_heterogeneous_finger_backend.py)：**31 个方法通过、0 跳过**。覆盖 singleton、同侧/交替/不规则端插、两 family、几何方向与左右镜像、稳定 handle/叶对象、owner slots、内部 pair 作 parent，以及非法/过时/外来边界引用和结构破坏拒错。所有 256 条长度为 8 的左右选择历史逐操作对照简单列表模型并审计；它们是一个测试内的子场景，不是 256 项新测试或 Jordan 合法输入。另有较长序列覆盖根/非根左右旋转和重着色传播。

正常路径测试禁用全量审计、物化接口和 registry 遍历，make/insert 与边界/owner/极端 child 查询仍能运行。查询账本在 8、64、513 项时相同；固定终止修复的工作量不会随更高祖先链增加。这些检查能发现所测路径的全量维护回归，不代替一般性证明。

现有定向核心回归 **173 个方法通过、0 跳过**，其中包含共享核心/后端选择/replay 的 15 项接入回归；它们运行的仍是普通后端和原路由夹具，不是树后端端到端证据。合计 **204 个不同方法**。本轮没有重跑完整仓库测试、抽象模型的完整 split 契约、原 16 例资格探测或论文编译。

日志为 [development_tests.log](development_tests.log) 与 [core_regression.log](core_regression.log)；[verification.json](verification.json) 记录命令、源码和证据哈希及明确的未完成标志。

## 成本账本与复跑

`WorkLedger` 对真实节点/handle/header 的字段读写自动记账。每次节点字段读或写计一次 `node_visits`，重复访问重复计数，不是“不同节点数”。另记几何/key 比较、左右旋转、重着色、元数据/指针写入、分配、registry 读写及点值读取。元数据写入包括初始化和 allocator 更新。分配统计节点、handle、header 和 child-slot tuple，**不是 Python 解释器的全部临时对象或内存字节**。record 字段之外的 Python 控制流、字典扩容、GC 和记账自身开销未换算成这些计数；不能把它们称为完整 CPU 指令成本。

更新中的嵌套查询计入更新账本；独立查询与完整审计另有 bucket。开发增量始终开启这套账本（包括指定 minimal policy 时），验证由开发调用者显式执行，不据此提供正式策略计时比较。逻辑快照只由审计生成，操作不依赖它。实际树 `span` 与 `rank` 只在局部变换节点更新；没有沿所有祖先更新普通 subtree size 或从根重新搜索。

小型 [成本探测程序](../../../experiments/probe_heterogeneous_insert.py) 固定 64/256/1024 项和同左、同右、交替、固定种子四种历史，共 12 个**操作序列**；不构成排序实验。每条序列独立建树，最终对照模型并检查结构。以下摘自 [summary.json](summary.json)，只列 insert 部分，register/make 的工作另有完整记录：

| 历史 | 端插数 | 节点字段访问 | 旋转 | 重着色 | 元数据写入 | 树节点分配 | 单次最大节点字段访问 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 同左 64 | 63 | 4,360 | 53 | 267 | 2,764 | 126 | 111 |
| 同左 256 | 255 | 18,954 | 241 | 1,209 | 11,546 | 510 | 145 |
| 同左 1024 | 1,023 | 77,900 | 1,005 | 5,031 | 46,824 | 2,046 | 179 |
| 交替 1024 | 1,023 | 77,369 | 990 | 4,977 | 46,594 | 2,046 | 169 |

同右序列对应计数与同左镜像一致。代码路径的工作可分为固定的几何/header/slot 检查、两次节点分配，以及实际发生的局部修复次数；一次重着色传播可能触及多级祖先。因此这里没有把单次端插宣称为最坏 O(1)，也没有从这些有限记录推出整个后端或 Jordan Sorting 的线性界。

[operation_work.jsonl.gz](operation_work.jsonl.gz) 无损保存全部逐操作记录，解压后的 SHA256 与 summary 中 `raw_sha256` 一致，可重新求和并核对总数。复跑到一个不存在的输出目录：

```sh
python3 -m unittest discover -s tests -p 'test_heterogeneous_finger_backend.py' -v
python3 experiments/probe_heterogeneous_insert.py --output-dir /tmp/jordan-insert-work-new
```

后续必须推进真实 split 与局部修复、header/ownership 转移、分裂后交错端插和再次分裂，再接完整排序。10-15 的完整排序中非零真实 split 检查点保持不变；本增量不满足该检查点，也不允许开始正式匹配计时。一般 locality 论证、split 的文献依赖与完整成本论证仍待闭合。
