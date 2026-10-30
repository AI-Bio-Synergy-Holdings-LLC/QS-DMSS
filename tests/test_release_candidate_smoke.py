"""Exercise release smoke orchestration with synthetic files, never real providers."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def smoke():
    spec = importlib.util.spec_from_file_location(
        "candidate_install_smoke", ROOT / ".github/scripts/fresh_install_smoke.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("version,expected", [
    ("0.13.2", False), ("0.14.0", False), ("0.14.99", False),
    ("0.15.0", True), ("0.15.1", True),
])
def test_cern_install_smoke_starts_at_new_public_feature_version(smoke, version, expected):
    assert smoke._includes_cern_lab(version) is expected


def quantum_payloads():
    return {
        "validate-fractal": ("quantum-sidecar-validation.json", {
            "success": True, "submission_policy": {"qpu_used": False, "submitted": False},
        }),
        "prepare-qpu-request": ("qpu-request.json", {
            "success": True, "credential_policy": {"credentials_read": False},
            "submission_policy": {"submitted": False, "never_submit": True},
            "cost_policy": {"max_authorized_cost_usd": 0.0},
        }),
        "validate-compilation": ("quantum-compilation-validation.json", {
            "success": True, "matrix": [{} for _ in range(12)],
            "execution_policy": {"credentials_read": False, "local_simulation_only": True,
                "max_authorized_cost_usd": 0.0, "provider": None,
                "remote_api_called": False, "submitted": False},
        }),
    }


def fake_quantum_runner(monkeypatch, smoke, payloads, missing=None):
    calls = []

    def run(command, *, cwd):
        calls.append(command)
        assert command[1] == "quantum"
        directory = Path(command[-1])
        directory.mkdir(parents=True)
        name, body = payloads[command[2]]
        (directory / name).write_text(json.dumps(body))
        artifacts = ("manifest.sha256.json", "quantum-sidecar-evidence.zip",
            "qpu-request-evidence.zip", "artifacts/fractal-fuzzy-target.openqasm",
            "quantum-compilation-evidence.zip", "quantum-compilation-matrix.csv")
        for name in artifacts:
            if name != missing:
                path = directory / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"synthetic smoke artifact")

    monkeypatch.setattr(smoke, "_run", run)
    return calls


def test_quantum_smoke_exercises_three_local_paths(smoke, monkeypatch, tmp_path):
    calls = fake_quantum_runner(monkeypatch, smoke, quantum_payloads())
    smoke._smoke_quantum(Path("synthetic-cli"), tmp_path, tmp_path / "out")
    assert [(c[2], c[4]) for c in calls] == [
        ("validate-fractal", "1024"), ("prepare-qpu-request", "128"),
        ("validate-compilation", "128"),
    ]


@pytest.mark.parametrize("command,keys,value", [
    ("validate-fractal", ("success",), False),
    ("validate-fractal", ("submission_policy", "qpu_used"), True),
    ("validate-fractal", ("submission_policy", "submitted"), True),
    ("prepare-qpu-request", ("success",), False),
    ("prepare-qpu-request", ("credential_policy", "credentials_read"), True),
    ("prepare-qpu-request", ("submission_policy", "submitted"), True),
    ("prepare-qpu-request", ("submission_policy", "never_submit"), False),
    ("prepare-qpu-request", ("cost_policy", "max_authorized_cost_usd"), 1),
    ("prepare-qpu-request", ("cost_policy", "max_authorized_cost_usd"), False),
    ("validate-compilation", ("success",), False),
    ("validate-compilation", ("matrix",), []),
    ("validate-compilation", ("matrix",), {str(i): {} for i in range(12)}),
    ("validate-compilation", ("execution_policy", "credentials_read"), True),
    ("validate-compilation", ("execution_policy", "local_simulation_only"), False),
    ("validate-compilation", ("execution_policy", "max_authorized_cost_usd"), 1),
    ("validate-compilation", ("execution_policy", "max_authorized_cost_usd"), False),
    ("validate-compilation", ("execution_policy", "provider"), "not-allowed"),
    ("validate-compilation", ("execution_policy", "remote_api_called"), True),
    ("validate-compilation", ("execution_policy", "submitted"), True),
])
def test_quantum_smoke_refuses_policy_drift(
    smoke, monkeypatch, tmp_path, command, keys, value
):
    payloads = copy.deepcopy(quantum_payloads())
    body = payloads[command][1]
    for key in keys[:-1]:
        body = body[key]
    body[keys[-1]] = value
    fake_quantum_runner(monkeypatch, smoke, payloads)
    with pytest.raises(AssertionError, match="never-submit"):
        smoke._smoke_quantum(Path("synthetic-cli"), tmp_path, tmp_path / "out")


@pytest.mark.parametrize("missing", ["manifest.sha256.json", "quantum-sidecar-evidence.zip",
    "qpu-request-evidence.zip", "artifacts/fractal-fuzzy-target.openqasm",
    "quantum-compilation-evidence.zip", "quantum-compilation-matrix.csv"])
def test_quantum_smoke_requires_complete_artifacts(smoke, monkeypatch, tmp_path, missing):
    fake_quantum_runner(monkeypatch, smoke, quantum_payloads(), missing)
    with pytest.raises(AssertionError, match="Missing quantum artifact"):
        smoke._smoke_quantum(Path("synthetic-cli"), tmp_path, tmp_path / "out")


@pytest.mark.parametrize("version", ["0.14.0", "0.15.0"])
@pytest.mark.parametrize("with_quantum", [False, True])
def test_candidate_install_spec_and_feature_gates(
    smoke, monkeypatch, tmp_path, version, with_quantum
):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    wheel = tmp_path / f"qs_dmss-{version}-py3-none-any.whl"
    wheel.write_bytes(b"synthetic wheel; subprocesses are mocked")
    monkeypatch.setattr(smoke.tempfile, "mkdtemp", lambda **kwargs: str(workspace))
    monkeypatch.setenv("QS_DMSS_KEEP_SMOKE_OUTPUTS", "1")
    monkeypatch.setattr(smoke, "_capture", lambda *args, **kwargs: version)
    monkeypatch.setattr(smoke, "_smoke_cockpit", lambda *args: None)
    quantum_calls = []
    monkeypatch.setattr(smoke, "_smoke_quantum", lambda *args: quantum_calls.append(args))
    calls = []

    def run(command, *, cwd):
        calls.append(command)
        outputs = workspace / "outputs"
        if "run-demo" in command:
            target = outputs / ("experiments" if "campaigns" in command else "runs") / "run-a"
            target.mkdir(parents=True)
            (target / "evidence_bundle.zip").write_bytes(b"synthetic")
        if "showcase" in command:
            root = outputs / "simulation-showcase"
            for name in ("simulation-showcase.json", "simulation-showcase.md",
                "artifacts/step-history.csv", "artifacts/radial-density-profile.csv",
                "artifacts/density-midplane.csv", "artifacts/energy-history.svg",
                "artifacts/radial-density-profile.svg", "artifacts/density-midplane.svg"):
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"synthetic")

    monkeypatch.setattr(smoke, "_run", run)
    smoke.run_smoke("candidate-wheel", None, None, wheel, with_quantum=with_quantum)
    install_specs = [c[-1] for c in calls if c[1:4] == ["-m", "pip", "install"]]
    assert str(wheel) + ("[quantum]" if with_quantum else "") in install_specs
    assert any(Path(c[1]).name == "external_dimuon_smoke.py" for c in calls) is (version == "0.15.0")
    assert bool(quantum_calls) is with_quantum
    assert workspace.is_dir()


def test_quantum_candidate_gate_covers_all_three_supported_os():
    workflow = yaml.load((ROOT / ".github/workflows/fresh-install-smoke.yml").read_text(), Loader=yaml.BaseLoader)
    job = workflow["jobs"]["candidate-quantum-wheel"]
    assert job["if"] == "github.event_name == 'pull_request'"
    assert set(job["strategy"]["matrix"]["os"]) == {"ubuntu-latest", "macos-latest", "windows-latest"}
    assert any("--with-quantum" in step.get("run", "") for step in job["steps"])


def test_new_build_does_not_retarget_frozen_reconciliation_or_publication():
    protocol = json.loads((ROOT / "research/cern_dimuon_qualification/protocol-v1.json").read_text())
    assert protocol["candidate_commit"] == "c158c3ba3f81cadf7d11bdfcab3441c8d99be851"
    assert protocol["candidate_wheel_sha256"] == "6a8af63f047be841a9ce17d3f02392d56f0963498979f7c27593aed40aac1e60"
    assert protocol["qualification_outcome"] == "NOT_EXECUTED"
    notes = (ROOT / "docs/release-v0.15.0.md").read_text()
    for text in ("DEFERRED, HOLD", "NOT_ESTABLISHED", "NOT_EXECUTED", "PENDING", "v0.14.0"):
        assert text in notes
    security = (ROOT / "SECURITY.md").read_text()
    assert "does not end the existing `v0.13.x`" in security
    assert "`v0.15.0` source target is under preparation" in security
