from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from qs_dmss.io.config import EngineConfig, InitialConditionConfig


@dataclass(frozen=True)
class SimulationResult:
    psi: np.ndarray
    density: np.ndarray
    history: list[dict]


class QuantumScalarDarkMatterSolver:
    """Deterministic NumPy-first reference solver for QS-DMSS."""

    def __init__(
        self,
        engine: EngineConfig,
        initial: InitialConditionConfig,
        seed: int,
    ) -> None:
        if engine.backend != "numpy":
            raise ValueError(
                f"Unsupported backend '{engine.backend}'. This reference build supports only 'numpy'."
            )

        self.engine = engine
        self.initial = initial
        self.rng = np.random.default_rng(seed)
        self.grid_shape = engine.grid_shape
        self.box_size = engine.box_size
        self.mass = engine.mass
        self.g_int = engine.g_int
        self.time_step = engine.time_step
        self.num_steps = engine.num_steps
        self.log_every = engine.log_every
        self.cell_volume = np.prod(
            [self.box_size / axis_size for axis_size in self.grid_shape],
            dtype=float,
        )

        freqs = [
            2.0 * np.pi * np.fft.fftfreq(axis_size, d=self.box_size / axis_size)
            for axis_size in self.grid_shape
        ]
        self.k2 = (
            freqs[0][:, None, None] ** 2
            + freqs[1][None, :, None] ** 2
            + freqs[2][None, None, :] ** 2
        )
        self.linear_half_phase = np.exp(
            -1j * self.time_step * self.k2 / (4.0 * self.mass)
        )

    def _coordinate_mesh(self) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        axes = [
            np.linspace(
                -self.box_size / 2.0,
                self.box_size / 2.0,
                axis_size,
                endpoint=False,
            )
            for axis_size in self.grid_shape
        ]
        return np.meshgrid(*axes, indexing="ij")

    def initialize_wavefunction(self) -> np.ndarray:
        if self.initial.kind == "uniform":
            density = np.full(
                self.grid_shape,
                fill_value=self.initial.amplitude,
                dtype=np.float64,
            )
        elif self.initial.kind == "gaussian":
            x, y, z = self._coordinate_mesh()
            radius_squared = x**2 + y**2 + z**2
            density = self.initial.amplitude * np.exp(
                -radius_squared / (2.0 * self.initial.width**2)
            )
        else:
            raise ValueError(f"Unsupported initial condition kind: {self.initial.kind}")

        amplitude = np.sqrt(density)
        if self.initial.random_phase:
            phase = self.rng.uniform(0.0, 2.0 * np.pi, size=self.grid_shape)
            return amplitude * np.exp(1j * phase)
        return amplitude.astype(np.complex128)

    def compute_potential(self, density: np.ndarray) -> np.ndarray:
        rho_k = np.fft.fftn(density)
        phi_k = -rho_k / (self.k2 + 1e-12)
        return np.real(np.fft.ifftn(phi_k))

    def compute_norm(self, psi: np.ndarray) -> float:
        return float(np.sum(np.abs(psi) ** 2) * self.cell_volume)

    def compute_energy(self, psi: np.ndarray, phi: np.ndarray) -> float:
        density = np.abs(psi) ** 2
        psi_k = np.fft.fftn(psi)
        kinetic = (
            np.sum(self.k2 * np.abs(psi_k) ** 2).real
            / (2.0 * self.mass * np.prod(self.grid_shape))
        )
        gravitational = 0.5 * np.sum(density * phi).real * self.cell_volume
        interaction = 0.5 * self.g_int * np.sum(density**2).real * self.cell_volume
        return float(kinetic + gravitational + interaction)

    def record_snapshot(self, step: int, psi: np.ndarray) -> dict:
        density = np.abs(psi) ** 2
        phi = self.compute_potential(density)
        return {
            "step": step,
            "norm": round(self.compute_norm(psi), 12),
            "energy": round(self.compute_energy(psi, phi), 12),
            "max_density": round(float(np.max(density)), 12),
        }

    def step(self, psi: np.ndarray) -> np.ndarray:
        psi_k = np.fft.fftn(psi)
        psi = np.fft.ifftn(psi_k * self.linear_half_phase)

        density = np.abs(psi) ** 2
        phi = self.compute_potential(density)
        nonlinear_phase = np.exp(
            -1j * self.time_step * (self.mass * phi + self.g_int * density)
        )
        psi = nonlinear_phase * psi

        psi_k = np.fft.fftn(psi)
        return np.fft.ifftn(psi_k * self.linear_half_phase)

    def run(self) -> SimulationResult:
        psi = self.initialize_wavefunction()
        history: list[dict] = [self.record_snapshot(step=0, psi=psi)]

        for step in range(1, self.num_steps + 1):
            psi = self.step(psi)
            if step % self.log_every == 0 or step == self.num_steps:
                history.append(self.record_snapshot(step=step, psi=psi))

        density = np.abs(psi) ** 2
        return SimulationResult(psi=psi, density=density, history=history)
