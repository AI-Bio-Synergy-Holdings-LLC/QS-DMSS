"""Scale-aware nullspace and whole-eigenspace diagnostic conventions."""

import numpy as np


def spectral_tolerance(values: np.ndarray) -> float:
    return float(64 * np.finfo(float).eps * max(len(values), 1)
                 * max(float(np.max(np.abs(values))), np.finfo(float).tiny))


def sanitize_spectrum(values: np.ndarray) -> np.ndarray:
    if not np.all(np.isfinite(values)):
        raise ValueError("Graph eigenvalues must be finite")
    tolerance = spectral_tolerance(values)
    if np.any(values < -tolerance):
        raise ValueError("Graph operator has materially negative eigenvalues")
    return np.where(np.abs(values) <= tolerance, 0.0, values)


def tail_cluster_start(values: np.ndarray, fraction: float) -> tuple[int, float]:
    """Include the whole cluster containing the nominal rank cutoff.

    Adjacent eigenvalues within norm-scaled roundoff tolerance form one cluster.
    Diagnostic power is summed over the complete cluster, never individual columns.
    """
    tolerance = spectral_tolerance(values)
    start = int(np.floor(fraction * len(values)))
    if start == len(values):
        return start, tolerance
    while start > 0 and values[start] - values[start - 1] <= tolerance:
        start -= 1
    return start, tolerance
