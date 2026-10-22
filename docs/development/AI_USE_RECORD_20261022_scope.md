# AI 使用说明与个人反思（时段限定与影响范围补充）

更新：2026-10-22。修订基线：`46ac95db7d771b503e3eca5afe28b7661fd697d5`。

**状态：已补充可定位的影响范围，全部披露尚未完成。** 本版承接已并入反思的记录；
保留反思原文，补回 PDF 的非首次使用限定，列明现有历史不完整，准备正文标注方案供导师确认。
前版记录和清单原样保留。

作者已于 2026-10-22 明确要求“并入吧”。前一版据此将已确认的 418 词英文反思
原文并入论文附录 B，并同步工具用途与案例归属。本版保留该正文与配套中文对照。
高效后端是作者自己确定的项目目标；ChatGPT 网页版的额外用途与 Claude 的发现归属
沿用本人确认的记录。前版记录、PDF 及清单保持原样。

本稿依据作者本日补充、已保存的修订材料和所提供的 Claude 审阅说明整理。
研究由作者主导，AI 作为辅助工具。按具体活动记录辅助范围，不估算贡献比例，
也不依据提交者姓名或工具执行次数推断作者在会话之外完成的工作。
本文记录已采用的反思及使用说明；不是已签署的独立性声明。
10 月 20 日审阅包中的旧记录保持原样，本稿不改变旧包的身份或清单。

## 一、作者本日确认的事实

- 使用的工具包括 Codex、Claude 和 ChatGPT 网页版。
- 作者进一步明确确认：ChatGPT 网页版用于翻译、算法解释、审阅意见讨论和项目规划。
- 高效后端必须完成是作者自己确定的项目目标，不写成导师明确提出的要求。
- 没有据此添加 DeepL、Google 翻译等未经确认的工具。
- 最有帮助的用途：查找文献、帮助建立项目架构、将通俗表述转成学术语言，
  以及检查和修正 LaTeX 语法错误。
- 作者注意到 AI 建议可能遗漏算法步骤，希望采用项目中可核对的具体例子。
- 作者对最终成果满意；目前没有明确认为不用 AI 会更快的环节。

后两点的写法必须保留边界：下文以有记录的**证明前提遗漏**作为具体例子，
不把它改写成一次已经证实的生产算法漏步事故。也不编造“手工更快”的个人经历。

## 二、Dokumentation der KI-Nutzung / 工具与用途

| Tool | Provider / version | Period supported by current information | Assistance and affected work |
| --- | --- | --- | --- |
| Codex desktop | OpenAI; session-specific model versions not fully documented | Recorded revision work: 11–22 October 2026; this is not a claim about the first-ever use | Writing support: outline and structure suggestions, translation, academic wording, and LaTeX syntax/build troubleshooting. Technical support: literature search and project-architecture discussion; code and test changes; experiment and validation tooling; execution and inspection of checks; proof-exposition revision and correction. This reflection was revised from the author's supplied account and English draft; a Chinese review translation was also prepared. |
| Claude | Anthropic; exact serving model not independently verified | Reviewer-reported reviews on 17 and 20 October 2026, and disclosure discussion on 22 October | Technical and manuscript review, including the missing premise in the English proof exposition and the incomplete diagnostic table, as well as access-hook overhead and interpretation; reviewer-supplied diagnostic/stress scripts and test reports. These reports are distinguished from locally reproduced evidence. |
| ChatGPT web interface | OpenAI; model version not specified by the author | Used during thesis preparation; available records do not establish exact dates or a complete history | Translation, algorithm explanations, and discussions of review findings and project planning, explicitly confirmed by the author on 22 October. The available record does not locate exact dates or passages; no complete account history has been inspected. |

模型备注：所提供的 Claude 说明自报配置标签为 `claude-opus-5-5`，并同时说明
实际服务模型可能不同。因此该标签不作为已核实型号写入工具表。
版本信息缺失时不猜测；翻译和 LaTeX 检查也不应掩盖已记录的代码、实验工具和论证表述辅助。

## 三、代表性请求、产出和采用方式

以下保留可核对的请求摘录与产出摘录。它们不是完整聊天转录；概括的响应明确标为概括。
外部审阅指出问题、Codex 执行修订、作者决定采用是不同环节，不合并成作者亲自执行了全部检查。

### 示例 1：完整展示诊断结果

- **来源：** 作者转交的 Claude 第二轮审稿意见，随后在 Codex 中处理。
- **请求摘录：** “表 6.5 改为 15 行全列，或按 n × 层级列 15 格。”
- **Codex 辅助产出摘录（生成的论文文本，不是聊天原话）：**
  “Four of fifteen cases, the large heavy constructions, favor the hook-free
  tree; the remaining eleven take 1.09–1.68 times the list time.”
- **如何采用：** 从已保存的原始批次重建全部十五行，修改结果表、摘要和结论，
  保留四例更快、十一例仍较慢的结果；没有删除不利数据或重新计时。
- **对应证据：** [结果章](../../thesis/chapters/results.tex)、
  [本地补充重建报告](../validation/thesis_review_round2_20261020/local_supplement_recheck.json)。

### 示例 2：补回 locality 论证的适用前提

- **来源：** 作者转交的同一轮 Claude 审稿意见，随后在 Codex 中处理。
- **请求摘录：** “A.5/A.6 补前提”；“全文能检索到 bracket 条件，并注明出处为 Fung p. 88 (b)”。
- **Codex 辅助产出摘录（论文文本）：**
  “In the latter case, z_j and the re-entry point z_k bracket all other
  finite endpoints of the region.”（此处将原 LaTeX 数学符号转为纯文本。）
- **如何采用：** 对照原文印刷页 88，在 A.5 补充 dummy 外侧间隙的夹住条件，
  在 A.6 解释该条件为何保证有空闲分组槽。修改的是证明表述；排序核心未变。
- **对应证据：** [证明附录](../../thesis/appendix/backend_argument.tex)、
  [第二轮修订核对](../validation/thesis_review_round2_20261020/README.md)。

### 示例 3：依据本人经历组织和翻译反思

- **来源：** 作者 22 October 2026 在 Codex 中的补充。
- **请求摘录：** “最有帮助的点在于找文献以及帮我立项目架构帮我把通俗的语言转化为学术用语”；
  “最终成果满意”；“哦补充一个 更方便的 帮我检查 latex 语法错误”。
- **后续调整：** 作者提供了以个人贡献为主线的英文稿，随后要求采用本次小修。
- **响应：** 下节已采用的英文反思及中文对照。反思保留“目前没有明确的手工更快案例”，
  用已归档的证明遗漏说明局限，没有虚构算法事故或个人经历。
- **采用状态：** 作者明确授权并入；418 词英文正文已纳入附录 B，并就本次语言辅助作就地说明。
  本次组织、翻译和语言修订本身计入 Codex 的使用范围。

## 四、Reflexion der KI-Nutzung / 已并入的英文个人反思

> Revised with Codex from the author's Chinese account, the English draft
> supplied for revision, and the author's explicit clarifications on 22 October
> 2026. The author approved inclusion in Appendix B on the same day.

My contribution centred on defining the research requirements and directing the development and evaluation of the project. I treated the efficient backend as a core project requirement and kept subsequent development focused on it. I required the implementation to recover its output from its own maintained state and maintained a clear distinction between implemented functionality, bounded testing, complexity arguments, and measured performance. These requirements guided the assessment of proposed changes and the presentation of results.

I used Codex, Claude, and ChatGPT for technical and language assistance. They contributed implementation suggestions, code changes, proof formulations, and review findings. I communicated requirements, set priorities, requested explanations, and decided which revisions to pursue. When a data structure was unfamiliar, I asked for examples explaining the relationships between the Jordan algorithm, sibling groups, and the red–black tree. Particularly useful assistance included finding literature, discussing the project architecture, expressing ideas academically, and checking LaTeX syntax. I used ChatGPT's web interface for translation, algorithm explanations, and discussions of review findings and project planning.

The review process required decisions about what the evidence could support. Claude-assisted review identified a missing premise in the English proof exposition and an incomplete diagnostic table. I incorporated these findings into the revision process while distinguishing corrections to the exposition from changes to the implementation. The thesis reports that the measured tree configuration had higher per-input median runtimes than the list backend throughout the formal comparison. I accepted this outcome and maintained the requirement to report the observed results and their limitations accurately.

I cannot identify a specific task in this project that I believe would have been faster without AI. Nevertheless, checking suggestions, understanding unfamiliar concepts, and revising incomplete answers required effort. The omitted proof premise illustrates why fluent wording cannot establish that an argument is complete. Similarly, a successful test run supports a bounded claim about the tested cases; it does not establish a general correctness or complexity result. These distinctions remained important when assessing proposed explanations and revisions.

Overall, I am satisfied with the outcome. AI assistance helped me organize the work, explore technical questions, and express ideas more clearly. The experience reinforced the importance of clear questions, explicit acceptance criteria, and sufficient understanding to assess proposed changes. In future work, I would document my decisions and the reasons for accepting or rejecting suggestions more systematically, alongside the AI contributions themselves. This would make both my reasoning and the role of the tools easier to trace. Responsibility for understanding and defending the submitted work remains with me.

### 中文对照（供本人核对）

我的贡献主要在于明确研究要求，主导项目的开发与评估。我将高效后端确定为项目的核心要求，并使后续开发始终围绕这一要求推进。我要求实现从自身维护的状态恢复输出，并明确区分已实现的功能、有界测试、复杂度论证和实际性能测量。这些要求指导了对修改建议的评估及结果的呈现。

我使用 Codex、Claude 和 ChatGPT 获得技术与语言辅助。这些工具提供了实现建议、代码修改、证明表述和审阅发现。我负责沟通要求、安排优先级、请求解释，并决定推进哪些修订。遇到不熟悉的数据结构时，我会要求用具体例子说明 Jordan 算法、兄弟分组和红黑树之间的关系。尤其有帮助的用途包括查找文献、讨论项目架构、用学术语言表达想法，以及检查 LaTeX 语法。我使用 ChatGPT 网页版进行翻译、理解算法，并讨论审阅意见和项目规划。

审阅过程也需要判断证据能够支持什么。Claude 辅助审阅指出了英文证明表述中缺失的一个前提，以及一张不完整的诊断表。我将这些发现纳入修订过程，并区分表述修正和实现变化。论文报告了正式比较中的实际结果：被测树配置在每个输入上的耗时中位数都高于列表后端。我接受这一结果，并坚持准确报告观察结果及其限制。

我无法指出这个项目中哪个具体任务不用 AI 会更快。不过，检查建议、理解陌生概念和修改不完整回答仍需要投入精力。遗漏的证明前提说明，流畅的文字不能证明论证完整。同样，测试通过只能支持关于被测案例的有界结论，不能建立一般性的正确性或复杂度结论。这些区分始终是评估解释和修订建议时的重要依据。

总体上，我对成果满意。AI 辅助帮助我组织工作、探讨技术问题并更清楚地表达想法。这次经历强化了明确问题、设定验收标准，以及充分理解修改建议以便作出判断的重要性。在今后的工作中，我会更系统地记录自己的决策及接受或拒绝建议的理由，同时记录 AI 的具体贡献。这会使我的推理和工具的作用都更容易追溯。理解并解释所提交工作的责任仍由我承担。

## 五、时段、影响范围与正文标注的处理状态

1. **反思已并入，原文不变。** 本次不改变已获准的418词反思或其中文对照。
2. **使用时段已按证据限定。** Codex 的11–22 October 2026只是有记录的修订时段，
   不代表首次使用或完整周期；该限定已同步回PDF。Claude日期仍注明来自审稿人说明。
   ChatGPT准确日期不能从当前提供的材料恢复，本次未查看完整账号历史，不猜首次使用日期。
3. **建立可定位的影响范围。** [影响范围与标注方案](../thesis/ai_disclosure_scope_20261022.md)
   逐项列出摘要、正文相关章节、英文证明、反思和排版工作的具体辅助类型，保留版本、标签与证据入口。
   新英文表述、改写、英文转述/翻译和技术审阅分开记录；这不是整章AI创作或贡献比例结论。
   ChatGPT翻译的具体段落仍未能定位，清单不宣称覆盖全部历史。
4. **正文标注方案已准备，尚未确认或全面实施。** 方案采用总体清单加可定位段落的就地说明；
   章节/小节级说明只用于明确界定的连续修订，不能默认代替段落标注。
   已写好具体脚注候选和供导师确认的短说明，但没有代发，也没有假定导师已批准。
   当前已实施的反思语言辅助说明继续保留。
5. **正式定稿前仍需完成。** 本人应向导师确认格式与历史缺口的处理，再落实相应标注，
   核实允许的辅助范围及个人声明。学校提交手续和完整披露状态不由本次构建通过自动取得。

## 六、所依据的公开指引与复核边界

已核对 [FU 数学与计算机系考试办公室的 Informatik AI 使用指引](https://www.imp.fu-berlin.de/fbv/pruefungsbuero/Informationen-Anleitungen-FAQ/Informationen-und-Anleitungen/Handreichung-KI-Nutzung-Informatik.pdf)
（5 November 2025 版，22 October 2026 访问）。指引要求说明工具、时段、典型请求与回答、
采用方式及影响范围，并附约 400 词的个人反思；意译采用的 AI 段落应在原处标明。
具体补充要求由导师确定，不能用本清单推断所有既往用途均已获准。

关于审稿中提到的文献文件：此前的10月22日记录报告 GitHub 仓库为公开，
`docs/papers/` 中两篇 PDF 受版本管理；检查到的论文目录说明没有记载再分发许可。
这不等于证明不存在许可。不能仅凭工具读取过文件，就断言特定云服务配置不合规；
上传处理条件与公开再分发权限应分别核实。本次未重新查询公开状态，也没有删除文件或改写 Git 历史。

反思全文和详细证据索引在前一轮已完成整合。本次只更新附录B的时段及范围说明，
新增可追溯的影响范围表和标注方案，批准的反思文字、正文论证与实验结果均不改变。
重新构建与检查 PDF；不重新执行算法、资格、校准或正式测量。
原 PDF、封存记录及审阅 ZIP 均保留原身份。
