from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path
from typing import Any

import numpy as np

from qs_dmss.core.fractal_ssfm import FractalQuadrantSSFMSolver
from qs_dmss.evidence.bundle import (
    build_environment_lock,
    create_bundle_zip_for_directory,
    write_manifest_for_directory,
)
from qs_dmss.io.config import SimulationConfig, config_digest, load_config, write_config
from qs_dmss.paths import contained_path, quantum_sidecar_config_path


QUANTUM_SIDECAR_SCHEMA_VERSION = 1
QUANTUM_SIDECAR_PROFILE_ID = "fractal-fuzzy-4x4-linear"
QUANTUM_SIDECAR_JSON_REPORT = "quantum-sidecar-validation.json"
QUANTUM_SIDECAR_MARKDOWN_REPORT = "quantum-sidecar-validation.md"
QUANTUM_SIDECAR_BUNDLE = "quantum-sidecar-evidence.zip"
QUANTUM_SIDECAR_MANIFEST = "manifest.sha256.json"
DEFAULT_SHOTS = 4096
MAX_SHOTS = 100_000
DEFAULT_EXACT_TOLERANCE = 1e-10
DEFAULT_SINGLE_QUBIT_ERROR = 0.001
DEFAULT_TWO_QUBIT_ERROR = 0.01

CLAIM_BOUNDARY = (
    "Simulator-only quantum-readiness validation of one small, linear, phase-only "
    "Fractal SSFM Strang step. It is not QPU execution, quantum advantage, nonlinear "
    "Schrodinger-Poisson simulation, peer-reviewed physical validation, or validation "
    "of hard/soft mask geometry modes."
)


def _require_quantum_stack() -> dict[str, Any]:
    try:
        from qiskit import QuantumCircuit, qasm3, qpy, transpile
        from qiskit.circuit.library import DiagonalGate, QFTGate
        from qiskit.quantum_info import Statevector
        from qiskit_aer import AerSimulator
        from qiskit_aer.noise import NoiseModel, depolarizing_error
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Fractal SSFM quantum sidecar requires the optional quantum stack. "
            "Install it with: python -m pip install 'qs-dmss[quantum]'"
        ) from exc

    return {
        "QuantumCircuit": QuantumCircuit,
        "qasm3": qasm3,
        "qpy": qpy,
        "transpile": transpile,
        "DiagonalGate": DiagonalGate,
        "QFTGate": QFTGate,
        "Statevector": Statevector,
        "AerSimulator": AerSimulator,
        "NoiseModel": NoiseModel,
        "depolarizing_error": depolarizing_error,
    }


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _validate_profile(config: SimulationConfig) -> None:
    if config.engine.backend != "numpy_fractal_ssfm":
        raise ValueError("Quantum sidecar profile requires backend: numpy_fractal_ssfm")
    if config.engine.grid_shape != (4, 4, 1):
        raise ValueError("Quantum sidecar profile is fixed to grid_shape: [4, 4, 1]")
    if config.engine.g_int != 0.0:
        raise ValueError("Quantum sidecar profile requires engine.g_int: 0.0")
    if config.engine.num_steps != 1:
        raise ValueError("Quantum sidecar profile validates exactly one Strang step")
    if config.geometry is None or config.geometry.mode != "fuzzy_potential":
        raise ValueError("Quantum sidecar profile requires geometry.mode: fuzzy_potential")
    if config.spectral is None or config.spectral.dealias_fraction is not None:
        raise ValueError("Quantum sidecar profile requires spectral.dealias_fraction: null")
    if config.initial.random_phase:
        raise ValueError("Quantum sidecar profile requires initial.random_phase: false")


def _normalized_state(state: np.ndarray) -> np.ndarray:
    flattened = np.asarray(state, dtype=np.complex128).reshape(-1)
    norm = np.linalg.norm(flattened)
    if norm == 0.0:
        raise ValueError("Quantum sidecar cannot encode a zero-norm initial state")
    return flattened / norm


def _aligned_state_error(
    candidate: np.ndarray,
    reference: np.ndarray,
) -> tuple[np.ndarray, float]:
    overlap = np.vdot(reference, candidate)
    aligned = candidate
    if abs(overlap) > 0.0:
        aligned = candidate * np.exp(-1j * np.angle(overlap))
    return aligned, float(np.linalg.norm(aligned - reference))


def _counts_to_probabilities(counts: dict[str, int], dimension: int) -> np.ndarray:
    total = sum(counts.values())
    if total <= 0:
        raise ValueError("Quantum simulator returned no measurement shots")
    probabilities = np.zeros(dimension, dtype=np.float64)
    for bitstring, count in counts.items():
        state_index = int(bitstring.replace(" ", ""), 2)
        probabilities[state_index] += count / total
    return probabilities


def _total_variation(candidate: np.ndarray, reference: np.ndarray) -> float:
    return float(0.5 * np.sum(np.abs(candidate - reference)))


def _package_version(package_name: str) -> str | None:
    try:
        return metadata.version(package_name)
    except metadata.PackageNotFoundError:
        return None


def _build_evolution_circuit(
    solver: FractalQuadrantSSFMSolver,
    stack: dict[str, Any],
):
    QuantumCircuit = stack["QuantumCircuit"]
    DiagonalGate = stack["DiagonalGate"]
    QFTGate = stack["QFTGate"]

    nx = solver.nx
    ny = solver.ny
    x_qubits = int(math.log2(nx))
    y_qubits = int(math.log2(ny))
    if 2**x_qubits != nx or 2**y_qubits != ny:
        raise ValueError("Quantum sidecar grid axes must be powers of two")

    circuit = QuantumCircuit(x_qubits + y_qubits, name="fractal_fuzzy_strang")
    axis_wires = (
        list(range(y_qubits)),
        list(range(y_qubits, y_qubits + x_qubits)),
    )
    qft_y = QFTGate(y_qubits)
    qft_x = QFTGate(x_qubits)
    qft_gates = (qft_y, qft_x)
    kinetic_phase = np.asarray(solver.linear_half_phase).reshape(-1)
    potential_phase = np.exp(
        -1j * solver.time_step * np.asarray(solver.fields.potential)
    ).reshape(-1)

    for wires, gate in zip(axis_wires, qft_gates, strict=True):
        circuit.append(gate, wires)
    circuit.append(DiagonalGate(kinetic_phase), circuit.qubits)
    for wires, gate in zip(axis_wires, qft_gates, strict=True):
        circuit.append(gate.inverse(), wires)

    circuit.append(DiagonalGate(potential_phase), circuit.qubits)

    for wires, gate in zip(axis_wires, qft_gates, strict=True):
        circuit.append(gate, wires)
    circuit.append(DiagonalGate(kinetic_phase), circuit.qubits)
    for wires, gate in zip(axis_wires, qft_gates, strict=True):
        circuit.append(gate.inverse(), wires)

    circuit.metadata = {
        "profile_id": QUANTUM_SIDECAR_PROFILE_ID,
        "construction": "2d-qft-diagonal-phase-strang-step",
        "submitted": False,
    }
    return circuit


def _measurement_circuit(evolution_circuit, initial_state: np.ndarray, stack: dict[str, Any]):
    QuantumCircuit = stack["QuantumCircuit"]
    qubits = evolution_circuit.num_qubits
    circuit = QuantumCircuit(qubits, qubits, name="fractal_fuzzy_measurement")
    circuit.initialize(initial_state, range(qubits))
    circuit.compose(evolution_circuit, inplace=True)
    circuit.measure(range(qubits), range(qubits))
    return circuit


def _run_sampling(
    measurement_circuit,
    *,
    shots: int,
    seed: int,
    stack: dict[str, Any],
) -> dict[str, Any]:
    AerSimulator = stack["AerSimulator"]
    transpile = stack["transpile"]

    ideal_backend = AerSimulator()
    ideal_circuit = transpile(
        measurement_circuit,
        ideal_backend,
        optimization_level=1,
        seed_transpiler=seed,
    )
    ideal_counts = ideal_backend.run(
        ideal_circuit,
        shots=shots,
        seed_simulator=seed,
    ).result().get_counts()

    NoiseModel = stack["NoiseModel"]
    depolarizing_error = stack["depolarizing_error"]
    noise_model = NoiseModel()
    noise_model.add_all_qubit_quantum_error(
        depolarizing_error(DEFAULT_SINGLE_QUBIT_ERROR, 1),
        ["u"],
    )
    noise_model.add_all_qubit_quantum_error(
        depolarizing_error(DEFAULT_TWO_QUBIT_ERROR, 2),
        ["cx"],
    )
    noisy_circuit = transpile(
        measurement_circuit,
        basis_gates=noise_model.basis_gates,
        optimization_level=1,
        seed_transpiler=seed,
    )
    noisy_backend = AerSimulator(noise_model=noise_model)
    noisy_counts = noisy_backend.run(
        noisy_circuit,
        shots=shots,
        seed_simulator=seed,
    ).result().get_counts()

    return {
        "ideal_counts": dict(sorted(ideal_counts.items())),
        "noisy_counts": dict(sorted(noisy_counts.items())),
        "ideal_circuit": ideal_circuit,
        "noisy_circuit": noisy_circuit,
        "noise_model": {
            "kind": "synthetic_depolarizing",
            "single_qubit_error": DEFAULT_SINGLE_QUBIT_ERROR,
            "two_qubit_error": DEFAULT_TWO_QUBIT_ERROR,
            "physical_calibration": False,
        },
    }


def _resource_metrics(circuit, stack: dict[str, Any], *, seed: int) -> tuple[Any, dict[str, Any]]:
    transpile = stack["transpile"]
    transpiled = transpile(
        circuit,
        basis_gates=["u", "cx"],
        optimization_level=1,
        seed_transpiler=seed,
    )
    operations = {str(name): int(count) for name, count in transpiled.count_ops().items()}
    return transpiled, {
        "qubits": int(transpiled.num_qubits),
        "depth": int(transpiled.depth()),
        "size": int(transpiled.size()),
        "operations": operations,
        "two_qubit_gates": int(operations.get("cx", 0)),
        "basis_gates": ["u", "cx"],
        "optimization_level": 1,
        "seed_transpiler": seed,
    }


def _write_markdown(report: dict[str, Any], path: Path) -> None:
    exact = report["metrics"]["exact_statevector"]
    sampling = report["metrics"]["sampling"]
    resources = report["metrics"]["resources"]
    status = "PASS" if report["success"] else "FAIL"
    lines = [
        "# QS-DMSS Fractal SSFM Quantum-Readiness Sidecar",
        "",
        f"Overall status: **{status}**",
        f"Profile: `{report['profile_id']}`",
        f"Generated at: `{report['generated_at']}`",
        "",
        "This local sidecar compares one 4x4, linear, phase-only fuzzy-potential",
        "Fractal SSFM Strang step against an exact Qiskit statevector and deterministic",
        "Aer sampling. The synthetic noise run is diagnostic only.",
        "",
        "## Exact Encoding Agreement",
        "",
        f"- Global-phase-aligned state L2 error: `{exact['state_l2_error']:.6e}`",
        f"- Density mean absolute error: `{exact['density_mae']:.6e}`",
        f"- Quantum state norm error: `{exact['norm_error']:.6e}`",
        "",
        "## Sampling Diagnostics",
        "",
        f"- Shots: `{sampling['shots']}`",
        f"- Ideal total-variation distance: `{sampling['ideal_total_variation']:.6e}`",
        f"- Synthetic-noise total-variation distance: `{sampling['noisy_total_variation']:.6e}`",
        f"- Conservative 95% binomial half-width: `{sampling['max_95pct_binomial_half_width']:.6e}`",
        "",
        "## Circuit Resources",
        "",
        f"- Qubits: `{resources['qubits']}`",
        f"- Depth after basis decomposition: `{resources['depth']}`",
        f"- Two-qubit gates: `{resources['two_qubit_gates']}`",
        f"- Operations: `{json.dumps(resources['operations'], sort_keys=True)}`",
        "",
        "## Checks",
        "",
        "| Check | Status | Detail |",
        "| --- | --- | --- |",
    ]
    for check in report["checks"]:
        check_status = "PASS" if check["success"] else "FAIL"
        detail = str(check["detail"]).replace("|", "\\|").replace("\n", " ")
        lines.append(f"| {check['name']} | {check_status} | {detail} |")
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            report["claim_boundary"],
            "",
            "No cloud account, QPU, provider credential, or remote submission was used.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def verify_quantum_sidecar_directory(path: str | Path) -> dict[str, Any]:
    root = Path(path).resolve()
    manifest_path = root / QUANTUM_SIDECAR_MANIFEST
    if not manifest_path.exists():
        return {"success": False, "checked_files": 0, "errors": ["Missing manifest"]}

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    errors: list[str] = []
    checked_files = 0
    for entry in manifest.get("files", []):
        try:
            file_path = contained_path(root, entry["path"])
        except ValueError:
            errors.append(f"Manifest path escapes output root: {entry['path']}")
            continue
        if not file_path.is_file():
            errors.append(f"Missing file: {entry['path']}")
            continue
        if _sha256(file_path) != entry["sha256"]:
            errors.append(f"Hash mismatch: {entry['path']}")
        if file_path.stat().st_size != entry["size_bytes"]:
            errors.append(f"Size mismatch: {entry['path']}")
        checked_files += 1
    return {
        "success": not errors,
        "checked_files": checked_files,
        "errors": errors,
    }


def validate_fractal_quantum_sidecar(
    *,
    output_root: str | Path | None = None,
    shots: int = DEFAULT_SHOTS,
    seed: int = 7,
    exact_tolerance: float = DEFAULT_EXACT_TOLERANCE,
) -> dict[str, Any]:
    if (
        isinstance(shots, bool)
        or not isinstance(shots, int)
        or not 128 <= shots <= MAX_SHOTS
    ):
        raise ValueError(f"shots must be an integer between 128 and {MAX_SHOTS}")
    if isinstance(seed, bool) or not isinstance(seed, int) or seed < 0:
        raise ValueError("seed must be a non-negative integer")
    if exact_tolerance <= 0.0:
        raise ValueError("exact_tolerance must be greater than zero")

    stack = _require_quantum_stack()
    config = load_config(quantum_sidecar_config_path())
    _validate_profile(config)
    output_path = (
        Path(output_root).resolve()
        if output_root is not None
        else (Path.cwd() / "quantum-sidecar-validation").resolve()
    )
    artifacts_dir = contained_path(output_path, "artifacts")
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    profile_path = contained_path(output_path, "profile.yaml")
    write_config(config, profile_path)
    solver = FractalQuadrantSSFMSolver(
        engine=config.engine,
        initial=config.initial,
        seed=config.run.seed,
        geometry=config.geometry,
        spectral=config.spectral,
    )
    initial_grid = solver.initialize_wavefunction()
    initial_state = _normalized_state(initial_grid)
    reference_state = _normalized_state(solver.step(initial_grid))
    evolution_circuit = _build_evolution_circuit(solver, stack)
    quantum_state = np.asarray(
        stack["Statevector"](initial_state).evolve(evolution_circuit).data,
        dtype=np.complex128,
    )
    aligned_state, state_l2_error = _aligned_state_error(
        quantum_state,
        reference_state,
    )
    reference_density = np.abs(reference_state) ** 2
    quantum_density = np.abs(aligned_state) ** 2
    density_mae = float(np.mean(np.abs(quantum_density - reference_density)))
    norm_error = abs(float(np.vdot(quantum_state, quantum_state).real) - 1.0)

    measurement_circuit = _measurement_circuit(
        evolution_circuit,
        initial_state,
        stack,
    )
    sampling_run = _run_sampling(
        measurement_circuit,
        shots=shots,
        seed=seed,
        stack=stack,
    )
    ideal_probabilities = _counts_to_probabilities(
        sampling_run["ideal_counts"],
        reference_density.size,
    )
    noisy_probabilities = _counts_to_probabilities(
        sampling_run["noisy_counts"],
        reference_density.size,
    )
    resource_circuit, resources = _resource_metrics(
        evolution_circuit,
        stack,
        seed=seed,
    )

    exact_metrics = {
        "state_l2_error": state_l2_error,
        "density_mae": density_mae,
        "norm_error": norm_error,
        "global_phase_aligned": True,
    }
    sampling_metrics = {
        "shots": shots,
        "seed_simulator": seed,
        "ideal_total_variation": _total_variation(
            ideal_probabilities,
            reference_density,
        ),
        "noisy_total_variation": _total_variation(
            noisy_probabilities,
            reference_density,
        ),
        "max_95pct_binomial_half_width": 1.96 * math.sqrt(0.25 / shots),
        "synthetic_noise_model": sampling_run["noise_model"],
        "acceptance_role": "diagnostic_only",
    }
    checks = [
        {
            "name": "profile:phase-only-fuzzy-potential",
            "success": config.geometry is not None
            and config.geometry.mode == "fuzzy_potential"
            and config.engine.g_int == 0.0
            and config.spectral is not None
            and config.spectral.dealias_fraction is None,
            "detail": "profile excludes nonlinear feedback, masks, and de-alias filtering",
        },
        {
            "name": "encoding:statevector-agreement",
            "success": state_l2_error <= exact_tolerance,
            "detail": f"L2 error {state_l2_error:.6e} <= {exact_tolerance:.6e}",
        },
        {
            "name": "encoding:density-agreement",
            "success": density_mae <= exact_tolerance,
            "detail": f"density MAE {density_mae:.6e} <= {exact_tolerance:.6e}",
        },
        {
            "name": "encoding:norm-conservation",
            "success": norm_error <= exact_tolerance,
            "detail": f"quantum state norm error {norm_error:.6e}",
        },
        {
            "name": "execution:simulator-only",
            "success": True,
            "detail": "local Statevector and Aer simulators; submitted=false",
        },
    ]
    success = all(check["success"] for check in checks)

    qasm_path = contained_path(artifacts_dir, "fractal-fuzzy-strang.openqasm")
    qasm_path.write_text(stack["qasm3"].dumps(resource_circuit), encoding="utf-8")
    qpy_path = contained_path(artifacts_dir, "fractal-fuzzy-strang.qpy")
    with qpy_path.open("wb") as handle:
        stack["qpy"].dump(evolution_circuit, handle)
    circuit_text_path = contained_path(artifacts_dir, "fractal-fuzzy-strang.txt")
    circuit_text_path.write_text(
        "\n".join(
            [
                "QS-DMSS Fractal SSFM quantum sidecar circuit",
                f"profile: {QUANTUM_SIDECAR_PROFILE_ID}",
                "construction: 2-D QFT -> kinetic phase -> inverse QFT",
                "              -> fuzzy-potential phase",
                "              -> 2-D QFT -> kinetic phase -> inverse QFT",
                f"qubits: {evolution_circuit.num_qubits}",
                f"high-level depth: {evolution_circuit.depth()}",
                f"high-level operations: {json.dumps(dict(evolution_circuit.count_ops()), sort_keys=True)}",
                "submitted: false",
                "",
            ]
        ),
        encoding="utf-8",
    )
    states_path = contained_path(artifacts_dir, "state-comparison.npz")
    np.savez(
        states_path,
        initial_state=initial_state,
        classical_reference=reference_state,
        quantum_state=quantum_state,
        aligned_quantum_state=aligned_state,
        classical_density=reference_density,
        quantum_density=quantum_density,
        ideal_sample_density=ideal_probabilities,
        noisy_sample_density=noisy_probabilities,
    )
    counts_path = contained_path(artifacts_dir, "measurement-counts.json")
    _write_json(
        counts_path,
        {
            "schema_version": 1,
            "shots": shots,
            "seed_simulator": seed,
            "ideal_counts": sampling_run["ideal_counts"],
            "noisy_counts": sampling_run["noisy_counts"],
            "noise_model": sampling_run["noise_model"],
        },
    )
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

    report = {
        "schema_version": QUANTUM_SIDECAR_SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "profile_id": QUANTUM_SIDECAR_PROFILE_ID,
        "success": success,
        "claim_boundary": CLAIM_BOUNDARY,
        "submission_policy": {
            "submitted": False,
            "qpu_used": False,
            "credentials_required": False,
            "provider": None,
        },
        "profile": {
            "config_digest": config_digest(config),
            "initial_seed": config.run.seed,
            "grid_shape": list(config.engine.grid_shape),
            "qubits": evolution_circuit.num_qubits,
            "geometry_mode": config.geometry.mode if config.geometry else None,
            "g_int": config.engine.g_int,
            "dealias_fraction": (
                config.spectral.dealias_fraction if config.spectral else None
            ),
            "time_step": config.engine.time_step,
            "num_steps": config.engine.num_steps,
        },
        "metrics": {
            "exact_statevector": exact_metrics,
            "sampling": sampling_metrics,
            "resources": resources,
        },
        "checks": checks,
        "artifacts": {
            "profile": profile_path.relative_to(output_path).as_posix(),
            "environment": environment_path.relative_to(output_path).as_posix(),
            "openqasm3": qasm_path.relative_to(output_path).as_posix(),
            "qiskit_qpy": qpy_path.relative_to(output_path).as_posix(),
            "circuit_text": circuit_text_path.relative_to(output_path).as_posix(),
            "state_comparison": states_path.relative_to(output_path).as_posix(),
            "measurement_counts": counts_path.relative_to(output_path).as_posix(),
        },
    }
    report_path = contained_path(output_path, QUANTUM_SIDECAR_JSON_REPORT)
    markdown_path = contained_path(output_path, QUANTUM_SIDECAR_MARKDOWN_REPORT)
    _write_json(report_path, report)
    _write_markdown(report, markdown_path)
    manifest_path = write_manifest_for_directory(
        output_path,
        manifest_name=QUANTUM_SIDECAR_MANIFEST,
        bundle_name=QUANTUM_SIDECAR_BUNDLE,
    )
    bundle_path = create_bundle_zip_for_directory(
        output_path,
        bundle_name=QUANTUM_SIDECAR_BUNDLE,
    )
    verification = verify_quantum_sidecar_directory(output_path)
    return {
        **report,
        "success": success and verification["success"],
        "report_path": str(report_path),
        "markdown_report_path": str(markdown_path),
        "manifest_path": str(manifest_path),
        "evidence_bundle_path": str(bundle_path),
        "evidence_verification": verification,
    }
