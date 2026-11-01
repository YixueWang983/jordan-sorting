# 无插桩正式计时前的资格检查与校准（2026-11-01）

本目录保存实际 qualification 和 calibration，**没有正式采样或作者批准收据**。

| 数据集 | 输入数 | qualification | calibration | 固定 B 分布（B: 输入数） |
|---|---:|---|---|---|
| common | 140 | 全部通过 | 全部通过 | {1: 24, 2: 13, 4: 27, 8: 28, 16: 26, 32: 22} |
| targeted_split | 12 | 全部通过 | 全部通过 | {8: 12} |

两组档案均已用独立验证器检查。每个输入的 B 由原候选阶梯和双后端中位批时长均至少 10 ms 的规则确定，没有调整输入、统计规则或筛除样本。校准时长不能作为正式性能结论。

- 实现、等价性、qualification 和校准均使用 `3bfc839fae8da3061938f48f490e936deb0c002e`。
- 预登记协议提交：`4aaf0022603e1abd9550b956c51da98ae89c29cf`，先于首次校准，见 [时间顺序核对](chronology.json)。
- 生产源码共 19 个文件，见 [摘要清单](production_sha256.json)；校准和正式执行也绑定实验工具源码。
- 机器：Apple M4；Python 3.12.14；系统：`macOS-27.2-arm64-arm-64bit`。
- 每组校准开始及每个输入前后均记录 `AC Power`、`lowpowermode 0` 和原始 pmset 输出。校准期间未并行运行测试、编译或其他实验。
- [保存性核对](preservation_final.json)：旧档案/PDF 的 18,106 个文件全部保持原字节，附录 A 未改。

资格检查记录位于 `qualification/common`、`qualification/targeted_split`；校准记录位于 `calibration/common`、`calibration/targeted_split`；对应的 `*_validation.json` 是独立复核结果。各原始档案的 `manifest.json` 原封保留。

下一步严格按作者提供说明第 6 节执行，见 [作者审阅和执行清单](../../thesis/uninstrumented_author_review_20261101.md)。没有实际正式档案之前，不更新论文主结果或生成声称包含新结果的 PDF。

## 档案复核命令

在仓库根目录，用绑定的 Python 3.12.14 执行以下命令（两数据集分别运行）：

```sh
PYTHONPATH=src:experiments /Users/schnee/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 experiments/validate_common_qualification_v2.py docs/validation/uninstrumented_preflight_20261101/qualification/common --dataset common
PYTHONPATH=src:experiments /Users/schnee/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 experiments/validate_matched_measurement.py docs/validation/uninstrumented_preflight_20261101/calibration/common --qualification docs/validation/uninstrumented_preflight_20261101/qualification/common
```

`targeted_split` 使用相应目录和 `--dataset targeted_split`。只要后续提交仅新增文档/档案而不改动绑定的 Python 源码，正式入口可继续使用本次校准；源文件变化必须按协议重新审查，不得绕过检查。
