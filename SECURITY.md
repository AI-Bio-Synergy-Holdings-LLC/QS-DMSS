# Security Policy

## Supported Versions

The currently supported public release line is `v0.9.x`, beginning with
`v0.9.0`.

Current `main` may include security or governance fixes that have not yet been
packaged into a release. As of the latest repository maintenance pass, `main`
contains the post-`v0.9.0` NOTICE packaging fix and the safe Starlette
dependency floor.

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
