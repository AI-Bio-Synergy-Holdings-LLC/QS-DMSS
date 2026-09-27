from __future__ import annotations

import json
from typing import Any

import numpy as np

from qs_dmss.core.fractal_graph import FractalGraph, build_sierpinski_gasket
from qs_dmss.core.fractal_validation import build_multilevel_spectral_report
from qs_dmss.core.graph_policy import (
    finite_number,
    graph_resource_estimate,
    positive_finite,
    validate_graph_execution,
    validate_graph_scale,
)
from qs_dmss.core.graph_spectrum import sanitize_spectrum, tail_cluster_start
from qs_dmss.core.solver import SimulationResult
from qs_dmss.io.config import EngineConfig, FractalGraphConfig, InitialConditionConfig


class FractalGraphSpectralSolver:
    """Strang-split nonlinear wave evolution on an intrinsic fractal graph.

    The linear generator is obtained from the generalized eigenproblem

        K_m phi_j = lambda_j M_m phi_j,

    where K_m is the renormalized graph-energy matrix and M_m is the finite-cell
    measure.  A full spectral basis makes the finite-graph linear substep exact
    up to eigendecomposition and floating-point roundoff.  It does not, by
    itself, prove convergence to the continuum fractal PDE; that requires a
    multilevel convergence study.
    """

    def __init__(
        self,
        engine: EngineConfig,
        initial: InitialConditionConfig,
        seed: int,
        fractal_graph: FractalGraphConfig,
    ) -> None:
        if engine.backend != "fractal_graph_spectral":
            raise ValueError(
                "FractalGraphSpectralSolver requires engine.backend='fractal_graph_spectral'."
            )
        self.engine = engine
        self.initial = initial
        self.config = fractal_graph
        # Direct construction must obey the same admission rules as config parsing.
        fractal_graph.__post_init__()
        validate_graph_execution(fractal_graph.level, fractal_graph.boundary_condition,
                                 engine.num_steps)
        for name in ("box_size", "mass", "time_step"):
            positive_finite(getattr(engine, name), name)
        validate_graph_scale(engine.box_size)
        if type(engine.log_every) is not int or engine.log_every < 1:
            raise ValueError("log_every must be a positive integer")
        finite_number(engine.g_int, "g_int")
        positive_finite(initial.amplitude, "initial.amplitude")
        positive_finite(initial.width, "initial.width")
        if (any(type(v) is not int for v in engine.grid_shape)
                or engine.grid_shape != fractal_graph.grid_shape):
            raise ValueError(
                "Derived engine.grid_shape does not match the active fractal vertex count."
            )
        self.graph = self._build_graph()

        self.xp = self._load_array_module(fractal_graph.device)
        self.rng = self.xp.random.default_rng(seed)
        self.mass_weights = self.xp.asarray(self.graph.mass_weights, dtype=self.xp.float64)
        self.sqrt_mass = self.xp.sqrt(self.mass_weights)
        self.stiffness = self.xp.asarray(self.graph.stiffness, dtype=self.xp.float64)
        self.coordinates = self.xp.asarray(self.graph.coordinates, dtype=self.xp.float64)
        self.potential, self.gamma = self._build_node_fields()
        if not np.all(np.isfinite(self.gamma)):
            raise ValueError("Graph node coupling must remain finite; reduce g_int/quadrant_gamma")
        self.eigenvalues, self.eigenvectors = self._build_spectral_basis()
        self.tail_start, self.cluster_tolerance = tail_cluster_start(
            self.eigenvalues, self.config.tail_fraction
        )

    def _build_graph(self) -> FractalGraph:
        if self.config.family != "sierpinski_gasket":
            raise ValueError(f"Unsupported fractal graph family: {self.config.family}")
        return build_sierpinski_gasket(
            self.config.level,
            boundary_condition=self.config.boundary_condition,
            physical_scale=self.engine.box_size,
        )

    @staticmethod
    def _load_array_module(device: str):
        if device == "cpu":
            return np
        raise ValueError("fractal_graph.device must be cpu")

    def _to_numpy(self, value):
        return np.asarray(value)

    def _build_spectral_basis(self):
        # Symmetric standard form of K phi = lambda M phi:
        # H = M^{-1/2} K M^{-1/2}, U = M^{1/2} phi.
        hamiltonian = self.stiffness / (
            self.sqrt_mass[:, None] * self.sqrt_mass[None, :]
        )
        eigenvalues, eigenvectors = self.xp.linalg.eigh(hamiltonian)
        eigenvalues = sanitize_spectrum(eigenvalues)
        return eigenvalues, eigenvectors

    def _build_node_fields(self):
        coordinates = self.coordinates
        centroid = self.xp.asarray(
            [self.engine.box_size / 2.0, self.engine.box_size * np.sqrt(3.0) / 6.0],
            dtype=self.xp.float64,
        )
        shifted = coordinates - centroid
        x = shifted[:, 0]
        y = shifted[:, 1]
        quadrants = (
            ((x >= 0.0) & (y >= 0.0)),
            ((x < 0.0) & (y >= 0.0)),
            ((x < 0.0) & (y < 0.0)),
            ((x >= 0.0) & (y < 0.0)),
        )
        gamma = self.xp.zeros(self.graph.vertex_count, dtype=self.xp.float64)
        potential = self.xp.zeros(self.graph.vertex_count, dtype=self.xp.float64)
        for index, selector in enumerate(quadrants):
            gamma = self.xp.where(
                selector,
                self.engine.g_int * self.config.quadrant_gamma[index],
                gamma,
            )
            potential = self.xp.where(
                selector,
                self.config.quadrant_potential[index],
                potential,
            )
        return potential, gamma

    def initialize_wavefunction(self):
        if self.initial.kind == "uniform":
            density = self.xp.full(
                self.graph.vertex_count,
                self.initial.amplitude,
                dtype=self.xp.float64,
            )
        elif self.initial.kind == "gaussian":
            center = self.xp.asarray(
                [self.engine.box_size / 2.0, self.engine.box_size * np.sqrt(3.0) / 6.0],
                dtype=self.xp.float64,
            )
            # Dimensionless distances avoid width**2 under/overflow. Infinite
            # distances correctly decay to zero; an entirely zero state is rejected.
            with np.errstate(over="ignore", divide="ignore"):
                radius_squared = self.xp.sum(
                    ((self.coordinates - center) / self.initial.width) ** 2, axis=1
                )
                density = self.initial.amplitude * self.xp.exp(-0.5 * radius_squared)
        else:
            raise ValueError(f"Unsupported initial condition kind: {self.initial.kind}")

        psi = self.xp.sqrt(density).astype(self.xp.complex128)
        if self.initial.random_phase:
            phase = self.rng.uniform(0.0, 2.0 * self.xp.pi, size=self.graph.vertex_count)
            psi *= self.xp.exp(1j * phase)
        return psi

    def compute_norm(self, psi) -> float:
        value = self.xp.sum(self.mass_weights * self.xp.abs(psi) ** 2).real
        return float(self._to_numpy(value))

    def compute_energy(self, psi) -> float:
        density = self.xp.abs(psi) ** 2
        kinetic = (
            self.xp.vdot(psi, self.stiffness @ psi).real
            / (2.0 * self.engine.mass)
        )
        potential = self.xp.sum(self.mass_weights * self.potential * density).real
        interaction = 0.5 * self.xp.sum(
            self.mass_weights * self.gamma * density**2
        ).real
        return float(self._to_numpy(kinetic + potential + interaction))

    def spectral_coefficients(self, psi):
        weighted_state = self.sqrt_mass * psi
        return self.eigenvectors.conj().T @ weighted_state

    def compute_spectral_tail_fraction(self, psi) -> float:
        coefficients = self.spectral_coefficients(psi)
        power = self.xp.abs(coefficients) ** 2
        total = self.xp.sum(power) + 1e-300
        tail = self.xp.sum(power[self.tail_start:]) / total
        return float(self._to_numpy(tail.real))

    def _apply_linear(self, psi, dt: float):
        coefficients = self.spectral_coefficients(psi)
        phase = self.xp.exp(
            -1j * dt * self.eigenvalues / (2.0 * self.engine.mass)
        )
        evolved_weighted = self.eigenvectors @ (phase * coefficients)
        return evolved_weighted / self.sqrt_mass

    def _apply_nonlinear(self, psi, dt: float):
        density = self.xp.abs(psi) ** 2
        return psi * self.xp.exp(-1j * dt * (self.potential + self.gamma * density))

    def _step_with_dt(self, psi, dt: float):
        psi = self._apply_nonlinear(psi, 0.5 * dt)
        psi = self._apply_linear(psi, dt)
        return self._apply_nonlinear(psi, 0.5 * dt)

    def step(self, psi):
        return self._step_with_dt(psi, self.engine.time_step)

    def record_snapshot(self, step: int, psi) -> dict[str, float | int]:
        density = self.xp.abs(psi) ** 2
        return {
            "step": step,
            "norm": round(self.compute_norm(psi), 12),
            "energy": round(self.compute_energy(psi), 12),
            "max_density": round(float(self._to_numpy(self.xp.max(density))), 12),
        }

    def _basis_diagnostics(self) -> tuple[float, float]:
        identity = self.xp.eye(self.graph.vertex_count, dtype=self.xp.float64)
        orthogonality = self.xp.linalg.norm(
            self.eigenvectors.T @ self.eigenvectors - identity
        ) / max(self.graph.vertex_count, 1)
        hamiltonian = self.stiffness / (
            self.sqrt_mass[:, None] * self.sqrt_mass[None, :]
        )
        residual = self.xp.linalg.norm(
            hamiltonian @ self.eigenvectors
            - self.eigenvectors * self.eigenvalues[None, :]
        ) / (self.xp.linalg.norm(hamiltonian) + 1e-300)
        return float(self._to_numpy(orthogonality)), float(self._to_numpy(residual))

    def _time_reversal_error(self, initial_state) -> float:
        forward = self._step_with_dt(initial_state, self.engine.time_step)
        backward = self._step_with_dt(forward, -self.engine.time_step)
        difference = backward - initial_state
        numerator = self.xp.sum(self.mass_weights * self.xp.abs(difference) ** 2).real
        denominator = self.xp.sum(
            self.mass_weights * self.xp.abs(initial_state) ** 2
        ).real + 1e-300
        return float(self._to_numpy(self.xp.sqrt(numerator / denominator)))

    def _array_artifacts(self) -> dict[str, np.ndarray]:
        mode_count = min(self.config.artifact_eigenmodes, self.graph.vertex_count)
        generalized_modes = (
            self.eigenvectors[:, :mode_count] / self.sqrt_mass[:, None]
        )
        return {
            "fractal_coordinates": self.graph.coordinates,
            "fractal_stiffness": self.graph.stiffness,
            "fractal_lattice_coordinates": self.graph.lattice_coordinates,
            "fractal_edges": self.graph.edges,
            "fractal_full_coordinates": self.graph.full_coordinates,
            "fractal_full_lattice_coordinates": self.graph.full_lattice_coordinates,
            "fractal_full_edges": self.graph.full_edges,
            "fractal_active_vertex_ids": self.graph.active_vertex_ids,
            "fractal_boundary_vertex_ids": self.graph.boundary_vertex_ids,
            "fractal_mass_weights": self.graph.mass_weights,
            "fractal_eigenvalues": self._to_numpy(self.eigenvalues),
            "fractal_eigenmodes": self._to_numpy(generalized_modes),
            "fractal_potential": self._to_numpy(self.potential),
            "fractal_gamma": self._to_numpy(self.gamma),
        }

    def run(self) -> SimulationResult:
        # Finite inputs alone do not guarantee representable phases, energies or
        # ratios. Fail before evidence persistence rather than emit NaN/Infinity.
        try:
            with np.errstate(over="raise", divide="raise", invalid="raise"):
                result = self._run()
                json.dumps(result.diagnostics, allow_nan=False)
                json.dumps(result.history, allow_nan=False)
                if not np.all(np.isfinite(result.psi)) or not np.all(np.isfinite(result.density)):
                    raise ValueError("Graph final state must be finite")
                return result
        except (FloatingPointError, OverflowError) as exc:
            raise ValueError(
                "Graph run is not representable with finite float64 diagnostics; "
                "reduce amplitude, coupling or timestep, or rescale the model."
            ) from exc

    def _run(self) -> SimulationResult:
        psi = self.initialize_wavefunction()
        initial_copy = psi.copy()
        initial_norm = self.compute_norm(psi)
        if not np.isfinite(initial_norm) or initial_norm <= 0:
            raise ValueError("Graph initial state has zero or non-finite mass-weighted norm")
        initial_energy = self.compute_energy(psi)
        history: list[dict] = [self.record_snapshot(step=0, psi=psi)]

        for step in range(1, self.engine.num_steps + 1):
            psi = self.step(psi)
            if step % self.engine.log_every == 0 or step == self.engine.num_steps:
                history.append(self.record_snapshot(step=step, psi=psi))

        final_norm = self.compute_norm(psi)
        final_energy = self.compute_energy(psi)
        orthogonality_error, eigen_residual = self._basis_diagnostics()
        eigenvalues_np = self._to_numpy(self.eigenvalues)
        multilevel_report = None
        if self.config.validation_levels:
            multilevel_report = build_multilevel_spectral_report(
                self.config.validation_levels,
                boundary_condition=self.graph.boundary_condition,
                physical_scale=self.engine.box_size,
                eigenvalue_count=self.config.validation_eigenvalues,
            )

        diagnostics: dict[str, Any] = {
            "solver_family": "intrinsic_fractal_graph_spectral",
            "domain": {"kind": "finite_graph", "state_shape": [self.graph.vertex_count],
                       "grid_shape_role": "compatibility_count_not_rectangular_geometry"},
            "resource_policy": graph_resource_estimate(self.graph.level, self.graph.boundary_condition),
            "operator_family": "renormalized_sierpinski_dirichlet_form",
            "fractal_family": self.graph.family,
            "graph_level": self.graph.level,
            "boundary_condition": self.graph.boundary_condition,
            "device": self.config.device,
            "exported_eigenmode_count": min(self.config.artifact_eigenmodes, self.graph.vertex_count),
            "eigenmode_export_policy": "leading_columns_may_split_clusters_not_canonical_observables",
            "vertex_count": self.graph.vertex_count,
            "full_vertex_count": self.graph.full_vertex_count,
            "edge_count": int(self.graph.full_edges.shape[0]),
            "energy_renormalization": self.graph.energy_renormalization,
            "pointwise_laplacian_scale": self.graph.pointwise_laplacian_scale,
            "mass_weight_sum": float(np.sum(self.graph.mass_weights)),
            "lowest_eigenvalues": [
                float(value) for value in eigenvalues_np[: min(12, len(eigenvalues_np))]
            ],
            "eigenbasis_orthogonality_error": orthogonality_error,
            "eigenpair_relative_residual": eigen_residual,
            "relative_norm_error": (final_norm - initial_norm) / max(initial_norm, 1e-300),
            "relative_energy_error": (final_energy - initial_energy)
            / max(abs(initial_energy), 1e-300),
            "time_reversal_error": self._time_reversal_error(initial_copy),
            "spectral_tail_fraction": self.compute_spectral_tail_fraction(psi),
            "spectral_tail_convention": "whole_eigenvalue_cluster_v1",
            "spectral_tail_start": self.tail_start,
            "spectral_tail_cutoff_eigenvalue": (
                float(self.eigenvalues[self.tail_start])
                if self.tail_start < self.graph.vertex_count else None
            ),
            "eigenvalue_cluster_tolerance": self.cluster_tolerance,
            "quadrant_gamma": list(self.config.quadrant_gamma),
            "quadrant_potential": list(self.config.quadrant_potential),
            "finite_graph_linear_step": "full_basis_exact_up_to_roundoff",
            "continuum_limit_status": "requires_multilevel_convergence_study",
            "time_integrator": "strang_splitting",
            "time_integrator_order": 2,
            "time_step": self.engine.time_step,
            "multilevel_spectral_validation": multilevel_report,
            "claim_boundary": (
                "This run solves the declared finite Sierpiński graph approximation "
                "using the renormalized Dirichlet-form operator and second-order Strang "
                "time integration (not exact full nonlinear evolution). Embedded-coordinate "
                "quadrant fields and length^-2 scaling are declared modeling conventions. "
                "A single graph level "
                "does not establish convergence to the continuum fractal PDE or physical validation."
            ),
        }
        return SimulationResult(
            psi=self._to_numpy(psi),
            density=self._to_numpy(self.xp.abs(psi) ** 2),
            history=history,
            diagnostics=diagnostics,
            array_artifacts=self._array_artifacts(),
        )
