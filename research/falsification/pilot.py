"""Run a bounded prospective challenge; never declare scientific validation."""

import argparse
import hashlib
import importlib.metadata
import json
import platform
import sys
import zipfile
from datetime import datetime, timezone
from itertools import product
from pathlib import Path

import numpy as np
import reference

import qs_dmss
from qs_dmss.core.fractal_spectral import FractalGraphSpectralSolver
from qs_dmss.core.fractal_ssfm import FractalQuadrantSSFMSolver
from qs_dmss.core.solver import QuantumScalarDarkMatterSolver
from qs_dmss.io.config import EngineConfig, InitialConditionConfig
from qs_dmss.io.graph_config import FractalGraphConfig

HERE = Path(__file__).resolve().parent
SOURCE_COMMIT = "48d7ab5d10da189caddbcad1dd6622e58d204940"
PROTOCOL_COMMIT = "5fe19ed857a253caa0cb91ffc1a4d18904cc07e3"
PROTOCOL_CANONICAL_SHA256 = "fcecbf9ae403ad26ee8e28383ef90a5d15b7732a85af2d756ddeef03a748402b"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def scaled_error(actual, expected):
    return float(np.linalg.norm(np.asarray(actual) - expected) / max(1, np.linalg.norm(expected)))


def state_error(actual, expected, weights, initial):
    difference = np.sqrt(np.sum(weights * np.abs(actual - expected)**2, axis=-1))
    return float(np.max(difference) / np.sqrt(np.sum(weights * np.abs(initial)**2)))


def status(checks):
    return "NOT_FALSIFIED_WITHIN_SCOPE" if all(checks) else "FAIL"


def bounded(value, limit):
    return bool(np.isfinite(value) and 0 <= value <= limit)


def load_protocol(path):
    protocol = json.loads(path.read_text(encoding="utf-8"))
    canonical = json.dumps(protocol, sort_keys=True, separators=(",", ":")).encode()
    if hashlib.sha256(canonical).hexdigest() != PROTOCOL_CANONICAL_SHA256:
        raise ValueError("Protocol differs from preregistration; use a separately reviewed revision")
    return protocol


def graph_solver(level, boundary, length, *, mass=1.3, coupling=0, potential=(0, 0, 0, 0),
                 gamma=(1, 1, 1, 1), time_step=0.001):
    count = (3**(level + 1) + 3)//2 - (3 if boundary == "dirichlet" else 0)
    return FractalGraphSpectralSolver(
        EngineConfig("fractal_graph_spectral", (count, 1, 1), length, mass,
                     coupling, time_step, 32),
        InitialConditionConfig("uniform", random_phase=False), 0,
        FractalGraphConfig(level=level, boundary_condition=boundary,
                           quadrant_potential=tuple(potential), quadrant_gamma=tuple(gamma)))


def fft_exercise(protocol):
    p = protocol["fft"]
    rows = []
    for dimension, backend, solver_type in (
        (3, "numpy", QuantumScalarDarkMatterSolver),
        (2, "numpy_fractal_ssfm", FractalQuadrantSSFMSolver),
    ):
        for shape, length, mass, mode in product(p[f"shapes_{dimension}d"], p["lengths"],
                                                 p["masses"], p[f"modes_{dimension}d"]):
            shape = tuple(shape)
            engine_shape = shape if dimension == 3 else (*shape, 1)
            solver = solver_type(EngineConfig(backend, engine_shape, length, mass, 0, 0.001, 1),
                                 InitialConditionConfig("uniform", random_phase=False), 0)
            axes = np.meshgrid(*(np.arange(n)/n for n in shape), indexing="ij")
            psi = np.exp(2j*np.pi*sum(n*x for n, x in zip(mode, axes))) / length**(dimension/2)
            expected = sum((2*np.pi*n/length)**2 for n in mode)/(2*mass)
            actual = solver.compute_energy(psi, np.zeros(shape)) if dimension == 3 else solver.compute_energy(psi)
            error = scaled_error(actual, expected)
            norm_error = abs(solver.compute_norm(psi) - 1)
            legacy = actual / (length**dimension / np.prod(shape))
            control_rejected = not bounded(scaled_error(legacy, expected), p["scaled_energy_error_max"])
            rows.append({"backend": backend, "shape": shape, "length": length, "mass": mass,
                         "mode": mode, "expected_energy": expected, "actual_energy": actual,
                         "scaled_energy_error": error, "norm_error": norm_error,
                         "legacy_omission_rejected": control_rejected,
                         "status": status([bounded(error, p["scaled_energy_error_max"]),
                                           bounded(norm_error, p["norm_error_max"]), control_rejected])})
    return rows


def graph_exercise(protocol, arrays):
    p = protocol["graph"]
    rows = []
    for level, boundary, length in product(p["levels"], p["boundaries"], p["lengths"]):
        if level == 0 and boundary == "dirichlet":
            continue
        ref = reference.graph(level, boundary, length)
        solver = graph_solver(level, boundary, length)
        actual = solver.graph
        values, modes = reference.spectrum(ref)
        groups = reference.clusters(values, p["reference_cluster_relative_gap"])
        projectors = np.array([reference.projector(modes[:, g]) for g in groups])
        observed_projectors = np.array([reference.projector(solver.eigenvectors[:, g]) for g in groups])
        projector_error = max(scaled_error(a, b) for a, b in zip(observed_projectors, projectors))
        topology_ok = all(np.array_equal(a, b) for a, b in (
            (actual.full_lattice_coordinates, ref["vertices"]), (actual.full_edges, ref["edges"]),
            (actual.active_vertex_ids, ref["active"]), (actual.boundary_vertex_ids, ref["boundary"])))
        matrix_error = max(scaled_error(actual.stiffness, ref["stiffness"]),
                           scaled_error(actual.mass_weights, ref["mass"]))
        spectrum_error = scaled_error(solver.eigenvalues, values)
        nominal = int(p["tail_fraction"] * len(values))
        start = next(int(g[0]) for g in groups if nominal in g)
        tail_projector = reference.projector(modes[:, start:])
        psi = reference.initial_state(ref)
        weighted = np.sqrt(ref["mass"]) * psi
        tail = float(np.vdot(weighted, tail_projector @ weighted).real / np.vdot(weighted, weighted).real)
        tail_error = abs(solver.compute_spectral_tail_fraction(psi) - tail)
        checks = [topology_ok, bounded(matrix_error, p["scaled_matrix_error_max"]),
                  bounded(spectrum_error, p["scaled_spectrum_error_max"]),
                  bounded(projector_error, p["projector_error_max"]),
                  bounded(tail_error, p["tail_error_max"]), solver.tail_start == start]
        controls = {}
        if level > 0 and boundary == "neumann":
            uniform = np.full_like(ref["mass"], 1/len(ref["mass"]))
            controls["uniform_mass_rejected"] = not bounded(scaled_error(uniform, ref["mass"]),
                                                            p["scaled_matrix_error_max"])
        if boundary == "dirichlet":
            induced = ref["stiffness"] - np.diag(ref["stiffness"].sum(axis=1))
            controls["induced_laplacian_rejected"] = not bounded(scaled_error(induced, ref["stiffness"]),
                                                                p["scaled_matrix_error_max"])
        key = f"graph_{len(rows):02d}"
        for name in ("vertices", "edges", "active", "boundary", "mass", "stiffness"):
            arrays[f"{key}_reference_{name}"] = ref[name]
        arrays[f"{key}_candidate_stiffness"] = actual.stiffness
        arrays[f"{key}_candidate_mass"] = actual.mass_weights
        arrays[f"{key}_reference_spectrum"] = values
        arrays[f"{key}_candidate_spectrum"] = solver.eigenvalues
        arrays[f"{key}_reference_projectors"] = projectors
        arrays[f"{key}_candidate_projectors"] = observed_projectors
        rows.append({"artifact_prefix": key, "level": level, "boundary": boundary, "length": length,
                     "topology_matches": topology_ok, "matrix_error": matrix_error,
                     "spectrum_error": spectrum_error, "projector_error": projector_error,
                     "tail_error": tail_error, "reference_tail_start": start,
                     "candidate_tail_start": solver.tail_start, "negative_controls": controls,
                     "status": status(checks + list(controls.values()))})
    return rows


def evolution_exercise(protocol, arrays):
    p = protocol["evolution"]
    rows = []
    for boundary in p["boundaries"]:
        ref = reference.graph(p["level"], boundary, p["length"])
        potential, gamma = reference.fields(ref, p["quadrant_potential"], p["quadrant_gamma"], p["coupling"])
        initial = reference.initial_state(ref)
        solver = graph_solver(p["level"], boundary, p["length"], mass=p["mass"], coupling=p["coupling"],
                              potential=p["quadrant_potential"], gamma=p["quadrant_gamma"])
        times = np.linspace(0, p["total_time"], max(p["step_counts"]) + 1)
        references = [reference.trajectory(ref, initial, potential, gamma, p["mass"], times, rtol, atol)
                      for rtol, atol in zip(p["reference_rtol"], p["reference_atol"])]
        agreement = state_error(*references, ref["mass"], initial)
        linear = reference.linear_state(ref, initial, p["mass"], p["total_time"])
        candidate_linear = solver._apply_linear(initial, p["total_time"])
        linear_error = state_error(candidate_linear, linear, ref["mass"], initial)
        errors, norm_errors = [], []
        key = f"evolution_{boundary}"
        arrays[f"{key}_times"] = times
        arrays[f"{key}_reference"] = references[-1]
        arrays[f"{key}_reference_loose"] = references[0]
        arrays[f"{key}_reference_mass"] = ref["mass"]
        arrays[f"{key}_reference_stiffness"] = ref["stiffness"]
        arrays[f"{key}_potential"] = potential
        arrays[f"{key}_gamma"] = gamma
        arrays[f"{key}_linear_reference"] = linear
        arrays[f"{key}_linear_candidate"] = candidate_linear
        for count in p["step_counts"]:
            states = [initial]
            for _ in range(count):
                states.append(solver._step_with_dt(states[-1], p["total_time"]/count))
            states = np.array(states)
            arrays[f"{key}_candidate_{count}"] = states
            target = references[-1][::max(p["step_counts"])//count]
            errors.append(state_error(states, target, ref["mass"], initial))
            norm_errors.append(float(np.max(np.abs(np.sum(ref["mass"]*np.abs(states)**2, axis=1)-1))))
        resolved = min(errors) > max(p["resolution_floor"], p["reference_separation_factor"]*agreement)
        orders = [float(np.log2(a/b)) if a > 0 and b > 0 else None for a, b in zip(errors, errors[1:])]
        phase_error = state_error(references[-1]*np.exp(0.1j), references[-1], ref["mass"], initial)
        fields_error = max(scaled_error(solver.potential, potential), scaled_error(solver.gamma, gamma))
        checks = [bounded(linear_error, p["linear_error_max"]),
                  bounded(errors[-1], p["fine_trajectory_error_max"]),
                  bounded(max(norm_errors), p["norm_error_max"]),
                  bounded(fields_error, protocol["graph"]["scaled_matrix_error_max"]),
                  phase_error > p["fine_trajectory_error_max"]]
        result = status(checks)
        if result != "FAIL":
            if not resolved or not bounded(agreement, p["reference_agreement_max"]):
                result = "INCONCLUSIVE"
            else:
                result = status([o is not None and p["order_interval"][0] <= o <= p["order_interval"][1]
                                 for o in orders])
        rows.append({"artifact_prefix": key, "boundary": boundary, "reference_agreement": agreement,
                     "linear_error": linear_error, "fields_error": fields_error,
                     "step_counts": p["step_counts"], "trajectory_errors": errors,
                     "norm_errors": norm_errors, "observed_orders": orders, "refinement_resolved": resolved,
                     "phase_control_error": phase_error, "phase_control_rejected": checks[-1], "status": result})
    return rows


def run_exercises(protocol):
    arrays = {}
    exercises = {}
    for name, operation in (("fft", lambda: fft_exercise(protocol)),
                            ("graph", lambda: graph_exercise(protocol, arrays)),
                            ("evolution", lambda: evolution_exercise(protocol, arrays))):
        try:
            exercises[name] = operation()
        except (ValueError, RuntimeError, FloatingPointError, np.linalg.LinAlgError) as exc:
            exercises[name] = [{"status": "INCONCLUSIVE", "reason": f"{type(exc).__name__}: {exc}"}]
    states = [row["status"] for rows in exercises.values() for row in rows]
    overall = "FAIL" if "FAIL" in states else ("INCONCLUSIVE" if "INCONCLUSIVE" in states
                                               else "NOT_FALSIFIED_WITHIN_SCOPE")
    return {"status": overall, "exercises": exercises}, arrays


def verify_candidate(wheel, receipt):
    if receipt.get("source_commit") != SOURCE_COMMIT or receipt.get("wheel_sha256") != digest(wheel):
        raise ValueError("Candidate source pin or wheel hash does not match build receipt")
    if receipt.get("source_clean") is not True:
        raise ValueError("Candidate must originate from a clean source snapshot")
    package = Path(qs_dmss.__file__).resolve().parent
    with zipfile.ZipFile(wheel) as archive:
        names = [name for name in archive.namelist() if name.startswith("qs_dmss/") and not name.endswith("/")]
        if len(names) != len(set(names)) or not names:
            raise ValueError("Candidate has duplicate or missing package entries")
        for name in names:
            relative = Path(name).relative_to("qs_dmss")
            if ".." in relative.parts or "\\" in name:
                raise ValueError("Unsafe package entry")
            installed = package / relative
            if not installed.is_file() or installed.read_bytes() != archive.read(name):
                raise ValueError(f"Installed candidate differs from wheel: {name}")
        installed_names = {"qs_dmss/" + path.relative_to(package).as_posix()
                           for path in package.rglob("*") if path.is_file()
                           and "__pycache__" not in path.parts and path.suffix != ".pyc"}
        if installed_names != set(names):
            raise ValueError("Installed package contains files outside candidate wheel")
    return len(names)


def packet_summary(results):
    lines = ["# Scientific falsification pilot result", "",
             f"Outcome: **{results['status']}**. Scientific validation: **NOT_ESTABLISHED**.", "",
             f"Source: `{SOURCE_COMMIT}`. Candidate wheel SHA-256: `{results['wheel_sha256']}`.", "",
             "| Exercise | Cases | Not falsified within scope | Failed | Inconclusive |",
             "| --- | ---: | ---: | ---: | ---: |"]
    for name, rows in results["exercises"].items():
        counts = [sum(row["status"] == s for row in rows)
                  for s in ("NOT_FALSIFIED_WITHIN_SCOPE", "FAIL", "INCONCLUSIVE")]
        lines.append(f"| {name} | {len(rows)} | {counts[0]} | {counts[1]} | {counts[2]} |")
    lines.extend(["", "Wolfram: NOT_EXECUTED by this runner; no cross-tool approval is implied.",
                  "Human disposition: PENDING. AI-assisted maintainer evidence is not independent review.",
                  "See results.json for every case, negative control, environment and limitation.",
                  "measurements.npz retains reference/candidate matrices, projectors and trajectories.",
                  "Hashes establish byte integrity only, not scientific correctness or authorship.", ""])
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wheel", required=True, type=Path)
    parser.add_argument("--build-receipt", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    protocol_path = HERE / "protocol-v1.json"
    protocol = load_protocol(protocol_path)
    receipt = json.loads(args.build_receipt.read_text(encoding="utf-8"))
    verified_files = verify_candidate(args.wheel, receipt)
    archive_path = args.output.with_name(args.output.name + ".zip")
    if archive_path.exists():
        raise FileExistsError("Evidence archive already exists; use a new output name")
    args.output.mkdir(parents=True, exist_ok=False)
    results, arrays = run_exercises(protocol)
    results.update({"protocol_id": protocol["protocol_id"], "source_commit": SOURCE_COMMIT,
                    "protocol_preregistration_commit": PROTOCOL_COMMIT,
                    "wheel_sha256": digest(args.wheel), "installed_files_verified": verified_files,
                    "created_utc": datetime.now(timezone.utc).isoformat(),
                    "scientific_validation_status": "NOT_ESTABLISHED",
                    "human_disposition": protocol["human_disposition"],
                    "ai_assistance": protocol["ai_assistance"],
                    "wolfram": {"status": "NOT_EXECUTED", "reason": "Separate cross-tool receipt required; this runner uses SciPy references."},
                    "environment": {"python": platform.python_version(), "platform": platform.platform(),
                                    "machine": platform.machine(),
                                    "packages": {name: importlib.metadata.version(name)
                                                 for name in ("qs-dmss", "numpy", "scipy")},
                                    "installed_distributions": sorted(
                                        f"{dist.metadata['Name']}=={dist.version}"
                                        for dist in importlib.metadata.distributions())},
                    "command": ["python", "pilot.py", "--wheel", args.wheel.name,
                                "--build-receipt", "build-receipt.json", "--output", "packet"],
                    "limitations": ["AI-assisted maintainer exercise, not independent human review",
                                    "Shared NumPy/SciPy infrastructure; no empirical or continuum validation",
                                    "Small fixed cases cannot establish universal correctness"]})
    for path in (protocol_path, HERE / "pilot.py", HERE / "reference.py", HERE / "requirements.txt"):
        (args.output / path.name).write_bytes(path.read_bytes())
    (args.output / "build-receipt.json").write_bytes(args.build_receipt.read_bytes())
    np.savez_compressed(args.output / "measurements.npz", **arrays)
    (args.output / "results.json").write_text(json.dumps(results, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    (args.output / "SUMMARY.md").write_text(packet_summary(results), encoding="utf-8")
    hashes = {p.name: digest(p) for p in sorted(args.output.iterdir()) if p.is_file()}
    (args.output / "manifest.sha256.json").write_text(json.dumps(hashes, indent=2) + "\n", encoding="utf-8")
    with zipfile.ZipFile(archive_path, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(args.output.iterdir()):
            archive.write(path, path.name)
    print(json.dumps({"status": results["status"], "cases": {key: len(rows) for key, rows in results["exercises"].items()},
                      "wheel_sha256": results["wheel_sha256"], "output": str(args.output)}, indent=2))
    return 0 if results["status"] == "NOT_FALSIFIED_WITHIN_SCOPE" else 1


if __name__ == "__main__":
    sys.exit(main())
