# ADR 0001: Commercial Sustainability And Licensing Boundary

- Status: Accepted
- Date: 2026-07-13
- Decision owner: AI-Bio Synergy Holdings LLC
- Applies to: QS-DMSS public core, distributions, hosted services, contributions,
  and future commercial offerings
- Release gate: required before `v0.12.0` preparation

## Context

QS-DMSS is publicly developed and distributed under the Apache License,
Version 2.0. The project is also presented as open-source research software on
GitHub, PyPI, Zenodo, QS-DMSS Studio, and Open Source Collective, with a future
JOSS/pyOpenSci review path.

The project needs a sustainable commercial model without creating ambiguity
about whether researchers can install, inspect, modify, redistribute, cite, or
reproduce the public software. A proposed research-only license would restrict
fields of use and would therefore no longer satisfy the Open Source Definition.
It would also conflict with the current public collaboration and fiscal-hosting
strategy.

Existing Apache-2.0 grants are perpetual and irrevocable subject to the license
terms. Previously published releases, archives, repository copies, and lawful
forks cannot be converted retroactively into research-only software.

Authoritative context:

- [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0.html)
- [Open Source Definition](https://opensource.org/osd)
- [Open Source Collective eligibility](https://docs.oscollective.org/interested-in-joining-osc/acceptance-criteria)
- [JOSS submission requirements](https://joss.readthedocs.io/en/latest/submitting.html)
- [pyOpenSci peer-review policies](https://www.pyopensci.org/software-peer-review/our-process/policies.html)

This record is a project governance decision, not legal advice. Bespoke license,
trademark, contributor, customer, or service terms require qualified counsel
before adoption.

## Decision

### 1. The Public Core Remains Apache-2.0

The QS-DMSS public core will remain licensed under Apache-2.0 for `v0.12.0` and
the foreseeable public release line.

The public core includes:

- code and original documentation in the canonical public repository;
- the `qs-dmss` wheel and source distribution;
- packaged scenarios, schemas, study templates, validation profiles, and demo
  assets included in those distributions;
- public CLI, local cockpit, evidence, replay, campaign, HPC dry-run, and
  simulator-only quantum-readiness interfaces.

Third-party material retains its own license and attribution where explicitly
identified. No restricted component may be silently added to the Apache-2.0
distribution.

### 2. Research-Only Relicensing Of The Public Core Is Rejected

QS-DMSS will not add non-commercial, research-only, ethical-use, field-of-use,
or no-production restrictions to the public core while calling that core open
source.

The existing Apache license will not be modified with an additional clause. A
modified Apache-derived license would be a new license and would require legal
review, complete metadata/public-surface changes, and a different product
positioning.

### 3. Commercial Value Must Use A Clear Separation Boundary

AI-Bio Synergy Holdings LLC may offer separately governed commercial services
and deliverables around the Apache-2.0 core, including:

- managed hosting, private deployment, monitoring, backups, and service-level
  commitments;
- private collaboration workspaces, identity/access administration, and
  organization-specific storage or retention;
- customer-specific deployment automation, HPC/site integration, and provider
  integration work;
- support, training, implementation, validation consulting, and sponsored
  engineering milestones;
- separately packaged proprietary integrations or operational tooling, after
  dependency, distribution, contribution, and legal review.

Commercial components must be separately named, packaged, documented, and
licensed. They must not be committed to the public core repository or included
in the public wheel/source distribution unless they are intentionally released
under Apache-2.0.

### 4. Hosted-Service Terms Do Not Change Code Rights

The official hosted service may enforce acceptable-use, privacy, security,
retention, rate, compute, and artifact-size limits. Those service controls apply
only to the managed service. They do not reduce rights granted for the local
Apache-2.0 software.

The public hosted demo must continue to state that outputs are temporary and
that sensitive data must not be uploaded. Paid hosted offerings require
separate service terms and privacy/security review before launch.

### 5. Ownership, License, Citation, And Brand Are Distinct

AI-Bio Synergy Holdings LLC remains the project steward and identified
copyright owner without limiting Apache-2.0 user rights.

Apache-2.0 does not grant permission to use project or company names, logos, or
marks to imply endorsement. Descriptive references such as "uses QS-DMSS" or
"compatible with QS-DMSS" remain appropriate. A standalone trademark policy
may be adopted later after brand/legal review; this decision does not assert a
trademark registration that does not exist.

Citation requests support reproducibility and scholarly credit. They are not
additional software-license conditions.

### 6. Public Contributions Use Inbound-Equals-Outbound Terms

Contributions intentionally submitted to the public QS-DMSS repository are
accepted for distribution under Apache-2.0. Contributors must have the right to
submit their work and disclose incompatible third-party material.

This decision does not impose a contributor license agreement or copyright
assignment. If the project later needs dual licensing or a commercial component
that incorporates third-party contributions, counsel-reviewed contribution
terms must be adopted before accepting that work. Existing contributors'
rights and grants must not be assumed or rewritten retroactively.

### 7. Data, Models, Outputs, And Integrations Need Independent Review

The Apache-2.0 software license does not automatically license:

- third-party datasets or provider products;
- user-supplied configurations, annotations, or private workspaces;
- trademarks, credentials, service accounts, or calibration snapshots;
- simulation outputs owned or controlled by users under applicable law and
  input-data terms.

Every future data pack, model, provider adapter, or hosted integration must
record its source, license/terms, redistribution status, credentials boundary,
and evidence implications.

## `v0.12.0` Release Gate

Preparation of `v0.12.0` may begin only after this decision is merged and the
following conditions are maintained:

1. `LICENSE`, `NOTICE`, `pyproject.toml`, citation metadata, and public license
   statements continue to identify Apache-2.0 correctly.
2. The wheel and source distribution contain no research-only or proprietary
   component.
3. Optional dependencies and bundled assets pass license/provenance review.
4. Hosted-service limits are described as service controls, not software-use
   restrictions.
5. Release notes preserve the scientific and quantum/HPC non-claim boundaries.
6. Funding language distinguishes donations/sponsorship from paid service or
   endorsement.
7. CI, security scanning, package checks, and fresh-install validation pass.

This decision authorizes no version bump, tag, GitHub release, Zenodo archive,
or PyPI publication by itself.

## Consequences

Positive consequences:

- researchers retain a stable and unambiguous reproducibility license;
- QS-DMSS remains aligned with Open Source Collective and potential JOSS or
  pyOpenSci review;
- commercial services can be developed without misrepresenting the public
  core;
- contribution and release decisions gain an explicit boundary before outside
  participation grows.

Tradeoffs:

- competitors may lawfully use and redistribute the Apache-2.0 core;
- commercial differentiation must come from execution quality, operations,
  integrations, support, validation, trust, and service delivery;
- any future proprietary component needs separate engineering and governance
  hygiene.

## Alternatives Considered

### Research-only license for the next QS-DMSS release

Rejected. It would not revoke earlier Apache rights, would end open-source
positioning for the new release, and would conflict with current review,
funding, and adoption goals.

### Dual-license the complete public core immediately

Rejected for now. There is no demonstrated customer requirement or
counsel-reviewed contribution framework that justifies the complexity.

### Change the core to a network copyleft license

Deferred. An OSI-approved network copyleft license could be evaluated if a
specific hosted-service appropriation risk emerges, but changing the public
license without demonstrated need would create adoption and compatibility
costs.

### Keep all future work in the public core

Not required. Apache-2.0 permits a sustainable services model, while genuinely
separate commercial components may be developed outside the public
distribution under appropriate terms.

## Reconsideration Triggers

Revisit this decision only when one or more concrete triggers occur:

- a signed institutional or commercial requirement cannot be met through
  services/support around the public core;
- a provider or data license requires a separately distributed integration;
- significant external contributions require a formal DCO, CLA, or governance
  structure;
- qualified IP counsel recommends a documented change;
- Open Source Collective, JOSS, pyOpenSci, or another relied-upon program
  changes its eligibility requirements;
- the project creates a separately named product whose scope and audience are
  materially different from QS-DMSS.

Any reconsideration requires a new decision record, an inventory of affected
copyright holders and dependencies, a public migration plan, and explicit
approval by the project steward before implementation.
