import fs from "node:fs/promises";
import { FileBlob, PresentationFile } from "@oai/artifact-tool";

const SOURCE = new URL("../../Jordan_Sorting_Progress_Report_ZH.pptx", import.meta.url);
const OUT = new URL(
  "../candidates/Jordan_Sorting_Progress_Report_ZH_midterm_candidate.pptx",
  import.meta.url,
);
const SCRIPT_OUT = new URL(
  "../candidates/Jordan_Sorting_Progress_Report_Speaker_Script_ZH_midterm.txt",
  import.meta.url,
);

const C = {
  navy: "#18324A",
  teal: "#187A84",
  coral: "#D36B4A",
  green: "#2E8B57",
  ink: "#243746",
  slate: "#5A6B78",
  line: "#CBD5DE",
  white: "#FFFFFF",
  paleBlue: "#EAF1F8",
  paleTeal: "#E8F4F3",
  paleCoral: "#FBEDE8",
};

const TIMES = {
  1: "0:50", 2: "0:55", 3: "0:50", 4: "0:50", 5: "0:45", 6: "1:10", 7: "1:30", 8: "1:40",
  9: "1:25", 10: "1:25", 11: "1:00", 12: "1:10", 13: "0:40", 14: "1:20", 15: "0:45", 16: "0:55",
};

const TITLES = {
  1: "Simplified Jordan Sorting 的可执行重构进展",
  2: "上一次汇报建立了静态结构基线",
  3: "上次汇报后的进展",
  4: "当前范围：有效输入排序",
  5: "三个问题连接重构、测量与解释",
  6: "Oracle、reference pipeline 与 paper core 承担不同角色",
  7: "Step 1/2/3 控制流与镜像方向",
  8: "Step 3(c) 使用几何极值，而非第二个存储端点",
  9: "奇数迭代需要单独的 z1 输出锚点修正",
  10: "Ownership 安全的拆分与转移",
  11: "实现检查与实验一致性",
  12: "正式实验将认证与 audit 保持在 paper 计时之外",
  13: "全部 60 个评估用例均返回正确输出",
  14: "Paper/reference 比值随五个测试规模下降",
  15: "当前证据说明了什么",
  16: "可能的下一步：finger-tree 后端",
  17: "备用 A：各规模的中位运行时间",
  18: "备用 B：Paper 输出来源",
  19: "备用 C：验证汇总",
  20: "备用 D：镜像后的局部选择",
  21: "备用 E：拟议的 finger-tree 后端边界",
};

const TALK = {
  1: `大家好。这次汇报介绍我的硕士论文进展，主题是 Simplified Jordan Sorting 的可执行重构。上次我主要讨论静态结构，包括 rank interval、upper 和 lower family、family tree，以及 oracle 支持的 reference implementation。此后的核心问题是，论文描述的动态过程能否在普通 Python list 上成为真正可执行、可检查，并能从自身状态恢复输出的实现。今天我会介绍重构中的关键决定、验证方法，以及在明确计时范围下得到的实验结果。`,
  2: `上一次实现已经把静态结构说明得比较清楚。它用 rank interval 表示输入，区分 upper 和 lower pair family，重构 laminar family tree，并计算结构指标。Oracle 用来确认输入和提供 reference output。但它还没有执行动态 Jordan-sorting procedure：没有持续维护 processed prefix，没有完成 sibling-list 的 split 和 ownership transfer，也没有从算法自己的状态恢复最终输出。因此，主要缺口是把结构描述转化为安全而明确的动态更新。`,
  3: `上次汇报之后，我集中完成了四项工作。第一，缩小范围，把有效输入排序、recognition 和理论后端主张分开。第二，实现 Step 1、Step 2 和 Step 3 的控制流。第三，加入 ownership 不变量、事务式更新、重放和有界验证。第四，在实现和验证边界稳定后，执行固定协议的正式实验。这些工作相互依赖，尤其是输出来源与状态检查明确之后，实验才有解释意义。当前成果是可执行的普通列表实现，历史论文中的专用后端仍属于未来工作。`,
  4: `随着实现逐渐明确，论文范围也有意收窄。当前研究的是 1990 年 sorting procedure 在 oracle 已认证有效的输入上如何运行。实验比较 Python sort、完整的 oracle-backed reference pipeline 和重构后的 paper core。Recognition 保持独立，不能从这次实验推断任意输入的识别能力。Paper core 也仍使用普通 Python list，而不是历史理论分析所需的专用后端。这个范围让论文可以集中回答一个具体问题：动态过程能否正确执行，并从自身维护状态恢复输出。Finger-tree 后端只是可能的扩展。`,
  5: `论文有三个研究问题。RQ1 问普通列表重构能否在认证后的有效输入上，从维护状态恢复正确排序。RQ2 问 paper call 相对于 Python sort 和完整 reference pipeline，在各自计时范围下呈现什么行为。RQ3 只探索输入结构、checked operation counter 与运行时间之间的描述性关系。RQ1 是主要技术问题，RQ2 报告测量结果，RQ3 不作因果解释。`,
  6: `Oracle、reference pipeline 和 paper core 的角色必须明确区分。Paper call 之前，oracle 只确认有效输入条件；调用之后，runner 才用 oracle 的排序结果作正确性比较。Reference pipeline 则有意消费完整 oracle result，包括 sorted output。Paper core 只接收原始 sequence 和已经成立的有效输入前提。它执行 Step 1、2、3，维护 partial order 与 sibling-list 状态，并从这些状态恢复输出。图中的虚线比较框位于 core 外部。两条路径面对同一个 expected answer，但输出来源不同。Oracle 排序结果不会进入 paper core，也不会决定它的返回值。`,
  7: `可执行重构采用统一的控制流。先排序 z1、z2、z3并初始化 partial order 与首批 upper、lower pair；随后每个新点都依次经过 Step 1、Step 2 和 Step 3。Step 1 计算 predecessor-side boundary A_i，Step 2 计算 successor-side boundary B_i。Step 3(a) 插入新 pair，Step 3(b) 在需要时拆分 sibling list 并转移 ownership，Step 3(c) 把新点插入维护的顺序。Increasing 与 decreasing 方向共享这些阶段，真正镜像的是 Step 3 对两个 boundary 的使用。1990 年论文直接描述 increasing case，decreasing case由对称性重构。几何端点和奇数索引 z1 输出锚点则是为了得到无歧义执行行为而明确补充的局部规则。`,
  8: `第一个关键问题是 Step 3(c) 应使用哪个端点。考虑有效前缀 3、2、1、4。Acquired pair P2 按 curve order 存为 3、2。如果机械地取第二个存储元素 2 作为锚点，插入 4 后得到 1、2、4、3，在 axis order 上是错误的。原因是 curve order 和 axis order 描述不同关系。Pair 的存储顺序来自曲线遍历，但 Step 3(c) 需要 x 轴上的几何极值。在这里正确端点是 3，把 4 插在 3 后得到 1、2、3、4。于是可执行规则选择几何极值，而不是固定选择第二个存储元素。Increasing 使用右端几何极值，decreasing 使用左端几何极值。我把它称为可执行化澄清，而不是直接归为 1990 年论文的原文规则。`,
  9: `第二个问题是奇数索引的 z1 特例。例子中的有效前缀为 1、2、3、4、6、7、0。当前是 decreasing iteration，普通几何锚点为 z2，也就是值 2。若直接把 0 插到 z2 前，会得到 1、0、2、3、4、6、7，z1 仍在新点错误的一侧。因为 0 小于 z1，且 z1 小于原锚点，所以输出锚点必须从 z2 改为 z1。这样插入后得到正确顺序 0、1、2、3、4、6、7。这个修正只影响输出插入，不替代 predecessor 或 successor boundary 的计算。二者分别决定 family update 的 pair 与 partial order 更新的点，代码也将它们分开记录。`,
  10: `正确插入还要求 ownership 一致。每个有限 pair 必须只有一个 parent 和一个 sibling-list owner。拆分前，原 owner 控制 retained 与 acquired 两部分；拆分后，原 owner 保留 retained segment，新 owner 接收 acquired segment。实现可能为两个非空侧都创建新的 sibling list，所以两侧的 list ID 都可能改变。但只有 acquired segment 改变 parent ownership。代码把 split 与 transfer 当作一个 transaction：保存受影响状态，执行更新，检查 split boundary、ownership 与局部后置条件；失败时恢复 registry、ownership link 与 list ID。普通列表使扫描、复制、切片和 ownership rebinding 都成为明确成本。这些检查保护正确性，但不提供历史线性时间分析所需的更新界。`,
  11: `实现层面使用四类主要检查。Focused regression case 覆盖已知边界；有界穷举验证覆盖 n 不超过 8 的 2,074 个 oracle-valid permutation；checked-state audit 检查 parent、ownership、sibling list 与恢复输出；确定性重放再次运行同一 core 并比较状态。重放检查一致性，不是第二套独立算法。另有一条实验验证路径确认保存结果与固定实验设置及重算汇总一致，详细合同放在 Backup C。这里的重点仍是算法状态。这些检查支持已评估用例，但不是对所有 Jordan sequence 的数学证明。`,
  12: `正式实验覆盖 5 个规模，每个规模 12 个 exact case，并比较 3 个算法。每个 case-algorithm cell 先做 5 次 warm-up，再做 20 次 measured call，因此得到 3,600 条记录。这 20 次是同一个 exact case 的重复调用，不是 20 个独立输入；每次调用会获得包含相同值的 fresh list。调度会轮转算法位置。对 paper algorithm，oracle certification 与 checked-state audit 在计时前完成，minimal paper call 位于计时内，其中包括从维护顺序恢复输出。返回值比较发生在计时后。Python 与 reference 的计时范围也各自不同，因此 paper/reference 只能作为 pipeline-scope 比值，不能解释为同口径端到端加速。`,
  13: `全部 60 个评估用例都通过认证与 case-level checked-state audit。每次 measured call 都返回 expected output，正式运行没有记录正确性错误。实验是每个 exact case 做一次 audit；3,600 条 timing row 携带对应的 case-level audit 结果，并不表示执行了 3,600 次独立 audit。这些结果只支持本次测试的有效用例，不评估任意输入 recognition，也不是对全部 Jordan sequence 的证明。`,
  14: `主要运行时间模式是 paper/reference 比值随五个测试规模下降。比值先在每个 exact case 内计算，再让每个 case 在规模中位数中具有相同权重。它从 n 等于 32 时的 3.226，降到 64 时的 2.202、128 时的 1.351，并在 256 时低于 1，达到 0.851；在 512 时为 0.567。观测到的 crossover 位于 128 和 256 之间。Pilot 也呈现相同下降方向，但两次运行的绝对时间不会合并。由于 paper 与 reference 的计时范围不同，这个趋势不是一般性能加速，也不能用五个规模推断渐近行为。`,
  15: `当前证据支持两类主要结论：普通列表重构可以执行，并从自身维护状态恢复输出；在测试的有效用例和固定计时范围下，记录到了正确输出与明确的运行时间趋势。主要限制也同样明确：普通 Python list 不构成线性时间实现，五个规模不能确定渐近复杂度。此外，本实验没有评估 recognition，paper 与 reference 也采用不同计时范围。因此这些数值只是固定条件下的运行时间观测。`,
  16: `一个可能的下一步是在保持 Step 1、Step 2 和 Step 3 语义不变的前提下研究 finger-tree 后端。普通列表实现提供了经过测试的参照点，详细的接口与 ownership-transfer 难点放在 Backup E。我希望向导师确认两个问题：第一，应专门实现历史 heterogeneous finger tree，还是实现支持所需列表操作的等价后端？第二，论文只做语义等价和实验比较是否足够，还是还应给出 amortized operation-bound 论证？这个选择决定扩展主要是实验性工作，还是还需要证明层面的内容。`,
  17: `如果需要查看绝对时间，这一页列出三个算法在五个规模上的 median call time。数值来自一次 Apple M4、CPython 3.12.4 的执行，不能推广到其他环境。对数坐标只是为了让 Python sort 与另外两条 pipeline 同时可见。`,
  18: `这页直接回答输出来源问题。Reference pipeline 返回 oracle_result 中的 sorted output；paper core 返回 state.partial_order.to_list。认证发生在 paper call 之前，比较发生在调用之后，因此二者都不会向 paper core 提供返回值。`,
  19: `这页汇总有界验证证据，包括仓库测试、n 不超过 8 的有效排列穷举、固定生成用例、正式 case-level checked-state audit，以及通过 evidence-contract validation 的实验输出。这些检查互相补充，但都不是普遍性证明。`,
  20: `这张表汇总镜像后的局部选择。Step 1 始终计算 predecessor-side boundary A_i，Step 2 始终计算 successor-side boundary B_i。镜像发生在 Step 3 如何使用这些 boundary，以及 split side、extreme child 与几何端点的选择上。`,
  21: `拟议结构把 Step 1、Step 2 和 Step 3 放在一个小型 sibling-list 接口之上。普通列表后端保留为当前参照，finger-tree 后端实现相同语义操作。具体目标是历史 heterogeneous finger tree，还是具有等价操作界的后端，仍需与导师确认。主要风险是，高效 tree split 本身不够；若 ownership transfer 仍逐项扫描并重新绑定，就无法得到历史分析所需的操作界。第一步应先保证语义等价与 differential correctness，任何复杂度主张都需要独立的证明论证。`,
};

const SOURCES = {
  1: ["thesis/frontmatter/abstract.tex", "thesis/chapters/introduction.tex", "thesis/figures/jordan_sorting_problem.pdf"],
  2: ["thesis/chapters/background.tex", "thesis/chapters/implementation.tex", "Hoffmann et al. (1986), doi:10.1016/S0019-9958(86)80033-X", "Fung et al. (1990), doi:10.1016/0020-0190(90)90111-A"],
  3: ["thesis/chapters/introduction.tex", "thesis/chapters/implementation.tex", "thesis/chapters/methodology.tex"],
  4: ["thesis/chapters/introduction.tex", "thesis/chapters/limitations.tex", "thesis/chapters/methodology.tex", "Supervisor feedback, September 2026"],
  5: ["thesis/chapters/introduction.tex"],
  6: ["thesis/chapters/implementation.tex", "thesis/chapters/methodology.tex", "src/paper_jordan.py", "src/simplified_jordan.py"],
  7: ["thesis/chapters/algorithm.tex", "thesis/chapters/implementation.tex", "Fung et al. (1990), doi:10.1016/0020-0190(90)90111-A"],
  8: ["thesis/chapters/algorithm.tex", "src/paper_jordan.py"],
  9: ["thesis/chapters/algorithm.tex", "thesis/figures/step3c_anchor_z1_anomaly.pdf", "Hoffmann et al. (1986), p. 175, doi:10.1016/S0019-9958(86)80033-X"],
  10: ["thesis/chapters/implementation.tex", "thesis/figures/family_sibling_structure.pdf", "src/paper_jordan.py"],
  11: ["thesis/chapters/implementation.tex", "thesis/chapters/methodology.tex", "docs/thesis/latex_final_audit.md", "experiments/validate_week12_formal_sorting_outputs.py"],
  12: ["thesis/chapters/methodology.tex", "thesis/figures/formal_experiment_pipeline.pdf", "results/runs/week12_formal_sorting_v1__run001/config.json", "results/runs/week12_formal_sorting_v1__run001/manifest.json"],
  13: ["thesis/chapters/results.tex", "results/runs/week12_formal_sorting_v1__run001/raw.csv", "results/runs/week12_formal_sorting_v1__run001/case_audit.csv", "results/runs/week12_formal_sorting_v1__run001/validation_report.json"],
  14: ["thesis/chapters/results.tex", "results/runs/week12_formal_sorting_v1__run001/case_summary.csv", "docs/analysis/week12_runtime_ratios.csv"],
  15: ["thesis/chapters/limitations.tex", "thesis/chapters/conclusion.tex", "Supervisor feedback, September 2026"],
  16: ["thesis/chapters/implementation.tex", "thesis/chapters/limitations.tex", "thesis/README.md", "Fung et al. (1990), doi:10.1016/0020-0190(90)90111-A", "Supervisor feedback, September 2026"],
  17: ["thesis/chapters/results.tex", "results/runs/week12_formal_sorting_v1__run001/case_summary.csv"],
  18: ["thesis/chapters/implementation.tex", "src/paper_jordan.py", "src/simplified_jordan.py"],
  19: ["docs/thesis/latex_final_audit.md", "experiments/validate_paper_algorithm.py", "results/runs/week12_formal_sorting_v1__run001/validation_report.json"],
  20: ["thesis/chapters/algorithm.tex", "thesis/chapters/implementation.tex", "Fung et al. (1990), doi:10.1016/0020-0190(90)90111-A"],
  21: ["thesis/chapters/implementation.tex", "thesis/chapters/limitations.tex", "Fung et al. (1990), doi:10.1016/0020-0190(90)90111-A", "Supervisor feedback, September 2026"],
};

function addText(slide, text, x, y, width, height, options = {}) {
  const shape = slide.shapes.add({
    geometry: "textbox",
    position: { left: x, top: y, width, height },
    fill: "none",
    line: { style: "solid", fill: "none", width: 0 },
  });
  shape.text = text;
  shape.text.style = {
    fontSize: options.fontSize ?? 20,
    bold: options.bold ?? false,
    color: options.color ?? C.ink,
    alignment: options.align ?? "left",
    verticalAlignment: options.valign ?? "top",
    autoFit: "shrinkText",
    wrap: "square",
    lineSpacing: options.lineSpacing ?? 1.05,
    insets: options.insets ?? { left: 4, right: 4, top: 2, bottom: 2 },
  };
  return shape;
}

function addBox(slide, x, y, width, height, options = {}) {
  return slide.shapes.add({
    geometry: options.geometry ?? "roundRect",
    position: { left: x, top: y, width, height },
    fill: options.fill ?? C.white,
    line: { style: "solid", fill: options.line ?? C.line, width: options.lineWidth ?? 1.2 },
    borderRadius: options.radius ?? 8,
  });
}

function addRule(slide, x, y, width, color = C.line, weight = 2) {
  return slide.shapes.add({
    geometry: "line",
    position: { left: x, top: y, width, height: 1 },
    fill: "none",
    line: { style: "solid", fill: color, width: weight },
  });
}

function addBulletList(slide, items, x, y, width, options = {}) {
  const gap = options.gap ?? 46;
  items.forEach((item, index) => {
    const top = y + index * gap;
    slide.shapes.add({
      geometry: "ellipse",
      position: { left: x, top: top + 8, width: 10, height: 10 },
      fill: options.bulletColor ?? C.teal,
      line: { style: "solid", fill: options.bulletColor ?? C.teal, width: 0 },
    });
    addText(slide, item, x + 22, top, width - 22, gap - 2, {
      fontSize: options.fontSize ?? 20,
      color: options.color ?? C.ink,
      valign: "middle",
      lineSpacing: 1,
    });
  });
}

function replaceText(presentation, id, text) {
  presentation.resolve(id).text = text;
}

function deleteShapes(presentation, ids) {
  ids.forEach((id) => presentation.resolve(id).delete());
}

function setNotes(slide, slideNumber) {
  slide.speakerNotes.textFrame.setText(
    `${TALK[slideNumber]}\n\n[Sources]\n${SOURCES[slideNumber].map((source) => `- ${source}`).join("\n")}`,
  );
  slide.speakerNotes.setVisible(true);
}

async function main() {
  const presentation = await PresentationFile.importPptx(await FileBlob.load(SOURCE.pathname));

  replaceText(presentation, "sh/cza94vmx", "上次汇报后的进展");
  replaceText(presentation, "sh/m1c3mlsn", "区分有效输入排序、识别问题与理论后端边界");
  replaceText(presentation, "sh/tgry9ofu", "当前成果：可执行的普通列表实现；历史专用后端仍属于未来工作。");

  replaceText(presentation, "sh/1cj2d8b6", "当前范围：有效输入排序");
  replaceText(presentation, "sh/tsrqlc7u", "当前实现使用普通列表");
  replaceText(presentation, "sh/sri9s7q9", "实验评估普通列表实现；finger-tree 后端仍只是可能的扩展。");

  replaceText(presentation, "sh/cb2tkvap", "Step 1/2/3 控制流与镜像方向");
  presentation.resolve("sh/kra50jqh").delete();

  replaceText(presentation, "sh/xc3mho32", "Ownership 安全的拆分与转移");
  replaceText(presentation, "sh/1o3ahwvq", "只有 acquired 的非空片段改变 parent ownership。");

  replaceText(presentation, "sh/b6d4f2lc", "5 个规模  ×  12 个用例  ×  3 个算法  ×  20 次重复调用");
  replaceText(presentation, "sh/7epczitg", "Reference 计时包含完整 oracle-backed pipeline。Python 计时覆盖完整排序调用。");
  replaceText(presentation, "sh/q5c7m5wb", "Paper 与 reference 使用不同计时范围，因此该比值不是端到端加速。");

  const slide11 = presentation.resolve("sl/jetc3ut0");
  replaceText(presentation, "sh/xcryxg7y", "实现检查与实验一致性");
  deleteShapes(presentation, [
    "sh/o7ih0r6h", "sh/72t03qp0", "sh/61kzalof", "sh/ofqtgnyt", "sh/9gza9sze", "sh/mdobedg3",
    "sh/nehs7iho", "sh/0b6tc3yx", "sh/1cfa58zi", "sh/epobatgr", "sh/zaxs3yhc", "sh/cn6t83y1",
    "sh/dofa18z6", "sh/tsnip0ny", "sh/87ehgv6d", "sh/7650nq5s", "sh/65wzelo7", "sh/l43ilgn2",
    "sh/k3uhcb6h", "sh/j2lgjq5w", "sh/y1czalob", "sh/p07ixkn6", "sh/4zyhofml", "sh/m58fih43",
    "sh/n61wbmlo",
  ]);
  addText(slide11, "实现与状态验证", 92, 158, 450, 28, { fontSize: 15, bold: true, color: C.teal });
  addText(slide11, "实验输出检查", 728, 158, 450, 28, { fontSize: 15, bold: true, color: C.coral });
  const checks = ["重点回归用例", "有界穷举验证\n2,074 个 oracle-valid 排列，n ≤ 8", "checked-state audit", "同一 core 的确定性重放"];
  const ys = [202, 294, 402, 494];
  checks.forEach((check, index) => {
    addBox(slide11, 88, ys[index], 470, index === 1 ? 82 : 64, { fill: C.paleTeal, line: C.teal, radius: 7 });
    addText(slide11, check, 104, ys[index] + 8, 438, index === 1 ? 66 : 48, {
      fontSize: index === 1 ? 18 : 20,
      bold: index === 1,
      color: C.ink,
      align: "center",
      valign: "middle",
    });
    if (index < 3) {
      addText(slide11, "↓", 286, ys[index] + (index === 1 ? 79 : 61), 72, 28, { fontSize: 26, bold: true, color: C.teal, align: "center" });
    }
  });
  addBox(slide11, 722, 232, 470, 250, { fill: C.paleCoral, line: C.coral, lineWidth: 1.5, radius: 8 });
  addText(slide11, "另一条验证路径确认保存的输出与固定实验设置及重算汇总一致。", 758, 282, 398, 142, { fontSize: 23, bold: true, color: C.ink, align: "center", valign: "middle" });
  addText(slide11, "完整一致性检查：见备用 C", 760, 506, 394, 34, { fontSize: 17, color: C.slate, align: "center", valign: "middle" });
  addText(slide11, "这些检查支持已评估用例，但不是对全部 Jordan sequence 的证明。", 140, 610, 1000, 40, { fontSize: 21, bold: true, color: C.navy, align: "center", valign: "middle" });

  const slide13 = presentation.resolve("sl/hgzapcr6");
  replaceText(presentation, "sh/q50nydsj", "全部 60 个评估用例均返回正确输出");
  deleteShapes(presentation, [
    "sh/32ponyts", "sh/gzy5s3a1", "sh/1076lobm", "sh/hcfy9k3u", "sh/gb6x0zm9", "sh/vaxg7ulo",
    "sh/u9ofyp43", "sh/t8fy5k3i", "sh/876xwfmx", "sh/7mdg3als", "sh/6l4fu547", "sh/lkvy103m", "sh/kjmxsfm1",
  ]);
  addText(slide13, "60", 130, 176, 410, 100, { fontSize: 72, bold: true, color: C.teal, align: "center", valign: "middle" });
  addText(slide13, "exact cases", 130, 278, 410, 46, { fontSize: 26, bold: true, color: C.navy, align: "center", valign: "middle" });
  addText(slide13, "0", 740, 176, 410, 100, { fontSize: 72, bold: true, color: C.green, align: "center", valign: "middle" });
  addText(slide13, "记录的正确性错误", 740, 278, 410, 46, { fontSize: 26, bold: true, color: C.navy, align: "center", valign: "middle" });
  addRule(slide13, 76, 354, 1128, C.line, 2);
  addText(slide13, "每个用例均在计时前完成 oracle 认证和一次检查。", 160, 382, 960, 56, { fontSize: 29, bold: true, color: C.navy, align: "center", valign: "middle" });
  addBox(slide13, 166, 474, 948, 92, { fill: C.paleBlue, line: C.navy, lineWidth: 1.5, radius: 8 });
  addText(slide13, "3,600 条计时记录携带对应的 case-level audit 结果。", 194, 492, 892, 56, { fontSize: 22, color: C.ink, align: "center", valign: "middle" });
  addText(slide13, "这些结果仅覆盖本次测试的有效用例。", 156, 606, 968, 36, { fontSize: 20, bold: true, color: C.coral, align: "center", valign: "middle" });

  const slide15 = presentation.resolve("sl/vaxsvy10");
  replaceText(presentation, "sh/547mhg3m", "当前证据说明了什么");
  deleteShapes(presentation, [
    "sh/s7y5sv2x", "sh/na5476l8", "sh/m9c3e1kn", "sh/wrm9kvep", "sh/hsvat0fa", "sh/upkrilwj",
    "sh/vqdsrqx4", "sh/4vm9ovel", "sh/5wvax0f6", "sh/it4rm5wv", "sh/judsvqxg", "sh/0z29cbyh",
    "sh/l0bqlgf2", "sh/1kjyt83e", "sh/gjax03m9", "sh/fi1grylo", "sh/ehsfyt43", "sh/p8jyx83q",
    "sh/o7ah4nm5", "sh/361gvilk", "sh/25sf2d4z", "sh/dc3y1s3m",
  ]);
  addBox(slide15, 78, 152, 536, 404, { fill: C.paleTeal, line: C.teal, lineWidth: 2, radius: 8 });
  addBox(slide15, 666, 152, 536, 404, { fill: C.paleCoral, line: C.coral, lineWidth: 2, radius: 8 });
  addText(slide15, "当前结果", 106, 178, 480, 52, { fontSize: 26, bold: true, color: C.teal, align: "center", valign: "middle" });
  addText(slide15, "主要限制", 694, 178, 480, 52, { fontSize: 26, bold: true, color: C.coral, align: "center", valign: "middle" });
  addBulletList(slide15, ["可执行重构从维护状态恢复输出", "在已评估用例中得到正确输出与固定范围的运行时间趋势"], 112, 270, 456, { fontSize: 22, gap: 132, bulletColor: C.teal });
  addBulletList(slide15, ["普通列表不能证明线性时间实现", "五个测试规模不能确定渐近复杂度"], 700, 270, 456, { fontSize: 22, gap: 132, bulletColor: C.coral });
  addText(slide15, "未评估 recognition；paper 与 reference 使用不同计时范围。", 150, 600, 980, 40, { fontSize: 20, bold: true, color: C.navy, align: "center", valign: "middle" });

  const slide16 = presentation.resolve("sl/gny5sjyp");
  replaceText(presentation, "sh/tcbmdcre", "下一步");
  replaceText(presentation, "sh/8z2h8bq1", "可能的下一步：finger-tree 后端");
  deleteShapes(presentation, [
    "sh/lwbyxwra", "sh/ip4zel83", "sh/3qdg7qpo", "sh/fm1gzq5o", "sh/e1sf65o3", "sh/1ojy10ne",
    "sh/gnax8v6t", "sh/nqlg3a5k", "sh/2pcfa5oz", "sh/ps3y5knq", "sh/oruhcf65", "sh/bulg7u5g",
    "sh/atczepob", "sh/mpgj6t8j", "sh/7qp0zepo", "sh/8by18jq9", "sh/9c7i1o7u", "sh/ylwj2987",
    "sh/lo7ixo7y", "sh/ih0jedob", "sh/ji9k7ypw", "sh/sb2l47at",
  ]);
  addText(slide16, "普通列表实现提供了经过测试的参照点。", 112, 156, 1056, 54, { fontSize: 28, bold: true, color: C.navy, align: "center", valign: "middle" });
  addBox(slide16, 172, 244, 936, 100, { fill: C.paleTeal, line: C.teal, lineWidth: 1.5, radius: 8 });
  addText(slide16, "新后端保持相同的 Step 1/2/3 行为，只替换 sibling-list 操作。", 204, 268, 872, 54, { fontSize: 24, color: C.ink, align: "center", valign: "middle" });
  addText(slide16, "与导师讨论", 112, 402, 1056, 38, { fontSize: 25, bold: true, color: C.teal, align: "center", valign: "middle" });
  addBox(slide16, 112, 456, 1056, 162, { fill: C.navy, line: C.navy, radius: 8 });
  addText(slide16, "1. 应实现历史 heterogeneous finger tree，还是具有所需操作的等价后端？\n2. 论文只做语义与实验评估，还是还要给出 amortized operation-bound 论证？", 154, 476, 972, 122, { fontSize: 24, color: C.white, valign: "middle" });

  presentation.slides.items.forEach((slide, index) => setNotes(slide, index + 1));

  const pptx = await PresentationFile.exportPptx(presentation);
  await pptx.save(OUT.pathname);

  const main = Array.from({ length: 16 }, (_, index) => {
    const slideNumber = index + 1;
    return [`第 ${slideNumber} 页 | 建议 ${TIMES[slideNumber]}`, TITLES[slideNumber], "", TALK[slideNumber]].join("\n");
  }).join("\n\n============================================================\n\n");
  const qa = Array.from({ length: 5 }, (_, index) => {
    const slideNumber = index + 17;
    return [`第 ${slideNumber} 页 | 问答备用`, TITLES[slideNumber], "", TALK[slideNumber]].join("\n");
  }).join("\n\n------------------------------------------------------------\n\n");
  const document = [
    "JORDAN SORTING 硕士论文进度汇报",
    "中文逐页参考讲稿",
    "",
    "对应文件：Jordan_Sorting_Progress_Report_ZH.pptx",
    "主讲范围：第 1-16 页",
    "目标时长：18.5-20 分钟",
    "说明：本稿用于中文理解、演练和内容核对，并已同步写入中文版演示稿的 speaker notes。",
    "",
    "============================================================",
    "主报告：第 1-16 页",
    "============================================================",
    "",
    main,
    "",
    "============================================================",
    "问答备用页：第 17-21 页",
    "============================================================",
    "",
    qa,
    "",
  ].join("\n");
  await fs.writeFile(SCRIPT_OUT, document, "utf8");
  console.log(`Wrote ${OUT.pathname}`);
  console.log(`Wrote ${SCRIPT_OUT.pathname}`);
}

main().catch((error) => {
  console.error(error?.stack ?? String(error));
  process.exitCode = 1;
});
