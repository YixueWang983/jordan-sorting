# 成本引理、中等切分覆盖与机械实验流程

父基线：`84f7e13394db66de1314aa6c8c11281081d0adae`。生产 `src/` 未改，
论文和历史实验未改；本轮新增探测/验证程序、测试和源码对应的成本推导。
精确文件身份见 [verification.json](verification.json)。本轮未开展正式或 pilot
墙钟测量，树的 `timing_ready=False` 保持不变。

## 已推进的内容与保留的边界

[成本引理](../../development/heterogeneous_cost_lemmas_20261014.md)修正了
`join_down` 的黑高比较基准，并给出：

- 根黑化后的单次 join rank/递归步数界；真实红根反例说明黑化前不能直接用“加一”。
- `split_down` 两侧累计输出 rank 的归纳性质及相邻 join 费用的望远镜求和。
- 删除修复仅在根附近进行另一 rib 查找，至多两次；费用由初始组件 rank 和传播支付。
- split/端插使用同一森林势能，分裂后的势能不会被清零；方向转换、大小维护、
  header/ownership 均计入。第二层列表势能的推导与算法层前提分别列明。

这是**操作契约与局部修复保持结构前提下的成本推导**。所有合法 Jordan 输入
的 gap/locality、`z1` 与分组归纳，以及局部逻辑修复和反向表示的完整对应仍需
继续核对。不得据此勾选“高效后端最低交付完成”，也不把 Python 墙钟时间声称
为无条件最坏线性。条件性引理的理由在文档中，有界测试只是反例搜索。

## 实际执行与数量

| 证据 | 本轮结果 | 准确含义 |
| --- | ---: | --- |
| [新增测试](cost_fixture_tests.log) | 15 个方法、0 跳过 | 3 个成本引理、10 个 runner/validator、2 个中等切分生成/资源失败检查 |
| [既有树回归](tree_regressions.log) | 80 个方法、0 跳过 | 53 个真实操作、15 个完整排序接入、12 个记账配置回归 |
| [成本探测](cost_probe/records.json.gz) | 2,634 次小树分裂 | 1–10 片叶全部合法着色形状和切分位置，含红根、空侧；不是 2,634 个独立统计样本 |
| 同一成本探测 | 12 条混合历史、300 条后构造操作、36 次 split | 两侧端插、再次分裂和稳定身份/ownership 对照；不是 Jordan 性能实验 |
| [完整排序定向验证](middle_splits/summary.json) | 12 个输入、72 次原始运行 | ordinary、tree on、tree off，各 checked/minimal；三个配置不构成三个独立输入 |
| [机械成功夹具](matched_fixture_check.json) | 27 行完整流程，12 条 synthetic samples | 合成 tick，不是墙钟测量 |
| [失败保留夹具](failed_fixture_check.json) | 1 条 ERROR，runner 退出码 2 | 非法输入保留；validator 确认归档有效，但执行未成功、不能计时 |

合计 **95 个测试方法通过**；内部子案例和独立探测重复的同一检查不再累计成
额外测试方法。没有复跑原 173 个普通核心回归或 125 个旧实验工具回归，也没有
宣称执行全仓库测试或论文构建；这些生产/历史工具本轮未修改。

成本原始事件共含 2,670 个 `split_down` 记录（2,634 + 36）、6,519 个 join
记录，以及 4 个删除修复记录。4 个修复中实际发生了 2 次根附近 rib 查找；
不能用这项观测覆盖所有修复形状。join 的规范化 rank 差实际覆盖 0–3。
1,056 条插入势能观察**包含初始构造**；300 条操作日志则不含初始构造，
二者不能直接当成同一统计单位。

探测器的结构/势能遍历会读取带包装的字段，所以归档只保留相关显式算法
步骤计数，**不将一般字段 ledger 声称为无观察干扰的完整工作量**。
操作记录的 join 步数之和已与对应引理事件重新核对。

## 中等较小侧与镜像覆盖

[执行前计划](middle_splits/plan.json)固定 `n=128/129`、较小侧目标 `3/7/19`，
每个组合均取正向和镜像，共 12 个不同输入。奇偶和方向不再绑定。整个批次
资源上限为 180 秒；超时或 worker 失败保留已完成记录并写失败标志，不重试、
不替换失败输入。资源上限仅控制开发验证，不是性能结果。

每个 checked 配置有 **1,518 个完成前缀、24 次真实 split，其中 12 次双侧
非空**，较小侧 3、7、19 各四次。每个完成前缀对照外部排序输出、独立最小
包围 parent 模型和后端结构审计；最终状态做同配置新实例 replay。
**不是每个前缀都完整 replay**。minimal 也对最终输出和状态执行验证；
相同策略下 tree on/off 的最终逻辑/物理快照、必要阶段状态、trace 和 metrics
比较一致。每例压缩文件包含值、哈希、前缀列表和完整 checked trace，可以
从真实 split 事件重新计算比例，而不只信汇总。

完整排序的这批构造不保证两侧均发生后续更新；该组合由单列的操作级历史
覆盖。不把它混称为端到端组合覆盖，也不继承为最终 140/380 比较集资格。

## 机械 runner/validator 的范围

[runner](../../../experiments/matched_backend_fixture.py)显式选择普通列表与
`SiblingBackendSpec(HeterogeneousFingerBackend, (("detailed_work", False),))`。
两端 sentinel 包住新一次 `paper_jordan_sort_valid(..., "minimal")`，包括
初始化、全部主循环和输出恢复；oracle、checked 资格、expected 输出及比较
都在外部。测试把初始化和 `to_list` 替换为检查 sentinel 状态的函数，并
记录实际新构造的独立 registry。每例固定一个 warmup round、两个 sample
round，按例与 round 交替后端先后顺序；这只是夹具协议，不是最终重复次数。

输入、协议、显式配置和源码 SHA-256 在执行前写入；环境记录包含父 HEAD、
dirty 状态、Python 和平台。此处允许带有已哈希新增文件的开发工作树，不能
冒称正式实验的干净源码冻结。结束时再比对源码。当前只接受最多 8 个、
长度 3–64 的整数输入；`pilot/formal` 显式拒绝，不提供实际计时开关。

[validator](../../../experiments/validate_matched_backend_fixture.py)核验文件及
输入哈希、当前源码内容、配置、逐行顺序、输出、错误保留及完整性，独立
重建预期执行顺序和汇总，不调用 runner 的 schedule/summary 函数。资格与
replay 的成功来自实际调用记录；重建不是对生产算法的独立证明。故障测试
覆盖错误输出、抛异常、非法输入、缺项/重复/篡改、开关和布尔/数值类型混淆。
validator 可接受“忠实记录失败的归档”，但其 `completed_successfully=false`，
始终 `performance_eligible=false`。

## 复现与原始记录核对

在仓库根目录使用 Python 3，输出目录必须不存在：

```sh
python3 experiments/probe_finger_cost_lemmas.py --output /tmp/jordan-cost-new
python3 experiments/validate_finger_middle_splits.py --output /tmp/jordan-middle-new
python3 experiments/matched_backend_fixture.py \
  --inputs docs/validation/finger_cost_and_fixture_20261014/fixture_inputs.json \
  --output /tmp/jordan-fixture-new
python3 experiments/validate_matched_backend_fixture.py /tmp/jordan-fixture-new
python3 docs/validation/finger_cost_and_fixture_20261014/recheck_evidence.py
```

测试命令保留于 [suite_commands.json](suite_commands.json)。
[archive_check.json](archive_check.json)由保留的 `recheck_evidence.py` 生成，
实际读取压缩记录，重算不等式、每例操作求和、输入哈希、前缀数量、split
大小与统计，以及两份机械夹具汇总；这不是重新运行全部排序。

下一步应集中核对上述 gap/locality 归纳与局部表示修复，再实现受预算控制的
实际 pilot、冻结最终配置并重新确认双方共同输入资格。本轮没有改变最低交付
要求，也没有将 10 月 18 日冻结检查点自动视为通过。
