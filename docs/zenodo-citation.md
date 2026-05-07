# Zenodo Citation Setup

QS-DMSS uses `CITATION.cff` as its canonical citation metadata file.

## Current Status

- Public baseline: `v0.1.3`
- Citation metadata file: `CITATION.cff`
- DOI status: pending Zenodo archival
- Zenodo-specific metadata file: not used

Do not add `.zenodo.json` unless QS-DMSS needs Zenodo-specific metadata that
`CITATION.cff` cannot express. If both files exist, Zenodo uses `.zenodo.json`
and ignores `CITATION.cff` for GitHub release archiving.

## Zenodo Steps

1. Connect the repository in Zenodo under the GitHub integration.
2. Enable `AI-Bio-Synergy-Holdings-LLC/QS-DMSS`.
3. Archive the desired release in Zenodo.
4. Copy the minted Zenodo DOI.
5. Open a follow-up PR that adds the DOI to `CITATION.cff`, this document, and
   the README citation section.

For automatic GitHub release archival, enable the repository before creating
the GitHub release that Zenodo should ingest. `v0.1.3` is the first planned
release after Zenodo was enabled, so it should be the first release archived
through the GitHub integration.

## DOI Update Target

After Zenodo mints a DOI, add it to `CITATION.cff`:

```yaml
doi: 10.5281/zenodo.<record>
```

Prefer the Zenodo DOI for formal research references once it exists.
