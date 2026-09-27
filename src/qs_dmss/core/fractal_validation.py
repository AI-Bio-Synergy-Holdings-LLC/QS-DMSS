from __future__ import annotations

from typing import Any

import numpy as np

from qs_dmss.core.fractal_graph import build_sierpinski_gasket
from qs_dmss.core.graph_policy import graph_resource_estimate
from qs_dmss.core.graph_spectrum import sanitize_spectrum, spectral_tolerance


def _generalized_eigenvalues(stiffness: np.ndarray, mass_weights: np.ndarray) -> np.ndarray:
    sqrt_mass = np.sqrt(mass_weights)
    symmetric_operator = stiffness / (sqrt_mass[:, None] * sqrt_mass[None, :])
    values = np.linalg.eigvalsh(symmetric_operator)
    return sanitize_spectrum(values)


def build_multilevel_spectral_report(
    levels: tuple[int, ...],
    *,
    boundary_condition: str,
    physical_scale: float,
    eigenvalue_count: int = 8,
) -> dict[str, Any]:
    """Build an evidence-oriented low-spectrum comparison across graph levels.

    This report measures stabilization of low eigenvalues across finite graph
    approximations.  It is a convergence diagnostic, not a proof of continuum
    convergence.
    """

    if not isinstance(levels, (tuple, list)) or not 1 <= len(levels) <= 6:
        raise ValueError("Validation requires one to six graph levels")
    if type(eigenvalue_count) is not int or not 1 <= eigenvalue_count <= 366:
        raise ValueError("eigenvalue_count must be an integer from 1 to 366")
    # Preflight every level before constructing even the first matrix.
    for level in levels:
        graph_resource_estimate(level, boundary_condition)
    ordered_levels = tuple(sorted(set(levels)))
    spectra: dict[int, np.ndarray] = {}
    records: list[dict[str, Any]] = []
    for level in ordered_levels:
        graph = build_sierpinski_gasket(
            level,
            boundary_condition=boundary_condition,
            physical_scale=physical_scale,
        )
        eigenvalues = _generalized_eigenvalues(graph.stiffness, graph.mass_weights)
        selected = eigenvalues[: min(eigenvalue_count, len(eigenvalues))]
        # Compare only positive modes. Nullspace roundoff is an absolute residual,
        # never a percentage divided by a nearly zero eigenvalue.
        null = eigenvalues == 0.0
        spectra[level] = selected
        records.append(
            {
                "level": level,
                "vertex_count": graph.vertex_count,
                "full_vertex_count": graph.full_vertex_count,
                "lowest_eigenvalues": [float(value) for value in selected],
                "nullity": int(np.count_nonzero(null)),
                "nullspace_absolute_residual": float(np.linalg.norm(graph.stiffness @ np.ones(graph.vertex_count))) if boundary_condition == "neumann" else None,
                "zero_tolerance": spectral_tolerance(eigenvalues),
            }
        )

    comparisons: list[dict[str, Any]] = []
    for lower, upper in zip(ordered_levels, ordered_levels[1:]):
        left = spectra[lower]
        right = spectra[upper]
        left = left[left > 0]
        right = right[right > 0]
        count = min(len(left), len(right))
        if count == 0:
            continue
        denominator = np.abs(right[:count])
        relative = np.abs(right[:count] - left[:count]) / denominator
        comparisons.append(
            {
                "from_level": lower,
                "to_level": upper,
                "compared_eigenvalues": count,
                "mean_relative_change": float(np.mean(relative)),
                "max_relative_change": float(np.max(relative)),
            }
        )

    return {
        "levels": list(ordered_levels),
        "boundary_condition": boundary_condition,
        "eigenvalue_count": eigenvalue_count,
        "spectra": records,
        "successive_level_changes": comparisons,
        "interpretation": (
            "Ordered positive eigenvalues are compared, excluding nullspace modes; "
            "indices do not assert physical mode correspondence across levels. "
            "Low-spectrum stabilization across levels is numerical evidence only; "
            "it does not replace a mathematical convergence proof."
        ),
    }
