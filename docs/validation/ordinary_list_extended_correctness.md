# Ordinary-list 非计时正确性与覆盖补充

这项验证与 Week 12 的正式性能实验独立。原性能实验仍只有 60 个输入、3,600 条测量记录；本任务不运行 timing runner，不产生性能排名、速度比或复杂度结论。

## 入口与固定计划

入口：`experiments/validate_ordinary_list_extended.py`。它复用当前 `generate_sequence`、`oracle`、`structure_profile`、公开 checked diagnostics 和 minimal valid-input 排序 API。测试文件：`tests/test_validate_ordinary_list_extended.py`。

默认计划在执行前写入新目录的 `config.json`：

- 32、33、64、65、128、129、256、257：各 20 个 incremental 基础输入。
- 512、513：各 5 个 incremental 基础输入。
- 1024、1025：各 1 个；只有较小输入无错误或超时、整批预算仍有余量时执行。
- 32、33、128、129、512、513：各 1 个 flat、1 个 nested 构造。
- 8 个小规模／固定边界输入，源于现有 endpoint、z₁、split 回归用例和小规模 API 边界。
- 每个长度的首个 incremental、每个确定性构造、4 个非平凡固定输入增加反射，共 28 个派生输入。

总计 220 个候选，其中 192 个基础候选、28 个派生候选。Incremental 的种子为 `20260916 + n*1000 + index`；生成器仍使用原有每步 20 次随机尝试及原有 fallback。反射使用 `min(sequence)+max(sequence)-x`，对 rank-coded 输入等于 `n+1-x`。每个派生输入保留基础身份和哈希，并再次认证。它们不是独立随机样本。按长度及 case_id 顺序执行；重复按与历史一致的 JSON 紧凑编码 SHA-256 判定，记录 `duplicate_of`，不重复执行或另换种子补足数量。

## 执行与资源边界

```sh
PYTHONDONTWRITEBYTECODE=1 python3 experiments/validate_ordinary_list_extended.py \
  --output results/validation_runs/ordinary_list_extended_correctness_v1__run001 \
  --batch-seconds 1800 --case-seconds 120
```

输出目录必须不存在。默认整批 30 分钟，单例生成、认证、checked/minimal、覆盖与可选 prefix 检查合计 120 秒；限制可在启动前通过命令行配置。每例在受父进程监管的子进程执行并逐阶段落盘，超时终止子进程。记录的整体验证耗时仅用于资源管理。退出码 0 表示计划无失败／超时／未执行（允许明确记录的重复）；1 表示验证错误；2 表示资源限制或未完成。

状态包括 PASS、GENERATION_ERROR、CERTIFICATION_ERROR、OUTPUT_MISMATCH、STATE_INVARIANT_ERROR、EXECUTION_ERROR、TIMEOUT、NOT_RUN_BUDGET。额外显式状态为 DUPLICATE、RESOURCE_ERROR、NOT_RUN_DEPENDENCY、NOT_RUN_STOPPED。发生已认证输入的输出、状态或执行错误后停止扩展，保留已生成输入、执行阶段、错误及可取得的 trace 尾部；不修改 core、不替换失败输入。内存不足与算法错误分开统计。

## 判据和观测定义

Oracle 先认证 distinct 与 valid；外部 `sorted(original_sequence)` 独立提供排序结果判据。两个公开 API 分别接收全新的原始列表，不接收 expected、oracle sorted output、rank map 或另一个模式的状态。检查与 expected 一致、长度、元素保留、严格递增、模式输出一致、checked processed_count 和 invariants。

Checked/minimal 是同一个核心的执行策略。Checked 内部还会执行确定性 replay；这些不是另一套独立 Jordan Sorting 实现。执行次数报告公开 API 调用，内部 replay 不伪装成独立用例。

每个分支标签在 `coverage.json` 中包含真实字段条件、事件次数、不同用例数及一个 witness（case_id、输入哈希、迭代、模式、实际事件）。尤其：

- 3(a) 使用 `insertion_mode`，并与 orientation 交叉统计。
- 3(b) 使用 `performed` 和实际 `left_size/right_size`；根据 `acquired_side` 确定转移数量。新 pair 在 3(b) 前无 children，因此获得 child 数量等于 acquired side 大小。
- 几何端点不一致：3(c) 有 child 且 `base_anchor_point_id != child_pair_id`。代码中 pair ID 是结束下标，第二个 curve-order point ID 就是该下标；同时保存原始两个端点值和几何 anchor 值。
- z₁ boundary adjustment 使用 Step 1/2 的 `adjusted_for_z1`，与 3(c) 的 output adjustment 分开统计。
- Live sibling-list 最大长度由初始化、3(a) 的插入、3(b) 的 retirement 和两侧长度重建，并保存触发最大值的事件。它不同于 split input length。
- `structure_profile` 的 depth 以有限根为 0；nesting_count 是有限非根节点数，containment_pair_count 包含所有严格包含关系；parented_interval_ratio 的分母为全部有限 intervals。结构 profile 只描述完整输入，不声称观测到了所有中间树深度。

预选 8 个代表性基础用例额外从头运行一次，在现有 callback 中检查 `k in {3,4,n//2,n}` 的维护输出与原始前缀排序一致。仅保存这些 prefix snapshots，不对所有大用例逐前缀重复运行。

Rollback 的故障分支独立由现有 fault-injection regression tests 检查，不计入 valid-input cases。Minimal 分支细节因禁用 trace/counters 标为 NOT MEASURABLE WITH CURRENT OBSERVABILITY；其输出恢复仍实际执行。

## 版本、冻结边界和产物

历史记录以 manifest 的 source_commit 为准。当前运行单独保存 HEAD、origin/main、源码 SHA-256、与历史版本的文件差异、工作区状态。未提交的新工具与测试有独立内容哈希，不能说已包含在 HEAD 中。历史 60 个用例的分析只读取归档字段和 manifest 验证的文件，不重跑历史 diagnostics；不足以判断的分支标为 INSUFFICIENT_ARCHIVED_FIELDS。

每个新目录含 config、逐例 cases、historical_coverage、coverage、summary、manifest，以及两处冻结目录的前后文件集合和哈希。已有目录拒绝覆盖。完整成功 trace 不归档，只保留指标、首个分支 witness、prefix snapshots 和失败证据。`manifest.files` 为除 manifest 自身外的完整文件哈希集合。

仓库现有 `.gitignore` 忽略新的 results 子目录。初次执行按要求仅保存在本机；用户后续授权发布后，仅显式加入本次归档目录，忽略规则保持不变。产物可按 manifest 核查。

## 本次实际结果

本次计划 220，尝试 216，完成 215（含 6 个重复认证），新增唯一输入开始执行 210，完全通过 209（183 基础、26 派生）。失败 0、内存错误 0、超时 1、未执行 4。最大实际通过长度 **513**，不是计划中的 1025。

`incremental_valid_n513_005` 已通过 oracle 认证，但在 checked 阶段达到单例 120 秒限制，未取得 checked 输出，minimal 未开始；输入及阶段已归档。这不是已确认的算法错误，也不能视为通过。按预定资格规则，1024/1025 的基础及反射共 4 例标为 NOT_RUN_BUDGET（smaller-case timeout 导致 large-tier eligibility failed），不是声称实际用光剩余整批时间。整批约 1782 秒，仅作资源管理记录。

Checked 开始 210 次、完成并通过 209 次；minimal 开始／完成／通过 209 次；prefix 额外从头执行 8 次，27 个 snapshot 通过。两种公开模式共开始 419 次，完成 418 次；另计 prefix 8 次。209 个成功输入均与外部排序一致。checked/minimal 及内部 replay 仍是同一核心，不是独立算法实现。

| n | PASS | 重复 | TIMEOUT | 未执行 |
|---|---:|---:|---:|---:|
| 0 | 1 | 0 | 0 | 0 |
| 1 | 1 | 0 | 0 | 0 |
| 2 | 2 | 0 | 0 | 0 |
| 4 | 2 | 0 | 0 | 0 |
| 7 | 4 | 0 | 0 | 0 |
| 8 | 2 | 0 | 0 | 0 |
| 32 | 23 | 2 | 0 | 0 |
| 33 | 25 | 0 | 0 | 0 |
| 64 | 21 | 0 | 0 | 0 |
| 65 | 21 | 0 | 0 | 0 |
| 128 | 23 | 2 | 0 | 0 |
| 129 | 25 | 0 | 0 | 0 |
| 256 | 21 | 0 | 0 | 0 |
| 257 | 21 | 0 | 0 | 0 |
| 512 | 8 | 2 | 0 | 0 |
| 513 | 9 | 0 | 1 | 0 |
| 1024 | 0 | 0 | 0 | 2 |
| 1025 | 0 | 0 | 0 | 2 |

本次 29 个预先定义的可观测分支标签均有实际 witness；不等于穷尽所有分支组合。代表性记录：双侧非空拆分 `fixed_n8_007/i=8`；多个 children `fixed_n7_006/i=7`；两种方向的端点不一致 `fixed_n4_005` 及其反射 `/i=4`；两种 boundary adjustment 为 `incremental_valid_n32_001` 及其反射 `/i=7`；两种 output-anchor correction 为 `fixed_n7_006` 及其反射 `/i=7`。完整输入哈希和事件见 coverage.json。

通过输入分类：strict-flat 13、low-nesting 6、medium-nesting 2、nested-heavy 188。完整输入最大深度 255，没有超过历史最大深度；嵌套节点数最大 510，最大 live sibling-list 长度 256。新增明确覆盖包括奇数输入长度、低／中嵌套类别及上述带 witness 的细分事件。历史细分事件无法判定，不能写成首次触发。

Minimal 逐分支、所有中间状态的树深度及正常成功运行中的 rollback 失败路径为 NOT MEASURABLE WITH CURRENT OBSERVABILITY。未来最小观测需求分别为 minimal 事件钩子、每轮状态 callback、单独故障注入；本任务不修改核心添加这些接口。Rollback 另由现有回归测试检查，不计入新增输入。超时用例的完整正确性及 n=1024/1025 均为 NOT INDEPENDENTLY VERIFIED。

新增工具测试与相关回归 103 项、Step 回归 49 项，共 152 项通过（14 新增、138 现有）。实际命令如下，Python 使用 bundled runtime 的绝对路径，前置 PYTHONDONTWRITEBYTECODE=1：

```sh
PYTHONPATH=src:experiments:tests python3 -m unittest test_validate_ordinary_list_extended test_paper_jordan_sort test_paper_execution_policy test_sibling_list_backend test_validate_paper_algorithm -v
# exit 0, 103 tests
PYTHONPATH=src:experiments:tests python3 -m unittest test_paper_jordan -v
# exit 0, 49 tests
python3 -u experiments/validate_ordinary_list_extended.py --output results/validation_runs/ordinary_list_extended_correctness_v1__run001 --batch-seconds 1800 --case-seconds 120
# exit 2, explicitly partial because 1 timeout and 4 not run
```

独立归档核对退出 0：220 条计划与逐例记录、209 条通过的外部排序摘要、27 个 prefix、覆盖聚合及 witness 成员关系、源码和产物 manifest 全部一致。两处冻结目录共 16 个文件，文件集合及 SHA-256 不变；本次任务开始时的 289 个 tracked 原文件全部保持原字节。核对发生在后续第 14 页编辑任务之前。

初次执行只新增验证入口、其测试、本文档及独立 results 目录，没有修改原有 tracked 文件，当时没有 commit/push。这些是新增非计时正确性与覆盖证据，不改变 60 输入／3,600 measured rows 的性能证据范围，也不证明线性复杂度或普遍正确性。


### 历史证据核查

本地 `main`、fetch 后的 `origin/main` 与真实远程 main 均为 `331262d7573c1e12aeb3e55fa5002da50b3c498e`。正式实验 manifest 绑定 `98868b1b705f6d5f22404ee8ad7b88ad7a834f52`。对两个提交的 `src`、生成器审计、paper validator、formal-output validator 和 formal execution support 比较无差异。因此被测核心及这些依赖的文件内容相同；本次运行仍按当前 HEAD 和未提交验证工具的独立哈希记录，不冒充历史执行。

原 60 例在 n=32、64、128、256、512 各有 10 个 incremental、1 个 flat、1 个 nested。归档的 60 个输入哈希互异；本任务没有重新生成历史输入字节。结构分类为 55 个 nested-heavy、5 个 strict-flat，最大树深范围 0–255，嵌套节点数范围 0–509，upper/lower roots 范围分别为 1–256、1–255。不存在奇数长度用例。

归档计数可确认：55 例发生过 singleton-list creation，55 例发生过 sibling-list insertion；50 例发生过 split，50 例发生过 ownership transfer；27 例发生过 z₁ boundary adjustment，13 例发生过 z₁ output-anchor adjustment。不能由这些正计数推断单侧／双侧拆分、children 数量、具体几何端点选择或修正方向均已覆盖。这些细分问题标为 `INSUFFICIENT_ARCHIVED_FIELDS`，没有为了补表重跑历史诊断。

开始时只有两份 OnlyOffice 锁文件未跟踪，没有 tracked 修改或核心代码的本地差异。锁文件保留。历史冻结目录、全部原有 tracked 文件均在本次开始前逐文件记录 SHA-256，结束后按文件集合及内容再核对。


### 后续授权发布

用户随后明确要求提交并推送本地扩展验证材料。发布前重新核对全部 234 个 manifest 所列产物哈希、19 个源码／工具哈希、220 条计划记录、覆盖聚合和通过用例的外部排序摘要，均一致；两处冻结 evidence 的文件集合及哈希仍未变化。

归档保留原始运行基线 `331262d7573c1e12aeb3e55fa5002da50b3c498e` 和当时未提交工具的内容哈希，不将发布提交伪称为计时或验证运行时的 HEAD。本次发布没有重跑用例、timing 或 profiling。结果仍是 209 PASS、6 DUPLICATE、1 TIMEOUT、4 NOT_RUN_BUDGET，最大实际通过 n=513；原正式性能证据仍为 60 cases、3,600 measured rows。
