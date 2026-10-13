# SC-GRAPH-001 recorded explorer and social handoff

## Scope and authorization

Owner approved the four-case, boundary-focused recorded prototype and the
dedicated portal URL/custom-card recommendation. This pass prepares and locally
qualifies that handoff. Protected review, merge, public deployment, LinkedIn
posting and any reviewer outreach are separate steps. No new scientific
calculations, release changes, AI activation or graph execution are included.

Intended URL after approved deployment:
`https://qs-dmss.studio/challenges/sc-graph-001/`. The route uses the existing
Render static portal, its `site` root and `python build_portal.py` command; no
new hosting service or DNS change is required. The homepage and challenge have
different Open Graph metadata. Hash-fragment view state does not create a
different social preview.

## Evidence and visual contract

The frozen candidate is `48d7ab5d10da189caddbcad1dd6622e58d204940`, distinct
from published v0.14.0. The presentation JSON is 39,979 exact bytes, SHA-256
`ed955ee0de108dddfd652a5cf0f847bbfc10332a9292623a5cf644ba5bfaf1ec`.
It copies graph_04, graph_07, graph_10 and graph_13 from the unchanged pilot
packet `17e568bf7944972c57eda3f275ec7a1126f1cd3d92a4fa04308063425ef02ba4`.
Reference/candidate arrays, record fields and source pointers are checked
against the retained packet, without running a solver or reference calculation.
Numerical `NOT_FALSIFIED_WITHIN_SCOPE`, scientific `NOT_ESTABLISHED`, independent
review `PENDING` and human disposition `PENDING` remain separate.

Each layer received a local specialist pass; no agents were delegated:

| Layer | Purpose and encoding | Interaction / fallback | Qualification |
| --- | --- | --- | --- |
| Reference graph | Inspect full/active boundary membership; integer lattice placement, not physical distances | Numbered circle/interior and diamond/boundary; tap/Enter/Space selection; mass table | Four cases, node detail and exact full/active IDs |
| Stiffness table | Inspect retained principal restriction, full-ID row labels | Candidate/reference select; selected row/column; bounded horizontal scroll | Exact recorded arrays and URL restore |
| Spectrum | Compare retained ordered generalized eigenvalues | Filled candidate/open reference markers; raw-value table | Preserve roundoff, degeneracies and no physical mode matching |
| Social card | Invite inspection of the boundary convention | 1200×630 annotated graph/question, no validation badge | Full-size and feed-size review, source SVG check |
| Video | Optional edited explanation, not live execution | Native controls, no autoplay, burned-in explanations plus text/VTT | Approved original retained; separately hashed small delivery copy and CC0 credit |

### Technical design

One native SVG graph and one conditional SVG spectrum; at most 15 vertices,
27 edges and 15 ordered eigenvalues. Native ES modules own state and DOM tables;
no D3 dependency is needed for these small fixed recorded arrays. Geometry,
validation, loading and rendering are separated. Data transport is bounded to
100,000 bytes and manifest transport to 10,000 bytes with a 15-second timeout.
Invalid identity/state fails closed with a retry/reset path, never a verdict.
No uploads, analytics, persistence, accounts or permission-gated sensors.

Desktop pairs graph/operator. Mobile portrait leads with the graph, then
controls and operator; landscape preserves contained table scrolling. Primary
controls and invisible node hit areas are 44 CSS px. No hover-only information,
drag/pinch capture or text input is required. Selected case, caveats and source
remain visible; hash state supports refresh/back/forward/copy/reset.
On mobile, a selected-case summary and explicit “View selected graph” control
return focus and scroll to the affected graph after a configuration change.
Reduced-motion has a static path. External script/CSS and same-origin assets
preserve the current production CSP without new hashes or directives.

### Card direction and narrative

Considered: question plus annotated recorded graph; operator-matrix specimen;
and low-containment editorial question only. Selected the first because the
active/excluded relationship is visible before a click. The capsule hard filters
are static/English/medium/documented/network. `agent-ring` wins the fixed weights
(explain-system + show-relationships = 16; network = 5), transferred as named
graph relationships, not a decorative orbit. The custom annotated blueprint
uses the actual triangular lattice instead of a radial role ring. No named
third-party identity assets are required or approximated.

Hook: which boundary? Evidence: six full vertices, three active. Payoff: inspect
the convention and offer an accountable assessment; agreement is not approval.
The approved forest/copper palette and editorial serif/system sans pairing are
retained. No remote font or generated scientific imagery. The 1200×630 canvas
has 56 px horizontal margins, an open question zone, one recorded graph and a
reserved pending-review footer; no nested cards or decorative motion.

## Qualification and approval handoff

Local qualification on 2026-10-12:

- Existing Windows Python 3.14.3 environment: 899 passed, 25 skipped; 91.44%
  coverage, exceeding 88%. This is supplementary, not the supported matrix.
- Fresh supported Windows Python 3.12.14 environment: 884 passed, 40 skipped.
  Quantum/optional test skips are not represented as successful quantum gates.
- JavaScript: 95 passed, including 55 explorer/state/transport cases. Final
  focused Python recheck: 64 passed. Ruff, registry consistency, discovery
  synchronization, JavaScript syntax and social-card source checks passed.
- Fresh 3.12 dependency audit after upgrading only its isolated pip: no known
  vulnerabilities. Source Bandit medium/high checks passed. The pre-existing
  `.venv` still has urllib3 2.7.0 tooling advisories PYSEC-2026-4175/4176/4177;
  it was not modified because it may serve the owner's local app. This is an
  explicit local-environment maintenance item, not a clean-audit claim for it.
- Wheel/sdist built into a separate QA directory; Twine passed. Installed-wheel
  version/import/config smoke passed. No published artifact was replaced. The
  Python sdist retains small portal test fixtures; the 15,981,923-byte MP4 stays
  portal-only and is excluded from Python distributions.
- Docker image built; loopback hosted-mode health/config/HTTP-header smoke
  passed with `hosted_custom_compute=false` and `ai_advisory_drafts=false`.
  The initial probe raced startup, then passed after readiness; the owned test
  container was removed. This was not a production deployment.
- In-app browser: four cases, candidate/reference, spectrum, Enter/Space node
  selection, reset/copy/URL restoration, mobile return-to-graph and unavailable
  states checked. Desktop 1440×1000, portrait 390×844 and landscape 844×390
  had no document-wide overflow. Wide matrices scroll within their container.
  Normal-page console warnings/errors were empty. Native video loaded a
  60-second timeline and played following a user-like click; it does not autoplay.
- Social PNG: 1200×630, 315,812 bytes, SHA-256
  `8f3dddb7ef4a0052636795a531f3e70048282677b7af9d8def4e29762b1f984a`.
  The image test caught a JPEG browser capture with a PNG filename; it was
  converted to genuine PNG and rechecked. Original evidence/media are unchanged.
- Card perception/visual pass: question dominates, active/excluded relationship
  survives thumbnail/grayscale inspection, pending-review footer is attached,
  no clipping, remote fonts, nested cards, invented metrics or decorative motion.
  All blocking taxonomy items pass; no remaining craft defects recorded.
  Owner review and approval of this handoff were confirmed in chat on
  2026-10-12. LinkedIn rendering and publication/outreach approval remain pending;
  no subjective listening result is asserted by the automated checks.

Remote Python 3.10–3.13, quantum, security, packaging/Docker and review gates
remain required on a PR.
Do not represent a local pass or a private design preview as public deployment.

### PR #203 web-delivery correction

The initial organization-policy gate rejected the 15,981,923-byte MP4 against
its unchanged 10,485,760-byte maximum. The owner separately approved a smaller
delivery copy, retention of the exact approved original and requalification,
without merge, deployment, outreach or scientific-status changes.

- Delivery: `boundary-explanation-web-v1.mp4`, 1,986,425 bytes, SHA-256
  `e88cc89d77a3989c725a67fbbd411d2e35134ccad6fac96e5a6dba037c4840e6`.
  FFmpeg 7.1/libx264 re-encodes only the video with CRF 24, slow/stillimage,
  a 1,000 kbit/s maximum rate and 2,000 kbit buffer. Dimensions remain
  1080×1350 at 30 fps, with all 1,800 frames and the 60-second sequence.
  Global metadata, including the original rights credit and pending-review
  comment, is copied. Fast-start metadata precedes media bytes.
- The approved original SHA-256
  `0e49295279b8698655fe896415adc7873bd3bfa2d2222960d86517427d2b2404`
  was checked before and after encoding. Exact bytes remain in the owner-held
  `linkedin-demo/captions-piano-v2` production bundle and prior PR commit
  `5e094782dd0926475350533a54e0e6150ceb2494`. The original is removed only
  from the served tree; no history rewrite or policy exception is used.
- Copied AAC compressed-payload hash:
  `8fc59b69a1f9c2f0ea6d24bee61d96ea63999ef89f170471ab7ede18d2a36dcf`.
  Source and derivative payloads match. Caption timing, transcript, poster,
  CC0 rights references and scientific-status footer remain unchanged.
- Technical comparison: all-frame SSIM 0.997942 versus the approved video;
  27 start/middle/end samples cover all nine scenes. Whole-frame, caption-band
  and status-footer mean absolute RGB errors stay below 4 per channel.
  Decoded first/middle/final frames and desktop/mobile playback were inspected.
  This is media qualification, not scientific or subjective-listening approval.
- Local requalification: 900 passed / 25 skipped, 91.46% coverage in the
  supplementary Windows 3.14 environment; supported Windows 3.12 had 885
  passed / 40 skipped. Final delivery/provenance recheck: 11 passed.
  JavaScript: 95 passed. Ruff, Bandit, isolated dependency audit, registry,
  discovery synchronization and social-card source checks passed. The previously
  documented owner-environment tooling advisories remain untouched.
- Rebuilt wheel/sdist and Twine checks passed; neither distribution contains
  an MP4. Testing the extracted sdist exposed missing homepage/sitemap fixtures;
  both small files are now included rather than weakening the metadata test.
  Extracted-sdist explorer tests: 10 passed / 1 intentionally skipped media test.
  Separate installed-wheel import/version/config/CLI smoke passed.
- Flow: local recorded explorer → native play control → decoded 60-second
  delivery video → pause/reload, with no autoplay. Playwright CLI checked
  desktop 1440×1000 and mobile 390×844 because the Browser skill/runtime was
  unavailable in this session. Correct URL/title, meaningful page content,
  no error overlay, empty warning/error console and no horizontal page overflow
  passed. Screenshots and comparison receipt are retained in the owner-held
  `portal-qa` directory. No public route or LinkedIn preview has been exercised.

`media-provenance.json` version 2 distinguishes source from delivery identity.
Regression tests enforce exact delivery bytes/hash, the unchanged size policy,
original retention pointers, safe local source selection and scientific-status
preservation. Remote gates must pass at the correction's new PR head; the
earlier successful matrix/Docker/security checks are not substituted for it.

### PR #203 accessibility correction

The first Copilot review identified two medium findings: the transcript existed
only inside video fallback content, and mobile CSS reordered graph/controls
visually without changing DOM/keyboard order. Both were reproduced in the local
preview and corrected with separate owner authorization on 2026-10-13.

- The existing transcript now has a normal, visible link outside `<video>`.
  It is reachable with the keyboard, opens the unchanged transcript and has a
  44 px touch target. Native video fallback, captions and media are preserved.
- Workbench source order is graph → controls → operator. Mobile uses that same
  vertical sequence; desktop places the graph on the left and controls above
  the operator on the right. CSS `order` and `display: contents` no longer
  rearrange focusable regions. No positive `tabindex` or scripted Tab ordering
  was introduced. The explicit mobile return-to-graph action remains available.
- Two new contract tests failed before the fix, then passed afterward. They
  check transcript ancestry/reachability and source/responsive region order.
  Focused explorer tests: 13 passed. Full supplementary Windows 3.14:
  902 passed / 25 skipped, 91.44% coverage. Supported Windows 3.12:
  887 passed / 40 skipped. JavaScript: 95 passed. Ruff, Bandit, isolated
  dependency audit, registry/discovery consistency and social-card checks passed.
- Playwright CLI checked desktop 1440×1000, portrait 390×844 and landscape
  844×390 because the Browser skill/runtime was unavailable. Mobile Tab now
  visits graph vertices and their table before controls and operator tabs.
  Graph Enter/Space activation retains focus; transcript focus/Enter navigation
  succeeds. All four cases, matrix-source selection, spectrum visibility, URL
  state, mobile return-to-graph and no horizontal page overflow were checked.
  Normal-page warning/error console was empty; page identity/content and
  screenshots showed no runtime overlay. This is not a full assistive-technology
  certification or a production/LinkedIn check.
- Rebuilt wheel/sdist/Twine and extracted-sdist tests passed: 12 passed /
  1 intentionally skipped portal-only media test. Both distributions exclude
  MP4s. Qualification artifacts and before/after screenshots are retained in
  the owner-held `portal-qa` directory without replacing the earlier records.

Only markup, styles, contract tests and this qualification record change.
JavaScript behavior, media/provenance, retained evidence, acceptance limits,
published versions and scientific statuses remain unchanged. Remote gates and
one Copilot re-review are required at the new correction head; no merge,
deployment or outreach is authorized by this correction.

### PR #203 manifest and artifact contract hardening

The owner separately approved the two previously missed concerns in Copilot's
re-review on 2026-10-13: unchecked manifest scope declarations and missing CI
archive assertions. This correction does not alter the manifest or any retained
scientific/media material, and does not authorize another review request, merge,
deployment or outreach.

- `validateManifest` now requires the exact frozen `origin`, `control_scope`
  and `presentation_scope` strings. Missing fields, changed claims and non-string
  values are refused before rendering. The manifest itself stays byte-identical,
  SHA-256 `b4e38c4594b37395d657972eb084be30c47f946713b0815475eced5fa6f945d6`.
- Eighteen new JavaScript mutation cases failed before the guard was added and
  pass afterward. Combined JavaScript qualification: 113 passed, including
  73 explorer tests. Focused Python explorer tests: 13 passed.
- The existing Python 3.10–3.13 CI archive-inspection step now asserts all
  declared small explorer fixtures and supporting test/generator files are in
  the sdist. It rejects `.mp4` entries case-insensitively in both wheel and sdist;
  source fixtures are not added to the runtime wheel. The 10 MiB Git cap and
  existing package contents/metadata are unchanged.
- Rebuilt wheel/sdist and Twine checks passed. The exact reviewed CI Python
  archive step was executed locally on those builds, then on QA-only copies
  containing an uppercase MP4 in the wheel, an uppercase MP4 in the sdist, or
  a missing `loader.mjs` fixture. Valid artifacts passed; all three invalid
  variants failed the intended assertion. Earlier QA artifacts were preserved.
- Full supplementary Windows 3.14: 902 passed / 25 skipped, 91.46% coverage.
  Supported Windows 3.12: 887 passed / 40 skipped. Ruff, Bandit, isolated
  dependency audit, registry/discovery synchronization and card-source checks
  passed. Previously documented owner-environment tooling debt was not changed.
- Playwright CLI checked desktop and portrait because the Browser skill/runtime
  was unavailable. Synthetic HTTP responses changing each of the three scope
  declarations were refused with an unavailable state, hidden explorer and
  cleared graph; Retry with the untouched manifest restored the recorded view.
  The four recorded cases, spectrum view, accessible transcript, page identity,
  no overflow and normal-page console health were checked. The initial QA mock
  used the wrong API-response header method; the harness was corrected and all
  three rejection/Retry paths were repeated successfully in a clean browser.
  QA interception changed no repository files and ran no scientific calculations.

Only the validator, mutation tests, CI assertions and this record change.
Manifest/media/evidence, published version and all scientific statuses are
preserved. Remote qualification must pass at the new correction head rather
than reusing the previous head's green checks.

After an approved merge/deployment: verify HTML, exact image and video URLs,
production CSP, expected deployment commit and read-only interactions. Use
LinkedIn Post Inspector on the dedicated URL before preparing the link-card
post. Cached previews on already-published posts are not guaranteed to update.
A native-video post uses its own thumbnail; do not promise a second URL card in
that post. Final outreach still needs the owner's approval.
