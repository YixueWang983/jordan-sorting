# 集中人工审阅、正式配对测量与论文同步

完成日期：2026-10-16（Europe/Berlin）。目录名沿用10月15日冻结协议的身份，
不是测量时间。生产执行提交：`4a83fa6b7a4213e9e5758fe3454e002ebc266459`；
其 Python 源码与资格/校准所绑定的相应源码一致，尤其与校准 `c5b5ac3` 的
`src/`、`experiments/`、`tests/` 完全相同。保存本归档的后续提交不替代执行版本。

## 1. 本次实际完成

- [集中审阅](../../development/finger_final_review_20261015.md)逐项核对表示保持、
  混合成本、locality/精确分组。每项给出源码分支、循环不变量或归纳依据；修正
  搜索“上行前组件”与“刚到达父组件”的区别，显式处理删除虚拟黑层及跨组件势能。
- 审阅是项目本次源码人工数学核对，**不是另一个外部审稿人的认证或机器形式化证明**。
  `manual_review_receipt.json` 绑定具体文档哈希和18份生产源码；凭据本身不证明定理。
  源级线性总工作量采用单位比较/机器字与字典期望查找、摊还扩容模型，不保证任意
  Python 对象的最坏墙钟时间。计算模型与已经论证的表示性质明确分开。
- 先将审阅与论文 span/rank 修订提交为 `4a83fa6`，在干净工作区依次运行两个
  正式 campaign。既有入口检查资格、原始 B 表、全部131份 Python 文件和要求
  一致的环境。未重跑资格、未重选 B、未修改排序器或测量工具。
- 两组均通过独立 validator 重建。`analyze_formal.py` 又读取全部7600份 batch
  记录（含warmup），核对每份输出并重算中位数、R7 IQR和比值，与validator一致。
  这属于记录重建，不是另一次排序执行或新增正确性测试。

## 2. 正式结果与统计单位

| 数据集 | 输入 | sample批次 | sample内调用 | warmup批次/调用 | 状态 |
| --- | ---: | ---: | ---: | ---: | --- |
| common | 140 | 5600 | 62720 | 1400 | 全部PASS |
| targeted_split | 12 | 480 | 3840 | 120 | 全部PASS |

没有ERROR、TIMEOUT、NOT_RUN、删例或重试。每个输入/后端20个sample批次；
批内调用用于时间粒度，不是独立样本。两组与镜像/相关构造不合并成152个独立随机样本。

| 数据集 | 逐输入 tree/list 中位数之比：最小/中位/最大 | 跨输入Q1/Q3 |
| --- | --- | --- |
| common | 1.113956 / 2.897505 / 3.534560 | 2.117054 / 3.210365 |
| targeted_split | 3.147083 / 3.180265 / 3.213334 | 3.164827 / 3.189364 |

所有输入的树中位数都大于对应列表中位数。范围和跨输入四分位数不是置信区间。
common没有两侧非空split；targeted的12次目标分裂来自已冻结资格trace，不能
声称所有formal调用都收集了详细操作账本。新结果不与旧pilot或历史60例混合。

common的逐cell相对IQR中位数为列表1.3744%、树1.0786%；最大值分别50.2632%、
61.8091%，均位于 `n33-strict_flat-00-mirror`。不为它们推测原因，也不删除。
targeted相对IQR中位数为1.1836%/1.5484%，最大9.0794%/7.5214%。
common有1个sample批次低于10ms，targeted为0；B依照原校准中位数规则保持不变。
sample计时间隔合计183.511291318秒和21.289948917秒，**不是campaign墙钟时间**。

运行环境：CPython3.12.14、Apple M4/arm64、10逻辑核、16GiB、macOS26.6，
GC开启阈值700/10/10。捕获时为电池供电100%；不声称整个campaign温度/频率恒定。
common环境UTC时间 `2026-10-15T21:35:25.430904+00:00`，targeted为
`2026-10-15T23:51:29.034515+00:00`，后者在柏林已是10月16日。
两组顺序执行，未与测试、checked资格、编译或绘图争用机器。

工具保留的 `performance_eligible=false` 是其“不自行认证数学/总交付门槛”的
字段，没有改成true来制造通过。实际执行身份是 `stage=formal`、真实时钟，
两组报告 `archive_valid=true, complete=true`；数学审阅依据是上面的正文和独立
绑定凭据。该字段不能用于把这些原始sample重新描述为calibration，也不能用
PASS反过来证明复杂度。

## 3. 复核入口

从仓库根、未修改的生产/实验 Python 源码运行（不重新执行排序）：

```sh
PYTHONPATH=src:experiments python3 experiments/validate_matched_measurement.py \
  docs/validation/final_review_formal_20261015/formal_common \
  --qualification docs/validation/common_qualification_v2_20261015/qualification \
  --calibration docs/validation/id_lifecycle_calibration_20261015/calibration_common

PYTHONPATH=src:experiments python3 experiments/validate_matched_measurement.py \
  docs/validation/final_review_formal_20261015/formal_targeted_split \
  --qualification docs/validation/split_trace_followup_20261015/qualification \
  --calibration docs/validation/id_lifecycle_calibration_20261015/calibration_targeted_split

python3 docs/validation/final_review_formal_20261015/analyze_formal.py
```

第三条重建CSV、JSON及两幅图，需Matplotlib；绘图依赖在**测量完成后**单独安装到
工作目录，没有改变测量解释器环境。版本见 `analysis_environment.json`。PDF元数据
可能带生成时间，不要求重绘PDF逐字相同；数值来自原始记录，当前产物哈希已记录。
两份 `formal_*_validation.json` 是实际运行独立验收入口保存的完整报告。
每个formal子目录自带原始manifest；不要重封旧manifest、修改raw或重写B表。

## 4. 论文、旧归档与未完成项

论文修正内部ROOT span=0、所有外部叶span=1及rank约定；加入审阅后的成本摘要。
摘要、研究问题、实现、方法、结果、限制和结论按当前证据重组；历史含回滚结果
压缩为单独小节，详细旧表与分析文件保持原样。新图来自本次原始记录。
新PDF为 `output/pdf/jordan_thesis_formal_20261016.pdf`，构建与页清单见
`thesis_review/`；旧PDF不覆盖。最终68物理页、零构建警告；八章正文区间13–62共50页，整份PDF包含10张右页开章/前置排版空白页（已计入68页）。字号、间距、页边距及右页开章规则未改。

封面明确是审阅稿；尚未取得的作者、学号、导师、第二阅卷人和正式提交日期没有
伪造或打印成模板文字。正式提交前须填写 `thesis/config/metadata.tex` 并关闭
`ReviewDraft`。本轮不代表导师已审阅或学校提交要求已检查完毕。

`old_archive_preservation.json` 核对995+103+3948项旧哈希，全部未变。
`src/`、`tests/`、`experiments/`、`data/`、`results/` 未修改；本轮没有新增生产
代码，因此没有重复宣称复跑整套生产回归。原140例、12例及校准均没有重新执行。
后续重点是对数学论证和整篇审阅稿的独立审核、逐项意见处理及最终提交资料；不
因为实测较慢改树、扩大到380例或重测直到得到更好结果。
