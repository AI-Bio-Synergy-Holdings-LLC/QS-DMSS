from __future__ import annotations

import json
from pathlib import Path

from qs_dmss.cli import main
from qs_dmss.fractal_validation import (
    FRACTAL_VALIDATION_JSON_REPORT,
    FRACTAL_VALIDATION_MARKDOWN_REPORT,
    validate_fractal_ssfm,
)


def _write_tiny_fractal_config(path: Path) -> None:
    path.write_text(
        """
run:
  name: fractal-validation-test
  seed: 7
  output_root: runs
engine:
  backend: numpy_fractal_ssfm
  grid_shape: [8, 8, 1]
  box_size: 2.0
  mass: 1.0
  g_int: 0.5
  time_step: 0.001
  num_steps: 2
  log_every: 1
geometry:
  mode: fuzzy_potential
  fractal: mandelbrot
  potential_strength: 2.0
  boundary_epsilon: 0.1
  mandelbrot_iterations: 8
  quadrant_gamma: [1.0, 0.9, 1.1, 0.75]
spectral:
  dealias_fraction: null
  leakage_fraction: 0.8
initial:
  kind: gaussian
  amplitude: 1.0
  width: 0.3
  random_phase: false
""".lstrip(),
        encoding="utf-8",
    )


def test_fractal_validation_harness_writes_structured_reports(tmp_path: Path) -> None:
    config_path = tmp_path / "fractal-validation.yaml"
    output_root = tmp_path / "validation"
    _write_tiny_fractal_config(config_path)

    report = validate_fractal_ssfm(
        config_path=config_path,
        output_root=output_root,
    )

    assert report["success"] is True
    assert report["convergence"]["success"] is True
    assert len(report["convergence"]["runs"]) == 3
    assert len(report["convergence"]["comparisons"]) == 2
    assert report["convergence"]["estimated_order"] is not None
    assert report["norm_conservation"]["success"] is True
    assert report["geometry_comparison"]["success"] is True

    report_path = output_root / FRACTAL_VALIDATION_JSON_REPORT
    markdown_path = output_root / FRACTAL_VALIDATION_MARKDOWN_REPORT
    assert report_path.exists()
    assert markdown_path.exists()

    persisted = json.loads(report_path.read_text(encoding="utf-8"))
    assert persisted["schema_version"] == 1
    assert persisted["claim_boundary"].startswith("Experimental pseudo-spectral")
    assert all(
        run["verification"]["success"]
        for run in persisted["convergence"]["runs"]
    )

    variants_by_mode = {
        variant["geometry_mode"]: variant
        for variant in persisted["geometry_comparison"]["variants"]
    }
    assert variants_by_mode["fuzzy_potential"]["conservation_mode"] == (
        "phase_only_fuzzy_potential"
    )
    assert variants_by_mode["soft_mask"]["conservation_mode"] == (
        "nonconservative_exploratory"
    )
    assert variants_by_mode["hard_mask"]["nonconservative_reasons"]

    markdown = markdown_path.read_text(encoding="utf-8")
    assert "## Strang Convergence" in markdown
    assert "## Norm Conservation" in markdown
    assert "## Geometry Comparison" in markdown
    assert "not peer-reviewed physical validation" in markdown


def test_fractal_validation_cli_routes_to_harness(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    from qs_dmss import fractal_validation

    seen: dict[str, object] = {}

    def fake_validate_fractal_ssfm(
        config_path: str | Path,
        output_root: str | Path | None = None,
        *,
        norm_tolerance: float,
    ) -> dict[str, object]:
        seen["config_path"] = config_path
        seen["output_root"] = output_root
        seen["norm_tolerance"] = norm_tolerance
        return {
            "success": True,
            "report_path": str(tmp_path / FRACTAL_VALIDATION_JSON_REPORT),
            "markdown_report_path": str(tmp_path / FRACTAL_VALIDATION_MARKDOWN_REPORT),
        }

    monkeypatch.setattr(
        fractal_validation,
        "validate_fractal_ssfm",
        fake_validate_fractal_ssfm,
    )

    exit_code = main(
        [
            "validation",
            "fractal-ssfm",
            "--config",
            "example.yaml",
            "--output-root",
            str(tmp_path),
            "--norm-tolerance",
            "1e-8",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert seen == {
        "config_path": "example.yaml",
        "output_root": str(tmp_path),
        "norm_tolerance": 1e-8,
    }
    assert "Fractal SSFM validation passed." in captured.out


def test_fractal_validation_cli_uses_bundled_default_config(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    from qs_dmss import fractal_validation

    seen: dict[str, object] = {}

    def fake_validate_fractal_ssfm(
        config_path: str | Path,
        output_root: str | Path | None = None,
        *,
        norm_tolerance: float,
    ) -> dict[str, object]:
        seen["config_path"] = config_path
        seen["output_root"] = output_root
        seen["norm_tolerance"] = norm_tolerance
        return {
            "success": True,
            "report_path": str(tmp_path / FRACTAL_VALIDATION_JSON_REPORT),
            "markdown_report_path": str(tmp_path / FRACTAL_VALIDATION_MARKDOWN_REPORT),
        }

    monkeypatch.setattr(
        fractal_validation,
        "validate_fractal_ssfm",
        fake_validate_fractal_ssfm,
    )

    exit_code = main(
        [
            "validation",
            "fractal-ssfm",
            "--output-root",
            str(tmp_path),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert Path(seen["config_path"]).name == "fractal_quadrant_ssfm.yaml"
    assert Path(seen["config_path"]).is_file()
    assert seen["output_root"] == str(tmp_path)
    assert seen["norm_tolerance"] == 1e-9
    assert "Fractal SSFM validation passed." in captured.out
