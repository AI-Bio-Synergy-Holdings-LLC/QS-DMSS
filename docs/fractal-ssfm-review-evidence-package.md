# Fractal SSFM independent-review evidence package

This contract gives an external reviewer a deterministic way to package the
evidence associated with Fractal SSFM v0.13.2 and issues #105 and #183. It
validates package integrity and provenance only. A passing package does not
establish independent scientific validation, approve a model, or close either
issue.

## Verify without execution

```console
qs-dmss validation review-evidence PATH_TO_PACKAGE --json
```

`PATH_TO_PACKAGE` may be a directory or ZIP archive. Verification performs no
network request, runs no packaged command, imports no packaged code, and writes
nothing into the package. The result is deterministic for identical bytes.

The package root must contain `review-evidence-manifest.json` and only the files
listed by that manifest. Paths must be portable, relative POSIX paths. Absolute
paths, `..`, backslashes, symbolic links, duplicate paths, case-colliding paths,
encrypted ZIP members, and undeclared files are rejected.

## Required evidence

The closed manifest schema is
[`schemas/fractal-ssfm-review-evidence-package-v1.schema.json`](../schemas/fractal-ssfm-review-evidence-package-v1.schema.json).
It requires exactly one file for each of these roles:

- `technical_review`: the human-accountable technical assessment in Markdown;
- `validation_json`: machine-readable output from the pinned validation run;
- `validation_markdown`: the companion reviewer-facing validation report; and
- `environment`: the release, wheel, Python, NumPy, and platform identity.

At least one `command_receipt` is required. Each receipt must repeat the exact
declared command, record exit code `0`, use an ISO-8601 UTC timestamp, and point
to the declared environment file. `supplemental` files are permitted only when
declared with hashes and sizes.

The manifest also binds the package to:

- release `0.13.2` / tag `v0.13.2`;
- source commit `7a063eb91af6c50e483c2d062bf6cee0daf709e4`;
- wheel `qs_dmss-0.13.2-py3-none-any.whl`; and
- wheel SHA-256
  `6f22876fa625681aa72b96d99e14de92cfd5cfae870fc53d9d41673ebf82416f`.

## Reviewer accountability boundary

The manifest requires reviewer identity, affiliation, a contact or public
profile, an independence declaration, a human-accountability statement, and an
AI-assistance disclosure. The validator confirms that these declarations are
present; it cannot establish whether they are true. Human review and public
finding disposition remain mandatory under issue #105.

Every valid result reports `scientific_validation_status` as
`NOT_ESTABLISHED`. Any package that attempts to change that status is rejected.
