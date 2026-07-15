from __future__ import annotations

import argparse
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path


REPOSITORY = "AI-Bio-Synergy-Holdings-LLC/QS-DMSS"


def _run(command: list[str], *, cwd: Path) -> None:
    print("+ " + " ".join(command), flush=True)
    subprocess.run(command, cwd=cwd, check=True)


def _capture(command: list[str], *, cwd: Path) -> str:
    print("+ " + " ".join(command), flush=True)
    completed = subprocess.run(
        command,
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _venv_python(venv: Path) -> Path:
    if os.name == "nt":
        return venv / "Scripts" / "python.exe"
    return venv / "bin" / "python"


def _venv_command(venv: Path, name: str) -> Path:
    if os.name == "nt":
        return venv / "Scripts" / f"{name}.exe"
    return venv / "bin" / name


def _download_wheel(package_version: str, release_tag: str, workspace: Path) -> Path:
    wheel_name = f"qs_dmss-{package_version}-py3-none-any.whl"
    wheel_url = (
        f"https://github.com/{REPOSITORY}/releases/download/"
        f"{release_tag}/{wheel_name}"
    )
    wheel_path = workspace / wheel_name
    print(f"Downloading {wheel_url}", flush=True)
    urllib.request.urlretrieve(wheel_url, wheel_path)
    return wheel_path


def _candidate_wheel(path: Path) -> Path:
    resolved = path.resolve()
    if resolved.is_file() and resolved.suffix == ".whl":
        return resolved
    if resolved.is_dir():
        wheels = sorted(resolved.glob("qs_dmss-*.whl"))
        if len(wheels) == 1:
            return wheels[0]
        raise AssertionError(
            f"Expected one candidate wheel under {resolved}, found {wheels!r}"
        )
    raise AssertionError(f"Candidate wheel path does not exist: {resolved}")


def _latest_child(path: Path) -> Path:
    children = [child for child in path.iterdir() if child.is_dir()]
    if not children:
        raise AssertionError(f"No generated directories found under {path}")
    return max(children, key=lambda child: child.stat().st_mtime)


def _version_at_least(version: str, minimum: tuple[int, int, int]) -> bool:
    parts = version.split(".")
    parsed = tuple(int(part) for part in parts[:3])
    return parsed >= minimum


def _available_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


def _smoke_cockpit(
    cli: Path,
    workspace: Path,
    output_root: Path,
    package_version: str,
) -> None:
    port = _available_port()
    health_url = f"http://127.0.0.1:{port}/api/health"
    log_path = workspace / "cockpit-smoke.log"
    command = [
        str(cli),
        "cockpit",
        "--host",
        "127.0.0.1",
        "--port",
        str(port),
        "--output-root",
        str(output_root),
    ]
    print("+ " + " ".join(command), flush=True)

    payload: dict[str, object] | None = None
    response_headers: dict[str, str] = {}
    with log_path.open("w", encoding="utf-8") as log_file:
        process = subprocess.Popen(
            command,
            cwd=workspace,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            text=True,
        )
        try:
            deadline = time.monotonic() + 30
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    break
                try:
                    with urllib.request.urlopen(health_url, timeout=2) as response:
                        payload = json.loads(response.read().decode("utf-8"))
                        response_headers = {
                            key.lower(): value for key, value in response.headers.items()
                        }
                    break
                except OSError:
                    time.sleep(0.25)
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)

    if payload is None:
        logs = log_path.read_text(encoding="utf-8", errors="replace")
        raise AssertionError(f"Cockpit health check failed at {health_url}:\n{logs}")
    if payload.get("status") != "ok" or payload.get("version") != package_version:
        raise AssertionError(f"Unexpected cockpit health payload: {payload!r}")

    forbidden_health_fields = {
        "package_root",
        "repo_root",
        "output_root",
        "experiments_root",
        "jobs_root",
    }
    exposed_fields = forbidden_health_fields.intersection(payload)
    if exposed_fields:
        raise AssertionError(f"Cockpit health exposed server paths: {sorted(exposed_fields)}")

    required_headers = {
        "content-security-policy",
        "x-frame-options",
        "x-content-type-options",
        "referrer-policy",
        "strict-transport-security",
    }
    missing_headers = required_headers.difference(response_headers)
    if missing_headers:
        raise AssertionError(f"Cockpit health missing headers: {sorted(missing_headers)}")


def run_smoke(
    source: str,
    package_version: str | None,
    release_tag: str | None,
    wheel_path: Path | None = None,
) -> None:
    workspace = Path(tempfile.mkdtemp(prefix=f"qs-dmss-{source}-")).resolve()
    try:
        venv = workspace / "venv"
        _run([sys.executable, "-m", "venv", str(venv)], cwd=workspace)
        python = _venv_python(venv)
        cli = _venv_command(venv, "qs-dmss")

        _run([str(python), "-m", "pip", "install", "--upgrade", "pip"], cwd=workspace)
        if source == "pypi":
            if not package_version:
                raise ValueError("PyPI smoke requires --package-version")
            _run(
                [
                    str(python),
                    "-m",
                    "pip",
                    "install",
                    "--no-cache-dir",
                    f"qs-dmss=={package_version}",
                ],
                cwd=workspace,
            )
        elif source == "release-wheel":
            if not package_version or not release_tag:
                raise ValueError(
                    "Release-wheel smoke requires --package-version and --release-tag"
                )
            wheel_path = _download_wheel(package_version, release_tag, workspace)
            _run([str(python), "-m", "pip", "install", str(wheel_path)], cwd=workspace)
        elif source == "candidate-wheel":
            if wheel_path is None:
                raise ValueError("Candidate-wheel smoke requires --wheel-path")
            candidate = _candidate_wheel(wheel_path)
            _run([str(python), "-m", "pip", "install", str(candidate)], cwd=workspace)
        else:  # pragma: no cover - argparse prevents this path.
            raise ValueError(f"Unsupported source: {source}")

        installed_version = _capture(
            [
                str(python),
                "-c",
                "from importlib.metadata import version; print(version('qs-dmss'))",
            ],
            cwd=workspace,
        )
        if package_version and installed_version != package_version:
            raise AssertionError(
                f"Installed qs-dmss {installed_version}, expected {package_version}"
            )
        package_version = installed_version

        output_root = workspace / "outputs"
        run_root = output_root / "runs"
        campaign_runs_root = output_root / "campaign-runs"
        campaign_experiments_root = output_root / "experiments"
        replay_root = output_root / "replays"
        showcase_root = output_root / "simulation-showcase"
        cockpit_root = output_root / "cockpit"

        _run([str(cli), "run-demo", "--output-root", str(run_root)], cwd=workspace)
        run_dir = _latest_child(run_root)
        if not (run_dir / "evidence_bundle.zip").is_file():
            raise AssertionError(f"Missing evidence bundle under {run_dir}")

        _run([str(cli), "verify", str(run_dir)], cwd=workspace)
        _run([str(cli), "replay", str(run_dir), "--output-root", str(replay_root)], cwd=workspace)

        _run(
            [
                str(cli),
                "campaigns",
                "run-demo",
                "--output-root",
                str(campaign_runs_root),
            ],
            cwd=workspace,
        )
        campaign_dir = _latest_child(campaign_experiments_root)
        if not (campaign_dir / "evidence_bundle.zip").is_file():
            raise AssertionError(f"Missing campaign bundle under {campaign_dir}")

        if _version_at_least(package_version, (0, 4, 0)):
            _run(
                [
                    str(cli),
                    "showcase",
                    "run",
                    "--output-root",
                    str(showcase_root),
                ],
                cwd=workspace,
            )
            for required in (
                showcase_root / "simulation-showcase.json",
                showcase_root / "simulation-showcase.md",
                showcase_root / "artifacts" / "step-history.csv",
                showcase_root / "artifacts" / "radial-density-profile.csv",
                showcase_root / "artifacts" / "density-midplane.csv",
                showcase_root / "artifacts" / "energy-history.svg",
                showcase_root / "artifacts" / "radial-density-profile.svg",
                showcase_root / "artifacts" / "density-midplane.svg",
            ):
                if not required.is_file():
                    raise AssertionError(f"Missing showcase artifact: {required}")
        else:
            print(
                "Skipping showcase smoke because it ships in qs-dmss>=0.4.0.",
                flush=True,
            )

        _smoke_cockpit(cli, workspace, cockpit_root, package_version)

        print(
            f"Fresh install smoke passed for {source} "
            f"qs-dmss=={package_version} in {workspace}",
            flush=True,
        )
    finally:
        if os.environ.get("QS_DMSS_KEEP_SMOKE_OUTPUTS") != "1":
            shutil.rmtree(workspace, ignore_errors=True)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Fresh-install QS-DMSS smoke test for candidate, PyPI, and release wheels."
        ),
    )
    parser.add_argument(
        "--source",
        choices=["candidate-wheel", "pypi", "release-wheel"],
        required=True,
        help="Install source to validate.",
    )
    parser.add_argument(
        "--package-version",
        default=None,
        help="Published package version, for example 0.5.0.",
    )
    parser.add_argument(
        "--release-tag",
        default=None,
        help="GitHub release tag containing the wheel, for example v0.5.0.",
    )
    parser.add_argument(
        "--wheel-path",
        type=Path,
        default=None,
        help="Candidate wheel file or directory containing exactly one wheel.",
    )
    args = parser.parse_args()
    run_smoke(args.source, args.package_version, args.release_tag, args.wheel_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
