from __future__ import annotations

import numpy as np
from scipy.sparse import coo_matrix, csr_matrix

from pdescale.grid import Grid2D
from pdescale.problems import k_field

FACE_AVERAGING_MODES = ("arithmetic", "harmonic")


def interior_to_vector(u: np.ndarray) -> np.ndarray:
    if u.ndim != 2 or u.shape[0] < 3 or u.shape[1] < 3:
        raise ValueError("u must be a 2D array including boundary nodes")
    return np.asarray(u[1:-1, 1:-1]).ravel()


def vector_to_interior(v: np.ndarray, grid: Grid2D) -> np.ndarray:
    v = np.asarray(v)
    if v.size != grid.num_interior:
        raise ValueError(f"expected vector of length {grid.num_interior}, got {v.size}")
    u = np.zeros((grid.nx, grid.ny), dtype=v.dtype)
    u[1:-1, 1:-1] = v.reshape((grid.nx - 2, grid.ny - 2))
    return u


def face_coefficient(left: float, right: float, mode: str = "arithmetic") -> float:
    if mode == "arithmetic":
        return 0.5 * (left + right)
    if mode == "harmonic":
        denominator = left + right
        if denominator <= 0.0:
            raise ValueError("harmonic face averaging requires positive coefficients")
        return 2.0 * left * right / denominator
    raise ValueError(f"unknown face averaging mode: {mode}")


def assemble_operator(grid: Grid2D, case: str, *, face_average: str = "arithmetic") -> csr_matrix:
    if face_average not in FACE_AVERAGING_MODES:
        raise ValueError(f"face_average must be one of {FACE_AVERAGING_MODES}")
    k = k_field(grid.x, grid.y, case)
    inv_hx2 = 1.0 / grid.hx**2
    inv_hy2 = 1.0 / grid.hy**2
    rows: list[int] = []
    cols: list[int] = []
    data: list[float] = []

    for i in range(1, grid.nx - 1):
        for j in range(1, grid.ny - 1):
            row = grid.interior_index(i, j)
            ke = face_coefficient(k[i, j], k[i + 1, j], face_average)
            kw = face_coefficient(k[i, j], k[i - 1, j], face_average)
            kn = face_coefficient(k[i, j], k[i, j + 1], face_average)
            ks = face_coefficient(k[i, j], k[i, j - 1], face_average)

            diag = (ke + kw) * inv_hx2 + (kn + ks) * inv_hy2
            rows.append(row)
            cols.append(row)
            data.append(diag)

            if i + 1 <= grid.nx - 2:
                rows.append(row)
                cols.append(grid.interior_index(i + 1, j))
                data.append(-ke * inv_hx2)
            if i - 1 >= 1:
                rows.append(row)
                cols.append(grid.interior_index(i - 1, j))
                data.append(-kw * inv_hx2)
            if j + 1 <= grid.ny - 2:
                rows.append(row)
                cols.append(grid.interior_index(i, j + 1))
                data.append(-kn * inv_hy2)
            if j - 1 >= 1:
                rows.append(row)
                cols.append(grid.interior_index(i, j - 1))
                data.append(-ks * inv_hy2)

    return coo_matrix(
        (data, (rows, cols)),
        shape=(grid.num_interior, grid.num_interior),
    ).tocsr()
