# 导师反馈后的开发阶段（2026-09-21）

## 基线与阶段边界

实际 fetch 后 main、HEAD、origin/main 均为 `4a18f3942ee4d45ba22198911437a80d2806033f`。默认分支 main。开始时唯一未提交文件是英文 PPT；其字节哈希受保护，未修改。未发现适用 AGENTS.md。导师反馈是扩大输入、不需要 rollback、后端及操作界尽量靠近原论文；本文件中的阶段、预算和数量是工程决定，不是导师指定的要求。

本轮完成核心简化、相关回归、实际非计时预检与后端设计；完整 finger-tree 实现和正式 timing 在下一阶段。没有把旧“不得修改核心”限制套用到本轮。没有 commit/push。

## 已实现：去掉恢复机制，保留成功语义

`src/sibling_list_backend.py` 的 commit_split 删除旧 owner child-list 副本、全部 pair ownership 备份字典、旧 next-id 备份及 except 恢复分支；`src/paper_jordan.py` 的 Step 3(a) 删除异常后注销注册 pair 的分支。只服务于该恢复分支的 unregister_unowned_pair API 删除，没有另一份旧 core、rollback=False 开关或隐藏恢复 helper。

失败约定：廉价必要前置条件继续先检查；发生更新或不变量错误，异常传播并终止排序；调用方丢弃状态，不恢复、不重试、不返回部分输出，也不转用 sorted/oracle/reference。公共排序成功结果不变，内部注销 helper 不再存在。docstring 已同步。

保留 SplitPlan：它计算边界分区，保存 original/left/right 标识来拒绝 stale plan，并验证连续顺序和集合守恒；并非只用于回滚。保留 staged output lists、正常分区复制、owner 的新 children slots，这是正常更新及前置校验所需。保留 audit_snapshot、确定性 replay 的只读快照和验证器文件写入 temp/replace；后者是文件可靠性，与算法恢复无关。

小规模分支、前三点初始化、A_i/B_i、镜像、几何端点、z1 boundary adjustment 和 output-anchor correction、两 family 的 parent/list 不变量均未改变。输出仍从维护的 partial order 恢复；core 不接收期望答案。checked/minimal policy 文件没有改变，完整 checked 仍保留每前缀 replay。

成功 trace 和现有逻辑 operation counters 的定义没有改变；它们从来没有精确记录恢复备份的 Python 成本，所以相同计数不意味着旧新耗时相同。历史 timing 只描述旧实现，不能拿来报告新实现速度。

## 测试约定变化

保留所有正常 split/ownership/排序和先拒绝坏参数的测试。仅变更恢复相关断言：

- 删除两个 unregister_unowned_pair 测试，因为对应恢复专用 API 已删除。
- Step 3(a) 原“注册回滚”测试改成错误传播、注册可能已发生、必须丢弃状态。
- checked 最终 invariant 注入失败、minimal 局部 postcondition 失败及 ownership corruption 的三个 split 测试，不再要求状态还原；仍断言错误，且不继续使用失败对象。
- 新增公开排序 checked/minimal 与 diagnostics 的错误注入，验证同一异常传播、split 只尝试一次、output recovery 未调用。
- 新增要求中的小输入、端点例子、z1 例子及其镜像，两策略用新副本，分别对外部 sorted 判据检查。

基线 168 项相关测试全部通过；首次修改后 166 项中唯一失败来自尚未改写的旧恢复断言，已修复测试约定，不是有效输入排序错误。修改后相关 168 项通过。新预检生成器的首次测试发现六点块的密度仍属于 low，改为八点 medium excursion；没有修改分类阈值或 core 算法。4 项生成器/去重/拒绝覆盖测试随后通过。

## 下一轮计时任务（明确尚未执行）

当前入口是 `experiments/preflight_next_stage.py`；复用已有 extended validator 的 bounded worker、oracle、完整 checked diagnostics、minimal 新副本、外部结果比较、coverage 与 summary。结果目录拒绝覆盖；run config 在新样本生成前固定，记录 dirty HEAD、源码哈希、工作区 patch。旧 validator 的历史 source gate 没有放宽；本轮不重放旧版本归档。

下一轮优先普通列表 minimal 与 Python sorted，不等待 finger-tree。工程目标是 **380 个唯一 rank 输入**：32/33、64/65、128/129、256/257、512/513 十规模，每规模最多 2 个严格 flat、12 low、12 medium、12 heavy。这是待资格验证的 300–600 范围目标，不是统计充分性或导师指定数。strict flat 缺额不能靠数值缩放补位；反射保留 base identity，作为配对样本，不能宣称独立随机抽样。

首先将 block 构造推广到预先固定的可变偶数 excursion 长度和间隔，用预注册 seed 范围产生候选；与固定 seed incremental pool 分开计数。先生成并按实际 profile 分类、rank 去重，冻结候选表，再审计，再 timing。每格候选预算及保留顺序预先固定；不能看到排序速度/错误后换种子补位。报告所有重复、invalid、资源失败和格缺额。新的生成规则必须先在小规模 oracle/穷举下验证，而不是直接复制现有少数 block 形状凑 380。

资源资格：本轮只代表性检查 512/513 的 flat/low/medium；其 heavy、256/257 代表输入以及 1024/1025 尚须分预算预检。完整 checked/replay 每候选一次，上限 180 秒，按独立审计批次设置总预算；超时停止该批并保留状态，不能作为输出错误或通过，也不能偷偷减轻 replay。大规模资格未齐前，不启动最终完整主表。

计时实施入口：新建 `experiments/run_expanded_timing.py` 与独立 config/run dir，复用现有 runner 的记录/输出检验逻辑，不修改冻结 Week12 gate。首个实现任务是接受冻结输入 JSON、绑定新源码版本/dirty hashes、验证输出范围并跑短 pilot。没有创建空 runner 冒充完成。

建议先固定环境与 GC、顺序种子 20260921，5 warmups + 20 measured calls/算法/case。输入副本在调用前准备，输入值不变，每调用各自重新初始化状态；paper 的前三点初始化、全部 Step、output recovery 都计时。外部 oracle、expected 比较、结构分类、完整 audit 不计时。Python sorted 同样计算并返回完整输出。Reference 如加入，仅作为单独说明范围的辅助 pipeline，不作为主加速结论。pilot 检查时钟分辨率与整体资源；若需批处理，先修订协议，再冻结正式配置。

统计以唯一 case 为单位，报告每 case 时间中位数和波动、每规模/结构格的 case 分布及缺额；反射按 base 配对报告。重复调用不是独立输入。后端完成后，普通列表与新后端在同一批输入、环境、诊断策略、调用范围重测，不把旧普通列表归档拼成匹配对照。

后端开发的具体接口、ownership 与 S_i 成本、原文依赖和验收顺序见 [后端规格](heterogeneous_finger_backend_spec.md)。这是已设计未实现的工作。

## 待后续同步的材料

本轮不改 thesis 或 PPT。后续需核对 thesis/chapters/algorithm.tex 的 transaction 描述、implementation.tex 的 rollback 测试说明、methodology.tex 的计时工作范围、introduction.tex 与 conclusion.tex 的 transactional 表述。历史实验的实现版本描述仍应保留历史语境，不能全部替换成新行为。

## 已验证结果与可复现入口

最终预检目录为 `results/preflight_runs/ordinary_no_rollback_20260921_002/`。88 候选，85 个本批唯一 rank 输入 PASS，3 DUPLICATE；认证/输出/状态失败 0、TIMEOUT 0、NOT_RUN 0。基础 64、派生 21；coverage-guided 67、seeded incremental（含其反射）18。这里的唯一性是本批去重，并未宣称 85 个全部不同于历史归档。

实测结构：strict_flat 14、low 27、medium 20、heavy 24；最大通过 n=513。29 个预定义 trace 分支均有见证，包括跳过 split、单/双侧非空、0/1/多 child、increasing/decreasing、两类 z1 修正；最大观察到的 live sibling list 长度 256，最终 profile 最大深度 31。有限覆盖不能推出全部路径覆盖或数学正确性。

整批资源墙钟 105.42 秒，包含生成、认证、完整审计和进程开销，不是 core timing。每个唯一输入 checked/minimal 各一次独立新状态；checked 内部原有逐前缀 replay 保持，不把它称作第二个独立算法。001 是相同候选表的首次预检，只有共用模板中一个旧 rollback limitation 标签未适配；002 修正新报告说明后复验。两次都保留，**不能相加成 170 个唯一输入**。

基线 168/168 回归通过；最终 172/172 通过。原有 bounded exhaustive 在修改前后均检出 n=0..8 共 2,074 个有效排列，全部通过；另以 minimal 新副本独立执行相同 2,074 个有效排列，逐例与外部 sorted 比较通过。没有新增有效输入排序错误。没有运行无关全仓库测试或历史 timing replay。

实际命令（仓库根目录，使用 bundled Python 3）：

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:experiments:tests python3 -m unittest test_paper_jordan test_paper_jordan_sort test_paper_execution_policy test_sibling_list_backend test_partial_sorted_list test_certified_paper_jordan test_validate_paper_algorithm test_validate_ordinary_list_extended test_preflight_next_stage -v
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:experiments:tests python3 experiments/validate_paper_algorithm.py --max-n 8 --skip-generated
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:experiments:tests python3 experiments/preflight_next_stage.py --output results/preflight_runs/ordinary_no_rollback_20260921_002
```

第三条是已执行命令；再次执行必须换一个不存在的输出目录，旧目录会被拒绝。minimal 穷举的实际独立脚本与 JSON、完整测试日志保存在 `results/development_checks/ordinary_no_rollback_20260921_002/`。基线与最终源码身份、工作区差异见预检 `provenance.json`、`worktree.patch`；实际测试的是 dirty 源码，不是只凭 HEAD 标注该提交。

历史归档和原有 PPT 共 301 个保护文件，开始/结束文件集合和 SHA-256 完全一致。预检 manifest 的 93 个文件哈希验证通过，测试期间源码哈希未改变。现有 results ignore 规则未更改；新增本地结果目录当前被 Git 忽略，未来归档需显式审阅选取，本轮没有暂存或提交。

`git diff --check` 通过；执行了 `git diff --stat` 和 `git status --short`。本轮修改 3 个 core 文件、3 个既有测试文件，新增 preflight runner、其 4 项测试和本开发说明/后端规格。工作区显示的英文 PPT 修改是原先已有内容，字节未改变。

未执行：正式扩展 timing、完整后端实现/线性界证明、512/513 heavy 及 1024/1025 的新资源资格验证。下一轮先完成候选池扩展和资格审计、冻结配置、实现新 timing runner 与 pilot；后端按规格从真实 rib/red-black 操作与 owner 访问验证开始。没有 commit，没有 push。

## 后续授权归档

用户在上述开发与验证完成后另行授权 commit/push。本次提交归档最终 002 预检与检查目录；001 首次运行仅留本地，不合并计数。此前关于未提交、结果被忽略的描述记录的是开发阶段结束时的状态；最终 002 证据已显式纳入版本控制。原先已有的英文 PPT 修改不属于本次提交。
