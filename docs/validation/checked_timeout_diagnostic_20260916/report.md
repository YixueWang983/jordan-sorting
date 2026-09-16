# Checked 超时输入的独立诊断

输入：incremental_valid_n513_005，原始已归档序列，n=513。基于 HEAD 071973c639a26eb6f08ee5d9f7025e5de97b2a34。没有生成新验证用例、修改核心或重跑正式 timing。

本次设置独立 180 秒诊断上限。完整 checked diagnostics 在 97.365 秒返回，全部 511 次前缀状态校验完成，输出与 oracle expected 一致；随后在独立全新输入列表上调用 minimal，输出也一致。该次运行没有复现历史的 120 秒超时，不能据此解释历史环境为何更慢，也不回写历史 TIMEOUT 或把归档的 209 改成 210。

## 耗时位置

用外部 Python 包装器为函数累计 inclusive/exclusive wall time，保留原调用与校验语义。计数和秒数均包含诊断及包装器开销，仅供资源定位。

| 诊断环节 | 调用次数 | inclusive 秒 | exclusive 秒 |
|---|---:|---:|---:|
| backend_invariants | 54825 | 85.861 | 85.861 |
| full_state_validation | 511 | 96.693 | 3.410 |
| deterministic_replay | 511 | 91.760 | 8.041 |

这些 inclusive 时间有包含关系，不能相加。完整状态校验包含 replay；replay 又包含大量 backend invariants。约 94.2% 的总诊断时间位于 replay 内，约 88.2% 位于 backend invariants 内（后者包含 replay 内外的调用）。这说明本次运行的主要开销是逐前缀 replay 及其重复结构审计，不是卡在 oracle，也没有观察到某一轮无限循环。

静态代码进一步显示 backend invariant audit 遍历 live lists 与 pairs，并针对每个有 parent 的 pair 检查 parent chain。该结构解释了深嵌套输入为何可能使审计昂贵；本轮没有单独计量 parent-chain 子函数，因此不能给它分配精确耗时比例，也不能从一次诊断推出渐近复杂度。

调用链：paper_jordan_sort.py:paper_jordan_diagnostics_valid → 每轮 validate_paper_jordan_state → _validate_state_against_deterministic_replay → 同一核心的 checked 前缀运行 → OrdinarySiblingListBackend.validate_invariants。Replay 本身不再递归触发完整状态 callback。它仍是 same-core replay，不是独立实现。

## 验证与边界

完整 checked 输出和 minimal 输出均与 expected 一致；原 source 文件哈希未变化，扩展归档 manifest 的所有文件哈希通过，tracked diff 为空。工作区仍只有原有两个 ONLYOFFICE lock 文件。诊断脚本、JSON 和草案均在仓库外；没有 commit、push、修改 PPT 或正式稿，也没有运行算法回归测试。

未独立验证：历史超时当时的 CPU/系统负载、历史每个函数的耗时、1024/1025、所有输入结构在 180 秒内的可执行性。一次成功诊断不保证未来运行不会超时，不是数学证明，也不是正式排序性能数据。

扩展方案见同目录 expanded-timing-proposal.md。建议先做有结构配额的资源预检，再冻结新的正式计时计划；不直接把验证 wall time 或本表作为性能结果。
