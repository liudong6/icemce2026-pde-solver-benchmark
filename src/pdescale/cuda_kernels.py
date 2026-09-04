from __future__ import annotations

import numpy as np
from numba import njit, prange
from numba import cuda


JACOBI_BYTES_PER_POINT = 5 * np.dtype(float).itemsize


def _validate_jacobi_input(u0: np.ndarray, steps: int) -> np.ndarray:
    if steps < 0:
        raise ValueError("steps must be non-negative")
    u = np.asarray(u0, dtype=np.float64)
    if u.ndim != 2:
        raise ValueError("u0 must be a 2D array")
    if u.shape[0] < 3 or u.shape[1] < 3:
        raise ValueError("u0 must be at least 3 by 3")
    return np.ascontiguousarray(u)


def jacobi_bytes_per_step(shape: tuple[int, int]) -> int:
    if len(shape) != 2:
        raise ValueError("shape must be two-dimensional")
    interior_points = max(int(shape[0]) - 2, 0) * max(int(shape[1]) - 2, 0)
    return int(interior_points * JACOBI_BYTES_PER_POINT)


@njit(cache=True, parallel=True)
def _numba_jacobi_step(src: np.ndarray, dst: np.ndarray) -> None:
    nx, ny = src.shape
    for i in prange(nx):
        dst[i, 0] = src[i, 0]
        dst[i, ny - 1] = src[i, ny - 1]
    for j in prange(ny):
        dst[0, j] = src[0, j]
        dst[nx - 1, j] = src[nx - 1, j]

    for i in prange(1, nx - 1):
        for j in range(1, ny - 1):
            dst[i, j] = 0.25 * (
                src[i - 1, j]
                + src[i + 1, j]
                + src[i, j - 1]
                + src[i, j + 1]
            )


def numba_jacobi_steps_workspace(
    src: np.ndarray,
    dst: np.ndarray,
    steps: int,
) -> tuple[np.ndarray, np.ndarray]:
    src_arr = _validate_jacobi_input(src, steps)
    dst_arr = np.asarray(dst, dtype=np.float64)
    if dst_arr.shape != src_arr.shape:
        raise ValueError("src and dst must have the same shape")
    dst_arr = np.ascontiguousarray(dst_arr)

    current = src_arr
    work = dst_arr
    for _ in range(steps):
        _numba_jacobi_step(current, work)
        current, work = work, current
    return current, work


def numba_jacobi_steps(u0: np.ndarray, steps: int) -> np.ndarray:
    u = _validate_jacobi_input(u0, steps).copy()
    if steps == 0:
        return u
    work = u.copy()
    current, _ = numba_jacobi_steps_workspace(u, work, steps)
    return current.copy()


@cuda.jit
def _cuda_jacobi_step(src: np.ndarray, dst: np.ndarray) -> None:
    i, j = cuda.grid(2)
    nx, ny = src.shape
    if i >= nx or j >= ny:
        return
    if i == 0 or j == 0 or i == nx - 1 or j == ny - 1:
        dst[i, j] = src[i, j]
    else:
        dst[i, j] = 0.25 * (
            src[i - 1, j]
            + src[i + 1, j]
            + src[i, j - 1]
            + src[i, j + 1]
        )


def launch_cuda_jacobi_steps(
    src,
    dst,
    steps: int,
    *,
    block: tuple[int, int] = (16, 16),
    sync: bool = True,
):
    if steps < 0:
        raise ValueError("steps must be non-negative")
    grid = (
        (src.shape[0] + block[0] - 1) // block[0],
        (src.shape[1] + block[1] - 1) // block[1],
    )
    current = src
    work = dst
    for _ in range(steps):
        _cuda_jacobi_step[grid, block](current, work)
        current, work = work, current
    if sync:
        cuda.synchronize()
    return current, work


def cuda_jacobi_steps(u0: np.ndarray, steps: int) -> np.ndarray:
    if not cuda.is_available():
        raise RuntimeError("CUDA is not available")
    u = _validate_jacobi_input(u0, steps)
    if steps == 0:
        return u.copy()
    d_u = cuda.to_device(u)
    d_work = cuda.device_array_like(d_u)
    current, _ = launch_cuda_jacobi_steps(d_u, d_work, steps)
    return current.copy_to_host()
