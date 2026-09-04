import numpy as np
import pytest


def test_numba_stencil_matches_matrix_free_reference():
    from pdescale.grid import Grid2D
    from pdescale.matrix_free import matrix_free_apply
    from pdescale.numba_kernels import numba_apply_stencil
    from pdescale.operators import interior_to_vector
    from pdescale.problems import k_field

    grid = Grid2D(24, 24)
    rng = np.random.default_rng(0)
    u = np.zeros((grid.nx, grid.ny), dtype=float)
    u[1:-1, 1:-1] = rng.normal(size=(grid.nx - 2, grid.ny - 2))
    k = k_field(grid.x, grid.y, "smooth")
    out = np.ones_like(u)

    numba_apply_stencil(u, k, out, grid.hx, grid.hy)
    expected = matrix_free_apply(interior_to_vector(u), grid, "smooth").reshape(
        (grid.nx - 2, grid.ny - 2)
    )

    assert np.allclose(out[1:-1, 1:-1], expected, rtol=1e-12, atol=1e-9)
    assert np.all(out[0, :] == 0.0)
    assert np.all(out[-1, :] == 0.0)
    assert np.all(out[:, 0] == 0.0)
    assert np.all(out[:, -1] == 0.0)


def test_numpy_serial_and_parallel_stencils_match():
    from pdescale.numba_kernels import (
        numba_apply_stencil,
        numba_apply_stencil_serial,
        numpy_apply_stencil,
    )

    rng = np.random.default_rng(1)
    u = np.zeros((18, 18), dtype=float)
    u[1:-1, 1:-1] = rng.normal(size=(16, 16))
    k = 1.0 + rng.random(size=u.shape)
    expected = np.zeros_like(u)
    serial = np.zeros_like(u)
    parallel = np.zeros_like(u)

    numpy_apply_stencil(u, k, expected, 1.0 / 17, 1.0 / 17)
    numba_apply_stencil_serial(u, k, serial, 1.0 / 17, 1.0 / 17)
    numba_apply_stencil(u, k, parallel, 1.0 / 17, 1.0 / 17)

    assert np.allclose(serial, expected, rtol=1e-12, atol=1e-9)
    assert np.allclose(parallel, expected, rtol=1e-12, atol=1e-9)


def test_numba_stencil_rejects_invalid_inputs():
    from pdescale.numba_kernels import numba_apply_stencil

    u = np.zeros((8, 8), dtype=float)
    k = np.ones_like(u)
    out = np.zeros((7, 8), dtype=float)

    with pytest.raises(ValueError, match="same shape"):
        numba_apply_stencil(u, k, out, 1.0, 1.0)

    with pytest.raises(ValueError, match="positive"):
        numba_apply_stencil(u, k, np.zeros_like(u), 0.0, 1.0)
