# 大规模输入资格探测与边界复制核对

2026 年 10 月 11 日，预先固定的 16 个候选全部通过 oracle 认证、完整 checked diagnostics（含同核前缀 replay）及独立新状态 minimal 输出核对。候选覆盖 256/257、512/513，每规模 flat、low、medium、深嵌套 heavy 各一例。两种模式分别与外部排序判据比较。

本批 rank 输入互异；未将它们宣称为相对所有历史批次新增的输入。深嵌套 heavy 的最大深度分别为 127 和 255，不能代表所有 heavy 结构。low/medium 使用既有固定块构造，不属于尚待实现的扩展生成器。

每例 worker 上限 180 秒、每规模批次 720 秒；四批预算容量合计 2,880 秒（48 分钟），并非耗时预测。全部规则与候选顺序在生成前写入 campaign_config.json。资源失败终止该规模的余项，但其他预定规模继续；正确性或执行错误终止后续批次。实际无失败、超时、重复或未运行项。

| 长度 | flat 秒 | low 秒 | medium 秒 | heavy 秒 |
| ---: | ---: | ---: | ---: | ---: |
| 256 | 1.024 | 1.469 | 2.440 | 1.412 |
| 257 | 1.051 | 1.496 | 2.430 | 1.435 |
| 512 | 5.014 | 8.962 | 16.031 | 7.833 |
| 513 | 5.041 | 8.657 | 16.155 | 7.820 |

四批记录的资源墙钟合计 88.277 秒，最慢单例 16.155 秒。它们包含生成、认证、进程启动、完整 checked/replay、minimal 输出核对及证据处理，是验证资源观测，不是排序 benchmark。不能据此线性外推 380 个候选的耗时，也不据此降低完整 checked 标准。

下一步保留 180 秒单例上限，并在扩大候选前明确整批预算；继续探测不同 heavy 形状和 seeded incremental 输入。正式性能结果仍需冻结输入资格、完成新 runner/validator 与 pilot。本次未执行正式计时。

## 文件与复核

- qualification/：冻结配置、源码和环境身份、16 个逐例记录、四批汇总、coverage 和哈希清单。
- resource_summary.csv：从逐例记录提取的资源观测。
- probe_verification.json：归档完整性、身份及记录一致性核对；未重跑 checked/replay。
- verify_probe_archive.py：可重跑的只读核对脚本。
- boundary_cost/：16 个递增/递减例的复制计数核对，全部符合 (n/2-1)^2 且 split 为零；这些是独立成本探针，不并入 16 个资格候选。
- check_boundary_copy_cost.py：在原方法入口观察插入前列表长度，随后调用原实现；不计时、不改变排序逻辑、不模拟完整解释器访问量。

从仓库根目录运行：

```sh
python3 docs/validation/cost_and_qualification_20261011/verify_probe_archive.py --repo . --archive docs/validation/cost_and_qualification_20261011/qualification
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:experiments:tests python3 experiments/probe_large_qualification.py --output results/preflight_runs/NEW_UNIQUE_DIRECTORY
python3 docs/validation/cost_and_qualification_20261011/check_boundary_copy_cost.py --repo . --output results/boundary_copy_NEW_UNIQUE_DIRECTORY
```

重跑目录必须不存在；不得覆盖本次归档。源码身份按实际工作树文件哈希记录，基础提交 b6a407461c2f94a4b491016376861142f4b14577 不包含本次新增工具；不能仅凭 HEAD 认定工具版本。
