from __future__ import annotations

import hashlib
import html
import json
import platform
import zipfile
from collections.abc import Iterable
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _manifest_entries(
    root_dir: Path,
    excluded_paths: Iterable[str],
) -> list[dict]:
    excluded = set(excluded_paths)
    entries = []
    for file_path in sorted(path for path in root_dir.rglob("*") if path.is_file()):
        relative_path = file_path.relative_to(root_dir).as_posix()
        if relative_path in excluded:
            continue
        entries.append(
            {
                "path": relative_path,
                "sha256": _file_sha256(file_path),
                "size_bytes": file_path.stat().st_size,
            }
        )
    return entries


def build_environment_lock() -> dict:
    packages: dict[str, str] = {}
    for package_name in ("numpy", "PyYAML", "qs-dmss"):
        try:
            packages[package_name] = metadata.version(package_name)
        except metadata.PackageNotFoundError:
            continue

    return {
        "schema_version": 1,
        "captured_at": _utc_now(),
        "python": {
            "version": platform.python_version(),
            "implementation": platform.python_implementation(),
        },
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
        },
        "packages": packages,
    }


def write_report(
    run_dir: Path,
    run_record: dict,
    metrics: dict,
    decision: dict | None = None,
) -> None:
    report_path = run_dir / "report.html"
    rows = "\n".join(
        "<tr>"
        f"<td>{snapshot['step']}</td>"
        f"<td>{snapshot['norm']}</td>"
        f"<td>{snapshot['energy']}</td>"
        f"<td>{snapshot['max_density']}</td>"
        "</tr>"
        for snapshot in metrics["history"]
    )
    experiment = run_record.get("experiment")
    experiment_markup = ""
    if experiment:
        kind = str(experiment.get("kind", "sweep"))
        dimensions = experiment.get("dimensions") or []
        variant = experiment.get("variant") or []
        dimension_rows = "".join(
            f"<li>{html.escape(str(item.get('label') or item.get('path')))} (<code>{html.escape(str(item.get('path')))}</code>)</li>"
            for item in dimensions
        )
        variant_rows = "".join(
            f"<li>{html.escape(str(item.get('label') or item.get('path')))}: <code>{html.escape(str(item.get('value_label', '-')))}</code></li>"
            for item in variant
        )
        context_rows = f"""
      <li>Experiment ID: <code>{html.escape(str(experiment['id']))}</code></li>
      <li>Label: {html.escape(str(experiment['label']))}</li>
      <li>Kind: {html.escape(kind)}</li>
      <li>Ordinal: {experiment['ordinal']} of {experiment['total_runs']}</li>
"""
        if experiment.get("strategy"):
            context_rows += (
                f"      <li>Strategy: {html.escape(str(experiment['strategy']))}</li>\n"
            )
        if experiment.get("variant_label"):
            context_rows += (
                f"      <li>Variant: {html.escape(str(experiment['variant_label']))}</li>\n"
            )
        experiment_markup = f"""
    <h2>Experiment Context</h2>
    <ul>
{context_rows}    </ul>
    <h3>Search Dimensions</h3>
    <ul>
      {dimension_rows}
    </ul>
    <h3>Variant Values</h3>
    <ul>
      {variant_rows}
    </ul>
"""

    decision_markup = ""
    decision_profile = run_record.get("decision_profile")
    if decision_profile:
        objective = decision_profile["objective"]
        constraints = decision_profile["constraints"]
        ranking = decision_profile["ranking"]
        constraint_rows = "".join(
            f"<li>{html.escape(str(label))}: <code>{html.escape(str(value))}</code></li>"
            for label, value in constraints.items()
        )
        ranking_rows = "".join(
            f"<li>{html.escape(str(metric))}: {weight}</li>"
            for metric, weight in ranking["weights"].items()
        )
        evaluation_markup = ""
        if decision:
            checks = "".join(
                f"<li>{'PASS' if check['passed'] else 'FAIL'} - {html.escape(check['label'])} ({html.escape(check['actual_display'])})</li>"
                for check in decision["constraints"]["checks"]
            )
            primary = decision["primary_objective"]
            evaluation_markup = f"""
    <h3>Assessment</h3>
    <ul>
      <li>Status: {html.escape(decision['status'])}</li>
      <li>Reason: {html.escape(decision['reason'])}</li>
      <li>Primary metric: {html.escape(primary['label'])} = <code>{html.escape(primary['actual_display'])}</code></li>
    </ul>
    <h3>Constraint Checks</h3>
    <ul>
      {checks}
    </ul>
"""

        decision_markup = f"""
    <h2>Decision Profile</h2>
    <ul>
      <li>Objective: {html.escape(str(objective['name']))}</li>
      <li>Summary: {html.escape(str(objective.get('summary', '')) or 'No summary provided.')}</li>
      <li>Primary metric: {html.escape(str(objective['primary_metric']))}</li>
      <li>Goal: {html.escape(str(objective['goal']))}</li>
      <li>Target value: <code>{html.escape(str(objective.get('target_value', '-')))}</code></li>
    </ul>
    <h3>Constraints</h3>
    <ul>
      {constraint_rows}
    </ul>
    <h3>Ranking Weights</h3>
    <ul>
      <li>Primary metric boost: {ranking['primary_metric_weight']}</li>
      {ranking_rows}
    </ul>
    {evaluation_markup}
"""

    html_body = f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>QS-DMSS Evidence Report</title>
    <style>
      body {{ font-family: Arial, sans-serif; margin: 32px; color: #111827; }}
      h1, h2 {{ margin-bottom: 0.4rem; }}
      table {{ border-collapse: collapse; width: 100%; margin-top: 16px; }}
      th, td {{ border: 1px solid #d1d5db; padding: 8px; text-align: left; }}
      th {{ background: #f3f4f6; }}
      code {{ background: #f3f4f6; padding: 2px 4px; }}
    </style>
  </head>
  <body>
    <h1>QS-DMSS Evidence Report</h1>
    <p><strong>Run ID:</strong> {html.escape(run_record['run_id'])}</p>
    <p><strong>Name:</strong> {html.escape(run_record['name'])}</p>
    <p><strong>Backend:</strong> {html.escape(run_record['backend'])}</p>
    <p><strong>Config Digest:</strong> <code>{html.escape(run_record['config_digest'])}</code></p>
    <p><strong>Elapsed Seconds:</strong> {metrics['elapsed_seconds']}</p>
    <h2>Summary</h2>
    <ul>
      <li>Initial norm: {metrics['initial_norm']}</li>
      <li>Final norm: {metrics['final_norm']}</li>
      <li>Norm drift: {metrics['norm_drift']}</li>
      <li>Initial energy: {metrics['initial_energy']}</li>
      <li>Final energy: {metrics['final_energy']}</li>
      <li>Energy drift: {metrics['energy_drift']}</li>
    </ul>
    {experiment_markup}
    {decision_markup}
    <h2>Step History</h2>
    <table>
      <thead>
        <tr>
          <th>Step</th>
          <th>Norm</th>
          <th>Energy</th>
          <th>Max Density</th>
        </tr>
      </thead>
      <tbody>
        {rows}
      </tbody>
    </table>
  </body>
</html>
"""
    report_path.write_text(html_body, encoding="utf-8")


def write_experiment_report(
    experiment_dir: Path,
    experiment_record: dict,
    comparison: dict,
) -> None:
    report_path = experiment_dir / "report.html"
    shared = experiment_record.get("shared_experiment")
    shared_markup = ""
    if shared:
        kind = str(shared.get("kind", "comparison"))
        dimensions = shared.get("dimensions") or []
        dimension_rows = "".join(
            f"<li>{html.escape(str(item.get('label') or item.get('path')))} (<code>{html.escape(str(item.get('path')))}</code>)</li>"
            for item in dimensions
        )
        shared_rows = f"""
      <li>Experiment ID: <code>{html.escape(str(shared["id"]))}</code></li>
      <li>Label: {html.escape(str(shared["label"]))}</li>
      <li>Kind: {html.escape(kind)}</li>
"""
        if shared.get("strategy"):
            shared_rows += f"      <li>Strategy: {html.escape(str(shared['strategy']))}</li>\n"
        if shared.get("dimension_count") is not None:
            shared_rows += f"      <li>Dimension count: {html.escape(str(shared['dimension_count']))}</li>\n"
        if shared.get("parameter_label") and shared.get("parameter_path"):
            shared_rows += (
                f"      <li>Primary parameter: {html.escape(str(shared['parameter_label']))} "
                f"(<code>{html.escape(str(shared['parameter_path']))}</code>)</li>\n"
            )
        shared_heading = "Shared Campaign Context" if kind == "campaign" else "Shared Sweep Context"
        shared_markup = f"""
    <h2>{shared_heading}</h2>
    <ul>
{shared_rows}    </ul>
    <h3>Dimensions</h3>
    <ul>
      {dimension_rows}
    </ul>
"""

    highlights = comparison["highlights"]
    decision = comparison.get("decision") or {}
    decision_markup = ""
    if decision.get("available"):
        profile = decision["profile"]
        objective = profile["objective"]
        decision_markup = f"""
    <h2>Recommendation</h2>
    <ul>
      <li>Status: {html.escape(str(decision['status']))}</li>
      <li>Recommended run: <code>{html.escape(str(decision['recommended_run_id']))}</code></li>
      <li>Recommended score: {decision['recommended_score']}</li>
      <li>Reason: {html.escape(str(decision['reason']))}</li>
      <li>Primary metric: {html.escape(str(decision['primary_metric_label']))} ({html.escape(str(decision['primary_goal']))})</li>
      <li>Objective: {html.escape(str(objective['name']))}</li>
    </ul>
"""
    elif decision:
        decision_markup = f"""
    <h2>Recommendation</h2>
    <p>{html.escape(str(decision.get('reason', 'No recommendation is available.')))}</p>
"""

    rows = "\n".join(
        "<tr>"
        f"<td>{html.escape(row['run_id'])}</td>"
        f"<td>{html.escape(str(row['parameter_value_label'] or '-'))}</td>"
        f"<td>{html.escape(str(row.get('decision_rank', '-')))}</td>"
        f"<td>{html.escape(str(row.get('decision_score', '-')))}</td>"
        f"<td>{'yes' if row.get('decision_qualified') else 'no'}</td>"
        f"<td>{row['energy_drift']}</td>"
        f"<td>{row['norm_drift']}</td>"
        f"<td>{row['max_density']}</td>"
        f"<td>{row['elapsed_seconds']}</td>"
        f"<td>{'verified' if row['verification_success'] else 'pending'}</td>"
        "</tr>"
        for row in comparison["rows"]
    )
    html_body = f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>QS-DMSS Experiment Report</title>
    <style>
      body {{ font-family: Arial, sans-serif; margin: 32px; color: #111827; }}
      h1, h2 {{ margin-bottom: 0.4rem; }}
      table {{ border-collapse: collapse; width: 100%; margin-top: 16px; }}
      th, td {{ border: 1px solid #d1d5db; padding: 8px; text-align: left; }}
      th {{ background: #f3f4f6; }}
      code {{ background: #f3f4f6; padding: 2px 4px; }}
    </style>
  </head>
  <body>
    <h1>QS-DMSS Experiment Report</h1>
    <p><strong>Experiment ID:</strong> <code>{html.escape(experiment_record['experiment_id'])}</code></p>
    <p><strong>Label:</strong> {html.escape(experiment_record['label'])}</p>
    <p><strong>Kind:</strong> {html.escape(experiment_record['kind'])}</p>
    <p><strong>Created:</strong> {html.escape(experiment_record['created_at'])}</p>
    <p><strong>Baseline Run:</strong> {html.escape(comparison['baseline_run_id'])}</p>
    <h2>Comparison Summary</h2>
    <ul>
      <li>Run count: {experiment_record['run_count']}</li>
      <li>Energy drift span: {comparison['ranges']['energy_drift']['span']}</li>
      <li>Norm drift span: {comparison['ranges']['norm_drift']['span']}</li>
      <li>Max density span: {comparison['ranges']['max_density']['span']}</li>
      <li>Fastest run: {comparison['ranges']['elapsed_seconds']['min_run_id']}</li>
    </ul>
    <h2>Highlights</h2>
    <ul>
      <li>Lowest absolute energy drift: {html.escape(highlights['lowest_abs_energy_drift_run_id'])}</li>
      <li>Lowest absolute norm drift: {html.escape(highlights['lowest_abs_norm_drift_run_id'])}</li>
      <li>Highest max density: {html.escape(highlights['highest_max_density_run_id'])}</li>
    </ul>
    {shared_markup}
    {decision_markup}
    <h2>Runs</h2>
    <table>
      <thead>
        <tr>
          <th>Run ID</th>
          <th>Variant</th>
          <th>Rank</th>
          <th>Score</th>
          <th>Qualified</th>
          <th>Energy Drift</th>
          <th>Norm Drift</th>
          <th>Max Density</th>
          <th>Elapsed Seconds</th>
          <th>Verification</th>
        </tr>
      </thead>
      <tbody>
        {rows}
      </tbody>
    </table>
  </body>
</html>
"""
    report_path.write_text(html_body, encoding="utf-8")


def write_manifest_for_directory(
    root_dir: Path,
    *,
    manifest_name: str = "manifest.sha256.json",
    bundle_name: str = "evidence_bundle.zip",
) -> Path:
    manifest_path = root_dir / manifest_name
    entries = _manifest_entries(root_dir, {manifest_name, bundle_name})

    manifest = {
        "schema_version": 1,
        "generated_at": _utc_now(),
        "algorithm": "sha256",
        "files": entries,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest_path


def write_manifest(run_dir: Path) -> Path:
    return write_manifest_for_directory(run_dir)


def create_bundle_zip_for_directory(
    root_dir: Path,
    *,
    bundle_name: str = "evidence_bundle.zip",
) -> Path:
    bundle_path = root_dir / bundle_name
    with zipfile.ZipFile(bundle_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for file_path in sorted(path for path in root_dir.rglob("*") if path.is_file()):
            if file_path == bundle_path:
                continue
            archive.write(
                file_path,
                arcname=(Path(root_dir.name) / file_path.relative_to(root_dir)).as_posix(),
            )
    return bundle_path


def create_bundle_zip(run_dir: Path) -> Path:
    return create_bundle_zip_for_directory(run_dir)
