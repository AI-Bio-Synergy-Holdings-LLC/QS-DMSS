// Presentation geometry only: read the pinned graph, never run a numerical model.
import { readFileSync, writeFileSync } from "node:fs";
import { createHash } from "node:crypto";
import { fileURLToPath } from "node:url";

const root = new URL("../../site/challenges/sc-graph-001/", import.meta.url);
const bytes = readFileSync(new URL("data.json", root));
if (
  createHash("sha256").update(bytes).digest("hex") !==
  "ed955ee0de108dddfd652a5cf0f847bbfc10332a9292623a5cf644ba5bfaf1ec"
) {
  throw new Error("Presentation source differs");
}
const data = JSON.parse(bytes);
const c = data.cases.find((item) => item.id === "graph_07");
const active = new Set(c.reference.active);
const boundary = new Set(c.reference.boundary);
const position = ([i, j]) => [
  754 + (i + j / 2) * 145,
  421 - ((j * Math.sqrt(3)) / 2) * 145,
];
const edges = c.reference.edges
  .map(([a, b]) => {
    const [x1, y1] = position(c.reference.vertices[a]);
    const [x2, y2] = position(c.reference.vertices[b]);
    const ghost = !active.has(a) || !active.has(b);
    return `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${ghost ? "#b1bcb7" : "#15393d"}" stroke-width="${ghost ? 2 : 3}"${ghost ? ' stroke-dasharray="7 7"' : ""}/>`;
  })
  .join("");
const nodes = c.reference.vertices
  .map((v, id) => {
    const [x, y] = position(v);
    const mark = boundary.has(id)
      ? '<path d="M 0 -13 L 13 0 L 0 13 L -13 0 Z" fill="#fff" stroke="#b14f16" stroke-width="3"/>'
      : '<circle r="11" fill="#15393d"/>';
    return `<g transform="translate(${x} ${y})">${mark}<text y="42" text-anchor="middle" font-family="Arial, sans-serif" font-size="22" fill="#536763">${id}</text></g>`;
  })
  .join("");
const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630" role="img" aria-labelledby="title desc">
<title id="title">Which Dirichlet boundary did we implement?</title>
<desc id="desc">SC-GRAPH-001. Recorded level-1 Dirichlet graph, full vertex IDs: interior vertices 1, 3 and 4 active; boundary vertices 0, 2 and 5 excluded. Principal restriction keeps full-matrix entries. Independent scientific review pending. Lattice illustration, not physical distance.</desc>
<rect width="1200" height="630" fill="#fff"/>
<rect x="0" y="0" width="10" height="630" fill="#15393d"/>
<text x="56" y="62" font-family="Georgia, serif" font-size="28" fill="#15393d">QS-DMSS · Scientific Challenges</text>
<text x="56" y="136" font-family="Arial, sans-serif" font-size="22" letter-spacing="1" fill="#b14f16">SC-GRAPH-001</text>
<g font-family="Georgia, serif" font-size="58" font-weight="bold" fill="#15393d">
<text x="56" y="219">Which Dirichlet</text><text x="56" y="288">boundary did</text><text x="56" y="357">we implement?</text></g>
<text x="56" y="427" font-family="Arial, sans-serif" font-size="27" fill="#536763">Explore four recorded cases.</text>
<text x="56" y="465" font-family="Arial, sans-serif" font-size="27" fill="#536763">Inspect the finite-model convention.</text>
<text x="900" y="112" text-anchor="middle" font-family="Arial, sans-serif" font-size="23" fill="#15393d">Recorded level 1 · Dirichlet</text>
${edges}${nodes}
<text x="900" y="505" text-anchor="middle" font-family="Arial, sans-serif" font-size="23" fill="#536763">3 active / 6 full vertices</text>
<line x1="56" y1="535" x2="1144" y2="535" stroke="#d4dedb"/>
<text x="56" y="578" font-family="Arial, sans-serif" font-size="26" font-weight="bold" fill="#b14f16">Independent scientific review pending</text>
<text x="56" y="610" font-family="Arial, sans-serif" font-size="18" fill="#536763">Frozen candidate 48d7ab5 · Lattice illustration, not physical distance · qs-dmss.studio</text>
</svg>
`;
const output = new URL("social-card-v1.svg", root);
const args = process.argv.slice(2);
if (args.length === 1 && args[0] === "--check") {
  if (readFileSync(output, "utf8") !== svg)
    throw new Error("Social-card source is stale");
  console.log("Social-card source matches the pinned presentation data");
} else if (args.length === 0) {
  writeFileSync(output, svg);
  console.log(fileURLToPath(output));
} else {
  throw new Error(
    "Use no arguments to render SVG source, or --check to verify it",
  );
}
