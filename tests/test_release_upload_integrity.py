from __future__ import annotations

import hashlib
import json
import os
import runpy
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / ".github/scripts/verify_release_upload.py"
verify_packet = runpy.run_path(str(SCRIPT))["verify_packet"]
TAG = "v0.15.0"
COMMIT = "a" * 40
WHEEL = "qs_dmss-0.15.0-py3-none-any.whl"
SDIST = "qs_dmss-0.15.0.tar.gz"
MANIFEST = "qs-dmss-release-manifest.json"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_manifest(packet: Path, manifest: dict) -> str:
    data = json.dumps(manifest, sort_keys=True).encode("utf-8")
    (packet / MANIFEST).write_bytes(data)
    return sha(data)


@pytest.fixture
def packet(tmp_path: Path) -> tuple[Path, dict, str]:
    root = tmp_path / "publication"
    dist = root / "dist"
    dist.mkdir(parents=True)
    members = {WHEEL: b"synthetic wheel", SDIST: b"synthetic sdist"}
    for name, data in members.items():
        (dist / name).write_bytes(data)
    manifest = {
        "schema_version": 1,
        "tag": TAG,
        "source_commit": COMMIT,
        "artifacts": {name: sha(data) for name, data in members.items()},
    }
    return root, manifest, write_manifest(root, manifest)


def test_exact_packet_passes_in_both_stages(packet) -> None:
    root, manifest, approved = packet
    assert verify_packet(root, TAG, COMMIT, approved) == manifest["artifacts"]
    assert verify_packet(root, TAG, COMMIT, approved) == manifest["artifacts"]


@pytest.mark.parametrize("name", [WHEEL, SDIST])
def test_handoff_rejects_modified_distribution(packet, name) -> None:
    root, _, approved = packet
    verify_packet(root, TAG, COMMIT, approved)
    (root / "dist" / name).write_bytes(b"different bytes")
    with pytest.raises(ValueError, match="artifact SHA-256 does not match"):
        verify_packet(root, TAG, COMMIT, approved)


def test_replacement_manifest_and_matching_release_bytes_are_not_approval(packet) -> None:
    root, manifest, approved = packet
    replacement = b"replacement wheel"
    (root / "dist" / WHEEL).write_bytes(replacement)
    manifest["artifacts"][WHEEL] = sha(replacement)
    write_manifest(root, manifest)
    with pytest.raises(ValueError, match="approved digest"):
        verify_packet(root, TAG, COMMIT, approved)


@pytest.mark.parametrize("replacement", ["", "a" * 63, "A" * 64, "x" * 64])
def test_invalid_or_missing_approval_is_rejected(packet, replacement) -> None:
    with pytest.raises(ValueError, match="expected a lowercase SHA-256"):
        verify_packet(packet[0], TAG, COMMIT, replacement)


@pytest.mark.parametrize(
    ("tag", "commit", "reason"),
    [
        ("v0.15.1", COMMIT, "tag or source commit"),
        (TAG, "b" * 40, "tag or source commit"),
        ("refs/heads/main", COMMIT, "final release tag"),
        (TAG, "abc", "full checked-out Git commit"),
    ],
)
def test_tag_and_full_source_binding(packet, tag, commit, reason) -> None:
    with pytest.raises(ValueError, match=reason):
        verify_packet(packet[0], tag, commit, packet[2])


@pytest.mark.parametrize("case", ["missing", "extra", "renamed", "directory"])
def test_distribution_membership_is_exact(packet, case) -> None:
    root, _, approved = packet
    wheel = root / "dist" / WHEEL
    if case == "extra":
        (wheel.parent / ".unapproved").write_bytes(b"extra member")
    elif case == "renamed":
        wheel.rename(wheel.with_name(f"new-{WHEEL}"))
    else:
        wheel.unlink()
        if case == "directory":
            wheel.mkdir()
    reason = "regular file" if case == "directory" else "exactly the expected wheel and sdist"
    with pytest.raises(ValueError, match=reason):
        verify_packet(root, TAG, COMMIT, approved)


def test_distribution_symlink_is_not_a_regular_member(packet) -> None:
    root, _, approved = packet
    wheel = root / "dist" / WHEEL
    wheel.unlink()
    try:
        wheel.symlink_to(root / "dist" / SDIST)
    except OSError as exc:
        pytest.skip(f"creating symlinks is unavailable: {exc}")
    with pytest.raises(ValueError, match="artifact must be a regular file"):
        verify_packet(root, TAG, COMMIT, approved)


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    [
        ("schema_version", True, "unsupported manifest schema"),
        ("other", "unexpected", "unexpected manifest fields"),
        ("artifacts", {"../outside.whl": "a" * 64, SDIST: "a" * 64}, "expected wheel and sdist"),
        ("artifacts", {WHEEL: "invalid", SDIST: "a" * 64}, "invalid manifest digest"),
    ],
)
def test_digest_does_not_excuse_malformed_manifest(packet, field, value, reason) -> None:
    root, manifest, _ = packet
    manifest[field] = value
    with pytest.raises(ValueError, match=reason):
        verify_packet(root, TAG, COMMIT, write_manifest(root, manifest))


@pytest.mark.parametrize(
    ("document", "reason"),
    [
        (b'{"schema_version":1,"schema_version":1}', "duplicate key"),
        (b" " * 4097, "size limit"),
        (b"not json", "Expecting value"),
    ],
)
def test_bounded_manifest_decoder(packet, document, reason) -> None:
    root, _, _ = packet
    (root / MANIFEST).write_bytes(document)
    with pytest.raises(ValueError, match=reason):
        verify_packet(root, TAG, COMMIT, sha(document))


def test_cli_retains_hashes_for_review_and_fails_closed(packet) -> None:
    root, manifest, approved = packet
    command = [
        sys.executable, str(SCRIPT), "--packet", str(root), "--tag", TAG,
        "--source-commit", COMMIT, "--manifest-sha256", approved,
    ]
    good = subprocess.run(command, check=True, capture_output=True, text=True, timeout=15)
    assert all(value in good.stdout for value in [COMMIT, approved, *manifest["artifacts"].values()])
    (root / MANIFEST).unlink()
    bad = subprocess.run(command, check=False, capture_output=True, text=True, timeout=15)
    assert bad.returncode != 0
    assert "Release upload refused" in bad.stderr
    assert "Verified release packet" not in bad.stdout


@pytest.fixture
def workflow() -> dict:
    return yaml.load(
        (ROOT / ".github/workflows/publish-pypi.yml").read_text(encoding="utf-8"),
        Loader=yaml.BaseLoader,
    )


@pytest.mark.parametrize(
    ("case", "reason"),
    [
        ("approved", "Verified release packet"),
        ("missing", "protected pypi manifest approval"),
        ("mismatch", "protected pypi manifest approval"),
        ("moved", "tag or source commit"),
        ("tampered", "artifact SHA-256 does not match"),
    ],
)
def test_final_workflow_step_on_synthetic_handoff(workflow, packet, case, reason) -> None:
    bash = shutil.which("bash")
    if os.name == "nt":
        git = shutil.which("git")
        git_bash = Path(git).parent.parent / "bin/bash.exe" if git else None
        bash = str(git_bash) if git_bash and git_bash.is_file() else None
    if bash is None:
        pytest.skip("Bash is unavailable for local workflow step validation")

    root, _, approved = packet
    if case == "tampered":
        (root / "dist" / SDIST).write_bytes(b"changed in transit")
    protected_digest = {"missing": "", "mismatch": "0" * 64}.get(case, approved)
    env = {
        **os.environ,
        "APPROVED_MANIFEST_SHA256": protected_digest,
        "RELEASE_MANIFEST_SHA256": approved,
        "RELEASE_TAG": TAG,
        "SYNTHETIC_COMMIT": "b" * 40 if case == "moved" else COMMIT,
        "SYNTHETIC_PYTHON": Path(sys.executable).as_posix(),
        "SYNTHETIC_VERIFIER": SCRIPT.as_posix(),
    }
    # Resolve only a synthetic checkout; invoke the real verifier. No publisher,
    # registry, Actions artifact service, release tag, or source checkout is used.
    setup = '''
git() {
    [[ "$*" == "-C release-source rev-parse HEAD" ]] || return 97
    printf '%s\\n' "$SYNTHETIC_COMMIT"
}
python() {
    [[ "$1" == ".github/scripts/verify_release_upload.py" ]] || return 97
    shift
    "$SYNTHETIC_PYTHON" "$SYNTHETIC_VERIFIER" "$@"
}
'''
    guard = workflow["jobs"]["publish"]["steps"][-2]["run"]
    result = subprocess.run(
        [bash, "--noprofile", "--norc", "-s"], input=setup + guard, cwd=root.parent,
        env=env, check=False, capture_output=True, text=True, timeout=15,
    )
    assert (result.returncode == 0) == (case == "approved"), result.stderr
    assert reason in result.stdout + result.stderr


def test_protected_workflow_checks_the_download_and_the_upload(workflow) -> None:
    assert set(workflow["on"]) == {"workflow_dispatch"}
    inputs = workflow["on"]["workflow_dispatch"]["inputs"]
    assert inputs["manifest_sha256"]["required"] == "true"
    prepare = workflow["jobs"]["prepare-release-assets"]
    publish = workflow["jobs"]["publish"]
    assert publish["environment"]["name"] == "pypi"
    assert publish["needs"] == "prepare-release-assets"
    steps = {step["name"]: step for step in prepare["steps"]}
    assert list(steps).index("Download GitHub release artifacts") < list(steps).index(
        "Verify downloaded release hashes"
    ) < list(steps).index("Validate release artifact metadata")
    assert "verify_release_upload.py" in steps["Verify downloaded release hashes"]["run"]
    assert "refs/heads/main" in steps["Validate manual dispatch"]["run"]
    assert steps["Upload PyPI-ready artifacts"]["with"]["path"] == "publication/"
    assert prepare["outputs"]["artifact_id"] == "${{ steps.handoff.outputs.artifact-id }}"
    for job in (prepare, publish):
        checkout = [step["with"]["ref"] for step in job["steps"] if step.get("uses", "").startswith(
            "actions/checkout@"
        )]
        assert checkout == ["${{ github.workflow_sha }}", "refs/tags/${{ inputs.tag }}"]
    download, guard, uploader = publish["steps"][-3:]
    assert "!= ''" in download["if"]
    assert download["with"]["artifact-ids"] == "${{ needs.prepare-release-assets.outputs.artifact_id }}"
    assert guard["env"]["APPROVED_MANIFEST_SHA256"] == "${{ secrets.QS_DMSS_APPROVED_MANIFEST_SHA256 }}"
    assert '!= "$RELEASE_MANIFEST_SHA256"' in guard["run"]
    assert 'verify_release_upload.py' in guard["run"]
    assert '--manifest-sha256 "$APPROVED_MANIFEST_SHA256"' in guard["run"]
    assert "continue-on-error" not in guard
    assert uploader["uses"].startswith("pypa/gh-action-pypi-publish@")
    assert uploader["with"]["packages-dir"] == "publication/dist/"
