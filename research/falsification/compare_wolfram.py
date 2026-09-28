"""Compare preserved candidate measurements with a bounded Wolfram reference.

This process executes neither QS-DMSS nor Wolfram code. It reads data only.
"""

import argparse
import hashlib
import io
import json
import platform
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
PLAN_COMMIT = "463e87e836188a94a39395aa7ec796ce95709a0c"
PLAN_HASH = "a8ddf83a5740be019de895f432af76b8f32ae8361c84730aba66aaaa905d14c3"
PACKET_HASH = "17e568bf7944972c57eda3f275ec7a1126f1cd3d92a4fa04308063425ef02ba4"
SUCCESS = "NOT_FALSIFIED_WITHIN_SCOPE"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def load_plan():
    plan = json.loads((HERE / "wolfram-plan-v1.json").read_text(encoding="utf-8"))
    canonical = json.dumps(plan, sort_keys=True, separators=(",", ":")).encode()
    if sha(canonical) != PLAN_HASH:
        raise ValueError("Wolfram plan differs from preregistration")
    return plan


def load_candidate(path):
    data = path.read_bytes()
    if sha(data) != PACKET_HASH:
        raise ValueError("Candidate packet differs from the pinned immutable evidence")
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        manifest = json.loads(archive.read("manifest.sha256.json"))
        if set(archive.namelist()) != set(manifest) | {"manifest.sha256.json"}:
            raise ValueError("Candidate manifest membership mismatch")
        if any(sha(archive.read(name)) != digest for name, digest in manifest.items()):
            raise ValueError("Candidate manifest hash mismatch")
        results = json.loads(archive.read("results.json"))
        protocol = json.loads(archive.read("protocol-v1.json"))
        with np.load(io.BytesIO(archive.read("measurements.npz")), allow_pickle=False) as stored:
            arrays = {key: stored[key] for key in stored.files}
    return results, protocol, arrays


def number_array(value, shape):
    array = np.asarray(value)
    if array.shape != shape or array.dtype.kind not in "iuf" or not np.all(np.isfinite(array)):
        raise ValueError(f"Malformed or nonfinite numeric evidence; expected shape {shape}")
    return array.astype(float)


def complex_array(value, shape):
    if not isinstance(value, dict) or set(value) != {"real", "imag"}:
        raise ValueError("Malformed complex evidence")
    return number_array(value["real"], shape) + 1j * number_array(value["imag"], shape)


def scalar(value):
    return float(number_array(value, ()))


def error(actual, expected):
    difference, scale = np.linalg.norm(actual - expected), np.linalg.norm(expected)
    # In particular, do not let max(finite, nan) conceal an overflowed comparison.
    if not np.isfinite(difference) or not np.isfinite(scale):
        return float("inf")
    return float(difference / max(1, scale))


def state_error(actual, expected, mass, initial):
    difference = np.max(np.sqrt(np.sum(mass * np.abs(actual - expected)**2, axis=-1)))
    scale = np.sqrt(np.sum(mass * np.abs(initial)**2))
    if not np.isfinite(difference) or not np.isfinite(scale) or scale <= 0:
        return float("inf")
    return float(difference / scale)


def bounded(value, limit):
    return bool(np.isfinite(value) and 0 <= value <= limit)


def outcome(checks):
    return SUCCESS if all(checks) else "FAIL"


def json_record(value):
    """Retain overflow counterexamples without writing invalid JSON."""
    if isinstance(value, float) and not np.isfinite(value):
        return {"nonfinite": str(value)}
    if isinstance(value, dict):
        return {key: json_record(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_record(item) for item in value]
    return value


def identities(rows, candidate_rows, fields):
    if not isinstance(rows, list) or len(rows) != len(candidate_rows):
        raise ValueError("Missing or extra cases")
    for row, candidate in zip(rows, candidate_rows):
        if not isinstance(row, dict) or any(row[key] != candidate[key] for key in fields):
            raise ValueError("Case identity/order mismatch, including duplicate cases")


def compare_fft(rows, candidate, protocol, arrays):
    identities(rows, candidate, ("backend", "shape", "length", "mass", "mode"))
    p = protocol["fft"]
    compared = []
    for row, old in zip(rows, candidate):
        energy_error = error(old["actual_energy"], scalar(row["energy"]))
        norm_error = abs(scalar(row["norm"]) - 1)
        compared.append({**{key: row[key] for key in ("backend", "shape", "length", "mass", "mode")},
                         "energy_error": energy_error, "analytic_norm_error": norm_error,
                         "candidate_norm_error": old["norm_error"],
                         "status": outcome([bounded(energy_error, p["scaled_energy_error_max"]),
                                            bounded(norm_error, p["norm_error_max"]),
                                            bounded(old["norm_error"], p["norm_error_max"])])})
    return compared


def compare_graph(rows, candidate, protocol, arrays):
    identities(rows, candidate, ("level", "boundary", "length"))
    p = protocol["graph"]
    compared = []
    for row, old in zip(rows, candidate):
        key = old["artifact_prefix"]
        mass = number_array(row["mass"], arrays[key + "_candidate_mass"].shape)
        if np.any(mass <= 0):
            raise ValueError("Nonpositive Wolfram mass weights")
        size = len(mass)
        stiffness = number_array(row["stiffness"], (size, size))
        spectrum = number_array(row["spectrum"], (size,))
        if np.any(np.diff(spectrum) < 0):
            raise ValueError("Unordered Wolfram spectrum")
        splits = np.flatnonzero(np.diff(spectrum) > p["reference_cluster_relative_gap"] *
                               max(1, np.max(np.abs(spectrum)))) + 1
        groups = [group.tolist() for group in np.split(np.arange(size), splits)]
        if row["groups"] != groups:
            raise ValueError("Incomplete or incorrectly clustered eigenspaces")
        ref_values = arrays[key + "_reference_spectrum"]
        ref_splits = np.flatnonzero(np.diff(ref_values) > p["reference_cluster_relative_gap"] *
                                   max(1, np.max(np.abs(ref_values)))) + 1
        if groups != [group.tolist() for group in np.split(np.arange(size), ref_splits)]:
            raise ValueError("Reference cluster correspondence is inconclusive")
        projectors = number_array(row["projectors"], arrays[key + "_candidate_projectors"].shape)
        topology = all(np.array_equal(number_array(row[field], arrays[key + "_reference_" + name].shape),
                                      arrays[key + "_reference_" + name]) for field, name in
                       (("vertices", "vertices"), ("edges", "edges"), ("active", "active"),
                        ("boundary_ids", "boundary")))
        matrix_error = max(error(arrays[key + "_candidate_mass"], mass),
                           error(arrays[key + "_candidate_stiffness"], stiffness))
        spectrum_error = error(arrays[key + "_candidate_spectrum"], spectrum)
        projector_error = max(error(a, b) for a, b in zip(arrays[key + "_candidate_projectors"], projectors))
        nominal = int(p["tail_fraction"] * size)
        tail_start = next(group[0] for group in groups if nominal in group)
        selected = [i for i, group in enumerate(groups) if group[0] >= tail_start]
        candidate_tail = arrays[key + "_candidate_projectors"][selected].sum(axis=0)
        weighted = np.sqrt(mass) * complex_array(row["initial"], (size,))
        denominator = np.vdot(weighted, weighted).real
        if denominator <= 0:
            raise ValueError("Zero-norm initial state")
        tail = float(np.vdot(weighted, candidate_tail @ weighted).real / denominator)
        tail_error = abs(tail - scalar(row["tail_power"]))
        compared.append({"artifact_prefix": key, "level": row["level"], "boundary": row["boundary"],
                         "length": row["length"], "topology_matches": topology, "matrix_error": matrix_error,
                         "spectrum_error": spectrum_error, "projector_error": projector_error,
                         "reconstructed_tail_error": tail_error,
                         "status": outcome([topology, bounded(matrix_error, p["scaled_matrix_error_max"]),
                                            bounded(spectrum_error, p["scaled_spectrum_error_max"]),
                                            bounded(projector_error, p["projector_error_max"]),
                                            bounded(tail_error, p["tail_error_max"]),
                                            row["tail_start"] == old["candidate_tail_start"] == tail_start])})
    return compared


def compare_evolution(rows, candidate, protocol, arrays):
    identities(rows, candidate, ("boundary",))
    p = protocol["evolution"]
    compared = []
    for row, old in zip(rows, candidate):
        key = old["artifact_prefix"]
        mass = number_array(row["mass"], arrays[key + "_reference_mass"].shape)
        if np.any(mass <= 0):
            raise ValueError("Nonpositive evolution mass weights")
        size = len(mass)
        times = number_array(row["times"], arrays[key + "_times"].shape)
        initial = complex_array(row["initial"], (size,))
        if not bounded(abs(float(np.sum(mass * np.abs(initial)**2)) - 1), p["norm_error_max"]):
            raise ValueError("Unnormalized Wolfram initial state")
        reference = complex_array(row["reference"], (len(times), size))
        loose = complex_array(row["reference_loose"], reference.shape)
        linear = complex_array(row["linear"], (size,))
        precision_error = scalar(row["internal_precision_refinement_error"])
        exported_error = state_error(loose, reference, mass, initial)
        cross_tool_error = state_error(arrays[key + "_reference"], reference, mass, initial)
        linear_error = state_error(arrays[key + "_linear_candidate"], linear, mass, initial)
        fields_error = max(error(arrays[key + "_" + field], number_array(row[field], (size,)))
                           for field in ("potential", "gamma"))
        matrix_error = max(error(arrays[key + "_reference_mass"], mass),
                           error(arrays[key + "_reference_stiffness"],
                                 number_array(row["stiffness"], (size, size))))
        initial_error = state_error(arrays[key + "_candidate_4"][0], initial, mass, initial)
        errors, norm_errors = [], []
        for count in p["step_counts"]:
            states = arrays[f"{key}_candidate_{count}"]
            target = reference[::max(p["step_counts"])//count]
            errors.append(state_error(states, target, mass, initial))
            norm_errors.append(float(np.max(np.abs(np.sum(mass * np.abs(states)**2, axis=1) - 1))))
        orders = [float(np.log2(a/b)) if a > 0 and b > 0 else None for a, b in zip(errors, errors[1:])]
        agreement = max(precision_error, exported_error, cross_tool_error)
        resolved = min(errors) > max(p["resolution_floor"], p["reference_separation_factor"] * agreement)
        result = outcome([bounded(linear_error, p["linear_error_max"]),
                          bounded(errors[-1], p["fine_trajectory_error_max"]),
                          bounded(max(norm_errors), p["norm_error_max"]),
                          bounded(initial_error, p["reference_agreement_max"]),
                          bounded(fields_error, protocol["graph"]["scaled_matrix_error_max"]),
                          bounded(matrix_error, protocol["graph"]["scaled_matrix_error_max"]),
                          bounded(error(arrays[key + "_times"], times), p["reference_agreement_max"])])
        if result != "FAIL":
            if not resolved or not all(bounded(value, p["reference_agreement_max"])
                                       for value in (precision_error, exported_error, cross_tool_error)):
                result = "INCONCLUSIVE"
            else:
                result = outcome([o is not None and p["order_interval"][0] <= o <= p["order_interval"][1]
                                  for o in orders])
        compared.append({"boundary": row["boundary"], "internal_precision_refinement_error": precision_error,
                         "exported_precision_refinement_error": exported_error, "cross_tool_error": cross_tool_error,
                         "linear_error": linear_error, "fields_error": fields_error, "matrix_error": matrix_error,
                         "initial_error": initial_error, "trajectory_errors": errors, "norm_errors": norm_errors,
                         "observed_orders": orders, "refinement_resolved": resolved, "status": result})
    return compared


def compare(receipt, candidate, protocol, arrays):
    plan = load_plan()
    result = {"assessment_id": plan["assessment_id"], "source_commit": plan["candidate_source_commit"],
              "candidate_packet_sha256": PACKET_HASH, "plan_preregistration_commit": PLAN_COMMIT,
              "scientific_validation_status": "NOT_ESTABLISHED", "human_disposition": plan["human_disposition"],
              "ai_assistance": plan["ai_assistance"], "status": "INCONCLUSIVE", "exercises": {}}
    try:
        if (receipt["status"] != "EXECUTED" or receipt["assessment_id"] != plan["assessment_id"] or
                receipt["source_commit"] != plan["candidate_source_commit"] or
                receipt["working_precisions"] != plan["working_precisions"]):
            raise ValueError("Wolfram execution or identity incomplete")
        for name, operation in (("fft", compare_fft), ("graph", compare_graph), ("evolution", compare_evolution)):
            try:
                result["exercises"][name] = operation(receipt["exercises"][name],
                                                       candidate["exercises"][name], protocol, arrays)
            except (KeyError, TypeError, ValueError, IndexError, FloatingPointError) as exc:
                result["exercises"][name] = [{"status": "INCONCLUSIVE", "reason": f"{type(exc).__name__}: {exc}"}]
        states = [row["status"] for rows in result["exercises"].values() for row in rows]
        result["status"] = "FAIL" if "FAIL" in states else ("INCONCLUSIVE" if "INCONCLUSIVE" in states else SUCCESS)
    except (KeyError, TypeError, ValueError) as exc:
        result["reason"] = f"{type(exc).__name__}: {exc}"
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-packet", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--execution-log", type=Path, required=True)
    parser.add_argument("--prior-attempt-log", type=Path, action="append", default=[])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    candidate, protocol, arrays = load_candidate(args.candidate_packet)
    if args.reference.stat().st_size > 2_000_000:
        raise ValueError("Reference exceeds bounded evidence size")
    receipt = json.loads(args.reference.read_text(encoding="utf-8"))
    sources = {name: (HERE / name).read_bytes() for name in
               ("protocol-v1.json", "wolfram-plan-v1.json", "wolfram_reference.wl", "compare_wolfram.py")}
    if json.loads(sources["protocol-v1.json"]) != protocol:
        raise ValueError("Protocol differs from the immutable candidate protocol")
    for field, name in (("protocol_file_sha256", "protocol-v1.json"), ("plan_file_sha256", "wolfram-plan-v1.json"),
                        ("reference_file_sha256", "wolfram_reference.wl")):
        if receipt.get(field) != sha(sources[name]):
            raise ValueError(f"Wolfram execution input/source hash mismatch: {name}")
    archive_path = args.output.with_name(args.output.name + ".zip")
    if args.output.exists() or archive_path.exists():
        raise FileExistsError("Use a new output name; evidence is immutable")
    result = compare(receipt, candidate, protocol, arrays)
    result.update({"created_utc": datetime.now(timezone.utc).isoformat(),
                   "environment": {"python": platform.python_version(), "numpy": np.__version__},
                   "kernel_version": receipt["kernel_version"],
                   "reference_sha256": sha(args.reference.read_bytes()),
                   "reference_command": ["wolframscript", "-file", "wolfram_reference.wl", "reference.json"],
                   "prior_attempt_logs": [f"prior-attempt-{i:02d}.log" for i in range(1, len(args.prior_attempt_log) + 1)],
                   "limitations": ["Same AI-assisted authoring context; not independent human review",
                                   "Finite-model agreement is not physical or continuum validation",
                                   "Candidate measurements reused from immutable installed-wheel packet",
                                   "Tail power reconstructed from retained candidate projectors; no new solver invocation"]})
    args.output.mkdir(parents=True, exist_ok=False)
    sources.update({"reference.json": args.reference.read_bytes(), "execution.log": args.execution_log.read_bytes(),
                    "results.json": (json.dumps(json_record(result), indent=2, allow_nan=False) + "\n").encode()})
    sources.update({f"prior-attempt-{i:02d}.log": path.read_bytes()
                    for i, path in enumerate(args.prior_attempt_log, start=1)})
    for name, data in sources.items():
        (args.output / name).write_bytes(data)
    manifest = {name: sha(data) for name, data in sources.items()}
    (args.output / "manifest.sha256.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    with zipfile.ZipFile(archive_path, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(args.output.iterdir()):
            archive.write(path, path.name)
    print(json.dumps({"status": result["status"], "cases": {name: len(rows) for name, rows in result["exercises"].items()},
                      "archive_sha256": sha(archive_path.read_bytes())}, indent=2))
    return 0 if result["status"] == SUCCESS else 1


if __name__ == "__main__":
    sys.exit(main())
