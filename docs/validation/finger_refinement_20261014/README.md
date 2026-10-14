# 物理表示与 locality 归纳的有界检查（2026-10-14）

生产源码基线：`6c259a8feea10726371cacb8ef4fda00626f34ae`。
本轮没有改 `src/`，没有改论文、历史数据或证据工具 v2；新增的是
[人工论证](../../development/heterogeneous_representation_locality_20261014.md)、
独立 ghost model、物理解码测试及本目录记录。
人工论证待审阅；本目录不是形式化证明证书、最终资格或性能实验。

## 实际执行

| 执行对象 | 本轮结果 | 解释边界 |
| --- | --- | --- |
| 5 个测试模块 | 89 项通过、0 跳过 | 9 项新增 refinement 测试 + 80 项既有真实树操作、接入和记账配置回归；不是 89 项新端到端测试 |
| 方向转换往返 | 271 个着色形状 | 1–10 叶，包括红根；先显式黑化，比较完整逻辑形状、节点身份、rank、span、key；属于上述测试内部案例 |
| 真实 finger split | 1,088 个形状／切口组合 | 所有 1–9 叶黑根合法形状及每个 cut；独立解码两输出、检查叶身份／集合守恒和 registry 可达性；属于上述测试内部案例 |
| 完整主循环逐阶段检查 | 694 次输入案例、1,388 次原始执行 | 678 个 n=3..7 合法排列 + 4 个固定／镜像案例 + 12 个 n=128/129、k=3/7/19 及镜像案例；每例 ordinary、tree_off 各运行一次 |

694 个原始值序列哈希均不同；平移、镜像或相同相对顺序不因此成为独立结构样本。
测试里的部分输入与另存的完整主循环批次重复，不把两者加成更多独立样本。
测试包含固定小例 checked 检查；独立归档批次统一使用 minimal。
树配置显式 `detailed_work=False`，无 replay；既有回归中的 replay 不计入这里的
1,388 次原始执行。

每种后端的归档原始执行分别包含：4,610 个完成前缀，3,916 个更新迭代，
1,236 次 split，其中 68 次双侧非空；398 次 z1 边界修正，152 次 z1 输出修正。
这是调用覆盖，不是统计样本或运行成本。对状态的观察会增加额外检查开销，
本轮不收集／报告排序耗时。

真实 finger split 的分支计数：红兄弟 37、near 旋转 25、far 旋转 63、
短缺传播 68；左旋 88、右旋 138。这些来自 1,088 个形状／切口测试中的实际
操作 bucket，不叠加插入构造、审计或上述完整排序调用。

## 本轮新增检查的实质

- 仅从输入值和索引独立重建最小包围 parent、直接 children 和原论文的精确分组
  （由该 parent family 最近 pair 决定）。不仅比较 child 集合和“至多两组”。
- Step 3(a) 前独立推导左右邻居、所需端点、同 owner／不同组、可取得的全部
  children，以及输出邻居。预期结果只作观察后的比较，不传给排序器。
- 检查 Step 3(a) 保持 source ID／owner／大小／端点，树 source header 对象也不变；
  Step 3(b) 后按新前缀检查恢复的完整森林和分组，验证旧 source header 退役；
  Step 3(c) 检查几何 base anchor、z1 修正和最终输出。
- 物理解码直接读取反向链、节点和 header 字段，不调用生产 `_up`、`_inner`、
  `_audit_tree` 或修复方法来确定预期孩子。独立重算 separator、rank、不同角色
  的 span、根缓存、端点、稳定身份及 registry 可达性，并与输入模型的分组比较。
- 负例包括错误反向指针、rib span、根缓存，以及“成员和次序都没变，但把两个
  child groups 合为一组”。最后一项会被新增精确分组判据拒绝。

物理解码仍读取生产节点类型，测试形状构造器复用已有有界红黑形状生成程序；
它不是另一个独立排序算法。几何模型为慢速检查模型，不能放入 minimal 正常路径。
有限案例用来寻找人工论证的反例，不能代替局部修复或 locality 的一般性证明。

## 复跑

在仓库根使用未优化 Python（本轮 Python、环境和源码哈希见 `plan.json`）：

```sh
PYTHONPATH=src:tests:experiments python3 -m unittest \
  test_finger_refinement test_heterogeneous_finger_backend \
  test_heterogeneous_finger_split test_heterogeneous_sort_integration \
  test_heterogeneous_work_configuration -v
python3 experiments/validate_finger_refinement.py --output /tmp/jordan-refinement-new
```

输出目录须不存在；归档程序有 180 秒整批预算，无重试和替换。失败保留已完成
案例并停止；只有完成全部循环且源文件身份未变才生成 accepted 汇总。
本目录 `plan.json` 是运行前固定的计划及代码身份，`cases.jsonl.gz` 是逐例原始值
和两后端覆盖计数，`summary.json` 可由逐例计数重建。
`verification.json` 记录本轮实际重建结果；`SHA256SUMS.json` 绑定归档文件，
不包含自身。`regressions.log` 保存 89 项测试及形状分支计数的原始输出。

没有重跑整个仓库全部测试，没有编译／逐页检查论文，没有执行实际 pilot 或
正式匹配计时。未将 `timing_ready` 改为 true，也未宣布高效后端最低交付完成。
