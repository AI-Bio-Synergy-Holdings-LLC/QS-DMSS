# Zenodo Citation

QS-DMSS uses `CITATION.cff` as its canonical citation metadata file.

## Current Status

- Public baseline: `v0.10.1` release target
- Current package metadata target: `v0.10.1` / `0.10.1`
- Citation metadata file: `CITATION.cff`
- DOI status: `v0.10.1` archived by Zenodo.
- PyPI metadata status: `v0.10.1` published; package-facing DOI metadata keeps
  the concept DOI and latest archived release DOI visible.
- Zenodo concept DOI: `10.5281/zenodo.20074924`
- Latest archived release DOI: `10.5281/zenodo.21270512` (`v0.10.1`)
- Latest archived release record: `https://zenodo.org/records/21270512`
- `v0.10.1` release DOI: `10.5281/zenodo.21270512`
- Previous archived release DOI: `10.5281/zenodo.20693736`
- Previous archived release record: `https://zenodo.org/records/20693736`
- Previous archived release DOI for `v0.8.0`: `10.5281/zenodo.20673804`
- Previous archived release record for `v0.8.0`: `https://zenodo.org/records/20673804`
- Previous archived release DOI for `v0.7.0`: `10.5281/zenodo.20671389`
- Previous archived release record for `v0.7.0`: `https://zenodo.org/records/20671389`
- Previous archived release DOI for `v0.6.1`: `10.5281/zenodo.20631860`
- Previous archived release record for `v0.6.1`: `https://zenodo.org/records/20631860`
- Previous archived release DOI for `v0.6.0`: `10.5281/zenodo.20618884`
- Previous archived release record for `v0.6.0`: `https://zenodo.org/records/20618884`
- Previous archived release DOI for `v0.5.0`: `10.5281/zenodo.20617028`
- Previous archived release record for `v0.5.0`: `https://zenodo.org/records/20617028`
- Previous archived release DOI for `v0.4.0`: `10.5281/zenodo.20500433`
- Previous archived release record for `v0.4.0`: `https://zenodo.org/records/20500433`
- Previous archived release DOI for `v0.3.0`: `10.5281/zenodo.20112923`
- Previous archived release record for `v0.3.0`: `https://zenodo.org/records/20112923`
- Previous archived release DOI for `v0.2.0`: `10.5281/zenodo.20091602`
- Previous archived release record for `v0.2.0`: `https://zenodo.org/records/20091602`
- Earlier archived release DOI: `10.5281/zenodo.20076871`
- Earlier archived release record: `https://zenodo.org/records/20076871`
- First archived release DOI: `10.5281/zenodo.20074925`
- First archived release record: `https://zenodo.org/records/20074925`
- Zenodo citation/reference metadata: no downstream citation or reference
  relationships recorded yet
- Software Heritage archival status: pending; no SWHID is recorded yet
- Zenodo-specific metadata file: not used

Do not add `.zenodo.json` unless QS-DMSS needs Zenodo-specific metadata that
`CITATION.cff` cannot express. If both files exist, Zenodo uses `.zenodo.json`
and ignores `CITATION.cff` for GitHub release archiving.

## Citation Guidance

Use the Zenodo concept DOI for project-level citations that should resolve to
the latest archived QS-DMSS release:

```text
10.5281/zenodo.20074924
```

Use the version DOI when citing the exact first archived release artifacts:

```text
10.5281/zenodo.20074925
```

Use the latest known version DOI when citing the current archived release:

```text
10.5281/zenodo.21270512
```

`CITATION.cff` stores the concept DOI in the root `doi` field so GitHub and
PyPI package metadata can point to a stable citation target across releases. It
also lists the latest and earlier archived release DOIs in `identifiers` so
exact release archives remain visible from the citation metadata.

## Zenodo Workflow

For automatic GitHub release archival, enable the repository before creating
the GitHub release that Zenodo should ingest. `v0.1.3` was the first release
created after Zenodo was enabled, and it archived successfully through the
GitHub integration.

Future release workflow:

1. Merge the release-prep PR through green CI.
2. Tag the merge commit and create the GitHub release.
3. Let Zenodo archive the release automatically.
4. Add the new version DOI to the GitHub release notes.
5. Add the Software Heritage SWHID once archival completes.
6. Keep the concept DOI in package-facing citation metadata unless the release
   process can inject the version DOI before PyPI publication.
