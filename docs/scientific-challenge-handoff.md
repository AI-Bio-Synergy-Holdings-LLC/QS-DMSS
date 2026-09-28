# Scientific Challenges: discovery and reviewer handoff

This is a read-only discovery layer over the [reviewed registry](scientific-challenges.md),
not a new experiment, validation decision or release. Its deployment follows
protected PR review. The published PyPI v0.13.2 package does not gain this UI
until a separately authorized future release.

## Entry points and reviewer path

After merge and deployment:

- Studio: <https://qs-dmss.studio/#scientific-challenges>.
- Hosted cockpit: <https://app.qs-dmss.studio/#scientific-challenges>.
- Local development cockpit: the Scientific challenges link and the contextual
  Evidence Assistant both lead to the same catalog.

Choose a challenge → inspect the pinned packets → reproduce the pinned candidate
locally → open the scientific-review form. The form link identifies the challenge
in its title and focus; the reviewer must explicitly choose the matching track
and supply their own commands, environment, measured hashes and disclosures.
No outcome, reviewer identity, independence or artifact hash is prefilled.
Opening a link does not submit a report.

The three displayed dimensions remain separate: numerical outcome, owner
engineering approval of pilot #194, and pending independent scientific review.
The catalog is a frozen v1 snapshot, not a live mirror of issue activity.
The linked [gate #183](https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/issues/183)
is the current record for findings and human dispositions. The contextual panel
describes the chosen registered challenge, **not the current simulation run**.
It sends no model request and cannot launch compute.

## Identity and unavailable states

The registry remains the single source of scientific content. Run:

```console
python research/challenges/build_discovery.py
python research/challenges/build_discovery.py --check
```

Generation first runs the existing schema/protocol/packet validator, including
the retained ZIP hashes, manifests, bounds and result pointers. It then emits
identical JSON, JavaScript and CSS assets into the portal and package static
directory. The source templates live in `research/challenges/discovery.js` and
`discovery.css`; do not edit generated copies. CI rejects drift.

The browser checks the exact catalog bytes against the digest embedded in its
generated script before parsing/rendering them. The generated assets use LF
line endings on all platforms. This is catalog identity checking, not a new
download/verification of the original evidence ZIPs, nor an authenticity signature.
The source/evidence correspondence is checked during generation and CI.

Missing, changed, malformed, redirected or timed-out data produce an unavailable
state without scientific success labels. A retry and the source reviewer guide
remain available. Without JavaScript, the same guide and gate links remain.
Prose is rendered through text nodes, links are restricted to this repository,
and no submitted scripts or archives are executed. No runtime scientific
dependency, API endpoint or CSP relaxation is added. Hosted AI and graph
execution remain disabled.

## Maintainer handoff dry-run (2026-09-28 UTC)

The documented source export → wheel build → clean environment → external runner
path was exercised again, outside an editable checkout:

- Candidate source: `48d7ab5d10da189caddbcad1dd6622e58d204940`.
- Reviewed runner/reference/protocol: `a5f72e614dc7d38e72ffe3f4b752aace0bb408b4`.
- Windows x86-64, Python 3.14.3, NumPy 2.5.1, SciPy 1.18.0.
- New wheel SHA-256: `a7efe624ff8ecc665aadf5627ef2f2ca2a16b6087f2af554fcc7416d9d1f144b`.
- New packet SHA-256: `3ff9c60fa4a671d45d877a344d0964b97824a6d1e60e62c7f8e601da88115e3f`.
- 72 FFT, 15 graph and 2 evolution cases: `NOT_FALSIFIED_WITHIN_SCOPE`; exit zero.
- New build receipt, install/build/run logs, raw arrays and per-file manifest are
  retained locally. Neither new wheel nor packet is a published release or a
  replacement for the registry's original evidence. Build isolation resolved
  build dependencies afresh; byte-identical builds are not promised.

This is an AI-assisted maintainer acceptance exercise, **not independent human
review**. It did not rerun Wolfram or resolve the historical Python 3.12 import
stall. Supported Python 3.10–3.13 engineering CI remains a separate gate.
Independent reviewers must retain their own receipts and findings.

## Independent-review pilot and unsent invitation

Milestone: obtain one substantive human-accountable independent reproduction and
methodological assessment, prioritizing graph measure, boundary treatment, length
scaling and multilevel interpretation. A conceptual NOT_RUN objection is welcome,
but is not counted as executed reproduction. One report need not settle all claims.

Owner action required: choose and approve an opt-in reviewer/channel before
sending the following invitation. No outreach has been sent or scheduled.

> We invite a scoped scientific assessment of QS-DMSS's experimental CPU
> graph-spectral model (SC-GRAPH-001). Please scrutinize its finite-cell measure,
> boundary restriction, length scaling and multilevel interpretation, and
> reproduce the pinned candidate where practical. The evidence is not a claim of
> physical validation or continuum convergence. Review the source guide, retain
> commands/environment/measured hashes and counterexamples, disclose independence
> and AI assistance, and submit through the Scientific Review form under #183.
> A named human must take responsibility for the assessment; criticism and
> inconclusive findings are welcome.

Attach the source guide and, only after verified deployment, the studio entry
point. Record each finding and named human disposition using the existing
template in `docs/scientific-challenges.md`. Keep failures and objections visible;
do not close #183 or promote the graph model automatically.
