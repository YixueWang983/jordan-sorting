import fs from "node:fs";

const source = fs.readFileSync(new URL("./build-progress-deck.mjs", import.meta.url), "utf8");
const block = source.match(/const TALK = \{([\s\S]*?)\n\};/)[1];
let total = 0;

for (const match of block.matchAll(/\n\s*(\d+): `([\s\S]*?)`,/g)) {
  const slide = Number(match[1]);
  const words = match[2].trim().split(/\s+/).length;
  if (slide <= 16) {
    console.log(`${slide}: ${words}`);
    total += words;
  }
}

console.log(`TOTAL: ${total}`);
