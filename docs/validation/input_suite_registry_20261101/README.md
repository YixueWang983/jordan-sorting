# 阶段二：五来源统一输入清单与核对结果

日期：2026 年 11 月 1 日。追加协议已单独提交并推送：
[afbbff68525b112ad9bc03c163b435ca74590212](https://github.com/YixueWang983/jordan-sorting/commit/afbbff68525b112ad9bc03c163b435ca74590212)。
本目录落实[追加协议](../../plan/uninstrumented_rerun_addendum_20261101.md)第 1.2 节。
**这里只做固定文件读取、输入身份核对和去重，没有运行生成器、oracle、排序、
等价性、qualification、校准或计时。**

## 核对结果

| 来源 | 纳入条目 | 来源内重复 | 跨来源重复 | 规范输入 | 排除条目 |
|---|---:|---:|---:|---:|---:|
| common | 140 | 0 | 0 | 140 | 0 |
| targeted_split | 12 | 0 | 0 | 12 | 0 |
| structural | 18 | 0 | 0 | 18 | 0 |
| geometric | 100 | 0 | 0 | 100 | 0 |
| seeded | 32 | 0 | 0 | 32 | 8 |
| 合计 | 302 | 0 | 0 | 302 | 8 |

302 个纳入条目和 8 个排除条目均逐项与绑定文件核对了原值、原索引/相对顺序、
关键元数据和归一化秩身份。五来源当前没有完全重复序列；仍发布全部 302 行映射，
每个 canonical_case_id 都指向自身，duplicate_of 均为 null。
来源数量不代表独立随机样本数量。

统一清单的内容身份（去掉 suite_sha256 字段后，按固定 JSON 编码计算 SHA-256）：

a8c2fe3aa2fe4b45bbe876db9e9dabe3b7f95fd666b3c3afab0776bef67234b7

文件字节摘要另见 manifest.json；内容身份与文件字节摘要不同。

## 固定输入及元数据

- 原值保持原样。seeded 保存 0..n−1，统一身份另用 1..n 的秩序列；
  不把归一化秩覆盖到实际待运行值中。镜像、逆序或旋转不自动合并。
- 去重归属顺序为 common → targeted_split → structural → geometric → seeded，
  来源内保留原数组顺序。先核对秩摘要，再逐项比较完整秩序列。
- seeded 只读取原 protocol.json 的 stress 条目，从其 40 个中排除 n=1500 的 8 个；
  不纳入同一 inputs.json 内的十五输入诊断。排除的是 seed 11–14 × bias 0.05/0.25，
  原 source_index 为 6、7、14、15、22、23、30、31。其余 32 个保留原索引，不重新编号。
  排除原因见追加协议第 1 节，旧输入文件及其摘要未修改。
- targeted_split 的 12 例和 structural 的 balanced/skew 共 12 例标为 values_for；
  smaller_side_k 覆盖 1、3、7、19、30、62、126。
  structural 的 6 个 repeated 条目独立标注构造族及 shape，其 k 为 null。
- common 的四类嵌套标签、原 seed、mirror、base_id 均保留。
  structural 额外保留 legacy_dataset=structural_split。
  geometric 保留全部 100 例及原种子，未按双侧 split 结果筛选。
- 每个条目保存源文件路径、字节摘要、JSON pointer、完整原始记录内容摘要，
  以及需要逐项核对的 source_metadata。旧 selection 的原非值元数据完整保留；
  几何旧 trace/多边形资料由固定源文件和完整记录摘要绑定，不复制成新实验记录。
  历史元数据中的 status 或 oracle 字段仅描述旧证据，不赋予新一轮资格状态。
- 不重新调用已有输入生成器；每个固定文件的字节摘要或旧 selection 身份不符即拒绝读取。

## 文件与入口

| 文件 | 内容 |
|---|---|
| [suite.json](suite.json) | 302 个纳入条目、8 个排除条目、输入与协议绑定、清单内容摘要 |
| [summary.json](summary.json) | 各来源数量、重复数、规范输入数、规模和构造族统计 |
| [deduplication.json](deduplication.json) | 全部 302 个条目的归属与重复映射 |
| [exclusions.json](exclusions.json) | 8 个 n=1500 条目的原值、元数据和排除依据 |
| [initial_execution_state.json](initial_execution_state.json) | 与输入清单分离的初始状态；302 条目各阶段全部 NOT_RUN |
| [verification.json](verification.json) | 独立读取原档案后生成的 310 条逐项核对记录 |
| [preservation.json](preservation.json) | 24,075 个既有文件字节核对，无变化 |
| [manifest.json](manifest.json) | 本目录文件和本阶段工具/测试源码的 SHA-256 |

[输入注册模块](../../../experiments/input_suite_registry.py)仅使用标准库，
集中登记五来源、固定文件摘要、字段映射、排除规则和去重规则。
load_suite() 返回统一清单，canonical_cases() 提供全部或指定来源的规范输入；
尚未连接到旧实验执行入口。

[独立核对程序](../../../experiments/validate_input_suite.py)直接重新读取绑定的旧文件，
另行重建秩序列、逐项检查字段和来源顺序，并重建去重归属及各来源统计。
它不调用注册模块的 load_suite、load_source、rank_normalize、assign_canonical 或
summarize，也不信任已有汇总。只共享固定来源定义和协议身份。

可在仓库根目录重建到一个**尚不存在**的新目录，避免覆盖本目录：

    python3 -B experiments/input_suite_registry.py --output /tmp/jordan-input-suite-review
    python3 -B experiments/validate_input_suite.py --input /tmp/jordan-input-suite-review

这些命令只处理输入文件，不运行 qualification 或计时。

## 验证与停止点

9 项针对性输入测试全部通过，见
[test_input_suite_registry.py](../../../tests/test_input_suite_registry.py)。
覆盖原值平移后的去重、镜像保留、异常数值拒绝、源文件改动拒绝、全部固定输入核对、
排除索引、构造参数、摘要重算后的元数据篡改、虚假资格状态和伪造汇总/映射。
独立进程检查确认读取和验证未导入 oracle、生成器、排序或实验执行模块。

src/、既有验证档案、results、论文和输出目录中预先记录的 24,075 个文件 SHA-256
全部一致；未修改原协议、旧档案或已有实验脚本。当前仅增加输入读取/核对模块、
相应测试和本目录。

追加协议已经提交并推送；本阶段代码及清单仍为本地待审阅改动，尚未提交或推送。
本目录不是最终运行版本的等价性或资格证据；初始状态文件不会因输入核对通过而
改成 PASS。阶段二到此停止，未开始阶段三的统一执行入口、分析接入或全量测试，
也未运行任何本轮前置实验或采样。
