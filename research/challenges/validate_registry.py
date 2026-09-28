"""Check the frozen challenge registry against retained evidence, without execution.

No network, archive extraction, submitted-code execution or scientific approval.
Requires the existing development dependency jsonschema, not a runtime dependency.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import zipfile
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = "research/challenges/registry-v1.json"
SCHEMA = "schemas/scientific-challenge-registry-v1.schema.json"
PROTOCOL_HASH = "fcecbf9ae403ad26ee8e28383ef90a5d15b7732a85af2d756ddeef03a748402b"
PACKETS = {
    "pilot-v1": ("docs/review-evidence/falsification-pilot-v1.zip",
                 "17e568bf7944972c57eda3f275ec7a1126f1cd3d92a4fa04308063425ef02ba4"),
    "wolfram-v1": ("docs/review-evidence/wolfram-falsification-v1.zip",
                   "fbdaa5c21a680f1d0a04be477c852ca1fedaddb2dae0f58be12b9256900e75b7"),
}
CASES = {
    "SC-FFT-001": ("fft", 72, ["fft_cell_measure_v2"]),
    "SC-GRAPH-001": ("graph", 15, ["graph_mass_stiffness_v1", "whole_eigenvalue_cluster_v1"]),
    "SC-EVOLUTION-001": ("evolution", 2, ["graph_mass_stiffness_v1"]),
}
LIMIT_KEYS = {
    "fft": ("scaled_energy_error_max", "norm_error_max"),
    "graph": ("scaled_matrix_error_max", "scaled_spectrum_error_max", "projector_error_max",
              "reference_cluster_relative_gap", "tail_fraction", "tail_error_max"),
    "evolution": ("reference_agreement_max", "linear_error_max", "fine_trajectory_error_max",
                  "norm_error_max", "order_interval", "resolution_floor", "reference_separation_factor"),
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def no_duplicates(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def reject_constant(value):
    raise ValueError(f"Nonfinite JSON constant: {value}")


def finite_float(value):
    parsed = float(value)
    require(math.isfinite(parsed), "Nonfinite JSON number")
    return parsed


def read_json(data):
    return json.loads(data, object_pairs_hook=no_duplicates, parse_constant=reject_constant, parse_float=finite_float)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def checked_path(root, relative):
    # Accept only repository-relative forward-slash paths, including on Windows.
    require(relative and "\\" not in relative and ":" not in relative and
            not relative.startswith("/") and ".." not in relative.split("/"), "Unsafe repository path")
    path = (root / relative).resolve()
    require(path.is_relative_to(root.resolve()), "Repository path escapes root")
    return path


def read_packet(root, packet):
    expected_path, expected_hash = PACKETS[packet["id"]]
    require((packet["path"], packet["sha256"]) == (expected_path, expected_hash),
            "Packet identity differs from frozen pilot evidence")
    path = checked_path(root, packet["path"])
    require(path.stat().st_size <= 2_000_000, "Oversized evidence archive")
    require(sha(path.read_bytes()) == expected_hash, "Evidence archive hash mismatch")
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        require(len(names) == len(set(names)) and len(names) <= 32, "Duplicate or excessive archive entries")
        require(sum(item.file_size for item in archive.infolist()) <= 4_000_000, "Oversized archive contents")
        manifest = read_json(archive.read("manifest.sha256.json"))
        require(set(names) == set(manifest) | {"manifest.sha256.json"}, "Evidence manifest membership mismatch")
        require(all(sha(archive.read(name)) == digest for name, digest in manifest.items()),
                "Evidence manifest hash mismatch")
        documents = {name: read_json(archive.read(name)) for name in names if name.endswith(".json")}
    return documents


def resolve_pointer(documents, pointer):
    filename, fragment = pointer.split("#", 1)
    require(fragment.startswith("/"), "Expected an explicit JSON pointer")
    value = documents[filename]
    for token in fragment[1:].split("/"):
        value = value[token.replace("~1", "/").replace("~0", "~")]
    return value


def aggregate(outcomes):
    require(bool(outcomes) and all(value in {"FAIL", "INCONCLUSIVE", "NOT_FALSIFIED_WITHIN_SCOPE"}
                                   for value in outcomes), "Missing or unknown numerical outcomes")
    if "FAIL" in outcomes:
        return "FAIL"
    return "INCONCLUSIVE" if "INCONCLUSIVE" in outcomes else "NOT_FALSIFIED_WITHIN_SCOPE"


def validate_registry(registry, root=ROOT):
    """Validate metadata/data correspondence only; never certify scientific prose."""
    root = Path(root)
    schema = read_json((root / SCHEMA).read_bytes())
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(registry)
    candidate = registry["candidate"]
    protocol = read_json(checked_path(root, candidate["protocol_path"]).read_bytes())
    canonical = json.dumps(protocol, sort_keys=True, separators=(",", ":")).encode()
    require(sha(canonical) == candidate["protocol_canonical_sha256"] == PROTOCOL_HASH,
            "Protocol differs from preregistration")
    require(candidate["source_commit"] == protocol["source_commit"], "Candidate source mismatch")
    baseline = registry["published_baseline"]
    published = read_json(checked_path(root, baseline["evidence_path"]).read_bytes())["release"]
    require(all(baseline[key] == published[key] for key in ("version", "source_commit", "wheel_sha256")),
            "Published baseline identity mismatch")
    require(candidate["source_commit"] != baseline["source_commit"] and
            candidate["wheel_sha256"] != baseline["wheel_sha256"], "Candidate/release identity conflation")
    packets = registry["evidence_packets"]
    require({packet["id"] for packet in packets} == set(PACKETS), "Duplicate/missing evidence packets")
    evidence = {}
    for packet in packets:
        documents = read_packet(root, packet)
        evidence[packet["id"]] = documents
        require(documents["protocol-v1.json"] == protocol, "Packet/protocol mismatch")
        report = documents["results.json"]
        require(report["source_commit"] == candidate["source_commit"], "Evidence source mismatch")
        require(report["scientific_validation_status"] == "NOT_ESTABLISHED" and
                report["human_disposition"] == {"status": "PENDING", "reviewer": None},
                "Evidence unexpectedly asserts scientific approval")
        expected_url = ("https://github.com/AI-Bio-Synergy-Holdings-LLC/QS-DMSS/blob/" +
                        registry["engineering_review"]["merged_commit"] + "/" + packet["path"])
        require(packet["url"] == expected_url, "Evidence URL must be pinned to its retained commit")
        expected_pointer = "results.json#/environment" if packet["id"] == "pilot-v1" else "reference.json#/kernel_version"
        require(packet["environment_pointer"] == expected_pointer, "Incorrect environment pointer")
        require(bool(resolve_pointer(documents, expected_pointer)), "Missing environment receipt")
    pilot = evidence["pilot-v1"]["results.json"]
    wolfram = evidence["wolfram-v1"]["results.json"]
    require(candidate["wheel_sha256"] == pilot["wheel_sha256"], "Candidate wheel mismatch")
    require(wolfram["candidate_packet_sha256"] == PACKETS["pilot-v1"][1], "Wolfram candidate binding mismatch")
    challenges = registry["challenges"]
    require({challenge["id"] for challenge in challenges} == set(CASES), "Duplicate/missing challenge IDs")
    for challenge in challenges:
        exercise, count, conventions = CASES[challenge["id"]]
        require((challenge["exercise"], challenge["case_count"], challenge["diagnostic_conventions"]) ==
                (exercise, count, conventions), "Challenge case or convention mismatch")
        require(challenge["source_commit"] == candidate["source_commit"], "Challenge source mismatch")
        limits = {key: protocol[exercise][key] for key in LIMIT_KEYS[exercise]}
        require(challenge["acceptance_limits"] == limits, "Challenge acceptance limits drifted")
        results = challenge["results"]
        require({result["packet_id"] for result in results} == set(PACKETS), "Duplicate/missing result references")
        outcomes = []
        for result in results:
            require(result["pointer"] == f"results.json#/exercises/{exercise}", "Incorrect result pointer")
            rows = resolve_pointer(evidence[result["packet_id"]], result["pointer"])
            require(len(rows) == result["case_count"] == count, "Incorrect result count")
            observed = aggregate([row["status"] for row in rows])
            require(result["outcome"] == observed, "Result outcome differs from retained evidence")
            outcomes.append(observed)
        require(challenge["evidence_outcome"] == aggregate(outcomes), "Challenge outcome differs from evidence")
        guide, anchor = challenge["reproduction_guide"].split("#", 1)
        text = checked_path(root, guide).read_text(encoding="utf-8")
        require("## " + anchor.replace("-", " ").capitalize() in text, "Reproduction anchor is missing")
    return {"registry_integrity": "CONSISTENT", "challenges": len(challenges),
            "candidate_cases": sum(challenge["case_count"] for challenge in challenges),
            "cross_tool_comparisons": sum(challenge["case_count"] for challenge in challenges),
            "scientific_validation_status": "NOT_ESTABLISHED", "independent_review": "PENDING"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=ROOT / REGISTRY)
    args = parser.parse_args()
    require(args.registry.stat().st_size <= 100_000, "Oversized registry")
    print(json.dumps(validate_registry(read_json(args.registry.read_bytes())), indent=2))


if __name__ == "__main__":
    main()
