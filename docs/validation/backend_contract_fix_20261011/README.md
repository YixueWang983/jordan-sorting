# 操作契约验收入口与交错更新修订（2026-10-11）

基线：`afb97023ddb843bc31fb37b7edb3bf6fca96005d`。用户反馈的两个测试缺口均已本机复现。本次只加强测试与说明，主计划的范围和排程不变。本审计及 JSON 的 Git 状态记录截止于本地验证完成时，不代表后续提交或推送状态。

## 复现与修复

| 反例 | 修复前 | 修复后严格入口 |
| --- | --- | --- |
| 假适配器在构造时抛 `SkipTest` | 16 项契约跳过、4 项模型自检通过，exit 0 | 当前 18 项契约跳过、4 项模型自检通过，exit 1、REJECTED |
| 指定假适配器但只选 `ModelAuditSelfTests` | 只执行 4 项模型自检，exit 0 | 操作契约开始数为 0，exit 1、REJECTED |
| 假适配器第一次 split 后禁止端插 | 原 16 项操作契约通过，exit 0 | 新增两项交错测试暴露错误，exit 1、REJECTED |

修复前日志为 `*_before.log`，修复后日志为 `*_after.log`。反例适配器是 [review_adapters.py](review_adapters.py)，明确继承参考模型用于故障注入，不是生产后端。修复前脚本与上述提交的测试文件逐字一致，其 SHA-256 见 [verification.json](verification.json)；可从该 Git 提交恢复。

严格模式通过 `ContractTestResult` 记录实际开始和成功的方法身份，要求完整的 18 项操作契约各成功一次；跳过、缺项、重复、失败、错误、expected failure 均无法通过。子测试的 skip/failure 归入所属契约；整体运行的其他错误或跳过也阻止验收。

开发模式仍允许筛选且保留 unittest 退出码语义，但始终输出 `contract_acceptance_passed=false`。所以开发 exit 0、只跑模型自检或普通 discovery 不属于完整契约验收。严格模式成功为 exit 0、`status=ACCEPTED`；未通过为 exit 1；找不到适配器为 exit 2、`UNAVAILABLE`。

`operation_contracts` 和 `reference_model_self_tests` 分开报告计数，前者的 subject 区分 reference_model/external_adapter。严格验收必需完整操作契约；模型审计自检可单独运行，也可选择只执行完整 `OperationContractTests`，不将未运行自检计为通过。所有模式仍报告 Jordan 接入、效率证明和计时就绪为 false。

两项新操作契约含 12 个场景：对两个非空输出，以及空侧 split 的非空输出，执行两轮 `split/adopt → 两端插入`。涵盖左右镜像、retained/acquired 两侧、singleton 输出、再次分裂、原列表 handle 退役、旧边界引用失效。每步与显式 item/owner 列表对照，检查顺序、稳定对象、owner、极端子项和逻辑审计。它们仍是抽象语义测试，不覆盖 Jordan 几何或真实树的红黑/rib 不变量。

## 验证与复现

- 18 项操作契约 + 4 项模型自检：严格运行通过、0 skip，见 `strict_reference_model.log`。
- 15 项 CLI 回归：包含全跳过、子测试跳过、只跑模型、零项、部分/重复选择、expected failure、构造错误、缺失适配器及上述交错反例。与模型合并 discovery 共 **37 PASS、0 skip**，见 `model_and_runner_regressions.log`。CLI 中通过的外部对象也是显式假适配器，不是新后端。
- `src/`、`experiments/`、`data/`、`results/`、`thesis/`、原合并审计和 16 例探测归档均与基线一致。
- 本次未复跑原有 155 项生产回归、全仓库回归或大规模 checked/replay；未执行正式计时、未编译论文。

从仓库根目录：

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_finger_backend_contract*.py' -v
PYTHONDONTWRITEBYTECODE=1 python3 tests/test_finger_backend_contract_model.py --strict -v
# 将来真实适配器实现后的严格语义验收：
PYTHONPATH=src:tests python3 tests/test_finger_backend_contract_model.py --strict --factory MODULE:FACTORY -v
# 以下两条应退出 1（故障注入）：
PYTHONPATH=docs/validation/backend_contract_fix_20261011 python3 tests/test_finger_backend_contract_model.py --strict --factory review_adapters:skip -v
PYTHONPATH=docs/validation/backend_contract_fix_20261011 python3 tests/test_finger_backend_contract_model.py --strict --factory review_adapters:BrokenAfterSplit -v
```

`MODULE:FACTORY` 尚不存在。验收只确认实际测试到的语义，不证明无缺陷，也不代替真实后端集成、效率审查和双方最终资格。后续仍按既定主线推进 ownership/locality、执行阶段状态、逻辑审计与 replay 契约。
