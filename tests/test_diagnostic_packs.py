"""fft_plane_wave_pack_contract_v1: admission, numerical and immutable-export contracts."""

from __future__ import annotations

import copy
import io
import json
import math
import zipfile
from contextlib import nullcontext
from pathlib import Path

import jsonschema
import pytest

from qs_dmss.cli import main
from qs_dmss.diagnostic_packs import fft
from qs_dmss.diagnostic_packs.admission import (
    PackError,
    admit_bytes,
    admit_pack,
    bundled_pack_path,
    decode_json,
    sha256,
)
from qs_dmss.diagnostic_packs.evidence import export_result, json_bytes, verify_bundle
from qs_dmss.diagnostic_packs.models import (
    MAX_BUNDLE_BYTES,
    MAX_FILE_BYTES,
    PackCases,
    PackManifest,
)


@pytest.fixture
def documents():
    root = bundled_pack_path()
    return (
        json.loads((root / "manifest.json").read_bytes()),
        json.loads((root / "cases.json").read_bytes()),
    )


def admitted(documents):
    manifest, cases = documents
    case_bytes = json_bytes(cases)
    manifest = {
        **manifest,
        "content": {"path": "cases.json", "sha256": sha256(case_bytes)},
    }
    return admit_bytes(json_bytes(manifest), case_bytes)


def snapshot(root):
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }


def test_bundled_pack_passes_without_evolution_or_source_changes(monkeypatch):
    original = snapshot(bundled_pack_path())

    def forbidden(*_args, **_kwargs):
        pytest.fail("Evolution must not be called by the data-only diagnostic.")

    monkeypatch.setattr(fft.FractalQuadrantSSFMSolver, "run", forbidden)
    monkeypatch.setattr(fft.FractalQuadrantSSFMSolver, "step", forbidden)
    pack = admit_pack()
    report = fft.evaluate_pack(pack)
    assert report["all_cases_pass"] is True
    assert len(report["case_results"]) == 12
    assert report["numerical_outcome"] == "NOT_FALSIFIED_WITHIN_SCOPE"
    assert report["scientific_validation_status"] == "NOT_ESTABLISHED"
    assert report["human_disposition"] == "PENDING"
    assert report["ai_advice"] is None
    assert report["execution_policy"]["pack_code_executed"] is False
    assert report["execution_policy"]["solver_evolution_called"] is False
    assert report["case_results"][0]["analytic_energy"] == 0
    assert snapshot(bundled_pack_path()) == original


@pytest.mark.parametrize(
    "name,model",
    [("diagnostic-pack-v1", PackManifest), ("diagnostic-pack-cases-v1", PackCases)],
)
def test_packaged_schema_matches_models_and_data(name, model, documents):
    repo = Path(__file__).resolve().parents[1]
    schema = json.loads((repo / "schemas" / f"{name}.schema.json").read_bytes())
    assert schema == {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        **model.model_json_schema(),
    }
    assert schema == json.loads(
        (repo / "src/qs_dmss/assets/schemas" / f"{name}.schema.json").read_bytes()
    )
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.validate(documents[0 if model is PackManifest else 1], schema)


def test_bundled_hash_bytes_are_pinned_to_lf_on_all_platforms():
    repo = Path(__file__).resolve().parents[1]
    attributes = (repo / ".gitattributes").read_text(encoding="utf-8")
    assert "src/qs_dmss/assets/diagnostic-packs/*/*.json text eol=lf" in attributes
    for data in snapshot(bundled_pack_path()).values():
        assert b"\r\n" not in data


@pytest.mark.parametrize(
    "key,value",
    [
        ("schema_version", "v2"),
        ("pack_type", "provider"),
        ("version", "01.0.0"),
        ("version", "1.0.0rc1"),
        ("pack_id", "../outside"),
        ("pack_id", "X"),
        ("diagnostic_id", "eval"),
        ("acceptance_suite", "python test.py"),
        ("dependencies", ["numpy"]),
        ("required_diagnostic_conventions", ["fft_cell_measure_v1"]),
        ("required_diagnostic_conventions", []),
        ("license", "research-only"),
        ("license", "GPL-3.0-only"),
        ("redistribution", "unknown"),
        ("entry_point", "os.system"),
        ("command", "evil"),
        ("title", 3),
        ("evidence_schema_version", "unknown"),
    ],
)
def test_closed_manifest_rejects_unknown_actions_and_invalid_values(
    documents, key, value
):
    documents[0][key] = value
    with pytest.raises(PackError, match="closed pilot schema"):
        admitted(documents)


@pytest.mark.parametrize(
    "path",
    [
        "../cases.json",
        "C:/cases.json",
        "/cases.json",
        "nested/cases.json",
        "cases\\.json",
        "caseS.json",
    ],
)
def test_content_path_is_literal_not_an_extension_loader(documents, path):
    manifest, cases = documents
    data = json_bytes(cases)
    manifest["content"] = {"path": path, "sha256": sha256(data)}
    with pytest.raises(PackError, match="closed pilot schema"):
        admit_bytes(json_bytes(manifest), data)


@pytest.mark.parametrize(
    "version,accepted",
    [
        ("0.13.2", True),
        ("0.14.0", True),
        ("0.13.1", False),
        ("0.15.0", False),
        ("0.14.0rc1", False),
        ("0.14", False),
    ],
)
def test_core_version_interval(documents, version, accepted):
    manifest, cases = documents
    data = json_bytes(cases)
    manifest["content"]["sha256"] = sha256(data)
    if accepted:
        assert admit_bytes(json_bytes(manifest), data, core_version=version)
    else:
        with pytest.raises(PackError):
            admit_bytes(json_bytes(manifest), data, core_version=version)


@pytest.mark.parametrize("values", [("0.14.0", "0.14.0"), ("0.15.0", "0.14.0")])
def test_empty_version_interval_rejected(documents, values):
    documents[0]["supported_core_versions"] = dict(
        zip(("min_inclusive", "max_exclusive"), values)
    )
    with pytest.raises(PackError):
        admitted(documents)


@pytest.mark.parametrize(
    "key,value",
    [
        ("grid_shape", [7, 8]),
        ("grid_shape", [129, 8]),
        ("grid_shape", [True, 8]),
        ("grid_shape", [8, 8, 1]),
        ("grid_shape", ["8", 8]),
        ("modes", [4, 0]),
        ("modes", [-4, 0]),
        ("modes", [False, 0]),
        ("mass", 0),
        ("mass", True),
        ("mass", "1"),
        ("box_size", 1000),
        ("expected_energy", -1),
        ("absolute_tolerance", 0),
        ("relative_tolerance", 1e-3),
        ("case_id", "x|html"),
        ("run_command", "evil"),
    ],
)
def test_bounded_cases_reject_coercion_and_unsafe_controls(documents, key, value):
    documents[1]["cases"][0][key] = value
    with pytest.raises(PackError, match="closed pilot schema"):
        admitted(documents)


@pytest.mark.parametrize(
    "key,value",
    [
        ("max_file_bytes", MAX_FILE_BYTES + 1),
        ("max_cases", 33),
        ("max_grid_cells", 16385),
        ("max_total_grid_cells", 65537),
        ("max_cases", True),
    ],
)
def test_resource_declarations_cannot_relax_core_policy(documents, key, value):
    documents[0]["resource_limits"][key] = value
    with pytest.raises(PackError):
        admitted(documents)


@pytest.mark.parametrize(
    "key,value",
    [
        ("max_cases", 1),
        ("max_file_bytes", 1),
        ("max_grid_cells", 64),
        ("max_total_grid_cells", 64),
    ],
)
def test_declared_limits_enforced_before_measurement(
    documents, key, value, monkeypatch
):
    monkeypatch.setattr(
        fft,
        "_measure",
        lambda _case: pytest.fail("Admission must reject before measurement."),
    )
    documents[0]["resource_limits"][key] = value
    with pytest.raises(PackError, match="ceiling|budget"):
        admitted(documents)


def test_content_tampering_and_reference_forgery(documents):
    manifest, cases = documents
    with pytest.raises(PackError, match="content hash"):
        admit_bytes(json_bytes(manifest), json_bytes(cases) + b"\n")
    cases["cases"][1]["expected_energy"] *= 2
    with pytest.raises(PackError, match="analytic formula"):
        admitted(documents)


def test_unique_nonempty_bounded_case_set(documents):
    for items in ([], documents[1]["cases"] * 3, [documents[1]["cases"][0]] * 2):
        altered = copy.deepcopy(documents)
        altered[1]["cases"] = items
        with pytest.raises(PackError):
            admitted(altered)


def test_reference_coherence_respects_stricter_declared_tolerance(documents):
    case = documents[1]["cases"][1]
    case["expected_energy"] += 1e-11
    case["absolute_tolerance"] = case["relative_tolerance"] = 1e-14
    with pytest.raises(PackError, match="analytic formula"):
        admitted(documents)


@pytest.mark.parametrize(
    "data",
    [
        b'{"x":1,"x":2}',
        b'{"x":NaN}',
        b'{"x":Infinity}',
        b'{"x":1e999}',
        b'{"x":"\\ud800"}',
        b"\xff",
        b"{",
        b"[" * 10000 + b"]" * 10000,
        b"[" * 17 + b"0" + b"]" * 17,
    ],
)
def test_hostile_json_fails_safely(data):
    with pytest.raises(PackError):
        decode_json(data)


def test_long_integer_parser_error_is_sanitized():
    with pytest.raises(PackError):
        decode_json(b'{"x":' + b"1" * 5000 + b"}")


def test_missing_directory_members_rejected(tmp_path):
    with pytest.raises(PackError, match="exactly"):
        admit_pack(tmp_path)


def test_opened_file_type_rechecked(monkeypatch):
    from qs_dmss.diagnostic_packs import admission

    class NotRegular:
        st_mode = 0o040755

    monkeypatch.setattr(admission.os, "fstat", lambda _fd: NotRegular())
    with pytest.raises(PackError, match="regular"):
        admit_pack()


def test_export_budget_enforced_before_writes(tmp_path):
    pack = admit_pack()
    report = {**fft.evaluate_pack(pack), "oversized": "x" * MAX_BUNDLE_BYTES}
    with pytest.raises(PackError, match="export ceiling"):
        export_result(pack, report, tmp_path / "result")
    assert not (tmp_path / "result").exists()


def test_compressed_bundle_and_advertised_budget_rejected(tmp_path):
    from qs_dmss.diagnostic_packs import evidence

    pack = admit_pack()
    bundle = Path(
        export_result(pack, fft.evaluate_pack(pack), tmp_path / "result")["bundle"]
    )
    with zipfile.ZipFile(bundle) as source:
        files = [(e.filename, source.read(e)) for e in source.infolist()]
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in files:
            archive.writestr(name, data)
    bundle.write_bytes(buffer.getvalue())
    with pytest.raises(PackError, match="stored"):
        verify_bundle(bundle)
    # An archive can claim oversized expanded members despite small actual bytes.
    with pytest.MonkeyPatch.context() as context:
        original = zipfile.ZipFile.infolist

        def oversized(self):
            entries = original(self)
            for entry in entries:
                entry.compress_type = zipfile.ZIP_STORED
            entries[0].file_size = evidence.MAX_BUNDLE_BYTES + 1
            return entries

        context.setattr(zipfile.ZipFile, "infolist", oversized)
        with pytest.raises(PackError, match="content exceeds"):
            verify_bundle(bundle)


def test_file_ceiling_and_immutable_snapshot(documents, tmp_path):
    with pytest.raises(PackError, match="core byte"):
        admit_bytes(b" " * (MAX_FILE_BYTES + 1), b"{}")
    root = tmp_path / "input"
    root.mkdir()
    for name, data in snapshot(bundled_pack_path()).items():
        (root / name).write_bytes(data)
    pack = admit_pack(root)
    (root / "cases.json").write_bytes(b"changed after admission")
    assert fft.evaluate_pack(pack)["all_cases_pass"] is True
    assert pack.cases_bytes != (root / "cases.json").read_bytes()


@pytest.mark.parametrize("extra", ["evil.py", "entry_point.json", "nested"])
def test_extra_content_not_executed(tmp_path, extra):
    root = tmp_path / "input"
    root.mkdir()
    for name, data in snapshot(bundled_pack_path()).items():
        (root / name).write_bytes(data)
    (root / extra).write_text("raise RuntimeError('never execute')", encoding="utf-8")
    with pytest.raises(PackError, match="exactly"):
        admit_pack(root)


def test_missing_and_oversized_storage_errors_are_authored(tmp_path):
    with pytest.raises(PackError):
        admit_pack(tmp_path / "missing")
    root = tmp_path / "input"
    root.mkdir()
    (root / "manifest.json").write_bytes(b" " * (MAX_FILE_BYTES + 1))
    (root / "cases.json").write_bytes(b"{}")
    with pytest.raises(PackError, match="core byte"):
        admit_pack(root)


def test_reparse_file_and_root_are_rejected(monkeypatch, tmp_path):
    original_lstat = Path.lstat

    class Reparse:
        st_mode = 0o100644
        st_file_attributes = 0x400

    root = bundled_pack_path()
    for target in (root, root / "cases.json"):
        with monkeypatch.context() as context:
            context.setattr(
                Path,
                "lstat",
                lambda path, **kwargs: (
                    Reparse() if path == target else original_lstat(path, **kwargs)
                ),
            )
            with pytest.raises(PackError):
                admit_pack(root)


def test_non_regular_file_and_storage_failure(monkeypatch):
    from qs_dmss.diagnostic_packs import admission

    root = bundled_pack_path()
    with monkeypatch.context() as context:
        context.setattr(admission.stat, "S_ISREG", lambda _mode: False)
        with pytest.raises(PackError, match="regular"):
            admit_pack(root)
    with monkeypatch.context() as context:
        context.setattr(
            admission.os,
            "scandir",
            lambda _path: (_ for _ in ()).throw(PermissionError()),
        )
        with pytest.raises(PackError, match="storage"):
            admit_pack(root)


@pytest.mark.parametrize(
    "energy,norm", [(1.0, 1.0), (math.nan, 1.0), (0.0, math.inf), (0.0, 2.0)]
)
def test_numerical_counterexamples_retained_not_hidden(
    monkeypatch, energy, norm, tmp_path
):
    monkeypatch.setattr(fft, "_measure", lambda _case: (energy, norm))
    pack = admit_pack()
    report = fft.evaluate_pack(pack)
    assert report["all_cases_pass"] is False
    assert report["numerical_outcome"] == "FALSIFIED_WITHIN_SCOPE"
    output = export_result(pack, report, tmp_path / "failed")
    assert verify_bundle(output["bundle"])["success"]
    assert b"NaN" not in (tmp_path / "failed/result.json").read_bytes()
    assert b"Infinity" not in (tmp_path / "failed/result.json").read_bytes()


def test_export_preserves_exact_inputs_hashes_and_no_overwrite(tmp_path):
    pack = admit_pack()
    report = fft.evaluate_pack(pack)
    original = snapshot(bundled_pack_path())
    output = tmp_path / "result"
    saved = export_result(
        pack, report, output, source_commit="a" * 40, candidate_wheel_sha256="b" * 64
    )
    assert verify_bundle(saved["bundle"])["checked_files"] == 4
    assert sha256(Path(saved["bundle"]).read_bytes()) == saved["bundle_sha256"]
    assert (output / "pack/manifest.json").read_bytes() == pack.manifest_bytes
    assert (output / "pack/cases.json").read_bytes() == pack.cases_bytes
    saved_report = json.loads((output / "result.json").read_bytes())
    assert saved_report["declared_artifact_identity"]["source_commit"] == "a" * 40
    assert saved_report["declared_artifact_identity"]["verification_scope"].startswith(
        "caller_declared"
    )
    before = snapshot(output)
    with pytest.raises(PackError, match="new writable"):
        export_result(pack, report, output)
    assert snapshot(output) == before
    assert snapshot(bundled_pack_path()) == original
    assert "declared_artifact_identity" not in report


@pytest.mark.parametrize(
    "identity", [{"source_commit": "main"}, {"candidate_wheel_sha256": "bad"}]
)
def test_invalid_identity_does_not_write(tmp_path, identity):
    pack = admit_pack()
    output = tmp_path / "result"
    with pytest.raises(PackError, match="identity"):
        export_result(pack, fft.evaluate_pack(pack), output, **identity)
    assert not output.exists()


def test_missing_parent_and_write_error_retains_partial_output(tmp_path, monkeypatch):
    pack = admit_pack()
    report = fft.evaluate_pack(pack)
    with pytest.raises(PackError, match="parent"):
        export_result(pack, report, tmp_path / "missing/result")
    original_open = Path.open
    target = tmp_path / "partial/result.json"

    def failed_open(path, *args, **kwargs):
        if path == target:
            raise PermissionError()
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", failed_open)
    with pytest.raises(PackError, match="partial output is retained"):
        export_result(pack, report, target.parent)
    assert (target.parent / "pack/manifest.json").exists()
    assert not (target.parent / "diagnostic-pack-evidence.zip").exists()


def rewrite_zip(path, transform):
    with zipfile.ZipFile(path) as source:
        files = [(e.filename, source.read(e)) for e in source.infolist()]
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_STORED) as archive:
        for name, data in transform(files):
            archive.writestr(name, data)
    path.write_bytes(buffer.getvalue())


@pytest.mark.parametrize(
    "change", ["tamper", "escape", "duplicate", "manifest-shape", "manifest-entry"]
)
def test_bundle_integrity_rejects_invalid_entries(tmp_path, change):
    pack = admit_pack()
    bundle = Path(
        export_result(pack, fft.evaluate_pack(pack), tmp_path / "result")["bundle"]
    )

    def transform(files):
        if change == "duplicate":
            return files + [files[0]]
        if change == "escape":
            return [
                ("../outside" if name == "summary.md" else name, data)
                for name, data in files
            ]
        changed = []
        for name, data in files:
            if change == "tamper" and name == "summary.md":
                data += b"changed"
            if name == "manifest.sha256.json" and change.startswith("manifest"):
                value = json.loads(data)
                if change == "manifest-shape":
                    value["files"] = []
                else:
                    value["files"]["result.json"]["size_bytes"] = True
                data = json_bytes(value)
            changed.append((name, data))
        return changed

    with pytest.warns(UserWarning) if change == "duplicate" else nullcontext():
        rewrite_zip(bundle, transform)
    with pytest.raises(PackError):
        verify_bundle(bundle)
    assert not (tmp_path / "outside").exists()


def test_bundle_read_is_bounded_and_invalid_zip_is_authored(tmp_path):
    bundle = tmp_path / "input.zip"
    bundle.write_bytes(b"X" * (MAX_BUNDLE_BYTES + 1))
    with pytest.raises(PackError, match="byte ceiling"):
        verify_bundle(bundle)
    bundle.write_bytes(b"not a zip")
    with pytest.raises(PackError, match="safely"):
        verify_bundle(bundle)


def test_complete_cli_workflow_and_failure_codes(tmp_path, capsys, monkeypatch):
    assert main(["diagnostic-packs", "inspect"]) == 0
    summary = json.loads(capsys.readouterr().out)
    assert summary["admitted"] and len(summary["cases"]["cases"]) == 12
    output = tmp_path / "result"
    assert main(["diagnostic-packs", "run", "--output", str(output)]) == 0
    saved = json.loads(capsys.readouterr().out)
    assert main(["diagnostic-packs", "verify", saved["bundle"]]) == 0
    assert json.loads(capsys.readouterr().out)["integrity_scope"].startswith(
        "content_hashes_only"
    )
    assert main(["diagnostic-packs", "run", "--output", str(output)]) == 1
    assert json.loads(capsys.readouterr().out)["success"] is False
    assert (
        main(["diagnostic-packs", "inspect", "--pack", str(tmp_path / "missing")]) == 1
    )
    assert "Traceback" not in capsys.readouterr().out
    monkeypatch.setattr(fft, "_measure", lambda _case: (0.0, 2.0))
    assert (
        main(["diagnostic-packs", "run", "--output", str(tmp_path / "counterexample")])
        == 1
    )
    assert (
        json.loads(capsys.readouterr().out)["numerical_outcome"]
        == "FALSIFIED_WITHIN_SCOPE"
    )
