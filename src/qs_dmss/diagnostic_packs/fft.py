"""One built-in CPU diagnostic. No evolution, graph, provider or AI calls."""

from __future__ import annotations

import math
import platform
import sys
from pathlib import Path

import numpy as np

from qs_dmss import __version__
from qs_dmss.core.fractal_ssfm import FractalQuadrantSSFMSolver
from qs_dmss.diagnostic_packs.admission import AdmittedPack, analytic_energy, sha256
from qs_dmss.io.config import (
    EngineConfig,
    FractalGeometryConfig,
    InitialConditionConfig,
)


def _measure(case):
    nx, ny = case.grid_shape
    solver = FractalQuadrantSSFMSolver(
        EngineConfig(
            "numpy_fractal_ssfm", (nx, ny, 1), case.box_size, case.mass, 0.0, 0.001, 1
        ),
        InitialConditionConfig("uniform", random_phase=False),
        0,
        geometry=FractalGeometryConfig(fractal="radial_shells", potential_strength=0.0),
    )
    phase = (
        case.modes[0] * np.arange(nx)[:, None] / nx
        + case.modes[1] * np.arange(ny)[None, :] / ny
    )
    psi = np.exp(2j * np.pi * phase) / case.box_size
    return solver.compute_energy(psi), solver.compute_norm(psi)


def evaluate_pack(pack: AdmittedPack) -> dict:
    rows = []
    for case in pack.cases.cases:
        energy, norm = _measure(case)
        reference = analytic_energy(case)
        finite = math.isfinite(energy) and math.isfinite(norm)
        error = abs(energy - reference) if finite else None
        tolerance = case.absolute_tolerance + case.relative_tolerance * abs(reference)
        passed = finite and error <= tolerance and abs(norm - 1.0) <= 1e-12
        rows.append(
            {
                "case": case.model_dump(mode="json"),
                "analytic_energy": reference,
                "measured_energy": energy if math.isfinite(energy) else None,
                "measured_norm": norm if math.isfinite(norm) else None,
                "absolute_energy_error": error,
                "allowed_energy_error": tolerance,
                "norm_absolute_tolerance": 1e-12,
                "passed": bool(passed),
            }
        )
    root = Path(__file__).resolve().parents[1]
    modules = (
        "diagnostic_packs/models.py",
        "diagnostic_packs/admission.py",
        "diagnostic_packs/fft.py",
        "diagnostic_packs/evidence.py",
        "core/fractal_ssfm.py",
        "io/config.py",
    )
    passed = all(row["passed"] for row in rows)
    return {
        "schema_version": pack.manifest.evidence_schema_version,
        "pack": pack.summary(),
        "diagnostic_convention": "fft_cell_measure_v2",
        "formula": "E=(2*pi/L)^2*(mode_x^2+mode_y^2)/(2*mass); norm=1; hbar=1",
        "case_results": rows,
        "all_cases_pass": passed,
        "numerical_outcome": "NOT_FALSIFIED_WITHIN_SCOPE"
        if passed
        else "FALSIFIED_WITHIN_SCOPE",
        "scientific_validation_status": "NOT_ESTABLISHED",
        "human_disposition": "PENDING",
        "ai_advice": None,
        "environment": {
            "core_version": __version__,
            "python": sys.version,
            "platform": platform.platform(),
            "numpy": np.__version__,
        },
        "implementation_sha256": {
            name: sha256((root / name).read_bytes()) for name in modules
        },
        "execution_policy": {
            "cpu_only": True,
            "solver_evolution_called": False,
            "pack_code_executed": False,
            "network_called": False,
            "ai_called": False,
            "graph_called": False,
        },
        "limitations": [
            "Checks kinetic energy on a square periodic 2-D domain with zero potential and interaction.",
            "Discrete resolved modes only; not temporal refinement, continuum convergence or physical calibration.",
            "References and core checks are maintainer-owned, not independent human scientific review.",
            "Hashes identify bytes, not authorship; preserve this bundle and candidate wheel separately.",
        ],
    }
