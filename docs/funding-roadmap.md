# Funding Roadmap

QS-DMSS funding should be tied to visible public outcomes. The project is most
fundable when supporters can see what their contribution unlocks in the open:
better simulation workflows, stronger evidence artifacts, clearer reports, and
more contributor-ready build surfaces.

Support QS-DMSS through Open Collective:

```text
https://opencollective.com/qs-dmss
```

Funding support does not change QS-DMSS access, license, ownership,
attribution, or scientific-claim boundaries. See
[`ownership-and-use.md`](ownership-and-use.md).

Donations and public milestone sponsorship are distinct from paid hosting,
support, deployment, or integration services. The separation rules are defined
in the accepted
[commercial sustainability and licensing boundary](decisions/0001-commercial-sustainability-and-licensing-boundary.md).

## Funding Principles

- Fund outcomes, not vague maintenance.
- Keep the code, docs, issues, and release artifacts public.
- Preserve the scientific boundary: funding does not imply peer-reviewed
  validation or endorsement of a physical model.
- Report progress through GitHub issues, pull requests, releases, and Open
  Collective updates.
- Prefer small funded milestones that produce visible artifacts over broad
  promises.

## Suggested Support Levels

These are not paywalls. They are practical ways to describe what recurring or
one-time support helps make possible.

### Community Supporter: $5-$25/month

Helps keep the public package healthy.

Likely outcomes:

- dependency and CI maintenance;
- PyPI, GitHub release, and Zenodo metadata upkeep;
- issue triage and contributor onboarding;
- documentation fixes that reduce first-run friction.

### Builder Backer: $50-$150/month

Helps turn QS-DMSS from a package into a more usable lab.

Likely outcomes:

- new packaged showcase scenarios;
- clearer metric and figure exports;
- better evidence-bundle documentation;
- small cockpit improvements that make runs easier to inspect.

### Lab Mode Sponsor: $250-$750/month or milestone funded

Targets the next major product slice: QS-DMSS Lab Mode.

Likely outcomes:

- cockpit scenario launcher;
- run progress and status surfaces;
- embedded simulation plots and evidence summaries;
- verify/replay controls inside the cockpit;
- polished report export from selected runs or campaigns.

### Research Artifact Sponsor: $1,000-$3,000 milestone

Funds a named, citable artifact that improves the public research workflow.

Likely outcomes:

- a documented scenario pack;
- a benchmark/evidence comparison report;
- a publication-grade export template;
- a reproducibility walkthrough with generated example artifacts;
- an archival-ready release packet.

### Institutional or Infrastructure Sponsor: $5,000+ milestone

Supports larger public-good improvements that need deeper engineering time.

Likely outcomes:

- plugin architecture for scenarios, metrics, or report templates;
- alternative compute backend exploration;
- Distributed Research Workspace and HPC executor prototypes;
- larger validation scenario suite;
- hosted documentation or gallery infrastructure;
- workshop/tutorial materials for research-software communities.

## Near-Term Fundable Milestones

Builder coordination:
`https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/issues/57`

1. Lab Mode cockpit experience.
2. Publication-grade report export.
3. Scenario library and contributor scenario template.
4. Evidence Explorer for bundles, manifests, and replay status.
5. Campaign Studio for parameter search and objective tuning.
6. Research paper/JOSS packet grounded in generated evidence.
7. Distributed Research Workspace and executor architecture for future
   collaboration and HPC connector work.

## What Funders Should Expect

Supporters should expect public work products:

- linked GitHub issues;
- pull requests with visible validation;
- release notes for meaningful package milestones;
- documentation that explains what changed;
- Open Collective updates for funded milestones.

Supporters should not expect private scientific endorsement, private validation
claims, or hidden feature development that bypasses the public project.

## Best Current Funding Ask

The best current ask is:

> Help fund independent validation and interoperability for QS-DMSS: strengthen
> reviewer-ready numerical and quantum-compilation evidence, expand reproducible
> scenarios, and improve safe dry-run HPC/provider interfaces without adding
> unsupported execution or scientific claims.

That is the strongest current donation story because Lab Mode, Campaign Studio,
and publication exports have shipped. The next public value is making those
workflows easier to scrutinize, reproduce, extend, and integrate safely.

The current release target is `v0.11.0`, and the immediate
trust-building gate is scientific review of the installable Fractal/Quadrant
SSFM validation harness on
`https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/issues/105`. Funding
support should help convert that review and the merged quantum compilation
matrix into clearer validation artifacts, stronger documentation, and carefully
staged future build slices, not premature GPU/provider expansion or unsupported
scientific claims.
