from __future__ import annotations

from qs_dmss.core.solver import QuantumScalarDarkMatterSolver
from qs_dmss.io.config import SimulationConfig


def build_solver(config: SimulationConfig):
    """Build the configured solver backend while preserving the NumPy default path."""

    backend = config.engine.backend
    if backend == "numpy":
        return QuantumScalarDarkMatterSolver(
            engine=config.engine,
            initial=config.initial,
            seed=config.run.seed,
        )

    if backend in {"numpy_fractal_ssfm", "cupy_fractal_ssfm"}:
        from qs_dmss.core.fractal_ssfm import FractalQuadrantSSFMSolver

        return FractalQuadrantSSFMSolver(
            engine=config.engine,
            initial=config.initial,
            seed=config.run.seed,
            geometry=config.geometry,
            spectral=config.spectral,
        )

    raise ValueError(f"Unsupported engine backend: {backend}")
