# R3 暂态勘正与整篇审阅稿交付检查

日期：2026-10-16（Europe/Berlin）。本次基线为
`ce0148bf70f10eb1683e13abe573406413762331`，正式执行版本仍是
`4a83fa6b7a4213e9e5758fe3454e002ebc266459`，校准版本仍是 `c5b5ac3`。
这里只修正论证和论文，新增局部核对与只读复核记录；生产、实验及原测试目录未改。
没有重跑共同资格、校准或正式 sample，没有增加输入或重新选择 B。

## 修改及结论

1. [R3](../../development/finger_final_review_20261015.md) 明确三个递归出口：
   黑根无冲突、黑根四种局部修复、红根透传。红根可以返回一条根—孩子红红连接；
   叶序、等实际黑高和元数据仍保持，原黑父消除该连接。输入根预黑化保证顶层
   返回内部合法，最后根黑化只解决根色，不能承担内部冲突修复。
2. C1/C2 依赖完整契约，区分合法下降输入与回溯暂态；C1 增高的强性质只用于
   完整 join 出口。较早表示/成本文档加上同一勘正，避免继续引用过强句子。
3. 实现章给出上述暂态摘要；列表大小势能式限定为双侧非空、`1<=a<=b`，
   空侧单列 `DeltaPsi=0`。
4. 全文交叉检查另修两处旧表述：算法章明确列表 split plan 与树的 transfer/
   split/adopt 不同；附录区分“不继承线性界”和“已有二次复制下界”。
   旧审阅凭据只绑定旧文本；正式执行发生在原始审阅之后、本次勘正之前。
5. README 将旧里程碑显式列为历史，当前入口指向本次审阅稿。

这些修订关闭本次指出的 R3 覆盖与公式条件问题，不表示重新独立认证了全部数学
论证，也不把局部测试当作一般性证明。未发现要求改变算法或重跑计时的证据。

## 本次实际执行与核对范围

| 工作 | 结果与边界 |
| --- | --- |
| 生产 join 暂态局部检查 | 7 项测试方法、11 个内部场景，0 失败/错误/跳过；包括两例红根透传及镜像、LL/LR/RR/RL、无修复出口、红输入预黑化及两个空侧出口 |
| 观测内容 | 实际 `TreeOperations`、节点与账本；另行读取向下字段核对叶序、黑高、separator、span、稳定叶/handle/pair 和允许的暂态；不是完整排序资格 |
| 正式记录只读重建 | 两个原 validator 入口实际运行，common 140 与 targeted 12 均 `stage=formal, archive_valid=true, complete=true`；完整报告与原报告相同 |
| 数字交叉核对 | 全部7600份含warmup的原始记录重算批次/调用/区间总和；152份统计与CSV对照；当前表17行、历史比值5格与正文一致 |
| 保存身份 | 四份原清单共13284项哈希全部匹配；525份冻结目录受控文件与 `ce0148b` 逐文件相同 |
| 论文 | 最终干净构建68物理页、零警告；逐页视觉检查，详见 `visual_review.json`、`page_inventory.json` |

`initial_fixture_failure.log` 保留探测程序初次失败：沿用了未建立 handle→leaf
反向引用的历史 detached-shape builder，所有失败在调用 join 前发生。新程序在
夹具初始化中补齐该引用，再观测生产操作；没有关闭断言或修改生产代码。
最终结果见 `join_transient_tests.log` 和 `join_transient_results.json`。

两个原例在生产方法中确实出现了返回子树内部的红红，再由黑祖先修复；最终结果
合法。夹具用等比例 key 映射 `0,10,20,30` 保留同一树形和次序。因此修正对象
是归纳契约，不是为了适应原句而改算法。

## 全文与排版检查

已阅读摘要、八章正文、附录和书目，逐项检查：研究问题与结论对应、oracle 与
自身输出来源、无回滚语义、两后端表示差别、v2 与旧 replay 覆盖、计时边界、
版本归属、批次统计单位、范围/四分位数不等于置信区间、历史/当前结果分开。
16个书目条目成功解析，编译无未定义引用、交叉引用或缺字警告；这不等于本次
重新逐图核验所有原论文或再次证明全部 locality 分支。

正式结果仍为5600+480个sample批次、62720+3840次调用，warmup为1400+120次。
比值范围和中位数不变；“树较慢”仍指逐输入的后端中位数。common的空侧分裂
局限和targeted的有限较小侧/后续更新覆盖均保留。图文件未重绘。

PDF：[本次审阅稿](../../../output/pdf/jordan_thesis_review_20261016.pdf)。
全书68页，正文物理13–62共50页；空白页为2、4、10、12、16、34、42、54、58、62，
已含在68页内。字体、行距、页边距与右页开章设置未改。逐页检查使用1.5倍渲染、
每组4页且每页约893×1263像素，并针对勘正页/图表再次查看；检查范围记录为视觉
与内容一致性检查，不把“零警告”等同于数学或学校提交验收。

## 封面、声明与提交边界

封面明确为供导师阅读的 review draft；未打印姓名、学号、导师等占位文字，
PDF author 元数据为空。正式注册题名、个人信息、导师/第二阅卷人、个人提交
期限与适用考试条例仍需当事人确认；未代填、签署或发送声明。

2026-10-16读取的[考试办公室说明](https://www.imp.fu-berlin.de/fbv/pruefungsbuero/index.html)
仍列 Informatik 为电子提交，并要求声明原件另交；
[官方表格页](https://www.imp.fu-berlin.de/fbv/pruefungsbuero/Formulare/index.html)
提供声明。[英文声明](https://www.imp.fu-berlin.de/fbv/pruefungsbuero/Formulare/Selbstaendigkeitserklaerung_EN.pdf)
说明其为方便阅读的译本，德文版有约束力。正式提交前应再次核对。
[Informatik FAQ](https://www.mi.fu-berlin.de/stud/beratungszentrum/FAQ-Hilfe/FAQ-Abschlussarbeit/faq_abschlussarbeit_info/index.html)
列出2014硕士条例的一般50–80页范围；本稿继续遵循用户更严格的50–70页目标，
不据此推定个人适用规则。此次取回的FAQ未找到之前README所声称的Logo禁令，
已撤回那项来源归属；审阅稿继续不使用Logo。

## 复核与材料包

从仓库根运行，Python应关闭优化模式：

```sh
python3 docs/validation/join_proof_correction_20261016/check_join_transients.py
python3 docs/validation/join_proof_correction_20261016/audit_crosscheck.py
cd thesis
latexmk -lualatex main.tex
```

第一条仅执行本次局部例子；第二条读取原归档和保存的validator报告，核对数字、
哈希与冻结文件，不执行排序。两份validator完整只读入口仍见
[原归档复核说明](../final_review_formal_20261015/README.md#3-复核入口)，本次输出为
`formal_common_readonly.json`、`formal_targeted_readonly.json`。不要执行原分析脚本
去覆盖已封存的图或清单；需要重画时在另一个副本中运行。

`output/packages/jordan_review_20261016.zip` 是审阅材料包：含新PDF、可构建的
LaTeX源、修订证明及本次核对材料。完整生产代码与原始数据通过仓库版本取得，
没有把包内摘要冒充完整原始数据。包内清单绑定所含文件。

旧PDF、原审阅凭据、资格/校准/formal原始记录、manifest与B表均未覆盖。
`crosscheck_report.json` 同时记录旧证明SHA-256及修订后SHA-256；旧文本可用
`git show ce0148b:docs/development/finger_final_review_20261015.md` 取回。
本次没有重新执行全仓回归、排序资格或计时，也没有再次独立证明未修改的全部引理。
