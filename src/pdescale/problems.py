from __future__ import annotations

import numpy as np

from pdescale.coefficients import coefficient_field
from pdescale.grid import Grid2D


def u_exact(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    return np.sin(np.pi * x) * np.sin(np.pi * y)


def k_field(x: np.ndarray, y: np.ndarray, case: str) -> np.ndarray:
    return coefficient_field(x, y, case)


def forcing_full(grid: Grid2D, case: str) -> np.ndarray:
    x = grid.x
    y = grid.y
    u = u_exact(x, y)
    k = k_field(x, y, case)

    if case in {"constant", "smooth_constant"}:
        return 2.0 * np.pi**2 * u

    if case in {"smooth", "smooth_variable"}:
        ux = np.pi * np.cos(np.pi * x) * np.sin(np.pi * y)
        uy = np.pi * np.sin(np.pi * x) * np.cos(np.pi * y)
        kx = np.pi * np.cos(2.0 * np.pi * x) * np.sin(2.0 * np.pi * y)
        ky = np.pi * np.sin(2.0 * np.pi * x) * np.cos(2.0 * np.pi * y)
        return 2.0 * np.pi**2 * k * u - kx * ux - ky * uy

    if case == "high_contrast":
        raise NotImplementedError(
            "high_contrast is a solver-benchmark coefficient case, not a "
            "manufactured-solution forcing case"
        )

    raise ValueError(f"unknown forcing case: {case}")


def rhs_manufactured(grid: Grid2D, case: str) -> np.ndarray:
    return forcing_full(grid, case)[1:-1, 1:-1].ravel()
