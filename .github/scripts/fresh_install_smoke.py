from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path


REPOSITORY = "AI-Bio-Synergy-Holdings-LLC/QS-DMSS"


def _run(command: list[str], *, cwd: Path) -> None:
    print("+ " + " ".join(command), flush=True)
    subprocess.run(command, cwd=cwd, check=True)


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


def _latest_child(path: Path) -> Path:
    children = [child for child in path.iterdir() if child.is_dir()]
    if not children:
        raise AssertionError(f"No generated directories found under {path}")
    return max(children, key=lambda child: child.stat().st_mtime)


def run_smoke(source: str, package_version: str, release_tag: str) -> None:
    workspace = Path(tempfile.mkdtemp(prefix=f"qs-dmss-{source}-")).resolve()
    try:
        venv = workspace / "venv"
        _run([sys.executable, "-m", "venv", str(venv)], cwd=workspace)
        python = _venv_python(venv)
        cli = _venv_command(venv, "qs-dmss")

        _run([str(python), "-m", "pip", "install", "--upgrade", "pip"], cwd=workspace)
        if source == "pypi":
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
            wheel_path = _download_wheel(package_version, release_tag, workspace)
            _run([str(python), "-m", "pip", "install", str(wheel_path)], cwd=workspace)
        else:  # pragma: no cover - argparse prevents this path.
            raise ValueError(f"Unsupported source: {source}")

        output_root = workspace / "outputs"
        run_root = output_root / "runs"
        campaign_runs_root = output_root / "campaign-runs"
        campaign_experiments_root = output_root / "experiments"
        replay_root = output_root / "replays"

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
        description="Fresh-install QS-DMSS smoke test for PyPI and release wheel paths.",
    )
    parser.add_argument(
        "--source",
        choices=["pypi", "release-wheel"],
        required=True,
        help="Install source to validate.",
    )
    parser.add_argument(
        "--package-version",
        required=True,
        help="Published package version, for example 0.2.0.",
    )
    parser.add_argument(
        "--release-tag",
        required=True,
        help="GitHub release tag containing the wheel, for example v0.2.0.",
    )
    args = parser.parse_args()
    run_smoke(args.source, args.package_version, args.release_tag)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
