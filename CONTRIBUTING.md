# Contributing

Thanks for helping improve QS-DMSS. This project is early, evidence-first, and
public-facing, so small, reproducible changes are preferred over broad rewrites.

## Good First Contributions

- Documentation fixes that make installation, demos, or evidence artifacts easier
  to understand.
- Regression tests for CLI, cockpit, packaging, and reproducibility behavior.
- Small bug fixes with a clear before/after validation path.

New contributors can use [docs/contributor-map.md](docs/contributor-map.md) to
match user-facing behavior to source files and tests.

## Scientific Challenge Review

Use the [challenge registry and intake guide](docs/scientific-challenges.md) for
FFT-energy, finite-graph operator, and evolution-accuracy assessments under active
issue #183. Closed #105 is historical context. Supply source/artifact hashes,
commands, environment, counterexamples or limitations, reviewer independence,
AI assistance and a pending human disposition. PyPI v0.13.2 is not the later
development candidate, despite their shared version string. Conceptual NOT_RUN
feedback is welcome but does not establish independent reproduction.

## Funding And Stewardship

QS-DMSS participates in Open Source Collective at
`https://opencollective.com/qs-dmss`. Financial support is used to sustain
open-source maintenance, reviewer-facing documentation, reproducibility
workflow hardening, and public research-software readiness.

Funding does not change the review boundary: scientific claims still need
reproducible evidence, public review, and appropriate scholarly validation.

## Development Setup

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .[dev,audit] build
.\.venv\Scripts\python.exe -m pytest -q
```

Before opening a pull request, run:

```powershell
.\.venv\Scripts\python.exe -m ruff check src tests .github/scripts research site/build_portal.py
.\.venv\Scripts\python.exe research/challenges/validate_registry.py
.\.venv\Scripts\python.exe -m pytest -q --cov=qs_dmss --cov-fail-under=88
.\.venv\Scripts\python.exe -m bandit -r src --severity-level medium --confidence-level medium -q
.\.venv\Scripts\python.exe -m pip_audit --local
node --check src\qs_dmss\cockpit\static\app.js
.\.venv\Scripts\python.exe -m compileall src tests
```

The current measured baseline and prioritized maintenance register live in
[docs/engineering-health.md](docs/engineering-health.md).

## Pull Requests

- Keep pull requests focused on one behavior or documentation outcome.
- Include validation evidence in the PR body.
- Do not commit local runtime outputs, build artifacts, `.env`, `.pypirc`, or
  generated run/experiment data.
- Security concerns should follow `SECURITY.md`, not public issue threads.

## Contribution Licensing

The public QS-DMSS core is distributed under Apache-2.0. By intentionally
submitting a contribution for inclusion in this repository, you agree that the
contribution may be distributed under Apache-2.0 and confirm that you have the
right to submit it.

Do not submit code, data, model files, provider material, or documentation whose
terms are incompatible with Apache-2.0 distribution. Identify relevant
third-party sources and licenses in the pull request.

QS-DMSS does not currently require copyright assignment or a contributor
license agreement. Commercial or separately licensed work must not be submitted
through the public repository unless the maintainer has established a separate,
counsel-reviewed process first. See the
[commercial sustainability and licensing boundary](docs/decisions/0001-commercial-sustainability-and-licensing-boundary.md).
