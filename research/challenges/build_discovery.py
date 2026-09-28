"""Generate the two read-only discovery surfaces from validated frozen evidence.

Generated files are committed so portal builds and installed wheels need neither
research dependencies nor runtime archive processing. CI checks exact parity.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path("research/challenges")
DESTINATIONS = (Path("site"), Path("src/qs_dmss/cockpit/static"))


def render_assets(root: Path = ROOT) -> dict[Path, bytes]:
    spec = importlib.util.spec_from_file_location("challenge_validator", root / SOURCE / "validate_registry.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    registry = module.read_json((root / SOURCE / "registry-v1.json").read_bytes())
    module.validate_registry(registry, root)
    data = (json.dumps(registry, ensure_ascii=True, sort_keys=True, indent=2) + "\n").encode("utf-8")
    script = (root / SOURCE / "discovery.js").read_text(encoding="utf-8")
    if script.count("__REGISTRY_SHA256__") != 1:
        raise ValueError("Expected exactly one registry hash placeholder")
    script = script.replace("__REGISTRY_SHA256__", hashlib.sha256(data).hexdigest())
    assets = {
        "scientific-challenges.json": data,
        "scientific-challenges.js": script.encode("utf-8"),
        "scientific-challenges.css": (root / SOURCE / "discovery.css").read_text(encoding="utf-8").encode("utf-8"),
    }
    return {destination / name: content for destination in DESTINATIONS for name, content in assets.items()}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Reject missing or stale generated assets without writing")
    args = parser.parse_args()
    assets = render_assets()
    if args.check:
        stale = [str(path) for path, data in assets.items()
                 if not (ROOT / path).is_file() or (ROOT / path).read_bytes() != data]
        if stale:
            raise SystemExit("Regenerate discovery assets: " + ", ".join(stale))
        print("Discovery assets consistent with validated registry and templates (6 files).")
    else:
        for path, data in assets.items():
            (ROOT / path).write_bytes(data)
        print("Generated 6 discovery assets; numerical evidence and registry unchanged.")


if __name__ == "__main__":
    main()
