# 真实指尖树接入完整 Jordan 主循环

基线 `cc1aa2d85deb88e8d3231dd7042dc0d51595e8b2`。本轮修改共享核心与后端契约，并通过真实树端到端验证；不是 B 树重写，也不是仅开放后端开关。按这里记录的有界输入范围，10 月 15 日的“完整排序中执行非零真实树 split，输出、状态与同后端 replay 通过”检查点已取得证据。**高效后端的完整交付、一般性摊还论证和正式计时资格仍未完成。**

## 实际运行路径

`paper_jordan_sort_valid(..., backend="heterogeneous_finger")`、diagnostics 与 certified wrapper 均进入现有共享 runner，再由同一 Step 1/2/3 主循环使用真实树。默认仍是 `ordinary_list`。`SiblingBackendSpec` 继续拒绝 `sorting_ready=False` 的未完成类；新树的 `sorting_ready=True` 只表示完整操作可被路由，`timing_ready=False` 明确保留。正式实验 runner/协议本轮没有开放树后端计时。

- Step 3(a) 现在要求 Step 1 与 Step 2 都已完成。先检查插入目标/owner，再从另一边已选定的 finite boundary 取得未来 split source；包围前一点则记录 skip。该步骤只查询，不提前 split，不用 oracle 排名。
- 需要分裂时，检查 source 和插入目标是同 owner 的不同列表，将 `transfer_from` 传给 make/insert。插入后再次核对 source 的 live ID、owner 以及插入结果。`Step3AResult.transfer_source_list_id` 是所有模式都有的执行状态；trace 保持原 `jordan-trace-v1` 的诊断字段，Step 3(b) 事件已包含 source/output IDs。
- Step 3(b) 按原方向、原时机进行真实 split/adopt；调用前核对记录的 source、owner 和 target，不能换源或把已计划转移改成 skip。完成记录与转移意图的对应关系也在 trace 关闭时审计。
- 新的生产接口 `validate_iteration_complete()` 在 Step 3(c) 插入输出前执行。树在所有模式下拒绝未清除的 staged transfer/pending split；checked 模式在森林恢复后做完整结构审计。普通列表的 split/adopt 单次提交，没有这两类 pending 状态。
- complete-state validation 与 replay 沿原路径使用同类型、同配置的新树实例；同时比较逻辑和物理快照。测试明确检查新 registry、新 handle，构造失败不回退普通列表。

普通列表同步接受并校验 `transfer_from`；保留原 membership、ancestor 检查与 split 口径。阶段单测已补齐两侧选择；协调伪造 Step 3(b) 的旧测试也同时伪造新增 intent，确保 replay 仍能拒绝它，而非仅依靠新增字段不一致。

## locality 与中间态

| 查询位置 | 前提 | 查询 |
| --- | --- | --- |
| increasing 插入目标 | Step 1 的 finite pair 不包围前一点 | 该 pair 的 RIGHT boundary |
| decreasing 插入目标 | Step 2 的 finite pair 不包围前一点 | 该 pair 的 LEFT boundary |
| increasing 的未来 source | Step 2 的 finite pair 不包围前一点 | 该 pair 的 LEFT boundary |
| decreasing 的未来 source | Step 1 的 finite pair 不包围前一点 | 该 pair 的 RIGHT boundary |
| enclosing 分支 | 选择的 pair 包围前一点 | 直接用该 pair 作新 list 的 owner，不查任意内部 pair 所属列表 |

上述访问依赖论文边界选择与已完成森林的 child-group 不变量：相应的非 enclosing pair 应是该侧 child group 的端点。源码逐次检查端点身份、owner 相同及 group 不同，不通过上爬或扫描强行获取一个 owner。新增同 owner 检查覆盖的实际分支见下表；有限输入覆盖不能单独替代一般性 locality 证明。

Step 3(a) 后保留临时重叠，只允许局部查询及匹配转移；完整审计/完整快照仍明确拒绝。后端还保留已有操作契约允许的 staged parent 自身 child group 构造，但拒绝其他 owner 的无关列表更新，Jordan 主循环不插入这类额外步骤。split 后、adopt 前继续拒绝 header 查询、重复 split、注册更新和完整审计。adopt 清除两个 pending 后才进行完整森林检查及输出恢复。失败状态仍丢弃，没有回滚或重试。

## 可复跑证据

[新接入与原核心回归](integration_core_tests.log)：188 个方法、0 跳过，包含 15 个新真实树接入测试与原 173 个普通列表/路由/资格流程测试。[原真实树操作回归](operation_tests.log)：53 个方法、0 跳过。[实验消费方回归](consumer_tests.log)：125 个方法、0 跳过。三份日志合计 **366 个方法**，并非 366 个新树端到端测试；重复调试运行不累计。

新接入测试覆盖五种执行策略、真实 split 被实际调用且两侧非空、两个 z1 修正及镜像、逐前缀输出与稳定 handle/leaf、fresh-tree replay、缺少另一侧选择、错误 owner/source、伪造 split 成功仍有 pending、adopt/replay 失败传播，以及 minimal 正常主循环禁止全树物化/registry 枚举。未完成的树类和不存在的后端仍被拒绝，不静默替代。

[验证程序](../../../experiments/validate_heterogeneous_integration.py) 的 [summary.json](summary.json) 与 [逐输入记录](cases.jsonl.gz) 包含：

- 长度 0–7 的全部 oracle 合格排列，共 **682** 个；按长度为 `1/1/2/6/16/50/144/462`。不合格排列不属于 valid-input 算法定义域，未作为合法失败删例。
- 4 次固定结构输入运行，含 z1 与连续转移案例及取负镜像。
- 长度 16/32/64 的 flat、nested、incremental 各一例及其取负镜像，共 18 次；incremental 的 seed 固定为 `13000+n`。生成规则固定，没有观察性能后筛选。
- 合计 **704 次输入运行**，对普通列表和真实树分别执行 checked 与 minimal。镜像与仿射等价序列相关，不是统计独立样本；这不是 140/380 正式比较集，也不继承旧 16 例资格。

checked 的每个完成前缀分别对照外部 `sorted(prefix)`，检查无 pending；另用独立的 O(n²) 几何模型求同 family 的最小包围 parent，核对逻辑 owner、child groups 的守恒与顺序，再执行真实结构审计和同后端新实例 replay。minimal 独立运行，检查最终外部输出、几何模型与 replay，和 checked 比较最终物理状态、阶段状态。oracle、expected 和几何模型只在验证程序中使用，没有反馈进排序。

以下数量只统计每个输入的原始 checked 主循环，**不把 minimal 重复运行或 replay 的 split 再累加**：

| 每个后端 | 数量 |
| --- | ---: |
| 通过外部检查的完成前缀 | 3,728 |
| 实际 Step 3(b) split | 1,300 |
| 两侧都非空的 split | 62 |
| z1 boundary 调整 | 400 |
| z1 output 调整 | 152 |

| split 分支（每个方向数量相同） | dummy owner | finite owner |
| --- | ---: | ---: |
| singleton 插入后转移 | 490 | 86 |
| 边界插入后转移 | 63 | 11 |

这些相同计数反映相同控制流；正确性的依据是**两个后端各自通过外部输出与几何检查**，而不是两者相等。same-core replay 仍只是执行一致性检查，不是独立算法证明。

## 工作量边界与后续

新增预检和复核在树上只查询端点、header、固定数量的 slots/几何字段；未引入全量成员扫描或逐叶 ownership 重绑。普通后端重复 membership 检查的实际成本仍存在，不能沿用历史计时来代表修改后的版本。树的 checked 在每次输出插入前额外审计完整森林，和普通后端的检查负担不同，不能把差异全部解释为树结构速度。

原始记录保存当前真实调用的 checked/minimal WorkLedger 三类 bucket（operations/queries/audit），包含初始化与各自显式验证，replay 使用另一个账本，不在这些值内。这些是诊断工作观察，既不是墙钟时间，也不是全部 Python 工作量。核心的所有比较/分配没有统一计入树账本。

**WorkLedger 在 minimal 下仍始终开启。** `rib_child` 的另一 rib 行走、组件转换、逐段 join、根处理与文献势能的完整对应仍未闭合。本次不新增更大 standalone split 曲线、不声称较小侧敏感摊还界已证成、不做新性能比较。

接下来应扩大真实算法资格覆盖，并核对上述成本；建立无详细记账路径、证明其行为一致，再验收正式 runner/validator/pilot 并按最终源码确认共同输入资格。论文精修与 140/380 大批正式实验本轮未执行；历史操作/计时证据及论文文件保持原样。

## 复跑与身份

```sh
PYTHONPATH=src:experiments:tests python3 -m unittest test_heterogeneous_sort_integration -v
python3 experiments/validate_heterogeneous_integration.py --output-dir /tmp/jordan-integration-new
```

输出目录必须不存在；出现合法输入错误即停止，未捕获成跳过或删除输入。只有完整成功才写出 `accepted=true` 的 summary。summary 绑定源文件 SHA-256，并检查验证期间源码未变化；HEAD 为本次工作包的父基线，不能把基线本身误称为已含本实现。`verification.json` 记录完整测试命令、日志与源码身份，以及对压缩逐例记录的独立解压核对。
