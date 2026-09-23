import fs from "node:fs/promises";
import { FileBlob, PresentationFile } from "@oai/artifact-tool";

try {
  const sourcePath = new URL(
    "../../Jordan_Sorting_Progress_Report_ZH.pptx",
    import.meta.url,
  );
  const presentation = await PresentationFile.importPptx(
    await FileBlob.load(sourcePath.pathname),
  );
  const snapshot = await presentation.inspect({
    kind: "slide,textbox,shape,notes,layout",
    maxChars: 200000,
  });
  await fs.writeFile(new URL("./zh-inspect.ndjson", import.meta.url), snapshot.ndjson, "utf8");
  console.log(`slides=${presentation.slides.items.length}`);
} catch (error) {
  console.error(error?.stack ?? String(error));
  process.exitCode = 1;
}
