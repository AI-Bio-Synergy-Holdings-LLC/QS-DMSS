"""Independent finite-model assembly. Deliberately imports no QS-DMSS code."""

from fractions import Fraction
from itertools import combinations, product

import numpy as np
from scipy.integrate import solve_ivp
from scipy.linalg import eigh, expm


def graph(level, boundary, length):
    """Address words translate unit triangles; B.T B supplies edge energy.

    Unlike production's repeated midpoint subdivision and edge-loop Laplacian,
    each address gives one final cell directly. Rational arithmetic determines
    masses and the stiffness prefactor before conversion to float64.
    """
    if level not in (0, 1, 2) or boundary not in ("dirichlet", "neumann"):
        raise ValueError("Reference is bounded to levels 0..2 and declared boundaries")
    if level == 0 and boundary == "dirichlet":
        raise ValueError("No active Dirichlet vertices at level zero")
    if length not in (0.75, 1.0, 2.5):
        raise ValueError("Reference uses only preregistered lengths")
    corners = ((0, 0), (1, 0), (0, 1))
    cells = []
    for address in product(corners, repeat=level):
        offset = tuple(sum(2**k * digit[j] for k, digit in enumerate(address))
                       for j in (0, 1))
        cells.append(tuple((offset[0] + x, offset[1] + y) for x, y in corners))
    vertices = sorted(set(vertex for cell in cells for vertex in cell))
    indices = {vertex: i for i, vertex in enumerate(vertices)}
    edge_set = {tuple(sorted((indices[a], indices[b])))
                for cell in cells for a, b in combinations(cell, 2)}
    edges = np.array(sorted(edge_set), dtype=int)
    incidence = np.zeros((len(edges), len(vertices)))
    for row, (a, b) in enumerate(edges):
        incidence[row, a], incidence[row, b] = -1, 1
    rational_mass = [sum((Fraction(1, 3**(level + 1)) for cell in cells if v in cell),
                         Fraction(0)) for v in vertices]
    factor = Fraction(5, 3)**level / Fraction(str(length))**2
    full_k = float(factor) * (incidence.T @ incidence)
    full_m = np.array([float(value) for value in rational_mass])
    boundary_ids = np.array([indices[(0, 0)], indices[(2**level, 0)],
                             indices[(0, 2**level)]])
    active = np.array([i for i in range(len(vertices))
                       if boundary == "neumann" or i not in boundary_ids])
    lattice = np.array(vertices)
    return {"vertices": lattice, "edges": edges, "active": active,
            "boundary": boundary_ids, "mass": full_m[active],
            "stiffness": full_k[np.ix_(active, active)],
            "full_mass": full_m, "full_stiffness": full_k,
            "level": level, "length": length}


def fields(reference, potential, gamma, coupling):
    """Use exact lattice inequalities, avoiding production's embedded floats."""
    lattice = reference["vertices"][reference["active"]]
    scale = 2**reference["level"]
    right = 2*lattice[:, 0] + lattice[:, 1] >= scale
    upper = 3*lattice[:, 1] >= scale
    quadrant = np.where(upper, np.where(right, 0, 1), np.where(right, 3, 2))
    return np.asarray(potential)[quadrant], coupling * np.asarray(gamma)[quadrant]


def initial_state(reference):
    lattice = reference["vertices"][reference["active"]] / 2**reference["level"]
    psi = (1 + 0.2*lattice[:, 0] + 0.1*lattice[:, 1]) * np.exp(
        1j * (0.4*lattice[:, 0] - 0.3*lattice[:, 1]))
    return psi / np.sqrt(np.sum(reference["mass"] * np.abs(psi)**2))


def spectrum(reference):
    values, modes = eigh(reference["stiffness"], np.diag(reference["mass"]), driver="gv")
    return values, np.sqrt(reference["mass"])[:, None] * modes


def clusters(values, gap):
    splits = np.flatnonzero(np.diff(values) > gap * max(1, np.max(np.abs(values)))) + 1
    return np.split(np.arange(len(values)), splits)


def projector(modes):
    return modes @ modes.conj().T


def linear_state(reference, initial, mass, time):
    generator = reference["stiffness"] / reference["mass"][:, None] / (2*mass)
    return expm(-1j * time * generator) @ initial


def trajectory(reference, initial, potential, gamma, mass, times, rtol, atol):
    generator = reference["stiffness"] / reference["mass"][:, None] / (2*mass)

    def derivative(time, state):
        return -1j * (generator @ state + (potential + gamma*np.abs(state)**2)*state)

    result = solve_ivp(derivative, (0, times[-1]), initial, method="DOP853",
                       t_eval=times, rtol=rtol, atol=atol)
    if not result.success or result.y.shape != (len(initial), len(times)):
        raise RuntimeError("Reference integration did not reach every requested time")
    if not np.all(np.isfinite(result.y)):
        raise RuntimeError("Reference integration produced non-finite states")
    return result.y.T
