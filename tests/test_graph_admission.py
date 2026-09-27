"""Admission contracts shared by JSON Schema, parsing and direct CPU execution."""

import json
from copy import deepcopy
from dataclasses import replace
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from qs_dmss.core.solver_registry import build_solver
from qs_dmss.io.config import load_config, parse_config

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def raw():
    data = load_config(ROOT / "configs/sierpinski_graph_spectral.yaml").to_dict()
    data["engine"].pop("grid_shape")
    data["fractal_graph"]["validation_levels"] = []
    return data


@pytest.fixture
def validator():
    schema = json.loads((ROOT / "schemas/run_config.schema.json").read_text())
    assert schema == json.loads(
        (ROOT / "src/qs_dmss/assets/schemas/run_config.schema.json").read_text()
    )
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def assert_admission(raw, validator, admitted):
    assert validator.is_valid(raw) is admitted
    if admitted:
        parse_config(raw)
    else:
        with pytest.raises(ValueError):
            parse_config(raw)


@pytest.mark.parametrize("boundary", ["dirichlet", "neumann"])
@pytest.mark.parametrize("level", range(6))
def test_level_shape_work_and_validation_boundaries(raw, validator, level, boundary):
    raw["fractal_graph"].update(level=level, boundary_condition=boundary)
    if level == 0 and boundary == "dirichlet":
        assert_admission(raw, validator, False)
        return
    vertices = (3 ** (level + 1) + 3) // 2 - (3 if boundary == "dirichlet" else 0)
    limit = min(10000, 100_000_000 // (2 * vertices**2))
    raw["engine"]["num_steps"] = limit
    assert_admission(raw, validator, True)
    raw["engine"]["grid_shape"] = [vertices, 1, 1]
    assert_admission(raw, validator, True)
    invalid = deepcopy(raw)
    invalid["engine"]["num_steps"] = limit + 1
    assert_admission(invalid, validator, False)
    invalid = deepcopy(raw)
    invalid["engine"]["grid_shape"][0] += 1
    assert_admission(invalid, validator, False)
    for levels, admitted in [([level], True), ([level, level], False),
                             ([level + 1], False), ([0], boundary == "neumann")]:
        variant = deepcopy(raw)
        variant["fractal_graph"]["validation_levels"] = levels
        assert_admission(variant, validator, admitted)


@pytest.mark.parametrize("omitted", [("level",), ("boundary_condition",),
                                    ("level", "boundary_condition")])
def test_graph_defaults_keep_shape_and_work_constraints(raw, validator, omitted):
    raw["fractal_graph"].update(level=4, boundary_condition="dirichlet")
    for key in omitted:
        raw["fractal_graph"].pop(key)
    vertices = 120
    raw["engine"].update(grid_shape=[vertices, 1, 1], num_steps=3472)
    assert_admission(raw, validator, True)
    raw["engine"]["num_steps"] = 3473
    assert_admission(raw, validator, False)


@pytest.mark.parametrize("backend,shape", [("numpy", [8, 8, 8]),
                                          ("numpy_fractal_ssfm", [8, 8, 1]),
                                          ("cupy_fractal_ssfm", [8, 8, 1])])
def test_legacy_backends_keep_rectangular_shape_contract(raw, validator, backend, shape):
    raw.pop("fractal_graph")
    raw["engine"].update(backend=backend, grid_shape=shape)
    assert_admission(raw, validator, True)
    raw["engine"]["grid_shape"][1] = 1
    assert_admission(raw, validator, False)
    raw["engine"].pop("grid_shape")
    assert_admission(raw, validator, False)


@pytest.mark.parametrize("section,field,value", [
    ("initial", "amplitude", 1e308), ("initial", "width", 1e-300),
    ("engine", "time_step", 1e308), ("engine", "mass", 1e-320),
])
def test_nonrepresentable_runs_fail_without_nonfinite_evidence(raw, section, field, value):
    raw["fractal_graph"]["level"] = 1
    raw["engine"]["num_steps"] = 1
    raw[section][field] = value
    with pytest.raises(ValueError, match="finite|representable|zero"):
        build_solver(parse_config(raw)).run()


@pytest.mark.parametrize("value", [True, "invalid", float("inf"), float("nan")])
def test_direct_solver_rejects_invalid_coupling_before_allocation(raw, value, monkeypatch):
    config = parse_config(raw)
    config = replace(config, engine=replace(config.engine, g_int=value))

    def forbidden(*args, **kwargs):
        pytest.fail("Invalid coupling reached graph allocation")

    monkeypatch.setattr("qs_dmss.core.fractal_spectral.build_sierpinski_gasket", forbidden)
    with pytest.raises(ValueError, match="finite"):
        build_solver(config)
