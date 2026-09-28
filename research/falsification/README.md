# Bounded scientific-falsification pilot

Read [the protocol and claim boundary](../../docs/scientific-falsification-pilot.md)
before interpreting any output. These repository-only scripts do not change the
application or establish independent scientific validation.

## Reproduction

1. Obtain this PR's reviewed runner and `protocol-v1.json`. The prospective
   protocol commit is `5fe19ed857a253caa0cb91ffc1a4d18904cc07e3`.
2. Export the target source with
   `git archive --format=zip --output=source.zip 48d7ab5d10da189caddbcad1dd6622e58d204940`.
   Extract into a new directory, then run `python -m build --wheel --outdir candidate source`.
   Do not build the published v0.13.2 tag or identify this candidate by version alone.
3. Create an isolated environment, install the candidate wheel and
   `research/falsification/requirements.txt`. Do not install QS-DMSS editable.
4. Record the build in a JSON receipt with `source_commit`, `source_tree`,
   `source_archive_sha256`, `wheel_file`, `wheel_sha256`, `source_clean: true`,
   build tool/Python versions, exact build command and observed exit code.
   The runner requires the source pin, clean-source declaration and wheel hash;
   the remaining provenance is a human-audited receipt, not a signed attestation.
   Obtain SHA-256 with `Get-FileHash -Algorithm SHA256` (PowerShell) or `sha256sum`.
5. From **outside the checkout**, use the isolated environment's Python:

   ```console
   python /path/to/runner/pilot.py --wheel /path/to/candidate.whl --build-receipt /path/to/build-receipt.json --output /new/path/packet
   ```

The output directory and adjacent `.zip` must not already exist. Exit zero means
only `NOT_FALSIFIED_WITHIN_SCOPE`; FAIL or INCONCLUSIVE exits nonzero. All 89 cases,
seeded negative controls and raw graph/evolution arrays are retained. The archive
includes the exact protocol/reference/runner files and a per-file hash manifest.
Extract only trusted archives into a new directory. Verify each manifest hash
before interpreting results. Hash consistency is not scientific assessment.

Wheel byte hashes can differ between legitimate builds because of packaging
metadata/timestamps. Preserve each candidate and its own receipt. The installed
package must match every file in the supplied candidate wheel and contain no
additional non-cache package files. No network or execution of submitted evidence
is performed by the runner.

## Regression checks

```console
python -m pip install -e .[dev] -r research/falsification/requirements.txt
python -m pytest -q tests/test_falsification_pilot.py
```

These tests are engineering regressions on the current checkout, not the pinned
candidate exercise. The supported CI matrix installs the research requirements
explicitly. A base developer environment without SciPy skips the numerical pilot
tests, while the reference-import boundary check still runs.

## Attempt record

- Protocol frozen before numerical execution; no cases/tolerances changed after
  observing results. First development regression run: all 89 cases not falsified.
- WolframScript was found but returned exit code 1: product not activated or a
  license problem. No Wolfram computation is claimed; no licensing changes made.
- First fresh installed-candidate attempt: Python 3.12.14, NumPy 2.5.3, SciPy
  1.18.1. It stalled before numerical execution while importing
  `scipy.optimize._highspy._core` through `scipy.integrate`. A diagnostic traceback
  located the stall; the task-owned processes were stopped. No packet or numerical
  result was produced. Root cause is unconfirmed; this is an environment issue,
  not evidence for or against the model.
- Retry uses the working local combination Python 3.14.3, NumPy 2.5.1, SciPy
  1.18.0 in a new isolated environment and the identical candidate wheel. The
  supported Python 3.10-3.13 CI matrix remains required separately.

Human finding dispositions remain PENDING. Do not infer owner scientific approval
from the request to implement or open this PR.
