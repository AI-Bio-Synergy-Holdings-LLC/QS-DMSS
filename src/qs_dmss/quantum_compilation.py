from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

from qs_dmss.evidence.bundle import (
    create_bundle_zip_for_directory,
    write_manifest_for_directory,
)
from qs_dmss.paths import contained_path
from qs_dmss.quantum_request import prepare_fractal_qpu_request
from qs_dmss.quantum_sidecar import (
    DEFAULT_EXACT_TOLERANCE,
    DEFAULT_SHOTS,
    verify_quantum_sidecar_directory,
)


COMPILATION_SCHEMA_VERSION = 1
COMPILATION_JSON_REPORT = "quantum-compilation-validation.json"
COMPILATION_MARKDOWN_REPORT = "quantum-compilation-validation.md"
COMPILATION_CSV = "quantum-compilation-matrix.csv"
COMPILATION_MANIFEST = "manifest.sha256.json"
COMPILATION_BUNDLE = "quantum-compilation-evidence.zip"
OPTIMIZATION_LEVELS = (0, 1, 2, 3)
BASIS_GATES = ["rz", "sx", "x", "cx"]
DEFAULT_COMPILATION_TOLERANCE = 1e-6


def _bidirectional_edges(edges: list[tuple[int, int]]) -> list[list[int]]:
    return [[source, target] for edge in edges for source, target in (edge, edge[::-1])]


TOPOLOGY_PROFILES = (
    {
        "profile_id": "generic-linear-5q",
        "label": "Linear five-qubit chain",
        "num_qubits": 5,
        "coupling_map": _bidirectional_edges([(0, 1), (1, 2), (2, 3), (3, 4)]),
    },
    {
        "profile_id": "generic-ring-5q",
        "label": "Five-qubit ring",
        "num_qubits": 5,
        "coupling_map": _bidirectional_edges(
            [(0, 1), (1, 2), (2, 3), (3, 4), (4, 0)]
        ),
    },
    {
        "profile_id": "generic-all-to-all-5q",
        "label": "Fully connected five-qubit target",
        "num_qubits": 5,
        "coupling_map": [
            [source, target]
            for source in range(5)
            for target in range(5)
            if source != target
        ],
    },
)

CLAIM_BOUNDARY = (
    "Local, ideal-simulator validation of logical-to-target circuit semantics and "
    "resource attribution across fixed generic topologies. It is not physical "
    "hardware validation, calibrated-noise analysis, provider selection, QPU "
    "execution, cost prediction, quantum advantage, or scientific validation of "
    "the underlying Fractal SSFM model."
)


def _require_compilation_stack() -> dict[str, Any]:
    try:
        from qiskit import QuantumCircuit, qasm3, qpy, transpile
        from qiskit.providers.fake_provider import GenericBackendV2
        from qiskit_aer import AerSimulator
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Quantum compilation validation requires the optional quantum stack. "
            "Install it with: python -m pip install 'qs-dmss[quantum]'"
        ) from exc
    return {
        "QuantumCircuit": QuantumCircuit,
        "GenericBackendV2": GenericBackendV2,
        "AerSimulator": AerSimulator,
        "qasm3": qasm3,
        "qpy": qpy,
        "transpile": transpile,
    }


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _operation_counts(circuit) -> dict[str, int]:
    return {str(name): int(count) for name, count in circuit.count_ops().items()}


def _resource_metrics(circuit) -> dict[str, Any]:
    operations = _operation_counts(circuit)
    return {
        "qubits": int(circuit.num_qubits),
        "depth": int(circuit.depth()),
        "size": int(circuit.size()),
        "two_qubit_gates": int(operations.get("cx", 0)),
        "operations": operations,
    }


def _measurement_map(circuit) -> list[tuple[int, int]]:
    mapping: list[tuple[int, int]] = []
    for instruction in circuit.data:
        if instruction.operation.name != "measure":
            continue
        physical = circuit.find_bit(instruction.qubits[0]).index
        classical = circuit.find_bit(instruction.clbits[0]).index
        mapping.append((physical, classical))
    if not mapping:
        raise ValueError("Transpiled target circuit has no final measurements")
    return mapping


def _recover_logical_state(
    target_circuit,
    *,
    stack: dict[str, Any],
) -> tuple[np.ndarray, float, list[tuple[int, int]]]:
    mapping = _measurement_map(target_circuit)
    simulation_circuit = target_circuit.remove_final_measurements(inplace=False)
    simulation_circuit.save_statevector()
    backend = stack["AerSimulator"](method="statevector")
    result = backend.run(simulation_circuit).result()
    physical_state = np.asarray(
        result.get_statevector(simulation_circuit),
        dtype=np.complex128,
    )

    logical_state = np.zeros(2 ** len(mapping), dtype=np.complex128)
    measured_qubits = {physical for physical, _ in mapping}
    ancilla_leakage = 0.0
    for physical_index, amplitude in enumerate(physical_state):
        logical_index = sum(
            ((physical_index >> physical) & 1) << classical
            for physical, classical in mapping
        )
        has_unused_qubit = any(
            (physical_index >> physical) & 1
            for physical in range(target_circuit.num_qubits)
            if physical not in measured_qubits
        )
        if has_unused_qubit:
            ancilla_leakage += float(abs(amplitude) ** 2)
        else:
            logical_state[logical_index] = amplitude
    return logical_state, ancilla_leakage, mapping


def _semantic_metrics(
    target_circuit,
    reference_state: np.ndarray,
    *,
    stack: dict[str, Any],
) -> dict[str, Any]:
    logical_state, ancilla_leakage, mapping = _recover_logical_state(
        target_circuit,
        stack=stack,
    )
    overlap = np.vdot(reference_state, logical_state)
    aligned = logical_state
    if abs(overlap) > 0.0:
        aligned = logical_state * np.exp(-1j * np.angle(overlap))
    state_l2_error = float(np.linalg.norm(aligned - reference_state))
    fidelity = min(1.0, max(0.0, float(abs(overlap) ** 2)))
    density_tvd = float(
        0.5
        * np.sum(
            np.abs(np.abs(logical_state) ** 2 - np.abs(reference_state) ** 2)
        )
    )
    return {
        "state_l2_error": state_l2_error,
        "state_fidelity": fidelity,
        "density_total_variation": density_tvd,
        "unused_qubit_leakage": ancilla_leakage,
        "global_phase_aligned": True,
        "measurement_map": [
            {"physical_qubit": physical, "classical_bit": classical}
            for physical, classical in mapping
        ],
    }


def _build_components(
    logical_circuit,
    evolution_circuit,
    initial_state: np.ndarray,
    *,
    stack: dict[str, Any],
) -> dict[str, Any]:
    qubits = evolution_circuit.num_qubits
    state_preparation = stack["QuantumCircuit"](qubits, name="state_preparation")
    state_preparation.initialize(initial_state, range(qubits))
    measurement = stack["QuantumCircuit"](qubits, qubits, name="measurement")
    measurement.measure(range(qubits), range(qubits))
    return {
        "state_preparation": state_preparation,
        "ssfm_evolution": evolution_circuit,
        "measurement": measurement,
        "full_experiment": logical_circuit,
    }


def _transpile_components(
    components: dict[str, Any],
    *,
    backend,
    optimization_level: int,
    seed: int,
    stack: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    return {
        name: _resource_metrics(
            stack["transpile"](
                circuit,
                backend=backend,
                optimization_level=optimization_level,
                seed_transpiler=seed,
            )
        )
        for name, circuit in components.items()
    }


def _mark_routing_overhead(rows: list[dict[str, Any]]) -> None:
    baselines = {
        row["optimization_level"]: row
        for row in rows
        if row["topology_id"] == "generic-all-to-all-5q"
    }
    for row in rows:
        baseline = baselines[row["optimization_level"]]
        row["routing_overhead"] = {
            "depth_above_all_to_all": row["resources"]["depth"]
            - baseline["resources"]["depth"],
            "cx_above_all_to_all": row["resources"]["two_qubit_gates"]
            - baseline["resources"]["two_qubit_gates"],
        }


def _mark_pareto_rows(rows: list[dict[str, Any]]) -> None:
    passing = [row for row in rows if row["success"]]
    for row in rows:
        depth = row["resources"]["depth"]
        cx_count = row["resources"]["two_qubit_gates"]
        semantic_rank = row["semantics"]["acceptance_rank"]
        row["pareto_optimal"] = row["success"] and not any(
            other is not row
            and other["resources"]["depth"] <= depth
            and other["resources"]["two_qubit_gates"] <= cx_count
            and other["semantics"]["acceptance_rank"] <= semantic_rank
            and (
                other["resources"]["depth"] < depth
                or other["resources"]["two_qubit_gates"] < cx_count
                or other["semantics"]["acceptance_rank"] < semantic_rank
            )
            for other in passing
        )


def _recommended_row(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    candidates = [row for row in rows if row["success"] and row["pareto_optimal"]]
    if not candidates:
        return None
    selected = min(
        candidates,
        key=lambda row: (
            row["resources"]["two_qubit_gates"],
            row["resources"]["depth"],
            row["resources"]["size"],
            row["topology_id"],
            row["optimization_level"],
        ),
    )
    return {
        "topology_id": selected["topology_id"],
        "optimization_level": selected["optimization_level"],
        "depth": selected["resources"]["depth"],
        "two_qubit_gates": selected["resources"]["two_qubit_gates"],
        "state_l2_error": selected["semantics"]["state_l2_error"],
        "acceptance_class": selected["semantics"]["acceptance_class"],
        "attribution": selected["attribution"],
        "selection_rule": "minimum CX count, then depth and circuit size, among tolerance-passing Pareto rows",
    }


def _write_matrix_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "topology_id",
                "optimization_level",
                "success",
                "pareto_optimal",
                "depth",
                "size",
                "cx_count",
                "acceptance_class",
                "state_l2_error",
                "state_fidelity",
                "density_tvd",
                "unused_qubit_leakage",
                "routing_depth_overhead",
                "routing_cx_overhead",
            ]
        )
        for row in rows:
            writer.writerow(
                [
                    row["topology_id"],
                    row["optimization_level"],
                    row["success"],
                    row["pareto_optimal"],
                    row["resources"]["depth"],
                    row["resources"]["size"],
                    row["resources"]["two_qubit_gates"],
                    row["semantics"]["acceptance_class"],
                    row["semantics"]["state_l2_error"],
                    row["semantics"]["state_fidelity"],
                    row["semantics"]["density_total_variation"],
                    row["semantics"]["unused_qubit_leakage"],
                    row["routing_overhead"]["depth_above_all_to_all"],
                    row["routing_overhead"]["cx_above_all_to_all"],
                ]
            )


def _write_markdown(path: Path, report: dict[str, Any]) -> None:
    recommended = report["recommended_configuration"]
    lines = [
        "# QS-DMSS Quantum Compilation Validation",
        "",
        f"Overall status: **{'PASS' if report['success'] else 'FAIL'}**",
        f"Generated at: `{report['generated_at']}`",
        "",
        "The matrix validates exact logical-output preservation and attributes",
        "resource growth across state preparation, SSFM evolution, routing, and",
        "measurement for generic local targets only.",
        "",
        "## Matrix",
        "",
        "| Topology | Opt | Class | Pass | Pareto | Depth | CX | State L2 | Fidelity | TVD | Leakage |",
        "| --- | ---: | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in report["matrix"]:
        semantics = row["semantics"]
        lines.append(
            f"| {row['topology_id']} | {row['optimization_level']} | "
            f"{semantics['acceptance_class']} | "
            f"{'PASS' if row['success'] else 'FAIL'} | "
            f"{'yes' if row['pareto_optimal'] else 'no'} | "
            f"{row['resources']['depth']} | {row['resources']['two_qubit_gates']} | "
            f"{semantics['state_l2_error']:.3e} | {semantics['state_fidelity']:.12f} | "
            f"{semantics['density_total_variation']:.3e} | "
            f"{semantics['unused_qubit_leakage']:.3e} |"
        )
    lines.extend(["", "## Recommended Generic Configuration", ""])
    if recommended is None:
        lines.append("No matrix row passed the semantic acceptance gate.")
    else:
        lines.extend(
            [
                f"- Topology: `{recommended['topology_id']}`",
                f"- Optimization level: `{recommended['optimization_level']}`",
                f"- Depth: `{recommended['depth']}`",
                f"- CX gates: `{recommended['two_qubit_gates']}`",
                f"- State L2 error: `{recommended['state_l2_error']:.6e}`",
                f"- Acceptance class: `{recommended['acceptance_class']}`",
                f"- Rule: {recommended['selection_rule']}",
            ]
        )
        lines.extend(
            [
                "",
                "### Resource Attribution",
                "",
                "| Component | Depth | CX | Size |",
                "| --- | ---: | ---: | ---: |",
            ]
        )
        for name, resources in recommended["attribution"].items():
            lines.append(
                f"| {name} | {resources['depth']} | "
                f"{resources['two_qubit_gates']} | {resources['size']} |"
            )
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            report["claim_boundary"],
            "",
            "No provider, credential, remote API, QPU, or authorized spend was used.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def validate_fractal_quantum_compilation(
    *,
    output_root: str | Path | None = None,
    shots: int = DEFAULT_SHOTS,
    seed: int = 7,
    reference_tolerance: float = DEFAULT_EXACT_TOLERANCE,
    compilation_tolerance: float = DEFAULT_COMPILATION_TOLERANCE,
) -> dict[str, Any]:
    if isinstance(shots, bool) or not isinstance(shots, int) or not 128 <= shots <= 100_000:
        raise ValueError("shots must be an integer between 128 and 100000")
    if isinstance(seed, bool) or not isinstance(seed, int) or seed < 0:
        raise ValueError("seed must be a non-negative integer")
    if reference_tolerance <= 0.0:
        raise ValueError("reference_tolerance must be greater than zero")
    if compilation_tolerance <= 0.0:
        raise ValueError("compilation_tolerance must be greater than zero")

    output_path = (
        Path(output_root).resolve()
        if output_root is not None
        else (Path.cwd() / "quantum-compilation-validation").resolve()
    )
    if output_path.exists():
        if not output_path.is_dir() or any(output_path.iterdir()):
            raise ValueError(
                f"Quantum compilation output directory must be empty: {output_path}"
            )
    output_path.mkdir(parents=True, exist_ok=True)
    stack = _require_compilation_stack()

    baseline_dir = contained_path(output_path, "baseline-request")
    baseline = prepare_fractal_qpu_request(
        output_root=baseline_dir,
        shots=shots,
        seed=seed,
        optimization_level=1,
        exact_tolerance=reference_tolerance,
    )
    if not baseline["success"]:
        raise RuntimeError("Baseline provider-neutral QPU request did not pass")

    with contained_path(
        baseline_dir,
        "artifacts/fractal-fuzzy-logical.qpy",
    ).open("rb") as handle:
        logical_circuit = stack["qpy"].load(handle)[0]
    reference_dir = contained_path(baseline_dir, "reference-validation")
    with contained_path(
        reference_dir,
        "artifacts/fractal-fuzzy-strang.qpy",
    ).open("rb") as handle:
        evolution_circuit = stack["qpy"].load(handle)[0]
    with np.load(
        contained_path(reference_dir, "artifacts/state-comparison.npz")
    ) as states:
        initial_state = np.asarray(states["initial_state"], dtype=np.complex128)
        reference_state = np.asarray(
            states["classical_reference"],
            dtype=np.complex128,
        )
    components = _build_components(
        logical_circuit,
        evolution_circuit,
        initial_state,
        stack=stack,
    )

    circuits_dir = contained_path(output_path, "circuits")
    circuits_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    for topology in TOPOLOGY_PROFILES:
        for optimization_level in OPTIMIZATION_LEVELS:
            backend = stack["GenericBackendV2"](
                num_qubits=topology["num_qubits"],
                coupling_map=topology["coupling_map"],
                basis_gates=BASIS_GATES,
                noise_info=False,
                seed=seed,
            )
            target_circuit = stack["transpile"](
                logical_circuit,
                backend=backend,
                optimization_level=optimization_level,
                seed_transpiler=seed,
            )
            semantics = _semantic_metrics(
                target_circuit,
                reference_state,
                stack=stack,
            )
            is_reference_exact = (
                semantics["state_l2_error"] <= reference_tolerance
                and 1.0 - semantics["state_fidelity"] <= reference_tolerance
                and semantics["density_total_variation"] <= reference_tolerance
                and semantics["unused_qubit_leakage"] <= reference_tolerance
            )
            semantics["acceptance_class"] = (
                "reference_exact" if is_reference_exact else "bounded_approximation"
            )
            semantics["acceptance_rank"] = 0 if is_reference_exact else 1
            resources = _resource_metrics(target_circuit)
            attribution = _transpile_components(
                components,
                backend=backend,
                optimization_level=optimization_level,
                seed=seed,
                stack=stack,
            )
            stem = f"{topology['profile_id']}-opt{optimization_level}"
            qpy_path = contained_path(circuits_dir, f"{stem}.qpy")
            qasm_path = contained_path(circuits_dir, f"{stem}.openqasm")
            with qpy_path.open("wb") as handle:
                stack["qpy"].dump(target_circuit, handle)
            qasm_path.write_text(stack["qasm3"].dumps(target_circuit), encoding="utf-8")
            success = (
                semantics["state_l2_error"] <= compilation_tolerance
                and 1.0 - semantics["state_fidelity"] <= compilation_tolerance
                and semantics["density_total_variation"] <= compilation_tolerance
                and semantics["unused_qubit_leakage"] <= compilation_tolerance
            )
            rows.append(
                {
                    "topology_id": topology["profile_id"],
                    "topology_label": topology["label"],
                    "coupling_map": topology["coupling_map"],
                    "basis_gates": BASIS_GATES,
                    "optimization_level": optimization_level,
                    "success": success,
                    "semantics": semantics,
                    "resources": resources,
                    "attribution": attribution,
                    "artifacts": {
                        "qpy": qpy_path.relative_to(output_path).as_posix(),
                        "openqasm3": qasm_path.relative_to(output_path).as_posix(),
                    },
                }
            )

    _mark_routing_overhead(rows)
    _mark_pareto_rows(rows)
    recommended = _recommended_row(rows)
    report = {
        "schema_version": COMPILATION_SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "success": all(row["success"] for row in rows),
        "claim_boundary": CLAIM_BOUNDARY,
        "execution_policy": {
            "local_simulation_only": True,
            "submitted": False,
            "provider": None,
            "credentials_read": False,
            "remote_api_called": False,
            "max_authorized_cost_usd": 0.0,
        },
        "acceptance": {
            "reference_tolerance": reference_tolerance,
            "compilation_tolerance": compilation_tolerance,
            "required_checks": [
                "state_l2_error",
                "state_fidelity",
                "density_total_variation",
                "unused_qubit_leakage",
            ],
        },
        "matrix_definition": {
            "topologies": list(TOPOLOGY_PROFILES),
            "optimization_levels": list(OPTIMIZATION_LEVELS),
            "row_count": len(rows),
            "basis_gates": BASIS_GATES,
            "seed_transpiler": seed,
        },
        "matrix": rows,
        "recommended_configuration": recommended,
        "baseline_request": {
            "success": baseline["success"],
            "directory": baseline_dir.relative_to(output_path).as_posix(),
            "request": Path(baseline["request_path"])
            .relative_to(output_path)
            .as_posix(),
            "evidence_bundle": Path(baseline["evidence_bundle_path"])
            .relative_to(output_path)
            .as_posix(),
        },
    }
    report_path = contained_path(output_path, COMPILATION_JSON_REPORT)
    markdown_path = contained_path(output_path, COMPILATION_MARKDOWN_REPORT)
    csv_path = contained_path(output_path, COMPILATION_CSV)
    _write_json(report_path, report)
    _write_markdown(markdown_path, report)
    _write_matrix_csv(csv_path, rows)
    manifest_path = write_manifest_for_directory(
        output_path,
        manifest_name=COMPILATION_MANIFEST,
        bundle_name=COMPILATION_BUNDLE,
    )
    bundle_path = create_bundle_zip_for_directory(
        output_path,
        bundle_name=COMPILATION_BUNDLE,
    )
    verification = verify_quantum_sidecar_directory(output_path)
    return {
        **report,
        "success": report["success"] and verification["success"],
        "report_path": str(report_path),
        "markdown_report_path": str(markdown_path),
        "matrix_csv_path": str(csv_path),
        "manifest_path": str(manifest_path),
        "evidence_bundle_path": str(bundle_path),
        "evidence_verification": verification,
    }
