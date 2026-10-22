"""Synthetic-only characterization of source-only CERN qualification helpers."""

import ast
import copy
import hashlib
import json
import math
import os
import subprocess
import sys
import zipfile
from decimal import ROUND_UP, Decimal, localcontext
from pathlib import Path
from types import SimpleNamespace

import pytest

from research.cern_dimuon_qualification import (
    candidate,
    preflight,
    retention,
)
from research.cern_dimuon_qualification import (
    comparison as comparison_module,
)
from research.cern_dimuon_qualification.comparison import compare
from research.cern_dimuon_qualification.contract import (
    BUCKETS,
    COMMIT,
    LOG_BYTES,
    SCIENTIFIC,
    SLOT_BYTES,
    TOTAL_BYTES,
    WHEEL_SHA256,
    Hold,
    checked_protocol,
    json_bytes,
)
from research.cern_dimuon_qualification.reference import (
    HEADER,
    bin_index,
    checked_edges,
    evaluate,
    ideal_edges,
    parse,
)
from research.cern_dimuon_qualification.retention import (
    Store,
    audit_existing,
    literal,
    read_regular,
)

ROOT = Path(__file__).resolve().parents[1]
HELPERS = ROOT / "research/cern_dimuon_qualification"


def read_json(path):
    return json.loads(path.read_bytes())


def retained_files(root):
    return {
        p.relative_to(root).as_posix(): p.read_bytes()
        for p in root.rglob("*")
        if p.is_file()
    }


def csv_fixture(**changes):
    original = dict(
        zip(HEADER, preflight.synthetic_csv().decode().splitlines()[1].split(","))
    )
    original.update({key: str(value) for key, value in changes.items()})
    return (
        ",".join(HEADER) + "\n" + ",".join(original[key] for key in HEADER) + "\n"
    ).encode()


def comparison(raw):
    result, views = candidate.probe(raw)
    return compare(parse(raw), result, views)


def test_protocol_and_fixed_budget_are_separate_from_production():
    plan = read_json(HELPERS / "protocol-v1.json")
    assert plan["qualification_outcome"] == "NOT_EXECUTED"
    assert plan["profile"] == {"bins": 60, "mass_min": 2, "mass_max": 5, "pt_min": 0}
    assert sum(BUCKETS.values()) == TOTAL_BYTES == 26 * 1024 * 1024
    assert plan["retention"]["buckets"] == BUCKETS
    assert plan["preservation"]["gate_183"] == "OPEN_AND_UNCHANGED"
    assert (
        plan["retention"]["unchanged_production_limits"]["retained_output_bytes"]
        == 10 * 1024 * 1024
    )
    assert len(checked_protocol()["canonical_sha256"]) == 64


def test_protocol_drift_duplicate_fields_and_portable_newlines(tmp_path):
    raw = (HELPERS / "protocol-v1.json").read_bytes()
    path = tmp_path / "protocol.json"
    path.write_bytes(raw.replace(b"\n", b"\r\n"))
    assert (
        checked_protocol(path)["canonical_sha256"]
        == checked_protocol()["canonical_sha256"]
    )
    value = json.loads(raw)
    value["reference"]["summary_tolerance_GeV"] = "looser"
    path.write_text(json.dumps(value))
    with pytest.raises(Hold, match="approved"):
        checked_protocol(path)
    path.write_bytes(b'{"revision":1,"revision":1}')
    with pytest.raises(Hold):
        checked_protocol(path)


def test_approved_candidate_pin_matches_protocol_and_adapter():
    plan = read_json(HELPERS / "protocol-v1.json")
    assert plan["candidate_commit"] == COMMIT
    assert (
        plan["candidate_wheel_sha256"]
        == WHEEL_SHA256
        == candidate.WHEEL_SHA256
        == "6a8af63f047be841a9ce17d3f02392d56f0963498979f7c27593aed40aac1e60"
    )


@pytest.mark.parametrize("field", ["candidate_commit", "candidate_wheel_sha256"])
def test_candidate_retargeting_requires_a_new_approved_contract(tmp_path, field):
    plan = read_json(HELPERS / "protocol-v1.json")
    plan[field] = "0" * len(plan[field])
    path = tmp_path / "retargeted.json"
    path.write_text(json.dumps(plan))
    with pytest.raises(Hold, match="approved semantic contract"):
        checked_protocol(path)


def test_comparison_is_independent_of_ambient_decimal_context():
    raw = csv_fixture(E1="1.6123456789", E2="1.6123456789")
    original = comparison(raw)
    with localcontext() as context:
        context.prec = 6
        context.rounding = ROUND_UP
        context.Emax = 4
        context.Emin = -4
        assert comparison(raw) == original


@pytest.mark.parametrize("delta,outcome", [(1e-14, "MATCH"), (1e-10, "MISMATCH")])
def test_fixed_mass_squared_threshold_is_not_retuned(delta, outcome):
    raw = csv_fixture()
    result, views = candidate.probe(raw)
    views[0]["mass"] += delta
    assert compare(parse(raw), result, views)["comparison_outcome"] == outcome


def test_tiny_decimal_underflow_refuses_instead_of_silently_zeroing():
    row = parse(csv_fixture(px1="1e-10000000", px2="0"))[0]
    with pytest.raises(Hold, match="arithmetic range"):
        evaluate(row, "decimal80")


def identity_fixture(tmp_path, monkeypatch, blob, member):
    module_path = tmp_path / "module.py"
    module_path.write_bytes(blob)
    wheel = tmp_path / "synthetic.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr(member, blob)
    monkeypatch.setattr(candidate, "IDENTITY_MODULES", {"fixture": member})
    monkeypatch.setattr(
        candidate, "WHEEL_SHA256", hashlib.sha256(wheel.read_bytes()).hexdigest()
    )
    monkeypatch.setattr(
        candidate.importlib,
        "import_module",
        lambda _name: SimpleNamespace(__file__=module_path),
    )
    monkeypatch.setattr(
        candidate.subprocess, "run", lambda *a, **kw: SimpleNamespace(stdout=blob)
    )
    return module_path, wheel


def test_wheel_source_identity_positive_and_negative_paths(tmp_path, monkeypatch):
    blob = b"# synthetic identity fixture\n"
    module_path, wheel = identity_fixture(
        tmp_path, monkeypatch, blob, "qs_dmss/external_data/analysis.py"
    )
    assert (
        candidate.wheel_identity(wheel, ROOT)["module_sha256"][
            "qs_dmss/external_data/analysis.py"
        ]
        == hashlib.sha256(blob).hexdigest()
    )
    module_path.write_bytes(b"drift")
    with pytest.raises(Hold, match="Imported candidate bytes"):
        candidate.wheel_identity(wheel, ROOT)
    module_path.write_bytes(blob)
    monkeypatch.setattr(
        candidate.subprocess,
        "run",
        lambda *a, **kw: SimpleNamespace(stdout=b"different Git bytes"),
    )
    with pytest.raises(Hold, match="pinned Git"):
        candidate.wheel_identity(wheel, ROOT)


def test_git_lf_and_wheel_crlf_are_not_silently_normalized(tmp_path, monkeypatch):
    blob = b"# synthetic CRLF identity fixture\r\n"
    source, wheel = identity_fixture(tmp_path, monkeypatch, blob, "qs_dmss/cli.py")
    monkeypatch.setattr(
        candidate.subprocess,
        "run",
        lambda *a, **kw: SimpleNamespace(stdout=blob.replace(b"\r\n", b"\n")),
    )
    before = wheel.read_bytes()
    with pytest.raises(Hold, match="pinned Git bytes"):
        candidate.wheel_identity(wheel, ROOT)
    assert source.read_bytes() == blob and wheel.read_bytes() == before


def test_partial_storage_failure_keeps_receipts_and_partial_source(
    tmp_path, monkeypatch
):
    original = Store.write

    def fail_after_partial(self, bucket, relative, data):
        if bucket == "records/source":
            original(self, bucket, relative, data[:10])
            raise OSError("unbounded private storage error must not be retained")
        return original(self, bucket, relative, data)

    monkeypatch.setattr(Store, "write", fail_after_partial)
    output = tmp_path / "failed-storage"
    with pytest.raises(Hold):
        preflight.run_preflight(output)
    starts = (output / "records/logs/supervisor-started.json").read_bytes()
    final = (output / "records/logs/supervisor-final.json").read_bytes()
    assert json.loads(starts)["state"] == "STARTED"
    assert json.loads(final)["state"] == "HOLD"
    assert b"private storage" not in final
    assert any(
        p.stat().st_size == 10 for p in (output / "records/source").rglob("*.py")
    )


def test_failed_root_read_only_accounting(tmp_path):
    store = Store(tmp_path / "failed")
    store.finish("supervisor", {"state": "HOLD"})
    before = {p: p.read_bytes() for p in store.root.rglob("*") if p.is_file()}
    assert audit_existing(store.root)["total_bytes"] == sum(map(len, before.values()))
    assert {p: p.read_bytes() for p in before} == before


def test_cli_refusal_is_json_and_preserves_failed_root(tmp_path, capsys):
    wheel = tmp_path / "synthetic-not-wheel"
    wheel.write_bytes(b"not a wheel")
    output = tmp_path / "failed"
    assert (
        preflight.main(["--output", str(output), "--candidate-wheel", str(wheel)]) == 1
    )
    record = json.loads(capsys.readouterr().out)
    assert record["preflight_outcome"] == "HOLD"
    assert record["qualification_outcome"] == "NOT_EXECUTED"
    assert record["pilot_execution_ready"] is False
    assert audit_existing(output)["total_bytes"] < TOTAL_BYTES
    with pytest.raises(SystemExit):
        preflight.main(["--worker", "normal", "--output", str(output)])


def test_fixed_worker_controls_directly_without_external_inputs(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.chdir(tmp_path)
    raw = preflight.synthetic_csv()
    (tmp_path / "synthetic.csv").write_bytes(raw)
    assert preflight.worker("normal") == 0
    assert (
        json.loads(capsys.readouterr().out)["synthetic_input_sha256"]
        == hashlib.sha256(raw).hexdigest()
    )
    (tmp_path / "drift-target.txt").write_bytes(b"synthetic drift input\n")
    assert preflight.worker("drift") == 0
    assert (tmp_path / "drift-target.txt").read_bytes() == b"synthetic drift changed\n"
    capsys.readouterr()
    waits = []
    monkeypatch.setattr(preflight.time, "sleep", waits.append)
    assert preflight.worker("timeout") == 0 and waits == [10]
    capsys.readouterr()
    assert preflight.worker("overflow") == 0
    assert capsys.readouterr().out == "X" * (LOG_BYTES + 1)


def test_private_worker_cli_refuses_unreserved_cwd_without_mutating(
    tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    target = tmp_path / "drift-target.txt"
    target.write_bytes(b"synthetic drift input\n")
    with pytest.raises(SystemExit):
        preflight.main(["--worker", "drift"])
    assert target.read_bytes() == b"synthetic drift input\n"


def test_missing_null_scientific_field_is_not_inferred():
    raw = csv_fixture()
    result, views = candidate.probe(raw)
    del result["ai_advice"]
    with pytest.raises(Hold, match="scientific-status"):
        compare(parse(raw), result, views)


def test_reference_has_no_candidate_or_numpy_imports():
    tree = ast.parse((HELPERS / "reference.py").read_text())
    names = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            names.append(node.module or "")
    assert not any(name.startswith(("numpy", "qs_dmss", "candidate")) for name in names)
    assert "decimal" in names


def test_synthetic_reference_candidate_row_views_and_accounting():
    result = comparison(preflight.synthetic_csv())
    assert result["comparison_outcome"] == "MATCH"
    assert result["input_rows"] == 3
    assert result["selected"] == sum(result["histogram_counts"]) == 2
    assert len(result["exclusions"]) == 1
    assert result["exclusions"][0]["data_row"] == 3
    assert result["exclusions"][0]["physical_line"] == 4
    assert result["exclusions"][0]["tokens"]["eta1"] == "2.4"
    assert set(result["reference_stream_sha256"]) == {
        "binary64",
        "decimal80",
        "decimal120",
    }
    assert (
        result["reference_stream_sha256"]["decimal80"]
        == result["reference_stream_sha256"]["decimal120"]
    )
    for key, value in SCIENTIFIC.items():
        assert result[key] == value


@pytest.mark.parametrize(
    "changes,stage",
    [
        ({"E1": 1, "E2": 1}, "source_strict_mass_2_to_5_GeV"),
        ({"E1": 2.5, "E2": 2.5}, "source_strict_mass_2_to_5_GeV"),
        ({"eta2": "-2.4"}, "source_both_abs_eta_below_2_4"),
        ({"type1": "T"}, "source_at_least_one_global_muon"),
        ({"Q2": 1}, "source_opposite_sign"),
        (
            {"E1": 1, "E2": 1, "px1": 3, "px2": 0},
            "nonnegative_mass_squared_with_roundoff_policy",
        ),
        (
            {"E1": 1, "E2": 1, "px1": "2.0000000000000004", "px2": 0},
            "source_strict_mass_2_to_5_GeV",
        ),
    ],
)
def test_analytic_boundary_and_empty_controls(changes, stage):
    raw = csv_fixture(**changes)
    result = comparison(raw)
    assert result["comparison_outcome"] == "MATCH"
    assert result["selected"] == 0
    assert sum(result["histogram_counts"]) == 0
    assert result["exclusions"][0]["first_failure"] == stage


@pytest.mark.parametrize(
    "changes,reason",
    [
        ({"E1": "bad"}, "invalid_numeric"),
        ({"E1": "NaN"}, "nonfinite_or_out_of_range"),
        ({"E1": "1000001"}, "nonfinite_or_out_of_range"),
        ({"pt1": -1}, "invalid_category_or_identity"),
        ({"Q1": 0}, "invalid_category_or_identity"),
        ({"Run": "1" * 20}, "invalid_category_or_identity"),
    ],
)
def test_invalid_admission_first_failure_is_independently_checked(changes, reason):
    from qs_dmss.external_data.admission import admit_csv

    raw = csv_fixture(**changes)
    rows = parse(raw)
    assert rows[0].invalid == reason
    assert evaluate(rows[0])["first_failure"] == reason
    assert admit_csv(raw, "synthetic").invalid_rows[reason] == 1
    with pytest.raises(Hold, match="cannot infer"):
        candidate.probe(raw)


@pytest.mark.parametrize(
    "raw",
    [
        b"",
        b"header\nrow\n",
        b"\xff",
        csv_fixture() + b"\x00",
        csv_fixture().replace(b"1,1,G", b'1,1,"G\n'),
    ],
)
def test_reference_structure_refusal(raw):
    with pytest.raises(Hold):
        parse(raw)


@pytest.mark.parametrize(
    "changes,expected_reason",
    [
        ({"E1": "1.49999999999999999"}, "higher_precision_bin_disagreement"),
        (
            {"E1": "1.000000000000000001", "E2": 1},
            "higher_precision_selection_disagreement",
        ),
    ],
)
def test_decimal_tokens_are_not_preconverted_and_boundary_changes_hold(
    changes, expected_reason
):
    result = comparison(csv_fixture(**changes))
    assert result["comparison_outcome"] == "HOLD"
    assert expected_reason in result["counterexamples"][0]["reasons"]


def test_candidate_counterexamples_are_retained_not_tolerance_reassigned():
    raw = preflight.synthetic_csv()
    result, views = candidate.probe(raw)
    views[0]["mass"] += 0.01
    views[0]["bin"] += 1
    checked = compare(parse(raw), result, views)
    assert checked["comparison_outcome"] == "MISMATCH"
    assert "mass_squared_threshold_exceeded" in checked["counterexamples"][0]["reasons"]
    assert (
        "candidate_binary64_bin_disagreement"
        in checked["counterexamples"][0]["reasons"]
    )
    assert checked["counterexamples"][0]["candidate"]["mass"] == views[0]["mass"]


def test_all_aggregate_criteria_and_scientific_fields_are_checked():
    raw = preflight.synthetic_csv()
    original, views = candidate.probe(raw)
    for field in ("histogram", "cut_flow", "mass_summary_GeV"):
        result = copy.deepcopy(original)
        if field == "histogram":
            result[field]["counts"][0] += 1
        elif field == "cut_flow":
            result[field][-1]["remaining"] += 1
        else:
            result[field]["mean"] += 1
        assert compare(parse(raw), result, views)["comparison_outcome"] == "MISMATCH"
    original["scientific_validation_status"] = "VALIDATED"
    with pytest.raises(Hold, match="scientific-status"):
        compare(parse(raw), original, views)


def test_row_identity_and_finite_value_refusals():
    raw = preflight.synthetic_csv()
    result, views = candidate.probe(raw)
    with pytest.raises(Hold, match="identities"):
        compare(parse(raw), result, list(reversed(views)))
    views[0]["mass"] = float("nan")
    with pytest.raises(Hold, match="finite"):
        compare(parse(raw), result, views)


def test_histogram_conventions_and_one_ulp_edge_gate():
    edges = [float(edge) for edge in ideal_edges()]
    assert checked_edges(edges) == edges
    assert bin_index(3.0, edges) == 20
    assert bin_index(5.0, edges) == 59
    assert bin_index(1.9, edges) is None
    assert (
        bin_index(
            Decimal("2.99999999999999999"), [Decimal.from_float(e) for e in edges]
        )
        == 19
    )
    edges[1] = math.nextafter(edges[1], math.inf)
    checked_edges(edges)
    edges[1] = math.nextafter(edges[1], math.inf)
    with pytest.raises(Hold, match="one-ULP"):
        checked_edges(edges)
    with pytest.raises(Hold):
        checked_edges(None)


def test_counterexample_limit_preserves_trigger_and_marks_incomplete(monkeypatch):
    line = csv_fixture().decode().splitlines()[1]
    raw = (",".join(HEADER) + "\n" + (line + "\n") * 40).encode()
    result, views = candidate.probe(raw)
    for view in views:
        view["mass"] += 0.01
    evaluated = []
    original = comparison_module.evaluate

    def counted(row, track):
        evaluated.append(row.number)
        return original(row, track)

    monkeypatch.setattr(comparison_module, "evaluate", counted)
    checked = compare(parse(raw), result, views)
    assert checked["comparison_outcome"] == "HOLD" and not checked["complete"]
    assert len(checked["counterexamples"]) == checked["processed_rows"] == 33
    assert max(evaluated) == 33 and len(evaluated) == 99


def retention_case(roles, padded):
    """Original rows: x=excluded, s=selected; capitals inject disagreements."""
    lines = [",".join(HEADER)]
    for number, role in enumerate(roles, 1):
        cells = (
            csv_fixture(
                Run="9223372036854775807",
                Event=number,
                eta1="2.4" if role.lower() == "x" else "0",
            )
            .decode()
            .splitlines()[1]
            .split(",")
        )
        if padded:
            cells = [
                value if key in {"Run", "Event", "type1", "type2"} else value.ljust(128)
                for key, value in zip(HEADER, cells)
            ]
        lines.append(",".join(cells))
    raw = ("\n".join(lines) + "\n").encode("ascii")
    result, views = candidate.probe(raw)
    for role, view in zip(roles, views):
        if role == "S":
            view["mass"] += 0.01
        elif role == "X":
            view["first_failure"] = "source_opposite_sign"
    return raw, result, views


@pytest.mark.parametrize("padded", [False, True], ids=["minimal", "max-cells"])
@pytest.mark.parametrize(
    "roles,processed,reason",
    [
        ("x" + "S" * 33 + "ss", 34, "counterexample_limit_reached"),
        ("x" * 32 + "Xss", 33, "exclusion_detail_limit_reached"),
        ("SS" + "x" * 32 + "Xss", 35, "exclusion_detail_limit_reached"),
        ("X" * 33 + "ss", 33, "exclusion_detail_limit_reached"),
        ("xS" * 32 + "Sss", 65, "counterexample_limit_reached"),
        ("S" * 33 + "x" * 33, 33, "counterexample_limit_reached"),
        ("x" * 33 + "S" * 33, 33, "exclusion_detail_limit_reached"),
    ],
    ids=[
        "hr001-prior-exclusion",
        "hr002-trigger-disagreement",
        "prior-and-trigger-disagreements",
        "simultaneous-limits",
        "interleaved-stream",
        "counterexample-limit-first",
        "exclusion-limit-first",
    ],
)
def test_early_stop_retains_both_collections_and_trigger_within_limits(
    roles, processed, reason, padded, tmp_path, monkeypatch
):
    raw, result, views = retention_case(roles, padded)
    before_views = copy.deepcopy(views)
    evaluated = []
    original = comparison_module.evaluate

    def counted(row, track):
        evaluated.append(row.number)
        return original(row, track)

    monkeypatch.setattr(comparison_module, "evaluate", counted)
    checked = compare(parse(raw), result, views)
    assert checked["comparison_outcome"] == "HOLD" and checked["complete"] is False
    assert checked["processed_rows"] == processed and checked["reason"] == reason
    assert max(evaluated) == processed and len(evaluated) == 3 * processed
    assert views == before_views
    prefix = roles[:processed]
    assert [row["data_row"] for row in checked["exclusions"]] == [
        i for i, role in enumerate(prefix, 1) if role.lower() == "x"
    ]
    assert [row["data_row"] for row in checked["counterexamples"]] == [
        i for i, role in enumerate(prefix, 1) if role.isupper()
    ]
    assert len(checked["exclusions"]) <= 33
    assert len(checked["counterexamples"]) <= 33
    for row in checked["counterexamples"]:
        assert row["candidate"] == views[row["data_row"] - 1]
        assert row["reasons"] and len(json_bytes(row)) <= 4096
    for key, value in SCIENTIFIC.items():
        assert checked[key] == value
    payload = json_bytes(checked)
    assert len(payload) <= BUCKETS["records/comparison"]
    store = Store(tmp_path / "retained")
    target = store.write("records/comparison", "partial.json", payload)
    store.finish("supervisor", {"state": "HOLD", "reason": reason})
    receipt = store.inventory()
    assert read_json(target) == checked
    assert store.audit()["bucket_bytes"]["records/comparison"] == len(payload)
    assert receipt["total_bytes"] == sum(
        path.stat().st_size for path in store.root.rglob("*") if path.is_file()
    )
    assert receipt["total_bytes"] <= TOTAL_BYTES


@pytest.mark.parametrize("padded", [False, True], ids=["minimal", "max-cells"])
def test_below_detail_limits_keeps_complete_comparison_behavior(padded):
    raw, result, views = retention_case("x" * 32 + "S" * 32, padded)
    checked = compare(parse(raw), result, views)
    assert checked["comparison_outcome"] == "MISMATCH"
    assert checked["complete"] is True and checked["input_rows"] == 64
    assert len(checked["exclusions"]) == len(checked["counterexamples"]) == 32
    assert len(checked["reference_stream_sha256"]) == 3
    assert not checked["aggregate_failures"]


def test_store_reserves_full_receipt_and_log_allowance_before_controls(tmp_path):
    store = Store(tmp_path / "retained")
    assert store.audit()["bucket_bytes"]["records/logs"] == BUCKETS["records/logs"]
    assert store.audit()["total_bytes"] == 192 * 1024
    started = (store.root / "records/logs/supervisor-started.json").read_bytes()
    store.finish(
        "supervisor",
        {
            "state": "HOLD",
            "qualification_outcome": "VALIDATED",
            "scientific_validation_status": "VALIDATED",
        },
    )
    final = read_json(store.root / "records/logs/supervisor-final.json")
    assert final["qualification_outcome"] == "NOT_EXECUTED"
    assert final["scientific_validation_status"] == "NOT_ESTABLISHED"
    assert (store.root / "records/logs/supervisor-started.json").read_bytes() == started
    assert len(started) == SLOT_BYTES


def test_bucket_limits_copies_unallocated_files_and_immutable_writes(tmp_path):
    store = Store(tmp_path / "retained")
    store.write("input", "one.bin", b"x" * (2 * 1024 * 1024))
    with pytest.raises(FileExistsError):
        store.write("input", "one.bin", b"x")
    store.write("input", "transport-copy.bin", b"x" * (2 * 1024 * 1024))
    with pytest.raises(Hold, match="allocation"):
        store.write("input", "extra.bin", b"x")
    (store.root / "unallocated.bin").write_bytes(b"x")
    with pytest.raises(Hold, match="Unallocated"):
        store.audit()
    assert (store.root / "input/one.bin").exists()
    assert (store.root / "input/transport-copy.bin").exists()


def test_identity_read_limits_paths_and_no_overwrite(tmp_path):
    path = tmp_path / "data"
    path.write_bytes(b"123")
    assert read_regular(path, 3) == b"123"
    with pytest.raises(Hold):
        read_regular(path, 2)
    with pytest.raises(Hold, match="parent traversal"):
        literal(tmp_path / "link" / ".." / "data")
    with pytest.raises(Hold):
        Store(tmp_path)
    with pytest.raises(Hold, match="SHA-256"):
        candidate.wheel_identity(path, ROOT)


def test_inventory_counts_itself_padding_and_every_file(tmp_path):
    store = Store(tmp_path / "retained")
    store.write("records/source", "fixture.txt", b"fixture")
    store.finish("supervisor", {"state": "PREFLIGHT_PASSED"})
    receipt = store.inventory()
    inventory_path = store.root / "records/integrity/inventory.json"
    raw = inventory_path.read_bytes()
    inventory = json.loads(raw)
    assert receipt["sha256"] == hashlib.sha256(raw).hexdigest()
    actual = retained_files(store.root)
    assert set(actual) == set(inventory["files"]) | {"records/integrity/inventory.json"}
    assert (
        receipt["total_bytes"]
        == inventory["total_retained_bytes"]
        == sum(map(len, actual.values()))
    )
    assert inventory["inventory_bytes"] == len(raw)
    for name, entry in inventory["files"].items():
        assert entry == {
            "bytes": len(actual[name]),
            "sha256": hashlib.sha256(actual[name]).hexdigest(),
        }


@pytest.mark.parametrize("error_type", [PermissionError, FileNotFoundError, OSError])
@pytest.mark.parametrize("directory", ["", "input/nested"])
@pytest.mark.parametrize("operation", ["audit", "audit_existing", "inventory", "write"])
def test_enumeration_failure_refuses_incomplete_accounting(
    tmp_path, monkeypatch, error_type, directory, operation
):
    store = Store(tmp_path / "retained")
    store.write("input", "nested/fixture.bin", b"retained synthetic input")
    before = retained_files(store.root)
    denied = store.root / directory
    original_scandir = os.scandir
    error = error_type("private filesystem exception detail")

    def failing_scandir(path):
        if Path(path) == denied:
            raise error
        return original_scandir(path)

    with monkeypatch.context() as patch:
        patch.setattr(retention.os, "scandir", failing_scandir)
        with pytest.raises(Hold, match="enumeration") as refused:
            if operation == "audit_existing":
                audit_existing(store.root)
            elif operation == "write":
                store.write("input", "must-not-exist.bin", b"new bytes")
            else:
                getattr(store, operation)()

    assert refused.value.__cause__ is error
    assert "private filesystem exception detail" not in str(refused.value)
    after = retained_files(store.root)
    assert after == before
    assert not (store.root / "records/integrity/inventory.json").exists()
    assert store.audit()["bucket_bytes"]["input"] == len(
        before["input/nested/fixture.bin"]
    )


@pytest.mark.parametrize("directory", ["", "input/nested"])
@pytest.mark.parametrize("failure_scan", [2, 3])
def test_inventory_refuses_later_enumeration_failure_and_retains_partial_files(
    tmp_path, monkeypatch, directory, failure_scan
):
    store = Store(tmp_path / "retained")
    store.write("input", "nested/fixture.bin", b"retained synthetic input")
    before = retained_files(store.root)
    denied = store.root / directory
    original_scandir = os.scandir
    scans = 0
    error = PermissionError("private filesystem exception detail")

    def failing_scandir(path):
        nonlocal scans
        if Path(path) == denied:
            scans += 1
            if scans == failure_scan:
                raise error
        return original_scandir(path)

    with monkeypatch.context() as patch:
        patch.setattr(retention.os, "scandir", failing_scandir)
        with pytest.raises(Hold, match="enumeration") as refused:
            store.inventory()

    assert scans == failure_scan
    assert refused.value.__cause__ is error
    assert "private filesystem exception detail" not in str(refused.value)
    after = retained_files(store.root)
    assert {name: after[name] for name in before} == before
    # A failed final scan must preserve the written partial inventory, not retry
    # or return a success receipt. A failure before writing must create none.
    inventory_name = "records/integrity/inventory.json"
    assert set(after) - set(before) == (
        {inventory_name} if failure_scan == 3 else set()
    )
    assert store.audit()["total_bytes"] == sum(map(len, after.values()))


def test_synthetic_preflight_including_timeout_overflow_and_drift(tmp_path):
    result = preflight.run_preflight(tmp_path / "preflight")
    assert result["preflight_outcome"] == "PREFLIGHT_PASSED"
    assert result["qualification_outcome"] == "NOT_EXECUTED"
    assert result["pilot_execution_ready"] is False
    assert result["candidate_identity"]["state"] == "NOT_CHECKED"
    assert result["controls"]["timeout"]["reason"] == "TIMEOUT"
    assert result["controls"]["overflow"]["reason"] == "LOG_LIMIT"
    assert result["controls"]["overflow"]["log_bytes_used"] == LOG_BYTES
    assert result["controls"]["overflow"]["overflow_byte_hex"] == "58"
    assert result["controls"]["drift"]["reason"] == "SOURCE_DRIFT"
    assert (
        result["controls"]["drift"]["source_before"]
        != result["controls"]["drift"]["source_after"]
    )
    assert result["inventory"]["total_bytes"] < TOTAL_BYTES
    assert not list((tmp_path / "preflight/input").iterdir())
    assert not list((tmp_path / "preflight/windows").iterdir())
    assert not list((tmp_path / "preflight/linux").iterdir())


def test_preflight_failure_retains_initial_final_and_partial_source(tmp_path):
    bad_wheel = tmp_path / "not-a-wheel"
    bad_wheel.write_bytes(b"not a wheel")
    output = tmp_path / "failed"
    with pytest.raises(Hold):
        preflight.run_preflight(output, bad_wheel)
    assert (
        read_json(output / "records/logs/supervisor-started.json")["state"] == "STARTED"
    )
    assert read_json(output / "records/logs/supervisor-final.json")["state"] == "HOLD"
    assert (
        output / "records/source/research/cern_dimuon_qualification/reference.py"
    ).exists()
    with pytest.raises(Hold, match="no overwrite"):
        preflight.run_preflight(output, bad_wheel)


@pytest.mark.parametrize("argument", ["--input", "--execute", "--pilot"])
def test_cli_has_no_actual_dataset_or_pilot_entrypoint(argument):
    completed = subprocess.run(
        [
            sys.executable,
            "-B",
            "-m",
            "research.cern_dimuon_qualification.preflight",
            argument,
            "forbidden",
        ],
        cwd=ROOT,
        capture_output=True,
        timeout=10,
    )
    assert completed.returncode == 2
    assert b"unrecognized arguments" in completed.stderr


def test_worker_validation_and_source_distribution_contract(tmp_path):
    from research.cern_dimuon_qualification.supervision import run_worker

    store = Store(tmp_path / "root")
    for mode, timeout in (
        ("unknown", 1),
        ("normal", 301),
        ("normal", float("nan")),
        ("normal", True),
    ):
        with pytest.raises(Hold):
            run_worker(store, mode, timeout)
    assert (
        "recursive-include research/cern_dimuon_qualification *.py *.json"
        in (ROOT / "MANIFEST.in").read_text()
    )


@pytest.mark.skipif(
    os.name == "nt", reason="Windows symlink privileges are not assumed"
)
def test_link_and_hardlink_refusal(tmp_path):
    source = tmp_path / "source"
    source.write_bytes(b"source")
    linked = tmp_path / "linked"
    linked.symlink_to(source)
    with pytest.raises(Hold):
        read_regular(linked, 100)
    hard = tmp_path / "hard"
    os.link(source, hard)
    with pytest.raises(Hold):
        read_regular(hard, 100)
