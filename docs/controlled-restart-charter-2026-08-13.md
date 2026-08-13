# Controlled Restart Charter: QS-DMSS

Date: 2026-08-13

Repository: `AI-Bio-Synergy-Holdings-LLC/QS-DMSS`

Baseline default head: `55141f783ae575abb7a63938f8762301e089012b`

Operational project ID: `qs-dmss`

Asset registry ID: unassigned

## Decision

The completed `lumical-studio` bounded delivery and its protected central
ledger closeout satisfy the prerequisite for one further repository
admission. The owner has explicitly authorized the recommended sequence.

This protected charter admits exactly one repository to the next controlled
engineering step. QS-DMSS remains `PENDING_KICKOFF` until this charter reaches
`main` through the normal protected merge path. That merge changes only
QS-DMSS to `ACTIVE_CONTROLLED`.

After protected merge, the only engineering-active repositories are:

1. `AI-Bio-Synergy-Holdings-LLC/portfolio-control-plane`
2. `AI-Bio-Synergy-Holdings-LLC/lumical-studio`
3. `AI-Bio-Synergy-Holdings-LLC/QS-DMSS`

Every other organization repository remains `PENDING_KICKOFF`. The canonical
public-website monorepo is owned by a personal GitHub account, remains outside
the 42-repository organization census, and is not an engineering admission.

## Asset-identity boundary

The repository slug and project name are technical identifiers only. They are
not a registered asset name or an asset-ownership mapping. `assetRegistryId`
remains null and the asset-mapping status remains `UNASSIGNED`.

Any future asset reference must use a separately authorized registry ID. This
charter does not create or infer one.

## First bounded delivery

Once this charter is merged, QS-DMSS may have one protected feature pull
request active at a time. The first delivery is limited to deterministic
validation of the independent-review evidence packet associated with Fractal
SSFM v0.13.2 and issues #105 and #183.

Authorized work is limited to:

- a closed manifest or schema for required reviewer-facing evidence;
- deterministic file inventory, hash, version, command-receipt, and provenance
  consistency checks;
- rejection of missing, duplicate, unsafe, unlisted, or tampered evidence;
- tests, CI, and documentation necessary to validate those controls; and
- non-executing reviewer guidance for reproducing the validation locally.

The feature may validate an evidence package. It may not declare the
underlying scientific model independently validated.

This charter pull request contains governance records only. It does not alter
runtime behavior, dependencies, scientific algorithms, claims, releases, or
deployment configuration.

## Retained prohibitions

The following remain prohibited:

- claiming independent scientific validation from owner-authored evidence or
  closing issues #105 or #183 without the required external review;
- changing scientific conclusions, Fractal SSFM semantics, calibration
  claims, or benchmark claims in the first bounded delivery;
- adding an HPC, Slurm, QPU, cloud-provider, data-provider, or execution
  connector;
- publishing a release or package, changing production deployment authority,
  or adding autonomous repository actions;
- any Holdings connector, credential, mount, token, network path, or private
  asset-data access;
- Control Plane repository execution, actuation, automated merge, deployment,
  transaction, diligence, or Gate 6 authority;
- representing an internal development identifier as registered asset
  identity;
- admin bypass, force push, history rewrite, unprotected merge, or weakened
  required checks; and
- activating another repository without a separate protected charter and
  explicit owner approval.

## Entry controls

The admission baseline captured at `2026-08-13T20:04:29.020Z` is:

- default branch `main` at `55141f783ae575abb7a63938f8762301e089012b`;
- exact-head status rollup `SUCCESS`;
- zero open pull requests;
- strict required Python 3.10-3.13, Docker smoke,
  `policy / Organization baseline`, and `metadata / PR metadata` checks pinned
  to GitHub Actions app `15368`;
- zero open high or critical Dependabot alerts;
- zero open CodeQL alerts;
- zero open secret-scanning alerts;
- Dependabot security updates, secret scanning, and push protection enabled;
  and
- successful production auto-deploy verification on run `31228889437`.

## Exit criteria for the first bounded delivery

The delivery is complete only when:

1. the pull request is exact-head and all required checks are successful;
2. Ruff, tests with the repository coverage floor, Bandit, pip-audit, build,
   Docker smoke, and applicable frontend validation pass;
3. high and critical dependency, CodeQL, and secret-scanning findings remain
   zero unless separately accepted in a protected risk record;
4. the evidence contract is deterministic, documented, and tested against
   missing, duplicate, unsafe, unlisted, and tampered inputs;
5. the result makes no independent scientific-validation claim and does not
   close #105 or #183 without external review evidence;
6. no provider, Holdings, execution, actuation, deployment-authority, or Gate 6
   path is introduced;
7. the observe-only Control Plane records a signed review; and
8. the central organization ledger records the result through a protected
   pull request.

## Operating limit

This admission raises the organization from exactly two to exactly three
engineering-active repositories. A fourth repository cannot enter engineering
until QS-DMSS completes this bounded delivery, the Control Plane and central
ledger record the result, and the owner explicitly authorizes another charter.
