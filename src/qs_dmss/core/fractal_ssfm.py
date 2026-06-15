from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from qs_dmss.core.solver import SimulationResult
from qs_dmss.io.config import (
    EngineConfig,
    FractalGeometryConfig,
    InitialConditionConfig,
    SpectralConfig,
)


@dataclass(frozen=True)
class FractalFields:
    x: Any
    y: Any
    mask: Any
    potential: Any
    gamma: Any


class FractalQuadrantSSFMSolver:
    """Pseudo-spectral NLSE/GPE-style solver for fuzzy fractal effective potentials.

    This backend intentionally remains an embedded rectangular-grid approximation. The
    defensible default is ``geometry.mode == "fuzzy_potential"``, where geometry is a
    real-valued phase potential. Hard and soft masks are available for exploratory
    comparisons and are labelled as non-conservative in diagnostics.
    """

    def __init__(
        self,
        engine: EngineConfig,
        initial: InitialConditionConfig,
        seed: int,
        geometry: FractalGeometryConfig | None = None,
        spectral: SpectralConfig | None = None,
    ) -> None:
        if engine.backend == "cupy_fractal_ssfm":
            try:
                import cupy as xp  # type: ignore[import-not-found]
            except ModuleNotFoundError as exc:
                raise RuntimeError(
                    "backend='cupy_fractal_ssfm' requires CuPy and a CUDA-capable runtime. "
                    "Install a CUDA-compatible CuPy package before selecting this backend."
                ) from exc
        elif engine.backend == "numpy_fractal_ssfm":
            xp = np
        else:
            raise ValueError(
                "FractalQuadrantSSFMSolver requires backend='numpy_fractal_ssfm' "
                "or backend='cupy_fractal_ssfm'."
            )
        if engine.grid_shape[2] != 1:
            raise ValueError(
                "Fractal SSFM is currently a 2-D solver embedded as grid_shape=[nx, ny, 1]."
            )

        self.xp = xp
        self.engine = engine
        self.initial = initial
        self.geometry = geometry or FractalGeometryConfig()
        self.spectral = spectral or SpectralConfig()
        self.rng = xp.random.default_rng(seed)
        self.nx, self.ny, _ = engine.grid_shape
        self.box_size = engine.box_size
        self.dx = self.box_size / self.nx
        self.dy = self.box_size / self.ny
        self.cell_area = self.dx * self.dy
        self.time_step = engine.time_step
        self.num_steps = engine.num_steps
        self.log_every = engine.log_every

        kx = 2.0 * xp.pi * xp.fft.fftfreq(self.nx, d=self.dx)
        ky = 2.0 * xp.pi * xp.fft.fftfreq(self.ny, d=self.dy)
        self.kx, self.ky = xp.meshgrid(kx, ky, indexing="ij")
        self.k2 = self.kx**2 + self.ky**2
        self.linear_half_phase = xp.exp(
            -1j * self.time_step * self.k2 / (4.0 * self.engine.mass)
        )
        self.dealias_filter = self._build_dealias_filter()
        self.fields = self._build_fields()

    def _to_float(self, value: Any) -> float:
        if hasattr(value, "get"):
            value = value.get()
        return float(value)

    def _as_numpy(self, value: Any) -> np.ndarray:
        if self.engine.backend == "cupy_fractal_ssfm":
            return self.xp.asnumpy(value)
        return np.asarray(value)

    def _coordinate_mesh(self) -> tuple[Any, Any]:
        xp = self.xp
        axis_x = xp.linspace(
            -self.box_size / 2.0,
            self.box_size / 2.0,
            self.nx,
            endpoint=False,
        )
        axis_y = xp.linspace(
            -self.box_size / 2.0,
            self.box_size / 2.0,
            self.ny,
            endpoint=False,
        )
        return xp.meshgrid(axis_x, axis_y, indexing="ij")

    def _build_dealias_filter(self) -> Any | None:
        if self.spectral.dealias_fraction is None:
            return None
        xp = self.xp
        fraction = self.spectral.dealias_fraction
        kx_max = xp.max(xp.abs(self.kx))
        ky_max = xp.max(xp.abs(self.ky))
        return (
            (xp.abs(self.kx) <= fraction * kx_max)
            & (xp.abs(self.ky) <= fraction * ky_max)
        ).astype(xp.float64)

    def _build_fields(self) -> FractalFields:
        x, y = self._coordinate_mesh()
        if self.geometry.fractal == "mandelbrot":
            mask = self._mandelbrot_occupancy(x, y)
        elif self.geometry.fractal == "radial_shells":
            mask = self._radial_shell_occupancy(x, y)
        else:  # Guarded by config parsing; kept defensive for direct construction.
            raise ValueError(f"Unsupported fractal geometry: {self.geometry.fractal}")

        potential = self.geometry.potential_strength * (1.0 - mask)
        gamma = self._quadrant_gamma(x, y, mask)
        return FractalFields(x=x, y=y, mask=mask, potential=potential, gamma=gamma)

    def _mandelbrot_occupancy(self, x: Any, y: Any) -> Any:
        xp = self.xp
        cx = 3.0 * (x + self.box_size / 2.0) / self.box_size - 2.0
        cy = 3.0 * (y + self.box_size / 2.0) / self.box_size - 1.5
        c = cx + 1j * cy
        z = xp.zeros_like(c)
        counts = xp.zeros(c.shape, dtype=xp.float64)
        active = xp.ones(c.shape, dtype=xp.bool_)
        for _ in range(self.geometry.mandelbrot_iterations):
            z = xp.where(active, z * z + c, z)
            escaped = xp.abs(z) > 2.0
            counts += active & (~escaped)
            active &= ~escaped
        raw = counts / float(max(self.geometry.mandelbrot_iterations, 1))
        epsilon = max(self.geometry.boundary_epsilon, 1e-12)
        return 0.5 * (1.0 + xp.tanh((raw - 0.5) / epsilon))

    def _radial_shell_occupancy(self, x: Any, y: Any) -> Any:
        xp = self.xp
        radius = xp.sqrt(x**2 + y**2)
        normalized = radius / max(float(self.box_size) / 2.0, 1e-12)
        raw = 0.5 + 0.5 * xp.cos(8.0 * xp.pi * normalized)
        epsilon = max(self.geometry.boundary_epsilon, 1e-12)
        return 0.5 * (1.0 + xp.tanh((raw - 0.5) / epsilon))

    def _quadrant_gamma(self, x: Any, y: Any, mask: Any) -> Any:
        xp = self.xp
        q1 = ((x >= 0.0) & (y >= 0.0)).astype(xp.float64)
        q2 = ((x < 0.0) & (y >= 0.0)).astype(xp.float64)
        q3 = ((x < 0.0) & (y < 0.0)).astype(xp.float64)
        q4 = ((x >= 0.0) & (y < 0.0)).astype(xp.float64)
        g1, g2, g3, g4 = self.geometry.quadrant_gamma
        return self.engine.g_int * (g1 * q1 + g2 * q2 + g3 * q3 + g4 * q4) * mask

    def initialize_wavefunction(self) -> Any:
        xp = self.xp
        if self.initial.kind == "uniform":
            density = xp.full((self.nx, self.ny), self.initial.amplitude, dtype=xp.float64)
        elif self.initial.kind == "gaussian":
            radius_squared = self.fields.x**2 + self.fields.y**2
            density = self.initial.amplitude * xp.exp(
                -radius_squared / (2.0 * self.initial.width**2)
            )
        else:
            raise ValueError(f"Unsupported initial condition kind: {self.initial.kind}")

        amplitude = xp.sqrt(density)
        if self.initial.random_phase:
            phase = self.rng.uniform(0.0, 2.0 * xp.pi, size=(self.nx, self.ny))
            psi = amplitude * xp.exp(1j * phase)
        else:
            psi = amplitude.astype(xp.complex128)

        return self._apply_geometry_projection(psi)

    def compute_norm(self, psi: Any) -> float:
        xp = self.xp
        return self._to_float(xp.sum(xp.abs(psi) ** 2) * self.cell_area)

    def _spectral_power(self, psi: Any) -> Any:
        xp = self.xp
        psi_k = xp.fft.fft2(psi)
        return xp.abs(psi_k) ** 2

    def compute_spectral_leakage(self, psi: Any) -> float:
        xp = self.xp
        power = self._spectral_power(psi)
        total = xp.sum(power) + 1e-300
        fraction = self.spectral.leakage_fraction
        kx_max = xp.max(xp.abs(self.kx))
        ky_max = xp.max(xp.abs(self.ky))
        edge = (xp.abs(self.kx) > fraction * kx_max) | (xp.abs(self.ky) > fraction * ky_max)
        return self._to_float(xp.sum(power * edge.astype(xp.float64)) / total)

    def compute_aliasing_ratio(self, psi: Any) -> float:
        xp = self.xp
        fraction = self.spectral.dealias_fraction or self.spectral.leakage_fraction
        power = self._spectral_power(psi)
        total = xp.sum(power) + 1e-300
        kx_max = xp.max(xp.abs(self.kx))
        ky_max = xp.max(xp.abs(self.ky))
        high = (xp.abs(self.kx) > fraction * kx_max) | (xp.abs(self.ky) > fraction * ky_max)
        return self._to_float(xp.sum(power * high.astype(xp.float64)) / total)

    def compute_energy(self, psi: Any) -> float:
        xp = self.xp
        density = xp.abs(psi) ** 2
        psi_k = xp.fft.fft2(psi)
        kinetic = xp.sum(self.k2 * xp.abs(psi_k) ** 2).real / (
            2.0 * self.engine.mass * self.nx * self.ny
        )
        potential = xp.sum(density * self.fields.potential).real * self.cell_area
        interaction = 0.5 * xp.sum(self.fields.gamma * density**2).real * self.cell_area
        return self._to_float(kinetic + potential + interaction)

    def record_snapshot(self, step: int, psi: Any) -> dict[str, float | int]:
        xp = self.xp
        density = xp.abs(psi) ** 2
        return {
            "step": step,
            "norm": round(self.compute_norm(psi), 12),
            "energy": round(self.compute_energy(psi), 12),
            "max_density": round(self._to_float(xp.max(density)), 12),
        }

    def _apply_geometry_projection(self, psi: Any) -> Any:
        xp = self.xp
        if self.geometry.mode == "hard_mask":
            return psi * (self.fields.mask >= 0.5).astype(xp.float64)
        if self.geometry.mode == "soft_mask":
            return psi * xp.sqrt(self.fields.mask)
        return psi

    def step(self, psi: Any) -> Any:
        xp = self.xp
        psi = xp.fft.ifft2(xp.fft.fft2(psi) * self.linear_half_phase)

        density = xp.abs(psi) ** 2
        nonlinear_phase = xp.exp(
            -1j * self.time_step * (self.fields.potential + self.fields.gamma * density)
        )
        psi = self._apply_geometry_projection(nonlinear_phase * psi)

        psi_k = xp.fft.fft2(psi) * self.linear_half_phase
        if self.dealias_filter is not None:
            psi_k *= self.dealias_filter
        return self._apply_geometry_projection(xp.fft.ifft2(psi_k))

    def _diagnostics(self, psi: Any, norm_initial: float) -> dict[str, Any]:
        xp = self.xp
        norm_final = self.compute_norm(psi)
        relative_norm_error = (norm_final - norm_initial) / norm_initial if norm_initial else 0.0
        nonconservative_reasons: list[str] = []
        if self.geometry.mode in {"soft_mask", "hard_mask"}:
            nonconservative_reasons.append(
                f"geometry_mode={self.geometry.mode} applies amplitude projection"
            )
        if self.spectral.dealias_fraction is not None:
            nonconservative_reasons.append("spectral de-alias filter removes high-frequency modes")

        return {
            "solver_family": "fractal_quadrant_ssfm",
            "backend": self.engine.backend,
            "geometry_mode": self.geometry.mode,
            "fractal": self.geometry.fractal,
            "conservation_mode": (
                "phase_only_fuzzy_potential"
                if not nonconservative_reasons
                else "nonconservative_exploratory"
            ),
            "nonconservative_reasons": nonconservative_reasons,
            "norm_initial": round(norm_initial, 12),
            "norm_final": round(norm_final, 12),
            "relative_norm_error": round(float(relative_norm_error), 12),
            "spectral_leakage": round(self.compute_spectral_leakage(psi), 12),
            "aliasing_ratio": round(self.compute_aliasing_ratio(psi), 12),
            "dealias_fraction": self.spectral.dealias_fraction,
            "leakage_fraction": self.spectral.leakage_fraction,
            "quadrant_gamma": list(self.geometry.quadrant_gamma),
            "potential_strength": self.geometry.potential_strength,
            "boundary_epsilon": self.geometry.boundary_epsilon,
            "mask_mean": round(self._to_float(xp.mean(self.fields.mask)), 12),
            "mask_min": round(self._to_float(xp.min(self.fields.mask)), 12),
            "mask_max": round(self._to_float(xp.max(self.fields.mask)), 12),
            "claim_boundary": (
                "Experimental pseudo-spectral nonlinear wave backend on a rectangular "
                "periodic grid. Fuzzy-potential mode is the scientific default; "
                "hard/soft masks are exploratory. This is not exact fractal-boundary "
                "PDE solving, peer-reviewed physical validation, or direct atomic-void modeling."
            ),
        }

    def run(self) -> SimulationResult:
        psi = self.initialize_wavefunction()
        norm_initial = self.compute_norm(psi)
        history: list[dict] = [self.record_snapshot(step=0, psi=psi)]
        for step in range(1, self.num_steps + 1):
            psi = self.step(psi)
            if step % self.log_every == 0 or step == self.num_steps:
                history.append(self.record_snapshot(step=step, psi=psi))

        density = self.xp.abs(psi) ** 2
        diagnostics = self._diagnostics(psi, norm_initial)
        return SimulationResult(
            psi=self._as_numpy(psi)[:, :, None],
            density=self._as_numpy(density)[:, :, None],
            history=history,
            diagnostics=diagnostics,
        )
