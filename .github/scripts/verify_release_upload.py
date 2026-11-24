"""Verify the exact publication packet against an independently approved digest."""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import re
from pathlib import Path

MANIFEST_NAME = "qs-dmss-release-manifest.json"
MANIFEST_MAX_BYTES = 4096


def _unique_mapping(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for name, value in pairs:
        if name in result:
            raise ValueError("manifest contains a duplicate key")
        result[name] = value
    return result


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _is_digest(value: object) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def verify_packet(packet: Path, tag: str, source_commit: str, manifest_sha256: str) -> dict[str, str]:
    if not _is_digest(manifest_sha256):
        raise ValueError("expected a lowercase SHA-256 manifest digest")
    if not re.fullmatch(r"v[0-9]+\.[0-9]+\.[0-9]+", tag):
        raise ValueError("expected a final release tag")
    if not re.fullmatch(r"[0-9a-f]{40}", source_commit):
        raise ValueError("expected the full checked-out Git commit")

    manifest_path = packet / MANIFEST_NAME
    dist = packet / "dist"
    if packet.is_symlink() or not packet.is_dir():
        raise ValueError("publication packet must be a directory")
    if {path.name for path in packet.iterdir()} != {MANIFEST_NAME, "dist"}:
        raise ValueError("packet must contain only the manifest and dist directory")
    if manifest_path.is_symlink() or not manifest_path.is_file():
        raise ValueError("manifest must be a regular file")
    if dist.is_symlink() or not dist.is_dir():
        raise ValueError("dist must be a directory")

    with manifest_path.open("rb") as stream:
        manifest_bytes = stream.read(MANIFEST_MAX_BYTES + 1)
    if len(manifest_bytes) > MANIFEST_MAX_BYTES:
        raise ValueError("manifest exceeds the size limit")
    if not hmac.compare_digest(hashlib.sha256(manifest_bytes).hexdigest(), manifest_sha256):
        raise ValueError("manifest SHA-256 does not match the approved digest")
    manifest = json.loads(manifest_bytes.decode("utf-8"), object_pairs_hook=_unique_mapping)
    if not isinstance(manifest, dict) or set(manifest) != {
        "schema_version", "tag", "source_commit", "artifacts"
    }:
        raise ValueError("unexpected manifest fields")
    if type(manifest["schema_version"]) is not int or manifest["schema_version"] != 1:
        raise ValueError("unsupported manifest schema version")
    if manifest["tag"] != tag or manifest["source_commit"] != source_commit:
        raise ValueError("manifest tag or source commit does not match the checked-out release")

    version = tag.removeprefix("v")
    expected = {f"qs_dmss-{version}-py3-none-any.whl", f"qs_dmss-{version}.tar.gz"}
    artifacts = manifest["artifacts"]
    if not isinstance(artifacts, dict) or set(artifacts) != expected:
        raise ValueError("manifest must name the expected wheel and sdist")
    if {path.name for path in dist.iterdir()} != expected:
        raise ValueError("dist must contain exactly the expected wheel and sdist")

    verified = {}
    for name in sorted(expected):
        path = dist / name
        if not _is_digest(artifacts[name]):
            raise ValueError(f"invalid manifest digest for {name}")
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"artifact must be a regular file: {name}")
        actual = _sha256(path)
        if not hmac.compare_digest(actual, artifacts[name]):
            raise ValueError(f"artifact SHA-256 does not match the manifest: {name}")
        verified[name] = actual
    return verified


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet", type=Path, required=True)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--manifest-sha256", required=True)
    args = parser.parse_args()
    try:
        verified = verify_packet(args.packet, args.tag, args.source_commit, args.manifest_sha256)
    except (OSError, RecursionError, ValueError) as exc:
        raise SystemExit(f"Release upload refused: {exc}") from None

    print("### Verified release packet")
    print(f"- Tag: `{args.tag}`")
    print(f"- Source commit: `{args.source_commit}`")
    print(f"- Manifest SHA-256: `{args.manifest_sha256}`")
    for name, digest in verified.items():
        print(f"- `{name}`: `{digest}`")


if __name__ == "__main__":
    main()
