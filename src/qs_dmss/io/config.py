from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

SUPPORTED_BACKENDS = ("numpy", "numpy_fractal_ssfm", "cupy_fractal_ssfm")
SUPPORTED_FRACTAL_BACKENDS = ("numpy_fractal_ssfm", "cupy_fractal_ssfm")
SUPPORTED_GEOMETRY_MODES = ("fuzzy_potential", "soft_mask", "hard_mask")
SUPPORTED_FRACTALS = ("mandelbrot", "radial_shells")
SUPPORTED_DECISION_METRICS = (
    "energy_drift",
    "norm_drift",
    "max_density",
    "elapsed_seconds",
)
SUPPORTED_OBJECTIVE_GOALS = (
    "minimize",
    "minimize_abs",
    "maximize",
    "target",
)
DEFAULT_RANKING_WEIGHT_ITEMS: tuple[tuple[str, float], ...] = (
    ("energy_drift", 1.0),
    ("norm_drift", 0.9),
    ("max_density", 0.6),
    ("elapsed_seconds", 0.3),
)


@dataclass(frozen=True)
class RunConfig:
    name: str
    seed: int
    output_root: str = "runs"


@dataclass(frozen=True)
class EngineConfig:
    backend: str
    grid_shape: tuple[int, int, int]
    box_size: float
    mass: float
    g_int: float
    time_step: float
    num_steps: int
    log_every: int = 1


@dataclass(frozen=True)
class FractalGeometryConfig:
    mode: str = "fuzzy_potential"
    fractal: str = "mandelbrot"
    potential_strength: float = 0.0
    boundary_epsilon: float = 0.04
    quadrant_gamma: tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0)
    mandelbrot_iterations: int = 64

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "fractal": self.fractal,
            "potential_strength": self.potential_strength,
            "boundary_epsilon": self.boundary_epsilon,
            "quadrant_gamma": list(self.quadrant_gamma),
            "mandelbrot_iterations": self.mandelbrot_iterations,
        }


@dataclass(frozen=True)
class SpectralConfig:
    dealias_fraction: float | None = None
    leakage_fraction: float = 0.8

    def to_dict(self) -> dict[str, Any]:
        return {
            "dealias_fraction": self.dealias_fraction,
            "leakage_fraction": self.leakage_fraction,
        }


@dataclass(frozen=True)
class InitialConditionConfig:
    kind: str
    amplitude: float = 1.0
    width: float = 0.2
    random_phase: bool = True


@dataclass(frozen=True)
class ObjectiveConfig:
    name: str
    summary: str
    primary_metric: str
    goal: str
    target_value: float | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "name": self.name,
            "summary": self.summary,
            "primary_metric": self.primary_metric,
            "goal": self.goal,
        }
        if self.target_value is not None:
            payload["target_value"] = self.target_value
        return payload


@dataclass(frozen=True)
class ConstraintConfig:
    max_abs_energy_drift: float | None = None
    max_abs_norm_drift: float | None = None
    min_max_density: float | None = None
    max_elapsed_seconds: float | None = None
    require_verification: bool = True

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        if self.max_abs_energy_drift is not None:
            payload["max_abs_energy_drift"] = self.max_abs_energy_drift
        if self.max_abs_norm_drift is not None:
            payload["max_abs_norm_drift"] = self.max_abs_norm_drift
        if self.min_max_density is not None:
            payload["min_max_density"] = self.min_max_density
        if self.max_elapsed_seconds is not None:
            payload["max_elapsed_seconds"] = self.max_elapsed_seconds
        if self.require_verification is not True:
            payload["require_verification"] = self.require_verification
        return payload


@dataclass(frozen=True)
class RankingConfig:
    primary_metric_weight: float = 2.0
    weights: tuple[tuple[str, float], ...] = DEFAULT_RANKING_WEIGHT_ITEMS

    def weights_dict(self) -> dict[str, float]:
        return dict(self.weights)

    def to_dict(self) -> dict[str, Any]:
        return {
            "primary_metric_weight": self.primary_metric_weight,
            "weights": self.weights_dict(),
        }


@dataclass(frozen=True)
class CampaignDimensionConfig:
    path: str
    values: tuple[int | float, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "values": list(self.values),
        }


@dataclass(frozen=True)
class CampaignConfig:
    label: str
    strategy: str = "grid"
    max_runs: int = 16
    dimensions: tuple[CampaignDimensionConfig, ...] = ()

    def planned_run_count(self) -> int:
        total = 1
        for dimension in self.dimensions:
            total *= len(dimension.values)
        return total

    def to_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "strategy": self.strategy,
            "max_runs": self.max_runs,
            "dimensions": [dimension.to_dict() for dimension in self.dimensions],
        }


@dataclass(frozen=True)
class SimulationConfig:
    run: RunConfig
    engine: EngineConfig
    initial: InitialConditionConfig
    geometry: FractalGeometryConfig | None = None
    spectral: SpectralConfig | None = None
    objective: ObjectiveConfig | None = None
    constraints: ConstraintConfig | None = None
    ranking: RankingConfig | None = None
    campaign: CampaignConfig | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "run": {
                "name": self.run.name,
                "seed": self.run.seed,
                "output_root": self.run.output_root,
            },
            "engine": {
                "backend": self.engine.backend,
                "grid_shape": list(self.engine.grid_shape),
                "box_size": self.engine.box_size,
                "mass": self.engine.mass,
                "g_int": self.engine.g_int,
                "time_step": self.engine.time_step,
                "num_steps": self.engine.num_steps,
                "log_every": self.engine.log_every,
            },
            "initial": {
                "kind": self.initial.kind,
                "amplitude": self.initial.amplitude,
                "width": self.initial.width,
                "random_phase": self.initial.random_phase,
            },
        }
        if self.geometry is not None:
            payload["geometry"] = self.geometry.to_dict()
        if self.spectral is not None:
            payload["spectral"] = self.spectral.to_dict()
        if self.objective is not None:
            payload["objective"] = self.objective.to_dict()
            payload["constraints"] = (self.constraints or ConstraintConfig()).to_dict()
            payload["ranking"] = (self.ranking or RankingConfig()).to_dict()
        if self.campaign is not None:
            payload["campaign"] = self.campaign.to_dict()
        return payload


def _require_mapping(data: Any, field_name: str) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ValueError(f"'{field_name}' must be a mapping")
    return data


def _require_int(value: Any, field_name: str, minimum: int | None = None) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"'{field_name}' must be an integer")
    if minimum is not None and value < minimum:
        raise ValueError(f"'{field_name}' must be >= {minimum}")
    return value


def _require_number(value: Any, field_name: str, positive: bool = False) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"'{field_name}' must be numeric")
    numeric_value = float(value)
    if positive and numeric_value <= 0:
        raise ValueError(f"'{field_name}' must be > 0")
    return numeric_value


def _require_non_negative_number(value: Any, field_name: str) -> float:
    numeric_value = _require_number(value, field_name)
    if numeric_value < 0:
        raise ValueError(f"'{field_name}' must be >= 0")
    return numeric_value


def _require_bool(value: Any, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"'{field_name}' must be a boolean")
    return value


def _require_string(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"'{field_name}' must be a non-empty string")
    return value.strip()


def _parse_optional_fraction(value: Any, field_name: str) -> float | None:
    if value is None:
        return None
    numeric_value = _require_number(value, field_name, positive=True)
    if numeric_value > 1.0:
        raise ValueError(f"'{field_name}' must be <= 1.0")
    return numeric_value


def _parse_geometry(data: Any) -> FractalGeometryConfig:
    geometry_data = _require_mapping(data or {}, "geometry")
    mode = _require_string(geometry_data.get("mode", "fuzzy_potential"), "geometry.mode")
    if mode not in SUPPORTED_GEOMETRY_MODES:
        supported = ", ".join(SUPPORTED_GEOMETRY_MODES)
        raise ValueError(f"'geometry.mode' must be one of: {supported}")

    fractal = _require_string(geometry_data.get("fractal", "mandelbrot"), "geometry.fractal")
    if fractal not in SUPPORTED_FRACTALS:
        supported = ", ".join(SUPPORTED_FRACTALS)
        raise ValueError(f"'geometry.fractal' must be one of: {supported}")

    quadrant_raw = geometry_data.get("quadrant_gamma", [1.0, 1.0, 1.0, 1.0])
    if not isinstance(quadrant_raw, list) or len(quadrant_raw) != 4:
        raise ValueError("'geometry.quadrant_gamma' must be a list of four numeric values")
    quadrant_gamma = tuple(
        _require_number(value, f"geometry.quadrant_gamma[{index}]")
        for index, value in enumerate(quadrant_raw)
    )

    return FractalGeometryConfig(
        mode=mode,
        fractal=fractal,
        potential_strength=_require_non_negative_number(
            geometry_data.get("potential_strength", 0.0),
            "geometry.potential_strength",
        ),
        boundary_epsilon=_require_number(
            geometry_data.get("boundary_epsilon", 0.04),
            "geometry.boundary_epsilon",
            positive=True,
        ),
        quadrant_gamma=quadrant_gamma,  # type: ignore[arg-type]
        mandelbrot_iterations=_require_int(
            geometry_data.get("mandelbrot_iterations", 64),
            "geometry.mandelbrot_iterations",
            minimum=1,
        ),
    )


def _parse_spectral(data: Any) -> SpectralConfig:
    spectral_data = _require_mapping(data or {}, "spectral")
    return SpectralConfig(
        dealias_fraction=_parse_optional_fraction(
            spectral_data.get("dealias_fraction"),
            "spectral.dealias_fraction",
        ),
        leakage_fraction=_parse_optional_fraction(
            spectral_data.get("leakage_fraction", 0.8),
            "spectral.leakage_fraction",
        )
        or 0.8,
    )


def _parse_objective(data: Any) -> ObjectiveConfig:
    objective_data = _require_mapping(data, "objective")
    name = _require_string(objective_data.get("name"), "objective.name")
    summary = str(objective_data.get("summary", "")).strip()
    primary_metric = _require_string(
        objective_data.get("primary_metric"),
        "objective.primary_metric",
    )
    if primary_metric not in SUPPORTED_DECISION_METRICS:
        supported = ", ".join(SUPPORTED_DECISION_METRICS)
        raise ValueError(f"'objective.primary_metric' must be one of: {supported}")

    goal = _require_string(objective_data.get("goal"), "objective.goal")
    if goal not in SUPPORTED_OBJECTIVE_GOALS:
        supported_goals = ", ".join(SUPPORTED_OBJECTIVE_GOALS)
        raise ValueError(f"'objective.goal' must be one of: {supported_goals}")

    target_raw = objective_data.get("target_value")
    target_value = None
    if target_raw is not None:
        target_value = _require_number(target_raw, "objective.target_value")
    if goal == "target" and target_value is None:
        raise ValueError("'objective.target_value' is required when objective.goal is 'target'")

    return ObjectiveConfig(
        name=name,
        summary=summary,
        primary_metric=primary_metric,
        goal=goal,
        target_value=target_value,
    )


def _parse_constraints(data: Any) -> ConstraintConfig:
    if data is None:
        return ConstraintConfig()
    constraint_data = _require_mapping(data, "constraints")
    return ConstraintConfig(
        max_abs_energy_drift=(
            _require_non_negative_number(
                constraint_data["max_abs_energy_drift"],
                "constraints.max_abs_energy_drift",
            )
            if "max_abs_energy_drift" in constraint_data
            else None
        ),
        max_abs_norm_drift=(
            _require_non_negative_number(
                constraint_data["max_abs_norm_drift"],
                "constraints.max_abs_norm_drift",
            )
            if "max_abs_norm_drift" in constraint_data
            else None
        ),
        min_max_density=(
            _require_number(
                constraint_data["min_max_density"],
                "constraints.min_max_density",
            )
            if "min_max_density" in constraint_data
            else None
        ),
        max_elapsed_seconds=(
            _require_non_negative_number(
                constraint_data["max_elapsed_seconds"],
                "constraints.max_elapsed_seconds",
            )
            if "max_elapsed_seconds" in constraint_data
            else None
        ),
        require_verification=_require_bool(
            constraint_data.get("require_verification", True),
            "constraints.require_verification",
        ),
    )


def _parse_ranking(data: Any) -> RankingConfig:
    if data is None:
        return RankingConfig()
    ranking_data = _require_mapping(data, "ranking")
    weights_data = ranking_data.get("weights")
    if weights_data is None:
        weights = DEFAULT_RANKING_WEIGHT_ITEMS
    else:
        weights_mapping = _require_mapping(weights_data, "ranking.weights")
        weights = tuple(
            (
                metric,
                _require_non_negative_number(
                    weights_mapping.get(metric, default_value),
                    f"ranking.weights.{metric}",
                ),
            )
            for metric, default_value in DEFAULT_RANKING_WEIGHT_ITEMS
        )

    return RankingConfig(
        primary_metric_weight=_require_non_negative_number(
            ranking_data.get("primary_metric_weight", 2.0),
            "ranking.primary_metric_weight",
        ),
        weights=weights,
    )


def _parse_campaign(data: Any) -> CampaignConfig:
    from qs_dmss.experiment import coerce_parameter_values, get_sweep_parameter

    campaign_data = _require_mapping(data, "campaign")
    label = _require_string(campaign_data.get("label"), "campaign.label")
    strategy = _require_string(campaign_data.get("strategy", "grid"), "campaign.strategy")
    if strategy != "grid":
        raise ValueError("'campaign.strategy' must be 'grid' in this reference build")

    max_runs = _require_int(campaign_data.get("max_runs", 16), "campaign.max_runs", minimum=2)
    dimensions_data = campaign_data.get("dimensions")
    if not isinstance(dimensions_data, list) or not dimensions_data:
        raise ValueError("'campaign.dimensions' must be a non-empty list")

    dimensions: list[CampaignDimensionConfig] = []
    seen_paths: set[str] = set()
    for index, raw_dimension in enumerate(dimensions_data):
        prefix = f"campaign.dimensions[{index}]"
        dimension_data = _require_mapping(raw_dimension, prefix)
        path = _require_string(dimension_data.get("path"), f"{prefix}.path")
        if path in seen_paths:
            raise ValueError(f"Duplicate campaign dimension path: {path}")
        get_sweep_parameter(path)

        raw_values = dimension_data.get("values")
        if not isinstance(raw_values, list):
            raise ValueError(f"'{prefix}.values' must be a list")
        values = tuple(coerce_parameter_values(path, raw_values, minimum_count=1))
        dimensions.append(CampaignDimensionConfig(path=path, values=values))
        seen_paths.add(path)

    campaign = CampaignConfig(
        label=label,
        strategy=strategy,
        max_runs=max_runs,
        dimensions=tuple(dimensions),
    )
    planned_runs = campaign.planned_run_count()
    if planned_runs < 2:
        raise ValueError("Campaign requires at least two planned runs")
    if planned_runs > campaign.max_runs:
        raise ValueError(
            f"Campaign expands to {planned_runs} runs, which exceeds campaign.max_runs={campaign.max_runs}"
        )
    return campaign


def parse_config(data: dict[str, Any]) -> SimulationConfig:
    root = _require_mapping(data, "config")
    run_data = _require_mapping(root.get("run"), "run")
    engine_data = _require_mapping(root.get("engine"), "engine")
    initial_data = _require_mapping(root.get("initial"), "initial")

    name = _require_string(run_data.get("name"), "run.name")
    seed = _require_int(run_data.get("seed"), "run.seed", minimum=0)
    output_root = run_data.get("output_root", "runs")
    if not isinstance(output_root, str) or not output_root.strip():
        raise ValueError("'run.output_root' must be a non-empty string")

    backend = _require_string(engine_data.get("backend"), "engine.backend")
    if backend not in SUPPORTED_BACKENDS:
        supported = ", ".join(SUPPORTED_BACKENDS)
        raise ValueError(f"'engine.backend' must be one of: {supported}")

    grid_shape = engine_data.get("grid_shape")
    if (
        not isinstance(grid_shape, list)
        or len(grid_shape) != 3
        or any(not isinstance(value, int) or isinstance(value, bool) for value in grid_shape)
    ):
        raise ValueError("'engine.grid_shape' must be a list of three integers")
    if backend in SUPPORTED_FRACTAL_BACKENDS:
        if grid_shape[0] < 2 or grid_shape[1] < 2 or grid_shape[2] != 1:
            raise ValueError(
                "'engine.grid_shape' must be [nx, ny, 1] with nx and ny >= 2 "
                "for fractal SSFM backends"
            )
    elif any(value < 2 for value in grid_shape):
        raise ValueError("'engine.grid_shape' must be a list of three integers >= 2")

    if backend == "numpy" and (root.get("geometry") is not None or root.get("spectral") is not None):
        raise ValueError("'geometry' and 'spectral' are only supported by fractal SSFM backends")

    geometry = _parse_geometry(root.get("geometry")) if backend in SUPPORTED_FRACTAL_BACKENDS else None
    spectral = _parse_spectral(root.get("spectral")) if backend in SUPPORTED_FRACTAL_BACKENDS else None

    initial_kind = initial_data.get("kind")
    if initial_kind not in {"gaussian", "uniform"}:
        raise ValueError("'initial.kind' must be one of: gaussian, uniform")

    objective_data = root.get("objective")
    constraints_data = root.get("constraints")
    ranking_data = root.get("ranking")
    campaign_data = root.get("campaign")

    if objective_data is None:
        if constraints_data is not None or ranking_data is not None or campaign_data is not None:
            raise ValueError("'objective' is required when constraints, ranking, or campaign are provided")
        objective = None
        constraints = None
        ranking = None
        campaign = None
    else:
        objective = _parse_objective(objective_data)
        constraints = _parse_constraints(constraints_data)
        ranking = _parse_ranking(ranking_data)
        campaign = _parse_campaign(campaign_data) if campaign_data is not None else None

    return SimulationConfig(
        run=RunConfig(
            name=name,
            seed=seed,
            output_root=output_root.strip(),
        ),
        engine=EngineConfig(
            backend=backend,
            grid_shape=tuple(grid_shape),
            box_size=_require_number(engine_data.get("box_size"), "engine.box_size", positive=True),
            mass=_require_number(engine_data.get("mass"), "engine.mass", positive=True),
            g_int=_require_number(engine_data.get("g_int"), "engine.g_int"),
            time_step=_require_number(
                engine_data.get("time_step"),
                "engine.time_step",
                positive=True,
            ),
            num_steps=_require_int(engine_data.get("num_steps"), "engine.num_steps", minimum=1),
            log_every=_require_int(engine_data.get("log_every", 1), "engine.log_every", minimum=1),
        ),
        initial=InitialConditionConfig(
            kind=initial_kind,
            amplitude=_require_number(
                initial_data.get("amplitude", 1.0),
                "initial.amplitude",
                positive=True,
            ),
            width=_require_number(
                initial_data.get("width", 0.2),
                "initial.width",
                positive=True,
            ),
            random_phase=_require_bool(
                initial_data.get("random_phase", True),
                "initial.random_phase",
            ),
        ),
        geometry=geometry,
        spectral=spectral,
        objective=objective,
        constraints=constraints,
        ranking=ranking,
        campaign=campaign,
    )


def canonicalize_config(config: SimulationConfig) -> str:
    return json.dumps(config.to_dict(), sort_keys=True, separators=(",", ":"))


def config_digest(config: SimulationConfig) -> str:
    return hashlib.sha256(canonicalize_config(config).encode("utf-8")).hexdigest()


def load_config(path: str | Path) -> SimulationConfig:
    config_path = Path(path)
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if raw is None:
        raise ValueError(f"Configuration file is empty: {config_path}")
    if not isinstance(raw, dict):
        raise ValueError(f"Configuration root must be a mapping: {config_path}")
    return parse_config(raw)


def config_digest_for_file(path: str | Path) -> str:
    return config_digest(load_config(path))


def write_config(config: SimulationConfig, path: str | Path) -> None:
    config_path = Path(path)
    config_path.write_text(
        yaml.safe_dump(config.to_dict(), sort_keys=False),
        encoding="utf-8",
    )
