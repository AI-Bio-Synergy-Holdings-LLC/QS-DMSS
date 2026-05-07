# Zenodo Citation Setup

QS-DMSS uses `CITATION.cff` as its canonical citation metadata file.

## Current Status

- Public baseline: `v0.1.2`
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
the GitHub release that Zenodo should ingest. If the goal is to mint a DOI for
the already-published `v0.1.2` baseline without more release churn, use a manual
Zenodo software upload based on the `v0.1.2` source archive, then record the DOI
in a follow-up PR.

## DOI Update Target

After Zenodo mints a DOI, add it to `CITATION.cff`:

```yaml
doi: 10.5281/zenodo.<record>
```

Prefer the Zenodo DOI for formal research references once it exists.
