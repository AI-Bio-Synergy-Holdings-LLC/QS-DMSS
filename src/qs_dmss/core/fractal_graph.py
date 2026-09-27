from __future__ import annotations

from dataclasses import dataclass
from math import sqrt

import numpy as np

from qs_dmss.core.graph_policy import graph_resource_estimate, validate_graph_scale


@dataclass(frozen=True)
class FractalGraph:
    """Finite graph approximation of a post-critically finite fractal.

    ``stiffness`` is the renormalized graph-energy matrix K_m and
    ``mass_weights`` is the diagonal of the finite-cell measure M_m.  The
    generalized eigenproblem K_m phi = lambda M_m phi therefore approximates
    the intrinsic fractal Laplacian rather than a Euclidean FFT Laplacian.
    """

    family: str
    level: int
    boundary_condition: str
    coordinates: np.ndarray
    lattice_coordinates: np.ndarray
    edges: np.ndarray
    full_coordinates: np.ndarray
    full_lattice_coordinates: np.ndarray
    full_edges: np.ndarray
    active_vertex_ids: np.ndarray
    boundary_vertex_ids: np.ndarray
    mass_weights: np.ndarray
    stiffness: np.ndarray
    energy_renormalization: float
    pointwise_laplacian_scale: float

    @property
    def vertex_count(self) -> int:
        return int(self.coordinates.shape[0])

    @property
    def full_vertex_count(self) -> int:
        return int(self.full_coordinates.shape[0])


def sierpinski_vertex_count(level: int) -> int:
    graph_resource_estimate(level, "neumann")
    return (3 ** (level + 1) + 3) // 2


def _sierpinski_cells(level: int) -> list[tuple[tuple[int, int], tuple[int, int], tuple[int, int]]]:
    scale = 2**level
    cells = [((0, 0), (scale, 0), (0, scale))]
    for _ in range(level):
        refined: list[tuple[tuple[int, int], tuple[int, int], tuple[int, int]]] = []
        for a, b, c in cells:
            ab = ((a[0] + b[0]) // 2, (a[1] + b[1]) // 2)
            ac = ((a[0] + c[0]) // 2, (a[1] + c[1]) // 2)
            bc = ((b[0] + c[0]) // 2, (b[1] + c[1]) // 2)
            refined.extend(((a, ab, ac), (ab, b, bc), (ac, bc, c)))
        cells = refined
    return cells


def build_sierpinski_gasket(
    level: int,
    *,
    boundary_condition: str = "dirichlet",
    physical_scale: float = 1.0,
) -> FractalGraph:
    """Build the standard Sierpiński-gasket graph approximation.

    The graph energy uses the canonical renormalization ``(5/3)^level``.  Cell
    mass ``3^-level`` is shared equally among each cell's three vertices.  For
    interior vertices this yields the familiar pointwise scaling
    ``(3/2) * 5^level`` for ``-Delta``.  Scaling the embedded gasket by
    ``physical_scale`` divides the operator by ``physical_scale**2``.
    """

    graph_resource_estimate(level, boundary_condition)
    if boundary_condition not in {"dirichlet", "neumann"}:
        raise ValueError("boundary_condition must be 'dirichlet' or 'neumann'")
    validate_graph_scale(physical_scale)

    cells = _sierpinski_cells(level)
    vertex_keys = sorted({vertex for cell in cells for vertex in cell})
    if len(vertex_keys) != sierpinski_vertex_count(level):
        raise RuntimeError("Sierpiński vertex-count invariant failed")

    index = {key: idx for idx, key in enumerate(vertex_keys)}
    full_edges_set: set[tuple[int, int]] = set()
    incidence = np.zeros(len(vertex_keys), dtype=np.float64)
    for cell in cells:
        ids = [index[vertex] for vertex in cell]
        for vertex_id in ids:
            incidence[vertex_id] += 1.0
        for left, right in ((ids[0], ids[1]), (ids[0], ids[2]), (ids[1], ids[2])):
            full_edges_set.add((min(left, right), max(left, right)))

    full_edges = np.asarray(sorted(full_edges_set), dtype=np.int64)
    laplacian = np.zeros((len(vertex_keys), len(vertex_keys)), dtype=np.float64)
    for left, right in full_edges:
        laplacian[left, left] += 1.0
        laplacian[right, right] += 1.0
        laplacian[left, right] -= 1.0
        laplacian[right, left] -= 1.0

    energy_renormalization = (5.0 / 3.0) ** level / (physical_scale**2)
    stiffness_full = energy_renormalization * laplacian
    mass_full = incidence / (3.0 * (3.0**level))

    scale = 2**level
    boundary_keys = ((0, 0), (scale, 0), (0, scale))
    boundary_vertex_ids = np.asarray([index[key] for key in boundary_keys], dtype=np.int64)
    if boundary_condition == "dirichlet":
        active_vertex_ids = np.asarray(
            [idx for idx in range(len(vertex_keys)) if idx not in set(boundary_vertex_ids.tolist())],
            dtype=np.int64,
        )
        if active_vertex_ids.size == 0:
            raise ValueError("Dirichlet Sierpiński graph requires level >= 1")
    else:
        active_vertex_ids = np.arange(len(vertex_keys), dtype=np.int64)

    remap = {full_id: local_id for local_id, full_id in enumerate(active_vertex_ids.tolist())}
    active_edges = np.asarray(
        [
            (remap[int(left)], remap[int(right)])
            for left, right in full_edges
            if int(left) in remap and int(right) in remap
        ],
        dtype=np.int64,
    )
    if active_edges.size == 0:
        active_edges = np.empty((0, 2), dtype=np.int64)

    lattice = np.asarray(vertex_keys, dtype=np.int64)
    denominator = float(scale)
    full_coordinates = np.column_stack(
        (
            (lattice[:, 0] + 0.5 * lattice[:, 1]) / denominator,
            (sqrt(3.0) / 2.0) * lattice[:, 1] / denominator,
        )
    ) * physical_scale

    active = active_vertex_ids
    stiffness = stiffness_full[np.ix_(active, active)]
    mass_weights = mass_full[active]
    if np.any(mass_weights <= 0):
        raise RuntimeError("Fractal mass weights must be strictly positive")

    return FractalGraph(
        family="sierpinski_gasket",
        level=level,
        boundary_condition=boundary_condition,
        coordinates=full_coordinates[active],
        lattice_coordinates=lattice[active],
        edges=active_edges,
        full_coordinates=full_coordinates,
        full_lattice_coordinates=lattice,
        full_edges=full_edges,
        active_vertex_ids=active,
        boundary_vertex_ids=boundary_vertex_ids,
        mass_weights=mass_weights,
        stiffness=stiffness,
        energy_renormalization=energy_renormalization,
        pointwise_laplacian_scale=(1.5 * (5.0**level)) / (physical_scale**2),
    )
