"""Analytic quadrature/Parseval checks, independent of trajectory snapshots."""

import numpy as np
import pytest

from qs_dmss.core.fractal_ssfm import FractalFields, FractalQuadrantSSFMSolver
from qs_dmss.core.solver import QuantumScalarDarkMatterSolver
from qs_dmss.io.config import EngineConfig, InitialConditionConfig


def test_benchmark_rejects_unspecified_energy_convention():
    from qs_dmss.benchmarks import _validate_metric_envelopes

    expected = {"energy_diagnostic_convention": "fft_cell_measure_v2", "metric_envelopes": {}}
    assert not _validate_metric_envelopes({}, expected)[0]["success"]
    assert _validate_metric_envelopes(
        {"energy_diagnostic_convention": "fft_cell_measure_v2"}, expected
    )[0]["success"]


@pytest.mark.parametrize("shape", [(8, 8, 8), (16, 16, 16), (8, 12, 10)])
@pytest.mark.parametrize("length,mass", [(1.0, 1.0), (2.5, 1.7)])
def test_reference_plane_wave_energy(shape, length, mass):
    solver = QuantumScalarDarkMatterSolver(
        EngineConfig("numpy", shape, length, mass, 0.0, 0.001, 1),
        InitialConditionConfig("uniform"), 1,
    )
    x = np.arange(shape[0]) * length / shape[0]
    psi = np.broadcast_to(
        np.exp(2j * np.pi * x[:, None, None] / length) / length**1.5, shape
    )
    assert solver.compute_norm(psi) == pytest.approx(1.0)
    expected = (2 * np.pi / length)**2 / (2 * mass)
    assert solver.compute_energy(psi, np.zeros(shape)) == pytest.approx(expected)
    # A zero-frequency field isolates the unchanged potential/interaction terms.
    solver.g_int = 0.3
    constant = np.full(shape, 2.0, dtype=complex)
    assert solver.compute_energy(constant, np.full(shape, 0.7)) == pytest.approx(
        length**3 * (0.5 * 4 * 0.7 + 0.5 * 0.3 * 16)
    )


@pytest.mark.parametrize("shape", [(8, 8, 1), (16, 16, 1), (8, 12, 1)])
@pytest.mark.parametrize("length,mass", [(1.0, 1.0), (2.5, 1.7)])
def test_fractal_plane_wave_energy(shape, length, mass):
    solver = FractalQuadrantSSFMSolver(
        EngineConfig("numpy_fractal_ssfm", shape, length, mass, 0.0, 0.001, 1),
        InitialConditionConfig("uniform"), 1,
    )
    x = np.arange(shape[0]) * length / shape[0]
    psi = np.broadcast_to(np.exp(2j * np.pi * x[:, None] / length) / length, shape[:2])
    assert solver.compute_norm(psi) == pytest.approx(1.0)
    assert solver.compute_energy(psi) == pytest.approx((2 * np.pi / length)**2 / (2 * mass))
    fields = solver.fields
    solver.fields = FractalFields(fields.x, fields.y, fields.mask,
                                 np.full(shape[:2], 0.7), np.full(shape[:2], 0.3))
    assert solver.compute_energy(np.full(shape[:2], 2.0, dtype=complex)) == pytest.approx(
        length**2 * (4 * 0.7 + 0.5 * 0.3 * 16)
    )
