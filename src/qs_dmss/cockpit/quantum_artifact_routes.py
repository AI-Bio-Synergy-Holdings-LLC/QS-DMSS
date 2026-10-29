"""Quantum artifact registration with application-owned lookup and response policy."""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Protocol

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse


class _QuantumArtifactService(Protocol):
    def quantum_validation_artifact_path(self, artifact_name: str) -> Path:
        pass

    def quantum_validation_run_artifact_path(
        self, run_id: str, artifact_name: str
    ) -> Path:
        pass


def register_quantum_artifact_routes(
    app: FastAPI,
    service_dependency: Callable[..., _QuantumArtifactService],
    quantum_validation_file_response: Callable[..., FileResponse],
    quantum_compilation_showcase_artifact_key: Callable[[str], str],
) -> None:
    """Move two GET registrations only; retain the distinct injected HTML policy."""

    @app.get("/api/quantum-validation/files/{artifact_name}")
    def quantum_validation_artifact(
        artifact_name: str,
        active_service: _QuantumArtifactService = Depends(service_dependency),
    ) -> FileResponse:
        path = active_service.quantum_validation_artifact_path(artifact_name)
        artifact_key = quantum_compilation_showcase_artifact_key(artifact_name)
        return quantum_validation_file_response(
            active_service,
            path,
            artifact_key,
        )

    @app.get(
        "/api/quantum-validation/runs/{run_id}/files/{artifact_name}"
    )
    def quantum_validation_run_artifact(
        run_id: str,
        artifact_name: str,
        active_service: _QuantumArtifactService = Depends(service_dependency),
    ) -> FileResponse:
        path = active_service.quantum_validation_run_artifact_path(
            run_id,
            artifact_name,
        )
        try:
            artifact_key = quantum_compilation_showcase_artifact_key(artifact_name)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail="Quantum artifact not found") from exc
        return quantum_validation_file_response(
            active_service,
            path,
            artifact_key,
        )
