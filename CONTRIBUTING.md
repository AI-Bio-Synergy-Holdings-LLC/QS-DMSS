# Contributing

Thanks for helping improve QS-DMSS. This project is early, evidence-first, and
public-facing, so small, reproducible changes are preferred over broad rewrites.

## Good First Contributions

- Documentation fixes that make installation, demos, or evidence artifacts easier
  to understand.
- Regression tests for CLI, cockpit, packaging, and reproducibility behavior.
- Small bug fixes with a clear before/after validation path.

## Development Setup

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .[dev] build
.\.venv\Scripts\python.exe -m pytest -q
```

Before opening a pull request, run:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
node --check src\qs_dmss\cockpit\static\app.js
.\.venv\Scripts\python.exe -m compileall src tests
```

## Pull Requests

- Keep pull requests focused on one behavior or documentation outcome.
- Include validation evidence in the PR body.
- Do not commit local runtime outputs, build artifacts, `.env`, `.pypirc`, or
  generated run/experiment data.
- Security concerns should follow `SECURITY.md`, not public issue threads.
