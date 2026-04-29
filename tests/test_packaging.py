from __future__ import annotations

from importlib import metadata
from pathlib import Path
import tomllib

import qs_dmss


def test_version_metadata_is_aligned() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    pyproject = tomllib.loads((repo_root / "pyproject.toml").read_text(encoding="utf-8"))
    declared_version = pyproject["project"]["version"]

    assert qs_dmss.__version__ == declared_version
    assert metadata.version("qs-dmss") == declared_version
