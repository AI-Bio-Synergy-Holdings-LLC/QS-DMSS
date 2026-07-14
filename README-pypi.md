# QS-DMSS

QS-DMSS is a deterministic, evidence-first simulation lab for
QuantumScalar dark matter workflows. It helps researchers run bounded local
simulations, inspect and compare evidence, verify and replay results, and
export reproducible research objects.

The software is beta for reproducible package and evidence workflows. It is
not peer-reviewed scientific validation, and its quantum-readiness paths are
simulator-first and provider-neutral: they do not use provider credentials,
remote APIs, QPU execution, job submission, or authorized spend.

## Install and run the local cockpit

```powershell
python -m pip install --upgrade qs-dmss
qs-dmss cockpit --host 127.0.0.1 --port 8001
```

Use the local cockpit to run Lab Mode, inspect evidence, compare campaigns,
verify and replay outputs, and export reports. The constrained hosted demo is
available at [app.qs-dmss.studio](https://app.qs-dmss.studio/).

## Citation and release records

Use the stable QS-DMSS project concept DOI for project-level citation:
[10.5281/zenodo.20074924](https://doi.org/10.5281/zenodo.20074924).

For an exact software release, cite the installed package version together with
the matching [GitHub Release](https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/releases)
and version-specific Zenodo record. This distribution intentionally uses stable
links so its immutable PyPI metadata does not become stale when a later release
is archived.

More information is available at [qs-dmss.studio](https://qs-dmss.studio/), in
the [repository](https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS), and
the [reviewer quickstart](https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/blob/main/docs/reviewer-wheel-quickstart.md).
