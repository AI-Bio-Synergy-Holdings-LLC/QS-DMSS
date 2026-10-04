"""Isolated recorded-campaign analysis and immutable derived artifacts."""

from __future__ import annotations

import hashlib
import json
import platform
import re
import shutil
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse

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
        items = []
        paths = sorted(self.experiments_root.glob("*/experiment.json"), reverse=True)
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
                items.append(
                    {
                        "experiment_id": path.parent.name,
                        "label": str(record.get("label") or path.parent.name),
                        "run_count": record.get("run_count"),
                        "created_at": record.get("created_at"),
                    }
                )
            except (ValueError, OSError, KeyError, TypeError):
                continue  # Broken records are not launchable; originals remain untouched.
        return {"available": True, "items": items}

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
        with bundle.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
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

    def load(self, analysis_id: str) -> dict:
        self._local()
        root = _directory(self._analysis_root(), analysis_id)
        entries = _entries(_json(_read_bytes(root / "manifest.sha256.json")))
        result = _json(_verified_bytes(root, "analysis.json", entries))
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
        bundle_hash = _read_bytes(root / "bundle.sha256", 64).decode("ascii")
        if (
            hashlib.sha256(
                _read_bytes(root / "evidence_bundle.zip", MAX_BUNDLE_BYTES)
            ).hexdigest()
            != bundle_hash
        ):
            raise RobustnessError(
                "Saved analysis bundle failed its retained integrity hash"
            )
        result["bundle_sha256"] = bundle_hash
        result["urls"] = {"bundle": f"/api/robustness/analyses/{analysis_id}/bundle"}
        return result

    def analyses(self) -> dict:
        self._local()
        items = []
        paths = []
        # Older pathlib glob implementations stat literal child names during
        # enumeration, before the per-artifact error boundary can handle them.
        for directory in self._analysis_root().iterdir():
            path = directory / "analysis.json"
            try:
                paths.append((path.stat().st_mtime_ns, path))
            except OSError:
                continue
        for _, path in sorted(paths, key=lambda item: item[0], reverse=True)[:200]:
            try:
                result = self.load(path.parent.name)
                item = {
                    key: result[key]
                    for key in ("analysis_id", "created_at", "profile_sha256", "source")
                }
            except (HTTPException, OSError, ValueError, KeyError, TypeError):
                continue  # Direct access still fails closed; healthy entries remain discoverable.
            items.append(item)
        return {"items": items}

    def bundle(self, analysis_id: str) -> Path:
        self.load(analysis_id)  # Verify retained metadata before exporting.
        return _directory(self._analysis_root(), analysis_id) / "evidence_bundle.zip"


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
        path = checked(lambda: active.bundle(analysis_id))
        return FileResponse(
            path, media_type="application/zip", filename=f"{analysis_id}.zip"
        )

    return router
