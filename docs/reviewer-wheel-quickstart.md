# Reviewer Install Quickstart

This path validates QS-DMSS from a published distribution without a source
checkout. It is intended for reviewers who need a fast productization smoke
test.

Release: `v0.1.4`

PyPI:
`https://pypi.org/project/qs-dmss/`

Wheel:
`https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/releases/download/v0.1.4/qs_dmss-0.1.4-py3-none-any.whl`

## PyPI Install

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install qs-dmss

qs-dmss run-demo
qs-dmss campaigns run-demo
```

## GitHub Release Wheel

Use this path when validating the GitHub release asset directly.

```powershell
$release = "https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/releases/download/v0.1.4"
Invoke-WebRequest "$release/qs_dmss-0.1.4-py3-none-any.whl" -OutFile "qs_dmss-0.1.4-py3-none-any.whl"
python -m pip install .\qs_dmss-0.1.4-py3-none-any.whl
```

## Expected Signals

- `python -m pip install` reports the expected `qs-dmss` version.
- `qs-dmss run-demo` prints a run directory, evidence bundle path, and
  `Verification passed`.
- `qs-dmss campaigns run-demo` prints a saved campaign ID, planned run count,
  recommended run, decision status, and experiment bundle path.

## Optional Source Checkout

Use this path only when reviewing repository contents or running the full test
suite.

```powershell
git clone https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS.git
cd QS-DMSS
git checkout v0.1.4
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .[dev]
pytest
```
