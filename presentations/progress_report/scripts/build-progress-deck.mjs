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
  runtime: `${PRESENTATION_DIR}/assets/week12_runtime_by_size.png`,
};

const TALK = {
  1: `Good afternoon. This presentation updates my master's thesis on an executable reconstruction of Simplified Jordan Sorting. My previous report focused on static structure: rank intervals, upper and lower pair families, family trees, and an oracle-backed reference. Since then, I have focused on one question. Can the paper's dynamic procedure run with ordinary Python lists while preserving its own state and recovering its own output? I will explain the reconstruction issues, the checks I used, and the runtime pattern observed in the formal experiment. I will spend most of the time on the two places where the paper description needed an explicit executable decision.`,

  2: `The earlier implementation made the static structure explicit. It represented rank intervals, separated the upper and lower families, rebuilt their laminar family trees, and computed structural metrics. The oracle checked whether an input was valid and supplied a reference answer. However, the code did not yet execute the dynamic procedure. It did not update the processed prefix as new points arrived. It also did not split sibling lists, transfer ownership, or recover the final order from the algorithm's own state. These operations matter because an error in one update can corrupt both the partial order and the family structure. The main gap was therefore the move from a structural description to safe dynamic updates.`,

  3: `Since the previous report, I have worked on four areas. I first narrowed the scope to sorting inputs that an external oracle has already certified. I then implemented the Step 1, Step 2, and Step 3 control flow. Next, I added ownership checks, transactional updates, replay, and bounded validation. Finally, after the implementation was working and checked, I ran a formal experiment with a fixed protocol. The result is an executable ordinary-list implementation. The specialized backend used in the historical linear-time analysis remains future work.`,

  4: `As the implementation became clearer, I narrowed the scope. The thesis now studies the 1990 sorting procedure on inputs that an oracle has already certified as valid. The experiment compares Python sort, the complete oracle-backed reference pipeline, and the reconstructed paper core. Recognition remains a separate question. I do not use the experiment to classify invalid inputs. The paper core also uses ordinary Python lists rather than the specialized historical backend. This scope lets the thesis study one concrete issue: whether the dynamic procedure can run correctly and recover output from its own maintained state. A finger-tree backend remains a possible extension.`,

  5: `The work has three research questions. RQ1 asks whether the ordinary-list reconstruction can recover the correct sorted order from its maintained state on certified valid inputs. RQ2 asks how the paper call behaves relative to Python sort and the complete reference pipeline under their stated timing scopes. RQ3 looks for descriptive relationships between input structure, checked operation counters, and runtime. These questions keep reconstruction, measurement, and interpretation separate. RQ1 is the main technical question. RQ2 reports measured behavior. RQ3 remains exploratory and does not claim a causal explanation.`,

  6: `The oracle, reference pipeline, and paper core play different roles. Before the paper call, the oracle checks the valid-input condition. After the call, the runner uses the oracle's sorted result as the expected answer. The reference pipeline intentionally consumes the complete oracle result, including that sorted output. The paper core receives only the original sequence under the certified precondition. It runs Step 1, Step 2, and Step 3, updates its partial order and sibling-list state, and returns the order recovered from that state. The dashed comparison box sits outside the paper core. Both methods are checked against the same expected answer, but they produce their outputs differently. This distinction lets me test the paper core without supplying the answer as input. The oracle-sorted list never enters the paper core and never determines its return value.`,

  7: `The reconstruction follows one control-flow skeleton. It first orders z one, z two, and z three, then initializes the partial order and the first upper and lower pairs. After that, each new point passes through Step 1, Step 2, and Step 3. Step 1 finds the predecessor boundary, which I call A sub i. Step 2 finds the successor boundary, B sub i. Step 3(a) inserts the new pair. Step 3(b) performs any required sibling-list split and ownership transfer. Step 3(c) inserts the new point into the maintained order. The increasing and decreasing cases share these stages. Their local roles are reflected. In an increasing iteration, Step 3(a) uses A sub i and Step 3(b) uses B sub i. A decreasing iteration swaps those uses. The 1990 paper states the increasing case, while the decreasing case follows by symmetry. Two operational details still need explicit rules in code: the geometric endpoint and the odd-index z one output anchor. The next two slides explain why those choices matter.`,

  8: `The first issue concerns the endpoint used in Step 3(c). Consider the valid prefix three, two, one, four. The acquired pair P two is stored in curve order as three, two. A mechanical reading might choose the second stored element, two, as the insertion anchor. That produces one, two, four, three, which is wrong on the axis. Curve order and axis order describe different things. The pair records traversal along the curve, while Step 3(c) needs the geometric extreme on the axis. Here the correct endpoint is three. Inserting four after three gives one, two, three, four. This is a representation issue, not a special case for these four numbers. The stored pair order follows the curve, so its second item does not always represent the required side of the current axis order. The increasing orientation uses the right geometric endpoint, and the decreasing orientation uses the left endpoint. I describe this as an executable clarification because the 1990 paper does not state it in this form. Without the clarification, valid examples fail.`,

  9: `The second issue is the odd-index z one case. The valid prefix here is one, two, three, four, six, seven, zero. During this decreasing iteration, the ordinary geometric base anchor is z two, with value two. Inserting zero directly before z two gives one, zero, two, three, four, six, seven. Z one remains on the wrong side of the new point. Zero is smaller than z one. Z one is also smaller than the original anchor. Therefore, the output anchor changes from z two to z one. Inserting zero before z one gives the correct order. The important point is that this change affects the output insertion only. It does not replace the earlier predecessor or successor boundary calculation. Those two decisions solve different problems. One selects the pair used by the family update. The other selects the point used to update the output order. The implementation records both decisions separately, which also makes the diagnostic trace easier to check.`,

  10: `Correct insertion also requires consistent ownership. Every finite pair has one parent and one sibling-list owner. Before a split, the existing owner controls both the retained and acquired segments. After the split, the existing owner keeps the retained segment, and the new owner receives the acquired segment. The split may create new lists for both nonempty sides, but only the acquired segment changes parent. The code treats the split and transfer as one transaction. It saves the affected state, performs the update, and checks the split boundary, ownership, and local postconditions. If a check fails, it restores the old registry, ownership links, and list identifiers. The maintained state also contains the sorted processed prefix and both pair families. Ordinary lists make scanning, copying, slicing, and ownership rebinding visible costs. These checks protect correctness, but they do not provide the update bounds used in the historical linear-time analysis.`,

  11: `I use four main checks for the implementation. Focused regression cases cover known edge conditions. Exhaustive validation runs all 2,074 oracle-valid permutations up to size eight. Checked-state audits inspect parent links, ownership, sibling lists, and recovered output. Deterministic replay runs the same core again and compares the resulting state. Replay checks consistency. It does not provide a second Jordan-sorting implementation. Separately, an experiment validation path checks that the saved outputs match the fixed setup and recomputed summaries. I keep the detailed archive checks in Backup C because the main research point here is the algorithm state. These checks support the evaluated cases, but they do not prove correctness for every Jordan sequence.`,

  12: `The formal experiment covers five sizes and twelve exact cases per size. It compares three algorithms. Each case-algorithm cell has five warm-up calls and twenty measured calls, producing 3,600 rows. These are repeated calls on the same exact case, not twenty independent inputs. Each call receives a fresh list containing the same values. The schedule rotates algorithm positions so that one method does not always run first. For the paper algorithm, oracle certification and the checked-state audit happen before timing. The minimal paper call runs inside the timer, including output recovery from the maintained order. The runner compares the returned output after timing. Python timing covers its sorting call. Reference timing covers the complete oracle-backed reference pipeline. Paper and reference therefore use different timing scopes, so their ratio is not an end-to-end speedup.`,

  13: `All 60 evaluated cases passed certification and the case-level checked-state audit. Every measured call returned the expected output, and the run recorded no correctness errors. The experiment used one audit per exact case. Its 3,600 timing rows carry the corresponding case-level audit result, so the row count does not mean 3,600 independent audits. These results support the tested valid cases only. They do not evaluate recognition of arbitrary inputs or prove correctness for every Jordan sequence.`,

  14: `The main runtime pattern is the decrease in the paper/reference ratio across the five tested sizes. I first compute the ratio for each exact case. Each case then has equal weight in the size-level median. The ratio is 3.226 at n equals 32, 2.202 at 64, and 1.351 at 128. It falls below one at 256, where it is 0.851, and reaches 0.567 at 512. The observed crossover lies between the tested sizes 128 and 256. Under these timing scopes, the recorded paper call is smaller than the reference-pipeline call at the two larger sizes. The scopes differ, so this pattern does not establish a general speedup. Five sizes also do not establish asymptotic behavior. Python sort, shown in Backup A, has the lowest median call time at every tested size.`,

  15: `The current evidence supports an executable ordinary-list reconstruction whose output comes from maintained state. It also supports correct output on the evaluated valid cases and a recorded runtime trend under the stated timing scopes. The main limits are equally important. Ordinary Python lists do not establish a linear-time implementation, and five tested sizes do not establish asymptotic complexity. Recognition was not evaluated. The paper/reference comparison still uses different timing scopes. I therefore present the runtime values as observations for this implementation and experiment, not as a general algorithmic bound.`,

  16: `A possible next step is to investigate a finger-tree backend while keeping the same Step 1, Step 2, and Step 3 behavior. The ordinary-list implementation gives a tested reference point for that work. The detailed backend boundary appears in Backup E, including the ownership-transfer difficulty. I would like guidance on two questions. First, should the extension target the historical heterogeneous finger tree, or an equivalent backend with the required list operations? Second, is a tested, semantically equivalent prototype enough, or should I also prove the required amortized operation bounds? The answer determines whether this stays an implementation experiment or also needs a complexity proof.`,

  17: `If exact runtimes are requested, this backup slide reports the median call times for all three algorithms. The values belong to one recorded Apple M4 and CPython 3.12.4 execution. The logarithmic scale makes the Python values visible beside the reference and paper values. These absolute times should not be generalized to other environments.`,

  18: `This slide answers the output-provenance question directly. The reference pipeline returns oracle_result sorted. The paper core returns state.partial_order.to_list. Certification precedes the paper call and comparison follows it, so neither operation supplies the paper core's return value.`,

  19: `This inventory summarizes the bounded validation evidence: repository tests, exhaustive valid permutations through size eight, fixed generated cases, formal case-level checked-state audits, and a formal evidence archive that passed evidence-contract validation. These checks are complementary; none is a universal proof.`,

  20: `This table summarizes the reflected local choices. Step 1 always selects the predecessor-side boundary A-i, and Step 2 always selects the successor-side boundary B-i. Step 3 reflects how those boundaries are used. Increasing iterations acquire the left split side and use the rightmost child and right endpoint; decreasing iterations mirror those choices.`,

  21: `This proposed boundary keeps the paper-facing Step 1, Step 2, and Step 3 control flow above a small sibling-list interface. The current ordinary-list backend remains the validated baseline. A finger-tree backend would be a separate implementation of the same semantic operations: singleton creation, boundary insertion, split, extreme-child access, ownership preservation, and stable handles. The exact data-structure target—either the historical heterogeneous finger tree or an equivalently efficient backend—remains to be agreed with the supervisor. The main risk is that efficient tree splitting is not enough by itself. If ownership transfer still scans the acquired segment and rebinds every item, the backend may not satisfy the operation bounds needed by the historical analysis. The first milestone is therefore semantic equivalence and differential correctness; any complexity claim requires a separate proof-level argument.`,
};

const TALK_TIMES = {
  1: "0:50", 2: "0:55", 3: "0:50", 4: "0:50", 5: "0:45", 6: "1:10", 7: "1:30", 8: "1:40",
  9: "1:25", 10: "1:25", 11: "1:00", 12: "1:10", 13: "0:40", 14: "1:20", 15: "0:45", 16: "0:55",
};

const TALK_TITLES = {
  1: "Progress on the Executable Reconstruction of Simplified Jordan Sorting",
  2: "The previous report established a static structural baseline",
  3: "Progress since the previous report",
  4: "Current scope: valid-input sorting",
  5: "Three questions connect reconstruction, measurement, and interpretation",
  6: "The oracle, reference pipeline, and paper core have distinct roles",
  7: "Step 1/2/3 control flow and reflected orientation",
  8: "Step 3(c) uses the geometric extreme, not the second stored endpoint",
  9: "Odd iterations require a separate z1 output-anchor correction",
  10: "Ownership-safe split and transfer",
  11: "Implementation checks and experiment consistency",
  12: "The formal experiment keeps certification and audit outside paper timing",
  13: "All 60 evaluated cases returned the correct output",
  14: "The paper/reference ratio decreases across the five tested sizes",
  15: "What the current evidence shows",
  16: "Possible next step: a finger-tree backend",
  17: "Backup A: Median runtime by size",
  18: "Backup B: Paper output provenance",
  19: "Backup C: Validation summary",
  20: "Backup D: Reflected local choices",
  21: "Backup E: Proposed finger-tree backend boundary",
};

function countWords(text) {
  return text.trim().split(/\s+/).filter(Boolean).length;
}

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

function addFooter(slide, pageLabel, backup = false) {
  addRule(slide, 64, 680, 1152, C.line, 1);
  addText(slide, backup ? "BACKUP" : "MASTER'S THESIS PROGRESS REPORT", 68, 686, 380, 20, {
    fontSize: 11,
    bold: true,
    color: backup ? C.coral : C.muted,
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

function baseSlide(presentation, title, section, pageLabel, backup = false) {
  const slide = presentation.slides.add();
  slide.background.fill = C.light;
  addText(slide, section.toUpperCase(), 66, 26, 360, 22, {
    fontSize: 12,
    bold: true,
    color: backup ? C.coral : C.teal,
    valign: "middle",
  });
  addText(slide, title, 64, 54, 1152, 55, {
    fontSize: 36,
    bold: true,
    color: C.navy,
    valign: "middle",
    lineSpacing: 0.95,
  });
  addRule(slide, 64, 114, 1152, backup ? C.coral : C.teal, 3);
  addFooter(slide, pageLabel, backup);
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
    const slide = baseSlide(presentation, "Step 1/2/3 control flow and reflected orientation", "Reconstruction", "7 / 16");
    const nodes = [
      { x: 86, y: 170, w: 184, h: 84, title: "Initialize", body: "order z₁, z₂, z₃" },
      { x: 310, y: 170, w: 184, h: 84, title: "Step 1", body: "predecessor-side boundary" },
      { x: 534, y: 170, w: 184, h: 84, title: "Step 2", body: "successor-side boundary" },
      { x: 758, y: 170, w: 184, h: 84, title: "Step 3(a)", body: "insert new pair" },
      { x: 982, y: 170, w: 184, h: 84, title: "Step 3(b)", body: "split + transfer" },
      { x: 500, y: 316, w: 280, h: 88, title: "Step 3(c)", body: "insert new point into maintained order" },
    ];
    const shapes = nodes.map((n) => {
      const s = addBox(slide, n.x, n.y, n.w, n.h, { fill: C.paleBlue, line: C.slate, lineWidth: 2, radius: 8 });
      addText(slide, n.title, n.x + 8, n.y + 10, n.w - 16, 30, { fontSize: 22, bold: true, color: C.navy, align: "center" });
      addText(slide, n.body, n.x + 10, n.y + 42, n.w - 20, n.h - 48, { fontSize: 16, color: C.ink, align: "center", valign: "middle" });
      return s;
    });
    for (let i = 0; i < 4; i++) slide.shapes.connect(shapes[i], shapes[i + 1], { kind: "straight", fromSide: "right", toSide: "left", line: { style: "solid", fill: C.slate, width: 2 }, tail: { type: "arrow", width: "med", length: "med" } });
    slide.shapes.connect(shapes[4], shapes[5], { kind: "elbow", fromSide: "bottom", toSide: "top", line: { style: "solid", fill: C.slate, width: 2 }, tail: { type: "arrow", width: "med", length: "med" } });
    const evidence = [
      { x: 82, color: C.navy, fill: C.paleBlue, title: "Explicit source rule", body: "Increasing Step 1/2/3 structure" },
      { x: 447, color: C.teal, fill: C.paleTeal, title: "Symmetric reconstruction", body: "Reflected decreasing orientation" },
      { x: 812, color: C.coral, fill: C.paleCoral, title: "Executable clarifications", body: "Geometric endpoint and odd-index z₁ anchor" },
    ];
    evidence.forEach((e) => {
      addBox(slide, e.x, 470, 326, 112, { fill: e.fill, line: e.color, lineWidth: 1.5, radius: 8 });
      addText(slide, e.title, e.x + 14, 484, 298, 30, { fontSize: 19, bold: true, color: e.color, align: "center" });
      addText(slide, e.body, e.x + 18, 526, 290, 42, { fontSize: 17, color: C.ink, align: "center", valign: "middle" });
    });
    setNotes(
      slide,
      "The reconstruction is not a line-by-line transcription. Some rules are explicit in the 1990 paper, the decreasing orientation is reconstructed by symmetry, and a small number of operational details must be fixed to obtain unambiguous executable behavior.",
      [
        `${REPO}/thesis/chapters/algorithm.tex`,
        `${REPO}/thesis/chapters/implementation.tex`,
        "Fung et al. (1990), doi:10.1016/0020-0190(90)90111-A",
      ],
    );
  }

  // 8. Endpoint semantics
  {
    const slide = baseSlide(presentation, "Step 3(c) uses the geometric extreme, not the second stored endpoint", "Reconstruction Issue I", "8 / 16");
    addText(slide, "Input prefix", 84, 156, 170, 30, { fontSize: 16, bold: true, color: C.muted });
    addText(slide, "(3, 2, 1, 4)", 84, 188, 280, 48, { fontSize: 32, bold: true, color: C.navy });
    addText(slide, "Acquired pair", 84, 254, 170, 30, { fontSize: 16, bold: true, color: C.muted });
    addText(slide, "P₂ = (3, 2)", 84, 286, 280, 48, { fontSize: 30, bold: true, color: C.coral });

    addRule(slide, 410, 252, 680, C.slate, 3);
    const points = [1, 2, 3, 4];
    points.forEach((p, i) => {
      const x = 430 + i * 205;
      slide.shapes.add({ geometry: "ellipse", position: { left: x, top: 232, width: 40, height: 40 }, fill: i === 1 ? C.paleCoral : i === 2 ? C.paleTeal : C.white, line: { style: "solid", fill: i === 1 ? C.coral : i === 2 ? C.teal : C.slate, width: 2 } });
      addText(slide, String(p), x, 234, 40, 36, { fontSize: 20, bold: true, color: C.navy, align: "center", valign: "middle" });
    });
    addText(slide, "stored direction 3 → 2", 720, 166, 250, 42, { fontSize: 20, bold: true, color: C.coral, align: "center" });
    addText(slide, "geometric axis", 646, 286, 260, 34, { fontSize: 16, color: C.muted, align: "center" });

    addBox(slide, 414, 358, 330, 154, { fill: C.paleCoral, line: C.coral, lineWidth: 2, radius: 8 });
    addText(slide, "Curve-order endpoint", 436, 374, 286, 34, { fontSize: 23, bold: true, color: C.coral, align: "center" });
    addText(slide, "anchor = 2\nresult: [1, 2, 4, 3]", 438, 418, 282, 70, { fontSize: 20, color: C.ink, align: "center", valign: "middle" });
    addBox(slide, 790, 358, 330, 154, { fill: C.paleTeal, line: C.teal, lineWidth: 2, radius: 8 });
    addText(slide, "Geometric endpoint", 812, 374, 286, 34, { fontSize: 23, bold: true, color: C.teal, align: "center" });
    addText(slide, "anchor = 3\nresult: [1, 2, 3, 4]", 814, 418, 282, 70, { fontSize: 20, color: C.ink, align: "center", valign: "middle" });
    addText(slide, "Executable rule: choose the geometric extreme.", 390, 558, 760, 48, { fontSize: 25, bold: true, color: C.teal, align: "center", valign: "middle" });
    addText(slide, "Recorded as a reconstruction clarification, not as a verbatim 1990-paper rule.", 390, 610, 760, 34, { fontSize: 17, color: C.slate, align: "center", valign: "middle" });
    setNotes(
      slide,
      "A pair is stored in curve order, but Step 3(c) needs a geometric boundary. These are not always the same endpoint. A mechanical interpretation of the second stored endpoint produces an incorrect order on this valid example. The executable reconstruction therefore selects the geometric extreme.",
      [
        `${REPO}/thesis/chapters/algorithm.tex`,
        `${REPO}/src/paper_jordan.py`,
      ],
    );
  }

  // 9. z1 anomaly
  {
    const slide = baseSlide(presentation, "Odd iterations require a separate z₁ output-anchor correction", "Reconstruction Issue II", "9 / 16");
    addBox(slide, 72, 150, 760, 196, { fill: C.white, line: C.coral, lineWidth: 1.5, radius: 8 });
    addText(slide, "Ordinary geometric base anchor = z₂ = 2", 96, 168, 712, 34, { fontSize: 23, bold: true, color: C.coral });
    addText(slide, "new point 0", 106, 230, 142, 34, { fontSize: 20, bold: true, color: C.navy, align: "center" });
    addText(slide, "→", 248, 226, 62, 38, { fontSize: 28, bold: true, color: C.coral, align: "center" });
    addText(slide, "insert before 2", 312, 230, 170, 34, { fontSize: 20, bold: true, color: C.coral, align: "center" });
    addText(slide, "→", 482, 226, 62, 38, { fontSize: 28, bold: true, color: C.coral, align: "center" });
    addText(slide, "1, 0, 2, 3, 4, 6, 7", 548, 230, 246, 34, { fontSize: 21, bold: true, color: C.ink, align: "center" });
    addText(slide, "z₁ = 1 remains on the wrong side of the new point.", 116, 290, 670, 34, { fontSize: 19, color: C.slate, align: "center" });

    addBox(slide, 72, 372, 760, 196, { fill: C.paleTeal, line: C.teal, lineWidth: 2, radius: 8 });
    addText(slide, "Corrected output anchor = z₁ = 1", 96, 390, 712, 34, { fontSize: 23, bold: true, color: C.teal });
    addText(slide, "new point 0", 106, 452, 142, 34, { fontSize: 20, bold: true, color: C.navy, align: "center" });
    addText(slide, "→", 248, 448, 62, 38, { fontSize: 28, bold: true, color: C.teal, align: "center" });
    addText(slide, "insert before z₁", 312, 452, 170, 34, { fontSize: 20, bold: true, color: C.teal, align: "center" });
    addText(slide, "→", 482, 448, 62, 38, { fontSize: 28, bold: true, color: C.teal, align: "center" });
    addText(slide, "0, 1, 2, 3, 4, 6, 7", 548, 452, 246, 34, { fontSize: 21, bold: true, color: C.ink, align: "center" });
    addText(slide, "The maintained partial order now matches the geometric axis order.", 116, 512, 670, 34, { fontSize: 19, color: C.slate, align: "center" });

    addBox(slide, 870, 160, 330, 164, { fill: C.white, line: C.line, radius: 8 });
    addText(slide, "Valid prefix", 892, 178, 286, 26, { fontSize: 16, bold: true, color: C.muted });
    addText(slide, "(1, 2, 3, 4, 6, 7, 0)", 892, 210, 286, 52, { fontSize: 21, bold: true, color: C.navy, align: "center", valign: "middle" });
    addText(slide, "0 < z₁ < 2", 892, 268, 286, 38, { fontSize: 27, bold: true, color: C.coral, align: "center", valign: "middle" });
    addBox(slide, 870, 372, 330, 174, { fill: C.white, line: C.teal, lineWidth: 1.5, radius: 8 });
    addText(slide, "Two separate decisions", 892, 390, 286, 34, { fontSize: 22, bold: true, color: C.teal, align: "center" });
    addText(slide, "boundary-pair selection\n≠\noutput-anchor selection", 900, 432, 270, 92, { fontSize: 19, color: C.ink, align: "center", valign: "middle" });
    addText(slide, "This correction is separate from predecessor/successor boundary selection.", 864, 580, 342, 58, { fontSize: 18, bold: true, color: C.navy, align: "center", valign: "middle" });
    setNotes(
      slide,
      "The special role of the first point is not completely handled by predecessor and successor boundary selection. On certain odd iterations, the final output anchor must be adjusted to z1. Treating these as two separate corrections was necessary to make the reconstructed state correct.",
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
    addText(slide, "Local split and ownership transfer", 94, 170, 606, 38, { fontSize: 25, bold: true, color: C.navy, align: "center" });

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
    addBulletList(slide, ["sorted processed prefix", "upper and lower pair families", "one parent per finite pair", "one sibling-list owner per finite pair"], 770, 205, 410, { fontSize: 19, gap: 45 });
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
    addText(slide, "IMPLEMENTATION AND STATE VALIDATION", 92, 158, 450, 28, { fontSize: 15, bold: true, color: C.teal });
    addText(slide, "EXPERIMENT OUTPUT CHECK", 728, 158, 450, 28, { fontSize: 15, bold: true, color: C.coral });
    const left = ["Focused regression cases", "Bounded exhaustive validation\n2,074 oracle-valid permutations, n ≤ 8", "Checked-state audits", "Same-core deterministic replay"];
    const ys = [202, 294, 402, 494];
    for (let i = 0; i < 4; i++) {
      addBox(slide, 88, ys[i], 470, i === 1 ? 82 : 64, { fill: C.paleTeal, line: C.teal, radius: 7 });
      addText(slide, left[i], 104, ys[i] + 8, 438, i === 1 ? 66 : 48, { fontSize: i === 1 ? 18 : 20, bold: i === 1, color: C.ink, align: "center", valign: "middle" });
      if (i < 3) {
        addText(slide, "↓", 286, ys[i] + (i === 1 ? 79 : 61), 72, 28, { fontSize: 26, bold: true, color: C.teal, align: "center" });
      }
    }
    addBox(slide, 722, 232, 470, 250, { fill: C.paleCoral, line: C.coral, lineWidth: 1.5, radius: 8 });
    addText(slide, "A separate validation path checked that the saved outputs match the fixed experiment setup and recomputed summaries.", 758, 282, 398, 142, { fontSize: 23, bold: true, color: C.ink, align: "center", valign: "middle" });
    addText(slide, "Full consistency checks: Backup C", 760, 506, 394, 34, { fontSize: 17, color: C.slate, align: "center", valign: "middle" });
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
    const slide = baseSlide(presentation, "The formal experiment keeps certification and audit outside paper timing", "Experimental Method", "12 / 16");
    addBox(slide, 76, 148, 1128, 82, { fill: C.navy, line: C.navy, radius: 8 });
    addText(slide, "5 sizes  ×  12 cases  ×  3 algorithms  ×  20 calls", 98, 158, 728, 54, { fontSize: 23, bold: true, color: C.white, align: "center", valign: "middle" });
    addText(slide, "3,600 measured rows", 850, 158, 326, 54, { fontSize: 25, bold: true, color: C.teal, align: "center", valign: "middle" });

    const stages = ["Generate", "Certify", "Checked-state\naudit", "Warm-up", "Measure", "Aggregate", "Validate\nand archive"];
    const stageShapes = stages.map((stage, i) => {
      const x = 74 + i * 164;
      const timed = stage === "Measure";
      const s = addBox(slide, x, 278, 136, 82, { fill: timed ? C.paleCoral : C.white, line: timed ? C.coral : C.slate, lineWidth: timed ? 2 : 1.5, radius: 7 });
      addText(slide, stage, x + 8, 290, 120, 58, { fontSize: stage.startsWith("Checked") ? 15 : 18, bold: true, color: timed ? C.coral : C.navy, align: "center", valign: "middle" });
      return s;
    });
    for (let i = 0; i < stageShapes.length - 1; i++) {
      slide.shapes.connect(stageShapes[i], stageShapes[i + 1], { kind: "straight", fromSide: "right", toSide: "left", line: { style: "solid", fill: C.slate, width: 1.6 }, tail: { type: "arrow", width: "sm", length: "sm" } });
    }

    const scopes = [
      { x: 76, fill: C.paleTeal, line: C.teal, title: "Certification outside paper timing", body: "valid-input precondition" },
      { x: 446, fill: C.paleTeal, line: C.teal, title: "Checked-state audit outside paper timing", body: "one audit per exact case" },
      { x: 816, fill: C.paleCoral, line: C.coral, title: "Minimal paper call inside timing", body: "output recovery remains timed" },
    ];
    scopes.forEach((s) => {
      addBox(slide, s.x, 410, 338, 104, { fill: s.fill, line: s.line, lineWidth: 1.5, radius: 8 });
      addText(slide, s.title, s.x + 16, 424, 306, 42, { fontSize: 18, bold: true, color: s.line, align: "center", valign: "middle" });
      addText(slide, s.body, s.x + 18, 472, 302, 28, { fontSize: 17, color: C.ink, align: "center", valign: "middle" });
    });
    addText(slide, "Reference timing includes its complete oracle-backed pipeline. Python timing covers its complete sorting call.", 120, 538, 1040, 32, { fontSize: 18, color: C.slate, align: "center", valign: "middle" });
    addBox(slide, 212, 586, 856, 52, { fill: C.paleCoral, line: C.coral, lineWidth: 1.5, radius: 6 });
    addText(slide, "Paper and reference use different timing scopes, so this ratio is not an end-to-end speedup.", 230, 592, 820, 40, { fontSize: 18, bold: true, color: C.coral, align: "center", valign: "middle" });
    setNotes(
      slide,
      "Each exact case is generated once, oracle-certified, structurally profiled, and checked once before timing. The paper call is timed only after certification. The reference call includes its full oracle-backed workflow. This difference is deliberate and must remain visible when interpreting the ratio.",
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
    const slide = baseSlide(presentation, "All 60 evaluated cases returned the correct output", "Results", "13 / 16");
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

  // 14. Runtime chart
  {
    const slide = baseSlide(presentation, "The paper/reference ratio decreases across the five tested sizes", "Results", "14 / 16");
    slide.charts.add("line", {
      position: { left: 68, top: 148, width: 720, height: 430 },
      categories: ["32", "64", "128", "256", "512"],
      series: [
        { name: "paper/reference", values: [3.22642, 2.202394, 1.351064, 0.850597, 0.567187], line: { style: "solid", fill: C.teal, width: 4 }, marker: { symbol: "circle", size: 9 } },
        { name: "ratio = 1", values: [1, 1, 1, 1, 1], line: { style: "dashed", fill: C.coral, width: 2 }, marker: { symbol: "none" } },
      ],
      hasLegend: true,
      legend: { position: "bottom", overlay: false, textStyle: { fill: C.slate, fontSize: 15 } },
      lineOptions: { grouping: "standard", smooth: false },
      chartFill: C.white,
      chartLine: { style: "solid", fill: C.line, width: 1 },
      plotAreaFill: C.white,
      plotAreaLine: { style: "solid", fill: C.line, width: 1 },
      xAxis: { title: { text: "input size n", textStyle: { fill: C.slate, fontSize: 15 } }, textStyle: { fill: C.slate, fontSize: 15 }, line: { style: "solid", fill: C.line, width: 1 }, majorGridlines: null },
      yAxis: { title: { text: "median exact-case ratio", textStyle: { fill: C.slate, fontSize: 15 } }, min: 0, max: 3.5, majorUnit: 0.5, numberFormatCode: "0.0", textStyle: { fill: C.slate, fontSize: 14 }, line: { style: "solid", fill: C.line, width: 1 }, majorGridlines: { style: "solid", fill: "#E6EDF3", width: 1 } },
    });
    addBox(slide, 830, 160, 350, 104, { fill: C.paleTeal, line: C.teal, radius: 8 });
    addText(slide, "3.226", 850, 172, 126, 54, { fontSize: 38, bold: true, color: C.teal, align: "center" });
    addText(slide, "at n = 32", 980, 184, 176, 34, { fontSize: 20, color: C.ink, valign: "middle" });
    addBox(slide, 830, 282, 350, 104, { fill: C.paleCoral, line: C.coral, radius: 8 });
    addText(slide, "0.567", 850, 294, 126, 54, { fontSize: 38, bold: true, color: C.coral, align: "center" });
    addText(slide, "at n = 512", 980, 306, 176, 34, { fontSize: 20, color: C.ink, valign: "middle" });
    addBox(slide, 830, 418, 350, 112, { fill: C.white, line: C.navy, lineWidth: 1.5, radius: 8 });
    addText(slide, "Observed crossover", 850, 432, 310, 34, { fontSize: 24, bold: true, color: C.navy, align: "center" });
    addText(slide, "between tested sizes 128 and 256", 852, 476, 306, 38, { fontSize: 19, color: C.ink, align: "center", valign: "middle" });
    addBox(slide, 820, 566, 372, 68, { fill: C.navy, line: C.navy, radius: 6 });
    addText(slide, "five sizes  |  ordinary lists  |  different timed scopes", 838, 576, 336, 48, { fontSize: 17, bold: true, color: C.white, align: "center", valign: "middle" });
    setNotes(
      slide,
      "Under the fixed scopes, the median paper/reference ratio decreases over the five tested sizes. It is above one through n equals 128 and below one at 256 and 512. This means that the measured paper call is smaller than the measured reference call for the larger tested cases. It does not establish an end-to-end speedup or an asymptotic result.",
      [
        `${REPO}/thesis/chapters/results.tex`,
        `${REPO}/results/runs/week12_formal_sorting_v1__run001/case_summary.csv`,
        `${REPO}/docs/analysis/week12_runtime_ratios.csv`,
      ],
    );
  }

  // 15. Interpretation boundaries
  {
    const slide = baseSlide(presentation, "What the current evidence shows", "Interpretation", "15 / 16");
    addBox(slide, 78, 152, 536, 404, { fill: C.paleTeal, line: C.teal, lineWidth: 2, radius: 8 });
    addBox(slide, 666, 152, 536, 404, { fill: C.paleCoral, line: C.coral, lineWidth: 2, radius: 8 });
    addText(slide, "Current results", 106, 178, 480, 52, { fontSize: 26, bold: true, color: C.teal, align: "center", valign: "middle" });
    addText(slide, "Main limits", 694, 178, 480, 52, { fontSize: 26, bold: true, color: C.coral, align: "center", valign: "middle" });
    addBulletList(slide, ["Executable reconstruction with output recovered from maintained state", "Correct outputs and a recorded runtime trend for the evaluated cases"], 112, 270, 456, { fontSize: 22, gap: 132, bulletColor: C.teal });
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

  // Backup A: full runtime table
  {
    const slide = baseSlide(presentation, "Median runtime by size under the recorded call scopes", "Backup A", "A", true);
    addImage(slide, imgs.runtime, "Median exact-case runtime by input size", 66, 164, 720, 408, { fit: "contain" });
    addBox(slide, 66, 164, 720, 50, { fill: C.white, line: C.white, geometry: "rect", radius: 0 });
    addBox(slide, 630, 216, 152, 118, { fill: C.white, line: C.white, geometry: "rect", radius: 0 });
    addRule(slide, 646, 238, 24, C.green, 3);
    addText(slide, "Python sort", 680, 225, 94, 28, { fontSize: 13, color: C.ink, valign: "middle" });
    addRule(slide, 646, 274, 24, "#2E75B6", 3);
    addText(slide, "Reference pipeline", 680, 261, 98, 28, { fontSize: 13, color: C.ink, valign: "middle" });
    addRule(slide, 646, 310, 24, C.coral, 3);
    addText(slide, "Paper ordinary-list core", 680, 297, 98, 32, { fontSize: 12, color: C.ink, valign: "middle" });
    const rows = [
      ["n", "Python (ms)", "Reference (ms)", "Paper (ms)"],
      ["32", "0.000791", "0.181177", "0.586906"],
      ["64", "0.001417", "0.585667", "1.282198"],
      ["128", "0.002635", "2.077959", "2.815083"],
      ["256", "0.005208", "7.929646", "6.721250"],
      ["512", "0.010584", "33.014458", "18.716687"],
    ];
    const x0 = 816;
    const widths = [70, 112, 128, 112];
    let y = 172;
    rows.forEach((row, ri) => {
      let x = x0;
      row.forEach((cell, ci) => {
        const fill = ri === 0 ? C.navy : ri % 2 === 0 ? C.paleBlue : C.white;
        addBox(slide, x, y, widths[ci], 55, { fill, line: C.line, geometry: "rect", radius: 0 });
        addText(slide, cell, x + 2, y + 4, widths[ci] - 4, 47, { fontSize: ri === 0 ? 14 : 16, bold: ri === 0, color: ri === 0 ? C.white : C.ink, align: "center", valign: "middle" });
        x += widths[ci];
      });
      y += 55;
    });
    addText(slide, "Absolute times belong to one recorded Apple M4 / CPython 3.12.4 execution.", 824, 534, 410, 58, { fontSize: 17, color: C.slate, align: "center", valign: "middle" });
    setNotes(slide, "Use this table only if exact runtime values are requested. Emphasize that the vertical scales and timed scopes differ and that Python sort remains the lowest median call time.", [`${REPO}/thesis/chapters/results.tex`, `${REPO}/results/runs/week12_formal_sorting_v1__run001/case_summary.csv`]);
  }

  // Backup B: provenance
  {
    const slide = baseSlide(presentation, "Paper output is recovered from state, not from the oracle result", "Backup B", "B", true);
    addBox(slide, 102, 162, 430, 374, { fill: C.paleCoral, line: C.coral, lineWidth: 2, radius: 8 });
    addBox(slide, 748, 162, 430, 374, { fill: C.paleTeal, line: C.teal, lineWidth: 2, radius: 8 });
    addText(slide, "Reference pipeline", 130, 188, 374, 42, { fontSize: 28, bold: true, color: C.coral, align: "center" });
    addText(slide, "oracle_result[\"sorted\"]", 130, 270, 374, 58, { fontSize: 25, bold: true, color: C.navy, align: "center", valign: "middle" });
    addText(slide, "Oracle validation, structure, trace, and serializable result assembly are part of the reference call.", 150, 360, 334, 106, { fontSize: 19, color: C.ink, align: "center", valign: "middle" });
    addText(slide, "Paper core", 776, 188, 374, 42, { fontSize: 28, bold: true, color: C.teal, align: "center" });
    addText(slide, "state.partial_order.to_list()", 776, 270, 374, 58, { fontSize: 23, bold: true, color: C.navy, align: "center", valign: "middle" });
    addText(slide, "Certification precedes the call. Output comparison follows it. Neither provides the paper core's return value.", 796, 352, 334, 122, { fontSize: 19, color: C.ink, align: "center", valign: "middle" });
    addText(slide, "Same expected answer, different output provenance.", 230, 590, 820, 44, { fontSize: 25, bold: true, color: C.navy, align: "center", valign: "middle" });
    setNotes(slide, "Show this slide if asked whether the paper core is only a wrapper around the oracle. The outer certification wrapper and the post-call comparison are deliberately separate from the paper core's output construction.", [`${REPO}/thesis/chapters/implementation.tex`, `${REPO}/src/paper_jordan.py`, `${REPO}/src/simplified_jordan.py`]);
  }

  // Backup C: validation inventory
  {
    const slide = baseSlide(presentation, "Validation summary for the current implementation baseline", "Backup C", "C", true);
    const items = [
      ["537", "repository tests"],
      ["2,074", "bounded exhaustive valid permutations, n ≤ 8"],
      ["48", "fixed generated cases"],
      ["60", "formal case-level checked-state audits"],
      ["passed", "formal evidence-contract validation"],
    ];
    items.forEach((it, i) => {
      const y = 158 + i * 88;
      addText(slide, it[0], 104, y, 250, 60, { fontSize: i === 4 ? 34 : 42, bold: true, color: i % 2 === 0 ? C.teal : C.coral, align: "right", valign: "middle" });
      addBox(slide, 386, y + 12, 4, 36, { fill: i % 2 === 0 ? C.teal : C.coral, line: i % 2 === 0 ? C.teal : C.coral, geometry: "rect", radius: 0 });
      addText(slide, it[1], 420, y, 720, 60, { fontSize: 23, color: C.ink, valign: "middle" });
    });
    addBox(slide, 196, 610, 888, 48, { fill: C.paleCoral, line: C.coral, radius: 6 });
    addText(slide, "Finite validation evidence is not a proof for every Jordan sequence.", 216, 614, 848, 40, { fontSize: 20, bold: true, color: C.coral, align: "center", valign: "middle" });
    setNotes(slide, "Use this inventory only if the audience asks for test counts. The main presentation focuses on the validation logic because raw test totals can be mistaken for independent proofs.", [`${REPO}/docs/thesis/latex_final_audit.md`, `${REPO}/experiments/validate_paper_algorithm.py`, `${REPO}/results/runs/week12_formal_sorting_v1__run001/validation_report.json`]);
  }

  // Backup D: reflection table
  {
    const slide = baseSlide(presentation, "Increasing and decreasing iterations use reflected local choices", "Backup D", "D", true);
    const headers = ["Control choice", "Increasing orientation", "Decreasing orientation"];
    const body = [
      ["Step 3(a) boundary", "predecessor-side (Aᵢ)", "successor-side (Bᵢ)"],
      ["Boundary insertion", "after last sibling", "before first sibling"],
      ["Step 3(b) boundary", "successor-side (Bᵢ)", "predecessor-side (Aᵢ)"],
      ["Acquired split side", "left", "right"],
      ["Child extreme", "rightmost child", "leftmost child"],
      ["Geometric anchor", "right endpoint", "left endpoint"],
      ["Output insertion", "after anchor", "before anchor"],
    ];
    const x = [92, 440, 786];
    const widths = [348, 346, 394];
    headers.forEach((h, i) => {
      addBox(slide, x[i], 154, widths[i], 52, { fill: i === 0 ? C.navy : i === 1 ? C.paleTeal : C.paleCoral, line: C.line, geometry: "rect", radius: 0 });
      addText(slide, h, x[i] + 8, 160, widths[i] - 16, 40, { fontSize: 19, bold: true, color: i === 0 ? C.white : i === 1 ? C.teal : C.coral, align: "center", valign: "middle" });
    });
    body.forEach((row, ri) => {
      row.forEach((cell, ci) => {
        const y = 206 + ri * 54;
        addBox(slide, x[ci], y, widths[ci], 54, { fill: ri % 2 === 0 ? C.white : "#F0F4F8", line: C.line, geometry: "rect", radius: 0 });
        addText(slide, cell, x[ci] + 8, y + 6, widths[ci] - 16, 42, { fontSize: 17, bold: ci === 0, color: C.ink, align: "center", valign: "middle" });
      });
    });
    addText(slide, "Step 1 always selects Aᵢ and Step 2 always selects Bᵢ; Step 3 reflects how those boundaries are used.", 120, 602, 1040, 42, { fontSize: 18, bold: true, color: C.navy, align: "center", valign: "middle" });
    setNotes(slide, "Use this table if asked how one implementation supports both orientations. The table is a compact reconstruction summary, not a verbatim table from the source paper.", [`${REPO}/thesis/chapters/algorithm.tex`, `${REPO}/thesis/chapters/implementation.tex`, "Fung et al. (1990), doi:10.1016/0020-0190(90)90111-A"]);
  }

  // Backup E: proposed finger-tree backend boundary
  {
    const slide = baseSlide(presentation, "Proposed finger-tree backend boundary", "Backup E", "E", true);
    const stepBox = addBox(slide, 94, 160, 290, 72, { fill: C.paleTeal, line: C.teal, lineWidth: 1.5, radius: 8 });
    addText(slide, "Paper Step 1/2/3", 108, 174, 262, 44, { fontSize: 22, bold: true, color: C.navy, align: "center", valign: "middle" });
    const interfaceBox = addBox(slide, 500, 148, 686, 96, { fill: C.white, line: C.navy, lineWidth: 1.5, radius: 8 });
    addText(slide, "Sibling-list backend interface", 520, 156, 646, 36, { fontSize: 22, bold: true, color: C.navy, align: "center", valign: "middle" });
    addText(slide, "make singleton • insert at left/right boundary • split at new-point value\naccess first/last child • preserve ownership and stable handles", 524, 194, 638, 42, { fontSize: 14, color: C.slate, align: "center", valign: "middle" });

    const ordinaryBox = addBox(slide, 92, 352, 500, 182, { fill: C.paleTeal, line: C.teal, lineWidth: 1.5, radius: 8 });
    const fingerBox = addBox(slide, 688, 352, 500, 182, { fill: C.paleCoral, line: C.coral, lineWidth: 1.5, radius: 8 });
    addText(slide, "Ordinary-list backend", 122, 370, 440, 40, { fontSize: 26, bold: true, color: C.teal, align: "center", valign: "middle" });
    addText(slide, "CURRENT VALIDATED BASELINE", 122, 414, 440, 42, { fontSize: 23, bold: true, color: C.navy, align: "center", valign: "middle" });
    addText(slide, "ordinary Python lists\narchived correctness and timing evidence", 142, 462, 400, 54, { fontSize: 19, color: C.ink, align: "center", valign: "middle" });
    addText(slide, "Finger-tree backend", 718, 370, 440, 40, { fontSize: 26, bold: true, color: C.coral, align: "center", valign: "middle" });
    addText(slide, "PROPOSED EXTENSION", 718, 414, 440, 42, { fontSize: 23, bold: true, color: C.navy, align: "center", valign: "middle" });
    addText(slide, "semantic-equivalence target\nnew validation and experiment version", 738, 462, 400, 54, { fontSize: 19, color: C.ink, align: "center", valign: "middle" });
    addText(slide, "Efficient tree splitting alone is insufficient if ownership transfer still scans and\nrebinds every item.", 174, 570, 932, 64, { fontSize: 25, bold: true, color: C.navy, align: "center", valign: "middle" });

    slide.shapes.connect(stepBox, interfaceBox, { kind: "straight", fromSide: "right", toSide: "left", line: { style: "solid", fill: C.teal, width: 2 }, tail: { type: "arrow", width: "med", length: "med" } });
    slide.shapes.connect(interfaceBox, ordinaryBox, { kind: "elbow", fromSide: "bottom", toSide: "top", line: { style: "solid", fill: C.teal, width: 2 }, tail: { type: "arrow", width: "med", length: "med" } });
    slide.shapes.connect(interfaceBox, fingerBox, { kind: "elbow", fromSide: "bottom", toSide: "top", line: { style: "solid", fill: C.coral, width: 2 }, tail: { type: "arrow", width: "med", length: "med" } });
    setNotes(slide, TALK[21], [`${REPO}/thesis/chapters/implementation.tex`, `${REPO}/thesis/chapters/limitations.tex`, "Fung et al. (1990), doi:10.1016/0020-0190(90)90111-A", "Supervisor feedback, September 2026"]);
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
  const mainWordCount = Array.from({ length: 16 }, (_, index) => countWords(TALK[index + 1])).reduce((a, b) => a + b, 0);
  const mainScript = Array.from({ length: 16 }, (_, index) => {
    const slideNumber = index + 1;
    return [
      `SLIDE ${slideNumber} | TARGET ${TALK_TIMES[slideNumber]} | ${countWords(TALK[slideNumber])} WORDS`,
      TALK_TITLES[slideNumber],
      "",
      TALK[slideNumber],
    ].join("\n");
  }).join("\n\n============================================================\n\n");
  const qaScript = Array.from({ length: 5 }, (_, index) => {
    const slideNumber = index + 17;
    return [
      `SLIDE ${slideNumber} | Q&A ONLY`,
      TALK_TITLES[slideNumber],
      "",
      TALK[slideNumber],
    ].join("\n");
  }).join("\n\n------------------------------------------------------------\n\n");
  const scriptDocument = [
    "JORDAN SORTING MASTER'S THESIS PROGRESS REPORT",
    "FULL SPEAKER SCRIPT",
    "",
    `Main presentation word count: ${mainWordCount}`,
    "Target duration: 18.5-20 minutes, including slide transitions and brief pauses.",
    "Recommended delivery: approximately 105-110 words per minute, with brief pauses for slide transitions and figure explanation.",
    "Slides 17-21 are Q&A material and are not included in the main word count.",
    "",
    "============================================================",
    "MAIN PRESENTATION: SLIDES 1-16",
    "============================================================",
    "",
    mainScript,
    "",
    "============================================================",
    "Q&A NOTES: SLIDES 17-21",
    "============================================================",
    "",
    qaScript,
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
