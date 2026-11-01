# 修改说明：用无插桩树重跑正式计时实验（2026-11-01）

## 0. 背景与目标

当前正式实验（measured version `4a83fa6`）计时的树后端带着两类插桩：

1. `_Tracked.__getattribute__` / `__setattr__`（`src/heterogeneous_finger_backend.py` 第 169–190 行；`src/heterogeneous_finger_split.py` 的 `RootedPiece`、`FingerPiece` 也继承 `_Tracked`）；
2. `observed(bucket)` 装饰器（第 157–166 行，共 21 处 `@observed`）。

即使 `detailed_work=False`，每次字段访问和每次被装饰的方法调用仍要多走 Python 层的判断。10 月 20 日的补充诊断显示，去掉两类插桩后树的中位时间明显下降（论文 `tab:results-hooks` 的 U 列）。

**作者决定：** 插桩只用于复杂度分析中的操作计数；正式计时改用**无插桩**的树。本说明描述完整的改动、验证、重跑和论文更新流程。

### 总原则（全程遵守）

- **不修改任何已有档案**（`results/`、`docs/validation/` 下已有目录、`output/pdf/` 已有 PDF）。旧的正式实验结果保留，并在论文中作为"插桩配置"的结果继续报告。
- **算法代码只有一份。** 无插桩版和插桩版必须由同一份方法源码生成，禁止复制算法方法后再删插桩。
- **先写协议，再跑实验。** 第 1 步的协议文件提交之后才能开始校准和正式采样。协议中的规则在看到结果后不得修改。
- **无论结果偏向哪个后端，都照实报告。** 不得因为结果调整输入、batch 规则、统计方法或排除样本。
- 输入集、随机种子 `20261015`、预热次数、batch 数、交替顺序、统计量定义保持与原协议一致；只有树的配置和电源条件改变。
- 修订记录用中文写，风格与 `docs/thesis/supervisor_revision_20261102.md` 一致。

---

## 1. 预先登记协议（先做，单独提交）

新建 `docs/plan/uninstrumented_rerun_protocol_20261101.md`，内容至少包括：

1. **目的：** 在不含测量插桩的树配置上重复配对计时比较；插桩版只用于操作计数。
2. **被测配置：**
   - `ordinary_list`（不变）；
   - 新后端名 `heterogeneous_finger_uninstrumented`：无 `_Tracked` 字段拦截、无 `observed` 包装，`detailed_work` 必须为 `False`。
   - 默认两组对比（list vs. 无插桩树）。旧的插桩树**不**作为第三组加入本次实验，其结果引用已有档案。
3. **输入：** 与原实验完全相同的 140 个 common 输入和 12 个 targeted split 输入（同一 selection SHA-256）。
4. **流程：** 等价性验证 → qualification → 校准（同一 B 阶梯 1…128、三批、两后端中位批时长均 ≥ 10 ms 的第一个公共 B）→ 正式采样（种子 `20261015`，每后端 5 次预热，20 个配对 batch，按输入序号和轮次交替先后）→ 独立档案验证。
5. **环境要求：** 同一台 Apple M4、CPython 3.12.14；**接通电源**；**低电量模式关闭**；采样期间不运行测试、编译或其他实验。
6. **统计：** 与原实验相同（每输入每后端 20 个 batch 的中位数、R7 四分位、输入内 tree/list 比值；跨输入汇总仅作描述）。不剔除离群值，不重跑、不替换输入。
7. **报告承诺：** 结果无论方向如何都写入论文；旧插桩结果保留为单独小节；两次实验不合并统计。
8. **失败处理：** 任一输入在 qualification 或正式采样中输出错误，停止并记录，不得跳过该输入继续。

提交信息示例：`Preregister uninstrumented tree timing protocol`。

---

## 2. 代码：同一源码生成两种树配置

### 2.1 要求

- 在 `HeterogeneousFingerBackend` 增加构造参数 `instrumented: bool = True`。默认 `True`，保证所有旧实验、旧测试和旧 backend identity **不变**。
- `instrumented=False` 时：
  - 节点、句柄、header、split piece 对象的类型**不**带 `_Tracked` 的 `__getattribute__` / `__setattr__`；
  - 被 `@observed` 装饰的方法调用直接进入原函数，不经过包装层；
  - 若同时传入 `detailed_work=True`，抛出 `ValueError`（无插桩版无法计数）。
- 新后端注册：
  - 在 `experiments/matched_backend_fixture.py` 的 `backend_spec` 中增加 `heterogeneous_finger_uninstrumented`，对应 `SiblingBackendSpec(HeterogeneousFingerBackend, (('detailed_work', False), ('instrumented', False)))`；
  - 新协议使用新的 `BACKENDS` 元组 `('ordinary_list', 'heterogeneous_finger_uninstrumented')`，在新的协议模块里定义，**不要**修改 `common_input_protocol.BACKENDS`，否则旧档案验证会失败。

### 2.2 实现提示和陷阱（请先阅读源码再动手）

- **`__slots__` 布局冲突：** `_Tracked` 定义了 `__slots__ = ("_ledger",)`。如果用"插桩类 = `_Tracked` + 无插桩类"的多重继承，而两个基类都有非空 slots，Python 会报 `multiple bases have instance lay-out conflict`。可选做法：
  - (a) 把 `_ledger` slot 移到无插桩基类中（无插桩时不赋值或置 `None`），让 `_Tracked` 的 slots 为空，再定义 `class TrackedInternalNode(_Tracked, InternalNode)` 等；
  - (b) 用工厂函数 `make_node_classes(instrumented)` 从同一组方法定义生成两套类。
  - 选哪种由你根据源码判断，在修订记录里说明理由。
- **`isinstance` 检查：** `heterogeneous_finger_split.py` 多处使用 `isinstance(node, InternalNode)` / `isinstance(node, ExternalLeaf)`。两套类都必须让这些检查保持正确。最简单的做法是让无插桩类保留原名作为基类，插桩类作为其子类。
- **对象创建：** 所有创建节点、句柄、header、`RootedPiece`、`FingerPiece` 的地方，都必须通过 backend 当前选择的类族来创建，不能硬编码类名。逐一检查两个模块里所有构造调用。
- **`observed` 包装：** 推荐在构造时由 backend 选择方法：无插桩时绑定 `function.__wrapped__`（`functools.wraps` 已提供），或者只在插桩子类上应用装饰器。不要在每次调用时再做运行时判断，否则开销又回来了。
- `_UNOBSERVED`、`WorkLedger` 在无插桩路径上不应被访问；如果某处无条件调用 `self.work.xxx`，需要确认它在无插桩下不会出错，也不会产生开销。

### 2.3 自检：无插桩版确实没有插桩

在测试中断言（无插桩 backend 实例创建并运行一次排序后）：

- 所有树对象的 `type(obj).__getattribute__ is object.__getattribute__`，并且 `type(obj).__setattr__ is object.__setattr__`；
- backend 上原先被 `@observed` 装饰的 21 个方法，实际调用到的函数对象等于其 `__wrapped__`（或没有包装层）；
- 插桩版（默认参数）的行为和 identity 与改动前完全一致。

---

## 3. 等价性验证：两个版本执行同一套算法

复杂度计数来自插桩版，计时来自无插桩版，所以必须证明插桩只旁观、不改变控制流。

新建 `tests/test_uninstrumented_tree.py` 和 `experiments/validate_uninstrumented_equivalence.py`：

1. **全部旧测试通过**（`tests/` 全量），且插桩版的结果与改动前一致。
2. **输入集合：** 140 个 common 输入、12 个 targeted 输入、40 个 seeded supplement 输入（`n ≤ 1500`）。
3. 对每个输入，在 `checked` 策略下分别运行插桩版（`detailed_work=False`）和无插桩版，比较：
   - 输出完全相同；
   - checked 策略记录的 trace（stage 结果、split / insert / ownership transfer 序列）逐项相同；
   - 每个完成前缀处的 audit 均通过。
4. 再在 `minimal` 策略下比较两者输出。
5. 另取一个插桩版 `detailed_work=True` 的运行，确认其 trace 与上面两者相同。这一点说明打开计数也不改变执行路径，所以计数结果适用于无插桩版。
6. 结果写入新目录 `docs/validation/uninstrumented_equivalence_20261101/`，包括 README（中文）、机器可读 JSON，以及源码版本 hash。

---

## 4. Qualification

- 以 `qualify_common_inputs_v2.py` 的流程为基础，使用新后端元组，分别对 `common` 和 `targeted_split` 两个数据集运行。可以通过新增参数或新的协议模块实现，**不要**改变旧协议的 identity。
- 两个后端都要通过；输出到新目录（例如 `results/uninstrumented_qualification_20261101/`），并用对应的 `validate_*` 脚本独立验证。
- 记录 production source hash；之后校准和正式采样必须使用同一 hash，否则作废重来。

---

## 5. 校准

- 使用 `experiments/matched_measurement.py --stage calibration`，规则与原实验相同。无插桩树更快，B 值可能变化，这是预期的，照实记录。
- 输出到新目录，并独立验证。

---

## 6. 正式采样（需要作者本人在 Mac 上执行）

### 6.1 环境门槛（在代码中检查，不满足就拒绝开始）

- 当前采集环境的代码（`experiments/qualify_common_inputs.py` 的 `environment()`）只记录 `pmset -g batt`。新增记录 `pmset -g`，并解析：
  - 电源来源必须是 `AC Power`；
  - `lowpowermode` 必须为 `0`。
- 不满足时报错退出，并提示作者接通电源或关闭低电量模式。
- 两项都写入档案的 environment 字段。

### 6.2 执行

- `matched_measurement.py --stage formal` 需要 manual-review receipt。**这份 receipt 必须由作者本人确认后创建，Codex 不得代填。** 请为作者准备一份清单，说明需要确认哪些内容。
- 先跑 `common`，再跑 `targeted_split`，两次之间不运行任何其他任务。
- 正式采样过程中出现任何错误输出，按协议停止。

### 6.3 独立验证和分析

- 用现有的验证和分析流程（参照 `final_review_formal_20261015` 的做法）从原始样本记录重建中位数、四分位数和比值，并与验证器结果对照。
- 新建 `docs/validation/uninstrumented_formal_20261101/`（实际执行日期以实际为准），README 写明：环境、源码 hash、两数据集的样本数、全部输出正确与否、主要统计量。

---

## 7. 论文修改

**所有新数字必须直接来自第 6 步的档案，不得手填或估算。** 旧数字仍来自旧档案。

### 7.1 术语

- "measured tree" 改为两个明确的名称：**instrumented tree**（带插桩，用于操作计数；旧正式实验）和 **uninstrumented tree**（无插桩，新的正式计时）。
- 保持上一轮的术语约定：正文不出现 frozen、v2、matched、access hooks、post-review；commit hash 只放在附录 B.1。

### 7.2 各章

| 位置 | 修改 |
|---|---|
| `frontmatter/abstract.tex` | 主要结果换成新实验数字（约数写法同上一轮：比值保留一位小数）。保留一句说明：带插桩配置下树更慢（中位约 2.9 倍），说明插桩开销。末句的结论按新结果改写，不得预设方向。 |
| `chapters/introduction.tex` | Contributions and Findings 中的数字和表述按新结果改写。顺带修复第 23–30 行的重复：September 一段后另起一段，删去重复列举两个后端的句子，改为 "Both backends share one Python core for the 1990 procedure." |
| `chapters/implementation.tex` 第 262–282 行（Execution Policies） | 改为描述两种树配置：插桩版用于操作计数，无插桩版用于计时；两者由同一源码生成；等价性验证结果（第 3 步）及其范围。保留现有对 `_Tracked` 机制的准确描述。 |
| `chapters/methodology.tex` | 新增一小段说明为什么计时不用插桩（插桩属于测量工具）；说明协议在采样前登记（引用第 1 步文件）；更新环境描述：接通电源、低电量模式关闭。 |
| `chapters/results.tex` | 主结果表、比值、结构分组、targeted split、variability 等全部换成新实验数据。新增小节 "Instrumented Configuration"，简要报告旧实验的结果（数字来自旧档案），作为插桩开销的正式证据。原 "Supplementary Instrumentation-Hook Diagnostic" 小节保留但缩短，定位为促成本次重跑的早期诊断。"What the Comparison Shows" 按新结果改写。 |
| `chapters/limitations.tex` | 删除或改写"电池供电"相关句子，改为本次已接通电源、关闭低电量模式。新增一句：M4 有性能核和能效核，macOS 不支持绑定核心，少数相对 IQR 较大的单元可能与调度有关，但未经验证。插桩版与无插桩版的等价性只在所测输入上验证过。 |
| `chapters/conclusion.tex` | RQ2、RQ3 按新结果改写；Further Work 删除 "qualify a production hook-free configuration"（已经完成）。 |
| `appendix/claim_traceability.tex` | B.1 增加新实验的源码 hash 和档案路径。B.2 AI 使用记录增加两条：(1) 11 月 1 日 Claude（Anthropic）审阅建议正式计时改用无插桩配置，并给出本修改说明；(2) Codex 完成的实现、验证和论文修改范围。 |
| 图表 | 所有基于旧正式数据的结果图，需要新增或替换为新数据版本；实验流程图（`figures/source/current_experiment_pipeline.tex`）加入"等价性验证"步骤。 |

### 7.3 编译与交付

- 完整编译（LuaLaTeX + Biber），要求无警告、无未定义引用、无 overfull/underfull box。
- 逐页渲染检查，重点看摘要、结果章各表、新小节、局限章和附录 B。
- 输出新 PDF：`output/pdf/Wang_Thesis_Draft_<实际日期>.pdf`，同时更新 `config/metadata.tex` 里的 `\ReviewDraftDate`。
- 新建修订记录 `docs/thesis/uninstrumented_revision_<日期>.md`，格式参照 `supervisor_revision_20261102.md`。
- 核对：公式、定义、引理、定理和证明环境与本轮开始前一致（附录 A 的证明不应改动）。

---

## 8. 验收清单

- [ ] 协议文件在第一次校准之前已提交（看 git 时间戳）
- [ ] 默认参数下插桩版 identity、行为、旧测试全部不变
- [ ] 无插桩版的自检断言通过（无 `_Tracked` 拦截、无 `observed` 包装）
- [ ] 192 个输入上，插桩与无插桩的输出和 checked trace 完全一致
- [ ] 两个数据集的 qualification 通过并独立验证
- [ ] 校准和正式采样使用同一 source hash
- [ ] 正式采样档案记录 AC Power 和 `lowpowermode 0`
- [ ] 全部正式样本输出正确；统计量由原始记录独立重建并一致
- [ ] 论文中每个新数字都能追溯到新档案，旧数字追溯到旧档案
- [ ] 旧档案和旧 PDF 未被修改
- [ ] 论文编译干净，新 PDF 已生成，修订记录已写

## 9. 不要做的事

- 不要修改旧协议、旧 `BACKENDS`、旧档案或旧 PDF。
- 不要复制算法方法来构造无插桩版。
- 不要在看到结果后修改协议、输入、B 规则或统计方法。
- 不要代作者创建 manual-review receipt，也不要在电池供电下开始正式采样。
- 不要修改附录 A 的证明内容。
- 不要把新旧两次实验的数据合并统计。
