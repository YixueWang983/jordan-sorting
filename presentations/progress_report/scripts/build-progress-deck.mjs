import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { Presentation, PresentationFile } from "@oai/artifact-tool";

const SCRIPT_DIR = path.dirname(fileURLToPath(import.meta.url));
const PRESENTATION_DIR = process.env.PRESENTATION_DIR
  ? path.resolve(process.env.PRESENTATION_DIR)
  : path.resolve(SCRIPT_DIR, "..");
const REPO = process.env.REPO_ROOT
  ? path.resolve(process.env.REPO_ROOT)
  : path.resolve(PRESENTATION_DIR, "../..");
const BUILD = path.join(PRESENTATION_DIR, "build");
const OUT = process.env.PRESENTATION_OUT
  ? path.resolve(process.env.PRESENTATION_OUT)
  : path.join(PRESENTATION_DIR, "Jordan_Sorting_Progress_Report.pptx");
const SCRIPT_OUT = process.env.SCRIPT_OUT
  ? path.resolve(process.env.SCRIPT_OUT)
  : path.join(PRESENTATION_DIR, "Jordan_Sorting_Progress_Report_Speaker_Script.txt");

const W = 1280;
const H = 720;
const C = {
  navy: "#102A43",
  teal: "#2A9D8F",
  coral: "#E76F51",
  slate: "#52606D",
  ink: "#243B53",
  muted: "#7B8794",
  light: "#F7FAFC",
  paleTeal: "#E8F5F3",
  paleCoral: "#FCEEEA",
  paleBlue: "#EAF1F8",
  white: "#FFFFFF",
  line: "#D9E2EC",
  green: "#1F8A70",
};

const ASSET = {
  jordan: `${PRESENTATION_DIR}/assets/jordan_sorting_problem.png`,
  family: `${PRESENTATION_DIR}/assets/family_sibling_structure.png`,
  z1: `${PRESENTATION_DIR}/assets/step3c_anchor_z1_anomaly.png`,
  pipeline: `${PRESENTATION_DIR}/assets/formal_experiment_pipeline.png`,
};

const TALK = {
  1: `Good afternoon. This presentation updates my master's thesis on an executable reconstruction of Simplified Jordan Sorting using ordinary Python lists. The input gives the intersection points in curve order. The task is to recover their order along the x-axis. My previous report focused on static structure: rank intervals, upper and lower pair families, family trees, and an oracle-backed reference. The main question is whether the paper's dynamic procedure can maintain its own state and recover its own output. I will focus on two reconstruction decisions, then explain the validation checks and the runtime results from the formal experiment.`,

  2: `The previous implementation represented rank intervals, separated upper and lower pair families, rebuilt their laminar family trees, and computed structural metrics. An oracle checked input validity and supplied a reference answer. The missing part was the dynamic procedure: updating the processed prefix, splitting sibling lists, transferring ownership, and recovering output from maintained state. Each update must preserve both the partial order and the family structure. An error in one update can corrupt both, so safe dynamic updates were the main implementation gap.`,

  3: `Since then, I narrowed the scope to externally certified valid inputs and implemented the Step 1, Step 2, and Step 3 control flow. I added ownership checks, transactional updates, replay, and bounded validation. Once the implementation passed these checks, I ran a formal experiment with a fixed protocol. The result is an executable ordinary-list reconstruction.`,

  4: `The thesis studies the 1990 sorting procedure on inputs already certified as valid by an oracle. The experiment compares Python sort, the complete oracle-backed reference pipeline, and the reconstructed paper core. Recognition remains outside this experiment. The current core uses ordinary Python lists. It does not implement the specialized backend used in the historical linear-time analysis.`,

  5: `RQ1 is the main technical question: can the ordinary-list reconstruction recover the correct sorted order from maintained state on certified valid inputs? RQ2 compares the paper call with Python sort and the complete reference pipeline under their stated timing scopes. RQ3 explores descriptive relationships between input structure, checked operation counters, and runtime. It does not claim a causal explanation. This talk focuses on RQ1 and the runtime baseline in RQ2. I do not present the structure–cost analysis here.`,

  6: `Before the paper call, the oracle certifies input validity. After the call, the runner compares the returned output with the oracle's sorted result. The reference pipeline uses the complete oracle result, including that sorted output. The paper core receives only the original sequence under the certified precondition. It executes Step 1, Step 2, and Step 3, maintains the partial order and sibling lists, and recovers output from the partial order. Both methods are checked against the same expected answer, but they produce their outputs differently. The oracle-sorted answer never enters the paper core. The dashed comparison box therefore sits outside it.`,

  7: `We maintain two things: the sorted order of the processed points, and the parent-child structure of the pairs. We initialize once, sorting only the first three points by x-coordinate. Their sorted order is called S three. We also initialize the upper and lower pair families, without an oracle answer. Point labels and stored pair endpoints keep curve order. Starting with point four, each round adds one point. We start from the previous point along the curve. Steps one and two use its neighbors in the sorted list to find predecessor boundary A sub i and successor boundary B sub i. Step three A places the new pair in the family structure and assigns its parent. Step three B splits a sibling list when needed, so newly enclosed pairs become children of the new pair. Only then does Step three C insert the new point into the sorted list, using an anchor selected from the maintained state. Increasing Step three A uses A sub i, and three B uses B sub i. Decreasing swaps these uses and reflects left and right operations. Steps one and two still return A and B. The paper states the increasing case. Decreasing is a symmetric reconstruction; anchor details are executable clarifications. These categories describe the basis of the reconstruction, not separate steps.`,

  8: `Take the input three, two, one, four. After initialization, the sorted list is one, two, three. The point labels still follow curve order.

We now insert the fourth point, four. After Step three B, the new upper pair P four, with endpoints one and four, has one child: P two, stored as three, two.

This update goes from one to four, so it is increasing. The child’s interval, from two to three, lies inside the new interval, from one to four. Four must therefore come after both child endpoints. The child’s right boundary is three, so three is our anchor.

Inserting four immediately after two would put it between the child endpoints, giving one, two, four, three. Inserting it after three gives one, two, three, four.

We could also store the endpoints from left to right, provided we keep their curve-order identities. The mistake is treating the second curve-order endpoint as the right endpoint.

I record this as an executable clarification, not a verbatim rule from the 1990 paper.`,

  9: `Here we insert zero at iteration seven. The odd index makes the new pair a lower pair. Since zero is less than seven, this iteration is decreasing. After Step three B, the new pair has children P three and P five, shown here. Step three C takes the left endpoint of the leftmost child, P three, with endpoints two and three. So the base anchor is two. However, z one, with value one, is not an endpoint of any lower pair. It is still in the sorted list. Inserting zero before two would leave zero after one. Here the index is odd, and zero is smaller than z one, which is smaller than the base anchor. We therefore change the anchor to z one. This changes only output insertion, not the earlier boundary-pair selection.`,

  10: `Here, ownership means which parent pair a child list belongs to. When children move, their parent links and list membership must stay consistent. Before a split, the existing parent owns both segments. After the split, it keeps the retained segment, while the new parent receives the acquired segment. Both nonempty sides may get new lists, but only the acquired segment changes parent. Split and transfer form one transaction: save the affected state, update it, then check the boundary and ownership. If a check fails, rollback restores the previous state. Ordinary lists incur scanning, copying, slicing, and ownership-rebinding costs. These checks do not establish the update bounds required by the historical linear-time analysis.`,

  11: `The left side checks the implementation and its state. The right side checks the saved experiment records and recomputes their summaries. On the left, complementary checks include focused regression cases, all 2,074 oracle-valid permutations up to size eight, and checked-state audits of parent links, ownership, sibling lists, and recovered output. Deterministic replay compares states from repeated runs of the same core; it is not a second independent implementation. On the right, checks compare the archived records with the fixed experiment setup and recomputed summaries. This finite evidence is not a mathematical proof for every Jordan sequence.`,

  12: `We test five sizes from 32 to 512 points. Each size has one flat case, one nested case, and ten incrementally generated valid cases: 60 inputs. Flat inputs increase; nested inputs alternate the smallest and largest remaining values. Incremental generation uses fixed seeds and validity checks. Each algorithm has five warm-ups and twenty measured calls per input, giving 3,600 rows. Repeated calls use fresh lists; algorithm positions rotate. Certification and one checked-state audit per case precede paper timing. Minimal mode runs the same core on all points, omitting detailed trace and some diagnostic checks. Paper timing includes initialization, Steps one to three, and output recovery. Output comparison follows timing. Python times sorting; reference times its complete oracle-backed pipeline. The runtime slide shows paper and Python.`,

  13: `All 60 cases in this runtime experiment passed certification and one checked-state audit each. Every measured call returned the expected output, with no recorded correctness errors. The 3,600 measured rows carry their case-level audit results; they do not represent 3,600 independent audits. These results cover the tested valid cases only.`,

  14: `This slide shows the runtime of the ordinary-list paper core, with Python sort as a practical baseline.

Both methods receive the same valid inputs and produce their own sorted outputs. Certification and external checks are outside timing. Each method's output construction remains timed.

Each plotted value is the median of twelve case medians, with equal weight per case. Each case median comes from twenty timed calls. The vertical axis uses a logarithmic scale.

The paper time rises from about 0.59 milliseconds at 32 points to 18.72 milliseconds at 512 points. Python sort has a much lower median time at every tested size.

These results describe the current implementation. They do not establish linear-time performance or isolate the cost of individual components. They give us a baseline for later optimization and backend comparisons.`,

  15: `The evidence supports an executable ordinary-list reconstruction that recovers output from maintained state, with correct results on the 60 cases in the runtime experiment. The runtime trend describes this implementation under the stated timing scopes. Ordinary lists do not establish a linear-time implementation, and five tested sizes do not establish asymptotic complexity. Recognition was not evaluated.`,

  16: `A finger-tree backend is a possible future extension, outside the current experimental evidence. It would keep the same Step 1, Step 2, and Step 3 behavior. The ordinary-list implementation provides a tested reference point for checking the behavior of a new backend. I would like guidance on two questions. Should I target the historical heterogeneous finger tree, or an equivalent backend supporting the required list operations? Is a tested, semantically equivalent prototype enough, or should I also prove the required amortized operation bounds?`,





};

const TALK_TITLES = {
  1: "Progress on the Executable Reconstruction of Simplified Jordan Sorting",
  2: "The previous report established a static structural baseline",
  3: "Progress since the previous report",
  4: "Current scope: valid-input sorting",
  5: "Three questions connect reconstruction, measurement, and interpretation",
  6: "The oracle, reference pipeline, and paper core have distinct roles",
  7: "Initialize once, then update one point at a time",
  8: "From S₃ to S₄: the geometric insertion anchor",
  9: "Why z₁ needs a separate output-anchor check",
  10: "Ownership-safe split and transfer",
  11: "Implementation checks and experiment consistency",
  12: "Runtime experiment: inputs and measurement",
  13: "All 60 cases in the runtime experiment returned the correct output",
  14: "Runtime baseline for the ordinary-list implementation",
  15: "What the current evidence shows",
  16: "Possible next step: a finger-tree backend",
};

async function imageBytes(path) {
  const bytes = await fs.readFile(path);
  return bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
}

function addText(slide, text, x, y, width, height, options = {}) {
  const shape = slide.shapes.add({
    geometry: "textbox",
    name: options.name,
    position: { left: x, top: y, width, height },
    fill: "none",
    line: { style: "solid", fill: "none", width: 0 },
  });
  shape.text = text;
  shape.text.style = {
    fontSize: options.fontSize ?? 20,
    bold: options.bold ?? false,
    italic: options.italic ?? false,
    color: options.color ?? C.ink,
    alignment: options.align ?? "left",
    verticalAlignment: options.valign ?? "top",
    autoFit: options.autoFit ?? "shrinkText",
    wrap: "square",
    lineSpacing: options.lineSpacing ?? 1.05,
    insets: options.insets ?? { left: 4, right: 4, top: 2, bottom: 2 },
  };
  return shape;
}

function addBox(slide, x, y, width, height, options = {}) {
  return slide.shapes.add({
    geometry: options.geometry ?? "roundRect",
    name: options.name,
    position: { left: x, top: y, width, height },
    fill: options.fill ?? C.white,
    line: {
      style: options.lineStyle ?? "solid",
      fill: options.line ?? C.line,
      width: options.lineWidth ?? 1.2,
    },
    borderRadius: options.radius ?? 10,
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
  const fontSize = options.fontSize ?? 20;
  const color = options.color ?? C.ink;
  const bulletColor = options.bulletColor ?? C.teal;
  items.forEach((item, index) => {
    const top = y + index * gap;
    slide.shapes.add({
      geometry: "ellipse",
      position: { left: x, top: top + 8, width: 10, height: 10 },
      fill: bulletColor,
      line: { style: "solid", fill: bulletColor, width: 0 },
    });
    addText(slide, item, x + 22, top, width - 22, gap - 2, {
      fontSize,
      color,
      valign: "middle",
      lineSpacing: 1.0,
    });
  });
}

function addFooter(slide, pageLabel) {
  addRule(slide, 64, 680, 1152, C.line, 1);
  addText(slide, "MASTER'S THESIS PROGRESS REPORT", 68, 686, 380, 20, {
    fontSize: 11,
    bold: true,
    color: C.muted,
    valign: "middle",
  });
  addText(slide, pageLabel, 1120, 686, 92, 20, {
    fontSize: 11,
    bold: true,
    color: C.muted,
    align: "right",
    valign: "middle",
  });
}

function baseSlide(presentation, title, section, pageLabel) {
  const slide = presentation.slides.add();
  slide.background.fill = C.light;
  addText(slide, section.toUpperCase(), 66, 26, 360, 22, {
    fontSize: 12,
    bold: true,
    color: C.teal,
    valign: "middle",
  });
  addText(slide, title, 64, 54, 1152, 55, {
    fontSize: 36,
    bold: true,
    color: C.navy,
    valign: "middle",
    lineSpacing: 0.95,
  });
  addRule(slide, 64, 114, 1152, C.teal, 3);
  addFooter(slide, pageLabel);
  return slide;
}

let notesIndex = 0;

function relativeSource(source) {
  if (source.startsWith(`${REPO}/`)) return source.slice(REPO.length + 1);
  return source;
}

function setNotes(slide, talkTrack, sources) {
  notesIndex += 1;
  const resolvedTalkTrack = TALK[notesIndex] ?? talkTrack;
  slide.speakerNotes.textFrame.setText(
    `${resolvedTalkTrack}\n\n[Sources]\n${sources.map((s) => `- ${relativeSource(s)}`).join("\n")}`,
  );
  slide.speakerNotes.setVisible(true);
}

function metric(slide, value, label, x, y, width, accent = C.teal) {
  addText(slide, value, x, y, width, 68, {
    fontSize: 48,
    bold: true,
    color: accent,
    align: "center",
    valign: "middle",
  });
  addText(slide, label, x + 4, y + 68, width - 8, 48, {
    fontSize: 18,
    color: C.slate,
    align: "center",
    valign: "top",
  });
}

function labelTag(slide, text, x, y, width, fill, color = C.white) {
  addBox(slide, x, y, width, 30, { fill, line: fill, radius: 6 });
  addText(slide, text, x, y + 1, width, 28, {
    fontSize: 13,
    bold: true,
    color,
    align: "center",
    valign: "middle",
  });
}

function addImage(slide, blob, alt, x, y, width, height, options = {}) {
  return slide.images.add({
    blob,
    contentType: "image/png",
    alt,
    fit: options.fit ?? "contain",
    position: { left: x, top: y, width, height },
    crop: options.crop,
    geometry: options.geometry ?? "rect",
    borderRadius: options.radius,
  });
}

async function main() {
  await fs.mkdir(`${BUILD}/rendered`, { recursive: true });
  const imgs = {};
  for (const [key, path] of Object.entries(ASSET)) imgs[key] = await imageBytes(path);

  const presentation = Presentation.create({ slideSize: { width: W, height: H } });

  // 1. Title
  {
    const slide = presentation.slides.add();
    slide.background.fill = C.navy;
    addBox(slide, 760, 0, 520, 720, { fill: C.white, line: C.white, geometry: "rect", radius: 0 });
    addImage(slide, imgs.jordan, "Simple curve and axis intersections defining Jordan sorting", 770, 158, 490, 320, { fit: "contain" });
    addText(slide, "MASTER'S THESIS PROGRESS REPORT", 72, 70, 590, 28, {
      fontSize: 14,
      bold: true,
      color: C.teal,
      valign: "middle",
    });
    addText(slide, "Progress on the Executable Reconstruction of Simplified Jordan Sorting", 72, 128, 620, 260, {
      fontSize: 50,
      bold: true,
      color: C.white,
      valign: "middle",
      lineSpacing: 0.92,
    });
    addText(slide, "Implementation progress, validation, and initial experimental results", 76, 405, 560, 72, {
      fontSize: 24,
      color: "#D9EAF2",
      valign: "middle",
    });
    addRule(slide, 76, 508, 150, C.coral, 5);
    addText(slide, "Research Seminar  |  Freie Universität Berlin  |  September 2026", 76, 534, 620, 42, {
      fontSize: 17,
      color: "#BCCCDC",
      valign: "middle",
    });
    addText(slide, "1 / 16", 1156, 680, 74, 20, { fontSize: 11, color: C.muted, align: "right" });
    setNotes(
      slide,
      "In the previous report, I presented the structural framework and the initial reference pipeline for Simplified Jordan Sorting. Since then, I have focused on the main implementation gap: turning the paper-facing dynamic procedure into an executable ordinary-list reconstruction. Today I will present that reconstruction, the validation strategy, and the formal experimental evidence obtained under the current protocol.",
      [
        `${REPO}/thesis/frontmatter/abstract.tex`,
        `${REPO}/thesis/chapters/introduction.tex`,
        `${REPO}/thesis/figures/jordan_sorting_problem.pdf`,
      ],
    );
  }

  // 2. Previous report boundary
  {
    const slide = baseSlide(presentation, "The previous report established a static structural baseline", "Context", "2 / 16");
    addText(slide, "PREVIOUS BASELINE", 94, 150, 390, 30, { fontSize: 15, bold: true, color: C.teal });
    addText(slide, "Structural reference framework", 94, 185, 390, 45, { fontSize: 27, bold: true, color: C.navy });
    addBulletList(slide, ["rank-interval abstraction", "upper and lower families", "family trees and structural metrics", "oracle-backed validation"], 102, 250, 390, { fontSize: 20, gap: 52 });

    addBox(slide, 548, 312, 120, 58, { fill: C.paleBlue, line: C.navy, radius: 29 });
    addText(slide, "static", 550, 318, 116, 45, { fontSize: 18, bold: true, color: C.navy, align: "center", valign: "middle" });
    addText(slide, "→", 665, 313, 70, 55, { fontSize: 38, bold: true, color: C.coral, align: "center", valign: "middle" });
    addBox(slide, 730, 312, 130, 58, { fill: C.paleTeal, line: C.teal, radius: 29 });
    addText(slide, "dynamic", 734, 318, 122, 45, { fontSize: 18, bold: true, color: C.teal, align: "center", valign: "middle" });

    addText(slide, "OPEN IMPLEMENTATION GAP", 900, 150, 300, 30, { fontSize: 15, bold: true, color: C.coral });
    addText(slide, "Executable dynamic reconstruction", 900, 185, 300, 70, { fontSize: 27, bold: true, color: C.navy });
    addBulletList(slide, ["Step 1/2/3 control flow", "sibling-list insertion and splitting", "ownership transfer", "output recovery from maintained state"], 908, 270, 294, { fontSize: 20, gap: 52, bulletColor: C.coral });

    addBox(slide, 94, 585, 1106, 54, { fill: C.navy, line: C.navy, radius: 6 });
    addText(slide, "Family trees explain nesting; executable Jordan sorting requires dynamic updates.", 112, 590, 1070, 44, { fontSize: 21, bold: true, color: C.white, align: "center", valign: "middle" });
    setNotes(
      slide,
      "The previous implementation already made the laminar upper and lower structures explicit. However, that was still primarily a static structural view. The central unresolved question was how to execute the incremental updates described by the paper while maintaining the sorted prefix and sibling-family ownership.",
      [
        `${REPO}/thesis/chapters/background.tex`,
        `${REPO}/thesis/chapters/implementation.tex`,
        "Hoffmann et al. (1986), doi:10.1016/S0019-9958(86)80033-X",
        "Fung et al. (1990), doi:10.1016/0020-0190(90)90111-A",
      ],
    );
  }

  // 3. Work packages
  {
    const slide = baseSlide(presentation, "Progress since the previous report", "Progress", "3 / 16");
    const xs = [76, 371, 666, 961];
    const colors = [C.navy, C.teal, C.coral, C.slate];
    const fills = [C.paleBlue, C.paleTeal, C.paleCoral, "#EDF2F7"];
    const titles = ["Scope stabilization", "Executable reconstruction", "State and correctness controls", "Initial formal evaluation"];
    const bodies = [
      "Separated valid-input sorting, recognition, and theoretical-backend claims",
      "Implemented the paper-facing Step 1/2/3 control flow",
      "Added ownership invariants, transactional updates, and replay",
      "Executed a fixed valid-input sorting experiment",
    ];
    for (let i = 0; i < 4; i++) {
      addText(slide, String(i + 1).padStart(2, "0"), xs[i], 170, 72, 54, { fontSize: 40, bold: true, color: colors[i] });
      addRule(slide, xs[i], 232, 205, colors[i], 4);
      addText(slide, titles[i], xs[i], 258, 220, 76, { fontSize: 24, bold: true, color: C.navy, valign: "middle" });
      addBox(slide, xs[i], 350, 226, 170, { fill: fills[i], line: fills[i], radius: 8 });
      addText(slide, bodies[i], xs[i] + 14, 366, 198, 140, { fontSize: 19, color: C.ink, align: "center", valign: "middle", lineSpacing: 1.08 });
    }
    addText(slide, "Current result: an executable ordinary-list implementation. The historical backend remains future work.", 130, 580, 1020, 56, { fontSize: 23, bold: true, color: C.navy, align: "center", valign: "middle" });
    setNotes(
      slide,
      "I organized the work into four technical packages. The largest part was the transition from the structural model to an executable dynamic state. The experiment was conducted only after the implementation and validation boundaries had been stabilized.",
      [
        `${REPO}/thesis/chapters/introduction.tex`,
        `${REPO}/thesis/chapters/implementation.tex`,
        `${REPO}/thesis/chapters/methodology.tex`,
      ],
    );
  }

  // 4. Refined scope
  {
    const slide = baseSlide(presentation, "Current scope: valid-input sorting", "Scope", "4 / 16");
    addBox(slide, 76, 152, 520, 410, { fill: C.white, line: C.line, radius: 8 });
    addBox(slide, 684, 152, 520, 410, { fill: C.white, line: C.teal, lineWidth: 2, radius: 8 });
    addText(slide, "Earlier planning emphasis", 100, 176, 470, 44, { fontSize: 25, bold: true, color: C.slate });
    addText(slide, "Current research scope", 708, 176, 470, 44, { fontSize: 25, bold: true, color: C.teal });
    const left = ["General structural framework", "Valid and invalid generators", "Static family trees", "Broad reference evaluation", "Recognition as a possible experiment", "Theoretical backend implementation"];
    const right = ["Executable reconstruction of the 1990 procedure", "Oracle-certified valid-input sorting", "Dynamic sibling-list state", "Paper core, reference pipeline, Python sort", "Recognition remains separate", "Ordinary lists in the current implementation"];
    left.forEach((t, i) => {
      addText(slide, t, 102, 238 + i * 50, 455, 38, { fontSize: 18, color: C.slate, valign: "middle" });
      addText(slide, "→", 610, 238 + i * 50, 58, 38, { fontSize: 26, bold: true, color: C.coral, align: "center", valign: "middle" });
      addText(slide, right[i], 710, 238 + i * 50, 455, 38, { fontSize: 18, bold: i === 0 || i === 2, color: C.ink, valign: "middle" });
    });
    addText(slide, "The experiment evaluates the ordinary-list implementation. A finger-tree backend remains a possible extension.", 120, 578, 1040, 64, { fontSize: 22, bold: true, color: C.navy, align: "center", valign: "middle" });
    setNotes(
      slide,
      "During implementation, it became important to separate three different questions: whether an input is valid, whether the reconstructed core sorts a valid input correctly, and whether the historical data structure achieves the theoretical bound. The thesis now focuses on the second question while using the first as an external precondition and leaving the third unimplemented.",
      [
        `${REPO}/thesis/chapters/introduction.tex`,
        `${REPO}/thesis/chapters/limitations.tex`,
        `${REPO}/thesis/chapters/methodology.tex`,
        "Supervisor feedback, September 2026",
      ],
    );
  }

  // 5. Research questions
  {
    const slide = baseSlide(presentation, "Three questions connect reconstruction, measurement, and interpretation", "Research Questions", "5 / 16");
    const rows = [
      { y: 156, color: C.teal, fill: C.paleTeal, id: "RQ1", title: "Executable reconstruction and correctness", text: "Can an ordinary-list reconstruction recover sorted order from maintained state for oracle-certified valid inputs?" },
      { y: 314, color: C.coral, fill: C.paleCoral, id: "RQ2", title: "Observed runtime behavior", text: "How does the paper core behave on pre-certified inputs relative to Python sort and the complete reference pipeline under different timing scopes?" },
      { y: 472, color: C.slate, fill: "#EDF2F7", id: "RQ3", title: "Structure and implementation cost", text: "What descriptive relationships appear between input structure, checked operation counters, and runtime?" },
    ];
    rows.forEach((r, i) => {
      addBox(slide, 76, r.y, 1128, 126, { fill: r.fill, line: r.fill, radius: 8 });
      addText(slide, r.id, 96, r.y + 18, 120, 46, { fontSize: 28, bold: true, color: r.color, valign: "middle" });
      addText(slide, r.title, 226, r.y + 14, 520, 44, { fontSize: 24, bold: true, color: C.navy, valign: "middle" });
      addText(slide, r.text, 226, r.y + 60, 930, 50, { fontSize: 18, color: C.ink, valign: "middle" });
      if (i === 0) labelTag(slide, "PRIMARY TECHNICAL QUESTION", 890, r.y + 17, 270, C.teal);
    });
    setNotes(
      slide,
      "RQ1 asks whether the reconstructed algorithm actually recovers its own output. RQ2 studies the observed runtime under explicitly different scopes. RQ3 examines implementation behavior, but only descriptively and without causal claims.",
      [`${REPO}/thesis/chapters/introduction.tex`],
    );
  }

  // 6. Component roles
  {
    const slide = baseSlide(presentation, "The oracle, reference pipeline, and paper core have distinct roles", "Architecture", "6 / 16");
    const oracle = addBox(slide, 445, 142, 390, 92, { fill: C.paleBlue, line: C.navy, lineWidth: 2, radius: 8 });
    addText(slide, "Certification oracle", 465, 156, 350, 34, { fontSize: 25, bold: true, color: C.navy, align: "center" });
    addText(slide, "validity + expected sorted order", 465, 194, 350, 26, { fontSize: 18, color: C.slate, align: "center" });
    const ref = addBox(slide, 92, 326, 455, 190, { fill: C.paleCoral, line: C.coral, lineWidth: 2, radius: 8 });
    const paper = addBox(slide, 733, 326, 455, 190, { fill: C.paleTeal, line: C.teal, lineWidth: 2, radius: 8 });
    slide.shapes.connect(oracle, ref, { kind: "elbow", fromSide: "bottom", toSide: "top", line: { style: "solid", fill: C.slate, width: 2 }, tail: { type: "arrow", width: "med", length: "med" } });
    slide.shapes.connect(oracle, paper, { kind: "elbow", fromSide: "bottom", toSide: "top", line: { style: "solid", fill: C.slate, width: 2 }, tail: { type: "arrow", width: "med", length: "med" } });
    addBox(slide, 142, 254, 356, 48, { fill: C.white, line: C.coral, radius: 6 });
    addText(slide, "oracle result, including sorted output", 156, 260, 328, 36, { fontSize: 17, bold: true, color: C.coral, align: "center", valign: "middle" });
    addBox(slide, 782, 254, 356, 48, { fill: C.white, line: C.teal, radius: 6 });
    addText(slide, "valid-input certification only", 796, 260, 328, 36, { fontSize: 17, bold: true, color: C.teal, align: "center", valign: "middle" });
    addText(slide, "Oracle-backed reference pipeline", 116, 344, 405, 48, { fontSize: 25, bold: true, color: C.coral, align: "center" });
    addText(slide, "family trees\nstructural information\noracle-derived output", 126, 404, 385, 88, { fontSize: 20, color: C.ink, align: "center", valign: "middle" });
    addText(slide, "Paper ordinary-list core", 757, 344, 405, 48, { fontSize: 25, bold: true, color: C.teal, align: "center" });
    addText(slide, "input sequence + certified precondition\nStep 1/2/3 and maintained state\noutput recovered from state", 770, 400, 380, 92, { fontSize: 18, color: C.ink, align: "center", valign: "middle" });
    const comparison = addBox(slide, 858, 526, 286, 36, { fill: C.white, line: C.slate, lineStyle: "dashed", radius: 5 });
    addText(slide, "post-call output comparison", 868, 531, 266, 26, { fontSize: 16, bold: true, color: C.slate, align: "center", valign: "middle" });
    slide.shapes.connect(paper, comparison, { kind: "straight", fromSide: "bottom", toSide: "top", line: { style: "dashed", fill: C.slate, width: 1.5 }, tail: { type: "arrow", width: "sm", length: "sm" } });
    addBox(slide, 132, 582, 1016, 54, { fill: C.navy, line: C.navy, radius: 6 });
    addText(slide, "Certification before the paper call  |  comparison after the call  |  oracle-sorted output never enters the paper core", 150, 589, 980, 40, { fontSize: 18, bold: true, color: C.white, align: "center", valign: "middle" });
    setNotes(
      slide,
      "The oracle has two external roles: it certifies the valid-input precondition and supplies the expected result used after execution. The reference pipeline deliberately consumes oracle-derived output. The paper core does not. Its output is recovered from the maintained partial order.",
      [
        `${REPO}/thesis/chapters/implementation.tex`,
        `${REPO}/thesis/chapters/methodology.tex`,
        `${REPO}/src/paper_jordan.py`,
        `${REPO}/src/simplified_jordan.py`,
      ],
    );
  }

  // 7. Step flow
  {
    const slide = baseSlide(presentation, "Initialize once, then update one point at a time", "Reconstruction", "7 / 16");
    addBox(slide, 76, 138, 1128, 158, { fill: C.paleBlue, line: C.slate, radius: 8 });
    addText(slide, "A. Initialize once (n ≥ 3)", 92, 146, 1088, 30, { fontSize: 23, bold: true, color: C.navy });
    addText(slide, "Sort only z₁, z₂, z₃\nby x-coordinate", 96, 190, 300, 62, { fontSize: 23, color: C.ink, align: "center" });
    addText(slide, "→", 398, 194, 46, 40, { fontSize: 30, color: C.teal, align: "center" });
    addText(slide, "Initial sorted list S₃", 452, 194, 310, 42, { fontSize: 24, bold: true, color: C.teal, align: "center" });
    addText(slide, "→", 766, 194, 46, 40, { fontSize: 30, color: C.teal, align: "center" });
    addText(slide, "Upper/lower families\nP₂, P₃ and dummy roots", 822, 186, 360, 64, { fontSize: 22, color: C.ink, align: "center" });
    addText(slide, "Core-local initialization. No oracle answer. Labels and stored pair endpoints keep curve order.", 94, 258, 1092, 28, { fontSize: 20, color: C.slate, align: "center" });

    addText(slide, "B. For i = 4, …, n: process one new point", 76, 312, 1128, 32, { fontSize: 24, bold: true, color: C.teal });
    addText(slide, "Sᵢ₋₁ + new point zᵢ → one round below → Sᵢ", 76, 350, 1128, 32, { fontSize: 23, bold: true, color: C.navy, align: "center" });
    const nodes = [
      { title: "Step 1", body: "Find predecessor-side\nboundary Aᵢ" },
      { title: "Step 2", body: "Find successor-side\nboundary Bᵢ" },
      { title: "Step 3(a)", body: "Insert new pair\nPᵢ = (zᵢ₋₁, zᵢ)" },
      { title: "Step 3(b)", body: "Split sibling lists\nTransfer ownership\nwhen needed" },
      { title: "Step 3(c)", body: "Insert zᵢ into the\nmaintained sorted list" },
    ];
    const shapes = nodes.map((n, i) => {
      const x = 76 + i * 230;
      const shape = addBox(slide, x, 398, 208, 114, { fill: i < 2 ? C.paleBlue : C.paleTeal, line: C.slate, radius: 6 });
      addText(slide, n.title, x + 8, 406, 192, 30, { fontSize: 22, bold: true, color: C.navy, align: "center" });
      addText(slide, n.body, x + 7, 441, 194, 66, { fontSize: 19, color: C.ink, align: "center", valign: "middle" });
      return shape;
    });
    for (let i = 0; i < 4; i++) slide.shapes.connect(shapes[i], shapes[i + 1], { kind: "straight", fromSide: "right", toSide: "left", line: { style: "solid", fill: C.teal, width: 2 }, tail: { type: "arrow", width: "sm", length: "sm" } });
    addText(slide, "Step 1 → Aᵢ and Step 2 → Bᵢ in both orientations", 76, 522, 1128, 28, { fontSize: 21, bold: true, color: C.navy, align: "center" });
    addText(slide, "Increasing: 3(a) uses Aᵢ, 3(b) uses Bᵢ. Decreasing swaps these uses and reflects left/right operations.", 76, 552, 1128, 28, { fontSize: 20, color: C.slate, align: "center" });
    addText(slide, "How the reconstruction is justified (categories, not algorithm stages)", 76, 594, 1128, 26, { fontSize: 19, color: C.muted });
    const evidence = [
      { x: 76, color: C.navy, fill: C.paleBlue, text: "Explicit source rules" },
      { x: 460, color: C.teal, fill: C.paleTeal, text: "Symmetric reconstruction" },
      { x: 844, color: C.coral, fill: C.paleCoral, text: "Executable clarifications" },
    ];
    evidence.forEach((e) => {
      addBox(slide, e.x, 630, 360, 40, { fill: e.fill, line: e.color, radius: 6 });
      addText(slide, e.text, e.x + 8, 634, 344, 30, { fontSize: 21, bold: true, color: e.color, align: "center" });
    });
    setNotes(slide, TALK[7], [
      `${REPO}/thesis/chapters/algorithm.tex`,
      `${REPO}/thesis/chapters/implementation.tex`,
      "Fung et al. (1990), doi:10.1016/0020-0190(90)90111-A",
    ]);
  }

  // 8. Endpoint semantics
  {
    const slide = baseSlide(presentation, "From S₃ to S₄: the geometric insertion anchor", "Reconstruction Issue I", "8 / 16");
    addText(slide, "Input in curve order: (z₁, z₂, z₃, z₄) = (3, 2, 1, 4)", 76, 138, 1128, 34, { fontSize: 25, bold: true, color: C.navy });
    addBox(slide, 76, 188, 690, 112, { fill: C.paleBlue, line: C.slate, radius: 6 });
    addText(slide, "After initialization: S₃ = [1, 2, 3]", 92, 198, 658, 36, { fontSize: 25, bold: true, color: C.navy });
    addText(slide, "Point IDs: [z₃, z₂, z₁]. Curve labels stay unchanged.", 92, 250, 658, 32, { fontSize: 22, color: C.slate });
    addBox(slide, 790, 188, 414, 112, { fill: C.paleTeal, line: C.teal, radius: 6 });
    addText(slide, "Now process z₄ = 4", 806, 198, 382, 36, { fontSize: 25, bold: true, color: C.teal });
    addText(slide, "z₃ = 1 → z₄ = 4: increasing", 806, 250, 382, 32, { fontSize: 22, color: C.ink });
    addText(slide, "After Step 3(b)", 76, 324, 242, 32, { fontSize: 22, bold: true, color: C.navy });
    addText(slide, "New upper P₄ = (z₃, z₄) = (1, 4)", 320, 324, 420, 32, { fontSize: 22, bold: true, color: C.teal });
    addText(slide, "→ child", 744, 324, 106, 32, { fontSize: 22, color: C.teal });
    addText(slide, "Upper P₂ = (z₁, z₂) = (3, 2)", 850, 324, 354, 32, { fontSize: 21, bold: true, color: C.navy });
    addText(slide, "P₄ has child P₂. In this increasing update, use its geometric right endpoint.", 76, 373, 1128, 32, { fontSize: 23, bold: true, color: C.navy, align: "center" });

    addBox(slide, 76, 427, 552, 160, { fill: C.paleCoral, line: C.coral, lineWidth: 2, radius: 8 });
    addText(slide, "Second stored endpoint of P₂: 2", 92, 437, 520, 34, { fontSize: 23, bold: true, color: C.coral });
    addText(slide, "Insert 4 immediately after 2", 92, 484, 520, 32, { fontSize: 23, color: C.ink });
    addText(slide, "[1, 2, 4, 3]  Incorrect (illustration)", 92, 535, 520, 36, { fontSize: 24, bold: true, color: C.coral });
    addBox(slide, 652, 427, 552, 160, { fill: C.paleTeal, line: C.teal, lineWidth: 2, radius: 8 });
    addText(slide, "Geometric right endpoint of P₂: 3", 668, 437, 520, 34, { fontSize: 23, bold: true, color: C.teal });
    addText(slide, "Insert 4 immediately after 3", 668, 484, 520, 32, { fontSize: 23, color: C.ink });
    addText(slide, "[1, 2, 3, 4]  Correct", 668, 535, 520, 36, { fontSize: 24, bold: true, color: C.teal });
    addText(slide, "Here, the anchor is the existing point immediately after which we insert 4.", 76, 605, 1128, 30, { fontSize: 22, color: C.navy, align: "center" });
    addText(slide, "Executable clarification, not a verbatim 1990-paper rule. Stored curve order ≠ geometric order.", 76, 644, 1128, 28, { fontSize: 20, color: C.slate, align: "center" });
    setNotes(slide, TALK[8], [
      `${REPO}/thesis/chapters/algorithm.tex`,
      `${REPO}/src/paper_jordan.py`,
    ]);
  }

  // 9. z1 output-anchor check
  {
    const slide = baseSlide(presentation, "Why z₁ needs a separate output-anchor check", "Reconstruction Issue II", "9 / 16");
    addText(slide, "Input (z₁, …, z₇) = (1, 2, 3, 4, 6, 7, 0)", 76, 136, 700, 32, { fontSize: 22, bold: true, color: C.navy });
    addText(slide, "S₆ = [1, 2, 3, 4, 6, 7]", 802, 138, 402, 30, { fontSize: 21, color: C.slate });
    addText(slide, "i = 7 (odd) → lower family", 76, 182, 530, 30, { fontSize: 22, bold: true, color: C.teal });
    addText(slide, "z₇ = 0 < z₆ = 7 → decreasing", 668, 182, 536, 30, { fontSize: 22, bold: true, color: C.teal });

    addText(slide, "Decreasing: leftmost child → left endpoint", 76, 234, 552, 32, { fontSize: 22, bold: true, color: C.navy });
    const parent = addBox(slide, 230, 308, 240, 48, { fill: C.paleBlue, line: C.navy, radius: 6 });
    addText(slide, "P₇ = (7, 0)", 238, 314, 224, 36, { fontSize: 25, bold: true, color: C.navy, align: "center" });
    addText(slide, "curve order (7, 0); interval [0, 7]", 126, 274, 454, 28, { fontSize: 18, color: C.slate, align: "center" });
    const left = addBox(slide, 94, 384, 220, 48, { fill: C.paleTeal, line: C.teal, lineWidth: 2, radius: 6 });
    const right = addBox(slide, 374, 384, 220, 48, { fill: C.white, line: C.slate, radius: 6 });
    slide.shapes.connect(parent, left, { kind: "elbow", fromSide: "left", toSide: "top", line: { style: "solid", fill: C.teal, width: 2 }, tail: { type: "arrow", width: "sm", length: "sm" } });
    slide.shapes.connect(parent, right, { kind: "elbow", fromSide: "right", toSide: "top", line: { style: "solid", fill: C.slate, width: 2 }, tail: { type: "arrow", width: "sm", length: "sm" } });
    addText(slide, "P₃ = (2, 3)", 102, 389, 204, 36, { fontSize: 24, bold: true, color: C.teal, align: "center" });
    addText(slide, "P₅ = (4, 6)", 382, 389, 204, 36, { fontSize: 24, bold: true, color: C.navy, align: "center" });
    addText(slide, "leftmost child", 98, 434, 210, 26, { fontSize: 18, bold: true, color: C.teal, align: "center" });
    addText(slide, "P₃ → left endpoint 2 → base anchor z₂", 76, 468, 552, 32, { fontSize: 21, bold: true, color: C.teal, align: "center" });

    addText(slide, "Why check z₁?", 668, 234, 536, 32, { fontSize: 24, bold: true, color: C.navy });
    addText(slide, "z₁ = 1 belongs to upper pair P₂ = (1, 2).", 668, 282, 536, 34, { fontSize: 22, color: C.ink });
    addText(slide, "It is not an endpoint of any lower pair.", 668, 322, 536, 34, { fontSize: 22, bold: true, color: C.navy });
    addText(slide, "It is still in the sorted list S₆.", 668, 362, 536, 34, { fontSize: 22, color: C.ink });
    addText(slide, "Odd i and 0 < z₁ = 1 < base anchor = 2", 668, 416, 536, 38, { fontSize: 24, bold: true, color: C.coral });
    addText(slide, "Final output anchor: z₁", 668, 463, 536, 34, { fontSize: 23, bold: true, color: C.teal });

    addBox(slide, 76, 522, 552, 104, { fill: C.paleCoral, line: C.coral, radius: 6 });
    addText(slide, "Without correction (illustration)", 92, 530, 520, 30, { fontSize: 21, bold: true, color: C.coral });
    addText(slide, "insert 0 before 2 → [1, 0, 2, 3, 4, 6, 7]", 92, 574, 520, 34, { fontSize: 22, color: C.ink });
    addBox(slide, 652, 522, 552, 104, { fill: C.paleTeal, line: C.teal, radius: 6 });
    addText(slide, "With correction", 668, 530, 520, 30, { fontSize: 21, bold: true, color: C.teal });
    addText(slide, "insert 0 before z₁ → [0, 1, 2, 3, 4, 6, 7]", 668, 574, 520, 34, { fontSize: 22, color: C.ink });
    addText(slide, "This changes the output anchor, not the earlier boundary-pair selection.", 76, 642, 1128, 30, { fontSize: 21, bold: true, color: C.navy, align: "center" });
    setNotes(
      slide,
      TALK[9],
      [
        `${REPO}/thesis/chapters/algorithm.tex`,
        `${REPO}/thesis/figures/step3c_anchor_z1_anomaly.pdf`,
        "Hoffmann et al. (1986), p. 175, doi:10.1016/S0019-9958(86)80033-X",
      ],
    );
  }


  // 10. State and transactions
  {
    const slide = baseSlide(presentation, "Ownership-safe split and transfer", "Maintained State", "10 / 16");
    addBox(slide, 68, 150, 656, 420, { fill: C.white, line: C.line, radius: 8 });
    addText(slide, "Owner: the parent pair that owns this child list", 94, 170, 606, 38, { fontSize: 21, bold: true, color: C.navy, align: "center" });

    addText(slide, "Before", 94, 226, 92, 30, { fontSize: 18, bold: true, color: C.muted });
    addBox(slide, 194, 218, 164, 52, { fill: C.paleBlue, line: C.navy, lineWidth: 1.5, radius: 6 });
    addText(slide, "existing owner", 204, 226, 144, 36, { fontSize: 19, bold: true, color: C.navy, align: "center", valign: "middle" });
    addText(slide, "owns", 368, 226, 70, 36, { fontSize: 18, color: C.slate, align: "center", valign: "middle" });
    addBox(slide, 446, 212, 220, 64, { fill: C.white, line: C.slate, radius: 6 });
    addText(slide, "retained  |  acquired", 458, 222, 196, 44, { fontSize: 18, bold: true, color: C.ink, align: "center", valign: "middle" });

    addText(slide, "split + transfer", 264, 302, 250, 38, { fontSize: 20, bold: true, color: C.coral, align: "center" });
    addText(slide, "↓", 354, 336, 72, 44, { fontSize: 34, bold: true, color: C.coral, align: "center" });

    addText(slide, "After", 94, 390, 92, 30, { fontSize: 18, bold: true, color: C.muted });
    addBox(slide, 194, 382, 164, 52, { fill: C.paleBlue, line: C.navy, lineWidth: 1.5, radius: 6 });
    addText(slide, "existing owner", 204, 390, 144, 36, { fontSize: 19, bold: true, color: C.navy, align: "center", valign: "middle" });
    addText(slide, "→", 365, 390, 54, 36, { fontSize: 24, bold: true, color: C.slate, align: "center", valign: "middle" });
    addBox(slide, 424, 382, 146, 52, { fill: C.white, line: C.navy, radius: 6 });
    addText(slide, "retained", 434, 390, 126, 36, { fontSize: 18, bold: true, color: C.navy, align: "center", valign: "middle" });
    addBox(slide, 194, 460, 164, 52, { fill: C.paleTeal, line: C.teal, lineWidth: 1.5, radius: 6 });
    addText(slide, "new owner", 204, 468, 144, 36, { fontSize: 19, bold: true, color: C.teal, align: "center", valign: "middle" });
    addText(slide, "→", 365, 468, 54, 36, { fontSize: 24, bold: true, color: C.teal, align: "center", valign: "middle" });
    addBox(slide, 424, 460, 146, 52, { fill: C.paleTeal, line: C.teal, radius: 6 });
    addText(slide, "acquired", 434, 468, 126, 36, { fontSize: 18, bold: true, color: C.teal, align: "center", valign: "middle" });
    addText(slide, "Only the acquired nonempty segment changes parent ownership.", 110, 526, 572, 28, { fontSize: 17, color: C.slate, align: "center" });

    addText(slide, "Maintained state", 765, 152, 390, 36, { fontSize: 25, bold: true, color: C.navy });
    addBulletList(slide, ["sorted processed prefix", "upper and lower pair families", "one parent per finite pair", "one sibling-list membership per finite pair"], 770, 205, 410, { fontSize: 19, gap: 45 });
    addText(slide, "Transactional update", 765, 408, 390, 36, { fontSize: 25, bold: true, color: C.teal });
    addText(slide, "save state  →  split  →  transfer  →\ncheck postconditions  →  roll back on failure", 770, 454, 410, 92, { fontSize: 20, color: C.ink, align: "center", valign: "middle" });
    addBox(slide, 112, 600, 1056, 50, { fill: C.paleCoral, line: C.coral, radius: 6 });
    addText(slide, "Ordinary lists expose scanning, copying, slicing, and ownership rebinding as concrete costs.", 128, 605, 1024, 40, { fontSize: 20, bold: true, color: C.coral, align: "center", valign: "middle" });
    setNotes(
      slide,
      "The main maintainability risk is not only sorted-order insertion. Every pair must remain attached to exactly one parent and exactly one sibling-list owner. Split and transfer operations are therefore transactional: affected state is saved, local postconditions are checked, and an invalid update is rolled back.",
      [
        `${REPO}/thesis/chapters/implementation.tex`,
        `${REPO}/thesis/figures/family_sibling_structure.pdf`,
        `${REPO}/src/paper_jordan.py`,
      ],
    );
  }

  // 11. Correctness evidence
  {
    const slide = baseSlide(presentation, "Implementation checks and experiment consistency", "Validation", "11 / 16");
    addText(slide, "Is the output and maintained state correct?", 88, 146, 470, 50, { fontSize: 21, bold: true, color: C.teal });
    addText(slide, "Are the experiment records and summaries consistent?", 722, 146, 470, 66, { fontSize: 21, bold: true, color: C.coral });
    const left = ["Focused regression cases", "Bounded exhaustive validation\n2,074 oracle-valid permutations, n ≤ 8", "Checked-state audits", "Same-core deterministic replay"];
    const ys = [202, 294, 402, 494];
    for (let i = 0; i < 4; i++) {
      addBox(slide, 88, ys[i], 470, i === 1 ? 82 : 64, { fill: C.paleTeal, line: C.teal, radius: 7 });
      addText(slide, left[i], 104, ys[i] + 8, 438, i === 1 ? 66 : 48, { fontSize: i === 1 ? 18 : 20, bold: i === 1, color: C.ink, align: "center", valign: "middle" });
    }
    addBox(slide, 722, 232, 470, 250, { fill: C.paleCoral, line: C.coral, lineWidth: 1.5, radius: 8 });
    addText(slide, "Check saved experiment records against the fixed setup and recompute their summaries.", 758, 282, 398, 142, { fontSize: 23, bold: true, color: C.ink, align: "center", valign: "middle" });
    addText(slide, "Experiment records and summary consistency", 760, 506, 394, 34, { fontSize: 17, color: C.slate, align: "center", valign: "middle" });
    addText(slide, "These checks support the evaluated cases. They do not prove correctness for every Jordan sequence.", 140, 610, 1000, 40, { fontSize: 21, bold: true, color: C.navy, align: "center", valign: "middle" });
    setNotes(
      slide,
      "Replay checks state consistency and determinism; it is not a second independent implementation. The evidence-contract validator checks the archive and its schedule, counts, summaries, and hashes. Together these layers provide strong bounded empirical evidence, but not a mathematical proof for every Jordan sequence.",
      [
        `${REPO}/thesis/chapters/implementation.tex`,
        `${REPO}/thesis/chapters/methodology.tex`,
        `${REPO}/docs/thesis/latex_final_audit.md`,
        `${REPO}/experiments/validate_week12_formal_sorting_outputs.py`,
      ],
    );
  }

  // 12. Formal experiment
  {
    const slide = baseSlide(presentation, "Runtime experiment: inputs and measurement", "Experimental Method", "12 / 16");
    addText(slide, "n = 32, 64, 128, 256, 512", 82, 142, 650, 38, { fontSize: 26, bold: true, color: C.navy });
    addText(slide, "12 inputs per size · 60 total", 760, 142, 434, 38, { fontSize: 24, bold: true, color: C.teal, align: "right" });
    const inputRows = [
      ["Flat", "1", "[1, 2, 3, …, n]"],
      ["Nested", "1", "[1, n, 2, n−1, …]"],
      ["Incremental", "10", "Fixed seeds; validity checked during construction"],
    ];
    addText(slide, "Input type", 90, 197, 230, 30, { fontSize: 19, bold: true, color: C.slate });
    addText(slide, "Per size", 342, 197, 120, 30, { fontSize: 19, bold: true, color: C.slate });
    addText(slide, "Construction", 518, 197, 662, 30, { fontSize: 19, bold: true, color: C.slate });
    inputRows.forEach((row, i) => {
      const y = 235 + i * 46;
      addText(slide, row[0], 90, y, 230, 38, { fontSize: 23, bold: true, color: C.navy });
      addText(slide, row[1], 362, y, 100, 38, { fontSize: 23, color: C.teal });
      addText(slide, row[2], 518, y, 662, 38, { fontSize: 22, color: C.ink });
    });
    addText(slide, "5 warm-ups, then 20 measured calls per input and algorithm", 84, 385, 1112, 34, { fontSize: 23, bold: true, color: C.navy });
    addText(slide, "60 inputs × 3 algorithms × 20 calls = 3,600 measured rows", 84, 423, 1112, 34, { fontSize: 23, bold: true, color: C.teal });
    addText(slide, "Before paper timing: certification and one checked-state audit per case", 84, 474, 1112, 32, { fontSize: 20, color: C.ink });
    addText(slide, "Paper minimal: same core, all points; no detailed trace, fewer diagnostic checks", 84, 510, 1112, 32, { fontSize: 20, color: C.ink });
    addText(slide, "Timed paper call: initialization, Steps 1–3, and output recovery", 84, 546, 1112, 32, { fontSize: 20, color: C.coral, bold: true });
    addText(slide, "Python: sorting call. Reference: complete oracle-backed pipeline.", 84, 590, 1112, 32, { fontSize: 20, color: C.slate });
    addText(slide, "Output comparison follows timing. Runtime focus: paper core and Python sort.", 84, 626, 1112, 30, { fontSize: 19, color: C.slate });
    setNotes(
      slide,
      "Each exact case is generated once, oracle-certified, structurally profiled, and checked once before timing. The paper call is timed only after certification. The reference call includes its full oracle-backed workflow. The next runtime slide focuses on the paper core and Python sort.",
      [
        `${REPO}/thesis/chapters/methodology.tex`,
        `${REPO}/thesis/figures/formal_experiment_pipeline.pdf`,
        `${REPO}/results/runs/week12_formal_sorting_v1__run001/config.json`,
        `${REPO}/results/runs/week12_formal_sorting_v1__run001/manifest.json`,
      ],
    );
  }

  // 13. Correctness results
  {
    const slide = baseSlide(presentation, "All 60 cases in the runtime experiment returned the correct output", "Results", "13 / 16");
    addText(slide, "60", 130, 176, 410, 100, { fontSize: 72, bold: true, color: C.teal, align: "center", valign: "middle" });
    addText(slide, "exact cases", 130, 278, 410, 46, { fontSize: 26, bold: true, color: C.navy, align: "center", valign: "middle" });
    addText(slide, "0", 740, 176, 410, 100, { fontSize: 72, bold: true, color: C.green, align: "center", valign: "middle" });
    addText(slide, "recorded correctness errors", 740, 278, 410, 46, { fontSize: 26, bold: true, color: C.navy, align: "center", valign: "middle" });
    addRule(slide, 76, 354, 1128, C.line, 2);
    addText(slide, "Each case was oracle-certified and checked once before timing.", 160, 382, 960, 56, { fontSize: 29, bold: true, color: C.navy, align: "center", valign: "middle" });
    addBox(slide, 166, 474, 948, 92, { fill: C.paleBlue, line: C.navy, lineWidth: 1.5, radius: 8 });
    addText(slide, "The 3,600 timing rows carry the corresponding case-level audit result.", 194, 492, 892, 56, { fontSize: 22, color: C.ink, align: "center", valign: "middle" });
    addText(slide, "These results cover the tested valid cases only.", 156, 606, 968, 36, { fontSize: 20, bold: true, color: C.coral, align: "center", valign: "middle" });
    setNotes(
      slide,
      "All formal cases passed certification and the untimed checked-state audit. Every measured row returned the expected output without a recorded error. The important boundary is that these are sixty controlled valid cases; the experiment does not evaluate arbitrary-input recognition.",
      [
        `${REPO}/thesis/chapters/results.tex`,
        `${REPO}/results/runs/week12_formal_sorting_v1__run001/raw.csv`,
        `${REPO}/results/runs/week12_formal_sorting_v1__run001/case_audit.csv`,
        `${REPO}/results/runs/week12_formal_sorting_v1__run001/validation_report.json`,
      ],
    );
  }

  // 14. Runtime baseline; equal-weight median of 12 exact-case medians.
  {
    const slide = baseSlide(presentation, "Runtime baseline for the ordinary-list implementation", "Results", "14 / 16");
    // Milliseconds from the frozen run's case_summary.csv (20 calls per case).
    slide.charts.add("line", {
      position: { left: 68, top: 148, width: 750, height: 450 },
      categories: ["32", "64", "128", "256", "512"],
      series: [
        { name: "Paper ordinary-list core", values: [0.58690625, 1.2821975, 2.81508325, 6.72124975, 18.71668725], line: { style: "solid", fill: C.teal, width: 3 }, marker: { symbol: "circle", size: 8 } },
        { name: "Python sort", values: [0.000791, 0.00141675, 0.00263525, 0.00520825, 0.0105835], line: { style: "solid", fill: C.coral, width: 3 }, marker: { symbol: "square", size: 8 } },
      ],
      hasLegend: true,
      legend: { position: "bottom", overlay: false, textStyle: { fill: C.slate, fontSize: 17 } },
      lineOptions: { grouping: "standard", smooth: false },
      chartFill: C.white,
      chartLine: { style: "solid", fill: C.line, width: 1 },
      plotAreaFill: C.white,
      plotAreaLine: { style: "solid", fill: C.line, width: 1 },
      xAxis: { title: { text: "Input size n", textStyle: { fill: C.slate, fontSize: 17 } }, textStyle: { fill: C.slate, fontSize: 16 }, line: { style: "solid", fill: C.line, width: 1 }, majorGridlines: null },
      yAxis: { title: { text: "Median call time (ms, log scale)", textStyle: { fill: C.slate, fontSize: 17 } }, logBase: 10, min: 0.0001, max: 100, numberFormatCode: "0.####", textStyle: { fill: C.slate, fontSize: 15 }, line: { style: "solid", fill: C.line, width: 1 }, majorGridlines: { style: "solid", fill: "#E6EDF3", width: 1 } },
    });
    addBox(slide, 850, 170, 340, 165, { fill: C.paleTeal, line: C.teal, radius: 8 });
    addText(slide, "Observed result", 872, 188, 296, 36, { fontSize: 24, bold: true, color: C.teal });
    addText(slide, "Python sort has a much lower median call time at every tested size.", 872, 239, 296, 78, { fontSize: 23, color: C.ink });
    addBox(slide, 850, 370, 340, 165, { fill: C.paleBlue, line: C.navy, radius: 8 });
    addText(slide, "Use of this baseline", 872, 388, 296, 36, { fontSize: 24, bold: true, color: C.navy });
    addText(slide, "A reference point for future optimization and backend comparisons.", 872, 439, 296, 78, { fontSize: 23, color: C.ink });
    addText(slide, "60 valid cases · Apple M4 / CPython 3.12.4 · no asymptotic conclusion", 84, 622, 1112, 34, { fontSize: 19, color: C.slate, align: "center", valign: "middle" });
    setNotes(slide, TALK[14], ["thesis/chapters/results.tex", "thesis/chapters/methodology.tex", "results/runs/week12_formal_sorting_v1__run001/case_summary.csv", "results/runs/week12_formal_sorting_v1__run001/config.json", "results/runs/week12_formal_sorting_v1__run001/manifest.json (source_commit: 98868b1b705f6d5f22404ee8ad7b88ad7a834f52)", "results/runs/week12_formal_sorting_v1__run001/environment.json", "experiments/run_week11_pilot.py (timing boundaries at the manifest source_commit)", "src/paper_jordan_sort.py (output recovery at the manifest source_commit)"]);
  }

  // 15. Interpretation boundaries
  {
    const slide = baseSlide(presentation, "What the current evidence shows", "Interpretation", "15 / 16");
    addBox(slide, 78, 152, 536, 404, { fill: C.paleTeal, line: C.teal, lineWidth: 2, radius: 8 });
    addBox(slide, 666, 152, 536, 404, { fill: C.paleCoral, line: C.coral, lineWidth: 2, radius: 8 });
    addText(slide, "Current results", 106, 178, 480, 52, { fontSize: 26, bold: true, color: C.teal, align: "center", valign: "middle" });
    addText(slide, "Main limits", 694, 178, 480, 52, { fontSize: 26, bold: true, color: C.coral, align: "center", valign: "middle" });
    addBulletList(slide, ["Executable reconstruction with output recovered from maintained state", "Correct outputs and runtime results for the 60 cases in this experiment"], 112, 270, 456, { fontSize: 22, gap: 132, bulletColor: C.teal });
    addBulletList(slide, ["Ordinary lists do not establish a linear-time implementation", "Five tested sizes do not establish asymptotic complexity"], 700, 270, 456, { fontSize: 22, gap: 132, bulletColor: C.coral });
    addText(slide, "Recognition was not evaluated. Paper and reference use different timing scopes.", 150, 600, 980, 40, { fontSize: 20, bold: true, color: C.navy, align: "center", valign: "middle" });
    setNotes(
      slide,
      "The main result is not that a linear-time algorithm has been implemented. The contribution is that the paper-facing control flow has become executable and auditable, with explicit backend and evidence boundaries.",
      [
        `${REPO}/thesis/chapters/limitations.tex`,
        `${REPO}/thesis/chapters/conclusion.tex`,
        "Supervisor feedback, September 2026",
      ],
    );
  }

  // 16. Milestone and next phase
  {
    const slide = baseSlide(presentation, "Possible next step: a finger-tree backend", "Next Step", "16 / 16");
    addText(slide, "The ordinary-list implementation provides a tested reference point.", 112, 156, 1056, 54, { fontSize: 28, bold: true, color: C.navy, align: "center", valign: "middle" });
    addBox(slide, 172, 244, 936, 100, { fill: C.paleTeal, line: C.teal, lineWidth: 1.5, radius: 8 });
    addText(slide, "A new backend would keep the same Step 1/2/3 behavior while changing the sibling-list operations.", 204, 268, 872, 54, { fontSize: 24, color: C.ink, align: "center", valign: "middle" });
    addText(slide, "Discussion with the supervisor", 112, 402, 1056, 38, { fontSize: 25, bold: true, color: C.teal, align: "center", valign: "middle" });
    addBox(slide, 112, 456, 1056, 162, { fill: C.navy, line: C.navy, radius: 8 });
    addText(slide, "1. Should I target the historical heterogeneous finger tree or an equivalent backend?\n2. Is a tested, semantically equivalent prototype enough, or should I also prove the required amortized operation bounds?", 154, 476, 972, 122, { fontSize: 24, color: C.white, valign: "middle" });
    setNotes(
      slide,
      "The main technical gap identified in the previous report has now been addressed at the ordinary-list level. The current implementation and formal evidence form a stable thesis baseline. The next phase is consolidation and review rather than an expansion of the algorithmic scope. I would particularly welcome feedback on whether the reconstruction boundary and the balance between implementation and evaluation are sufficiently clear.",
      [
        `${REPO}/thesis/chapters/implementation.tex`,
        `${REPO}/thesis/chapters/limitations.tex`,
        `${REPO}/thesis/README.md`,
        "Fung et al. (1990), doi:10.1016/0020-0190(90)90111-A",
        "Supervisor feedback, September 2026",
      ],
    );
  }

  // Render slide previews and export.
  for (const [index, slide] of presentation.slides.items.entries()) {
    const stem = `slide-${String(index + 1).padStart(2, "0")}`;
    const png = await presentation.export({ slide, format: "png", scale: 1 });
    await fs.writeFile(`${BUILD}/rendered/${stem}.png`, new Uint8Array(await png.arrayBuffer()));
    const layout = await slide.export({ format: "layout" });
    await fs.writeFile(`${BUILD}/rendered/${stem}.layout.json`, await layout.text());
  }
  const montage = await presentation.export({ format: "webp", montage: true, scale: 1 });
  await fs.writeFile(`${BUILD}/rendered/deck-montage.webp`, new Uint8Array(await montage.arrayBuffer()));
  const pptx = await PresentationFile.exportPptx(presentation);
  await pptx.save(OUT);
  const mainScript = Array.from({ length: 16 }, (_, index) => {
    const slideNumber = index + 1;
    return [
      `SLIDE ${slideNumber}`,
      TALK_TITLES[slideNumber],
      "",
      TALK[slideNumber],
    ].join("\n");
  }).join("\n\n============================================================\n\n");
  const scriptDocument = [
    "============================================================",
    "MAIN PRESENTATION: SLIDES 1-16",
    "============================================================",
    "",
    mainScript,
    "",
  ].join("\n");
  await fs.writeFile(SCRIPT_OUT, scriptDocument, "utf8");
  console.log(`Wrote ${OUT}`);
  console.log(`Wrote ${SCRIPT_OUT}`);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
