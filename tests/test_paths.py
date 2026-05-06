from __future__ import annotations

from pathlib import Path

import pytest

from qs_dmss.paths import contained_path, safe_filename


def test_safe_filename_removes_path_components_and_enforces_suffix() -> None:
    assert safe_filename(
        "../../outside/demo",
        default="cockpit.yaml",
        suffixes=(".yaml", ".yml"),
    ) == "demo.yaml"


def test_contained_path_rejects_root_escape(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="escapes expected root"):
        contained_path(tmp_path, "..", "outside.yaml")
