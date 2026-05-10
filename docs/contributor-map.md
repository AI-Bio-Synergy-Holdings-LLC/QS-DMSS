# Contributor Map

This map connects user-facing QS-DMSS behavior to the source files and tests
that usually matter for a focused contribution.

## CLI And User Commands

- Source: `src/qs_dmss/cli.py`
- Tests: `tests/test_run_smoke.py`, `tests/test_cli_campaigns.py`,
  `tests/test_cli_experiments.py`, `tests/test_benchmarks.py`
- Start here for command-line help text, subcommands, output messages, and CLI
  error handling.

## Config Loading And Validation

- Source: `src/qs_dmss/io/config.py`
- Schema: `schemas/run_config.schema.json`,
  `src/qs_dmss/assets/schemas/run_config.schema.json`
- Tests: `tests/test_campaign.py`, `tests/test_paths.py`
- Start here for YAML parsing, type validation, decision profile fields, and
  campaign config parsing.

## Solver And Metrics

- Source: `src/qs_dmss/core/solver.py`, `src/qs_dmss/app.py`
- Tests: `tests/test_run_smoke.py`, `tests/test_benchmarks.py`
- Start here for deterministic NumPy solver behavior, metrics generation, and
  final numerical artifacts.

## Evidence Bundles And Replay

- Source: `src/qs_dmss/evidence/bundle.py`,
  `src/qs_dmss/evidence/verify.py`, `src/qs_dmss/run/ledger.py`,
  `src/qs_dmss/app.py`
- Tests: `tests/test_run_smoke.py`, `tests/test_cockpit_api.py`
- Start here for manifests, environment locks, reports, bundle ZIPs, and replay
  behavior.

## Experiments, Campaigns, And Decisions

- Source: `src/qs_dmss/experiment.py`, `src/qs_dmss/decision.py`,
  `src/qs_dmss/cockpit/api.py`
- Tests: `tests/test_decision.py`, `tests/test_campaign.py`,
  `tests/test_cli_campaigns.py`, `tests/test_cockpit_api.py`
- Start here for run comparisons, campaign expansion, objective scoring,
  recommendations, and experiment bundle persistence.

## Benchmarks

- Source: `src/qs_dmss/benchmarks.py`
- Assets: `src/qs_dmss/assets/benchmarks/`
- Tests: `tests/test_benchmarks.py`
- Docs: `docs/benchmark-validation.md`
- Start here for packaged benchmark scenarios, expected metric envelopes, and
  replay-backed validation reports.

## Cockpit UI And API

- API source: `src/qs_dmss/cockpit/api.py`,
  `src/qs_dmss/cockpit/server.py`
- Static source: `src/qs_dmss/cockpit/static/`
- Tests: `tests/test_cockpit_api.py`
- Start here for browser-facing workflows, API payloads, run inspection,
  verification, replay, experiment export, and campaign launch.

## Packaging, Releases, And Public Metadata

- Source: `pyproject.toml`, `MANIFEST.in`, `RELEASE.md`,
  `.github/workflows/`
- Tests: `tests/test_packaging.py`
- Docs: `docs/pypi-distribution-readiness.md`,
  `docs/reviewer-wheel-quickstart.md`
- Start here for package metadata, wheel contents, release artifacts, Trusted
  Publishing, and fresh-install smoke validation.

## Good First Path

1. Pick one user-facing behavior or doc gap.
2. Find the matching source and tests above.
3. Make a small change.
4. Run the narrow test first, then `python -m pytest -q`.
5. Include the command output in the pull request body.
