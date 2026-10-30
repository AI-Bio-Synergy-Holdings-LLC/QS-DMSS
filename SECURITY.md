# Security Policy

## Supported Versions

The current published release line is `v0.14.x`, beginning with `v0.14.0`.
The `v0.15.0` source target is under preparation, not a published release.
Security fixes target `main` first; publication requires a separate approval.

This preparation does not end the existing `v0.13.x` support/backport policy
(beginning with `v0.13.2`), declare an end-of-support date, or automatically
promote `v0.15.x` to the supported public line. Any such policy change requires
an explicit maintainer decision.

Current `main` may include security or governance fixes that have not yet been
packaged into a release. Security fixes should target `main` first and be
backported to a published line only when the maintainer determines that a public
patch release is required. The existing maintainer-directed `v0.13.x` backport
decision remains available; it is not silently revoked by the version bump.

Earlier public release lines remain archived and citable, but security fixes
should target the current supported line unless a maintainer explicitly decides
that a backport is necessary.

## Reporting a Vulnerability

Use GitHub Issues for non-sensitive bugs, packaging problems, and hardening
requests.

For sensitive vulnerability reports, do not post exploit details publicly. Use
GitHub private vulnerability reporting or a private repository-owner channel
before disclosure. The project owner will acknowledge valid sensitive reports,
coordinate remediation scope, and publish fix guidance through a tagged release
when applicable.
