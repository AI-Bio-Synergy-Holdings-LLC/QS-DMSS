"""Isolated recorded-campaign analysis and immutable derived artifacts."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import shutil
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response

from qs_dmss import __version__
from qs_dmss.evidence.bundle import (
    create_bundle_zip_for_directory,
    write_manifest_for_directory,
)
from qs_dmss.paths import contained_path
from qs_dmss.robustness import (
    RobustnessError,
    RobustnessRequest,
    build_robustness_analysis,
    canonical_json,
    fingerprint,
)

MAX_RUNS = 64
MAX_FILE_BYTES = 2 * 1024 * 1024
MAX_SOURCE_BYTES = 16 * 1024 * 1024
MAX_BUNDLE_BYTES = 64 * 1024 * 1024
MAX_DISCOVERY_ENTRIES = 4096
MAX_LISTING_RESPONSE_BYTES = 1024 * 1024
MAX_SUMMARY_LABEL_CHARS = 512
MAX_SUMMARY_TIMESTAMP_CHARS = 64
SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,199}$")


def _read_bytes(path: Path, limit: int = MAX_FILE_BYTES) -> bytes:
    with path.open("rb") as handle:
        payload = handle.read(limit + 1)
    if len(payload) > limit:
        raise RobustnessError("Recorded metadata exceeds the robustness resource limit")
    return payload


def _json(payload: bytes) -> dict:
    record = json.loads(payload)
    if not isinstance(record, dict):
        raise RobustnessError("Recorded metadata must be a JSON object")
    return record


def _directory(root: Path, identifier: str) -> Path:
    if not SAFE_ID.fullmatch(identifier):
        raise HTTPException(404, "Recorded artifact not found")
    candidate = contained_path(root, identifier)
    if candidate.parent != root.resolve() or not candidate.is_dir():
        raise HTTPException(404, "Recorded artifact not found")
    return candidate


def _entries(manifest: dict) -> dict:
    if manifest.get("algorithm") != "sha256":
        raise RobustnessError("Source requires a SHA-256 manifest")
    files = manifest.get("files")
    if not isinstance(files, list) or len(files) > 4096:
        raise RobustnessError("Source manifest is invalid or exceeds resource limits")
    entries = {}
    for entry in files:
        if (
            not isinstance(entry, dict)
            or not isinstance(entry.get("path"), str)
            or not entry["path"]
            or not isinstance(entry.get("sha256"), str)
            or not re.fullmatch(r"[0-9a-f]{64}", entry["sha256"])
            or isinstance(entry.get("size_bytes"), bool)
            or not isinstance(entry.get("size_bytes"), int)
            or entry["size_bytes"] < 0
        ):
            raise RobustnessError("Source manifest contains an invalid file entry")
        entries[entry["path"]] = entry
    if len(entries) != len(files):
        raise RobustnessError("Source manifest has duplicate paths")
    return entries


def _verified_bytes(root: Path, relative: str, entries: dict) -> bytes:
    payload = _read_bytes(contained_path(root, relative))
    entry = entries.get(relative, {})
    if len(payload) != entry.get("size_bytes") or hashlib.sha256(
        payload
    ).hexdigest() != entry.get("sha256"):
        raise RobustnessError("Source metadata failed its recorded integrity manifest")
    return payload


def _discovery_entries(root: Path) -> list[Path]:
    # scandir streams on every supported Python; older Path.iterdir uses listdir.
    # Count all immediate entries, including non-artifacts and _pending, before
    # stat/read/sort work. Never return a misleading partial "latest" collection.
    entries = []
    try:
        with os.scandir(root) as scan:
            for entry in scan:
                if len(entries) == MAX_DISCOVERY_ENTRIES:
                    raise RobustnessError(
                        f"Robustness discovery exceeds the {MAX_DISCOVERY_ENTRIES}-entry scan limit; "
                        "open a known artifact directly or use a smaller evidence root"
                    )
                entries.append(root / entry.name)
    except FileNotFoundError:
        return []  # A read does not create storage; other root errors propagate.
    return entries


def _summary_text(value: object, limit: int, *, nullable: bool = False) -> str | None:
    if nullable and value is None:
        return None
    if not isinstance(value, str) or not value or len(value) > limit:
        raise RobustnessError("Recorded listing summary is invalid or exceeds limits")
    value.encode("utf-8")  # Isolate invalid surrogate text before response encoding.
    return value


def _source_summary(record: dict, experiment_id: str) -> dict:
    label = record.get("label")
    if label is None or label == "":
        label = experiment_id  # Preserve legacy missing/empty-label fallback.
    count = record.get("run_count")
    if (
        isinstance(count, bool)
        or not isinstance(count, int)
        or not 0 <= count <= MAX_RUNS
    ):
        raise RobustnessError("Recorded listing summary is invalid or exceeds limits")
    return {
        "experiment_id": experiment_id,
        "label": _summary_text(label, MAX_SUMMARY_LABEL_CHARS),
        "run_count": count,
        "created_at": _summary_text(
            record.get("created_at"), MAX_SUMMARY_TIMESTAMP_CHARS, nullable=True
        ),
    }


def _analysis_source_summary(source: object) -> dict:
    if not isinstance(source, dict):
        raise RobustnessError("Saved analysis summary is invalid")
    # A selector needs compact identity, not all hashes/conventions or arbitrary
    # nested source data. Direct open/export still returns the full provenance.
    summary = {"label": _summary_text(source.get("label"), MAX_SUMMARY_LABEL_CHARS)}
    if "experiment_id" in source:
        identifier = source["experiment_id"]
        if not isinstance(identifier, str) or not SAFE_ID.fullmatch(identifier):
            raise RobustnessError("Saved analysis summary is invalid")
        summary["experiment_id"] = identifier
    if "source_fingerprint" in source:
        digest = source["source_fingerprint"]
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise RobustnessError("Saved analysis summary is invalid")
        summary["source_fingerprint"] = digest
    if "legacy_convention" in source:
        if not isinstance(source["legacy_convention"], bool):
            raise RobustnessError("Saved analysis summary is invalid")
        summary["legacy_convention"] = source["legacy_convention"]
    return summary


def _listing_size(payload: dict) -> int:
    # Match JSONResponse's compact UTF-8 serialization, including escaping.
    size = len(
        json.dumps(
            payload, ensure_ascii=False, allow_nan=False, separators=(",", ":")
        ).encode("utf-8")
    )
    return _checked_listing_size(size)


def _checked_listing_size(size: int) -> int:
    if size > MAX_LISTING_RESPONSE_BYTES:
        raise RobustnessError(
            "Robustness listing exceeds the response resource limit; "
            "open a known artifact directly or use a smaller evidence root"
        )
    return size


def _append_listing_item(payload: dict, item: dict, size: int) -> int:
    # Check before retaining an item. Include the empty envelope and list commas;
    # overflow must propagate, never be treated as an invalid individual record.
    size = _checked_listing_size(size + _listing_size(item) + bool(payload["items"]))
    payload["items"].append(item)
    return size


@dataclass(frozen=True)
class CockpitRobustnessService:
    experiments_root: Path
    hosted_demo_enabled: bool = False

    def _local(self) -> None:
        if self.hosted_demo_enabled:
            raise HTTPException(403, "Recommendation robustness pilot is local-only")

    def sources(self) -> dict:
        if self.hosted_demo_enabled:
            return {"available": False, "items": [], "reason": "Local-only pilot"}
        payload = {"available": True, "items": []}
        response_size = _listing_size(payload)
        paths = []
        for directory in _discovery_entries(self.experiments_root):
            try:
                root = _directory(self.experiments_root, directory.name)
                path = contained_path(root, "experiment.json")
                if path.is_file():
                    paths.append(path)
            except (HTTPException, ValueError, OSError):
                continue
        paths.sort(reverse=True)
        for path in paths[:200]:
            try:
                record = _json(_read_bytes(contained_path(self.experiments_root, path)))
                decision = record.get("decision")
                if (
                    record.get("kind") != "campaign"
                    or record.get("status", "completed") != "completed"
                    or not isinstance(decision, dict)
                    or not decision.get("available")
                ):
                    continue
                item = _source_summary(record, path.parent.name)
            except (ValueError, OSError, KeyError, TypeError, RecursionError):
                continue  # Broken records are not launchable; originals remain untouched.
            response_size = _append_listing_item(payload, item, response_size)
        return payload

    def _source(self, experiment_id: str) -> tuple[dict, dict[str, bytes]]:
        self._local()
        root = _directory(self.experiments_root, experiment_id)
        manifest_bytes = _read_bytes(contained_path(root, "manifest.sha256.json"))
        entries = _entries(_json(manifest_bytes))
        captures = {"manifest.sha256.json": manifest_bytes}

        def capture(relative: str) -> dict:
            captures[relative] = _verified_bytes(root, relative, entries)
            if sum(map(len, captures.values())) > MAX_SOURCE_BYTES:
                raise RobustnessError(
                    "Source metadata exceeds the total robustness resource limit"
                )
            return _json(captures[relative])

        record = capture("experiment.json")
        comparison = capture("comparison.json")
        if (
            record.get("experiment_id") != experiment_id
            or record.get("kind") != "campaign"
            or record.get("status", "completed") != "completed"
        ):
            raise RobustnessError(
                "Select a completed campaign with a recorded scoring profile"
            )
        rows = comparison.get("rows", [])
        if not isinstance(rows, list) or not 2 <= len(rows) <= MAX_RUNS:
            raise RobustnessError("Robustness requires 2 to 64 recorded configurations")
        run_ids = [row["run_id"] for row in rows]
        if len(set(run_ids)) != len(rows) or run_ids != record.get("run_ids"):
            raise RobustnessError("Campaign run identity or ordering is inconsistent")
        decision = comparison.get("decision")
        if (
            not isinstance(decision, dict)
            or not decision.get("available")
            or not isinstance(decision.get("profile"), dict)
        ):
            raise RobustnessError("Campaign has no shared scoring profile")
        conventions = {}
        for row in rows:
            run_id = row["run_id"]
            if not isinstance(run_id, str) or not SAFE_ID.fullmatch(run_id):
                raise RobustnessError("Invalid recorded run identity")
            metrics = capture(f"runs/{run_id}/metrics.json")
            run = capture(f"runs/{run_id}/run.json")
            for metric in (
                "energy_drift",
                "norm_drift",
                "max_density",
                "elapsed_seconds",
            ):
                value = row.get(metric)
                expected = (
                    run.get(metric)
                    if metric == "elapsed_seconds"
                    else metrics.get(metric)
                )
                if (
                    isinstance(value, bool)
                    or not isinstance(value, (int, float))
                    or isinstance(expected, bool)
                    or not isinstance(expected, (int, float))
                    or value != expected
                    or not -1e12 <= value <= 1e12
                ):
                    raise RobustnessError(
                        "Comparison metrics disagree with captured run evidence or exceed limits"
                    )
            if not isinstance(row.get("verification_success"), bool):
                raise RobustnessError("Recorded verification state is missing")
            if run.get("run_id") != run_id:
                raise RobustnessError("Captured run identity is inconsistent")
            convention = metrics.get(
                "energy_diagnostic_convention", "legacy/unspecified"
            )
            if not isinstance(convention, str) or not convention.strip():
                raise RobustnessError(
                    "Energy diagnostic convention must be a non-empty string"
                )
            conventions[run_id] = convention
        if len(set(conventions.values())) != 1:
            raise RobustnessError(
                "Mixed energy diagnostic conventions cannot be rescored together"
            )
        bundle = contained_path(root, "evidence_bundle.zip")
        if bundle.stat().st_size > MAX_BUNDLE_BYTES:
            raise RobustnessError("Source bundle exceeds the robustness resource limit")
        digest = hashlib.sha256()
        bundle_bytes = 0
        with bundle.open("rb") as handle:
            # The file can grow after stat. Bound every read and reject after
            # at most one overflow-detection byte; never hash an oversized chunk.
            while chunk := handle.read(
                min(1024 * 1024, MAX_BUNDLE_BYTES - bundle_bytes + 1)
            ):
                bundle_bytes += len(chunk)
                if bundle_bytes > MAX_BUNDLE_BYTES:
                    raise RobustnessError(
                        "Source bundle exceeds the robustness resource limit"
                    )
                digest.update(chunk)
        hashes = {
            name: hashlib.sha256(data).hexdigest() for name, data in captures.items()
        }
        hashes["evidence_bundle.zip"] = digest.hexdigest()
        identity = {
            "experiment_id": experiment_id,
            "sha256": hashes,
            "energy_diagnostic_conventions": conventions,
        }
        return {
            **identity,
            "source_fingerprint": fingerprint(identity),
            "label": str(record.get("label") or experiment_id),
            "comparison": comparison,
            "integrity_scope": "Compared metadata verified against the campaign manifest; full bundle hash pinned. Not a fresh verification of every solver artifact.",
            "verification_scope": "verification_success is the state recorded when the campaign was created",
            "legacy_convention": "legacy/unspecified" in conventions.values(),
        }, captures

    def source(self, experiment_id: str) -> dict:
        source, _ = self._source(experiment_id)
        return source

    def preview(self, request: RobustnessRequest) -> dict:
        source, _ = self._source(request.experiment_id)
        if source["source_fingerprint"] != request.source_fingerprint:
            raise HTTPException(
                409, "Source evidence changed; reopen the campaign before analyzing"
            )
        result = build_robustness_analysis(source["comparison"]["rows"], request)
        return {
            **result,
            "source": {
                key: value for key, value in source.items() if key != "comparison"
            },
        }

    def _analysis_root(self) -> Path:
        return contained_path(self.experiments_root, "_robustness")

    def save(self, request: RobustnessRequest) -> dict:
        # Read once: the exact verified bytes and scores form one retained snapshot.
        source, captures = self._source(request.experiment_id)
        if source["source_fingerprint"] != request.source_fingerprint:
            raise HTTPException(
                409, "Source evidence changed; reopen the campaign before saving"
            )
        result = build_robustness_analysis(source["comparison"]["rows"], request)
        root = self._analysis_root()
        root.mkdir(parents=True, exist_ok=True)
        pending_root = contained_path(root, "_pending")
        pending_root.mkdir(parents=True, exist_ok=True)
        for _ in range(3):
            analysis_id = f"robustness-{uuid.uuid4().hex}"
            published = contained_path(root, analysis_id)
            if published.exists():
                continue
            destination = contained_path(pending_root, analysis_id)
            try:
                destination.mkdir(exist_ok=False)
                break
            except FileExistsError:
                continue
        else:
            raise HTTPException(503, "Could not allocate an analysis identity; retry")
        try:
            result.update(
                {
                    "analysis_id": analysis_id,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "core_version": __version__,
                    "environment": {
                        "python": platform.python_version(),
                        "platform": platform.system(),
                    },
                    "implementation_sha256": {
                        name: hashlib.sha256(
                            _read_bytes(Path(__file__).parents[1] / name)
                        ).hexdigest()
                        for name in (
                            "decision.py",
                            "robustness.py",
                            "cockpit/robustness.py",
                        )
                    },
                    "source": {
                        key: value
                        for key, value in source.items()
                        if key != "comparison"
                    },
                    "retained_source_scope": "Compared JSON metadata and original campaign manifest. Full source bundle is hash-referenced, not duplicated.",
                }
            )
            analysis_bytes = canonical_json(result)
            if len(analysis_bytes) > MAX_FILE_BYTES:
                raise RobustnessError(
                    "Derived analysis exceeds the artifact resource limit"
                )
            (destination / "analysis.json").write_bytes(analysis_bytes)
            for name, payload in captures.items():
                path = contained_path(destination, "source", name)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(payload)
            write_manifest_for_directory(destination)
            bundle = create_bundle_zip_for_directory(destination)
            (destination / "bundle.sha256").write_text(
                hashlib.sha256(_read_bytes(bundle, MAX_BUNDLE_BYTES)).hexdigest(),
                encoding="ascii",
            )
            if published.exists():
                raise HTTPException(503, "Analysis identity became unavailable; retry")
            destination.rename(published)
        except Exception:
            # Only remove the newly allocated, contained, incomplete artifact.
            shutil.rmtree(destination)
            raise
        return self.load(analysis_id)

    def _analysis_metadata(self, analysis_id: str) -> tuple[Path, dict, dict]:
        self._local()
        root = _directory(self._analysis_root(), analysis_id)
        entries = _entries(
            _json(_read_bytes(contained_path(root, "manifest.sha256.json")))
        )
        result = _json(_verified_bytes(root, "analysis.json", entries))
        return root, entries, result

    def _summary(self, analysis_id: str) -> dict:
        _, _, result = self._analysis_metadata(analysis_id)
        if result.get("analysis_id") != analysis_id:
            raise RobustnessError("Saved analysis identity is inconsistent")
        summary = {
            "analysis_id": analysis_id,
            "created_at": _summary_text(
                result["created_at"], MAX_SUMMARY_TIMESTAMP_CHARS
            ),
            "profile_sha256": result["profile_sha256"],
            "source": _analysis_source_summary(result["source"]),
        }
        if not isinstance(summary["profile_sha256"], str) or not re.fullmatch(
            r"[0-9a-f]{64}", summary["profile_sha256"]
        ):
            raise RobustnessError("Saved analysis summary is invalid")
        # Discovery is not full artifact verification; open/export still use load().
        return {**summary, "integrity_scope": "analysis_json_only"}

    def load(self, analysis_id: str) -> dict:
        result, _ = self._load_snapshot(analysis_id)
        return result

    def _load_snapshot(self, analysis_id: str) -> tuple[dict, bytes]:
        root, entries, result = self._analysis_metadata(analysis_id)
        retained_bytes = 0
        for relative in entries:
            if relative.startswith("source/"):
                retained_bytes += len(_verified_bytes(root, relative, entries))
                if retained_bytes > MAX_SOURCE_BYTES:
                    raise RobustnessError(
                        "Retained source exceeds the total robustness resource limit"
                    )
        if result.get("analysis_id") != analysis_id:
            raise RobustnessError("Saved analysis identity is inconsistent")
        bundle_hash = _read_bytes(contained_path(root, "bundle.sha256"), 64).decode(
            "ascii"
        )
        bundle = _read_bytes(
            contained_path(root, "evidence_bundle.zip"), MAX_BUNDLE_BYTES
        )
        if hashlib.sha256(bundle).hexdigest() != bundle_hash:
            raise RobustnessError(
                "Saved analysis bundle failed its retained integrity hash"
            )
        result["bundle_sha256"] = bundle_hash
        result["urls"] = {"bundle": f"/api/robustness/analyses/{analysis_id}/bundle"}
        return result, bundle

    def analyses(self) -> dict:
        self._local()
        payload = {"items": []}
        response_size = _listing_size(payload)
        paths = []
        root = self._analysis_root()
        for directory in _discovery_entries(root):
            try:
                artifact = _directory(root, directory.name)
                path = contained_path(artifact, "analysis.json")
                paths.append((path.stat().st_mtime_ns, path))
            except (HTTPException, ValueError, OSError):
                continue
        for _, path in sorted(paths, key=lambda item: item[0], reverse=True)[:200]:
            try:
                item = self._summary(path.parent.name)
            except (
                HTTPException,
                OSError,
                ValueError,
                KeyError,
                TypeError,
                RecursionError,
            ):
                continue  # Direct access still fails closed; healthy entries remain discoverable.
            response_size = _append_listing_item(payload, item, response_size)
        return payload

    def bundle(self, analysis_id: str) -> Path:
        # Compatibility for local callers. HTTP must use the verified byte
        # snapshot below rather than reopening this mutable filesystem path.
        self.load(analysis_id)  # Verify retained metadata before exporting.
        return contained_path(
            _directory(self._analysis_root(), analysis_id), "evidence_bundle.zip"
        )

    def bundle_snapshot(self, analysis_id: str) -> bytes:
        _, bundle = self._load_snapshot(analysis_id)
        return bundle


def robustness_router(service_dependency: Callable) -> APIRouter:
    router = APIRouter(prefix="/api/robustness", tags=["recorded robustness"])

    def service(request: Request) -> CockpitRobustnessService:
        cockpit = service_dependency(request)
        return CockpitRobustnessService(
            cockpit.experiments_root, cockpit.hosted_demo.enabled
        )

    def checked(action: Callable):
        try:
            return action()
        except RobustnessError as exc:
            raise HTTPException(400, str(exc)) from exc
        except (OSError, ValueError, KeyError, TypeError) as exc:
            # Never send filesystem paths or raw parser exception text to clients.
            raise HTTPException(
                400,
                "Recorded robustness evidence is invalid, incompatible, or exceeds resource limits",
            ) from exc

    @router.get("/sources")
    def sources(active: CockpitRobustnessService = Depends(service)):
        return checked(active.sources)

    @router.get("/sources/{experiment_id}")
    def source(experiment_id: str, active: CockpitRobustnessService = Depends(service)):
        return checked(lambda: active.source(experiment_id))

    @router.post("/preview")
    def preview(
        payload: RobustnessRequest, active: CockpitRobustnessService = Depends(service)
    ):
        return checked(lambda: active.preview(payload))

    @router.post("/analyses")
    def save(
        payload: RobustnessRequest, active: CockpitRobustnessService = Depends(service)
    ):
        return checked(lambda: active.save(payload))

    @router.get("/analyses")
    def analyses(active: CockpitRobustnessService = Depends(service)):
        return checked(active.analyses)

    @router.get("/analyses/{analysis_id}")
    def load(analysis_id: str, active: CockpitRobustnessService = Depends(service)):
        return checked(lambda: active.load(analysis_id))

    @router.get("/analyses/{analysis_id}/bundle")
    def bundle(analysis_id: str, active: CockpitRobustnessService = Depends(service)):
        payload = checked(lambda: active.bundle_snapshot(analysis_id))
        return Response(
            payload,
            media_type="application/zip",
            headers={
                "Content-Disposition": f'attachment; filename="{analysis_id}.zip"'
            },
        )

    return router
