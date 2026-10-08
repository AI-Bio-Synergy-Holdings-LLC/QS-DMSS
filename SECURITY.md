# Security Policy

## Supported Versions

The currently supported public release line is `v0.13.x`, beginning with
`v0.13.2`.

The current development line is `v0.14.x`, under release preparation and not
yet published. Security fixes target this `main` source first. Publishing 0.14.0
and changing the supported public line require the separate publication gate;
the preparation version bump does not silently end v0.13.x support.

Current `main` may include security or governance fixes that have not yet been
packaged into a release. Security fixes should target `main` first and be
backported to `v0.13.x` only when the maintainer determines that a public patch
release is required.

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
