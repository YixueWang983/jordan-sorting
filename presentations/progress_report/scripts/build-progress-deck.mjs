import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { Presentation, PresentationFile } from "@oai/artifact-tool";

const SCRIPT_DIR = path.dirname(fileURLToPath(import.meta.url));
const PRESENTATION_DIR = path.resolve(SCRIPT_DIR, "..");
const REPO = path.resolve(PRESENTATION_DIR, "../..");
const BUILD = path.join(PRESENTATION_DIR, "build");
const OUT = path.join(PRESENTATION_DIR, "Jordan_Sorting_Progress_Report.pptx");
const SCRIPT_OUT = path.join(PRESENTATION_DIR, "Jordan_Sorting_Progress_Report_Speaker_Script.txt");

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
  1: `Good afternoon. This presentation gives an update on my master's thesis on the executable reconstruction of Simplified Jordan Sorting. In the previous seminar report, I focused mainly on the structural framework: rank intervals, upper and lower pair families, family trees, and an oracle-backed reference implementation. The central question since then has been whether the dynamic procedure described in the paper can be turned into an executable and auditable implementation using ordinary Python lists. Today I will show how that gap was addressed, how correctness and evidence integrity were checked, and what the formal experiment shows under clearly defined timing scopes.`,

  2: `The previous report established a useful static baseline. It represented the input by rank intervals, separated the upper and lower pair families, reconstructed their laminar family trees, and computed structural metrics. It also used an oracle to validate inputs and to provide a reference output. That framework explained why intervals within each family are nested or disjoint, but it did not yet execute the dynamic Jordan-sorting procedure. In particular, it did not maintain the processed prefix while new points were inserted, split sibling lists or transfer ownership, or recover the final output from the algorithm's own maintained state. So the main gap was not another static data model. It was the transition from a structural description to a sequence of safe dynamic updates.`,

  3: `I organized that transition into four connected work packages. First, I stabilized the scope by separating valid-input sorting from recognition and from the specialized backend required for the historical linear-time bound. Second, I reconstructed the paper-facing Step 1, Step 2, and Step 3 control flow as executable code. Third, I added state invariants, ownership checks, transactional updates, deterministic replay, and bounded validation. Fourth, only after the implementation and validation boundaries were stable, I carried out an initial formal evaluation under a pre-specified protocol. The result is a stable implementation baseline using ordinary lists. The distinction is important: this is an executable reconstruction of the control flow, not an implementation of the specialized data structures required for the historical linear-time bound.`,

  4: `The scope changed in a deliberate way as the implementation became more precise. Earlier planning combined several adjacent questions: generation of valid and invalid inputs, static family trees, recognition, a broad reference evaluation, and possible work on the theoretical backend. The current research scope is narrower and technically clearer. The thesis reconstructs the 1990 sorting procedure for inputs that have already been certified as valid. It compares three concrete calls: Python sort, the complete oracle-backed reference pipeline, and the reconstructed paper core. Recognition remains outside the formal experiment, and the backend remains ordinary Python lists. This refinement keeps the study focused on a single, defensible implementation and evaluation question. This ordinary-list implementation remains the validated baseline. Following the supervisor's suggestion, I am also investigating whether the sibling-list representation can be replaced by a finger-tree backend without changing the paper-facing control flow.`,

  5: `This leads to three research questions. The first, and primary technical question, is whether an ordinary-list reconstruction can recover the correct sorted order from its own maintained state for oracle-certified valid inputs. The second question concerns observed runtime behavior: how does the paper core, when called on a pre-certified input, behave relative to Python sort and the complete reference pipeline under the timing scope defined for each call? The third question is exploratory. It asks which descriptive relationships appear between input structure, checked operation counters, and runtime. These distinctions matter throughout the presentation. The first question is about executable reconstruction and bounded correctness evidence. The second is about measurements under different timing scopes, not a general performance claim. The third is descriptive rather than causal.`,

  6: `Before discussing the control flow, I need to separate the roles of the oracle, the reference pipeline, and the paper core. The oracle has two external roles. Before the paper call, it establishes the valid-input precondition. After the call, its expected sorted order is used for comparison. By contrast, the reference pipeline intentionally uses the complete oracle result, including the sorted output, together with family trees and structural information. The ordinary-list paper core receives the original sequence under a certified precondition. It runs Step 1, Step 2, and Step 3, maintains its own partial sorted order and sibling-list state, and returns the order reconstructed from that state. The dashed box on the right is deliberately outside the core: output comparison happens only after the call. Therefore, the expected answer is shared, but the output provenance is not. The oracle-derived sorted list is never passed into the paper core and never determines its return value. This lets correctness be checked without giving the implementation its answer.`,

  7: `The executable reconstruction has one main control-flow skeleton. After ordering the first three points, every new point is processed through Step 1, Step 2, and Step 3. Step 1 identifies the predecessor-side boundary. Step 2 identifies the successor-side boundary. Step 3(a) inserts the new pair, Step 3(b) performs any required sibling-list split and ownership transfer, and Step 3(c) inserts the new point into the maintained sorted order. Step 1 always computes the predecessor-side boundary A-i, and Step 2 always computes the successor-side boundary B-i. The reflection appears in Step 3: an increasing iteration uses A-i for Step 3(a) and B-i for Step 3(b), while a decreasing iteration uses them in the opposite roles. The evidence categories are shown separately below. The 1990 paper explicitly describes the increasing case, while the decreasing case is reconstructed by reflection. Two local details require executable clarification: selecting the geometric endpoint and handling the odd-index z-one output anchor. This distinction makes clear what is directly stated, what is symmetric reconstruction, and what is an operational clarification.`,

  8: `The first clarification concerns the endpoint used in Step 3(c). Consider the valid prefix shown here: three, two, one, four. The acquired pair is P-two, stored as the curve-order pair three, two. A mechanical reading might treat the second stored element, two, as the insertion anchor. That choice produces one, two, four, three, which is not sorted on the axis. The reason is that curve order and axis order are different concepts. The pair is stored according to traversal along the curve, while Step 3(c) needs the geometric extreme on the axis. For this example, the correct geometric endpoint is three, and inserting four after three produces the correct order: one, two, three, four. In the reflected control flow, the orientation determines which geometric extreme is used: the increasing case uses the right endpoint, while the decreasing case uses the left endpoint. That is different from asking which element happens to appear second in the stored pair. The executable rule is therefore to choose the geometric extreme, not simply the second stored endpoint. I treat this as a reconstruction clarification rather than attributing the rule directly to the 1990 paper. Without it, the maintained order fails on valid inputs.`,

  9: `The second clarification is the odd-index z-one anomaly. Here the valid prefix is one, two, three, four, six, seven, zero. On this decreasing iteration, the ordinary geometric base anchor is z-two, whose value is two. If the new point zero is inserted immediately before that anchor, the result is one, zero, two, three, four, six, seven. That leaves z-one, whose value is one, on the wrong side of the new point. Here, zero is smaller than z-one, which is smaller than the original anchor. Under this odd-index condition, the required correction changes the output anchor from z-two to z-one. Inserting zero before z-one gives the correct axis order: zero, one, two, three, four, six, seven. It is important not to merge this with the predecessor and successor boundary adjustment. They are two separate decisions. One selects the boundary pair used by the family update; the other selects the output anchor used to update the maintained order. Keeping those responsibilities separate was necessary for the maintained order to remain correct.`,

  10: `Correct insertion is only one part of the state problem. Every finite pair must also have one parent and one sibling-list owner. The left-hand diagram shows the local transaction. Before a split, an existing owner controls a sibling list that contains a retained segment and a segment that will be acquired. After the split, the existing owner keeps the retained segment, while the new owner receives the acquired nonempty segment. Only the transferred segment is rebound. The implementation therefore treats split and transfer as a transaction: save the affected state, execute the split, publish the ownership transfer, check local postconditions, and roll back if any check fails. The checks also reject invalid split boundaries and inconsistent ownership state. The maintained state includes the sorted processed prefix and the upper and lower pair families. Because the backend uses ordinary lists, scanning, copying, slicing, and ownership rebinding remain concrete costs. The transaction protects correctness, but ordinary lists do not provide the update bounds required by the historical linear-time analysis.`,

  11: `The validation strategy has two distinct sides. On the left are implementation and state checks. Focused regression cases exercise known edge conditions. Bounded exhaustive validation covers 2,074 oracle-valid permutations through size eight. Checked-state audits inspect the complete maintained state, including parent chains, ownership, list registries, split pairs, and the recovered output. Same-core deterministic replay checks deterministic consistency of the resulting state. Replay is not a second independent Jordan-sorting implementation; it is a consistency check over the same core. On the right is evidence integrity and reproducibility. The formal experiment used a pre-specified protocol, a manifest-bound archive, schema and schedule checks, row-count checks, summary recomputation, and hash verification. A separate evidence-contract validator regenerates the expected cases, recomputes the relevant summaries, and verifies the archive. These layers support different claims. Together they provide bounded correctness evidence and a reproducible evidence chain, but they do not constitute a mathematical proof for every Jordan sequence.`,

  12: `The formal experiment was designed so that the paper timing boundary is visible. The protocol contains five input sizes, twelve exact cases per size, three algorithms, and twenty measured calls per case-algorithm cell. That produces 3,600 measured rows. Each exact case is generated once, certified once, and receives one checked-state audit before timing. Each case-algorithm cell receives five warm-up calls followed by twenty measured calls. The schedule is deterministic and rotates algorithm positions across measured rounds. Each timed call receives a fresh input list. For the paper algorithm, certification and the checked-state audit are outside the timer, while the minimal paper-core call on a pre-certified input is inside. Importantly, output recovery from the maintained partial order remains inside that paper call. Runner-level normalization and comparison occur after timing. The comparison pipelines do not have identical timing scopes. Python timing covers the complete sorting call. Reference timing includes its complete oracle-backed pipeline. This is why the paper/reference value later in the presentation is called a pipeline-scope ratio. It describes the recorded experiment, but it is not a like-for-like end-to-end speedup. After measurement, the runner aggregates the rows, writes the manifest-bound archive, and validates the evidence contract.`,

  13: `All sixty cases in the formal experiment passed the relevant checks. The archive contains 3,600 measured rows; all 60 case-level checked-state audits passed; and no correctness errors were recorded. Each case was oracle-certified before timing, and every measured call returned the expected output. The distinction between rows and audits matters. There were sixty audits, one for each exact case; the audit result is then associated with that case's timing rows. There were not 3,600 independent audits. These results provide empirical correctness evidence for the controlled valid cases in the protocol. They do not evaluate recognition of arbitrary inputs, and they do not prove correctness for all Jordan sequences.`,

  14: `The main runtime pattern is the decrease in the median exact-case paper/reference ratio across the five tested sizes. The ratio is first computed within each exact case by dividing the paper median by the reference median; those case ratios are then summarized with equal case weight. At size thirty-two, the median ratio is 3.226, so the paper call is larger than the reference call under the defined timing scopes. It falls to 2.202 at size 64 and to 1.351 at size 128. At size 256 it is 0.851, and at size 512 it is 0.567. The observed crossover therefore lies between the tested sizes 128 and 256. This is a finite empirical pattern, not an asymptotic claim. It also does not mean that the paper implementation is universally faster, because the numerator and denominator represent different pipelines. The reference call includes oracle-backed work, while the paper call starts from a certified valid input and times only the minimal core. Python sort, shown in the backup material, still has the lowest median call time at every tested size.`,

  15: `The evidence supports four bounded conclusions. The ordinary-list reconstruction is executable. It recovers output from maintained state rather than from the oracle result. It returned correct output on every evaluated valid case, and its runtime observations are reproducible under the defined timing scopes. Four stronger conclusions are not established: this is not a linear-time implementation, five sizes do not determine asymptotic complexity, recognition of arbitrary inputs was not evaluated, and the paper/reference ratio is not a like-for-like end-to-end speedup. The limitations on this slide apply to the ordinary-list evidence reported today. A future finger-tree backend would require its own correctness validation, complexity analysis, and experimental evidence.`,

  16: `The validated baseline now gives a controlled starting point for a finger-tree extension. The executable ordinary-list reconstruction has stabilized, its output is recovered from maintained state, state and ownership validation is in place, and the formal evidence has been archived. The archived ordinary-list experiment remains the fixed baseline and will not be overwritten. If the finger-tree backend becomes thesis-facing, it will receive a separate source version, validation pass, and experiment rather than reusing the existing results. The first goal is a semantically equivalent backend that passes differential and Jordan-sorting correctness tests. A stronger complexity claim would require an additional argument that splitting, boundary insertion, and ownership handling satisfy the operation bounds used by the historical analysis. I would therefore welcome guidance on whether the extension should target the historical heterogeneous finger tree or an equivalent backend with the required list operations, and whether semantic equivalence plus experimental comparison is sufficient or an amortized operation-bound argument is also expected.`,

  17: `If exact runtimes are requested, this backup slide reports the median call times for all three algorithms. The values belong to one recorded Apple M4 and CPython 3.12.4 execution. The logarithmic scale makes the Python values visible beside the reference and paper values. These absolute times should not be generalized to other environments.`,

  18: `This slide answers the output-provenance question directly. The reference pipeline returns oracle_result sorted. The paper core returns state.partial_order.to_list. Certification precedes the paper call and comparison follows it, so neither operation supplies the paper core's return value.`,

  19: `This inventory summarizes the bounded validation evidence: repository tests, exhaustive valid permutations through size eight, fixed generated cases, formal case-level checked-state audits, and a formal evidence archive that passed evidence-contract validation. These checks are complementary; none is a universal proof.`,

  20: `This table summarizes the reflected local choices. Step 1 always selects the predecessor-side boundary A-i, and Step 2 always selects the successor-side boundary B-i. Step 3 reflects how those boundaries are used. Increasing iterations acquire the left split side and use the rightmost child and right endpoint; decreasing iterations mirror those choices.`,

  21: `This proposed boundary keeps the paper-facing Step 1, Step 2, and Step 3 control flow above a small sibling-list interface. The current ordinary-list backend remains the validated baseline. A finger-tree backend would be a separate implementation of the same semantic operations: singleton creation, boundary insertion, split, extreme-child access, ownership preservation, and stable handles. The exact data-structure target—either the historical heterogeneous finger tree or an equivalently efficient backend—remains to be agreed with the supervisor. The main risk is that efficient tree splitting is not enough by itself. If ownership transfer still scans the acquired segment and rebinds every item, the backend may not satisfy the operation bounds needed by the historical analysis. The first milestone is therefore semantic equivalence and differential correctness; any complexity claim requires a separate proof-level argument.`,
};

const TALK_TIMES = {
  1: "0:45", 2: "0:55", 3: "0:50", 4: "1:10", 5: "0:55", 6: "1:25", 7: "1:30", 8: "1:35",
  9: "1:20", 10: "1:25", 11: "1:05", 12: "1:40", 13: "0:50", 14: "1:20", 15: "0:45", 16: "1:00",
};

const TALK_TITLES = {
  1: "Progress on the Executable Reconstruction of Simplified Jordan Sorting",
  2: "The previous report established a static structural baseline",
  3: "Four work packages addressed the main implementation gap",
  4: "The thesis now isolates valid-input sorting from two adjacent questions",
  5: "Three questions connect reconstruction, measurement, and interpretation",
  6: "The oracle, reference pipeline, and paper core have distinct roles",
  7: "One Step 1/2/3 control flow supports a reflected decreasing orientation",
  8: "Step 3(c) uses the geometric extreme, not the second stored endpoint",
  9: "Odd iterations require a separate z1 output-anchor correction",
  10: "Correct insertion also requires ownership-safe transactional updates",
  11: "Validation spans implementation state and evidence integrity",
  12: "The formal experiment keeps certification and audit outside paper timing",
  13: "Every pre-specified formal case passed certification, audit, and output checks",
  14: "The paper/reference ratio decreases across the five tested sizes",
  15: "Evidence supports a bounded reconstruction, not a linear-time claim",
  16: "The validated baseline provides a controlled basis for a scoped finger-tree extension",
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
    addText(slide, "Implementation, validation, and formal experimental evidence", 76, 405, 560, 72, {
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
    const slide = baseSlide(presentation, "Four work packages addressed the main implementation gap", "Progress", "3 / 16");
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
    addText(slide, "The outcome is a stable ordinary-list research baseline, not the historical linear-time backend.", 130, 580, 1020, 56, { fontSize: 23, bold: true, color: C.navy, align: "center", valign: "middle" });
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
    const slide = baseSlide(presentation, "The thesis now isolates valid-input sorting from two adjacent questions", "Scope", "4 / 16");
    addBox(slide, 76, 152, 520, 410, { fill: C.white, line: C.line, radius: 8 });
    addBox(slide, 684, 152, 520, 410, { fill: C.white, line: C.teal, lineWidth: 2, radius: 8 });
    addText(slide, "Earlier planning emphasis", 100, 176, 470, 44, { fontSize: 25, bold: true, color: C.slate });
    addText(slide, "Current research scope", 708, 176, 470, 44, { fontSize: 25, bold: true, color: C.teal });
    const left = ["General structural framework", "Valid and invalid generators", "Static family trees", "Broad reference evaluation", "Recognition as a possible experiment", "Theoretical backend implementation"];
    const right = ["Executable reconstruction of the 1990 procedure", "Oracle-certified valid-input sorting", "Dynamic sibling-list state", "Paper core, reference pipeline, Python sort", "Recognition remains separate", "Ordinary-list backend as the validated baseline"];
    left.forEach((t, i) => {
      addText(slide, t, 102, 238 + i * 50, 455, 38, { fontSize: 18, color: C.slate, valign: "middle" });
      addText(slide, "→", 610, 238 + i * 50, 58, 38, { fontSize: 26, bold: true, color: C.coral, align: "center", valign: "middle" });
      addText(slide, right[i], 710, 238 + i * 50, 455, 38, { fontSize: 18, bold: i === 0 || i === 2, color: C.ink, valign: "middle" });
    });
    addText(slide, "The current evidence remains bound to the ordinary-list baseline; a finger-tree backend is being investigated as a separate extension.", 120, 578, 1040, 64, { fontSize: 22, bold: true, color: C.navy, align: "center", valign: "middle" });
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
    const slide = baseSlide(presentation, "One Step 1/2/3 control flow supports a reflected decreasing orientation", "Reconstruction", "7 / 16");
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
    addText(slide, "The colors describe reconstruction evidence, not ownership of individual algorithm steps.", 156, 606, 968, 34, { fontSize: 18, bold: true, color: C.navy, align: "center", valign: "middle" });
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
    const slide = baseSlide(presentation, "Correct insertion also requires ownership-safe transactional updates", "Maintained State", "10 / 16");
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
    addText(slide, "Only the acquired nonempty segment is rebound.", 120, 526, 552, 28, { fontSize: 17, color: C.slate, align: "center" });

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
    const slide = baseSlide(presentation, "Validation spans implementation state and evidence integrity", "Validation", "11 / 16");
    addText(slide, "IMPLEMENTATION AND STATE VALIDATION", 92, 158, 450, 28, { fontSize: 15, bold: true, color: C.teal });
    addText(slide, "EVIDENCE INTEGRITY AND REPRODUCIBILITY", 728, 158, 450, 28, { fontSize: 15, bold: true, color: C.coral });
    const left = ["Focused regression cases", "Bounded exhaustive validation\n2,074 oracle-valid permutations, n ≤ 8", "Checked-state audits", "Same-core deterministic replay"];
    const right = ["Pre-specified protocol", "Manifest-bound archive", "Schema, schedule, count, and hash checks", "Separate evidence-contract validation"];
    const ys = [202, 294, 402, 494];
    for (let i = 0; i < 4; i++) {
      addBox(slide, 88, ys[i], 470, i === 1 ? 82 : 64, { fill: C.paleTeal, line: C.teal, radius: 7 });
      addText(slide, left[i], 104, ys[i] + 8, 438, i === 1 ? 66 : 48, { fontSize: i === 1 ? 18 : 20, bold: i === 1, color: C.ink, align: "center", valign: "middle" });
      addBox(slide, 722, ys[i], 470, i === 2 ? 82 : 64, { fill: C.paleCoral, line: C.coral, radius: 7 });
      addText(slide, right[i], 738, ys[i] + 8, 438, i === 2 ? 66 : 48, { fontSize: i === 2 ? 18 : 20, bold: i === 2, color: C.ink, align: "center", valign: "middle" });
      if (i < 3) {
        addText(slide, "↓", 286, ys[i] + (i === 1 ? 79 : 61), 72, 28, { fontSize: 26, bold: true, color: C.teal, align: "center" });
        addText(slide, "↓", 920, ys[i] + (i === 2 ? 79 : 61), 72, 28, { fontSize: 26, bold: true, color: C.coral, align: "center" });
      }
    }
    addText(slide, "Together: bounded correctness evidence and a reproducible evidence chain—not a universal proof.", 140, 610, 1000, 40, { fontSize: 21, bold: true, color: C.navy, align: "center", valign: "middle" });
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
    addText(slide, "Reference timing includes its complete oracle-backed pipeline; Python timing covers its complete sorting call.", 120, 538, 1040, 32, { fontSize: 18, color: C.slate, align: "center", valign: "middle" });
    addBox(slide, 212, 586, 856, 52, { fill: C.paleCoral, line: C.coral, lineWidth: 1.5, radius: 6 });
    addText(slide, "Paper/reference is a pipeline-scope ratio, not a like-for-like end-to-end speedup.", 230, 592, 820, 40, { fontSize: 18, bold: true, color: C.coral, align: "center", valign: "middle" });
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
    const slide = baseSlide(presentation, "Every pre-specified formal case passed certification, audit, and output checks", "Results", "13 / 16");
    const xs = [76, 364, 652, 940];
    metric(slide, "60", "exact cases", xs[0], 170, 250, C.navy);
    metric(slide, "3,600", "measured rows", xs[1], 170, 250, C.teal);
    metric(slide, "60 / 60", "checked-state audits passed", xs[2], 170, 250, C.coral);
    metric(slide, "0", "recorded correctness errors", xs[3], 170, 250, C.green);
    addRule(slide, 76, 322, 1128, C.line, 2);
    addText(slide, "Every case was oracle-certified before timing.", 160, 360, 960, 56, { fontSize: 30, bold: true, color: C.navy, align: "center", valign: "middle" });
    addBox(slide, 166, 458, 948, 112, { fill: C.paleBlue, line: C.navy, lineWidth: 1.5, radius: 8 });
    addText(slide, "All 3,600 rows belong to 60 exact cases; each case received one untimed checked-state audit before timing.", 194, 476, 892, 72, { fontSize: 22, color: C.ink, align: "center", valign: "middle" });
    addText(slide, "Evidence for controlled valid cases, not recognition evidence and not a proof for all Jordan sequences.", 156, 602, 968, 42, { fontSize: 19, bold: true, color: C.coral, align: "center", valign: "middle" });
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
    const slide = baseSlide(presentation, "Evidence supports a bounded reconstruction, not a linear-time claim", "Interpretation", "15 / 16");
    addBox(slide, 78, 152, 536, 404, { fill: C.paleTeal, line: C.teal, lineWidth: 2, radius: 8 });
    addBox(slide, 666, 152, 536, 404, { fill: C.paleCoral, line: C.coral, lineWidth: 2, radius: 8 });
    addText(slide, "Supported by the current evidence", 106, 178, 480, 52, { fontSize: 26, bold: true, color: C.teal, align: "center", valign: "middle" });
    addText(slide, "Not established", 694, 178, 480, 52, { fontSize: 26, bold: true, color: C.coral, align: "center", valign: "middle" });
    addBulletList(slide, ["executable ordinary-list reconstruction", "output recovery from maintained state", "correctness on evaluated valid cases", "reproducible runtime observations under fixed scopes"], 112, 252, 456, { fontSize: 20, gap: 66, bulletColor: C.teal });
    addBulletList(slide, ["linear-time implementation", "asymptotic complexity", "arbitrary-input recognition", "like-for-like end-to-end speedup"], 700, 252, 456, { fontSize: 20, gap: 66, bulletColor: C.coral });
    addText(slide, "Structural relationships remain descriptive. A finger-tree backend is not yet part of the validated baseline.", 150, 576, 980, 30, { fontSize: 18, color: C.slate, align: "center", valign: "middle" });
    addText(slide, "The reported conclusions remain specific to the ordinary-list baseline.", 150, 616, 980, 36, { fontSize: 21, bold: true, color: C.navy, align: "center", valign: "middle" });
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
    const slide = baseSlide(presentation, "The validated baseline provides a controlled basis for a scoped finger-tree extension", "Milestone", "16 / 16");
    addText(slide, "VALIDATED BASELINE", 88, 158, 470, 28, { fontSize: 15, bold: true, color: C.teal });
    addText(slide, "FINGER-TREE EXTENSION", 722, 158, 470, 28, { fontSize: 15, bold: true, color: C.coral });
    addBulletList(slide, ["executable ordinary-list reconstruction", "output recovered from maintained state", "state and ownership validation", "archived ordinary-list formal evidence"], 94, 208, 488, { fontSize: 21, gap: 66, bulletColor: C.teal });
    addBulletList(slide, ["extract a backend-independent interface", "implement a finger-tree sibling-list backend", "compare it with the ordinary-list baseline", "assess whether required operation bounds can be justified"], 728, 202, 474, { fontSize: 19, gap: 57, bulletColor: C.coral });
    addText(slide, "The existing ordinary-list evidence remains read-only; finger-tree results require a separate validation and experiment version.", 92, 484, 1096, 28, { fontSize: 14, color: C.slate, align: "center", valign: "middle" });
    addBox(slide, 92, 520, 1096, 112, { fill: C.navy, line: C.navy, radius: 8 });
    addText(slide, "Discussion", 120, 540, 160, 30, { fontSize: 21, bold: true, color: C.teal });
    addText(slide, "1. Should the extension target the historical heterogeneous finger tree specifically, or an equivalent backend supporting the required list operations?\n2. Is semantic equivalence plus an experimental comparison sufficient, or should the thesis also include an amortized operation-bound argument?", 288, 526, 862, 92, { fontSize: 20, color: C.white, valign: "middle" });
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
    "Target duration: 18.5-20 minutes",
    "Recommended delivery: approximately 125-130 words per minute, with brief pauses at slide transitions",
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
