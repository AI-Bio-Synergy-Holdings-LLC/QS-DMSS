# Repository health reconciliation: 2026-09-23

## Baseline and conversation corrections

- Remote main: `9574f8ba37d71eadf8c5ad25e1950a0d3b64805b` (PR #190).
- The clean local checkout started at `66d1f41`, the July AI-context extraction.
  Its remote branch had advanced by nine commits. Local main was twelve
  commits behind remote main. Both branches were fast-forwarded without
  rewriting history or deleting historical branches.
- PR #182 merged the workspace, campaign, and AI-context extraction on
  2026-08-03. The earlier conversation's "unpushed" status is superseded.
- PRs #187-190 established security-only Dependabot updates, the controlled
  restart charter, review-package validation, and rejection of ambiguous JSON.
- No PRs were open at the start of this reconciliation. Maintenance changes
  are on `codex/repository-health-sync-20260923` for protected review.
- Issue #105 closed after PR #189; independent scientific review remains
  outstanding in [issue #183](https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/issues/183).
  Passing package verification does not establish scientific validity.

## Findings and corrections

The existing main suite passed 180 tests at 89.84% statement coverage, but new
negative-input tests reproduced four evidence-validator defects:

1. An empty directory or ZIP returned success without a manifest.
2. List or object values in a file's `role` raised `TypeError`.
3. Receipt exit codes `false` and `0.0` were accepted as integer zero.
4. JSON numbers such as `1e999` overflowed to infinity despite rejection of
   literal `NaN` and `Infinity`.

The validator now requires a manifest even for empty input, reports invalid
roles as findings, requires an integer zero exit code, and rejects float
overflow during JSON decoding. Twelve regression cases cover the failures
and related invalid types; valid directory and ZIP contracts still pass.

The local dependency audit initially reported eight vulnerability entries
across `httpx2` 2.7.0, `httpcore2` 2.7.0, and pip 26.1.2. The development
dependency floor is now `httpx2>=2.12`; the verified local environment uses
httpx2/httpcore2 2.13.1 and pip 26.2.1. A subsequent `pip check` and
`pip-audit --local` reported no broken requirements or known vulnerabilities.
CI and Docker already upgrade pip during environment creation.

The Docker builder now copies `README-pypi.md` and `NOTICE`, making the package
description and notice available when its wheel is built.

## Remote and public checks

- GitHub APIs returned zero open Dependabot, code-scanning, and secret-scanning
  alerts. These counts do not replace auditing an installed environment.
- Main's Python matrix, quantum sidecar, Docker, policy, and production checks
  passed on 2026-08-15. Scheduled CodeQL and code-quality analyses passed on
  2026-09-22 for the same main commit.
- The public deployment verifier passed: app commit `9574f8ba37d71eadf8c5ad25e1950a0d3b64805b`,
  portal commit `b2e7f164123c339ccc148ca881ebe69659ceb2e2`, version `0.13.2`.
  The portal commit is the latest first-parent commit affecting `site/`, as
  required by the independent deployment cadence introduced in PR #186.
- Required CSP, frame protection, content-type, referrer, and HSTS headers
  passed; the portal also supplied Permissions-Policy.
- Hosted AI reports disabled, with no configured provider or model.

## Local validation of the maintenance changes

- Complete suite: **192 passed, 89.93% coverage** on Python 3.14.3, including
  the installed quantum extra; the 88% coverage floor passed.
- Ruff, Bandit (medium severity/confidence gate), Python compilation,
  JavaScript syntax, and whitespace checks passed.
- `pip check` and the installed-environment dependency audit passed.
- Demo-baseline benchmark validation passed.
- Wheel and source distribution built; both passed Twine metadata checks.
- The fresh-wheel smoke passed simulation, manifest verification, replay,
  six-run campaign, showcase generation, and live cockpit startup checks.
- Docker build passed. The non-root container served health and configuration
  endpoints, and its installed wheel contained the package description and
  `NOTICE`. The temporary smoke-test container was removed afterward.

Local build outputs and logs are retained under `.local/health-20260923/`,
`.tmp/health-20260923/`, and `.local-health-*.log` (not committed). Remote
candidate-branch checks are recorded on the maintenance PR, not inferred from
the earlier successful main checks.

## Remaining boundaries

The architectural and governance debt register remains open. Historical
feature branches are retained; branch divergence alone does not mean their
changes are missing from main after squash merges. The maintenance branch
must pass protected PR checks before its fixes can become the main baseline.
No release or production configuration change is part of this reconciliation.

Zero reported findings is a measured result for the tools, versions, and
surfaces checked on this date, not a guarantee that the software contains no
defects. GPU execution, independent scientific review, and an operating-system
container vulnerability scan are outside the verified results.
