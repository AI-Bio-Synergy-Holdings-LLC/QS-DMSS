"""Non-configurable admission limits for the experimental dense CPU backend."""

import math

MAX_GRAPH_LEVEL = 5
MAX_DENSE_BYTES = 64 * 1024 * 1024
MAX_STEP_WORK = 100_000_000


def graph_resource_estimate(level: int, boundary_condition: str) -> dict[str, int]:
    # Check the level before exponentiation, recursion, or any allocation.
    if type(level) is not int or not 0 <= level <= MAX_GRAPH_LEVEL:
        raise ValueError(f"Graph level must be an integer from 0 to {MAX_GRAPH_LEVEL}")
    if not isinstance(boundary_condition, str) or boundary_condition not in {"dirichlet", "neumann"}:
        raise ValueError("Graph boundary_condition must be dirichlet or neumann")
    if boundary_condition == "dirichlet" and level == 0:
        raise ValueError("Dirichlet graph requires level >= 1")
    full = (3 ** (level + 1) + 3) // 2
    active = full - 3 if boundary_condition == "dirichlet" else full
    # Conservative admission estimate for real/complex matrices and LAPACK scratch,
    # not an OS-level peak-memory guarantee. Level cap also bounds cubic solve work.
    estimate = 16 * full * full * 8 + 1024 * full
    if estimate > MAX_DENSE_BYTES:
        raise ValueError("Graph exceeds the dense-memory admission budget")
    return {"full_vertices": full, "active_vertices": active,
            "estimated_peak_bytes": estimate, "memory_budget_bytes": MAX_DENSE_BYTES}


def validate_graph_execution(level: int, boundary_condition: str, num_steps: int) -> None:
    resource = graph_resource_estimate(level, boundary_condition)
    if type(num_steps) is not int or not 1 <= num_steps <= 10_000:
        raise ValueError("Graph num_steps must be an integer from 1 to 10000")
    if 2 * resource["active_vertices"]**2 * num_steps > MAX_STEP_WORK:
        raise ValueError("Graph run exceeds the dense step-work budget; reduce level or steps")


def finite_number(value: float, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number")


def positive_finite(value: float, name: str) -> None:
    finite_number(value, name)
    if value <= 0:
        raise ValueError(f"{name} must be finite and positive")


def validate_graph_scale(value: float) -> None:
    positive_finite(value, "physical_scale")
    if not 1e-6 <= value <= 1e6:
        raise ValueError("Graph physical_scale/box_size must be in [1e-6, 1e6]")
