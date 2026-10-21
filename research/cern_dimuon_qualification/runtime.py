"""Fail-closed native runtime admission; no dataset access or installation."""

import hashlib
import importlib
import importlib.metadata
import io
import json
import platform
import re
import struct
import sys
import zipfile
from pathlib import Path, PurePosixPath

from .candidate import IDENTITY_MODULES, wheel_identity
from .contract import COMMIT, SCIENTIFIC, WHEEL_SHA256, Hold, checked_protocol
from .retention import literal, read_regular

MANIFEST_SHA256 = "268f7242692bef6902dfed1d7dcb6c230734b45d143b1fdb2bc9d7fba6dd4650"
WINDOWS_LAUNCHER_SHA256 = (
    "f9475ecd98ef320792a4946b80b1915500a318e9ad537097b8188c28fd659928"
)
WINDOWS_BASE_SHA256 = "407de1f8feb303d3249bb835e5ff7f543daada4e229c2c496d24a5b99fdba9ec"
LOCKS = Path(__file__).parent / "environments/v1"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def load_locks(root=LOCKS):
    raw = read_regular(root / "manifest.json", 64 * 1024)
    if sha(raw) != MANIFEST_SHA256:
        raise Hold("Environment manifest differs from the reviewed identity.")
    plan = json.loads(raw)
    checked_protocol()
    if (
        plan["candidate_commit"] != COMMIT
        or plan["candidate_wheel_sha256"] != WHEEL_SHA256
    ):
        raise Hold("Environment candidate differs from the approved artifact.")
    for target in plan["targets"].values():
        if sha(read_regular(root / target["lock_file"], 8192)) != target["lock_sha256"]:
            raise Hold("Native dependency lock identity changed.")
    return plan


def canonical(name):
    if not isinstance(name, str) or not re.fullmatch(
        r"[A-Za-z0-9][A-Za-z0-9_.-]*", name
    ):
        raise Hold("Installed distribution identity is invalid.")
    return re.sub(r"[-_.]+", "-", name).lower()


def check_observations(target, plan, observed):
    if target not in {"windows", "linux"}:
        raise Hold("Only the two reviewed native targets are admitted.")
    locked = plan["targets"][target]
    expected = {row["name"]: row["version"] for row in locked["packages"]}
    if (
        observed["system"].lower() != target
        or observed["implementation"] != "CPython"
        or observed["python"] != plan["python"]
        or observed["sys_version"] != locked["runtime_sys_version"]
        or observed["machine"] != locked["machine"]
        or observed["pointer_bits"] != 64
        or not observed["isolated_environment"]
        or observed["packages"] != expected
    ):
        raise Hold("Actual native runtime or package set differs from its frozen lock.")


def check_member_path(name, size):
    relative = PurePosixPath(name)
    if (
        relative.is_absolute()
        or ".." in relative.parts
        or "\\" in name
        or ":" in name
        or ".data/" in name
        or size > 64 * 1024 * 1024
    ):
        raise Hold("Runtime wheel member is outside the reviewed install layout.")


def check_installed_wheel(path, row, distribution, prefix):
    raw = read_regular(path, row["bytes"])
    if len(raw) != row["bytes"] or sha(raw) != row["sha256"]:
        raise Hold("Runtime wheel cache differs from the frozen artifact.")
    count = 0
    stream = hashlib.sha256()
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise Hold("Runtime wheel contains duplicate members.")
        for member in sorted(archive.infolist(), key=lambda item: item.filename):
            if member.is_dir():
                continue
            name = member.filename
            check_member_path(name, member.file_size)
            # pip regenerates RECORD. All other original wheel members, including
            # metadata, Python modules and native libraries, must match raw bytes.
            if ".dist-info/" in name and name.endswith("/RECORD"):
                continue
            installed = Path(distribution.locate_file(name)).resolve(strict=True)
            if not installed.is_relative_to(prefix):
                raise Hold("Installed distribution escaped the isolated environment.")
            actual = read_regular(installed, member.file_size)
            expected = archive.read(member)
            if actual != expected:
                raise Hold("Installed runtime member differs from its locked wheel.")
            stream.update(name.encode() + b"\0" + hashlib.sha256(actual).digest())
            count += 1
    return {
        "version": row["version"],
        "artifact_sha256": row["sha256"],
        "installed_members": count,
        "installed_stream_sha256": stream.hexdigest(),
    }


def retained_candidate_identity(identity):
    """Linux verifies imports against the controller's retained Git-checked map."""
    if (
        identity.get("candidate_commit") != COMMIT
        or identity.get("wheel_sha256") != WHEEL_SHA256
        or set(identity.get("module_sha256", {})) != set(IDENTITY_MODULES.values())
    ):
        raise Hold("Retained candidate identity is incomplete or outside the pin.")
    for module_name, member in IDENTITY_MODULES.items():
        module = importlib.import_module(module_name)
        actual = read_regular(Path(module.__file__).resolve(strict=True), 256 * 1024)
        if sha(actual) != identity["module_sha256"][member]:
            raise Hold("Imported candidate differs from retained Git-checked identity.")
    return {
        **identity,
        "commit_assertion": "controller Git check; native imported bytes checked against retained map",
    }


def check_cache(path):
    path = literal(path)
    if (
        not sys.flags.dont_write_bytecode
        or not sys.pycache_prefix
        or literal(sys.pycache_prefix) != path
        or sys._xoptions.get("pycache_prefix") != str(path)
        or not path.is_dir()
        or any(path.iterdir())
    ):
        raise Hold("A fresh empty startup bytecode prefix and -B are required.")
    return str(path)


def admit_environment(
    target, wheel, wheelhouse, repository, *, cache_dir, candidate_identity=None
):
    """Verify before fixture access; hashes are integrity checks, not attestation."""
    try:
        cache = check_cache(cache_dir)
        plan = load_locks()
        distributions = {}
        for distribution in importlib.metadata.distributions():
            name = canonical(distribution.metadata["Name"])
            if name in distributions:
                raise Hold("Duplicate installed distributions are not admitted.")
            distributions[name] = distribution
        observed = {
            "system": platform.system(),
            "implementation": platform.python_implementation(),
            "python": platform.python_version(),
            "sys_version": sys.version,
            "machine": platform.machine(),
            "pointer_bits": struct.calcsize("P") * 8,
            "isolated_environment": sys.prefix != sys.base_prefix,
            "packages": {name: value.version for name, value in distributions.items()},
        }
        check_observations(target, plan, observed)
        executable_sha = sha(
            read_regular(Path(sys.executable).resolve(strict=True), 32 * 1024 * 1024)
        )
        if target == "windows" and (
            executable_sha != WINDOWS_LAUNCHER_SHA256
            or sha(
                read_regular(
                    Path(sys._base_executable).resolve(strict=True), 32 * 1024 * 1024
                )
            )
            != WINDOWS_BASE_SHA256
        ):
            raise Hold("Windows interpreter bytes differ from the reviewed runtime.")
        prefix = Path(sys.prefix).resolve(strict=True)
        packages = {}
        for row in plan["targets"][target]["packages"]:
            artifact = (
                Path(wheel)
                if row["name"] == "qs-dmss"
                else Path(wheelhouse) / row["filename"]
            )
            packages[row["name"]] = check_installed_wheel(
                artifact, row, distributions[row["name"]], prefix
            )
        candidate = (
            retained_candidate_identity(candidate_identity)
            if target == "linux" and candidate_identity is not None
            else wheel_identity(wheel, repository)
        )
        import numpy

        import qs_dmss

        if (
            numpy.__version__ != plan["numpy"]
            or not Path(numpy.__file__).resolve().is_relative_to(prefix)
            or not Path(qs_dmss.__file__).resolve().is_relative_to(prefix)
        ):
            raise Hold("Imported numerical code differs from the isolated runtime.")
        return {
            "state": "ADMITTED",
            "target": target,
            "observed": observed,
            "python_executable_sha256": executable_sha,
            "interpreter_prefix": str(prefix),
            "wheelhouse": str(Path(wheelhouse)),
            "numpy_build_configuration": numpy.show_config(mode="dicts"),
            "packages": packages,
            "candidate": candidate,
            "lock_manifest_sha256": MANIFEST_SHA256,
            "empty_startup_bytecode_prefix": cache,
            "scope": "Locked wheel members checked except installer-regenerated RECORD; no OS/BLAS attestation or hostile-code sandbox",
            "qualification_outcome": "NOT_EXECUTED",
            **SCIENTIFIC,
        }
    except (OSError, ValueError, KeyError, TypeError, zipfile.BadZipFile) as exc:
        if isinstance(exc, Hold):
            raise
        raise Hold("Native runtime identity could not be verified safely.") from exc
