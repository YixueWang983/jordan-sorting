# 资格验证重构的有界证据（2026-10-15）

本目录先提交源码、[v2检查安排](../../development/qualification_validation_v2_20261015.md)、
`preselected_plan.json`及针对性测试，再执行固定开发复核并归档结果。
未改140输入或其v1超时记录，未启动完整资格或正式计时。

源码冻结前的针对性回归：246项通过、0跳过。新增17项（语义/独立性/错误注入11项，
证据流程6项），其余229项涵盖原核心、执行策略、后端接入、真实树操作、记账配置、
refinement和已有资格/pilot/超时工具。此前单独运行的69项与11项没有重复累计。
结果在 `tests.log`；没有把各测试内部枚举案例另计作测试方法。执行命令：

```sh
PYTHONPATH=src:tests:experiments python -m unittest \
  test_qualification_refactor_evidence test_synchronous_qualification \
  test_paper_jordan test_paper_jordan_sort test_paper_execution_policy \
  test_paper_backend_integration test_heterogeneous_finger_backend \
  test_heterogeneous_finger_split test_heterogeneous_sort_integration \
  test_heterogeneous_work_configuration test_finger_refinement \
  test_common_qualification test_development_backend_pilot test_finger_review_hardening -v
```

## 实际执行与重建结果

执行源码为 **`f77df45d680cd74b94e83635d8c3a7a13aa196c1`**，启动时工作区干净。
本目录的结果保存提交晚于该冻结点；两者不互换。工具读取的140输入选择哈希
仍为 `c8d8f34f7dce619a87d54cffd8567255c80340742f00de072eb5ca771991b17b`。

20例全部在原定每例180秒共享worker预算内完成，0错误、0超时、0跳过。
来源/输入/精确配置/环境见 `development/plan.json` 和 `environment.json`。

| 批次 | 输入数 | 每后端的执行 | 实际证据 |
| --- | --- | --- | --- |
| 64/129，flat/middle及镜像 | 8 | reference＋v2＋fresh minimal | 1,512组新旧完成前缀比较均一致；最终trace、metrics、backend_work也一致 |
| 257/513，flat/middle/heavy及镜像 | 12 | v2＋fresh minimal | 逐前缀审计、比较、外部输出及最终fresh checked replay全部通过 |
| 合计 | 20 | 16 reference、40 v2、40 fresh minimal | 96条已完成版本记录，独立归档重建通过 |

v2的一次执行内部包含两个同步主状态及一个最终fresh replay，不能把“40 v2”
误写成只初始化40个实例；实际观测每次初始化3个。reference的fresh-prefix实例
也未计作独立输入或新样本。1,512是输入×后端的前缀比较次数，不是独立样本数。
同伴和fresh replay使用同一算法，所以不是独立排序证明。

对固定递增flat树路径，实际计数如下（镜像得到相同次数）：

| n | reference `_audit` | v2 `_audit` | reference初始化 | v2初始化 |
| --- | ---: | ---: | ---: | ---: |
| 64 | 2,201 | 312 | 63 | 3 |
| 129 | 8,636 | 637 | 128 | 3 |
| 513 | 本轮未运行 | 2,557 | 本轮未运行 | 3 |

513的旧版132,860仍只是调用模型推导，旧v1在180秒超时；本轮没有把它冒充实测。
树minimal的整森林审计计数为0。普通列表的 `tree_audit_calls=0` 只说明没有
调用树专用 `_audit` 函数，绝不表示普通列表没有执行检查。

历史邻接工作另行记录：64点reference有249,612次上述三处过滤访问，v2有
4,282次邻接链接、3,904次逆序移除；129点对应2,096,262次过滤，以及17,022次
链接、16,254次移除。两种工作单位不同，v2还检查两个实例并进行最终比较，
**不能直接把这些数字相除当成整体加速比**。原有全部历史轮次的判据仍执行。

这些数据为开发验证/资源观察，不是排序性能实验。`resource_wall_seconds`包含
观察、计数、前缀指纹和进度落盘；没有warmup/重复统计。原pilot结果不能代表
主循环入口改动后的minimal性能，本轮不报告新树/列表速度比。

`recheck_report.json`从原始记录核对顺序、每前缀指纹、最终记录、计数公式和manifest，
不调用排序器，但复用冻结计划构造函数；它不是独立算法证明。所有原始记录和
重建报告另由顶层 `SHA256SUMS.json` 绑定。旧v1目录的文件哈希保持不变。

## 当前边界与下一步

本轮完成验证计算重构、覆盖安排版本化、246项回归及20例有界复核。
这支持继续将v2接入**完整共同资格执行器**；该执行器仍需保留原140输入、错误保留、
独立重建及最终版本绑定，并重新执行资格。本轮没有启动140例批次，也没有将
v1的TIMEOUT/NOT_RUN改成v2通过。
正式runner/validator、校准B、人工表示/locality/成本审阅仍未完成；
`full_140_qualified=false`、`performance_eligible=false`、最低交付未验收。

```sh
python experiments/validate_qualification_refactor.py --output NEW_DIRECTORY
python experiments/recheck_qualification_refactor.py NEW_DIRECTORY
```

实际运行需干净工作区，准确执行提交、代码哈希及环境在运行目录保存。
对照checker保留旧fresh-prefix replay和旧历史过滤；新版同步检查减少重复构造覆盖，
不是语义无差别替换。手工证明、全部输入正确性和性能结论均不由此批授予。
