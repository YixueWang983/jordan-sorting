import fs from "node:fs/promises";
import { FileBlob, PresentationFile } from "@oai/artifact-tool";

const decks = [
  {
    name: "en",
    path: new URL("./final/Jordan_Sorting_Progress_Report_midterm_final.pptx", import.meta.url),
    forbidden: [
      "Only the acquired nonempty segment is rebound",
      "The validated baseline supports a scoped finger-tree extension",
      "manifest-bound archive",
    ],
  },
  {
    name: "zh",
    path: new URL("./final/Jordan_Sorting_Progress_Report_ZH_midterm_final.pptx", import.meta.url),
    forbidden: [
      "只重新绑定获得的非空片段",
      "已验证基线为限定范围的 finger-tree 扩展提供受控基础",
      "manifest 绑定的归档",
    ],
  },
];

for (const deck of decks) {
  const presentation = await PresentationFile.importPptx(await FileBlob.load(deck.path.pathname));
  const snapshot = await presentation.inspect({ kind: "slide,textbox,notes", maxChars: 500000 });
  const records = snapshot.ndjson
    .trim()
    .split("\n")
    .filter(Boolean)
    .map((line) => JSON.parse(line));
  const notes = records.filter((record) => record.kind === "notes");
  const allText = records.map((record) => record.text ?? "").join("\n");
  const sourceBlocks = notes.filter((record) => record.text.includes("[Sources]")).length;
  const forbidden = ["/Users/", "attachments/", ...deck.forbidden].filter((needle) => allText.includes(needle));
  console.log(JSON.stringify({
    deck: deck.name,
    slides: presentation.slides.items.length,
    notes: notes.length,
    sourceBlocks,
    forbidden,
  }));
}

const englishScript = await fs.readFile(
  new URL("./candidates/Jordan_Sorting_Progress_Report_Speaker_Script_midterm.txt", import.meta.url),
  "utf8",
);
const mainSection = englishScript.split("Q&A NOTES: SLIDES 17-21")[0];
const slideBodies = [...mainSection.matchAll(/SLIDE \d+ \| TARGET[^\n]*\n[^\n]*\n\n([\s\S]*?)(?=\n\n={10,}|$)/g)]
  .map((match) => match[1].trim());
const words = slideBodies.join(" ").split(/\s+/).filter(Boolean).length;
console.log(JSON.stringify({ englishMainSlideBodies: slideBodies.length, englishMainWords: words }));
