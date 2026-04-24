from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


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
class InitialConditionConfig:
    kind: str
    amplitude: float = 1.0
    width: float = 0.2
    random_phase: bool = True


@dataclass(frozen=True)
class SimulationConfig:
    run: RunConfig
    engine: EngineConfig
    initial: InitialConditionConfig

    def to_dict(self) -> dict[str, Any]:
        return {
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


def _require_mapping(data: Any, field_name: str) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ValueError(f"'{field_name}' must be a mapping")
    return data


def _require_int(value: Any, field_name: str, minimum: int | None = None) -> int:
    if not isinstance(value, int):
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


def _require_bool(value: Any, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"'{field_name}' must be a boolean")
    return value


def parse_config(data: dict[str, Any]) -> SimulationConfig:
    root = _require_mapping(data, "config")
    run_data = _require_mapping(root.get("run"), "run")
    engine_data = _require_mapping(root.get("engine"), "engine")
    initial_data = _require_mapping(root.get("initial"), "initial")

    name = run_data.get("name")
    if not isinstance(name, str) or not name.strip():
        raise ValueError("'run.name' must be a non-empty string")

    seed = _require_int(run_data.get("seed"), "run.seed", minimum=0)
    output_root = run_data.get("output_root", "runs")
    if not isinstance(output_root, str) or not output_root.strip():
        raise ValueError("'run.output_root' must be a non-empty string")

    backend = engine_data.get("backend")
    if backend != "numpy":
        raise ValueError("'engine.backend' must be 'numpy' in this reference build")

    grid_shape = engine_data.get("grid_shape")
    if (
        not isinstance(grid_shape, list)
        or len(grid_shape) != 3
        or any(not isinstance(value, int) or value < 2 for value in grid_shape)
    ):
        raise ValueError("'engine.grid_shape' must be a list of three integers >= 2")

    initial_kind = initial_data.get("kind")
    if initial_kind not in {"gaussian", "uniform"}:
        raise ValueError("'initial.kind' must be one of: gaussian, uniform")

    config = SimulationConfig(
        run=RunConfig(
            name=name.strip(),
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
    )
    return config


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
