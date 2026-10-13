# 可关闭详细记账、实际成本依据与定向完整排序验证

本次工作包父基线为 `d6622ce976b8b71d3dbe23618606d6d471e32069`。精确生产源码和验证程序 SHA-256 见 [provenance.json](structural_campaign/provenance.json)，测试及归档身份见 [verification.json](verification.json)。父基线本身不包含本次开关实现。

本轮关闭“详细账本不能关闭”这一阻塞，扩大真实主循环的复杂分裂覆盖，并给出源码循环的保守成本说明。**高效后端最低交付、一般性摊还论证、最终共同输入资格与正式计时仍未完成；`timing_ready=False`。** 没有修改论文、旧实验或旧验证归档，没有启动 140/380 输入正式批次。

## 实际代码变化

`HeterogeneousFingerBackend(..., detailed_work=False)` 不分配逐字段 bucket/phase 字典；正常节点字段访问不调用计数字段读写；操作/phase 装饰器直接进入原函数，不建立前后账本快照和逐操作报告。显式 phase 使用共享空上下文。关闭后的 `work.snapshot()` 明确抛出异常，不返回会被误解为“零成本”的数值。

算法、局部几何检查、pending fence、必要 `stage_results`、失败后丢弃状态的语义保留。树默认仍开启详细账本，普通列表默认选择不变。通过已有不可变 spec 配置即可使用关闭路径：

```python
from heterogeneous_finger_backend import HeterogeneousFingerBackend
from sibling_backend_contract import SiblingBackendSpec
from paper_jordan_sort import paper_jordan_sort_valid

backend = SiblingBackendSpec(
    HeterogeneousFingerBackend, (("detailed_work", False),))
output = paper_jordan_sort_valid(valid_input, "minimal", backend=backend)
```

replay 仍新建同类、同配置实例；创建与状态验证检查配置是否匹配，不能悄悄忽略参数。`detailed_work` 和 `work.enabled` 的公共属性只读。属性包装、开关分支、显式无操作 `add/allocate` 调用等残余开销仍在，不宣称零开销。

原 `SplitWork` 四字段观察与详细账本解耦：`count_operations=True` 时仅有两个 split 局部累计器统计比较与叶检查，再按原语义报告复制量零和转移规模。`minimal` 不分配这两个累计器。开关不改变 metrics schema、trace、高层计数和执行阶段状态。

## 测试与故障验证

| 本轮实际运行的套件 | 方法数 | 边界 |
| --- | ---: | --- |
| [树与配置回归](tree_configuration_tests.log) | 80 | 新增 12 项记账开关检查 + 原 53 项真实树操作 + 原 15 项完整排序接入 |
| [现有核心回归](core_tests.log) | 173 | 普通列表、策略、路由和资格工具；不计作新增真实树测试 |
| [实验消费方回归](consumer_tests.log) | 125 | 现有 runner/validator/protocol 的回归，不是正式实验 |

合计 **378 个方法、0 跳过**。早期调试重复运行不重复计数，未执行全仓库所有测试。新增测试包括：

- 五种执行策略下，镜像真实 split 与 z1 案例的外部输出、逻辑/物理结构、必要阶段状态、backend_work、metrics、trace 全部对照；同时执行完整状态检查与 replay。
- 把详细账本字段读写、snapshot、observe 和 phase generator 改为抛错，关闭配置的执行与 replay 仍通过；关闭模式的 buckets/phases/last_operation 始终为 None。
- 长度 3–7 的全部 678 个 oracle 合法排列，分别运行开/关的 minimal，对照外部输出、完整状态/replay 并比较状态；这些是一个测试方法中的子案例，不再累计成额外方法。
- 故意令 adopt 抛错或不清理 pending，两个配置均拒绝继续输出；只清理局部观察器，不把损坏的算法状态恢复成成功。非法 anchor、破坏 rank、错误或被篡改的配置同样拒绝。
- 同配置 fresh replay 的实例与 registry 不共享；counted split 的高层观察与开启账本的实际计数相符。

## 冻结的结构案例

[验证程序](../../../experiments/validate_finger_work_modes.py) 在第一例执行前写入 [config.json](structural_campaign/config.json) 与源码身份。长度为 `128/129/256/257/512/513`，每个长度固定 balanced、skew、repeated 三种构造，共 **18 个输入**；偶数长度用原方向，奇数长度用镜像并增加一个末点。构造规则先在小例中检查结构作用，再冻结本次列表，没有按运行时间筛选。

- balanced/skew：递增不相交 sibling pairs 后加入跨越指定间隙的更新，分别选中约一半和一个 pair；外层包围 pair 提供有限 owner。
- repeated：固定八点模板在不相交区间重复，再加两层包围，产生有限 owner 下的连续转移、旧输出列表上的继续插入与再次分裂。
- 没有随机种子、候选淘汰或替补；每个配置只生成一个确定输入并由 oracle 独立确认合法。单例预算 180 秒，整批 900 秒，任何错误或超时立即停止后续案例并保留状态。超时不算通过。

18 个输入均 PASS，18 个输入哈希不同；它们仍是相关构造和镜像，**不是 18 个统计独立样本，更不是 140/380 正式比较集**。[summary.json](structural_campaign/summary.json) 记录源码执行期间未变。

每个输入执行普通列表、真实树记账开、真实树记账关，各自 checked 与 minimal，共 **108 次原始执行**，另有最终状态审计引发的 replay。三个 checked 配置都在每个完成前缀分别对照外部 `sorted(prefix)`、独立最小包围 parent 几何模型与后端结构审计。两个树配置的各前缀输出/结构/阶段快照以及最终完整状态、trace、metrics 逐项一致。minimal 分别检查最终外部输出、几何、完整状态与同配置新实例 replay；本次大结构程序没有在每个前缀另跑完整 replay。

以下数量按**每一种 checked 后端配置的原始运行**汇总，三种配置得到相同值，但不相加；minimal 与 replay 不再累计：

| 覆盖项 | 数量 |
| --- | ---: |
| 完成前缀 | 5,349 |
| 实际 split（全部在 finite owner 下） | 460 |
| 两侧都非空 | 230 |
| 在此前 split 输出列表上继续端插 | 666 |
| 对此前 split 输出列表再次分裂 | 212 |

每个案例都有同一 finite owner 的多次转移；这是按案例计的 18 次 owner 覆盖，不是全局唯一对象数。最大的均衡两侧为 `126:127`，不均衡两侧为 `1:252`，镜像反向对应；重复模板的两侧非空次数在三个偶数长度分别为 `15/31/63`，相应奇数镜像相同。观察到的增长不用于证明复杂度。

## 归档、资源与成本边界

`structural_campaign/*.json.gz` 保存每例完整输入、输入哈希、每种运行的最终输出、每前缀快照摘要、最终状态摘要、覆盖计数和非空分裂两侧大小；开启配置另存 operations/queries/audit 三类账本。输入 SHA-256 的定义为 UTF-8 编码的 `repr(values)`，源码与文件清单为原始字节 SHA-256。程序先在内存中比较完整对象，再保存摘要；没有把完整 trace 事件或所有树快照存档，可通过固定输入和程序复跑。

[manifest.json](structural_campaign/manifest.json) 绑定该子目录的输入请求、压缩报告、config/provenance/summary；它不包含后来加入的本 README 和测试日志，后者由顶层 verification 单独绑定。[archive_check.json](archive_check.json) 另行解压全部 18 例，验证文件/源码/输入哈希、外部最终输出、前缀连续性、开关摘要一致、非空计数与大小条目数一致，以及归档报告的汇总。它**没有重新执行算法或从未存档的 trace 独立重建所有事件计数**。

原始 `worker_resource_wall_seconds` 包括输入构造、oracle、六次执行、检查及 replay，只用于资源可行性。整批 worker 合计约 221.2 秒，最长约 29.3 秒；回归测试在此批结束后才启动。这些值既不是排序耗时，也不能用来比较两个后端或两个开关的速度。tree 的 checked 还包含完整森林检查，与普通列表的检查负担并不相同。树账本没有覆盖共享核心全部 Python 工作，replay 的另一实例账本也未合并。

[源码成本说明](../../development/heterogeneous_cost_bounds_20261013.md) 给出真实路径范围，先按 `O(H²)` 支付 split 的逐段 join 和另一 rib 行走；在陈述的红黑/局部修复、单位成本及字典假设下得到保守的 `O(log²(m+1))` 单次界与 `O(n log²(n+1))` 整体界。它不是目标的较小侧敏感摊还界或线性总界，也不是完整正确性证明。下一步仍需收束这些摊还与 locality 缺口，并验收正式实验流程和最终输入资格。

## 复跑入口

```sh
PYTHONPATH=src:experiments:tests python3 -m unittest test_heterogeneous_work_configuration -v
python3 experiments/validate_finger_work_modes.py --output /tmp/jordan-work-modes-new
```

输出目录必须不存在；完整测试命令及解释器身份见 `verification.json`。本轮没有复跑旧 16 例探测或整套旧 704 例程序，没有编译论文，没有形成任何新排序性能结论。
