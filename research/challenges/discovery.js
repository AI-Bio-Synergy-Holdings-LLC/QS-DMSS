/* Source template. Run build_discovery.py after edits; never edit the generated copies. */
(() => {
  "use strict";
  const EXPECTED_SHA256 = "__REGISTRY_SHA256__";
  const REPO = "https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS";
  const REGISTRY_COMMIT = "08f75235cc1fe6e6a8ba4bfdbddcdd049359a7f9";
  const GUIDE = REPO + "/blob/" + REGISTRY_COMMIT + "/docs/scientific-challenges.md#reproduce-the-development-candidate";
  const root = document.querySelector("[data-scientific-challenges]");
  if (!root) return;
  const view = root.querySelector("[data-challenge-view]");
  const status = root.querySelector("[data-challenge-status]");
  const retry = root.querySelector("[data-challenge-retry]");
  const assistants = [...document.querySelectorAll("[data-challenge-assistant]")];

  function node(tag, text, className) {
    const element = document.createElement(tag);
    if (text !== undefined) element.textContent = String(text);
    if (className) element.className = className;
    return element;
  }

  function link(text, href) {
    const url = new URL(href);
    if (url.origin !== "https://github.com" ||
        !url.pathname.startsWith("/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/")) {
      throw new Error("Unexpected evidence link");
    }
    const element = node("a", text);
    element.href = url.href;
    return element;
  }

  function list(items) {
    const element = node("ul");
    items.forEach(item => element.append(node("li", item)));
    return element;
  }

  function reviewURL(challenge) {
    const url = new URL(REPO + "/issues/new");
    url.searchParams.set("template", "scientific_review.yml");
    url.searchParams.set("title", "[Scientific Review]: " + challenge.id + " — ");
    // Never prefill reproduction success, identity, hashes or independence.
    url.searchParams.set("focus", challenge.id + " — " + challenge.title + "\nDescribe your specific claim or methodological question.");
    return url.href;
  }

  function detail(label, content) {
    const section = node("details");
    section.append(node("summary", label), content);
    return section;
  }

  function renderAssistant(challenge) {
    assistants.forEach(assistant => {
      assistant.replaceChildren(
        node("h4", "Registered challenge · " + challenge.id),
        node("p", "Deterministic guidance, separate from the currently selected run. This is not a model-generated judgment."),
        node("p", "Review question: " + challenge.unresolved_questions[0]),
        node("p", "Numerical evidence: not falsified within scope. Independent scientific review and human disposition: pending."),
        link("Reproduce this challenge locally", GUIDE),
        document.createTextNode(" · "),
        link("Open review form for " + challenge.id, reviewURL(challenge))
      );
    });
  }

  function render(registry) {
    const choices = node("div", undefined, "sc-choices");
    choices.setAttribute("role", "group");
    choices.setAttribute("aria-label", "Choose a scientific challenge");
    const panel = node("section", undefined, "sc-detail");
    panel.id = "selected-scientific-challenge";
    panel.setAttribute("aria-labelledby", "selected-challenge-title");
    const buttons = [];
    function select(challenge) {
      buttons.forEach(button => button.setAttribute("aria-pressed", String(button.dataset.challengeId === challenge.id)));
      panel.replaceChildren();
      const title = node("h3", challenge.id + " · " + challenge.title);
      title.id = "selected-challenge-title";
      panel.append(title);
      const states = node("dl", undefined, "sc-states");
      [
        ["Numerical evidence", "Not falsified within scope"],
        ["Owner engineering approval", "Pilot #194 only"],
        ["Independent scientific review", "Pending · not established"],
      ].forEach(([label, value]) => {
        const item = node("div");
        item.append(node("dt", label), node("dd", value));
        states.append(item);
      });
      panel.append(states, node("p", challenge.claim, "sc-claim"));
      const flow = node("ol", undefined, "sc-handoff");
      [
        ["01 · Choose", node("span", challenge.id + " selected")],
        ["02 · Inspect", link("Open pinned evidence", registry.evidence_packets[0].url)],
        ["03 · Reproduce", link("Local reproduction guide", GUIDE)],
        ["04 · Submit", link("Open review form", reviewURL(challenge))],
      ].forEach(([label, action]) => {
        const item = node("li");
        item.append(node("strong", label), action);
        flow.append(item);
      });
      panel.append(flow, node("p", "Read-only evidence navigation. No experiment or AI request is launched here. Submitted findings require a named human disposition.", "sc-note"));

      const scope = node("div");
      scope.append(node("p", challenge.model_scope), list(challenge.limitations),
        node("h4", "Unresolved questions"), list(challenge.unresolved_questions),
        node("p", "Counterexample sought: " + challenge.falsification_target));
      const scopeDetails = detail("Scope, limitations and open questions", scope);
      scopeDetails.open = true;
      panel.append(scopeDetails);

      const evidence = node("div");
      evidence.append(node("p", challenge.case_count + " candidate cases; Wolfram compares these same cases, not additional independent experiments. References were authored in the same AI-assisted maintainer workflow."));
      registry.evidence_packets.forEach(packet => {
        const result = challenge.results.find(item => item.packet_id === packet.id);
        const row = node("div", undefined, "sc-packet");
        row.append(link(packet.id === "pilot-v1" ? "Original candidate packet" : "Wolfram cross-tool supplement", packet.url),
          node("p", packet.method),
          node("code", "SHA-256: " + packet.sha256),
          node("code", "Results: " + result.pointer),
          node("code", "Environment: " + packet.environment_pointer));
        evidence.append(row);
      });
      evidence.append(node("h4", "Registered limits (not retuned)"));
      const bounds = node("dl", undefined, "sc-bounds");
      Object.entries(challenge.acceptance_limits).forEach(([name, value]) => {
        const row = node("div");
        row.append(node("dt", name), node("dd", Array.isArray(value) ? value.join(" to ") : value));
        bounds.append(row);
      });
      evidence.append(bounds, link("Full prospective protocol and interpretation rules", REPO + "/blob/" + registry.engineering_review.merged_commit + "/" + registry.candidate.protocol_path));
      panel.append(detail("Evidence packets, hashes and tolerances", evidence));

      const identity = node("div");
      identity.append(
        node("p", "Development candidate — NOT the published v0.13.2 wheel."),
        node("code", "Source: " + registry.candidate.source_commit),
        node("code", "Original candidate wheel SHA-256: " + registry.candidate.wheel_sha256),
        node("p", registry.candidate.wheel_availability),
        node("p", "Published v0.13.2 is a separate historical baseline, predating the FFT correction and graph backend."),
        node("code", "Published source: " + registry.published_baseline.source_commit),
        node("code", "Published wheel SHA-256: " + registry.published_baseline.wheel_sha256),
        node("p", "Use your rebuilt wheel's measured hash in the intake. Do not copy the original wheel hash. Wolfram comparator v1 accepts only the original pinned packet."),
        link("Frozen registry source", REPO + "/blob/" + REGISTRY_COMMIT + "/research/challenges/registry-v1.json"),
        document.createTextNode(" · "), link("Pilot owner engineering record", registry.engineering_review.record_url)
      );
      panel.append(detail("Candidate identity versus published package", identity));
      panel.append(node("p", "A public GitHub handle can identify the accountable human. Disclose independence, AI assistance, commands, environment and measured hashes. Use NOT_RUN for conceptual feedback; never post secrets or private data.", "sc-note"));
      renderAssistant(challenge);
      status.textContent = challenge.id + " selected. Frozen numerical evidence; independent scientific review pending.";
    }
    registry.challenges.forEach(challenge => {
      const button = node("button", undefined, "sc-choice");
      button.type = "button";
      button.dataset.challengeId = challenge.id;
      button.setAttribute("aria-controls", panel.id);
      button.append(node("small", challenge.id), node("strong", challenge.title),
        node("span", challenge.case_count + " bounded cases"));
      button.addEventListener("click", () => select(challenge));
      buttons.push(button);
      choices.append(button);
    });
    view.replaceChildren(choices, panel);
    select(registry.challenges[0]);
  }

  function unavailable() {
    view.replaceChildren();
    status.textContent = "Challenge data unavailable or inconsistent. No scientific status can be inferred. Use the source guide and review gate below.";
    assistants.forEach(assistant => {
      assistant.replaceChildren(node("p", "Registered challenge guidance unavailable. No judgment is inferred."),
        link("Open the source reviewer guide", GUIDE));
    });
    retry.hidden = false;
  }

  async function load() {
    retry.hidden = true;
    view.replaceChildren();
    status.textContent = "Checking the frozen challenge catalog…";
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 8000);
    try {
      const url = new URL(root.dataset.scientificChallenges, window.location.href);
      if (url.origin !== window.location.origin) throw new Error("Cross-origin catalog");
      const response = await fetch(url.href, {signal: controller.signal, cache: "no-cache", redirect: "error"});
      if (!response.ok) throw new Error("Catalog unavailable");
      const data = await response.arrayBuffer();
      if (data.byteLength > 100000) throw new Error("Oversized catalog");
      const digest = await crypto.subtle.digest("SHA-256", data);
      const actual = Array.from(new Uint8Array(digest), value => value.toString(16).padStart(2, "0")).join("");
      if (actual !== EXPECTED_SHA256) throw new Error("Catalog identity mismatch");
      // This exact data was schema/evidence-validated at generation time and in CI.
      const registry = JSON.parse(new TextDecoder("utf-8", {fatal: true}).decode(data));
      render(registry);
    } catch {
      // Do not reinterpret exception text as HTML or call unavailable data "passed".
      unavailable();
    } finally {
      clearTimeout(timeout);
    }
  }
  retry.addEventListener("click", load);
  load();
})();
