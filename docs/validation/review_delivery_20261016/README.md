# 导师审阅包：辅助入口保护与正确性覆盖表

本批于 2026-10-16 开始、2026-10-17（Europe/Berlin）完成，沿用开始日期命名。
父基线为 `1d3106d9738ab0072dbf86de3e9124dd7a1add70`。当前交付是导师审阅稿；
不是学校正式提交验收，也没有代填个人信息、确认或签署声明。

## 本轮修改

- 给 `../join_proof_correction_20261016/audit_crosscheck.py` 加入模块入口的
  `sys.flags.optimize` 保护，在读归档及写报告前拒绝优化解释器。
  默认只向 stdout 输出；可用 `--output` 保存到一个尚不存在的新文件，
  避免重跑复核时覆盖旧报告。全部原始检查谓词保留。
- 实现章表 4.1 区分操作级、完整排序、共同组和补充分裂组；正文列出
  repeated-512 的 126/63/189/62 次更新与 balanced/skew 的 126+127、1+252。
  附录解释执行时未提交工作树与后续保存提交之间的区别；局限章关联该表。
- 准备 [英文导师阅读说明](FOR_SUPERVISOR.md)，说明实现贡献、计算模型、
  负面的速度结果及希望重点审阅的表示、混合势能和 locality 论证。
- R3、C1/C2 和势能公式的上轮修订保持；没有再次修改排序核心或重跑计时。

## 实际检查与边界

| 检查 | 本轮结果 |
| --- | --- |
| 优化入口 | `-O`、`-OO`、`PYTHONOPTIMIZE=1/2` 四次均明确拒绝；使用逐字相同的脚本、但目录没有归档，保证拒绝发生在归档读取之前，没有报告文件 |
| 正常入口 | 缺归档对照明确失败；实际完整归档正常复核完成，报告与上轮逐字相同；合计六个子进程，不是六项排序测试 |
| 正常复核内容 | 13284 项旧清单哈希、7600 份含 warmup 的正式记录、152 行统计、17 行当前表、5 格历史比值、525 份冻结目录文件 |
| 操作级历史证据 | 核对原日志的 53 项方法（31 端插＋22 split/adopt），10 项记录的源码哈希与 `cc1aa2d` 相同；没有重新执行这套测试 |
| 18 例结构归档 | 解压全部 18 份报告、核对清单和 108 份原运行记录；外部最终输出、前缀连续性、开关摘要、大小与保存的计数一致；19 项源码哈希与 `84f7e13` 相同 |
| 正式覆盖汇总 | 对 140/12 组已有 coverage JSON 核对原清单哈希并读取；本轮未从所有原始 trace 再重建这两个汇总 |
| 新稿 | 干净构建 68 物理页、最终编译警告 0；页面比较和视觉复核见下面记录 |

18 例的数字按每种 checked 配置原运行汇总：460 次 split、230 次双侧非空、
666 次向旧输出继续端插、212 次再次 split，5349 个完成前缀。其中 224 次
双侧非空的较小侧为 1，另 6 次为 balanced。重复配置及 replay 不计作额外输入。
原结构归档没有保存完整逐事件 trace，因此本轮是重算保存报告的汇总与大小分布，
不是独立重建每一次插入/再次分裂事件，也不是最新版本六例混合更新回归。

## 维护例外与版本

只有旧 `join_proof_correction_20261016` 目录中的 `audit_crosscheck.py` 作了
明确维护修改。该目录原 `SHA256SUMS.json`、旧报告、PDF 和旧 ZIP 均保持原样：
清单中的脚本哈希仍属于 `1d3106d9` 的旧脚本，**不能拿旧清单认证现行脚本**。
旧版可用 `git show 1d3106d9:docs/validation/join_proof_correction_20261016/audit_crosscheck.py`
取得。本批 `delivery_bindings.json` 同时记录旧/新哈希及其余旧文件核对结果；
新审阅包用自己的清单认证所含的修订版脚本，不修改旧归档身份。

本轮辅助检查是在父基线上的工作树修改执行的，精确工具身份以新文件哈希绑定；
不能把父提交写成已含修复的执行版本。操作级和结构批次亦分别绑定其原始源码哈希，
`cc1aa2d` / `84f7e13` 是匹配的后续保存提交，不是当时干净 checkout 的声明。
正式执行仍是 `4a83fa6`，校准仍是 `c5b5ac3`。四份资格/校准/formal 清单、
原始记录、B 表及原生产源码不变。

## 复现与阅读入口

完整仓库根目录、未启用优化的 Python：

```sh
python3 docs/validation/join_proof_correction_20261016/audit_crosscheck.py
python3 docs/validation/join_proof_correction_20261016/audit_crosscheck.py --output /tmp/jordan-new-crosscheck.json
python3 docs/validation/review_delivery_20261016/check_coverage.py --output /tmp/jordan-new-coverage.json
cd thesis
latexmk -lualatex main.tex
```

指定输出必须不存在。`check_audit_entrypoint.py` 是本次六个入口场景的执行程序；
它以排他创建方式保存本目录的新报告，复跑应在去掉这些新生成报告的另一个副本中
进行，不能删除封存记录后原地覆盖。这些命令只读已有证据或构建论文，不重新测量。

PDF 为 `output/pdf/jordan_thesis_supervisor_review_20261016.pdf`，材料包为
`output/packages/jordan_supervisor_review_20261016.zip`。包内含可构建论文源、
完整证明文档、辅助检查及阅读说明；原始性能数据通过仓库取得，不把选摘报告冒充
完整复现数据。包内清单逐文件验收，ZIP 外另有 SHA-256。

干净构建/源码/PDF绑定见 `build_report.json`，逐页像素比较见
`page_comparison.json`，视觉检查结论见 `visual_review.json`。没有扩大输入集、
执行新的生产回归/资格/校准/formal，也没有将有限执行证据当作一般性证明认证。
