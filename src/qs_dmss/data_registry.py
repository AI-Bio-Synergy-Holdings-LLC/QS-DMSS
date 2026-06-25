from __future__ import annotations

import hashlib
import json
import os
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from qs_dmss.paths import bundled_assets_root, contained_path, safe_filename


DATA_REGISTRY_SCHEMA_VERSION = 1
DATA_CALIBRATION_REPORT_SCHEMA_VERSION = 1
DATA_CALIBRATION_JSON_REPORT = "reference-data-calibration.json"
DATA_CALIBRATION_MARKDOWN_REPORT = "reference-data-calibration.md"
DATA_CALIBRATION_BUNDLE = "reference-data-calibration-evidence.zip"


@dataclass(frozen=True)
class PublicDataSource:
    source_id: str
    payload: dict[str, Any]


def data_assets_root() -> Path:
    root = bundled_assets_root() / "data"
    if not root.exists():
        raise FileNotFoundError(f"Data registry assets not found at {root}")
    return root


def source_registry_path() -> Path:
    path = data_assets_root() / "public-sources.json"
    if not path.exists():
        raise FileNotFoundError(f"Public data-source registry not found at {path}")
    return path


def calibration_fixture_path() -> Path:
    path = data_assets_root() / "calibration" / "workflow-smoke-reference.json"
    if not path.exists():
        raise FileNotFoundError(f"Calibration fixture not found at {path}")
    return path


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_registry() -> dict[str, Any]:
    registry = _read_json(source_registry_path())
    if registry.get("schema_version") != DATA_REGISTRY_SCHEMA_VERSION:
        raise ValueError("Unsupported public data-source registry schema")
    sources = registry.get("sources")
    if not isinstance(sources, list):
        raise ValueError("Public data-source registry missing sources list")
    return registry


def list_data_sources() -> list[PublicDataSource]:
    registry = _load_registry()
    sources = [
        PublicDataSource(source_id=str(source["id"]), payload=source)
        for source in registry["sources"]
    ]
    return sorted(sources, key=lambda source: source.source_id)


def _normalize_source_id(source_id: str) -> str:
    return safe_filename(source_id.lower(), default="source")


def resolve_data_source(source_id: str) -> PublicDataSource:
    normalized = _normalize_source_id(source_id)
    for source in list_data_sources():
        if source.source_id == normalized:
            return source
    raise FileNotFoundError(f"Public data source not found: {normalized}")


def default_cache_root() -> Path:
    override = os.environ.get("QS_DMSS_CACHE_DIR")
    if override:
        return Path(override).expanduser().resolve()

    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        return (Path(local_app_data) / "qs-dmss" / "cache").resolve()

    xdg_cache_home = os.environ.get("XDG_CACHE_HOME")
    if xdg_cache_home:
        return (Path(xdg_cache_home) / "qs-dmss").expanduser().resolve()

    return (Path.home() / ".cache" / "qs-dmss").resolve()


def _materialize_source_manifest(
    source: PublicDataSource,
    cache_root: Path,
    *,
    access_date: str,
) -> dict[str, Any]:
    source_dir = contained_path(cache_root, "public-data-sources", source.source_id)
    source_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = source_dir / "source-manifest.json"
    manifest = {
        "schema_version": 1,
        "cached_at": datetime.now(timezone.utc).isoformat(),
        "access_date": access_date,
        "source_id": source.source_id,
        "source": source.payload,
        "cache_policy": source.payload.get("cache_policy", ""),
        "claim_boundary": (
            "Cached metadata only; provider datasets are not bundled or mirrored by QS-DMSS."
        ),
    }
    _write_json(manifest_path, manifest)
    return {
        "role": "source_manifest",
        "source_id": source.source_id,
        "path": str(manifest_path),
        "sha256": _sha256(manifest_path),
        "size_bytes": manifest_path.stat().st_size,
        "source_url": source.payload.get("official_url"),
        "access_date": access_date,
        "citation": source.payload.get("citation"),
    }


def _materialize_calibration_fixture(cache_root: Path) -> dict[str, Any]:
    fixture = _read_json(calibration_fixture_path())
    fixture_dir = contained_path(cache_root, "public-data-calibration")
    fixture_dir.mkdir(parents=True, exist_ok=True)
    fixture_path = fixture_dir / "workflow-smoke-reference.json"
    _write_json(fixture_path, fixture)
    return {
        "role": "calibration_fixture",
        "fixture_id": fixture.get("fixture_id"),
        "path": str(fixture_path),
        "sha256": _sha256(fixture_path),
        "size_bytes": fixture_path.stat().st_size,
    }


def _copy_cache_entry_to_output(entry: dict[str, Any], output_root: Path) -> dict[str, Any]:
    source_path = Path(entry["path"])
    if entry["role"] == "source_manifest":
        file_name = (
            f"{safe_filename(str(entry['source_id']), default='source')}"
            ".source-manifest.json"
        )
        target_path = contained_path(output_root, "cached-sources", file_name)
    else:
        target_path = contained_path(
            output_root,
            "calibration-inputs",
            safe_filename(source_path.name, default="calibration-input.json"),
        )
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_bytes(source_path.read_bytes())
    copied = {
        **entry,
        "evidence_path": str(target_path),
        "evidence_sha256": _sha256(target_path),
        "evidence_size_bytes": target_path.stat().st_size,
    }
    return copied


def _build_checks(
    selected_sources: list[PublicDataSource],
    cache_entries: list[dict[str, Any]],
    fixture: dict[str, Any],
) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    cache_by_source = {
        entry.get("source_id"): entry
        for entry in cache_entries
        if entry.get("role") == "source_manifest"
    }
    for source in selected_sources:
        payload = source.payload
        source_cache = cache_by_source.get(source.source_id)
        checks.extend(
            [
                {
                    "name": f"source:{source.source_id}:official_url",
                    "success": bool(payload.get("official_url")),
                    "detail": payload.get("official_url") or "missing official URL",
                },
                {
                    "name": f"source:{source.source_id}:citation",
                    "success": bool(payload.get("citation")),
                    "detail": payload.get("citation") or "missing citation",
                },
                {
                    "name": f"source:{source.source_id}:cached_manifest",
                    "success": bool(source_cache and source_cache.get("sha256")),
                    "detail": (
                        source_cache.get("sha256")
                        if source_cache
                        else "missing cached manifest"
                    ),
                },
            ]
        )

    fixture_entry = next(
        (entry for entry in cache_entries if entry.get("role") == "calibration_fixture"),
        None,
    )
    checks.append(
        {
            "name": "calibration_fixture:cached",
            "success": bool(fixture_entry and fixture_entry.get("sha256")),
            "detail": (
                fixture_entry.get("sha256")
                if fixture_entry
                else "missing calibration fixture"
            ),
        }
    )
    checks.append(
        {
            "name": "calibration_fixture:selected_sources",
            "success": bool(selected_sources)
            and {
                source.source_id for source in selected_sources
            }.issubset(set(fixture["source_ids"])),
            "detail": f"{len(selected_sources)} selected source records",
        }
    )
    return checks


def _markdown_table_cell(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def _markdown_report(report: dict[str, Any]) -> str:
    status = "PASS" if report["success"] else "FAIL"
    lines = [
        "# QS-DMSS Reference-Data Calibration Sandbox",
        "",
        f"Overall status: **{status}**",
        f"Generated at: `{report['generated_at']}`",
        f"Output root: `{report['output_root']}`",
        f"Cache root: `{report['cache_root']}`",
        f"Evidence bundle: `{report['evidence_bundle_path']}`",
        "",
        "This workflow records public reference-data provenance, source citations,",
        "local cache checksums, and a tiny calibration fixture. It is a calibration",
        "sandbox for reproducible workflows, not a fine-tuned scientific model and",
        "not peer-reviewed scientific validation.",
        "",
        "## Sources",
        "",
        "| Source | Release | Official URL | Citation |",
        "| --- | --- | --- | --- |",
    ]
    for source in report["sources"]:
        lines.append(
            "| "
            f"{_markdown_table_cell(source['id'])} | "
            f"{_markdown_table_cell(source.get('release', ''))} | "
            f"{_markdown_table_cell(source['official_url'])} | "
            f"{_markdown_table_cell(source.get('citation', ''))} |"
        )

    lines.extend(
        [
            "",
            "## Checks",
            "",
            "| Check | Status | Detail |",
            "| --- | --- | --- |",
        ]
    )
    for check in report["checks"]:
        check_status = "PASS" if check["success"] else "FAIL"
        detail = _markdown_table_cell(check["detail"])
        lines.append(f"| {check['name']} | {check_status} | {detail} |")

    lines.extend(
        [
            "",
            "## Boundary",
            "",
            report["claim_boundary"],
            "",
        ]
    )
    return "\n".join(lines)


def _write_evidence_bundle(
    bundle_path: Path,
    files: list[Path],
) -> dict[str, Any]:
    entries = []
    with zipfile.ZipFile(bundle_path, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
        for path in files:
            arcname = path.name
            if path.parent.name in {"cached-sources", "calibration-inputs"}:
                arcname = f"{path.parent.name}/{path.name}"
            bundle.write(path, arcname)
            entries.append(
                {
                    "path": arcname,
                    "sha256": _sha256(path),
                    "size_bytes": path.stat().st_size,
                }
            )

        manifest = {
            "schema_version": 1,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "entries": entries,
        }
        bundle.writestr(
            "evidence-manifest.json",
            json.dumps(manifest, indent=2, sort_keys=True),
        )
    return {
        "path": str(bundle_path),
        "sha256": _sha256(bundle_path),
        "size_bytes": bundle_path.stat().st_size,
        "entries": entries,
    }


def run_reference_calibration(
    *,
    output_root: str | Path | None = None,
    cache_root: str | Path | None = None,
    source_ids: list[str] | tuple[str, ...] | None = None,
) -> dict[str, Any]:
    output_path = (
        Path(output_root).resolve()
        if output_root is not None
        else (Path.cwd() / "reference-data-calibration").resolve()
    )
    output_path.mkdir(parents=True, exist_ok=True)

    cache_path = (
        Path(cache_root).expanduser().resolve()
        if cache_root is not None
        else default_cache_root()
    )
    cache_path.mkdir(parents=True, exist_ok=True)

    fixture = _read_json(calibration_fixture_path())
    if fixture.get("schema_version") != 1:
        raise ValueError("Unsupported calibration fixture schema")

    selected_ids = list(source_ids) if source_ids else list(fixture["source_ids"])
    selected_sources = [resolve_data_source(source_id) for source_id in selected_ids]
    access_date = datetime.now(timezone.utc).date().isoformat()

    cache_entries = [
        _materialize_source_manifest(source, cache_path, access_date=access_date)
        for source in selected_sources
    ]
    cache_entries.append(_materialize_calibration_fixture(cache_path))
    evidence_cache_entries = [
        _copy_cache_entry_to_output(entry, output_path)
        for entry in cache_entries
    ]

    config = {
        "schema_version": 1,
        "source_ids": [source.source_id for source in selected_sources],
        "cache_root": str(cache_path),
        "output_root": str(output_path),
        "transform_script": fixture["calibration_contract"]["transform_script"],
        "claim_boundary": fixture["claim_boundary"],
    }
    config_path = contained_path(output_path, "calibration-config.json")
    _write_json(config_path, config)

    checks = _build_checks(selected_sources, cache_entries, fixture)
    success = all(check["success"] for check in checks)
    source_payloads = [
        {
            "id": source.source_id,
            "name": source.payload["name"],
            "provider": source.payload["provider"],
            "release": source.payload["release"],
            "official_url": source.payload["official_url"],
            "documentation_url": source.payload["documentation_url"],
            "citation": source.payload["citation"],
            "citation_url": source.payload["citation_url"],
            "access_date": access_date,
        }
        for source in selected_sources
    ]

    report = {
        "schema_version": DATA_CALIBRATION_REPORT_SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "success": success,
        "output_root": str(output_path),
        "cache_root": str(cache_path),
        "claim_boundary": fixture["claim_boundary"],
        "transform_script": fixture["calibration_contract"]["transform_script"],
        "config_path": str(config_path),
        "sources": source_payloads,
        "cache_entries": cache_entries,
        "evidence_cache_entries": evidence_cache_entries,
        "checks": checks,
        "metrics": {
            "source_count": len(selected_sources),
            "citation_count": sum(
                1 for source in source_payloads if source.get("citation")
            ),
            "official_url_count": sum(
                1 for source in source_payloads if source.get("official_url")
            ),
            "cached_entry_count": len(cache_entries),
            "provenance_score": (
                sum(1 for check in checks if check["success"]) / len(checks)
                if checks
                else 0.0
            ),
        },
    }

    report_path = contained_path(output_path, DATA_CALIBRATION_JSON_REPORT)
    markdown_path = contained_path(output_path, DATA_CALIBRATION_MARKDOWN_REPORT)
    bundle_path = contained_path(output_path, DATA_CALIBRATION_BUNDLE)
    report["report_path"] = str(report_path)
    report["markdown_report_path"] = str(markdown_path)
    report["evidence_bundle_path"] = str(bundle_path)

    _write_json(report_path, report)
    markdown_path.write_text(_markdown_report(report), encoding="utf-8")
    bundle_files = [
        report_path,
        markdown_path,
        config_path,
        *[Path(entry["evidence_path"]) for entry in evidence_cache_entries],
    ]
    bundle = _write_evidence_bundle(bundle_path, bundle_files)
    report["evidence_bundle"] = bundle
    _write_json(report_path, report)
    return report
