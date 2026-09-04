from __future__ import annotations

import numpy as np
from scipy.sparse.linalg import LinearOperator

from pdescale.grid import Grid2D
from pdescale.operators import face_coefficient, vector_to_interior
from pdescale.problems import k_field


def matrix_free_apply(
    v: np.ndarray,
    grid: Grid2D,
    case: str,
    *,
    face_average: str = "arithmetic",
) -> np.ndarray:
    u = vector_to_interior(v, grid)
    k = k_field(grid.x, grid.y, case)
    out = np.zeros((grid.nx - 2, grid.ny - 2), dtype=np.result_type(v, float))
    inv_hx2 = 1.0 / grid.hx**2
    inv_hy2 = 1.0 / grid.hy**2

    for i in range(1, grid.nx - 1):
        for j in range(1, grid.ny - 1):
            ke = face_coefficient(k[i, j], k[i + 1, j], face_average)
            kw = face_coefficient(k[i, j], k[i - 1, j], face_average)
            kn = face_coefficient(k[i, j], k[i, j + 1], face_average)
            ks = face_coefficient(k[i, j], k[i, j - 1], face_average)
            out[i - 1, j - 1] = (
                ke * (u[i, j] - u[i + 1, j]) * inv_hx2
                + kw * (u[i, j] - u[i - 1, j]) * inv_hx2
                + kn * (u[i, j] - u[i, j + 1]) * inv_hy2
                + ks * (u[i, j] - u[i, j - 1]) * inv_hy2
            )

    return out.ravel()


def make_linear_operator(grid: Grid2D, case: str, *, face_average: str = "arithmetic") -> LinearOperator:
    shape = (grid.num_interior, grid.num_interior)

    def matvec(v: np.ndarray) -> np.ndarray:
        return matrix_free_apply(v, grid, case, face_average=face_average)

    return LinearOperator(shape=shape, matvec=matvec, dtype=float)
