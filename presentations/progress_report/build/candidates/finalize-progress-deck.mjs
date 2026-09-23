import path from "node:path";
import { pathToFileURL } from "node:url";

const SKILL_DIR = "/Users/schneeshini/.codex/plugins/cache/openai-primary-runtime/presentations/26.905.11957/skills/presentations";
const workspaceDir = "/Users/schneeshini/Documents/Codex/2026-06-05/files-mentioned-by-the-user-thesis/jordan-sorting";
const candidatePath = path.join(
  workspaceDir,
  "presentations/progress_report/build/candidates/Jordan_Sorting_Progress_Report_midterm_candidate.pptx",
);
const finalPath = path.join(
  workspaceDir,
  "presentations/progress_report/build/final/Jordan_Sorting_Progress_Report_midterm_final.pptx",
);
const { finalizePresentation } = await import(
  pathToFileURL(path.join(SKILL_DIR, "container_tools/artifact_tool_utils.mjs")).href
);

const result = await finalizePresentation({
  explicitTotalSlideCount: 21,
  requiredNativeTableOwnerSlides: [],
  requiredNativeChartOwnerSlides: [14],
  materializeLiteralChartWorkbooks: true,
  workspaceDir,
  candidatePath,
  finalPath,
  pythonExecutable: "/Users/schneeshini/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3",
  integrityValidatorPath: path.join(SKILL_DIR, "container_tools/inspect_presentation_package_integrity.py"),
  layoutValidatorPath: path.join(SKILL_DIR, "container_tools/inspect_presentation_layout_geometry.py"),
  layoutArgs: [
    "--expected-slide-size-emu",
    "12192000,6858000",
    "--validate-bullet-geometry",
    "--validate-heading-fit",
  ],
  verifyArtifactToolImport: true,
  receiptPath: path.join(
    workspaceDir,
    "presentations/progress_report/build/validation/Jordan_Sorting_Progress_Report_midterm_final.validation.json",
  ),
});

console.log(JSON.stringify(result, null, 2));
