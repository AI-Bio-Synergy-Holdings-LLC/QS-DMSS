# QS-DMSS v0.13.2 Release

## Purpose

v0.13.2 is a backward-compatible reliability and security patch for the
research-grade Studio experience. It aligns the installable local cockpit with
the quantum-validation freshness behavior already verified in the hosted
deployment, hardens public HTTP responses, and preserves a clear boundary
between the current package version and the latest archived DOI.

## What Changes

- A completed local quantum-validation run now invalidates the prior client
  cache, reloads the latest persisted result, and redraws every topology and
  optimization attribution row. The recommended configuration remains a
  highlighted row rather than a redraw gate.
- Quantum-validation status copy identifies the persisted run, generation time,
  source, package version, and evidence downloads more clearly.
- Public cockpit responses include a baseline Content Security Policy,
  anti-framing, MIME-sniffing, referrer, and HSTS headers.
- `/api/health` retains public status, release, capability, and hosted-demo
  fields while omitting server filesystem paths.
- Unexpected cockpit request failures emit a stable
  `cockpit_request_failed` operator event without exception text, request data,
  credentials, or filesystem paths.
- Studio portal and hosted-demo social previews use stable, cache-busted public
  assets introduced after v0.13.1.
- Pull-request fresh-install smoke builds and installs the candidate wheel on
  Linux, macOS, and Windows instead of validating an outdated published
  baseline.

## Scientific Claim Boundary

This patch does not change the simulator-first scientific boundary. Quantum
validation uses local ideal simulators and generic topology profiles. It does
not use provider credentials, remote APIs, QPU execution, job submission,
authorized spend, or claims of quantum advantage. QS-DMSS remains beta workflow
software and is not peer-reviewed scientific validation.

## Release Verification

Publication completed from merge commit `7a063eb91af6c50e483c2d062bf6cee0daf709e4`:

1. Run the full test suite and CodeQL checks.
2. Build one wheel and one source distribution from the release commit.
3. Run `python -m twine check` against both artifacts.
4. Install the candidate wheel in a clean environment and exercise the bundled
   demo, campaign, showcase, and cockpit health paths.
5. Confirm the local quantum extra can execute and persist a fresh 12-row
   compilation validation with all configured rows passing.
6. Publish the exact GitHub release artifacts to PyPI through Trusted Publishing.
7. Zenodo archived the release as `10.5281/zenodo.21366910`; the
   post-publication change synchronizes that DOI and the release links across
   public surfaces.

Published artifacts:

- GitHub: <https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/releases/tag/v0.13.2>
- PyPI: <https://pypi.org/project/qs-dmss/0.13.2/>
- Zenodo: <https://zenodo.org/records/21366910>
- Wheel SHA-256: `6f22876fa625681aa72b96d99e14de92cfd5cfae870fc53d9d41673ebf82416f`
- Source archive SHA-256: `2c7c6a78974d0bcfd3cb558fe377b1425d3e265ee4e3b79b17f36207d822cfcf`

## Citation

Use the stable project concept DOI for project-level citation:

```text
10.5281/zenodo.20074924
```

Use the version-specific DOI when citing this exact release:

```text
10.5281/zenodo.21366910
```
