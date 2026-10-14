# `844ea6d` 审核问题修复

父基线为 `844ea6d71b108d79103b259856284c4dce28fe87`。本轮只修复证据生成、
验收程序和证明记号，生产 `src/`、论文、输入数据及历史性能结果均未改。
仍为合成 tick 夹具；没有 pilot/正式墙钟测量，也不宣布高效后端最低交付完成。

## 修复前的实际复现

[复现记录](before_fix_reproduction.log)来自修改前的完整 checkout：正常资格
阶段使用真实实现，只在指定故障处替换返回值。实际重现了以下问题：

- `[NaN]` 与 `[object()]` 输出使 runner 在序列化时退出，仅有三行 PASS，
  没有 ERROR、summary、manifest。
- 删除五项环境字段并重封 manifest 后，validator 仍返回完整成功。
- diagnostics 返回错误 `processed_count=0`，runner 自己仍返回成功。
- 普通模式下空 source 映射被拒绝，`-O` 下旧 `sources()` 静默接受。

这些是证据层故障注入，不算真实后端的正确性测试。修复前实际源码身份与
本轮身份分别记录于 [verification.json](verification.json)。

## 三项修复

**失败记录。** 正常或错误的纯整数列表保留原值；其他返回值保存为
`output=null` 加 `output_diagnostic`，最多八项、每项至多 160 字符，包含类型
和适用的长度。不递归展开对象，不调用任意对象的 `repr`，自引用列表也能
记录。NaN/Infinity 只出现在诊断字符串中，不产生非标准 JSON 数值。
JSON 编码在写入前完成；若该步骤本身失败，则生成 `SerializationError`
终止行，再完成失败汇总与 manifest。异常消息也限制长度。

磁盘写入/flush 等 I/O 故障仍向外报告；CLI 返回失败并明确归档可能不完整，
不承诺在存储不可写时仍能保存完整证据。测试分别覆盖程序级序列化失败和
外部 I/O 失败，没有混称为同一保证。

**字段与目录验收。** schema 升为 `matched_backend_fixture_v2`。environment
要求完整字段：源码 SHA-256、40/64 位 Git hash、布尔 dirty、非空 Python/
platform、有效且带 UTC 时区的 ISO 时间、合成计量类型、整数优化级别 0。
开发工作树允许 dirty 为真。runner 与 validator 都要求 `processed_count`
是严格整数且等于输入长度，浮点和布尔不能借 Python 数值相等通过。

按 kind/status 核对 row 的确切字段，包括成功资格、输出、错误和有界诊断。
配置、输入条目也检查字段集合。每个 fixture 子目录只允许 config、environment、
raw、summary 和 manifest 这五个普通文件，**不允许额外文件或目录**；说明和
验证报告放在外层归档。重新计算哈希不会绕过内容检查。环境字段校验是格式
和完整性约束，不是对运行机器信息的密码学证明。

**优化模式保护。** runner、validator、成本探测、中等切分主入口及直接 worker、
归档复核脚本均在模块加载时显式拒绝 `sys.flags.optimize != 0`。保护发生在
解析参数、创建输出或调用关键检查之前，也覆盖模块导入后直接调用的用法。
保留原有 assert，但不允许它们在证据流程中被静默关闭。新 plan、成本记录、
fixture environment 和复核结果都记录实际 `python_optimize=0`。

`-O`、`-OO`、`PYTHONOPTIMIZE=1/2` 在六条入口路径上共 24 次子进程调用均
明确失败，未生成输出；其中一条是 `--worker` 直接调用。普通模式五个入口的
帮助命令可用，空映射、缺文件和错误哈希仍会被实际检查并拒绝。

## 本轮验证结果

| 检查 | 结果与范围 |
| --- | --- |
| [定向测试](targeted_tests.log) | **27 个方法通过，0 跳过**：12 个新增审核回归 + 原 15 个成本/夹具/中等切分测试 |
| [真实成本探测](cost_probe/records.json.gz) | 普通解释器下复跑 2,634 次小树分裂、12 条混合历史；规模与上一轮相同，不算新增结构覆盖 |
| [中等切分](middle_splits/summary.json) | 复跑原 12 输入、72 次执行；每 checked 配置 1,518 个完成前缀、24 次 split，其中 12 次双侧非空 |
| [成功夹具](matched_fixture_check.json) | v2 schema，27 行，完整成功；全部为 synthetic ticks |
| [非法输入夹具](failed_fixture_check.json) | runner 退出码 2；完整失败归档可验收，`completed_successfully=false` |
| [五项故障注入](fault_injections/report.json) | NaN、普通对象、自引用列表、直接行序列化故障、错误资格数量；均保留 ERROR、summary 和 manifest，并停止调度 |
| [压缩原始记录复核](archive_check.json) | 源码、输入哈希、成本不等式、操作求和、完整 trace 的 split 大小及夹具汇总一致；记录优化级别 0 |

五项故障注入使用保留的 [exercise_failures.py](exercise_failures.py)，原始
fixture 在 `fault_injections/` 各子目录中。它们使用真实 checkout 的正常
依赖，只替换明确标记的故障调用，不是额外真实树验证。

27 是方法数，24 次优化模式调用等是其中子案例，不重复累计。没有复跑旧
80 项树回归、173 项普通核心回归、125 项旧实验工具回归，也没有论文编译。
修改只涉及证据流程；真实操作与完整排序复跑用于确认正常解释器路径仍有效。

## 版本与证明边界

旧 `finger_cost_and_fixture_20261014` 的原始 JSON/gzip/log、manifest 和
verification 保持原样。位于该目录的可执行 `recheck_evidence.py` 是本轮
明确维护的例外：添加优化保护、优化级别检查和 `--directory`，便于复核本轮
同构数据。旧 verification 中的脚本哈希对应 `844ea6d` 的原文件，不代表
维护后的脚本；本轮新哈希见本目录 verification。**没有重新封存旧记录使它们
冒充 v2。** 复现旧版本应检出 `844ea6d` 并使用优化级别 0；当前 v2 验证器
会拒绝旧 schema 或不匹配的源码身份。

[成本证明](../../development/heterogeneous_cost_lemmas_20261014.md)只精确化
`I`：它是 `recolor_cascades` 的传播轮数，不是逐节点 `recolorings`。
物理 ROOT/LEFT/RIGHT/INTERIOR 表示如何保持叶集合、separator、rank、span、
端点和 header，以及所有合法输入的最近邻、`z1`、ownership/分组归纳，仍是
两类需要继续完成的论证。抛错检查不能替代“合法输入必满足前提”的证明。

## 复现入口

从仓库根目录、优化级别 0 的 Python 3 执行；新输出目录必须不存在：

```sh
PYTHONPATH=src:experiments:tests python3 -m unittest \
  test_fixture_review_regressions test_matched_backend_fixture \
  test_finger_cost_lemmas test_finger_middle_splits -v
python3 experiments/probe_finger_cost_lemmas.py --output /tmp/jordan-cost-review
python3 experiments/validate_finger_middle_splits.py --output /tmp/jordan-middle-review
python3 docs/validation/fixture_review_hardening_20261014/exercise_failures.py \
  --output /tmp/jordan-fault-review
python3 docs/validation/finger_cost_and_fixture_20261014/recheck_evidence.py \
  --directory docs/validation/fixture_review_hardening_20261014
```

本机测试命令见 [suite_commands.json](suite_commands.json)。普通模式的成功
复跑与优化模式的明确拒绝是两类证据；均不授权把 synthetic ticks 直接替换
为时钟后就进入正式实验。
