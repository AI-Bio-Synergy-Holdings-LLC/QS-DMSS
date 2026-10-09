/* Execute the real export/citation callbacks without a browser or solver. */
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

const source = fs.readFileSync(path.join(__dirname, "../src/qs_dmss/cockpit/static/app.js"), "utf8");
function section(start, end) {
  const begin = source.indexOf(start), finish = source.indexOf(end, begin);
  assert(begin >= 0 && finish > begin, `Missing export test seam: ${start}`);
  return source.slice(begin, finish);
}

function researchObject(campaign = false) {
  return {
    generatedAt: "2026-10-08T00:00:00Z", runId: campaign ? "campaign-a" : "run-a",
    scenario: {label: "Recorded evidence", description: "Bounded workflow evidence"},
    status: "Ready", claimBoundary: "Not physical validation", metrics: [], evidence: [], artifacts: [],
    interpretation: {summary: "Inspect retained inputs", means: [], nonClaims: ["Not physical validation"]},
    comparison: {available: campaign, summary: "Recorded comparison", rows: [],
      reportUrl: "/api/experiments/campaign-a/report", bundleUrl: "/api/experiments/campaign-a/bundle"},
    campaignStudy: {available: campaign, label: "Study", templateId: "study-a",
      sourceConfigName: "demo.yaml", description: "Recorded comparison", scoringContract: {},
      recommendation: {status: "qualified", recommendedRunId: "run-a", reason: "Declared objective"}},
    replayCommands: ['qs-dmss verify "runs/run-a"'],
  };
}

function harness() {
  const surface = {innerHTML: "", querySelector: () => null};
  const context = vm.createContext({
    els: {researchObjectSurface: surface}, state: {}, jobSummary: () => null,
    escapeHtml: value => String(value).replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;"),
    researchObjectMetricsMarkup: () => "", researchObjectEvidenceMarkup: () => "",
    researchObjectArtifactMarkup: () => "", researchObjectComparisonMarkup: () => "",
    researchObjectCampaignStudyMarkup: () => "", renderInteractiveComparisonChart() {},
  });
  vm.runInContext([
    section("const citationMetadata = {", "const decisionMetricOptions ="),
    section("function buildResearchObjectMarkdown(", "function buildLabResearchObject("),
    section("function renderResearchObjectSurface(", "function renderResearchObjectComposer("),
  ].join("\n"), context);
  return {context, surface};
}

for (const campaign of [false, true]) {
  test(`${campaign ? "Campaign" : "Lab"} Markdown does not offer a different published artifact`, () => {
    const {context} = harness();
    const markdown = context.buildResearchObjectMarkdown(researchObject(campaign));
    assert.match(markdown, /Package: qs-dmss==0\.14\.0/);
    assert.match(markdown, /Latest archived release \(v0\.14\.0\) DOI:/);
    assert.match(markdown, /compare source commit and artifact hashes/);
    assert.doesNotMatch(markdown, /pypi\.org|PyPI:/);
    assert.match(markdown, /qs-dmss verify/);
    if (campaign) assert.match(markdown, /## Campaign Study Template/);
  });
}

test("Rendered citation identifies the published archive without assuming build identity", () => {
  const {context, surface} = harness();
  context.renderResearchObjectSurface(researchObject());
  assert.match(surface.innerHTML, /Archived v0\.14\.0 release/);
  assert.match(surface.innerHTML, /source commit and artifact hashes must match/);
  assert.doesNotMatch(surface.innerHTML, /pypi\.org|PyPI package/);
});
