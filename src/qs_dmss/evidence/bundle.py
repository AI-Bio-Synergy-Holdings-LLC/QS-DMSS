from __future__ import annotations

import hashlib
import html
import json
import platform
import zipfile
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


def write_report(run_dir: Path, run_record: dict, metrics: dict) -> None:
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
        experiment_markup = f"""
    <h2>Experiment Context</h2>
    <ul>
      <li>Experiment ID: <code>{html.escape(str(experiment['id']))}</code></li>
      <li>Label: {html.escape(str(experiment['label']))}</li>
      <li>Parameter: {html.escape(str(experiment['parameter_label']))} (<code>{html.escape(str(experiment['parameter_path']))}</code>)</li>
      <li>Value: {html.escape(str(experiment['parameter_value_label']))}</li>
      <li>Ordinal: {experiment['ordinal']} of {experiment['total_runs']}</li>
    </ul>
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


def write_manifest(run_dir: Path) -> Path:
    manifest_path = run_dir / "manifest.sha256.json"
    entries = []
    for file_path in sorted(path for path in run_dir.rglob("*") if path.is_file()):
        relative_path = file_path.relative_to(run_dir).as_posix()
        if relative_path in {"manifest.sha256.json", "evidence_bundle.zip"}:
            continue
        entries.append(
            {
                "path": relative_path,
                "sha256": _file_sha256(file_path),
                "size_bytes": file_path.stat().st_size,
            }
        )

    manifest = {
        "schema_version": 1,
        "generated_at": _utc_now(),
        "algorithm": "sha256",
        "files": entries,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest_path


def create_bundle_zip(run_dir: Path) -> Path:
    bundle_path = run_dir / "evidence_bundle.zip"
    with zipfile.ZipFile(bundle_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for file_path in sorted(path for path in run_dir.rglob("*") if path.is_file()):
            if file_path == bundle_path:
                continue
            archive.write(
                file_path,
                arcname=(Path(run_dir.name) / file_path.relative_to(run_dir)).as_posix(),
            )
    return bundle_path
