# 后端接入与成本验收表（2026-10-11）

原始代码审阅基线：`b6a407461c2f94a4b491016376861142f4b14577`。本地合并基线：`fa67fc664d7515b2504d355e35fadcfd23f16534`；下面两项源码及后端规格的 blob 身份在两基线间未变。另核对 `paper_jordan_sort.py` 与 `paper_execution_policy.py` 身份未变。这是源码审阅与待实施契约，不是实现报告；本轮没有修改生产源码。

## 1. 依据与来源层级

- `src/paper_jordan.py`，blob `97d9a4809c7aaafe7fbad1a7c120cc24521c8d17`：读取初始化/状态类型、状态审计、trace/指标推导、Step 3 和相关访问检查。
- `src/sibling_list_backend.py`，blob `75153800a67801cff15fd38e7825595f3a21d8f5`：读取对象表示、audit_snapshot、端插、split 与 ownership 提交路径。
- `docs/development/heterogeneous_finger_backend_spec.md`，blob `d98ca692a2a8d7db893e2f712ad5a2c93875452e`：既定目标表示/接口与文献界；本轮未重新逐页核对原论文或勘误，也未闭合其证明依赖。
- 10-11 用户确定的最低范围。16 例仅普通列表探测现已有 [可核验归档](../validation/cost_and_qualification_20261011/README.md)；本轮重跑身份与记录核对，未重跑这些输入的 checked/replay。该归档不能替代新后端或最终版本的资格检查。

下表中的源码区间以该 commit 为准，后续改动后需要更新。表已覆盖所读核心依赖，但不声称完成全仓库动态访问审计；外部实验验证器和故障注入测试的调用扫描仍须补齐。

## 2. 从调用位置到工作与成本

| ID / 调用位置 | 前提 / 当前依赖 | 拟议接口与实际维护工作 | 成本/检查依据与状态 |
| --- | --- | --- | --- |
| C01 `PaperJordanState`、`_initialize_paper_jordan_state_values`（约 110—260） | 直接构造 `OrdinarySiblingListBackend`；state.pairs 与 backend 共享 PairRecord 身份 | backend factory；稳定 PairHandle/PointRef；两 family dummy 与初始 singleton | 建立 O(n) points/初始化范围明确；字典成本不能无条件写成确定最坏 O(1)。待实现 |
| C02 `_validate_initial_backend_postconditions`（263—306） | 检查 eager parent/list、child_sibling_list_ids、pair_ids=[id] | 初始常数个 header、边界引用和 owner slots 的局部后置检查 | 不需要为 2 个 singleton 物化所有 registry；待适配 |
| C03 `_boundary_selection`、`_validated_boundary_pair`、`_validated_live_finite_pair`（1570—1695） | finite boundary 经过通用 live 检查；`.count(pair_id)` 扫描完整 sibling list | 区分身份/端点验证、enclosing 分支与 locality 合法的 `boundary_list(pair, side)`；不能对所有 finite pair 强制端点查询 | 当前 O(l) 扫描实际存在；locality 逐调用核实尚未完成，不得将任何内部 pair 爬树藏成 O(1) |
| C04 `_step3a`（约 1290—1370） | 新 pair 注册；enclosing 用 make_list，其他用端插；结果和 trace 读取 `new_pair.parent_pair_id` | make_list / insert_boundary 返回或可常数访问本次 header/owner；同时构造阶段结果；同步稳定 registry | 端插目标为规格摊还 O(1)，实际成本/证明待真实实现。不能为了得到结果字段再次扫描 |
| C05 `_step3b`（约 1374—1485） | 读取 boundary.sibling_list_id、pair_ids 首末与长度；调用 split_pairs_at_value | 按 increasing/decreasing 验证所需端；split_value + adopt_split；size 从真实维护元数据获得 | split 目标见成本表；不得 materialize 出 pair_ids 再切分。两侧集合守恒在完整审计检查 |
| C06 `_step3c_base_anchor`（约 1770—1811） | 选 child_list_ids 首末、pair_ids 首末；随后调用通用 live/parent 检查 | extreme_child(parent, side)；从至多两个 child slots 选几何极端；局部验证 owner header | 目标 O(1) 只适用于有界 child slots+端点访问；两种 z1 调整及几何端点规则须保留 |
| C07 `Step3AResult/Step3BResult`、`_record_stage_result`、`_require_*_stage`（类型及 1730—1768、1814 起） | 阶段结果含物理 list/parent ID；stage_results 还控制执行顺序，并非仅 trace 功能 | 常数大小的执行令牌/逻辑结果；记录 split 前后身份和生存期；单独版本化诊断序列化 | 不能在 minimal 下整体移除；不得为记录整个列表而每步物化。具体 schema 待实现 |
| C08 trace、`_sibling_list_size`、`_record_step3b_trace`（1819 起） | len(pair_ids)、input/left/right IDs 和计数进入事件 | header.size 与逻辑身份；避免把 audit snapshot 混入 trace；标 schema 与版本 | 完整日志/计数可独立关；执行令牌保留。待适配与模式回归 |
| C09 `_validate_iteration_records`（约 498—670）及 `_validate_stage_results_and_trace` | trace 逐字重建；split_items_* 用 input_size 推导，绑定列表后端口径 | 区分高层语义计数与 backend 专属节点访问/复制/写入；不得给树后端自动加 l 次 copied | 旧指标保持历史语义；新 schema 明确字段适用后端。待实现 |
| C10 `validate_paper_jordan_state`（309—401）及 `_validate_configured_dummy` | 遍历所有 pairs；依赖 live ownership、registered IDs、同对象身份 | `materialize_audit()` 建临时逻辑 membership/parent 视图；检查守恒、包含、单一归属和 cycles；身份与逻辑关系分别查 | 完整审计允许扫描但不能计入 minimal；逐前缀/replay 总成本另记。真实审计未适配 |
| C11 `_validate_state_against_deterministic_replay` 调用及 `audit_snapshot` | 现有完整审计调用 same-core replay；旧快照含物理 IDs 和 eager 字段 | 同后端 replay 持有 backend identity；跨后端比逻辑视图不比物理 ID；新旧 schema 不能默默互认 | same-core 不是独立算法；本轮未逐行读取 replay 整个实现，调用者已确认，函数体与消费方扫描待补 |
| C12 普通后端 make/insert/split 的 owner 安全检查、失败路径 | split 成功提交前后检查、逐 pair rebind；前置安全不全是 O(1) | 新结构给出局部前置检查与成功后置条件；内部错误传播并丢弃状态；完整检查移到 checked 的边界须明确 | 不新增 rollback，不要求失败原子性；不因赶工删掉必要安全；完整调用路径与成本待验证 |
| C13 public sorting/diagnostics、实验工具与外部 validator | 所有入口必须选择同一个真实后端；不能发生运行 A 验证 B | 输入 manifest 增 backend/schema/source identity；检测模式、错误传播与输出恢复；回归外部证据验证器 | 公共调用/实验消费方的全仓库定位仍待做，不标已完成；双方最终源码重新资格审计 |

## 3. 可验收的成本表

令 l 为本次列表长度，k 为左输出长度，h 为结构路径长度，m 为相关操作序列长度。以下“目标”来自现有规格或该规格的工程目标；均非本轮对代码已证成的界。

| 操作 | 目标 | 必须计入的实际工作 | 验收证据 / 尚未闭合项 |
| --- | --- | --- | --- |
| make-list | 摊还 O(1)（规格引用文献） | 节点/header 分配，owner slots，两端引用、registry | 真实代码、分配与写入账本；实现与势能对应未完成 |
| 边界插入 | 摊还 O(1)（规格目标） | finger/rib 更新、比较、旋转、重着色、分隔 key、黑高与必要 size 维护 | 不能仅报旋转常数；若沿全部祖先更新，成本必须纳入。重平衡/摊还证明待闭合 |
| split | 摊还 O(log(min(k,l-k)+2))（规格目标） | 两端搜索、沿路径拆解/拼接、局部平衡、端点/元数据/分配 | 0/l 空侧、极不均衡、多次 split 的操作证据；原文依赖与真实代码证明未闭合；不能全树重建 |
| boundary ownership 查询 | O(1)，仅在已证 locality 的边界 handle 上（工程目标） | 端点反向 header 查询、owner/生存期检查 | 逐调用的 locality 前提 + 访问轨迹；任意内部 owner 查询不是此接口 |
| split 后 ownership 转移 | O(1)，只针对有界 header/slot 更新（工程目标） | 退役 header、旧两端清理、至多四个新端点绑定、旧/new owner slots | 与树 split 成本分开；不逐叶写 parent/list、不推迟为以后全扫描；family/cycle 前提待核实 |
| 元数据维护 | 每个实际修改节点 O(1)，总成本随修改路径计入所属操作 | key、color、black-height、size、rib 身份、两端引用同步 | “单节点 O(1)”不推出“整次操作 O(1)”；需要计数所有触及节点及论证 |
| 极端 child 查询 / 输出局部插入 | O(1) 局部访问目标，依赖有界 slots/稳定 handles | 几何端点选择，两个 z1 规则，链表指针修改 | 不能误把曲线第二端当几何右端；无额外扫描的调用验证待做 |
| 初始化、输出恢复 | 计入 O(n) 工作目标 | 全部输入/point handles 物化、初始局部排序、最终遍历输出 | 是否数组或字典需与实际代码一致；不能预排序全部输入 |
| 运行期局部检查 | 逐项列实际成本，不预设 O(1) | identity、有效性、membership、owner 链、slot 前提 | 当前 `.count()` 和可能的祖先检查不能忽略；replacement 的正确性和成本均需说明 |
| 完整 audit / replay | 不承诺廉价；非主计时 | 全量逻辑物化、守恒/包含/无环、前缀重放 | audit 通过不是独立算法证明，也不能让 main 依赖 audit 生成的 oracle 排序结果 |

普通列表端插当前两侧均构造新列表：`[pair_id, *pair_ids]` 或 `[*pair_ids, pair_id]`，并非尾端 `append()` 的成本。split 还包含分区、快照/复制、逐项 rebind 与前后检查。只加速树 split 不足以完成上述验收。

## 4. 可执行模型测试的准确范围

文件：`tests/test_finger_backend_contract_model.py`。标准库 `unittest`；当前 22 个测试方法，部分含 subtests（`afb9702` 首次导入时为 20 项，旧记录不改写）。默认对象是**显式命名的慢速有序列表参考模型**，不是新树，也不是现有 `OrdinarySiblingListBackend`。测试通过只能确认该参考与契约测试底座的行为。

计数细分为 18 项 `OperationContractTests` 和 4 项 `ModelAuditSelfTests`。将来使用 `--factory` 时，只有前 18 项改用外部适配器，后 4 项始终检查参考模型审计器；不能将两者总数写成真实后端测试数。普通后端已有的 155 项定向回归另记，不是其对本模型接口的适配验证。

覆盖：make-list；两端插入与非法 anchor；<=/> split 含空侧/不均衡/重复分裂；旧 handle 退役；稳定 Item 引用；两端引用变化；两 owner slots、adopt 方向/来源；逻辑 membership/顺序/守恒审计；模型审计对人为破坏的拒绝。

修订后另覆盖 `insert → split → adopt → 两端继续插入 → 再次 split/adopt → 再次插入`。同时检查 retained/acquired 两侧、左右镜像、空侧与 singleton 输出、旧 handle 退役和过时边界引用拒绝；每次有效更新与显式 item/owner 列表核对。两项交错测试含 12 个场景，不当作 12 个新的测试方法或 Jordan 输入。

测试使用抽象 key 与 opaque owner 标签，**不模拟 Jordan 的几何区间和 parent-family 树**。key 等于 cut 按通用 split 契约进入左侧；实际 Jordan `split_pairs_at_value` 不允许端点跨越/等于新点，其更强前提必须由后续几何测试和生产适配验证，不能混同。

测试适配器接口：make_list(Item, owner)、boundary_list(item_id, side)、insert_boundary(Item, anchor_id, side)、split_value(handle, cut)、adopt_split(old_owner,new_owner,left,right,side)、extreme_child(owner,side)，以及仅供测试的 items/get_item/owner_of_list/materialize_audit。side 为 left/right。适配器可翻译生产接口，不据此强制生产 API。

`materialize_audit` 的规范化结果只含 `(owner, tuple(item_ids))`，不比较物理 handle。invalid 前提检查的测试不要求失败回滚；失败实例不得用于新的有效操作。测试适配器如果采用异常类型翻译，应保持真实拒绝原因，不得吞异常或代运行参考模型。

```bash
python -m unittest discover -s tests -p 'test_finger_backend_contract_model.py' -v
python tests/test_finger_backend_contract_model.py --strict -v
# 后续真实适配器实现后：
PYTHONPATH=src:tests python tests/test_finger_backend_contract_model.py --strict --factory MODULE:FACTORY -v
# 验收入口的独立回归（使用假适配器，不是真实后端验证）：
python -m unittest discover -s tests -p 'test_finger_backend_contract_runner.py' -v
```

`MODULE:FACTORY` 是显式占位符，不是已存在模块；工厂不存在时 exit 2。`--strict` 从真实执行记录核对每个预期操作契约必须恰好成功一次，且整次运行无 skip、failure、error、expected failure 或 unexpected success；不满足时 exit 1，`contract_acceptance_passed=false`。只跑模型自检、筛选到零项、缺项或重复执行都不能验收通过。

JSON 的 `operation_contracts` 明确 subject、预期/开始/通过方法数、skip/failure/error、缺失与重复方法；`reference_model_self_tests` 分开报告模型自检。严格验收必需的是完整操作契约；可显式选 `OperationContractTests` 不跑模型自检，此时自检开始数为 0，不将其算作通过。参考模型也可执行 strict，其 scope 仍是 `reference_model_only`。

未指定 `--strict` 时是开发检查，允许筛选，保留 unittest 退出码规则，但验收标志始终为 false；`partial_check` 标记操作契约是否不完整。不能仅凭开发入口或 discovery 的 exit 0 宣称契约验收。15 项 CLI 回归验证拒绝行为，包括方法/子测试 skip、只跑模型、零项/部分/重复选择、expected failure、错误和分裂后插入失效的反例。详见 [修订验证](../validation/backend_contract_fix_20261011/README.md)。

所有模式仍明确 `backend_ready_for_timing=false`。即使将来真实适配器严格通过，也尚不代表 Jordan 接入与效率验证完成。

## 5. 明确未实现 / 未验证清单

| 项目 | 本轮状态 | 下一步 |
| --- | --- | --- |
| 真实 heterogeneous 节点、ribs、左右旋转、重着色 | 未实现于本变更 | 按原文/勘误实现，加入真实结构不变量与分支覆盖 |
| 真实 make/insert/split，按目标成本维护 metadata | 未实现于本变更 | 为实际对象接测试适配器，记录真实访问成本 |
| header/边界 ownership、任意内部访问消除 | 设计与调用清单，未实现 | 对 locality 前提作实际调用验证，关闭 C03/C05/C06 |
| stage_results/trace/metrics/schema 改造 | 已定位主要依赖，未改造 | 区分执行阶段状态与可关闭诊断，不按物理 ID 做跨后端比较 |
| logical audit、same-core replay 适配 | 未实现；replay 函数体/全部消费方仍待核对 | 补全读集，版本化快照，注入错误验证真实 auditor |
| Jordan 几何、family、无环、镜像、z1 回归 | 本模型不覆盖 | 用真实核心加专项案例与外部排序判据 |
| 普通后端对本模型的适配测试 | 未执行 | 建测试适配器再运行；不把本轮模型自检冒称旧后端回归 |
| 真实树端到端 split | 未执行 | 10-15 检查点：完整排序中非零 split 与正确输出 |
| 最终双方 140/380 资格和计时 | 未执行 | 固定最终源码和规则，双方重验；今天不跑大批 |
| 操作摊还证明与完整排序界 | 未证明 | 每条假设/真实工作/来源逐项核实，证明缺口不消失于曲线 |
