# AI 使用说明与个人反思（作者核对稿，措辞修订版）

更新：2026-10-22。修订基线：`160a0fa3180f164b7a451f64484ed821fc164206`。

本次将写作辅助概括为“框架建议和翻译辅助”，并具体说明学术措辞与 LaTeX 语法检查。
不使用“大部分由 AI 起草”等没有依据的数量判断。技术和审阅辅助另列，
不把写作方面的概括当成全部 AI 使用范围。前版记录及其清单保持原样。

本稿依据作者本日补充、已保存的修订材料和所提供的 Claude 审阅说明整理。
研究由作者主导，AI 作为辅助工具。按具体活动记录辅助范围，不估算贡献比例，
也不依据提交者姓名或工具执行次数推断作者在会话之外完成的工作。
这是一份供作者检查、随后纳入论文的草稿，不是已签署的独立性声明。
10 月 20 日审阅包中的旧记录保持原样，本稿不改变旧包的身份或清单。

## 一、作者本日确认的事实

- 使用的工具包括 Codex、Claude 和 ChatGPT 网页版。
- ChatGPT 网页版主要用于翻译；没有据此添加 DeepL、Google 翻译等未经确认的工具。
- 最有帮助的用途：查找文献、帮助建立项目架构、将通俗表述转成学术语言，
  以及检查和修正 LaTeX 语法错误。
- 作者注意到 AI 建议可能遗漏算法步骤，希望采用项目中可核对的具体例子。
- 作者对最终成果满意；目前没有明确认为不用 AI 会更快的环节。

后两点的写法必须保留边界：下文以有记录的**证明前提遗漏**作为具体例子，
不把它改写成一次已经证实的生产算法漏步事故。也不编造“手工更快”的个人经历。

## 二、Dokumentation der KI-Nutzung / 工具与用途

| Tool | Provider / version | Period supported by current information | Assistance and affected work |
| --- | --- | --- | --- |
| Codex desktop | OpenAI; session-specific model versions not fully documented | Recorded revision work: 11–22 October 2026; this is not a claim about the first-ever use | Writing support: outline and structure suggestions, translation, academic wording, and LaTeX syntax/build troubleshooting. Technical support: literature search and project-architecture discussion; code and test changes; experiment and validation tooling; execution and inspection of checks; proof-exposition revision and correction. This reflection was organized and translated from the author's Chinese answers. |
| Claude | Anthropic; exact serving model not independently verified | Reviewer-reported reviews on 17 and 20 October 2026, and disclosure discussion on 22 October | Technical and manuscript review, including proof premises, access-hook overhead, table coverage and interpretation; reviewer-supplied diagnostic/stress scripts and test reports. These reports are distinguished from locally reproduced evidence. |
| ChatGPT web interface | OpenAI; model version not specified by the author | Used during thesis preparation; exact dates remain to be supplied | Mainly translation, as confirmed by the author on 22 October. The exact passages and extent remain to be identified from the author's history. |

模型备注：所提供的 Claude 说明自报配置标签为 `claude-opus-5-5`，并同时说明
实际服务模型可能不同。因此该标签不作为已核实型号写入工具表。
版本信息缺失时不猜测；翻译和 LaTeX 检查也不应掩盖已记录的代码、实验工具和论证表述辅助。

## 三、代表性请求、产出和采用方式

以下保留可核对的请求摘录与产出摘录。它们不是完整聊天转录；概括的响应明确标为概括。
外部审阅指出问题、Codex 执行修订、作者决定采用是不同环节，不合并成作者亲自执行了全部检查。

### 示例 1：完整展示诊断结果

- **来源：** 作者转交的第二轮审稿意见，随后在 Codex 中处理。
- **请求摘录：** “表 6.5 改为 15 行全列，或按 n × 层级列 15 格。”
- **Codex 辅助产出摘录（生成的论文文本，不是聊天原话）：**
  “Four of fifteen cases, the large heavy constructions, favor the hook-free
  tree; the remaining eleven take 1.09–1.68 times the list time.”
- **如何采用：** 从已保存的原始批次重建全部十五行，修改结果表、摘要和结论，
  保留四例更快、十一例仍较慢的结果；没有删除不利数据或重新计时。
- **对应证据：** [结果章](../../thesis/chapters/results.tex)、
  [本地补充重建报告](../validation/thesis_review_round2_20261020/local_supplement_recheck.json)。

### 示例 2：补回 locality 论证的适用前提

- **来源：** 作者转交的同一轮审稿意见，随后在 Codex 中处理。
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
- **响应：** 下节英文草稿及中文对照。草稿保留“目前没有明确的手工更快案例”，
  用已归档的证明遗漏说明局限，没有虚构算法事故或个人经历。
- **采用状态：** 待作者逐句核对和修改；尚未作为本人已确认的反思并入冻结 PDF。
  本次组织、翻译和语言修订本身计入 Codex 的使用范围。

## 四、Reflexion der KI-Nutzung / 英文个人反思草稿

> Draft prepared with Codex from the author's Chinese account on 22 October
> 2026 and documented project examples. The author should check that the
> wording reflects their own experience before adopting it.

I used AI tools as assistants while directing the research and deciding how the project should develop. Their most helpful contributions were finding relevant literature, discussing the project architecture, and turning my informal explanations into academic language. ChatGPT's web interface mainly supported translation. Assistance with LaTeX syntax errors was also useful: it made technical writing more convenient and helped me resolve presentation problems while continuing to work on the content. These uses supported my work, but did not determine which research claims I should accept.

AI assistance helped connect different parts of the project. Discussions could move from an algorithmic requirement to its implementation, tests, and explanation in the thesis. Suggestions also offered alternative ways to organize material that I initially expressed in everyday language. However, a clear explanation or a successful compilation was not evidence that an argument was complete. Literature suggestions, implementation changes, and proof formulations still required checks against their sources and the project's actual behaviour.

One documented example is the missing bracketing premise in the English explanation of the dummy outer-gap case. The revision restored the condition from Fung's lemma and explained why it leaves a free group slot. This was an omission in the proof exposition, not evidence of a failed sorting run. It illustrates the concern I raised about AI overlooking a necessary step or condition. The diagnostic table provided another lesson: showing all fifteen cases made clear that only four favoured the hook-free tree, while eleven remained slower than the list. Critical checking matters even when individual sentences or numbers appear plausible.

I cannot identify a specific part of this project that I believe would have been faster without AI. Checking suggestions and revising incomplete answers nevertheless took time, so convenience should not be confused with automatic time savings in every task. My experience was most positive when the task was concrete and the proposed result could be checked, for example against a source passage, a recorded result, or a LaTeX build. This suggests a useful distinction between receiving a suggestion and having sufficient grounds to adopt it.

Overall, I am satisfied with the outcome. The assistance was particularly valuable for literature discovery, organizing the project, and expressing technical ideas. The experience also reinforced the need to keep my own judgement active: I must understand the claims, decide what belongs in the thesis, and take responsibility for the submitted work. The final account should preserve limitations and corrections as well as successful results.

### 中文对照（供本人核对）

我把 AI 作为辅助工具，同时由我主导研究并决定项目的发展方向。对我最有帮助的是
寻找相关文献、讨论项目架构，以及把我较通俗的解释转化为学术表述。
ChatGPT 网页版主要帮助翻译。检查 LaTeX 语法错误也很有用，让技术写作更方便，
帮助我在继续处理内容时解决排版和表达形式上的问题。这些辅助支持了我的工作，
但不替我决定哪些研究主张应该被接受。

AI 辅助让项目各部分更容易衔接：讨论可以从算法要求延伸到实现、测试和论文说明，
也能为组织我最初用日常语言表达的材料提供不同建议。不过，文字清楚或者编译成功，
都不能证明论证完整。文献建议、代码修改和证明表述仍需要对照来源及项目实际行为检查。

一个有记录的例子，是 dummy 外侧间隙的英文论证漏掉了夹住前提。修订补回了
Fung 引理中的条件，并解释了它为何保证一个空闲分组槽。这是证明表述的遗漏，
不是排序运行失败的证据，也体现了我对 AI 可能漏掉必要步骤或条件的担心。
诊断表是另一个例子：列出全部十五例后，可以清楚看出，只有四例中去掉访问钩子的树更快，
其余十一例仍慢于列表。即使单个句子或数字看起来可信，也需要批判性检查。

目前，我无法指出这个项目中哪个具体环节不用 AI 会更快。不过，核对建议和修改
不完整回答也需要时间，因此不能把方便理解成每个任务都会自动节省时间。
任务明确、结果可以与文献原文、保存的实验结果或 LaTeX 构建核对时，我的使用体验最好。
这也提示我，要区分“收到一个建议”和“已有充分依据采用这个建议”。

总体上，我对成果满意。辅助在寻找文献、组织项目和表达技术思想方面尤其有价值。
这次经历也提醒我保持自己的判断：我必须理解主张、决定哪些内容应进入论文，
并对提交的工作负责。最终叙述应同时保留限制、修正和成功结果。

## 五、入稿前仍需完成的具体事项

1. **本人核对反思。** 特别是“任务明确时体验最好”等归纳性表述，若不符合真实感受，应修改或删除。
   草稿中的案例来自项目记录；不声称作者亲自执行了每一次工具调用或测试。
2. **补齐 ChatGPT 时段与受影响段落。** 不依据本日确认日期推断首次使用时间，
   也不把未知翻译范围写成全部论文。
3. **落实正文对应标注。** 确定实际采用的 AI 生成或改写段落，再按适用要求直接标注。
   本记录不能代替逐处核对；也不将整章笼统标为 AI 创作。
4. **确认导师具体要求。** 已检查公开指引，但尚无导师关于范围、示例数量或格式的具体说明。
   既有代码的作者来源与允许的代码辅助条件，须依据真实工作记录确认，不能靠 Git 提交者身份代替。
5. **个人声明。** 正式信息和签署由本人完成。本次草稿不宣称学校提交手续或全部合规审查已完成。

## 六、所依据的公开指引与复核边界

已核对 [FU 数学与计算机系考试办公室的 Informatik AI 使用指引](https://www.imp.fu-berlin.de/fbv/pruefungsbuero/Informationen-Anleitungen-FAQ/Informationen-und-Anleitungen/Handreichung-KI-Nutzung-Informatik.pdf)
（5 November 2025 版，22 October 2026 访问）。指引要求说明工具、时段、典型请求与回答、
采用方式及影响范围，并附约 400 词的个人反思；意译采用的 AI 段落应在原处标明。
具体补充要求由导师确定，不能用本清单推断所有既往用途均已获准。

关于审稿中提到的文献文件：本轮查询确认 GitHub 仓库为公开，
`docs/papers/` 中两篇 PDF 受版本管理；检查到的论文目录说明没有记载再分发许可。
这不等于证明不存在许可。不能仅凭工具读取过文件，就断言特定云服务配置不合规；
上传处理条件与公开再分发权限应分别核实。本轮没有删除文件或改写 Git 历史。

本次修订使用说明的措辞并同步论文附录；个人反思仍为待本人确认的草稿，
尚未并入 PDF。重新构建论文以检查措辞调整后的排版，不重新执行算法、资格、校准或正式测量。
原 PDF、封存记录及审阅 ZIP 均保留原身份。
