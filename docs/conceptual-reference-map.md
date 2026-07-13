# Conceptual Reference Map

QS-DMSS uses references to make its conceptual lineage, numerical-method
lineage, public data provenance, and reproducibility posture transparent.

This document is not a claim that QS-DMSS has been scientifically validated by
the works below. It is a map of citation roles so reviewers can distinguish
between:

- scientific motivation;
- numerical method precedent;
- public source-data provenance;
- reproducibility and research-object infrastructure;
- future comparison targets.

## How To Read This Map

| Citation role | Meaning | Boundary |
| --- | --- | --- |
| Conceptual context | Work that helps explain why Schrodinger-Poisson-style self-gravity or wave-dark-matter systems are relevant to QS-DMSS. | Context only; not validation of QS-DMSS. |
| Numerical method precedent | Work that motivates split-step, pseudo-spectral, convergence, or conservation checks. | Method lineage only; not proof that QS-DMSS is correct for all regimes. |
| Public source-data provenance | Official source lanes that QS-DMSS can record with URL, access date, citation, checksum, and transform metadata. | Metadata/provenance only; QS-DMSS does not mirror or validate against these datasets. |
| Research-object infrastructure | Standards and practices for citation, metadata, archival, replay, and packaging. | Workflow credibility only; not scientific endorsement. |
| Comparison target | Software or method families that future papers should compare against. | Future scholarly work; not a current performance claim. |

## Conceptual Physics Context

QS-DMSS is currently framed as a small, deterministic,
Schrodinger-Poisson-style evidence lab. The relevant conceptual background is
self-consistent wave evolution coupled to a potential, including adjacent
Schrodinger-Newton and fuzzy or ultralight dark matter literature.

Candidate references to assess for a future paper:

| Reference target | Suggested role in QS-DMSS | Notes |
| --- | --- | --- |
| Ruffini and Bonazzola, "Systems of self-gravitating particles in general relativity and the concept of an equation of state," Physical Review, 1969, DOI: `10.1103/PhysRev.187.1767` | Historical context for self-gravitating bosonic systems. | Useful for conceptual lineage, not for direct QS-DMSS validation. |
| Lieb, "Existence and uniqueness of the minimizing solution of Choquard's nonlinear equation," Studies in Applied Mathematics, 1977 | Mathematical context for stationary self-attractive nonlinear systems. | Include only if the paper discusses ground-state/self-bound analogies. |
| Diosi, "Gravitation and quantum-mechanical localization of macro-objects," Physics Letters A, 1984 | Schrodinger-Newton / semiclassical-gravity context. | Contextual reference for self-gravity questions. |
| Penrose, "On Gravity's role in Quantum State Reduction," General Relativity and Gravitation, 1996, DOI: `10.1007/BF02105068` | Conceptual context for gravity, localization, and quantum-to-classical discussions. | Do not imply QS-DMSS tests Penrose collapse. |
| Bahrami et al., "The Schrodinger-Newton equation and its foundations," New Journal of Physics, 2014, DOI: `10.1088/1367-2630/16/11/115007` | Reviewer-facing background for Schrodinger-Newton foundations. | Useful for cautious framing of self-gravity. |
| Hu, Barkana, and Gruzinov, "Fuzzy Cold Dark Matter: The Wave Properties of Ultralight Particles," Physical Review Letters, 2000, DOI: `10.1103/PhysRevLett.85.1158` | Fuzzy or ultralight dark matter motivation. | Use as field context, not as a claim that QS-DMSS is production cosmology. |

## Numerical Method Context

QS-DMSS uses small NumPy reference runs and validation harnesses. The current
project claim is workflow reproducibility around deterministic runs, not
large-scale numerical novelty.

Candidate references to assess for a future paper:

| Reference target | Suggested role in QS-DMSS | Notes |
| --- | --- | --- |
| Strang, "On the construction and comparison of difference schemes," SIAM Journal on Numerical Analysis, 1968 | Operator splitting / Strang splitting lineage. | Relevant to convergence-language discipline. |
| Taha and Ablowitz, "Analytical and numerical aspects of certain nonlinear evolution equations. II. Numerical, nonlinear Schrodinger equation," Journal of Computational Physics, 1984 | Split-step / spectral method precedent for nonlinear Schrodinger-type systems. | Good support for validation-harness expectations. |
| Bao, Jaksch, and Markowich, "Numerical solution of the Gross-Pitaevskii equation for Bose-Einstein condensation," Journal of Computational Physics, 2003 | Time-splitting spectral methods for nonlinear wave equations. | Adjacent method precedent; use only if applicable to the solver discussion. |
| Fractal/Quadrant SSFM validation issue, QS-DMSS issue #105 | Active technical review gate. | Public QS-DMSS feedback should focus on convergence, norm conservation, and diagnostic boundaries before GPU expansion. |

## Quantum-Readiness Context

QS-DMSS remains a classical simulation package. The optional Fractal SSFM
quantum-readiness sidecar tests one small circuit encoding against the NumPy
reference. Its provider-neutral QPU request bundle then makes topology,
state-preparation, routing, and gate costs reviewable without credentials,
provider access, or job submission. The compilation harness validates ideal
logical-output preservation and attributes resource tradeoffs across fixed
generic targets. None of these surfaces establishes QPU acceleration or
physical validation.

| Reference target | Suggested role in QS-DMSS | Notes |
| --- | --- | --- |
| Mocz and Szasz, "Towards Cosmological Simulations of Dark Matter on Quantum Computers," arXiv:2101.05821 | Direct conceptual context for hybrid quantum-classical Schrodinger-Poisson simulation. | Supports the sidecar research question while emphasizing that nonlinear self-gravity is difficult. |
| Weng et al., "Quantum simulation of the nonlinear Schrodinger equation via measurement-induced potential reconstruction," arXiv:2601.19184 | Emerging hybrid nonlinear-wave method context. | Preprint only; do not treat it as validation or settled method precedent. |
| OpenQASM 3 specification, <https://openqasm.com/> | Human-readable quantum-circuit interchange context. | QS-DMSS also preserves native Qiskit serialization because circuit interchange may be lossy across tools and targets. |
| Qiskit generic backend and transpiler interfaces | Provider-neutral target-contract and resource-review context. | QS-DMSS uses a local generic topology only; it does not model a named device, current calibration, execution fidelity, availability, or price. |

## Public Source-Data Provenance

QS-DMSS v0.11.0 includes source records for public astronomical/cosmological
data lanes. These are metadata and provenance lanes only. They are not bundled
datasets, calibration truth, or scientific validation datasets.

| QS-DMSS source ID | Official lane | Citation role | Recommended source reference |
| --- | --- | --- | --- |
| `planck-legacy` | Planck Legacy Archive | Official source lane for Planck mission products. | Planck Collaboration, "Planck 2018 results. I. Overview and the cosmological legacy of Planck," Astronomy and Astrophysics 641, A1, 2020, DOI: `10.1051/0004-6361/201833880`; official archive: <https://pla.esac.esa.int/> |
| `desi-dr1` | DESI Data Release 1 | Official source lane for DESI DR1 spectra/catalog metadata. | DESI Collaboration, "Data Release 1 of the Dark Energy Spectroscopic Instrument"; official DR1 docs: <https://data.desi.lbl.gov/doc/releases/dr1/> |
| `sdss-dr19` | Sloan Digital Sky Survey Data Release 19 | Official source lane for SDSS DR19 metadata. | SDSS Collaboration, "The Nineteenth Data Release of the Sloan Digital Sky Survey"; official data-release publication list: <https://www.sdss.org/science/publications/data-release-publications/> |
| `gaia-dr3` | Gaia Data Release 3 | Official source lane for Gaia DR3 catalog metadata. | Gaia Collaboration, "Gaia Data Release 3: Summary of the content and survey properties," Astronomy and Astrophysics 674, A1, 2023, DOI: `10.1051/0004-6361/202243940`; official DR3 page: <https://www.cosmos.esa.int/web/gaia/dr3> |

When QS-DMSS records these source lanes, the evidence object should preserve:

- source ID and official URL;
- access date;
- provider citation;
- local cache path and checksum for any user-selected material;
- transform script or command name;
- claim boundary that the workflow is provenance calibration, not scientific validation.

## Reproducibility And Research-Object Infrastructure

QS-DMSS should cite research-software and research-object practices when
describing evidence bundles, replay, metadata, and citation files.

Candidate references to assess for a future paper:

| Reference target | Suggested role in QS-DMSS | Notes |
| --- | --- | --- |
| Wilkinson et al., "The FAIR Guiding Principles for scientific data management and stewardship," Scientific Data, 2016, DOI: `10.1038/sdata.2016.18` | FAIR context for findability, accessibility, interoperability, and reuse. | Use for workflow and metadata framing. |
| Smith et al., "Software citation principles," PeerJ Computer Science, 2016, DOI: `10.7717/peerj-cs.86` | Software citation context. | Supports DOI, citation, and versioned release discipline. |
| RO-Crate Metadata Specification, version 1.2.0, Zenodo record: <https://zenodo.org/records/13751027> | Research-object packaging context. | QS-DMSS is not yet claiming RO-Crate compliance unless explicitly implemented. |
| CodeMeta project: <https://codemeta.github.io/> | Software metadata interoperability context. | Relevant because QS-DMSS maintains `codemeta.json`. |
| Citation File Format: <https://citation-file-format.github.io/> | Citation metadata context. | Relevant because QS-DMSS maintains `CITATION.cff`. |
| Software Heritage: <https://www.softwareheritage.org/> | Source-code preservation context. | Relevant once archive/indexing is confirmed. |
| Zenodo GitHub integration: <https://zenodo.org/> | Versioned software archival context. | Relevant to project DOI and release DOI discipline. |

## Comparison Targets For Future Paper Work

The current JOSS/ASCL gap is not package readiness. The gap is stronger
state-of-the-field comparison and concrete research-use evidence. Future paper
work should compare QS-DMSS against tools in two lanes:

- numerical/scientific solver families for fuzzy or scalar dark matter;
- reproducibility/workflow tools that package evidence, replay, and publication artifacts.

Candidate comparison targets already identified in QS-DMSS planning docs:

| Target | Comparison question |
| --- | --- |
| PyUltraLight | How does QS-DMSS differ from an ultralight dark matter solver in scope, scale, and evidence workflow? |
| SCALAR | How does QS-DMSS differ from production scalar-field cosmology simulation codes? |
| AxioNyx | How does QS-DMSS differ from AMR/HPC axion/fuzzy dark matter simulation infrastructure? |
| General workflow/provenance tools | What does QS-DMSS capture directly inside the simulation package that generic workflow tools leave to the user? |

## Public Claim Boundary

Use the references above to make the project easier to audit. Do not use them to
overstate the maturity of the software.

Acceptable wording:

> QS-DMSS draws on Schrodinger-Poisson-style conceptual context, split-step
> numerical-method precedent, public source-data provenance practices, and
> research-object metadata conventions to make small deterministic simulation
> studies inspectable and reproducible.

Avoid:

- "validated against Planck/DESI/SDSS/Gaia";
- "production cosmology simulator";
- "peer-reviewed dark matter model";
- "RO-Crate compliant" unless that metadata structure is implemented and tested;
- "GPU/HPC ready" before the relevant connector and site-policy reviews land.

## Maintenance Checklist

Before a paper, release note, outreach post, or website update cites this map:

1. Confirm that each cited work still matches the role being claimed.
2. Prefer official DOI, publisher, archive, or provider pages.
3. Preserve the distinction between public source-data provenance and scientific validation.
4. Update package/source registries only when the citation is reflected in runnable output.
5. Keep private ownership, AI disclosure details, and copyright registration material in internal governance documents unless they directly affect public use.
