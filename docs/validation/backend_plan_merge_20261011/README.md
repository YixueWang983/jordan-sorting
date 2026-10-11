# 后端计划与参考模型合并核对（2026-10-11）

用户上传 `jordan_backend_plan_bundle_reupload.zip` 后，本地审阅并合并到 `fa67fc664d7515b2504d355e35fadcfd23f16534`。本次范围是计划、接入/成本清单和测试底座；没有生产后端或共享核心改造。

## 来源与合并方式

- ZIP SHA-256：`0fb5f69003e905deb572b7010d9f0abebdd4d9a3b683cb5179247f7553df306e`。CRC 和 manifest 所列 10 个文件的 SHA-256 均通过；解压前检查了路径及符号链接。
- 原包审阅基线为 `b6a4074`。四个核心源码文件及后端规格与 `fa67fc6` 的 Git blob 一致；README 与活动计划已变化，见 [基线比较](bundle_baseline_comparison.json)。
- 阅读应用脚本后，仅对真实仓库执行 dry-run；它按预期以 exit 2 拒绝 README 身份不匹配。没有执行 `--apply`，没有绕过身份保护，采用人工合并。
- `fa67fc6` 的旧计划逐字保存至 [历史计划](../../plan/archive/remaining_work_20261011_before_backend_required.md)。新模型测试与导入文件逐字一致。
- 原包的 manifest 原样保存为 [imported_bundle_manifest.json](imported_bundle_manifest.json)。其中 403、未核验 16 例等字段只描述原作者那次执行，不是当前仓库状态。本审计及 JSON 中的 Git 状态记录截止于本地合并验证完成时；后续提交或推送不改变这次验证的历史身份。

## 内容修正

1. 活动范围改为高效 heterogeneous finger-search 后端最低交付；保留 10-15 完整排序中真实 split、10-18 最终资格、10-22 整稿及 23—24 日检查。约 140/380 是分层覆盖目标。
2. “导师明确要求”改为用户本轮确定的范围，不推断导师已批准新版排程。明确只参考文献，不复制或移植第三方后端源码。
3. 保留首次修订的 133 项/74 页历史记录，同时保留后续成本修订的 155 项/76 页及已有 16 例探测归档。本次没有重跑 16 例的大规模 checked/replay。
4. 接入表包含正常排序、阶段结果、trace、metrics、完整审计、same-core replay 与实验消费方；未完成的 locality 和消费方核对仍列为缺口。
5. 核实 `paper_jordan.py` 的 `_require_*_stage`（1737—1769）读取阶段结果，`_record_stage_result`（1804—1808）无 trace 开关。因此不能整体移除 `stage_results`；具体执行状态/诊断拆分尚未实现。
6. 明确测试的 20 项包含 16 项可复用操作契约和 4 项参考模型审计自检。将来外部适配器运行中的后 4 项依然属于模型，不能冒称真实后端验证。

## 本机验证

| 检查 | 结果 | 范围 |
| --- | --- | --- |
| 导入模型直接运行、合并后仓库 discovery | 各 20 PASS、0 skip | 同一套测试的两次运行，不能相加为 40 项；默认对象全是参考模型 |
| 现有定向回归 | 155 PASS、0 skip | 与成本修订相同的七个模块；不是全仓库回归 |
| 原包应用脚本测试 | 7 PASS | 合成临时目录；不表示旧基线脚本能够直接应用当前仓库 |
| 指定不存在的适配器 | exit 2 | 包内与仓库版本均拒绝，未以 skip 冒充通过 |
| 真实仓库应用 dry-run | exit 2 | 基线不一致时拒绝写入 |
| 已有 16 例探测归档 | 核对通过 | 文件/源码哈希、配置、输入输出身份及记录状态；没有重新执行 checked/replay |
| 原有文件保全 | 714 个已跟踪文件中 710 个逐字不变 | 只更新 README、计划索引、活动计划和 thesis README；其余原有文件包括源码、实验、旧测试、LaTeX 和历史数据均保留 |

命令、环境和日志见 [repo_runs.json](repo_runs.json)、[runs.json](runs.json)，源码身份和保全结果见 [merge_verification.json](merge_verification.json)。测试日志为 `repo_model_discovery.log`、`repo_targeted_regressions.log`、`bundle_installer.log`；失败条件日志为 `repo_missing_factory.log` 与 `actual_repo_dry_run.log`。`probe_archive.log` 为已有探测归档的只读核对输出。

从仓库根目录复跑相关检查：

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_finger_backend_contract_model.py' -v
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:experiments:tests python3 -m unittest test_paper_jordan test_paper_jordan_sort test_sibling_list_backend test_paper_execution_policy test_validate_ordinary_list_extended test_preflight_next_stage test_probe_large_qualification -v
PYTHONDONTWRITEBYTECODE=1 python3 tests/test_finger_backend_contract_model.py --factory missing_jordan_backend_adapter:build -v
python3 docs/validation/cost_and_qualification_20261011/verify_probe_archive.py --repo . --archive docs/validation/cost_and_qualification_20261011/qualification
```

第三条是预期 exit 2 的负向检查。应用脚本及其七项测试保留在原 ZIP，需解压该身份的原包后运行 `python3 -m unittest test_apply_changes -v`，不作为生产后端代码安装。

真实树、普通后端对新模型的适配、Jordan 端到端接入、红黑/rib 不变量、操作界与总复杂度均未由本次模型自检证成。本次没有启动正式计时，没有修改或构建论文 PDF。下一步仍是关闭实际访问的 locality、阶段状态、逻辑快照与 replay 契约缺口，再实现真实操作。
