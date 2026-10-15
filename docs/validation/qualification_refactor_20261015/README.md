# 资格验证重构的有界证据（2026-10-15）

本目录先提交源码、[v2检查安排](../../development/qualification_validation_v2_20261015.md)、
`preselected_plan.json`及针对性测试，再执行固定开发复核并归档结果。
未改140输入或其v1超时记录，未启动完整资格或正式计时。

源码冻结前的针对性回归：246项通过、0跳过。新增17项（语义/独立性/错误注入11项，
证据流程6项），其余229项涵盖原核心、执行策略、后端接入、真实树操作、记账配置、
refinement和已有资格/pilot/超时工具。此前单独运行的69项与11项没有重复累计。
完整命令与结果在 `tests.log`；没有把各测试内部枚举案例另计作测试方法。

```sh
python experiments/validate_qualification_refactor.py --output NEW_DIRECTORY
python experiments/recheck_qualification_refactor.py NEW_DIRECTORY
```

实际运行需干净工作区，准确执行提交、代码哈希及环境在运行目录保存。
对照checker保留旧fresh-prefix replay和旧历史过滤；新版同步检查减少重复构造覆盖，
不是语义无差别替换。手工证明、全部输入正确性和性能结论均不由此批授予。
