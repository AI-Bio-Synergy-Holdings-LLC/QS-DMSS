"""Opt-in finite graph configuration; does not replace rectangular geometry."""

import math
from dataclasses import asdict, dataclass
from typing import Any

from qs_dmss.core.graph_policy import graph_resource_estimate


@dataclass(frozen=True)
class FractalGraphConfig:
    family: str = "sierpinski_gasket"
    level: int = 4
    boundary_condition: str = "dirichlet"
    device: str = "cpu"
    quadrant_gamma: tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0)
    quadrant_potential: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0)
    tail_fraction: float = 0.8
    artifact_eigenmodes: int = 16
    validation_levels: tuple[int, ...] = ()
    validation_eigenvalues: int = 8

    def __post_init__(self) -> None:
        if self.family != "sierpinski_gasket" or self.device != "cpu":
            raise ValueError("fractal_graph supports only sierpinski_gasket on cpu")
        graph_resource_estimate(self.level, self.boundary_condition)
        for name in ("quadrant_gamma", "quadrant_potential"):
            values = getattr(self, name)
            if not isinstance(values, (tuple, list)) or len(values) != 4 or any(
                isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v)
                for v in values
            ):
                raise ValueError(f"fractal_graph.{name} requires four finite numbers")
        if (isinstance(self.tail_fraction, bool)
                or not isinstance(self.tail_fraction, (int, float))
                or not 0 < self.tail_fraction <= 1):
            raise ValueError("fractal_graph.tail_fraction must be in (0, 1]")
        for name in ("artifact_eigenmodes", "validation_eigenvalues"):
            value = getattr(self, name)
            if type(value) is not int or not 1 <= value <= 366:
                raise ValueError(f"fractal_graph.{name} must be an integer from 1 to 366")
        if not isinstance(self.validation_levels, (tuple, list)) or len(self.validation_levels) > 6:
            raise ValueError("fractal_graph.validation_levels requires at most six levels")
        for level in self.validation_levels:
            graph_resource_estimate(level, self.boundary_condition)
            if level > self.level:
                raise ValueError("validation_levels cannot exceed fractal_graph.level")
        if len(set(self.validation_levels)) != len(self.validation_levels):
            raise ValueError("validation_levels must be unique")

    @property
    def grid_shape(self) -> tuple[int, int, int]:
        return (graph_resource_estimate(self.level, self.boundary_condition)["active_vertices"], 1, 1)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        for name in ("quadrant_gamma", "quadrant_potential", "validation_levels"):
            data[name] = list(data[name])
        return data


def parse_fractal_graph(data: Any) -> FractalGraphConfig:
    if not isinstance(data, dict):
        raise ValueError("fractal_graph must be a mapping")
    if set(data) - set(FractalGraphConfig.__dataclass_fields__):
        raise ValueError("Unknown fractal_graph configuration field")
    values = dict(data)
    for name in ("quadrant_gamma", "quadrant_potential", "validation_levels"):
        if name in values:
            if not isinstance(values[name], list):
                raise ValueError(f"fractal_graph.{name} must be a list")
            values[name] = tuple(values[name])
    return FractalGraphConfig(**values)
