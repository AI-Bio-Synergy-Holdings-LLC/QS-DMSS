from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path
from typing import Any

import numpy as np

from qs_dmss.evidence.bundle import (
    build_environment_lock,
    create_bundle_zip_for_directory,
    write_manifest_for_directory,
)
from qs_dmss.paths import contained_path
from qs_dmss.quantum_sidecar import (
    DEFAULT_EXACT_TOLERANCE,
    DEFAULT_SHOTS,
    MAX_SHOTS,
    QUANTUM_SIDECAR_PROFILE_ID,
    validate_fractal_quantum_sidecar,
    verify_quantum_sidecar_directory,
)


QPU_REQUEST_SCHEMA_VERSION = 1
QPU_REQUEST_PROFILE_ID = "generic-linear-5q"
QPU_REQUEST_JSON = "qpu-request.json"
QPU_REQUEST_MARKDOWN = "README.md"
QPU_REQUEST_MANIFEST = "manifest.sha256.json"
QPU_REQUEST_BUNDLE = "qpu-request-evidence.zip"
SUPPORTED_OPTIMIZATION_LEVELS = (0, 1, 2, 3)

TARGET_PROFILE = {
    "profile_id": QPU_REQUEST_PROFILE_ID,
    "target_kind": "provider-neutral-review-profile",
    "backend_model": "qiskit.providers.fake_provider.GenericBackendV2",
    "num_qubits": 5,
    "basis_gates": ["rz", "sx", "x", "cx"],
    "coupling_map": [
        [0, 1],
        [1, 0],
        [1, 2],
        [2, 1],
        [2, 3],
        [3, 2],
        [3, 4],
        [4, 3],
    ],
    "calibration_source": None,
    "physical_device": False,
    "noise_model": None,
}

CLAIM_BOUNDARY = (
    "Review-only hardware-target transpilation of the validated Fractal SSFM "
    "sidecar profile. It is not a provider connection, QPU submission, hardware "
    "calibration, execution result, cost estimate, quantum advantage claim, or "
    "scientific validation of the underlying physical model."
)


def _require_request_stack() -> dict[str, Any]:
    try:
        from qiskit import QuantumCircuit, qasm3, qpy, transpile
        from qiskit.providers.fake_provider import GenericBackendV2
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "QPU request preparation requires the optional quantum stack. "
            "Install it with: python -m pip install 'qs-dmss[quantum]'"
        ) from exc
    return {
        "QuantumCircuit": QuantumCircuit,
        "GenericBackendV2": GenericBackendV2,
        "qasm3": qasm3,
        "qpy": qpy,
        "transpile": transpile,
    }


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _package_version(package_name: str) -> str | None:
    try:
        return metadata.version(package_name)
    except metadata.PackageNotFoundError:
        return None


def _artifact_entry(root: Path, path: Path, role: str) -> dict[str, Any]:
    return {
        "role": role,
        "path": path.relative_to(root).as_posix(),
        "sha256": _sha256(path),
        "size_bytes": path.stat().st_size,
    }


def _operation_counts(circuit) -> dict[str, int]:
    return {str(name): int(count) for name, count in circuit.count_ops().items()}


def _request_id(*, config_digest: str, shots: int, seed: int, level: int) -> str:
    payload = f"{config_digest}:{QPU_REQUEST_PROFILE_ID}:{shots}:{seed}:{level}"
    return "qpu-" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _write_review_readme(path: Path, request: dict[str, Any]) -> None:
    mapped = request["resources"]["target_transpiled"]
    logical = request["resources"]["logical_measurement_circuit"]
    lines = [
        "# QS-DMSS Fractal SSFM QPU Request Bundle",
        "",
        "Status: **review only; never submitted**",
        "",
        "This bundle maps the simulator-validated Fractal SSFM reference circuit",
        "onto a provider-neutral five-qubit topology. It does not contact a provider,",
        "read credentials, estimate provider pricing, or submit a QPU job.",
        "",
        "## Review Summary",
        "",
        f"- Request ID: `{request['request_id']}`",
        f"- Source profile: `{request['source_profile_id']}`",
        f"- Target profile: `{request['target']['profile_id']}`",
        f"- Requested shots: `{request['execution_request']['shots']}`",
        f"- Logical circuit: `{logical['qubits']}` qubits, depth `{logical['depth']}`",
        f"- Target circuit: `{mapped['qubits']}` qubits, depth `{mapped['depth']}`",
        f"- Target CX count: `{mapped['two_qubit_gates']}`",
        "- Authorized provider spend: `$0.00`",
        "",
        "## Review Checklist",
        "",
        "1. Inspect `qpu-request.json` for the target, shot, cost, and credential policies.",
        "2. Inspect `artifacts/fractal-fuzzy-target.openqasm` and the resource deltas.",
        "3. Confirm the generic coupling map and basis gates are appropriate for review.",
        "4. Review `reference-validation/` before treating the circuit mapping as meaningful.",
        "5. Do not add provider tokens, account identifiers, or private calibration data.",
        "6. A future provider adapter requires a separate explicit approval and security review.",
        "",
        "## Claim Boundary",
        "",
        request["claim_boundary"],
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def prepare_fractal_qpu_request(
    *,
    output_root: str | Path | None = None,
    shots: int = DEFAULT_SHOTS,
    seed: int = 7,
    optimization_level: int = 1,
    exact_tolerance: float = DEFAULT_EXACT_TOLERANCE,
) -> dict[str, Any]:
    if isinstance(shots, bool) or not isinstance(shots, int) or not 128 <= shots <= MAX_SHOTS:
        raise ValueError(f"shots must be an integer between 128 and {MAX_SHOTS}")
    if isinstance(seed, bool) or not isinstance(seed, int) or seed < 0:
        raise ValueError("seed must be a non-negative integer")
    if (
        isinstance(optimization_level, bool)
        or optimization_level not in SUPPORTED_OPTIMIZATION_LEVELS
    ):
        raise ValueError("optimization_level must be one of 0, 1, 2, or 3")
    if exact_tolerance <= 0.0:
        raise ValueError("exact_tolerance must be greater than zero")

    output_path = (
        Path(output_root).resolve()
        if output_root is not None
        else (Path.cwd() / "qpu-request-bundle").resolve()
    )
    if output_path.exists():
        if not output_path.is_dir() or any(output_path.iterdir()):
            raise ValueError(f"QPU request output directory must be empty: {output_path}")
    output_path.mkdir(parents=True, exist_ok=True)
    stack = _require_request_stack()

    reference_dir = contained_path(output_path, "reference-validation")
    reference = validate_fractal_quantum_sidecar(
        output_root=reference_dir,
        shots=shots,
        seed=seed,
        exact_tolerance=exact_tolerance,
    )
    if not reference["success"]:
        raise RuntimeError("Reference quantum-readiness validation did not pass")

    artifacts_dir = contained_path(output_path, "artifacts")
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    evolution_path = contained_path(
        reference_dir,
        reference["artifacts"]["qiskit_qpy"],
    )
    states_path = contained_path(
        reference_dir,
        reference["artifacts"]["state_comparison"],
    )
    with evolution_path.open("rb") as handle:
        evolution_circuit = stack["qpy"].load(handle)[0]
    with np.load(states_path) as states:
        initial_state = np.asarray(states["initial_state"], dtype=np.complex128)

    logical_circuit = stack["QuantumCircuit"](
        evolution_circuit.num_qubits,
        evolution_circuit.num_qubits,
        name="fractal_fuzzy_qpu_request",
    )
    logical_circuit.initialize(initial_state, range(evolution_circuit.num_qubits))
    logical_circuit.compose(evolution_circuit, inplace=True)
    logical_circuit.measure(
        range(evolution_circuit.num_qubits),
        range(evolution_circuit.num_qubits),
    )
    logical_circuit.metadata = {
        "source_profile_id": QUANTUM_SIDECAR_PROFILE_ID,
        "target_profile_id": QPU_REQUEST_PROFILE_ID,
        "submitted": False,
    }

    backend = stack["GenericBackendV2"](
        num_qubits=TARGET_PROFILE["num_qubits"],
        coupling_map=TARGET_PROFILE["coupling_map"],
        basis_gates=TARGET_PROFILE["basis_gates"],
        noise_info=False,
        seed=seed,
    )
    target_circuit = stack["transpile"](
        logical_circuit,
        backend=backend,
        optimization_level=optimization_level,
        seed_transpiler=seed,
    )

    logical_qpy_path = contained_path(artifacts_dir, "fractal-fuzzy-logical.qpy")
    target_qpy_path = contained_path(artifacts_dir, "fractal-fuzzy-target.qpy")
    target_qasm_path = contained_path(artifacts_dir, "fractal-fuzzy-target.openqasm")
    target_text_path = contained_path(artifacts_dir, "fractal-fuzzy-target.txt")
    with logical_qpy_path.open("wb") as handle:
        stack["qpy"].dump(logical_circuit, handle)
    with target_qpy_path.open("wb") as handle:
        stack["qpy"].dump(target_circuit, handle)
    target_qasm_path.write_text(stack["qasm3"].dumps(target_circuit), encoding="utf-8")
    target_text_path.write_text(
        "\n".join(
            [
                "QS-DMSS provider-neutral QPU request circuit",
                f"source profile: {QUANTUM_SIDECAR_PROFILE_ID}",
                f"target profile: {QPU_REQUEST_PROFILE_ID}",
                f"optimization level: {optimization_level}",
                f"qubits: {target_circuit.num_qubits}",
                f"depth: {target_circuit.depth()}",
                f"size: {target_circuit.size()}",
                f"operations: {json.dumps(_operation_counts(target_circuit), sort_keys=True)}",
                "submitted: false",
                "provider: none",
                "",
            ]
        ),
        encoding="utf-8",
    )

    target_path = contained_path(output_path, "target-profile.json")
    _write_json(target_path, TARGET_PROFILE)
    environment_path = contained_path(output_path, "environment.lock.json")
    environment_lock = build_environment_lock()
    environment_lock.setdefault("packages", {}).update(
        {
            name: version
            for name in ("qiskit", "qiskit-aer")
            if (version := _package_version(name)) is not None
        }
    )
    _write_json(environment_path, environment_lock)

    logical_operations = _operation_counts(logical_circuit)
    target_operations = _operation_counts(target_circuit)
    request = {
        "schema_version": QPU_REQUEST_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "request_id": _request_id(
            config_digest=reference["profile"]["config_digest"],
            shots=shots,
            seed=seed,
            level=optimization_level,
        ),
        "state": "draft",
        "source_profile_id": QUANTUM_SIDECAR_PROFILE_ID,
        "claim_boundary": CLAIM_BOUNDARY,
        "submission_policy": {
            "submitted": False,
            "never_submit": True,
            "manual_review_required": True,
            "provider": None,
            "remote_api_called": False,
        },
        "credential_policy": {
            "credentials_read": False,
            "credentials_required_for_bundle": False,
            "provider_adapter_configured": False,
            "secret_fields_allowed": False,
        },
        "cost_policy": {
            "estimated_cost_usd": None,
            "pricing_source": None,
            "max_authorized_cost_usd": 0.0,
            "manual_pricing_review_required": True,
        },
        "execution_request": {
            "intent": "transpilation-review-only",
            "shots": shots,
            "seed_transpiler": seed,
            "optimization_level": optimization_level,
            "result_schema": "measurement-counts",
        },
        "target": TARGET_PROFILE,
        "resources": {
            "logical_measurement_circuit": {
                "qubits": logical_circuit.num_qubits,
                "depth": logical_circuit.depth(),
                "size": logical_circuit.size(),
                "operations": logical_operations,
            },
            "target_transpiled": {
                "qubits": target_circuit.num_qubits,
                "depth": target_circuit.depth(),
                "size": target_circuit.size(),
                "operations": target_operations,
                "two_qubit_gates": int(target_operations.get("cx", 0)),
            },
        },
        "checks": [
            {
                "name": "reference-validation-passed",
                "success": reference["success"],
                "detail": "exact simulator encoding gate passed before transpilation",
            },
            {
                "name": "target-qubit-capacity",
                "success": logical_circuit.num_qubits <= TARGET_PROFILE["num_qubits"],
                "detail": (
                    f"{logical_circuit.num_qubits} logical qubits <= "
                    f"{TARGET_PROFILE['num_qubits']} target qubits"
                ),
            },
            {
                "name": "provider-disconnected",
                "success": True,
                "detail": "generic local target only; no provider SDK or credentials used",
            },
            {
                "name": "zero-authorized-spend",
                "success": True,
                "detail": "max_authorized_cost_usd=0.0",
            },
        ],
    }

    readme_path = contained_path(output_path, QPU_REQUEST_MARKDOWN)
    _write_review_readme(readme_path, request)
    request["artifacts"] = [
        _artifact_entry(output_path, target_path, "target_profile"),
        _artifact_entry(output_path, environment_path, "environment_lock"),
        _artifact_entry(output_path, logical_qpy_path, "logical_qpy"),
        _artifact_entry(output_path, target_qpy_path, "target_qpy"),
        _artifact_entry(output_path, target_qasm_path, "target_openqasm3"),
        _artifact_entry(output_path, target_text_path, "target_summary"),
        _artifact_entry(output_path, readme_path, "review_instructions"),
    ]
    request["reference_validation"] = {
        "success": reference["success"],
        "profile_digest": reference["profile"]["config_digest"],
        "directory": reference_dir.relative_to(output_path).as_posix(),
        "report": Path(reference["report_path"]).relative_to(output_path).as_posix(),
        "evidence_bundle": Path(reference["evidence_bundle_path"])
        .relative_to(output_path)
        .as_posix(),
    }
    request["success"] = all(check["success"] for check in request["checks"])

    request_path = contained_path(output_path, QPU_REQUEST_JSON)
    _write_json(request_path, request)
    manifest_path = write_manifest_for_directory(
        output_path,
        manifest_name=QPU_REQUEST_MANIFEST,
        bundle_name=QPU_REQUEST_BUNDLE,
    )
    bundle_path = create_bundle_zip_for_directory(
        output_path,
        bundle_name=QPU_REQUEST_BUNDLE,
    )
    verification = verify_quantum_sidecar_directory(output_path)
    return {
        **request,
        "success": request["success"] and verification["success"],
        "request_path": str(request_path),
        "review_path": str(readme_path),
        "manifest_path": str(manifest_path),
        "evidence_bundle_path": str(bundle_path),
        "evidence_verification": verification,
    }
