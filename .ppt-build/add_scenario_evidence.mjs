import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";
import { FileBlob, PresentationFile } from "@oai/artifact-tool";

const workspaceDir = "/Users/rajesh/Desktop/ai projects/dCortex";
const skillDir = "/Users/rajesh/.codex/plugins/cache/openai-primary-runtime/presentations/26.904.11930/skills/presentations";
const runtimePython = "/Users/rajesh/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3";
const buildDir = path.join(workspaceDir, ".ppt-build");
const stagingDir = path.join(workspaceDir, ".codex-finalizer");
const finalDir = path.join(workspaceDir, "docs", "revised");
const sourcePath = path.join(workspaceDir, "docs", "deck.pptx");
const finalPath = path.join(finalDir, "deck-with-scenario-evidence.pptx");

const paper = "#0F151C";
const card = "#161E27";
const ink = "#E6EDF3";
const muted = "#93A4B4";
const edge = "#2A3644";
const teal = "#4FC1D8";
const amber = "#E5A93D";
const green = "#62C48D";
const red = "#E0705C";
const sans = "Arial";
const mono = "Courier New";

function text(slide, value, left, top, width, height, opts = {}) {
  const shape = slide.shapes.add({
    geometry: "textbox",
    position: { left, top, width, height },
    fill: "none",
    line: { fill: "none", width: 0 },
  });
  shape.text = value;
  shape.text.style = {
    typeface: opts.typeface ?? sans,
    fontSize: opts.size ?? 18,
    bold: opts.bold ?? false,
    color: opts.color ?? ink,
    alignment: opts.align ?? "left",
    verticalAlignment: opts.valign ?? "top",
    autoFit: "shrinkText",
    wrap: "square",
    insets: { left: 4, right: 4, top: 2, bottom: 2 },
  };
  return shape;
}

function rect(slide, left, top, width, height, fill = card, lineFill = edge, radius = 14) {
  return slide.shapes.add({
    geometry: "rect",
    position: { left, top, width, height },
    fill,
    line: { style: "solid", fill: lineFill, width: 1 },
    borderRadius: radius,
  });
}

function header(slide, eyebrow, title) {
  text(slide, eyebrow.toUpperCase(), 67, 38, 400, 18, { size: 11, color: muted, typeface: mono });
  text(slide, title, 67, 67, 1120, 44, { size: 31, bold: true });
  rect(slide, 67, 132, 115, 3, teal, teal, 0);
}

function footer(slide, number) {
  text(slide, "Crew Ops Advisor  ·  dCortex hackathon 2026", 67, 676, 470, 18, { size: 10, color: muted, typeface: mono });
  text(slide, `${number} / 18`, 1070, 676, 142, 18, { size: 10, color: muted, typeface: mono, align: "right" });
}

function badge(slide, label, color) {
  rect(slide, 67, 151, label === "POSITIVE" ? 94 : 98, 28, paper, color, 14);
  text(slide, label, 67, 157, label === "POSITIVE" ? 94 : 98, 16, { size: 10, color, bold: true, typeface: mono, align: "center" });
}

const scenarios = [
  {
    tier: "Tier 1 · lookup evidence",
    title: "Reserve roster at BLR",
    type: "POSITIVE",
    color: green,
    summary: "Verified reserve lookup with ranks, ratings, on-call windows, and reasoning",
    image: "/var/folders/d6/sjxvns1n6td1mnqdb7qz2lgr0000gn/T/codex-clipboard-00e8bb87-b56b-414f-8a86-d838d7065a73.png",
    alt: "Positive Tier 1 reserve roster response for BLR",
  },
  {
    tier: "Tier 1 · lookup evidence",
    title: "Schedule outside the published week",
    type: "NEGATIVE",
    color: amber,
    summary: "The assistant declines a date outside the dataset and gives the supported date range",
    image: "/var/folders/d6/sjxvns1n6td1mnqdb7qz2lgr0000gn/T/codex-clipboard-8fcbef65-5cfc-4cf1-9cb1-83c2b8ff455a.png",
    alt: "Negative Tier 1 request for flights outside the schedule week",
  },
  {
    tier: "Tier 2 · consequence and legality evidence",
    title: "Reserve eligibility for a Captain duty",
    type: "POSITIVE",
    color: green,
    summary: "The response identifies eligible reserves and shows exclusions with their rule-based reasons",
    image: "/var/folders/d6/sjxvns1n6td1mnqdb7qz2lgr0000gn/T/codex-clipboard-f78aa58c-3f97-4994-8bde-b81b77c831a8.png",
    alt: "Positive Tier 2 reserve eligibility response",
  },
  {
    tier: "Tier 2 · consequence and legality evidence",
    title: "Cancellation outside schedule coverage",
    type: "NEGATIVE",
    color: amber,
    summary: "A cancellation request beyond the published schedule returns no invented flight, crew, or cost impact",
    image: "/var/folders/d6/sjxvns1n6td1mnqdb7qz2lgr0000gn/T/codex-clipboard-464be7cd-fd52-4b1a-929b-5b69791fe6dd.png",
    alt: "Negative Tier 2 cancellation request outside schedule coverage",
  },
  {
    tier: "Tier 3 · recommendation evidence",
    title: "Ranked legal cover options",
    type: "POSITIVE",
    color: green,
    summary: "The assistant ranks legal cover options by cost, delay, crew eligibility, and exclusion reasons",
    image: "/var/folders/d6/sjxvns1n6td1mnqdb7qz2lgr0000gn/T/codex-clipboard-2a30c9fe-96c8-4785-8f53-cf6f218ab2d6.png",
    alt: "Positive Tier 3 ranked legal cover recommendation",
  },
  {
    tier: "Tier 3 · recommendation evidence",
    title: "Employment action outside Crew Control",
    type: "NEGATIVE",
    color: red,
    summary: "The assistant declines an HR request and redirects to supported operational analysis",
    image: "/var/folders/d6/sjxvns1n6td1mnqdb7qz2lgr0000gn/T/codex-clipboard-d1927b7c-43ab-445c-a316-a04bafc8003e.png",
    alt: "Negative Tier 3 HR request response",
  },
];

const presentation = await PresentationFile.importPptx(await FileBlob.load(sourcePath));

const originalFooterIds = [
  "sh/fu94fe98", "sh/w3i1sfa9", "sh/n6ls3alk", "sh/3ytsrmpw", "sh/sb6xsvu9", "sh/h4bupgn6",
  "sh/baxkjqlk", "sh/5sne5wne", "sh/ofq5svm5", "sh/s7yt4b21", "sh/o7ih0r6h", "sh/dcbm583y",
];
const finalNumbers = [1, 2, 3, 4, 5, 12, 13, 14, 15, 16, 17, 18];
for (let i = 0; i < originalFooterIds.length; i += 1) {
  presentation.resolve(originalFooterIds[i]).text = `${finalNumbers[i]} / 18`;
}

let insertionPoint = presentation.slides.getItem(4);
for (let i = 0; i < scenarios.length; i += 1) {
  const scenario = scenarios[i];
  const inserted = presentation.slides.insert({ after: insertionPoint });
  const s = inserted.slide;
  insertionPoint = s;
  s.background.fill = paper;
  header(s, scenario.tier, scenario.title);
  badge(s, scenario.type, scenario.color);
  text(s, scenario.summary, 184, 154, 1010, 24, { size: 14, color: muted });
  rect(s, 106, 195, 1068, 449, card, edge, 16);
  const blob = await fs.readFile(scenario.image);
  s.images.add({
    blob,
    contentType: "image/png",
    alt: scenario.alt,
    fit: "contain",
    geometry: "roundRect",
    borderRadius: 12,
    position: { left: 117, top: 205, width: 1046, height: 429 },
  });
  footer(s, i + 6);
  s.speakerNotes.textFrame.setText(`Source: supplied scenario screenshot and pasted scenario matrix. ${scenario.tier}; ${scenario.type.toLowerCase()} scenario.`);
}

await fs.mkdir(buildDir, { recursive: true });
await fs.mkdir(stagingDir, { recursive: true });
await fs.mkdir(finalDir, { recursive: true });
const candidatePath = path.join(stagingDir, "deck-with-scenario-evidence.candidate.pptx");
await (await PresentationFile.exportPptx(presentation)).save(candidatePath);

const { finalizePresentation } = await import(pathToFileURL(path.join(skillDir, "container_tools", "artifact_tool_utils.mjs")).href);
const result = await finalizePresentation({
  explicitTotalSlideCount: 18,
  workspaceDir,
  candidatePath,
  finalPath,
  pythonExecutable: runtimePython,
  integrityValidatorPath: path.join(skillDir, "container_tools", "inspect_presentation_package_integrity.py"),
  layoutValidatorPath: path.join(skillDir, "container_tools", "inspect_presentation_layout_geometry.py"),
  layoutArgs: ["--expected-slide-size-emu", "12192000,6858000", "--validate-bullet-geometry", "--validate-heading-fit"],
  fontPolicy: {
    basis: "reference",
    families: [sans, mono],
    referencePath: sourcePath,
    referenceSha256: "3d03a4854cd36b3409b50224217a296132129d41d461670334e2751dc9b95b35",
  },
  verifyArtifactToolImport: true,
  receiptPath: path.join(stagingDir, "deck-with-scenario-evidence.validation.json"),
});

const montage = await presentation.export({ format: "webp", montage: true, scale: 1 });
await fs.writeFile(path.join(buildDir, "scenario-evidence-montage.webp"), new Uint8Array(await montage.arrayBuffer()));
console.log(JSON.stringify({ finalPath, result }, null, 2));
