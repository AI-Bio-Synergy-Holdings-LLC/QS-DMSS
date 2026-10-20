"""external_dimuon_v1: analytic, admission, retention, CLI and integrity contracts."""

from __future__ import annotations

import io
import json
import math
import os
import re
import struct
import zipfile
from pathlib import Path

import numpy as np
import pytest

from qs_dmss.cli import main
from qs_dmss.external_data import evidence
from qs_dmss.external_data.admission import admit_csv
from qs_dmss.external_data.analysis import analyze
from qs_dmss.external_data.contracts import (
    HEADER,
    MAX_BINS,
    MAX_BUNDLE_BYTES,
    MAX_INPUT_BYTES,
    MAX_RECORD_BYTES,
    MAX_ROWS,
    SCHEMA,
    SOURCE,
    AnalysisProfile,
    EvidenceError,
)
from qs_dmss.external_data.evidence import run_analysis, verify_bundle
from qs_dmss.external_data.reporting import render_report
from qs_dmss.external_data.storage import (
    decode_json,
    json_bytes,
    literal_path,
    read_snapshot,
    sha256,
)


def row(mass=3.0, **changes):
    """Synthetic back-to-back vectors; not a copied CMS event or collision claim."""
    values = dict(
        zip(
            HEADER,
            (
                "1",
                "1",
                "G",
                str(mass / 2),
                "0.5",
                "0",
                "0",
                "0.5",
                "0",
                "0",
                "1",
                "T",
                str(mass / 2),
                "-0.5",
                "0",
                "0",
                "0.5",
                "0",
                "3.14159265",
                "-1",
            ),
        )
    )
    values.update({name: str(value) for name, value in changes.items()})
    return ",".join(values[name] for name in HEADER)


def csv_bytes(*rows):
    return (",".join(HEADER) + "\n" + "\n".join(rows) + "\n").encode("ascii")


@pytest.fixture
def input_file(tmp_path):
    path = tmp_path / "synthetic.csv"
    path.write_bytes(csv_bytes(row(3), row(4)))
    return path


def run(input_file, target, **kwargs):
    return run_analysis(
        input_file, target, kind="synthetic", profile=AnalysisProfile(), **kwargs
    )


def read_archive(path):
    with zipfile.ZipFile(path) as archive:
        return {name: archive.read(name) for name in archive.namelist()}


def archive_bytes(files, *, compression=zipfile.ZIP_STORED):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=compression) as archive:
        for name, data in files.items():
            archive.writestr(name, data)
    return buffer.getvalue()


def test_analytic_reconstruction_histogram_and_cut_accounting():
    raw = csv_bytes(
        row(3),
        row(4),
        row(3, Q2=1),
        row(3, type1="T"),
        row(3, eta1=2.4),
        row(2),
        row(5),
        row(3, E1="nan"),
        row(3, E1="bad"),
    )
    admitted = admit_csv(raw, "synthetic", sha256(raw))
    result = analyze(admitted, AnalysisProfile(bins=3))
    assert result["selected_events"] == 2
    assert result["histogram"] == {
        "unit": "GeV",
        "counts": [0, 1, 1],
        "edges": [2.0, 3.0, 4.0, 5.0],
        "weighted": False,
    }
    assert result["mass_summary_GeV"] == {
        "minimum": 3.0,
        "maximum": 4.0,
        "mean": 3.5,
        "population_std": 0.5,
    }
    counts = result["cut_flow"]
    assert counts[0]["remaining"] == 9
    assert counts[-1]["remaining"] == 2
    assert sum(item["rejected"] for item in counts) + 2 == 9
    assert result["invalid_rows_first_failure"] == {
        "invalid_numeric": 1,
        "nonfinite_or_out_of_range": 1,
        "invalid_category_or_identity": 0,
    }
    assert admitted.source["observation_label"] == "SYNTHETIC_NOT_COLLISION_DATA"
    assert admitted.source["provider_reference"]["doi"] is None
    assert result["scientific_validation_status"] == "NOT_ESTABLISHED"
    assert result["independent_scientific_review"] == "PENDING"
    assert result["human_disposition"] == "PENDING"
    assert result["ai_advice"] is None


def test_vectorized_matches_independent_scalar_reference():
    generator = np.random.default_rng(14)
    rows, scalar = [], []
    for _ in range(100):
        momentum = generator.normal(0, 0.3, size=(2, 3))
        energy = [
            math.sqrt(sum(float(p) ** 2 for p in vector) + 1.5**2)
            for vector in momentum
        ]
        m2 = sum(energy) ** 2 - sum(
            (float(momentum[0, i]) + float(momentum[1, i])) ** 2 for i in range(3)
        )
        scalar.append(math.sqrt(m2))
        changes = {
            f"{axis}{i + 1}": momentum[i, j]
            for i in range(2)
            for j, axis in enumerate(("px", "py", "pz"))
        }
        rows.append(row(E1=energy[0], E2=energy[1], **changes))
    result = analyze(admit_csv(csv_bytes(*rows), "synthetic"), AnalysisProfile())
    assert result["selected_events"] == 100
    assert result["mass_summary_GeV"]["mean"] == pytest.approx(
        sum(scalar) / 100, rel=1e-14
    )
    assert (
        result["histogram"]["counts"]
        == np.histogram(scalar, bins=60, range=(2, 5))[0].tolist()
    )


def test_material_negative_mass_is_rejected_not_blindly_clamped():
    raw = csv_bytes(
        row(E1=1, E2=1, px1=3, px2=0), row(E1=1, E2=1, px1=2.0000000000000004, px2=0)
    )
    result = analyze(admit_csv(raw, "synthetic"), AnalysisProfile())
    assert result["roundoff_clamped_rows_before_cuts"] == 1
    assert result["cut_flow"][2] == {
        "stage": "nonnegative_mass_squared_with_roundoff_policy",
        "remaining": 1,
        "rejected": 1,
    }
    assert result["workflow_outcome"] == "COMPLETED_NO_SELECTED_EVENTS"
    assert all(value is None for value in result["mass_summary_GeV"].values())
    assert sum(result["histogram"]["counts"]) == 0


def test_profiles_change_recorded_selection_not_solver_calls(monkeypatch):
    from qs_dmss.core.fractal_ssfm import FractalQuadrantSSFMSolver

    def forbidden(*args, **kwargs):
        pytest.fail("External data must not invoke solver evolution.")

    monkeypatch.setattr(FractalQuadrantSSFMSolver, "run", forbidden)
    admitted = admit_csv(csv_bytes(row(3), row(4, pt1=0.1)), "synthetic")
    assert analyze(admitted, AnalysisProfile(pt_min=0.2))["selected_events"] == 1
    assert analyze(admitted, AnalysisProfile(mass_min=3.5))["selected_events"] == 1


@pytest.mark.parametrize(
    "kwargs",
    [
        {"bins": 0},
        {"bins": 101},
        {"bins": True},
        {"bins": 2.0},
        {"mass_min": float("nan")},
        {"mass_max": float("inf")},
        {"pt_min": -1},
        {"mass_min": 1.9},
        {"mass_max": 5.1},
        {"mass_min": 4, "mass_max": 3},
        {"pt_min": 10001},
        {"pt_min": "2"},
    ],
)
def test_profile_bounds(kwargs):
    with pytest.raises(EvidenceError):
        AnalysisProfile(**kwargs)


@pytest.mark.parametrize(
    "raw",
    [
        b"",
        b"wrong\n",
        csv_bytes(),
        csv_bytes(row()).replace(b"type1", b"Type1"),
        csv_bytes(row()).replace(b",Q2\n", b",Q2,M\n"),
        csv_bytes(row()) + b"\n",
        csv_bytes(row()) + b"bad\n",
        csv_bytes(row()).replace(b"1,1,G,", b'1,1,"G,', 1),
        csv_bytes(row()).replace(b"1,1,G,", b'1,1,"G\nG",', 1),
        csv_bytes(row()).replace(b"1,1,G,", b"1,1,\x00,", 1),
        csv_bytes(row()).replace(b"1,1,G,", b"1,1,\xff,", 1),
        csv_bytes(row(type1="X" * 129)),
        b"x" * 4097,
        b"x" * (MAX_INPUT_BYTES + 1),
    ],
    ids=lambda value: f"bytes-{len(value)}",
)
def test_malformed_csv_refusal(raw):
    with pytest.raises(EvidenceError):
        admit_csv(raw, "synthetic")


@pytest.mark.parametrize(
    "changes,reason",
    [
        ({"Q1": 0}, "invalid_category_or_identity"),
        ({"type1": "X"}, "invalid_category_or_identity"),
        ({"Run": "-1"}, "invalid_category_or_identity"),
        ({"Event": 2**63}, "invalid_category_or_identity"),
        ({"E1": -1}, "invalid_category_or_identity"),
        ({"pt1": -1}, "invalid_category_or_identity"),
        ({"E1": 1e7}, "nonfinite_or_out_of_range"),
        ({"E1": "inf"}, "nonfinite_or_out_of_range"),
    ],
)
def test_invalid_rows_are_counted(changes, reason):
    admitted = admit_csv(csv_bytes(row(**changes)), "synthetic")
    assert admitted.invalid_rows[reason] == 1
    result = analyze(admitted, AnalysisProfile())
    assert result["selected_events"] == 0


def test_maximum_rows_and_one_over():
    data = csv_bytes(*([row()] * MAX_ROWS))
    assert len(data) < MAX_INPUT_BYTES
    assert admit_csv(data, "synthetic").row_count == MAX_ROWS
    with pytest.raises(EvidenceError, match="25000"):
        admit_csv(data + (row() + "\n").encode(), "synthetic")


def test_source_metadata_match_does_not_become_source_authentication(monkeypatch):
    raw = csv_bytes(row())
    with pytest.raises(EvidenceError, match="provider size"):
        admit_csv(raw, "cms-record-5203")
    import zlib

    monkeypatch.setitem(SOURCE, "size_bytes", len(raw))
    monkeypatch.setitem(SOURCE, "adler32", f"{zlib.adler32(raw):08x}")
    with pytest.raises(EvidenceError, match="snapshot SHA-256"):
        admit_csv(raw, "cms-record-5203")
    monkeypatch.setitem(SOURCE, "maintainer_observed_sha256", sha256(raw))
    with pytest.raises(EvidenceError, match="row count"):
        admit_csv(raw, "cms-record-5203")
    monkeypatch.setitem(SOURCE, "events", 1)
    admitted = admit_csv(raw, "cms-record-5203")
    assert admitted.source["provider_metadata_match"] is True
    assert (
        "not cryptographic source authentication" in admitted.source["identity_scope"]
    )
    assert admitted.source["observation_label"].startswith("CALLER_DECLARED")


@pytest.mark.parametrize(
    "kind,digest",
    [
        ("unknown", None),
        ("synthetic", "F" * 64),
        ("synthetic", 2),
        ("synthetic", "0" * 64),
    ],
)
def test_kind_and_hash_admission(kind, digest):
    with pytest.raises(EvidenceError):
        admit_csv(csv_bytes(row()), kind, digest)


def test_immutable_export_recompute_and_source_preservation(input_file, tmp_path):
    original = input_file.read_bytes()
    target = tmp_path / "analysis"
    result = run(
        input_file,
        target,
        expected_sha256=sha256(original),
        source_commit="a" * 40,
        candidate_wheel_sha256="b" * 64,
    )
    assert result["success"] is True
    assert result["selected_events"] == 2
    files = read_archive(result["bundle"])
    assert set(files) == evidence.ARCHIVE_FILES
    assert input_file.read_bytes() == original == files["input.csv"]
    for name, raw in files.items():
        assert (target / name).read_bytes() == raw
    receipt = json.loads(files["receipt.json"])
    assert receipt["state"] == "COMPLETED"
    assert receipt["declared_artifact_identity"]["scope"].startswith("caller_declared")
    assert receipt["implementation_sha256"]["analysis.py"] == sha256(
        Path(evidence.__file__).with_name("analysis.py").read_bytes()
    )
    assert verify_bundle(result["bundle"])["recomputation"] == "NOT_RUN"
    assert (
        verify_bundle(result["bundle"], recompute=True)["recomputation"]
        == "MATCHED_CURRENT_IMPLEMENTATION"
    )
    before = {path.name: path.read_bytes() for path in target.iterdir()}
    with pytest.raises(EvidenceError, match="existing directory"):
        run(input_file, target)
    assert before == {path.name: path.read_bytes() for path in target.iterdir()}
    empty = tmp_path / "empty"
    empty.mkdir()
    with pytest.raises(EvidenceError):
        run(input_file, empty)
    assert not list(empty.iterdir())


@pytest.mark.parametrize(
    "mode",
    [
        "bad_csv",
        "wrong_hash",
        "missing",
        "too_large",
        "analysis_error",
        "interrupted",
        "export_error",
        "record_budget",
        "bundle_budget",
        "retention_budget",
    ],
)
def test_failure_receipt_reserved_and_evidence_retained(
    input_file, tmp_path, monkeypatch, mode
):
    if mode == "bad_csv":
        input_file.write_bytes(b"bad\n")
    if mode == "too_large":
        input_file.write_bytes(b"x" * (MAX_INPUT_BYTES + 1))
    if mode == "missing":
        input_file.unlink()
    if mode in {"analysis_error", "interrupted"}:

        def fail(*args):
            assert (
                json.loads((tmp_path / "failed" / "receipt.json").read_bytes())["state"]
                == "STARTED"
            )
            raise (
                KeyboardInterrupt()
                if mode == "interrupted"
                else RuntimeError("DO_NOT_LEAK_SECRET")
            )

        monkeypatch.setattr(evidence, "analyze", fail)
    if mode == "export_error":
        original = evidence.write_new

        def fail_export(path, raw):
            if path.name == "analysis.json":
                raise OSError("DO_NOT_LEAK_SECRET")
            original(path, raw)

        monkeypatch.setattr(evidence, "write_new", fail_export)
    for name, attribute in [
        ("record_budget", "MAX_RECORD_BYTES"),
        ("bundle_budget", "MAX_BUNDLE_BYTES"),
        ("retention_budget", "MAX_RETAINED_BYTES"),
    ]:
        if mode == name:
            monkeypatch.setattr(evidence, attribute, 10)
    target = tmp_path / "failed"
    with pytest.raises(KeyboardInterrupt if mode == "interrupted" else EvidenceError):
        run(
            input_file,
            target,
            expected_sha256="0" * 64 if mode == "wrong_hash" else None,
        )
    receipt = json.loads((target / "receipt.json").read_bytes())
    assert receipt["state"] == "FAILED"
    assert receipt["scientific_validation_status"] == "NOT_ESTABLISHED"
    assert "completed_utc" not in receipt
    assert "DO_NOT_LEAK_SECRET" not in json.dumps(receipt)
    assert not (target / "dimuon-evidence.zip").exists()
    if mode not in {"missing", "too_large"}:
        assert (target / "input.csv").read_bytes() == input_file.read_bytes()


def test_invalid_declarations_and_missing_parent_do_not_create_output(
    input_file, tmp_path
):
    target = tmp_path / "invalid"
    with pytest.raises(EvidenceError):
        run(input_file, target, source_commit="bad")
    assert not target.exists()
    with pytest.raises(EvidenceError, match="parent"):
        run(input_file, tmp_path / "missing" / "analysis")
    with pytest.raises(EvidenceError):
        read_snapshot(tmp_path, MAX_INPUT_BYTES)
    with pytest.raises(EvidenceError):
        read_snapshot("https://example.test/file.csv", MAX_INPUT_BYTES)


def test_symlink_refusal_when_supported(input_file, tmp_path):
    link = tmp_path / "linked.csv"
    try:
        link.symlink_to(input_file)
    except OSError:
        pytest.skip("Host does not permit creation of symlinks.")
    with pytest.raises(EvidenceError, match="Linked"):
        read_snapshot(link, MAX_INPUT_BYTES)
    directory = tmp_path / "linked-directory"
    directory.symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(EvidenceError, match="Linked"):
        read_snapshot(directory / input_file.name, MAX_INPUT_BYTES)
    with pytest.raises(EvidenceError, match="Linked"):
        run(input_file, directory / "analysis")


def test_snapshot_detects_source_drift(input_file, monkeypatch):
    original = os.fstat
    calls = 0

    def drift(fd):
        nonlocal calls
        calls += 1
        info = original(fd)
        if calls == 2:
            from types import SimpleNamespace

            return SimpleNamespace(
                st_dev=info.st_dev,
                st_ino=info.st_ino,
                st_size=info.st_size + 1,
                st_mtime_ns=info.st_mtime_ns,
                st_ctime_ns=info.st_ctime_ns,
            )
        return info

    monkeypatch.setattr(os, "fstat", drift)
    with pytest.raises(EvidenceError, match="changed"):
        read_snapshot(input_file, MAX_INPUT_BYTES)


@pytest.mark.parametrize(
    "mutation",
    [
        "tamper",
        "extra",
        "missing",
        "traversal",
        "compressed",
        "duplicate",
        "malformed_manifest",
        "false_size",
        "false_status",
        "false_profile",
        "false_source",
        "false_result",
    ],
)
def test_verification_rejects_bad_bundles(input_file, tmp_path, mutation):
    result = run(input_file, tmp_path / "analysis")
    files = read_archive(result["bundle"])
    if mutation == "tamper":
        files["input.csv"] += b"x"
    elif mutation == "extra":
        files["extra.txt"] = b"x"
    elif mutation == "missing":
        del files["source.json"]
    elif mutation == "traversal":
        files["../escape.txt"] = b"x"
    elif mutation == "malformed_manifest":
        files["manifest.sha256.json"] = b"[]"
    elif mutation == "false_size":
        manifest = decode_json(files["manifest.sha256.json"])
        manifest["files"]["input.csv"]["size_bytes"] = True
        files["manifest.sha256.json"] = json_bytes(manifest)
    elif mutation in {"false_status", "false_profile", "false_source", "false_result"}:
        name = {
            "false_status": "analysis.json",
            "false_profile": "profile.json",
            "false_source": "source.json",
            "false_result": "analysis.json",
        }[mutation]
        document = decode_json(files[name])
        key = {
            "false_status": "scientific_validation_status",
            "false_profile": "method",
            "false_source": "input_sha256",
            "false_result": "selected_events",
        }[mutation]
        document[key] = "VALIDATED" if mutation != "false_result" else 99
        files[name] = json_bytes(document)
        manifest = decode_json(files["manifest.sha256.json"])
        manifest["files"][name] = {
            "sha256": sha256(files[name]),
            "size_bytes": len(files[name]),
        }
        files["manifest.sha256.json"] = json_bytes(manifest)
    bundle = tmp_path / "bad.zip"
    bundle.write_bytes(
        archive_bytes(
            files,
            compression=zipfile.ZIP_DEFLATED
            if mutation == "compressed"
            else zipfile.ZIP_STORED,
        )
    )
    if mutation == "duplicate":
        with pytest.warns(UserWarning), zipfile.ZipFile(bundle, "a") as archive:
            archive.writestr("input.csv", b"duplicate")
    with pytest.raises(EvidenceError):
        verify_bundle(bundle, recompute=mutation == "false_result")
    assert not (tmp_path.parent / "escape.txt").exists()


@pytest.mark.parametrize(
    "raw", [b"not a zip", b"x" * (MAX_BUNDLE_BYTES + 1)], ids=["not-zip", "oversized"]
)
def test_bad_or_oversized_archive(raw, tmp_path):
    path = tmp_path / "bad.zip"
    path.write_bytes(raw)
    with pytest.raises(EvidenceError):
        verify_bundle(path)


@pytest.mark.parametrize(
    "raw",
    [
        b'{"x":1,"x":2}',
        b'{"x":NaN}',
        b'{"x":1e999}',
        b"\xff",
        b"[" * 20 + b"0" + b"]" * 20,
    ],
)
def test_strict_json(raw):
    with pytest.raises(EvidenceError):
        decode_json(raw)


def test_json_rejects_escaped_surrogate():
    with pytest.raises(EvidenceError):
        decode_json(b'{"x":"\\ud800"}')


def test_reparse_point_refusal_without_symlink_privileges(input_file, monkeypatch):
    from types import SimpleNamespace

    original = Path.lstat

    def reparse(path, *args, **kwargs):
        info = original(path, *args, **kwargs)
        if path == input_file:
            return SimpleNamespace(st_mode=info.st_mode, st_file_attributes=0x400)
        return info

    monkeypatch.setattr(Path, "lstat", reparse)
    with pytest.raises(EvidenceError, match="reparse"):
        read_snapshot(input_file, MAX_INPUT_BYTES)


def test_recompute_refuses_nonstring_kind(input_file, tmp_path):
    result = run(input_file, tmp_path / "analysis")
    files = read_archive(result["bundle"])
    for name in ("source.json", "receipt.json"):
        document = decode_json(files[name])
        document["input_kind"] = []
        files[name] = json_bytes(document)
    manifest = decode_json(files["manifest.sha256.json"])
    for name in ("source.json", "receipt.json"):
        manifest["files"][name] = {
            "size_bytes": len(files[name]),
            "sha256": sha256(files[name]),
        }
    files["manifest.sha256.json"] = json_bytes(manifest)
    bundle = tmp_path / "bad-kind.zip"
    bundle.write_bytes(archive_bytes(files))
    with pytest.raises(EvidenceError, match="Input kind"):
        verify_bundle(bundle, recompute=True)


def test_report_is_accessible_static_escaped_and_truthful():
    from qs_dmss.external_data.reporting import STYLE

    assert STYLE.startswith(":root")
    admitted = admit_csv(csv_bytes(row()), "synthetic")
    result = analyze(admitted, AnalysisProfile())
    source = {**admitted.source, "observation_label": '<script>alert("x")</script>'}
    report = render_report(result, AnalysisProfile().document(), source).decode()
    assert "<script" not in report and "&lt;script&gt;" in report
    assert 'lang="en"' in report and 'name="viewport"' in report
    assert report.count('role="img"') == 2
    assert 'scope="col"' in report and 'scope="row"' in report and "<caption>" in report
    assert "mobile-chart" in report and "default-src 'none'" in report
    assert "uncertainty estimate" in report and "not an independent discovery" in report
    assert "NOT_ESTABLISHED" in report and "gate #183 are unchanged" in report


def test_cli_end_to_end_and_errors(input_file, tmp_path, capsys):
    target = tmp_path / "cli"
    assert (
        main(
            [
                "external-data",
                "dimuon",
                "--input",
                str(input_file),
                "--output",
                str(target),
                "--input-kind",
                "synthetic",
                "--bins",
                "10",
            ]
        )
        == 0
    )
    output = json.loads(capsys.readouterr().out)
    assert output["success"]
    assert main(["external-data", "verify", output["bundle"], "--recompute"]) == 0
    assert (
        json.loads(capsys.readouterr().out)["recomputation"]
        == "MATCHED_CURRENT_IMPLEMENTATION"
    )
    assert (
        main(
            [
                "external-data",
                "dimuon",
                "--input",
                str(input_file),
                "--output",
                str(tmp_path / "no"),
                "--input-kind",
                "synthetic",
                "--bins",
                "101",
            ]
        )
        == 1
    )
    assert json.loads(capsys.readouterr().out)["success"] is False
    assert main(["external-data", "verify", str(tmp_path / "missing.zip")]) == 1
    assert json.loads(capsys.readouterr().out)["success"] is False


def test_records_stay_within_contract(input_file, tmp_path):
    result = run(input_file, tmp_path / "bounded")
    files = read_archive(result["bundle"])
    assert (
        sum(len(raw) for name, raw in files.items() if name != "input.csv")
        < MAX_RECORD_BYTES
    )
    assert json.loads(files["analysis.json"])["schema_version"] == SCHEMA


@pytest.mark.parametrize("field", ["mass_min", "mass_max", "pt_min"])
@pytest.mark.parametrize("sign", [1, -1], ids=["positive", "negative"])
@pytest.mark.parametrize("recompute", [False, True], ids=["integrity", "recompute"])
def test_oversized_integer_threshold_is_json_refusal(
    input_file, tmp_path, capsys, field, sign, recompute
):
    saved = run(input_file, tmp_path / "original")
    original = Path(saved["bundle"]).read_bytes()
    files = read_archive(saved["bundle"])
    profile = decode_json(files["profile.json"])
    profile[field] = sign * 10**400
    files["profile.json"] = json_bytes(profile)
    receipt = decode_json(files["receipt.json"])
    receipt["requested_profile"] = profile
    files["receipt.json"] = json_bytes(receipt)
    manifest = decode_json(files["manifest.sha256.json"])
    for name in ("profile.json", "receipt.json"):
        manifest["files"][name] = {
            "sha256": sha256(files[name]),
            "size_bytes": len(files[name]),
        }
    files["manifest.sha256.json"] = json_bytes(manifest)
    malformed = tmp_path / "oversized-threshold.zip"
    malformed.write_bytes(archive_bytes(files))
    with pytest.raises(EvidenceError, match="Mass window"):
        verify_bundle(malformed, recompute=recompute)
    arguments = ["external-data", "verify", str(malformed)]
    if recompute:
        arguments.append("--recompute")
    assert main(arguments) == 1
    output = capsys.readouterr()
    assert json.loads(output.out)["success"] is False
    assert "Traceback" not in output.err
    assert Path(saved["bundle"]).read_bytes() == original


@pytest.mark.parametrize(
    "invalid_byte", [0xFF, 0xC3], ids=["invalid-start", "truncated-utf8"]
)
def test_invalid_utf8_zip_filename_is_json_refusal(tmp_path, capsys, invalid_byte):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("a", b"x")
    raw = bytearray(buffer.getvalue())
    central = raw.index(b"PK\x01\x02")
    # General-purpose bit 11 declares UTF-8 names in both ZIP headers.
    struct.pack_into("<H", raw, 6, 0x800)
    struct.pack_into("<H", raw, central + 8, 0x800)
    raw[30] = invalid_byte
    raw[central + 46] = invalid_byte
    with pytest.raises(UnicodeDecodeError):
        zipfile.ZipFile(io.BytesIO(raw))
    malformed = tmp_path / "invalid-name.zip"
    malformed.write_bytes(raw)
    with pytest.raises(EvidenceError, match="cannot be read safely"):
        verify_bundle(malformed)
    assert main(["external-data", "verify", str(malformed)]) == 1
    output = capsys.readouterr()
    assert json.loads(output.out)["success"] is False
    assert "Traceback" not in output.err
    assert malformed.read_bytes() == raw


@pytest.mark.parametrize("bins", [2, 60, MAX_BINS])
def test_narrow_report_interval_labels_round_trip(bins):
    profile = AnalysisProfile(bins=bins, mass_min=3.000000001, mass_max=3.000000003)
    admitted = admit_csv(csv_bytes(row(3.000000002)), "synthetic")
    result = analyze(admitted, profile)
    report = render_report(result, profile.document(), admitted.source).decode()
    labels = [
        value
        for value in re.findall(r'<th scope="row">([^<]+)</th>', report)
        if " to " in value and value[0].isdigit()
    ]
    edges = result["histogram"]["edges"]
    assert len(labels) == bins == len(set(labels))
    for index, label in enumerate(labels):
        left, right = label.split(" to ")
        assert float(left) == edges[index]
        assert float(right) == edges[index + 1]
        assert float(left) < float(right)
    assert result["selected_events"] == sum(result["histogram"]["counts"]) == 1
    assert "NOT_ESTABLISHED" in report


def test_parent_traversal_rejected_before_path_normalization(monkeypatch):
    with monkeypatch.context() as patch:

        def forbidden(_path):
            pytest.fail("Parent traversal must be refused before normalization.")

        patch.setattr("qs_dmss.external_data.storage.os.path.abspath", forbidden)
        with pytest.raises(EvidenceError, match="Parent-traversal"):
            literal_path(Path("linked") / ".." / "events.csv")


@pytest.mark.parametrize("relative", [False, True], ids=["absolute", "relative"])
def test_parent_traversal_refuses_input_and_output_without_misdirection(
    input_file, tmp_path, monkeypatch, capsys, relative
):
    monkeypatch.chdir(tmp_path)
    prefix = Path() if relative else tmp_path
    unsafe_input = prefix / "linked" / ".." / input_file.name
    unsafe_output = prefix / "linked" / ".." / "misdirected"
    original = input_file.read_bytes()
    with pytest.raises(EvidenceError, match="Parent-traversal"):
        read_snapshot(unsafe_input, MAX_INPUT_BYTES)
    with pytest.raises(EvidenceError, match="Parent-traversal"):
        run(input_file, unsafe_output)
    assert not (tmp_path / "misdirected").exists()
    assert (
        main(
            [
                "external-data",
                "dimuon",
                "--input",
                str(input_file),
                "--output",
                str(unsafe_output),
                "--input-kind",
                "synthetic",
            ]
        )
        == 1
    )
    assert json.loads(capsys.readouterr().out)["success"] is False
    assert not (tmp_path / "misdirected").exists()
    target = tmp_path / "input-refusal"
    with pytest.raises(EvidenceError, match="Parent-traversal"):
        run(unsafe_input, target)
    receipt = decode_json((target / "receipt.json").read_bytes())
    assert receipt["state"] == "FAILED"
    assert receipt["stage"] == "snapshot"
    assert "Parent-traversal" in receipt["failure_reason"]
    assert not (target / "input.csv").exists()
    assert not (target / "dimuon-evidence.zip").exists()
    assert input_file.read_bytes() == original
