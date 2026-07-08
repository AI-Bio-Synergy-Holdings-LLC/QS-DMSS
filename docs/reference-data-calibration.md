# Public Reference-Data Provenance And Calibration Sandbox

QS-DMSS includes a small public reference-data provenance workflow for
reviewing how external source lanes, citations, access dates, local cache
checksums, transform metadata, and evidence bundles are recorded.

This is workflow calibration, not scientific validation. It does not download,
mirror, redistribute, fine-tune against, or physically validate QS-DMSS with
provider datasets.

## Source Registry

List packaged source records:

```powershell
qs-dmss data sources list
```

Inspect one source record:

```powershell
qs-dmss data sources inspect planck-legacy
```

Emit JSON for automation:

```powershell
qs-dmss data sources list --json
qs-dmss data sources inspect gaia-dr3 --json
```

The packaged registry currently includes metadata records for:

| Source ID | Public lane | Official URL |
| --- | --- | --- |
| `planck-legacy` | Planck Legacy Archive | <https://pla.esac.esa.int/> |
| `desi-dr1` | DESI Data Release 1 | <https://data.desi.lbl.gov/doc/releases/dr1/> |
| `sdss-dr19` | Sloan Digital Sky Survey Data Release 19 | <https://www.sdss.org/science/publications/data-release-publications/> |
| `gaia-dr3` | Gaia Data Release 3 | <https://www.cosmos.esa.int/web/gaia/dr3> |

These records are official source lanes and citation metadata. They are not
local copies of the provider datasets.

For role-labeled citations and the distinction between public source-data
provenance, conceptual context, and scientific validation, see
[conceptual-reference-map.md](conceptual-reference-map.md).

## Calibration Sandbox

Run the provenance calibration workflow:

```powershell
qs-dmss data calibration run --output-root reference-data-calibration
```

The command materializes metadata-only source manifests and a tiny packaged
fixture into a user cache directory, then emits a report and evidence bundle
under the output root.

To choose a cache directory explicitly:

```powershell
qs-dmss data calibration run `
  --output-root reference-data-calibration `
  --cache-root .cache/qs-dmss
```

To run against a subset of source lanes:

```powershell
qs-dmss data calibration run --source gaia-dr3 --output-root gaia-provenance-check
```

## Outputs

The workflow writes:

- `reference-data-calibration.json`
- `reference-data-calibration.md`
- `reference-data-calibration-evidence.zip`
- `calibration-config.json`
- `cached-sources/*.source-manifest.json`
- `calibration-inputs/workflow-smoke-reference.json`

The evidence bundle records:

- source ID, official URL, documentation URL, release, provider, and citation;
- access date for each source record;
- transform script name: `qs_dmss.data_registry.run_reference_calibration`;
- config path and selected source IDs;
- user cache path, cached file checksums, and copied evidence checksums;
- the claim boundary that this is workflow calibration only.

## Cache Policy

QS-DMSS stores calibration records in a user cache directory. By default this is
`%LOCALAPPDATA%\qs-dmss\cache` on Windows, `$XDG_CACHE_HOME/qs-dmss` on systems
that define `XDG_CACHE_HOME`, or `~/.cache/qs-dmss` otherwise.

You can override the cache location with:

```powershell
$env:QS_DMSS_CACHE_DIR = "C:\path\to\qs-dmss-cache"
qs-dmss data calibration run
```

Only metadata manifests and the tiny packaged fixture are cached by this
workflow. Future connectors may download user-selected public data products, but
those downloads should remain local, checksum-recorded, citation-recorded, and
excluded from the package distribution.

## Claim Boundary

Use this workflow to test whether QS-DMSS can preserve public source
provenance, cache checksums, citations, transform metadata, and evidence bundle
records.

Do not describe this workflow as:

- fine-tuning a scientific model;
- validating QS-DMSS against Planck, DESI, SDSS, or Gaia data;
- redistributing public survey data;
- a peer-reviewed cosmology or astrophysics result.

The intended framing is:

> Public reference-data provenance and calibration sandbox for reproducible
> workflow evidence.
