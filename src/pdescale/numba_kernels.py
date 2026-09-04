from __future__ import annotations

import numpy as np
from numba import njit, prange


STENCIL_BYTES_PER_POINT = 11 * np.dtype(float).itemsize


def _validate_stencil_inputs(
    u: np.ndarray,
    k: np.ndarray,
    out: np.ndarray,
    hx: float,
    hy: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    if u.ndim != 2 or k.ndim != 2 or out.ndim != 2:
        raise ValueError("u, k, and out must be 2D arrays")
    if u.shape != k.shape or u.shape != out.shape:
        raise ValueError("u, k, and out must have the same shape")
    if u.shape[0] < 3 or u.shape[1] < 3:
        raise ValueError("stencil arrays must be at least 3 by 3")
    if hx <= 0.0 or hy <= 0.0:
        raise ValueError("grid spacing must be positive")
    return (
        np.ascontiguousarray(u, dtype=np.float64),
        np.ascontiguousarray(k, dtype=np.float64),
        out,
    )


def stencil_bytes_per_apply(shape: tuple[int, int]) -> int:
    if len(shape) != 2:
        raise ValueError("shape must be two-dimensional")
    interior_points = max(int(shape[0]) - 2, 0) * max(int(shape[1]) - 2, 0)
    return int(interior_points * STENCIL_BYTES_PER_POINT)


def numpy_apply_stencil(
    u: np.ndarray,
    k: np.ndarray,
    out: np.ndarray,
    hx: float,
    hy: float,
) -> None:
    u_arr, k_arr, out_arr = _validate_stencil_inputs(u, k, out, hx, hy)
    inv_hx2 = 1.0 / hx**2
    inv_hy2 = 1.0 / hy**2
    out_arr.fill(0.0)

    uc = u_arr[1:-1, 1:-1]
    kc = k_arr[1:-1, 1:-1]
    ke = 0.5 * (kc + k_arr[2:, 1:-1])
    kw = 0.5 * (kc + k_arr[:-2, 1:-1])
    kn = 0.5 * (kc + k_arr[1:-1, 2:])
    ks = 0.5 * (kc + k_arr[1:-1, :-2])
    out_arr[1:-1, 1:-1] = (
        ke * (uc - u_arr[2:, 1:-1]) * inv_hx2
        + kw * (uc - u_arr[:-2, 1:-1]) * inv_hx2
        + kn * (uc - u_arr[1:-1, 2:]) * inv_hy2
        + ks * (uc - u_arr[1:-1, :-2]) * inv_hy2
    )


@njit(cache=True)
def _numba_apply_stencil_serial_impl(
    u: np.ndarray,
    k: np.ndarray,
    out: np.ndarray,
    hx: float,
    hy: float,
) -> None:
    inv_hx2 = 1.0 / (hx * hx)
    inv_hy2 = 1.0 / (hy * hy)
    nx, ny = u.shape
    for i in range(nx):
        out[i, 0] = 0.0
        out[i, ny - 1] = 0.0
    for j in range(ny):
        out[0, j] = 0.0
        out[nx - 1, j] = 0.0

    for i in range(1, nx - 1):
        for j in range(1, ny - 1):
            ke = 0.5 * (k[i, j] + k[i + 1, j])
            kw = 0.5 * (k[i, j] + k[i - 1, j])
            kn = 0.5 * (k[i, j] + k[i, j + 1])
            ks = 0.5 * (k[i, j] + k[i, j - 1])
            out[i, j] = (
                ke * (u[i, j] - u[i + 1, j]) * inv_hx2
                + kw * (u[i, j] - u[i - 1, j]) * inv_hx2
                + kn * (u[i, j] - u[i, j + 1]) * inv_hy2
                + ks * (u[i, j] - u[i, j - 1]) * inv_hy2
            )


@njit(cache=True, parallel=True)
def _numba_apply_stencil_parallel_impl(
    u: np.ndarray,
    k: np.ndarray,
    out: np.ndarray,
    hx: float,
    hy: float,
) -> None:
    inv_hx2 = 1.0 / (hx * hx)
    inv_hy2 = 1.0 / (hy * hy)
    nx, ny = u.shape
    for i in prange(nx):
        out[i, 0] = 0.0
        out[i, ny - 1] = 0.0
    for j in prange(ny):
        out[0, j] = 0.0
        out[nx - 1, j] = 0.0

    for i in prange(1, nx - 1):
        for j in range(1, ny - 1):
            ke = 0.5 * (k[i, j] + k[i + 1, j])
            kw = 0.5 * (k[i, j] + k[i - 1, j])
            kn = 0.5 * (k[i, j] + k[i, j + 1])
            ks = 0.5 * (k[i, j] + k[i, j - 1])
            out[i, j] = (
                ke * (u[i, j] - u[i + 1, j]) * inv_hx2
                + kw * (u[i, j] - u[i - 1, j]) * inv_hx2
                + kn * (u[i, j] - u[i, j + 1]) * inv_hy2
                + ks * (u[i, j] - u[i, j - 1]) * inv_hy2
            )


def numba_apply_stencil_serial(
    u: np.ndarray,
    k: np.ndarray,
    out: np.ndarray,
    hx: float,
    hy: float,
) -> None:
    u_arr, k_arr, out_arr = _validate_stencil_inputs(u, k, out, hx, hy)
    _numba_apply_stencil_serial_impl(u_arr, k_arr, out_arr, float(hx), float(hy))


def numba_apply_stencil(
    u: np.ndarray,
    k: np.ndarray,
    out: np.ndarray,
    hx: float,
    hy: float,
) -> None:
    u_arr, k_arr, out_arr = _validate_stencil_inputs(u, k, out, hx, hy)
    _numba_apply_stencil_parallel_impl(u_arr, k_arr, out_arr, float(hx), float(hy))
